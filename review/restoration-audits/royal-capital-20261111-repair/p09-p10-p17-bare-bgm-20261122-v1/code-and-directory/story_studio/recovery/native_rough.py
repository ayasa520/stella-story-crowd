"""Build native ADV drafts from explicit recording evidence, without Studio writes.

Input is a version-1 evidence plan: directory, preservedNative, sceneSegments,
nativeDialogueRows, transitions, and mapEvidence. A dialogue row supplies a
stableKey, sceneId, authored order, known nativeFields and recording evidence.
An existingScenarioId aliases a preserved row without authorizing any edit.
Transitions explicitly name targetKey or finish; a null target records a gap.

Run with --plan PLAN --output NEW_DIRECTORY. The complete plan is validated
before output is created, and an existing output directory is always rejected.
Carry allocation.json forward as previousAllocation when extending a plan;
this retains IDs even when new rows precede old rows in authored array order.
Structural validity, review status and captured/authored ID provenance remain
separate. A valid rough draft is never promoted to reviewed or game-ready.
Evidence verification "observed" means video continuity or the actual selection
was directly checked; "reviewed" adds a separate review. Both can establish an
explicit route while the resulting dialogue and scene remain draft. Candidate,
pending and draft routes retain empty native transition lists.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
from pathlib import Path
import re
from typing import Any

from story_studio.crowd_seed import NODE_FIELDS, NativeIdentifiers, digest, encoded, static_projection


DOCUMENT_FIELDS = {"scenario_list", "video_list", "branch_work_list", "chartmap"}
STRING_FIELDS = {"voice", "bg_picture", "bg_music", "motion", "video", "msg_text", "se",
                 "character", "talk_chara", "position", "msg_character", "character_image"}
MANAGED_FIELDS = {"scenario_id", "uniq_id", "branch_list"}
PERFORMANCE_FIELDS = {"voice", "bg_picture", "bg_music", "motion", "video", "command", "se",
                      "character", "talk_chara", "position", "character_image"}
VERIFICATIONS = {"reviewed", "observed", "candidate", "pending", "draft", "original"}
CONFIRMED_EVIDENCE = {"observed", "reviewed", "original"}
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def integer(value: Any, label: str, minimum: int = 0) -> int:
    require(type(value) is int and minimum <= value <= MAX_SAFE_INTEGER,
            f"{label} must be an integer in {minimum}..{MAX_SAFE_INTEGER}")
    return value


def finite(value: Any, label: str) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            f"{label} must be a finite nonnegative number")
    return float(value)


def string(value: Any, label: str, *, nonempty: bool = False) -> str:
    require(isinstance(value, str) and (not nonempty or bool(value)), f"{label} must be a string")
    return value


def classify_finish_destination(transition: dict) -> str:
    """Mirror the canonical native classifier without changing source fields.

    Captured intro TITLE41 has FINISH with -1/-1; final card102 omits both
    destinations. Normal ADV GetNext (logs/adv.html:7051-7084) completes ADV
    rather than loading another scene for those forms. Recognizing them does
    not recover P29's original payload. Mixed/partial pairs, bools, nulls and
    nonzero local targets without a real destination must remain invalid.
    """
    number = transition.get("next_scenario_id")
    if (transition.get("next_scenario_label") != "FINISH" or type(number) is not int
            or not 0 <= number <= MAX_SAFE_INTEGER):
        return "invalid"
    absent = "next_section_id" not in transition and "next_scene_id" not in transition
    sentinel = all(type(transition.get(key)) is int and transition[key] == -1
                   for key in ("next_section_id", "next_scene_id"))
    if number == 0 and (absent or sentinel):
        return "terminal"
    if all(type(transition.get(key)) is int and 0 < transition[key] <= MAX_SAFE_INTEGER
           for key in ("next_section_id", "next_scene_id")):
        return "target"
    return "invalid"


def unique_records(rows: list[dict]) -> list[dict]:
    result, seen = [], set()
    for row in rows:
        fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=False)
        if fingerprint not in seen:
            seen.add(fingerprint)
            result.append(deepcopy(row))
    return result


def issue(code: str, message: str, **context) -> dict:
    return dict(code=code, severity="warning", message=message, **context)


class InputSources:
    """Verify immutable inputs and retain source identities outside native JSON."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.identities: list[dict] = []

    def path(self, value: str | Path) -> Path:
        path = Path(value)
        return (path if path.is_absolute() else self.root / path).resolve()

    def load(self, value: str | Path | dict, role: str, *, locked: bool = False) -> tuple[dict, bytes]:
        spec = value if isinstance(value, dict) else dict(path=str(value))
        path = self.path(spec["path"])
        expected = spec.get("sha256")
        if locked:
            require(isinstance(expected, str) and bool(re.fullmatch(r"[a-f0-9]{64}", expected)),
                    f"{role} requires an explicit SHA-256 lock")
        raw = path.read_bytes()
        fingerprint = digest(raw)
        require(expected is None or fingerprint == expected, f"Source changed: {path}")
        record_path = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
        self.identities.append(dict(path=record_path, sha256=fingerprint, role=role))
        document = json.loads(raw)
        require(isinstance(document, dict), f"{path} must contain a JSON object")
        return document, raw


