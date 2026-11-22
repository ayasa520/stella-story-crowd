"""Stage reviewed translations, visual fields and map repairs over native data.

The installed snapshot is the input, not an earlier OCR assembly plan. This
keeps web edits, sparse inheritance fields, native IDs and authored array order
intact while separate reviewers contribute narrow, preconditioned patches.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from story_studio.crowd_seed import digest, encoded
from story_studio.crowd_seed import NativeIdentifiers
from .native_rough import OfficialDirectory, STRING_FIELDS, require, validate_document
from .native_rough import PERFORMANCE_FIELDS, default_scenario


class InstalledSnapshot:
    """Read and lock only the scenes owned by the restoration importer."""

    def __init__(self, root: Path, target: Path):
        self.root, self.target = root.resolve(), target.resolve()
        self.manifest_raw = (self.target / "manifest.json").read_bytes()
        self.ownership_raw = (self.target / "review/native-restoration.json").read_bytes()
        self.manifest = json.loads(self.manifest_raw)
        self.ownership = json.loads(self.ownership_raw)
        self.entries = {entry["id"]: entry for entry in self.manifest["scenes"]}
        self.documents, self.reviews = {}, {}
        for scene in self.ownership["scenes"]:
            identity = int(scene)
            entry = self.entries[identity]
            require(digest(encoded(entry)) == self.ownership["scenes"][scene],
                    f"Scene summary changed outside importer: {identity}")
            for kind, storage in (("native", self.documents), ("review", self.reviews)):
                name = f"{kind}/scenes/{identity}.json"
                raw = (self.target / name).read_bytes()
                require(digest(raw) == self.ownership["files"][name], f"Owned file changed: {name}")
                storage[identity] = json.loads(raw)

    def node(self, scene: int, number: int, stable_key: str):
        require(scene in self.documents, f"Repair cannot adopt an original baseline scene: {scene}")
        rows = [row for row in self.documents[scene]["scenario_list"] if row["scenario_id"] == number]
        require(len(rows) == 1, f"Repair scenario not unique: {scene}:{number}")
        review = self.reviews[scene]["scenarios"][str(number)]
        require(review["stableKey"] == stable_key, f"Repair stable key mismatch: {scene}:{number}")
        return rows[0], review

    def unchanged_on_disk(self):
        require((self.target / "manifest.json").read_bytes() == self.manifest_raw,
                "Manifest changed during repair staging")
        require((self.target / "review/native-restoration.json").read_bytes() == self.ownership_raw,
                "Ownership changed during repair staging")


class ReviewedRepair:
    """Apply independent evidence packets without declaring whole-scene fidelity."""

    def __init__(self, snapshot: InstalledSnapshot):
        self.snapshot = snapshot
        self.before_documents = deepcopy(snapshot.documents)
        self.before_reviews = deepcopy(snapshot.reviews)
        self.entries = deepcopy(snapshot.entries)
        self.inputs, self.directory_updates, self.counts = [], {}, Counter()
        self.appended_rows = {}

    def read_packet(self, path: Path):
        raw = path.read_bytes()
        self.inputs.append(dict(path=str(path.resolve()), sha256=digest(raw)))
        return json.loads(raw)

    def translations(self, path: Path):
        packet = self.read_packet(path)
        require(packet.get("language") == "zh-CN", "Repair translation must explicitly be zh-CN")
        scene = packet["sceneId"]
        require(scene in self.snapshot.documents, f"Translation scene is not owned: {scene}")
        seen = set()
        for change in packet["scenarios"]:
            number = change["scenarioId"]
            require(number not in seen, f"Duplicate translation: {scene}:{number}")
            seen.add(number)
            node, review = self.snapshot.node(scene, number, change["stableKey"])
            source = change["sourceText"]
            require(review.get("sourceText", node["msg_text"]) == source,
                    f"Japanese source changed before translation: {scene}:{number}")
            require(node["msg_text"] in (source, review.get("translation")),
                    f"Native text has an unaccounted edit: {scene}:{number}")
            chinese = change["translation"]
            require(isinstance(chinese, str) and (bool(chinese) or not source),
                    f"Missing Chinese translation: {scene}:{number}")
            # Native msg_text is the translated game payload. Japanese remains
            # in sourceText so the existing editor can expose both languages;
            # copying Japanese to both fields would hide the original defect.
            corrected_source = change.get("correctedSourceText", source)
            # A small source correction still supplies the entire guarded
            # scene packet. Opting into no-op preservation keeps unrelated
            # translation provenance intact instead of replacing every row's
            # evidence merely because its current values were carried forward.
            # Explicit branch work always follows the existing update path;
            # full-scene coverage and all source/native guards remain required.
            if (packet.get("preserveUnchanged") is True and corrected_source == source
                    and chinese == node["msg_text"] == review.get("translation")
                    and not change.get("branches")):
                self.counts["unchangedTranslationsPreserved"] += 1
                continue
            if corrected_source != source:
                # A later frame review may disambiguate an OCR glyph. Keep
                # the previous reading and its direct image evidence beside
                # the correction; never silently rewrite the Japanese source
                # merely to make it agree with a translated interpretation.
                require(change.get("sourceCorrectionConfirmedByRoot") is True and
                        isinstance(corrected_source, str) and bool(corrected_source) and
                        bool(change.get("sourceCorrectionEvidence")),
                        f"Japanese correction lacks direct root evidence: {scene}:{number}")
                review.setdefault("repairEvidence", {}).setdefault("sourceCorrections", []).append(dict(
                    previousSourceText=source, correctedSourceText=corrected_source,
                    evidence=deepcopy(change["sourceCorrectionEvidence"])))
            review["sourceText"], review["translation"] = corrected_source, chinese
            node["msg_text"] = chinese
            for translated in change.get("branches", []):
                branch = next((item for item in node["branch_list"]
                               if item["branch_id"] == translated["branchId"]), None)
                require(branch is not None, f"Translation branch missing: {scene}:{number}")
                evidence = next((item for item in review.get("branches", [])
                                 if item["branchId"] == branch["branch_id"]), None)
                require(evidence is not None, f"Branch review missing: {scene}:{number}")
                for native, original, target in (("msg_quote", "sourceQuote", "translationQuote"),
                                                  ("msg_quote_subject", "sourceLabel", "translationLabel")):
                    expected = translated[original]
                    require(evidence.get(original, branch[native]) == expected,
                            f"Branch Japanese source changed: {scene}:{number}:{native}")
                    value = translated[target]
                    require(isinstance(value, str) and (bool(value) or not expected),
                            f"Missing translated branch text: {scene}:{number}:{native}")
                    evidence[original] = expected
                    branch[native] = value
                self.counts["translatedBranches"] += 1
            review.setdefault("repairEvidence", {})["translation"] = dict(
                packet=str(path), language="zh-CN", originalSourcePreserved=True)
            self.counts["translatedNodes"] += 1
        require(seen == {row["scenario_id"] for row in self.snapshot.documents[scene]["scenario_list"]},
                f"Translation packet does not cover the entire scene: {scene}")
        title = packet.get("sceneTitleZh")
        if title:
            self.entries[scene]["title"] = title
            key = f"scene:{scene}"
            previous = self.snapshot.manifest.get("studioDirectory", {}).get("entries", {}).get(key, {})
            self.directory_updates[scene] = dict(sceneId=scene,
                expected={name: previous.get(name) for name in ("name", "description")},
                fields=dict(name=title, description=title))

    def charts(self, path: Path):
        packet = self.read_packet(path)
        changes = packet["changes"]
        for change in changes:
            scene = change["sceneId"]
            require(scene in self.snapshot.documents, f"Map repair scene is not owned: {scene}")
            owner = next(row for row in self.snapshot.documents[scene]["chartmap"]["scene_list"]
                         if row["scene_id"] == scene)
            require(owner["next_scene_list"] == change["expectedNextSceneList"],
                    f"Map repair precondition changed: {scene}")
            for addition in change["additions"]:
                require(bool(addition.get("evidenceRoutes")), f"Map edge lacks observed route: {scene}")
                require(all(route.get("overlayEligible") is True for route in addition["evidenceRoutes"]),
                        f"Map edge contains unconfirmed route evidence: {scene}")
                for route in addition["evidenceRoutes"]:
                    source, _ = self.snapshot.node(scene, route["scenarioId"], route["stableKey"])
                    branch = next((item for item in source["branch_list"]
                                   if item["branch_id"] == route["branchId"]), None)
                    require(branch is not None and route["transition"] in branch["transition_list"],
                            f"Map evidence does not match installed executable handoff: {scene}")
                    require(addition["native"] == dict(section_id=route["targetSectionId"],
                                                       scene_id=route["targetSceneId"]),
                            f"Map evidence target mismatch: {scene}")
            # chartmap is an embedded chapter-wide document. Add the same
            # evidence-backed edges to each owned copy while preserving row
            # metadata and existing edge order. Original baseline files are
            # outside this snapshot and are never rewritten for consistency.
            for identity, document in self.snapshot.documents.items():
                row = next(item for item in document["chartmap"]["scene_list"] if item["scene_id"] == scene)
                for addition in change["additions"]:
                    edge = addition["native"]
                    if edge not in row["next_scene_list"]:
                        row["next_scene_list"].append(deepcopy(edge))
            review = self.snapshot.reviews[scene]
            review.setdefault("repairEvidence", {}).setdefault("maps", []).append(dict(
                sourceSceneId=scene, additions=deepcopy(change["additions"]), packet=str(path)))
            self.counts["addedMapEdges"] += len(change["additions"])

    def node_fields(self, path: Path):
        packet = self.read_packet(path)
        for change in packet["changes"]:
            scene, number = change["sceneId"], change["scenarioId"]
            node, review = self.snapshot.node(scene, number, change["stableKey"])
            require(change.get("rootConfirmed") is True, f"Unreviewed performance patch: {scene}:{number}")
            fields = change["fields"]
            require(bool(fields) and set(fields) <= STRING_FIELDS | {"command"},
                    f"Performance patch contains identity/structural changes: {scene}:{number}")
            expected = change["expected"]
            require(set(fields) <= set(expected) <= STRING_FIELDS | {"command"},
                    f"Invalid performance preconditions: {scene}:{number}")
            # A face packet can also guard the model it was measured against.
            # Check every declared precondition, not just fields being changed;
            # otherwise a valid motion token could be applied to another actor.
            for name, value in expected.items():
                require(node[name] == value, f"Performance precondition changed: {scene}:{number}:{name}")
            for name, value in fields.items():
                require(name in change["expected"] and node[name] == change["expected"][name],
                        f"Performance precondition changed: {scene}:{number}:{name}")
                require(isinstance(value, str) if name != "command" else
                        isinstance(value, list) and len(value) == 3 and all(isinstance(x, str) for x in value),
                        f"Invalid performance value: {scene}:{number}:{name}")
                node[name] = deepcopy(value)
                self.counts[name] += 1
            review.setdefault("repairEvidence", {}).setdefault("performance", []).append(
                dict(packet=str(path), fields=sorted(fields), evidence=deepcopy(change.get("evidence", {}))))
            review["unknownFields"] = [name for name in review.get("unknownFields", []) if name not in fields]
            if "command" in fields and change.get("evidence", {}).get("originalCommandPhaseRecovered") is False:
                # A recording can prove that an overlay follows dialogue while
                # leaving the lost script's exact command phases and waits
                # unknown. Installing an explicitly authored reconstruction is
                # not recovery of that original CSV. Retain the command warning
                # beside the execution value so reviewers cannot mistake a
                # playable reproduction for a completely recovered field.
                review["unknownFields"] = sorted(set(review["unknownFields"]) | {"command"})
            if "motion" in fields and "verifiedMotionComponents" in change:
                components = set(change["verifiedMotionComponents"])
                require(bool(components) and components <= {"body", "face", "extra"},
                        f"Invalid verified motion components: {scene}:{number}")
                # Native motion is one CSV field, but its independent layers
                # have different evidence. Writing only a verified face must
                # not silently claim recovery of the body or additional layers.
                unknown = set(review["unknownFields"])
                unknown.update("motion." + part for part in {"body", "face", "extra"} - components)
                unknown.difference_update("motion." + part for part in components)
                review["unknownFields"] = sorted(unknown)

    def _validate_ending_source_attachment(self, packet, document, source, branch):
        """Keep suffix allocation separate from an explicitly reviewed route origin."""
        guard = packet.get("nonTailAttachment")
        if source is document["scenario_list"][-1]:
            require(guard is None, "Non-tail attachment guard does not match an array-tail source")
            return
        # Native array order supplies persistent parameters independently of
        # executable edges. An alternate-route row after the ending origin
        # must therefore stay in place, even when this route jumps past it to
        # newly appended VIDEO/TITLE rows. Existing tail-only packets receive
        # no implicit permission to use a different route origin.
        require(packet.get("version") == 2 and packet.get("terminal") is not None and
                packet.get("finish") is None and isinstance(guard, dict) and
                guard.get("kind") == "append-ending-from-existing-empty-branch" and
                guard.get("rootConfirmed") is True and bool(guard.get("evidence")),
                "Non-tail ending needs an explicit reviewed v2 terminal attachment")
        # Bind the complete ordered array, not only its last node or maximum
        # number: this also locks alternate-route transitions and parameter
        # providers. The caller separately requires the selected branch to be
        # empty; this guard never authorizes replacing an executable edge.
        require(guard.get("expectedSourceUniqId") == source["uniq_id"] and
                guard.get("expectedBranchUniqId") == branch["uniq_id"] and
                guard.get("expectedScenarioArraySha256") == digest(encoded(document["scenario_list"])),
                "Non-tail ending attachment source or ordered array changed")

    def ending_sequence(self, path: Path, directory_path: Path):
        """Append a directly reviewed ending while preserving installed IDs.

        Missing VIDEO/TITLE rows are structural gaps, not permission to rebuild
        the chapter from an old OCR plan. Allocate only a suffix after the last
        installed row, connect one explicitly guarded empty continuation, and
        retain the source witness and reconstruction limits on every new row.
        Cross-section FINISH targets must additionally match the original
        directory's explicit successor and root, rather than video numbering.
        """
        packet = self.read_packet(path)
        require(packet.get("rootConfirmed") is True and bool(packet.get("evidence")),
                "Ending sequence needs direct root-reviewed evidence")
        scene = packet["sceneId"]
        previous, previous_review = self.snapshot.node(scene, packet["afterScenarioId"], packet["afterStableKey"])
        document, review = self.snapshot.documents[scene], self.snapshot.reviews[scene]
        branch = next((row for row in previous["branch_list"] if row["branch_id"] == packet["branchId"]), None)
        require(branch is not None and branch["transition_list"] == packet["expectedTransitions"] == [],
                "Ending cannot replace an existing executable continuation")
        self._validate_ending_source_attachment(packet, document, previous, branch)
        directory_raw = directory_path.read_bytes()
        directory = OfficialDirectory(json.loads(directory_raw), 1)
        finish, terminal = packet.get("finish"), packet.get("terminal")
        require((finish is not None) != (terminal is not None),
                "Ending needs exactly one legacy finish or reviewed terminal object")
        section = self.entries[scene]["sectionId"]
        if terminal is not None:
            # This v2 option owns an authored no-successor FINISH decision.
            # The original intro102 provides its omitted-field representation,
            # while the chapter's own evidence must establish completion. It
            # cannot inherit a guessed next section from a matching route name.
            require(packet.get("version") == 2 and isinstance(terminal, dict) and
                    terminal.get("kind") == "finish-without-successor" and
                    terminal.get("nativeRepresentation") == "omitted-destination-fields" and
                    terminal.get("rootConfirmed") is True and bool(terminal.get("evidence")) and
                    terminal.get("originalPayloadRecovered") is False,
                    "Terminal ending needs explicit reviewed v2 authored-completion evidence")
        else:
            require(isinstance(finish, dict), "Ending finish must be an object")
            require(finish["sectionId"] in directory.sections[section]["native"]["next_section_id"],
                    "Ending successor is not an explicit original-master edge")
            destination = directory.scene(finish["sceneId"])
            require(destination["sectionId"] == finish["sectionId"] and destination["native"]["is_root"] == 1,
                    "Ending target is not the explicit original-master scene root")
        definitions = packet["nodes"]
        require(bool(definitions) and definitions[-1]["fields"].get("scenario_type") == 0,
                "Ending must terminate in a reviewed native TITLE")
        identifiers = NativeIdentifiers(scene)
        maximum = max(row["scenario_id"] for row in document["scenario_list"])
        require(scene not in self.appended_rows, "Only one ending suffix per scene is allowed in a repair batch")
        new_rows, new_reviews = [], []
        existing_keys = {row["stableKey"] for row in review["authoredArrayOrder"]}
        for offset, definition in enumerate(definitions, 1):
            number, fields = maximum + offset, definition["fields"]
            require(definition.get("rootConfirmed") is True and definition.get("evidence"),
                    "Unreviewed row in ending sequence")
            key = definition["stableKey"]
            require(key not in existing_keys, "Ending stable key already exists")
            existing_keys.add(key)
            require(set(fields) <= STRING_FIELDS | {"scenario_type", "command"},
                    "Ending row cannot override identities or branch arrays")
            row = default_scenario(scene, number)
            row.update(deepcopy(fields))
            japanese, chinese = definition["sourceText"], definition["translation"]
            require(isinstance(japanese, str) and isinstance(chinese, str) and (bool(chinese) or not japanese),
                    "Ending source/translation is incomplete")
            row["msg_text"] = chinese
            new_rows.append(row)
            new_reviews.append(dict(status="draft", nativeIdOrigin="authored", stableKey=key,
                sourceText=japanese, translation=chinese, sourceSpeaker="",
                recordings=deepcopy(definition["evidence"]),
                unknownFields=sorted((PERFORMANCE_FIELDS - fields.keys()) |
                                     {"native_array_order", "original_scenario_id", "original_command_phase"}),
                issues=[], branches=[],
                repairEvidence=dict(ending=dict(packet=str(path), evidence=deepcopy(packet["evidence"]),
                                                originalScenarioIdRecovered=False))))
        def connect(source, sidecar, target=None):
            if source is previous:
                link = branch
            else:
                bid, uid, _ = identifiers.branch(source["scenario_id"], 1)
                link = dict(branch_id=bid, uniq_id=uid, type=1, msg_quote="", msg_quote_subject="",
                            quote_voice="", gain_points=[0, 0, 0, 0], transition_list=[])
                source["branch_list"].append(link)
            transition = dict(uniq_id=link["uniq_id"], transition_id=link["branch_id"] * 100 + 1,
                              next_scenario_id=target["scenario_id"] if target else 0,
                              next_scenario_label="" if target else "FINISH")
            if target is None and finish is not None:
                transition.update(next_section_id=finish["sectionId"], next_scene_id=finish["sceneId"])
            link["transition_list"] = [transition]
            branch_review = next((item for item in sidecar["branches"] if item["branchId"] == link["branch_id"]), None)
            if branch_review is None:
                branch_review = dict(branchId=link["branch_id"], stableKey=sidecar["stableKey"] + "-next",
                                     nativeIdOrigin="authored", gainPointsRecovered=False)
                sidecar["branches"].append(branch_review)
            terminal_link = target is None and terminal is not None
            branch_review.update(state="confirmed", verification="observed" if target or terminal_link else "original",
                                 evidence=deepcopy(packet["evidence"]))
            if terminal_link:
                branch_review.update(nativeIdOrigin="authored", nativeTransitionOrigin="authored",
                    originalPayloadRecovered=False, terminal=deepcopy(terminal))
            sidecar["issues"] = [item for item in sidecar.get("issues", [])
                                 if not (item.get("code") == "missing_transition" and item.get("branchId") == link["branch_id"])]
        connect(previous, previous_review, new_rows[0])
        order = max(item["order"] for item in review["authoredArrayOrder"])
        for offset, (row, sidecar) in enumerate(zip(new_rows, new_reviews), 1):
            connect(row, sidecar, new_rows[offset] if offset < len(new_rows) else None)
            document["scenario_list"].append(row)
            review["scenarios"][str(row["scenario_id"])] = sidecar
            review["authoredArrayOrder"].append(dict(stableKey=sidecar["stableKey"],
                                                     scenarioId=row["scenario_id"], order=order + offset))
            if row["video"] and not any(item.get("name") == row["video"] for item in document["video_list"]):
                document["video_list"].append(dict(name=row["video"], command_list=[]))
        self.appended_rows[scene] = [row["uniq_id"] for row in new_rows]
        self.entries[scene]["nodeCount"] = len(document["scenario_list"])
        self.counts["addedEndingNodes"] += len(new_rows)
        if terminal is not None:
            # A completion action names no successor and establishes no map
            # line. Retain its review evidence only in this scene's sidecar;
            # do not touch other owned documents or invent a section handoff.
            review.setdefault("repairEvidence", {}).setdefault("terminalEndings", []).append(dict(
                packet=str(path), terminal=deepcopy(terminal), originalPayloadRecovered=False))
            return
        # The master chapter map is embedded in every owned native document.
        # Keep the newly established executable FINISH visible in the same
        # source-scene map row, including cross-section edges as in the
        # captured first-episode script. Existing baseline documents are not
        # part of this snapshot and remain untouched.
        edge = dict(section_id=finish["sectionId"], scene_id=finish["sceneId"])
        added = False
        for owned in self.snapshot.documents.values():
            owner = next(item for item in owned["chartmap"]["scene_list"] if item["scene_id"] == scene)
            if edge not in owner["next_scene_list"]:
                owner["next_scene_list"].append(deepcopy(edge))
                added = True
        if added:
            self.counts["addedMapEdges"] += 1
        review.setdefault("repairEvidence", {}).setdefault("maps", []).append(dict(
            sourceSceneId=scene, target=edge, packet=str(path),
            basis="Root-reviewed ending and explicit original-master successor/root"))

    def refresh_scene_review(self, scene: int):
        """Refresh derived warnings without promoting incomplete performance.

        Older summaries copied every initial OCR warning into both the scene
        and manifest. A verified narrow repair must remove only that specific
        field/route warning; unresolved fields, pending source reads and the
        scene's draft state remain explicit. This avoids contradicting the
        currently saved fields with an obsolete 'everything is missing' list.
        """
        document, review = self.snapshot.documents[scene], self.snapshot.reviews[scene]
        entries = self.entries[scene]
        global_issues = [deepcopy(item) for item in review.get("issues", []) if "scenarioId" not in item]
        counts, resolved_pairs = Counter(), set()
        for row in document["scenario_list"]:
            sidecar = review["scenarios"][str(row["scenario_id"]) ]
            counts[sidecar.get("status", "draft")] += 1
            resolved = {item["branchId"] for item in sidecar.get("branches", [])
                        if item.get("state") == "confirmed" and item.get("verification") in ("observed", "original", "reviewed")}
            resolved_pairs.update((row["scenario_id"], branch_id) for branch_id in resolved)
            issues = []
            for item in sidecar.get("issues", []):
                item = deepcopy(item)
                if item.get("code") == "performance_unrecovered":
                    unknown = sidecar.get("unknownFields", [])
                    item["fields"] = [name for name in item.get("fields", [])
                                      if name in unknown or any(part.startswith(name + ".") for part in unknown)]
                    if not item["fields"]:
                        continue
                if item.get("code") in ("missing_transition", "transition_review_pending") and item.get("branchId") in resolved:
                    continue
                issues.append(item)
            sidecar["issues"] = issues
            global_issues.extend(deepcopy(issues))
        review["issues"] = global_issues
        # Retain the original unresolved-branch record shape and evidence.
        review["unresolvedBranches"] = [item for item in review.get("unresolvedBranches", [])
                                       if (item.get("scenarioId"), item.get("branchId")) not in resolved_pairs]
        entries.update(nodeCount=len(document["scenario_list"]), reviewCounts=dict(counts), issues=deepcopy(global_issues))

    def stage(self, output: Path, directory_path: Path):
        require(not output.exists(), f"Refusing to overwrite a repair stage: {output}")
        require(not output.is_relative_to(self.snapshot.target) and
                not output.is_relative_to(self.snapshot.root / "data/story_studio"),
                "Repair staging must stay outside installed data and the original Studio workspace")
        directory_raw = directory_path.read_bytes()
        directory = OfficialDirectory(json.loads(directory_raw), 1)
        self.snapshot.unchanged_on_disk()
        files, entries = {}, []
        for scene, document in self.snapshot.documents.items():
            self.refresh_scene_review(scene)
            review = self.snapshot.reviews[scene]
            if document == self.before_documents[scene] and review == self.before_reviews[scene]:
                continue
            validate_document(document, scene, directory)
            # Existing numeric identities and native array order are a hard
            # boundary. Only the explicitly reviewed ending suffix may append
            # rows; ordinary field packets cannot introduce or renumber one.
            before = self.before_documents[scene]
            retained = document["scenario_list"][:len(before["scenario_list"])]
            require([row["uniq_id"] for row in document["scenario_list"]] ==
                    [row["uniq_id"] for row in before["scenario_list"]] + self.appended_rows.get(scene, []),
                    f"Repair reordered rows or added an unreviewed row: {scene}")
            require([[branch["uniq_id"] for branch in row["branch_list"]] for row in retained] ==
                    [[branch["uniq_id"] for branch in row["branch_list"]] for row in before["scenario_list"]],
                    f"Repair changed branch identities: {scene}")
            entry = self.entries[scene]
            entry.update(readyForGame=False, reviewStatus="draft")
            entry["repairStatus"] = "in-progress"
            files[f"native/scenes/{scene}.json"] = encoded(document)
            files[f"review/scenes/{scene}.json"] = encoded(review)
            entries.append(entry)
        require(bool(entries), "Repair stage contains no changed scenes")
        plan = dict(version=1, chapterId=1, directory=dict(path=str(directory_path), sha256=digest(directory_raw)),
                    sourceOwnershipSha256=digest(self.snapshot.ownership_raw), repairInputs=self.inputs)
        files["plan.json"] = encoded(plan)
        report = dict(version=1, scope="Reviewed incremental repairs; full restoration remains in progress",
                      scenes=len(entries), counts=dict(self.counts), inputs=self.inputs,
                      sourceOwnershipSha256=digest(self.snapshot.ownership_raw))
        files["repair-report.json"] = encoded(report)
        manifest = dict(version=1, restorationStatus="rough", structuralValidation="passed",
                        playbackValidation="not-run", scenes=entries, recordings=[],
                        directoryEntryUpdates=list(self.directory_updates.values()),
                        files={name: digest(raw) for name, raw in files.items()})
        output.mkdir(parents=True, exist_ok=False)
        for name, raw in files.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (output / "manifest.json").write_bytes(encoded(manifest))
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--target", type=Path, default=Path("story_crowd_data"))
    parser.add_argument("--directory", type=Path,
                        default=Path("data/native_recovery/royal-capital-20261110/native-directory.json"))
    parser.add_argument("--translations", type=Path, action="append", default=[])
    parser.add_argument("--charts", type=Path)
    parser.add_argument("--node-fields", type=Path, action="append", default=[])
    parser.add_argument("--ending-sequence", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    resolve = lambda path: path if path.is_absolute() else root / path
    repair = ReviewedRepair(InstalledSnapshot(root, resolve(args.target)))
    for path in args.translations:
        repair.translations(resolve(path))
    if args.charts:
        repair.charts(resolve(args.charts))
    for path in args.node_fields:
        repair.node_fields(resolve(path))
    for path in args.ending_sequence:
        repair.ending_sequence(resolve(path), resolve(args.directory))
    print(json.dumps(repair.stage(resolve(args.output), resolve(args.directory)), ensure_ascii=False))


if __name__ == "__main__":
    main()