class OfficialDirectory:
    """Read explicit official identity and map evidence, never infer adjacency."""

    def __init__(self, document: dict, chapter_id: int):
        require(document.get("version") == 1 and document.get("chapterId") == chapter_id,
                "Directory version/chapter does not match the plan")
        self.document = document
        self.sections = {row["id"]: row for row in document["sections"]}
        self.scenes = {row["id"]: row for section in document["sections"] for row in section["scenes"]}
        require(len(self.scenes) == sum(len(row["scenes"]) for row in document["sections"]),
                "Directory contains duplicate scene IDs")

    def scene(self, scene_id: int) -> dict:
        integer(scene_id, "sceneId", 1)
        require(scene_id in self.scenes, f"Unknown official scene ID: {scene_id}")
        return self.scenes[scene_id]

    def chart(self, evidence: list[dict]) -> tuple[dict, list[dict]]:
        rows, issues = {}, []
        for scene in self.scenes.values():
            variants = scene.get("chartmap", {}).get("capturedRows", [])
            require(len(variants) <= 1, f"Conflicting captured charts need resolution: {scene['id']}")
            rows[scene["id"]] = deepcopy(variants[0]["native"]) if variants else dict(
                scene_id=scene["id"], branch_num=0, next_scene_list=[],
                is_battle=False, branch_condition_list=[])
        # Captured empty next_scene_list rows are incomplete knowledge, not proof
        # that an unlocked scene has no route. Only a caller-reviewed map frame
        # may add map lines. Those lines never synthesize scenario transitions.
        for record in evidence:
            section_id = integer(record.get("sectionId"), "mapEvidence.sectionId", 1)
            require(section_id in self.sections, f"Unknown map section: {section_id}")
            string(record.get("frame"), "mapEvidence.frame", nonempty=True)
            verification = record.get("verification", "pending")
            require(verification in VERIFICATIONS, "Unknown map verification status")
            if verification not in CONFIRMED_EVIDENCE:
                issues.append(issue("map_evidence_pending", "Map lines remain review-only until their frame is reviewed.",
                                    sectionId=section_id, frame=record["frame"]))
                continue
            for edge in record.get("explicitEdges", []):
                source = self.scene(edge["sourceSceneId"])
                target = self.scene(edge["targetSceneId"])
                require(source["sectionId"] == section_id, "Map source scene is outside the stated section")
                require(target["sectionId"] == edge["targetSectionId"], "Map target scene/section mismatch")
                native = dict(section_id=target["sectionId"], scene_id=target["id"])
                targets = rows[source["id"]]["next_scene_list"]
                if not any(all(item.get(key) == value for key, value in native.items()) for item in targets):
                    targets.append(native)
        return dict(scene_list=list(rows.values())), issues


class StableIdentifiers:
    """Allocate authored IDs once; stable keys express deliberate scene sharing.

    Text equality is deliberately irrelevant. Two recordings can reference the
    same authored row only by supplying the same stableKey. A previous registry
    reserves even removed keys, so later additions cannot reuse or renumber them.
    IDs are authoring identifiers, never claims to have recovered original IDs.
    """

    def __init__(self, previous: dict | None, baselines: dict[int, dict]):
        previous = previous or dict(version=1, rows={}, branches={})
        require(previous.get("version") == 1, "Unsupported allocation registry")
        self.rows = deepcopy(previous.get("rows", {}))
        self.branches = deepcopy(previous.get("branches", {}))
        self.reserved: dict[int, set[int]] = defaultdict(set)
        self.baseline_branch_ids: dict[int, set[int]] = defaultdict(set)
        seen = {}
        for key, row in self.rows.items():
            identity = (integer(row["sceneId"], "allocated sceneId", 1),
                        integer(row["scenarioId"], "allocated scenarioId", 1))
            require(identity not in seen, f"Two stable keys alias an allocated ID: {key} / {seen.get(identity)}")
            seen[identity] = key
            self.reserved[identity[0]].add(identity[1])
        for scene_id, baseline in baselines.items():
            self.reserved[scene_id].update(row["scenario_id"] for row in baseline["scenario_list"])
            self.baseline_branch_ids[scene_id].update(
                branch["branch_id"] for row in baseline["scenario_list"] for branch in row["branch_list"])

    def row(self, record: dict, origin: str) -> int:
        key, scene_id = record["stableKey"], record["sceneId"]
        existing = record.get("existingScenarioId")
        allocated = self.rows.get(key)
        if allocated:
            require(allocated["sceneId"] == scene_id, f"A stable key moved to another scene: {key}")
            number = allocated["scenarioId"]
            require(existing is None or existing == number, f"Existing scenario alias changed: {key}")
        elif existing is not None:
            number = integer(existing, "existingScenarioId", 1)
            require(not any(row["sceneId"] == scene_id and row["scenarioId"] == number for row in self.rows.values()),
                    f"Use the same stableKey when sharing an existing scenario: {scene_id}:{number}")
        else:
            number = max(self.reserved[scene_id], default=0) + 1
            while any(number * 10 + kind in self.baseline_branch_ids[scene_id] for kind in (1, 2, 3)):
                number += 1
            NativeIdentifiers(scene_id).node(number)
        self.reserved[scene_id].add(number)
        value = dict(sceneId=scene_id, scenarioId=number, nativeIdOrigin=origin)
        if allocated:
            require(allocated == value, f"An allocated row changed identifier provenance: {key}")
        self.rows[key] = value
        return number

    def branch(self, key: str, scene_id: int, scenario_id: int, branch_type: int) -> tuple[int, int, int]:
        branch_id, uniq_id, transition_id = NativeIdentifiers(scene_id).branch(scenario_id, branch_type)
        value = dict(sceneId=scene_id, scenarioId=scenario_id, branchId=branch_id,
                     branchType=branch_type, nativeIdOrigin="authored")
        require(key not in self.branches or self.branches[key] == value, f"An allocated branch changed: {key}")
        self.branches[key] = value
        return branch_id, uniq_id, transition_id

    def document(self) -> dict:
        return dict(version=1, strategy="Persisted stable-key allocation; authored IDs are not recovered original IDs.",
                    rows=dict(sorted(self.rows.items())), branches=dict(sorted(self.branches.items())))


def merge_records(records: list[dict], label: str, *, fields: bool = False) -> list[dict]:
    merged = {}
    for raw in records:
        require(isinstance(raw, dict), f"{label} entries must be objects")
        key = string(raw.get("stableKey"), f"{label}.stableKey", nonempty=True)
        record = deepcopy(raw)
        require(isinstance(record.get("evidence", []), list), f"{key}.evidence must be an array")
        require(isinstance(record.get("unknownFields", []), list)
                and all(isinstance(value, str) for value in record.get("unknownFields", [])),
                f"{key}.unknownFields must be an array of strings")
        if fields:
            require(isinstance(record.get("nativeFields", {}), dict), f"{key}.nativeFields must be an object")
        if key not in merged:
            merged[key] = record
            continue
        current = merged[key]
        for name in (set(current) | set(record)) - {"evidence", "unknownFields", "nativeFields" if fields else ""}:
            if not fields and name in {"targetKey", "finish", "subject", "quote", "quoteVoice"}:
                before, after = current.get(name), record.get(name)
                if before in (None, "") and after not in (None, ""):
                    # A second recording may observe a branch that the first
                    # recording left explicitly unknown. This is a monotone
                    # evidence refinement, not permission to replace a known
                    # destination or bubble. Approved native baselines still
                    # cannot be edited by this planning path.
                    require(record.get("verification") in CONFIRMED_EVIDENCE,
                            f"An unknown branch can only be filled by confirmed evidence: {key}.{name}")
                    current[name] = deepcopy(after)
                    continue
                if before not in (None, "") and after in (None, ""):
                    continue
            if not fields and name == "verification" and name in current and name in record:
                rank = {"draft": 0, "pending": 0, "candidate": 1, "observed": 2, "reviewed": 3, "original": 4}
                require(current[name] in rank and record[name] in rank, f"Unknown verification for {key}")
                if rank[record[name]] > rank[current[name]]:
                    current[name] = record[name]
                continue
            if not fields and name == "gapReason" and name in current:
                continue
            require(name not in current or name not in record or current[name] == record[name],
                    f"Conflicting {label} field for shared key {key}: {name}")
            if name in record:
                current[name] = deepcopy(record[name])
        if fields:
            target = current.setdefault("nativeFields", {})
            for name, value in record.get("nativeFields", {}).items():
                require(name not in target or target[name] == value, f"Conflicting native field for {key}: {name}")
                target[name] = deepcopy(value)
        current["evidence"] = unique_records(current.get("evidence", []) + record.get("evidence", []))
        current["unknownFields"] = sorted(set(current.get("unknownFields", [])) | set(record.get("unknownFields", [])))
    return list(merged.values())


def default_scenario(scene_id: int, scenario_id: int) -> dict:
    row = {key: "" for key in sorted(STRING_FIELDS)}
    row.update(scenario_id=scenario_id, uniq_id=NativeIdentifiers(scene_id).node(scenario_id),
               is_root=0, scenario_type=2, battle_stage_id=0, command=["", "", ""], branch_list=[])
    return row


class RoughNativeBuilder:
    """Compile evidence into native documents and separate review sidecars."""

    def __init__(self, root: Path, plan_path: Path):
        self.sources = InputSources(root)
        self.plan, self.plan_bytes = self.sources.load(plan_path, "rough recovery evidence plan")
        require(self.plan.get("version") == 1, "Unsupported recovery plan version")
        self.chapter_id = integer(self.plan.get("chapterId"), "chapterId", 1)
        directory, _ = self.sources.load(self.plan["directory"], "official directory evidence")
        self.directory = OfficialDirectory(directory, self.chapter_id)
        self.chart, self.map_issues = self.directory.chart(self.plan.get("mapEvidence", []))
        self.documents: dict[int, dict] = {}
        self.baselines: dict[int, dict] = {}
        self.baseline_bytes: dict[int, bytes] = {}
        self.reviews: dict[int, dict] = {}
        self.baseline_origins: dict[int, str] = {}
        self.new_rows: dict[str, dict] = {}
        self.aliases: dict[str, tuple[int, dict]] = {}
        self.segments = self.read_segments()
        self.load_preserved()
        previous = None
        if self.plan.get("previousAllocation"):
            previous, _ = self.sources.load(self.plan["previousAllocation"], "previous stable ID allocation", locked=True)
        self.identifiers = StableIdentifiers(previous, self.baselines)

    def read_segments(self) -> dict[str, dict]:
        result = {}
        for segment in self.plan.get("sceneSegments", []):
            key = string(segment.get("id"), "sceneSegments.id", nonempty=True)
            require(key not in result, f"Duplicate scene segment ID: {key}")
            self.directory.scene(segment["sceneId"])
            string(segment.get("recordingId"), f"{key}.recordingId", nonempty=True)
            require(finite(segment.get("start"), f"{key}.start") < finite(segment.get("end"), f"{key}.end"),
                    f"Scene segment must have positive duration: {key}")
            require(segment.get("verification", "pending") in VERIFICATIONS, f"Unknown segment verification: {key}")
            require(isinstance(segment.get("evidenceFrames", []), list)
                    and all(isinstance(frame, str) for frame in segment.get("evidenceFrames", [])),
                    f"{key}.evidenceFrames must be an array of paths")
            result[key] = deepcopy(segment)
        return result

    def ensure_scene(self, scene_id: int):
        self.directory.scene(scene_id)
        if scene_id not in self.documents:
            self.documents[scene_id] = dict(scenario_list=[], video_list=[], branch_work_list=[], chartmap=deepcopy(self.chart))
            self.reviews[scene_id] = dict(version=1, sceneId=scene_id, scenarios={}, issues=[], unresolvedBranches=[])
            self.add_issue(scene_id, issue("native_metadata_unrecovered",
                "The draft uses authored IDs, zero default gain vectors and no invented branch lock rules."))
        review = self.reviews[scene_id]
        for key, default in (("scenarios", {}), ("issues", []), ("unresolvedBranches", [])):
            review.setdefault(key, deepcopy(default))

    def load_preserved(self):
        for spec in self.plan.get("preservedNative", []):
            scene_id = integer(spec.get("sceneId"), "preservedNative.sceneId", 1)
            self.directory.scene(scene_id)
            require(scene_id not in self.documents, f"Duplicate preserved native scene: {scene_id}")
            document, raw = self.sources.load(spec, f"preserved native scene {scene_id}", locked=True)
            is_capture = "adventure_data" in document
            if is_capture:
                require(document["adventure_data"]["scene_id"] == scene_id, "Preserved capture scene ID mismatch")
                document = static_projection(document)
            require(set(document) == DOCUMENT_FIELDS, f"Preserved scene {scene_id} is not a static native document")
            self.documents[scene_id] = deepcopy(document)
            self.baselines[scene_id] = deepcopy(document)
            if not is_capture:
                self.baseline_bytes[scene_id] = raw
            self.baseline_origins[scene_id] = "captured" if is_capture else spec.get("identifierOrigin", "preserved-unverified")
            review = dict(version=1, sceneId=scene_id, scenarios={}, issues=[], unresolvedBranches=[])
            if spec.get("reviewPath"):
                review, _ = self.sources.load(dict(path=spec["reviewPath"], sha256=spec.get("reviewSha256")),
                                              f"preserved review for {scene_id}", locked=True)
                require(review.get("sceneId") == scene_id, "Preserved review scene ID mismatch")
            self.reviews[scene_id] = review
            self.ensure_scene(scene_id)
            for node in document["scenario_list"]:
                record = review["scenarios"].setdefault(str(node["scenario_id"]), {})
                record.setdefault("status", "original-only" if is_capture else "unassessed-preserved")
                record.setdefault("nativeIdOrigin", self.baseline_origins[scene_id])

    def add_issue(self, scene_id: int, value: dict, node_id: int | None = None):
        review = self.reviews[scene_id]
        review.setdefault("issues", []).append(value)
        if node_id is not None:
            review["scenarios"][str(node_id)].setdefault("issues", []).append(deepcopy(value))

    def evidence(self, rows: list[dict], scene_id: int) -> list[dict]:
        result = []
        for row in rows:
            require(isinstance(row, dict), "Evidence records must be objects")
            segment = self.segments.get(row.get("segmentId"))
            require(segment is not None, f"Unknown evidence segment: {row.get('segmentId')}")
            require(segment["sceneId"] == scene_id, "Evidence segment belongs to another scene")
            start = finite(row.get("start", segment["start"]), "evidence.start")
            end = finite(row.get("end", start), "evidence.end")
            require(segment["start"] <= start <= end <= segment["end"], "Evidence interval is outside its scene segment")
            require("ocrReviewed" not in row or type(row["ocrReviewed"]) is bool, "ocrReviewed must be boolean")
            if "frame" in row:
                string(row["frame"], "evidence.frame", nonempty=True)
            result.append(dict(deepcopy(row), recordingId=segment["recordingId"], start=start, end=end))
        return unique_records(result)

    def add_rows(self):
        records = merge_records(self.plan.get("nativeDialogueRows", []), "dialogue", fields=True)
        for record in records:
            self.directory.scene(record.get("sceneId"))
            finite(record.get("order", 0), f"{record['stableKey']}.order")
            fields = record.get("nativeFields", {})
            require(isinstance(fields, dict), "nativeFields must be an object")
            require(not set(fields) - (NODE_FIELDS - MANAGED_FIELDS),
                    f"Unknown or builder-managed native fields for {record['stableKey']}: {set(fields) - (NODE_FIELDS - MANAGED_FIELDS)}")
        for record in sorted(records, key=lambda row: (row["sceneId"], row.get("order", 0), row["stableKey"])):
            key, scene_id = record["stableKey"], record["sceneId"]
            self.ensure_scene(scene_id)
            fields = record.get("nativeFields", {})
            evidence = self.evidence(record.get("evidence", []), scene_id)
            existing = record.get("existingScenarioId")
            if existing is not None:
                baseline = self.baselines.get(scene_id, {})
                node = next((row for row in baseline.get("scenario_list", []) if row["scenario_id"] == existing), None)
                require(node is not None, f"Existing scenario alias has no preserved source: {key}")
                require(all(node.get(name) == value for name, value in fields.items()),
                        f"Plan attempts to change preserved native fields: {key}")
                origin = self.reviews[scene_id]["scenarios"][str(existing)]["nativeIdOrigin"]
                self.identifiers.row(record, origin)
                self.aliases[key] = (scene_id, node)
                self.reviews[scene_id]["scenarios"][str(existing)].setdefault("additionalRecordingEvidence", []).extend(evidence)
                continue
            require(bool(evidence), f"New native row requires recording evidence: {key}")
            number = self.identifiers.row(record, "authored")
            require(not any(row["scenario_id"] == number for row in self.documents[scene_id]["scenario_list"]),
                    f"Allocated row collides with preserved content; use existingScenarioId: {key}")
            node = default_scenario(scene_id, number)
            node.update(deepcopy(fields))
            self.documents[scene_id]["scenario_list"].append(node)
            self.new_rows[key] = record
            self.aliases[key] = (scene_id, node)
            unknown = sorted((PERFORMANCE_FIELDS - fields.keys()) | set(record.get("unknownFields", [])))
            review = dict(status="draft", nativeIdOrigin="authored", stableKey=key,
                          sourceText=node["msg_text"], sourceSpeaker=node["msg_character"], translation="",
                          recordings=evidence, unknownFields=unknown, issues=[])
            self.reviews[scene_id]["scenarios"][str(number)] = review
            if unknown:
                self.add_issue(scene_id, issue("performance_unrecovered",
                    "Unrecovered performance fields stay empty/default; this does not block a rough dialogue draft.",
                    scenarioId=number, fields=unknown), number)
            if not all(item.get("ocrReviewed") is True for item in evidence):
                self.add_issue(scene_id, issue("text_review_pending", "Some text evidence still needs visual review.",
                                              scenarioId=number), number)
            if any(self.segments[item["segmentId"]].get("verification", "pending") not in CONFIRMED_EVIDENCE for item in evidence):
                self.add_issue(scene_id, issue("scene_assignment_pending",
                    "The recording segment's scene assignment still needs a title/map evidence check.", scenarioId=number), number)

    def add_transitions(self):
        slots = set()
        records = merge_records(self.plan.get("transitions", []), "transition")
        for record in records:
            string(record.get("fromKey"), "transition.fromKey", nonempty=True)
            integer(record.get("branchType"), "branchType", 1)
        for record in sorted(records, key=lambda row: (row["fromKey"], row["branchType"], row["stableKey"])):
            key, source_key = record["stableKey"], record.get("fromKey")
            require(source_key in self.aliases, f"Unknown transition source: {source_key}")
            scene_id, node = self.aliases[source_key]
            # A baseline alias is an observation target, not permission to edit
            # an approved branch. Adding a route to such a row requires a later
            # explicit editing workflow; rough recovery cannot silently rewrite it.
            require(source_key in self.new_rows, f"Cannot edit a preserved node's outgoing branches: {source_key}")
            branch_type = integer(record.get("branchType"), "branchType", 1)
            require(branch_type in (1, 2, 3), "Authored branchType must be 1, 2 or 3")
            slot = (scene_id, node["scenario_id"], branch_type)
            require(slot not in slots, f"Duplicate branch side; share a stableKey instead: {slot}")
            slots.add(slot)
            verification = record.get("verification", "pending")
            require(verification in VERIFICATIONS, f"Unknown transition verification: {key}")
            branch_id, uniq_id, transition_id = self.identifiers.branch(key, scene_id, node["scenario_id"], branch_type)
            transition = dict(uniq_id=uniq_id, transition_id=transition_id, next_scenario_id=0,
                              next_scenario_label=string(record.get("label", ""), "transition.label"))
            target_key, finish = record.get("targetKey"), record.get("finish")
            require(not (target_key is not None and finish is not None), "Use either targetKey or finish")
            transitions = []
            if finish is not None:
                require(isinstance(finish, dict), "finish must be an object")
                section_id = integer(finish.get("sectionId"), "finish.sectionId", 1)
                target_scene_id = integer(finish.get("sceneId"), "finish.sceneId")
                require(section_id in self.directory.sections, "Unknown FINISH section")
                if target_scene_id:
                    require(self.directory.scene(target_scene_id)["sectionId"] == section_id, "FINISH target scene/section mismatch")
                transition.update(next_scenario_label="FINISH", next_section_id=section_id,
                                  next_scene_id=target_scene_id,
                                  next_scenario_id=integer(finish.get("scenarioId", 0), "finish.scenarioId"))
                transitions = [transition]
            elif target_key is not None:
                require(target_key in self.aliases, f"Unknown transition target key: {target_key}")
                target_scene, target = self.aliases[target_key]
                require(target_scene == scene_id, "A cross-scene transition requires an explicit finish object")
                require(transition["next_scenario_label"] != "FINISH", "FINISH requires a finish object")
                transition["next_scenario_id"] = target["scenario_id"]
                transitions = [transition]
            candidate_transitions = []
            if transitions and verification not in CONFIRMED_EVIDENCE:
                # A proposed destination is useful review evidence, but it is not
                # an executable route until the source continuity/choice has been
                # checked. Preserve the candidate outside the native branch and
                # keep its transition_list empty like an unrecorded destination.
                candidate_transitions, transitions = transitions, []
            points = record.get("gainPoints", [0, 0, 0, 0])
            require(isinstance(points, list) and len(points) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in points),
                    "gainPoints must have four finite numbers")
            branch = dict(transition_list=transitions, uniq_id=uniq_id, branch_id=branch_id, type=branch_type,
                          quote_voice=string(record.get("quoteVoice", ""), "quoteVoice"), gain_points=deepcopy(points),
                          msg_quote=string(record.get("quote", ""), "quote"),
                          msg_quote_subject=string(record.get("subject", ""), "subject"))
            node["branch_list"].append(branch)
            evidence = self.evidence(record.get("evidence", []), scene_id)
            branch_review = dict(branchId=branch_id, stableKey=key, nativeIdOrigin="authored", verification=verification,
                                 state="confirmed" if transitions else "missing",
                                 evidence=evidence, gainPointsRecovered="gainPoints" in record)
            if candidate_transitions:
                branch_review["candidateTransitions"] = candidate_transitions
            self.reviews[scene_id]["scenarios"][str(node["scenario_id"])].setdefault("branches", []).append(branch_review)
            if not transitions:
                gap = dict(scenarioId=node["scenario_id"], branchId=branch_id, stableKey=key,
                           reason=record.get("gapReason", "Unrecorded or unverified branch destination."))
                self.reviews[scene_id]["unresolvedBranches"].append(gap)
                self.add_issue(scene_id, issue("missing_transition", gap["reason"], scenarioId=node["scenario_id"], branchId=branch_id), node["scenario_id"])
            if verification not in CONFIRMED_EVIDENCE:
                self.add_issue(scene_id, issue("transition_review_pending", "This explicit route still needs evidence review.",
                                              scenarioId=node["scenario_id"], branchId=branch_id), node["scenario_id"])

    def add_video_metadata(self):
        supplied = {}
        for record in self.plan.get("videoMetadata", []):
            scene_id = integer(record.get("sceneId"), "videoMetadata.sceneId", 1)
            self.ensure_scene(scene_id)
            native = record.get("native")
            require(isinstance(native, dict) and isinstance(native.get("command_list"), list),
                    "Video metadata must retain a native name and command_list")
            name = string(native.get("name"), "videoMetadata.native.name", nonempty=True)
            require((scene_id, name) not in supplied or supplied[(scene_id, name)] == native, "Conflicting video metadata")
            supplied[(scene_id, name)] = deepcopy(native)
        for scene_id, document in self.documents.items():
            known = {row["name"]: row for row in document["video_list"]}
            for (target_scene, name), value in supplied.items():
                if target_scene != scene_id:
                    continue
                require(name not in known or known[name] == value, f"Cannot change preserved video metadata: {name}")
                if name not in known:
                    document["video_list"].append(value)
                    known[name] = value
            for node in document["scenario_list"]:
                name = node["video"]
                if name and name not in known:
                    require(scene_id not in self.baselines or node not in self.baselines[scene_id]["scenario_list"],
                            "Preserved native video metadata is incomplete; do not silently repair its fields")
                    placeholder = dict(name=name, command_list=[])
                    document["video_list"].append(placeholder)
                    known[name] = placeholder
                    self.add_issue(scene_id, issue("video_metadata_unrecovered", "Movie timing/subtitle metadata remains unrecovered.",
                                                  scenarioId=node["scenario_id"]), node["scenario_id"])

    def verify_preservation(self):
        for scene_id, before in self.baselines.items():
            after = self.documents[scene_id]
            require(after["scenario_list"][:len(before["scenario_list"])] == before["scenario_list"],
                    f"Preserved scenario fields or source-array order changed: {scene_id}")
            require(after["video_list"][:len(before["video_list"])] == before["video_list"],
                    f"Preserved video metadata changed: {scene_id}")
            for key in ("branch_work_list", "chartmap"):
                require(after[key] == before[key], f"Preserved {key} changed: {scene_id}")

    def compile(self) -> dict[str, bytes]:
        self.add_rows()
        self.add_transitions()
        self.add_video_metadata()
        require(bool(self.documents), "Plan has no native scenes")
        self.verify_preservation()
        for scene_id, document in self.documents.items():
            validate_document(document, scene_id, self.directory)
            for node in document["scenario_list"]:
                for branch in node["branch_list"]:
                    for transition in branch["transition_list"]:
                        if (transition["next_scenario_label"] != "FINISH" or
                                classify_finish_destination(transition) == "terminal"):
                            continue
                        target = self.documents.get(transition["next_scene_id"])
                        target_id = transition["next_scenario_id"]
                        if target is not None and target_id:
                            require(any(row["scenario_id"] == target_id for row in target["scenario_list"]),
                                    f"FINISH targets a missing emitted scenario: {transition['next_scene_id']}:{target_id}")
        summaries, files = [], {}
        for scene_id, document in sorted(self.documents.items()):
            review = self.reviews[scene_id]
            authored = [key for key, (sid, _) in self.aliases.items() if sid == scene_id and key in self.new_rows]
            by_id = {row["scenario_id"]: row for row in document["scenario_list"]}
            root = next(row["scenario_id"] for row in document["scenario_list"] if row["is_root"] == 1)
            reachable, pending = set(), [root]
            while pending:
                current = pending.pop()
                if current in reachable:
                    continue
                reachable.add(current)
                for branch in by_id[current]["branch_list"]:
                    for transition in branch["transition_list"]:
                        if transition["next_scenario_label"] != "FINISH":
                            pending.append(transition["next_scenario_id"])
                        elif (classify_finish_destination(transition) == "target" and
                              transition["next_scene_id"] == scene_id):
                            pending.append(transition["next_scenario_id"] or root)
            for key in authored:
                _, node = self.aliases[key]
                if node["scenario_id"] not in reachable:
                    self.add_issue(scene_id, issue("unreachable_authored_row",
                        "This observed row is retained, but no confirmed route from the explicit scene root reaches it.",
                        scenarioId=node["scenario_id"]), node["scenario_id"])
                if not node["branch_list"]:
                    self.add_issue(scene_id, issue("missing_outgoing_branch", "No outgoing route is recovered for this row.",
                                                  scenarioId=node["scenario_id"]), node["scenario_id"])
                for branch in node["branch_list"]:
                    for transition in branch["transition_list"]:
                        if (transition["next_scenario_label"] == "FINISH" and
                                classify_finish_destination(transition) == "target" and
                                transition["next_scene_id"] not in self.documents):
                            self.add_issue(scene_id, issue("destination_body_unrecovered", "The explicit destination has no body in this staging package.",
                                                          scenarioId=node["scenario_id"], branchId=branch["branch_id"]), node["scenario_id"])
            review.update(restorationStatus="rough" if authored else "preserved",
                          structuralValidation="passed", playbackValidation="not-run",
                          authoredArrayOrder=[dict(stableKey=key, scenarioId=self.aliases[key][1]["scenario_id"],
                                                   order=self.new_rows[key].get("order", 0)) for key in authored],
                          sceneSegments=[row for row in self.segments.values() if row["sceneId"] == scene_id],
                          mapEvidence=deepcopy(self.plan.get("mapEvidence", [])))
            # Transition observations are evidence, not executable commands.
            # Preserve frame windows and uncertainty beside the script so a
            # later native-command match can be reviewed without manufacturing
            # Wait/CardOut timing from a dark frame or a background change.
            for field in ("visualTransitions", "transitionEvidence"):
                observations = self.plan.get(field, [])
                require(isinstance(observations, list), f"{field} must be an evidence array")
                review[field] = deepcopy([row for row in observations
                    if not any(name in row for name in ("sceneId", "sourceSceneId", "targetSceneId"))
                    or scene_id in {row.get("sceneId"), row.get("sourceSceneId"), row.get("targetSceneId")}])
            review["issues"] += deepcopy(self.map_issues)
            if authored:
                self.add_issue(scene_id, issue("draft_not_playback_verified",
                    "Native schema validation does not establish original authorship, reviewed text, or verified playback."))
            native_path, review_path = f"native/scenes/{scene_id}.json", f"review/scenes/{scene_id}.json"
            # When a complete native baseline is only carried forward, preserve
            # its source bytes as well as every JSON field. Captured responses
            # are sanitized static projections and therefore cannot use this
            # path: account and read-state data must never enter native outputs.
            unchanged = scene_id in self.baselines and document == self.baselines[scene_id]
            files[native_path] = self.baseline_bytes[scene_id] if unchanged and scene_id in self.baseline_bytes else encoded(document)
            files[review_path] = encoded(review)
            native_scene = self.directory.scenes[scene_id]
            summaries.append(dict(id=scene_id, chapterId=self.chapter_id, sectionId=native_scene["sectionId"],
                title=native_scene["native"]["name"], titleJa=native_scene["native"]["name"],
                path=native_path, reviewPath=review_path, nodeCount=len(document["scenario_list"]),
                source="reconstructed" if authored else "preserved", readyForGame=False,
                reviewStatus="draft" if authored else "preserved", reviewCounts=dict(Counter(
                    record.get("status", "unassessed-preserved") for record in review["scenarios"].values())),
                nativeIdentifierOrigins=sorted({record.get("nativeIdOrigin", "preserved-unverified") for record in review["scenarios"].values()}),
                baselineFieldsPreserved=scene_id in self.baselines,
                baselineBytesPreserved=unchanged and scene_id in self.baseline_bytes,
                issues=deepcopy(review["issues"])))
        files["allocation.json"] = encoded(self.identifiers.document())
        files["plan.json"] = self.plan_bytes
        files["source-locks.json"] = encoded(self.sources.identities)
        chapter = self.directory.document["chapter"]["native"]
        manifest = dict(version=1, title=chapter["name"] + " · 录像原生粗稿", language=self.plan.get("language", "ja"),
            restorationStatus="rough", structuralValidation="passed", playbackValidation="not-run",
            verificationMeanings=dict(observed="Video continuity, actual selection or map frame was directly checked.",
                                      reviewed="An additional evidence review has been completed.",
                                      original="The fact comes from a preserved native source.",
                                      candidate="Unverified candidate; never an executable route.",
                                      pending="Awaiting evidence confirmation; never an executable route."),
            source=dict(type="explicit-recording-evidence-plan", identities=self.sources.identities),
            chapters=[dict(id=self.chapter_id, title=chapter["name"], sections=[
                dict(id=section["id"], title=section["native"]["name"], titleJa=section["native"]["name"],
                     sceneIds=[row["id"] for row in section["scenes"]]) for section in self.directory.sections.values()])],
            scenes=summaries, recordings=deepcopy(self.plan.get("recordings", [])),
            unassignedEvidence=deepcopy(self.plan.get("unassignedEvidence", [])),
            limitations=["Authored scenario and branch IDs are stable authoring allocations, not recovered original IDs.",
                         "Unknown performance data and unrecorded destinations are retained as review gaps.",
                         "Map lines never create executable dialogue transitions.",
                         "Carry allocation.json forward for incremental plans; never identify shared scenes by text equality."],
            files={path: digest(raw) for path, raw in sorted(files.items())})
        files["manifest.json"] = encoded(manifest)
        return files


def validate_document(document: dict, scene_id: int, directory: OfficialDirectory):
    """Validate native shape and references while permitting documented gaps."""
    require(set(document) == DOCUMENT_FIELDS, "Unexpected top-level native fields")
    for key in ("scenario_list", "video_list", "branch_work_list"):
        require(isinstance(document[key], list), f"{key} must be an array")
    require(isinstance(document["chartmap"], dict) and isinstance(document["chartmap"].get("scene_list"), list),
            "chartmap.scene_list must be an array")
    rows = document["scenario_list"]
    require(bool(rows), f"Scene has no native body: {scene_id}")
    require(sum(row.get("is_root") == 1 for row in rows) == 1, f"Scene needs exactly one explicit native root: {scene_id}")
    node_ids, node_uids, branch_ids, branch_uids, transition_ids = set(), set(), set(), set(), set()
    for row in rows:
        require(isinstance(row, dict) and NODE_FIELDS <= row.keys(), f"Missing native fields in scene {scene_id}")
        identity = integer(row["scenario_id"], "scenario_id", 1)
        uid = integer(row["uniq_id"], "scenario uniq_id", 1)
        require(identity not in node_ids and uid not in node_uids, f"Duplicate scenario ID/UID in {scene_id}")
        node_ids.add(identity)
        node_uids.add(uid)
        require(type(row["is_root"]) is int and row["is_root"] in (0, 1), "is_root must be integer 0 or 1")
        require(type(row["scenario_type"]) is int and row["scenario_type"] in range(6), "Unknown scenario_type")
        integer(row["battle_stage_id"], "battle_stage_id")
        for field in STRING_FIELDS:
            string(row[field], field)
        require(isinstance(row["command"], list) and len(row["command"]) == 3 and all(isinstance(v, str) for v in row["command"]),
                "command must contain exactly three native strings")
        require(isinstance(row["branch_list"], list), "branch_list must be an array")
        for branch in row["branch_list"]:
            bid = integer(branch.get("branch_id"), "branch_id", 1)
            buid = integer(branch.get("uniq_id"), "branch uniq_id", 1)
            require(bid not in branch_ids and buid not in branch_uids, f"Duplicate branch ID/UID in {scene_id}")
            branch_ids.add(bid)
            branch_uids.add(buid)
            integer(branch.get("type"), "branch type")
            for field in ("msg_quote", "msg_quote_subject", "quote_voice"):
                string(branch.get(field), field)
            points = branch.get("gain_points")
            require(isinstance(points, list) and len(points) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in points),
                    "gain_points must contain four finite numbers")
            require(isinstance(branch.get("transition_list"), list), "transition_list must be an array")
            for transition in branch["transition_list"]:
                tid = integer(transition.get("transition_id"), "transition_id", 1)
                integer(transition.get("uniq_id"), "transition uniq_id", 1)
                integer(transition.get("next_scenario_id"), "next_scenario_id")
                require(tid not in transition_ids, f"Duplicate transition ID in {scene_id}")
                transition_ids.add(tid)
                string(transition.get("next_scenario_label"), "next_scenario_label")
                if transition["next_scenario_label"] == "FINISH":
                    destination_kind = classify_finish_destination(transition)
                    require(destination_kind != "invalid", "Invalid FINISH destination pair")
                    if destination_kind == "terminal":
                        continue
                    section = integer(transition.get("next_section_id"), "next_section_id", 1)
                    target_scene = integer(transition.get("next_scene_id"), "next_scene_id", 1)
                    require(section in directory.sections, "FINISH references an unknown section")
                    if target_scene:
                        require(directory.scene(target_scene)["sectionId"] == section, "FINISH scene/section mismatch")
    for row in rows:
        for branch in row["branch_list"]:
            for transition in branch["transition_list"]:
                if transition["next_scenario_label"] != "FINISH":
                    require(transition["next_scenario_id"] in node_ids,
                            f"Local transition has no destination: {scene_id}:{transition['next_scenario_id']}")


def build_staging(root: Path, plan_path: Path, output: Path | None = None) -> dict:
    root = root.resolve()
    if output is not None:
        output = (output if output.is_absolute() else root / output).resolve()
        require(not output.exists(), f"Refusing to overwrite existing output: {output}")
        for protected in ("story_crowd_data", "story_crowd", "data/story_studio"):
            require(not output.is_relative_to(root / protected), f"Choose independent staging outside {protected}")
    builder = RoughNativeBuilder(root, plan_path)
    files = builder.compile()
    manifest = json.loads(files["manifest.json"])
    if output is not None:
        # Validation and preservation checks have finished before the first write.
        # mkdir and exclusive file creation close the overwrite race; manifest is
        # written last so a failed disk write cannot masquerade as a complete set.
        output.mkdir(parents=True, exist_ok=False)
        for name, raw in files.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(raw)
    return dict(output=str(output) if output else None, sceneCount=len(manifest["scenes"]),
                nodeCount=sum(row["nodeCount"] for row in manifest["scenes"]),
                authoredSceneCount=sum(row["source"] == "reconstructed" for row in manifest["scenes"]),
                preservedSceneCount=sum(row["baselineFieldsPreserved"] for row in manifest["scenes"]),
                unassignedEvidenceCount=len(manifest["unassignedEvidence"]),
                structuralValidation="passed", restorationStatus="rough", playbackValidation="not-run")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    require(args.validate_only or args.output is not None, "--output is required unless --validate-only is used")
    require(not (args.validate_only and args.output is not None), "--validate-only does not accept --output")
    print(json.dumps(build_staging(args.root, args.plan, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
