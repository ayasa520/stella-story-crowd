"""Prepare native-format story assets for the first two crowdsourcing episodes.

The native scene files are the editable source of truth. Recovery evidence and
unresolved Studio extensions live in adjacent review files, never in the game
payload. This command reads existing workspaces but does not open a mutable
StoryWorkspace, run migrations, publish content, or change the local project.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SceneSpec:
    id: int
    section_id: int
    title: str
    title_ja: str


SCENES = (
    SceneSpec(10010020, 1001, "序章", "序章"),
    SceneSpec(10010001, 1001, "异世界召唤", "異世界召喚"),
    SceneSpec(10010016, 1001, "与拉姆相遇", "ラムとの出会い"),
    SceneSpec(10140002, 1014, "与少女相遇", "少女との出会い"),
    SceneSpec(10140003, 1014, "魔法与精灵", "魔法と精霊"),
)

# These identifiers were read from Bilibili's public pagelist endpoint for the
# source collection. The page number is descriptive; CID identifies the exact
# recording if the uploader subsequently changes the collection's ordering.
RECORDINGS = (
    dict(id="bili-capital-02", provider="bilibili", bvid="BV1bK4y1a7Fm",
         cid=235287283, p=2, title="1本编「异世界召唤」", duration=247),
    dict(id="bili-capital-03", provider="bilibili", bvid="BV1bK4y1a7Fm",
         cid=235290839, p=3, title="1本编「异世界召唤」Ver拉姆", duration=167),
    dict(id="bili-capital-04", provider="bilibili", bvid="BV1bK4y1a7Fm",
         cid=235293693, p=4, title="2本编「银发的少女」", duration=561),
)

KINDS = {"title": 0, "text": 1, "card": 2, "movie": 3, "battle": 4, "tutorial": 5}
READ_FIELDS = {"read_branch_list", "read_branch_num", "is_clear"}
NODE_FIELDS = {
    "voice", "bg_picture", "bg_music", "motion", "branch_list", "video",
    "msg_text", "is_root", "scenario_id", "command", "se", "character",
    "uniq_id", "talk_chara", "battle_stage_id", "position", "scenario_type",
    "msg_character", "character_image",
}


def encoded(value: Any) -> bytes:
    """Use one deterministic representation for files and projection digests."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def static_projection(capture: dict) -> dict:
    """Match the static native payload in tools/build_content.py.

    Whole captures contain a real player's identity, session keys, progress,
    transaction and account state. Only native content belongs in a public
    data repository. Preserve every unknown field inside the selected static
    collections while removing the same explicit read markers as the existing
    client packaging path.
    """
    return dict(
        scenario_list=deepcopy(capture["scenario_list"]),
        video_list=deepcopy(capture.get("video_list", [])),
        branch_work_list=[{key: deepcopy(value) for key, value in row.items()
                           if key != "is_read"}
                          for row in capture.get("branch_work_list", [])],
        chartmap=dict(scene_list=[{key: deepcopy(value) for key, value in row.items()
                                  if key not in READ_FIELDS}
                                 for row in capture["chartmap"]["scene_list"]]),
    )


def issue(code: str, message: str, *, severity: str = "blocker", **context) -> dict:
    return dict(code=code, severity=severity, message=message, **context)


def motion_field(node: dict) -> str:
    tokens = [node["body"], node["face"], *node["extra_motions"]]
    while tokens and not tokens[-1]:
        tokens.pop()
    return ",".join(tokens)


class NativeIdentifiers:
    """Allocate stable *authored* identifiers, never infer missing original IDs.

    IDs depend only on the persisted scenario number and native branch side.
    Adding a scene or another node cannot renumber an existing item. The
    reserved ranges are disjoint, fit exactly in JavaScript integers, and are
    validated before writing. These allocations are recorded as reconstruction
    provenance and are not represented as recovered official identifiers.
    """

    def __init__(self, scene_id: int):
        self.base = scene_id * 100_000

    def node(self, scenario_id: int) -> int:
        if not 0 < scenario_id < 1000:
            raise ValueError("Pilot authored scenario IDs must be in 1..999")
        return self.base + scenario_id

    def branch(self, scenario_id: int, branch_type: int) -> tuple[int, int, int]:
        self.node(scenario_id)
        branch_id = scenario_id * 10 + branch_type
        return branch_id, self.base + 10_000 + branch_id, branch_id * 100 + 1


class SeedSources:
    """Read immutable recovery inputs and provide explicit scene/recording lookups."""

    def __init__(self, root: Path, *, specs: tuple[SceneSpec, ...] = SCENES,
                 project_path: Path | None = None):
        self.root = root
        # Scene scope is supplied by the import workflow. The original pilot
        # remains the default, while later migrations can reuse the exact same
        # native writer without adding another list of hard-coded episodes.
        self.specs = specs
        self.project_path = project_path or root / "data/story_studio/project.json"
        payload = self.project_path.read_bytes()
        self.project = json.loads(payload)
        self.project_sha = digest(payload)
        self.videos = {row["id"]: row for row in self.project["videos"]}
        self.nodes = {row["id"]: row for row in self.project["nodes"]}
        self.entries = {row["id"]: row for row in self.project["directory"]["entries"]}
        self.edges = defaultdict(list)
        for edge in self.project["edges"]:
            if edge["state"] != "excluded":
                self.edges[edge["source"]].append(edge)
        self.originals = {}
        self.original_paths = {}
        self.movie_metadata = {}
        self.original_charts = {}
        for spec in self.specs:
            path = root / f"data/localization/ja-originals/main/rezelos-2020-scene-{spec.id}.json"
            if not path.exists():
                continue
            capture = read_json(path)
            self.originals[spec.id] = capture
            self.original_paths[spec.id] = path
            self.original_charts[spec.section_id] = static_projection(capture)["chartmap"]
            for video in capture.get("video_list", []):
                self.movie_metadata[video["name"].lower()] = deepcopy(video)

    def scene_nodes(self, scene_id: int, *, include_excluded: bool = False) -> list[dict]:
        return [node for node in self.project["nodes"]
                if self.videos[node["video_id"]]["workspace_scene"] == f"scene:{scene_id}"
                and (include_excluded or node["review_state"] != "excluded")]

    def recording(self, node: dict) -> dict:
        video = self.videos[node["video_id"]]
        scene = video["workspace_scene"]
        if scene in {"scene:10140002", "scene:10140003"}:
            item = RECORDINGS[2]
        elif scene == "scene:10010016" or "Ver拉姆" in Path(video["path"]).name:
            item = RECORDINGS[1]
        else:
            item = RECORDINGS[0]
        return dict(recordingId=item["id"], bvid=item["bvid"], cid=item["cid"], p=item["p"],
                    start=node["start"], end=node["end"], visualTime=node["visual_time"],
                    localDuration=video["duration"], timeMapping="same-recording-seconds")

    def public_notes(self, text: str) -> str:
        return text.replace(str(self.root) + "/", "").replace("/home/rikka/Videos/re0/", "recordings/")


class SceneSeed:
    """Convert one bounded scene, separating native data from review evidence."""

    def __init__(self, sources: SeedSources, spec: SceneSpec):
        self.sources, self.spec = sources, spec
        self.studio_nodes = sources.scene_nodes(spec.id)
        self.by_number = {node["scenario_id"]: node for node in self.studio_nodes}
        if len(self.by_number) != len(self.studio_nodes):
            raise ValueError(f"Duplicate Studio scenario ID in scene {spec.id}")
        self.issues = []
        self.unresolved = []
        self.review_nodes = {}
        self.ids = NativeIdentifiers(spec.id)
        self.original = sources.originals.get(spec.id)
        self.origin = "original" if self.original else "reconstructed"
        self.fallback_ids = []

    def add_issue(self, item: dict, review: dict | None = None):
        self.issues.append(item)
        if review is not None:
            review["issues"].append(item)

    def node_review(self, scenario: dict, studio: dict | None) -> dict:
        number = scenario["scenario_id"]
        review = dict(
            status=studio["review_state"] if studio else "original-only",
            sourceText=studio["text"] if studio else scenario["msg_text"],
            sourceSpeaker=studio["speaker"] if studio else scenario["msg_character"],
            translation=studio["translation"] if studio else "",
            notes=self.sources.public_notes(studio["notes"]) if studio else "原稿数组中的保留行。",
            recordings=[self.sources.recording(studio)] if studio else [],
            nativeIdOrigin="captured" if self.original else "authored",
            issues=[],
        )
        if studio:
            review["studioNodeId"] = studio["id"]
            extensions = {key: deepcopy(studio[key]) for key in
                          ("voice_delay_ms", "fx_emission_times", "actors") if studio.get(key)}
            if extensions:
                review["studioExtensions"] = extensions
                for key, label in (("voice_delay_ms", "语音相对正文的延迟"),
                                   ("fx_emission_times", "粒子发射时点覆盖"),
                                   ("actors", "多角色屏幕仿射投影")):
                    if key in extensions:
                        self.add_issue(issue("studio_extension_unmapped", f"{label}尚无已验证的原生表达；完整意图保存在审核记录中。",
                                             scenarioId=number, field=key), review)
            if studio["review_state"] != "reviewed":
                self.add_issue(issue("node_review_pending", "当前工作台节点仍未审核。", scenarioId=number), review)
        self.review_nodes[str(number)] = review
        return review

    def authored_fields(self, studio: dict) -> dict:
        return dict(
            scenario_type=KINDS[studio["kind"]],
            bg_picture=studio["bg_picture"], bg_music=studio["bg_music"],
            character_image=studio["character_image"], video=studio["movie_resource"],
            command=deepcopy(studio["command"]), motion=motion_field(studio),
            voice=f"{studio['bank']},{studio['cue']}" if studio["cue"] else "",
            character=f"live2d/AC_{studio['model']}" if studio["model"] else "",
        )

    def overlay(self, native: dict, studio: dict, review: dict):
        mapped = self.authored_fields(studio)
        # The existing extracted-resource browser normalizes resource-name case.
        # A case-only editor difference is not evidence to rename a native video
        # reference and break its exact video_list name. Keep the captured name.
        for field in ("video", "character", "character_image"):
            if native.get(field, "").casefold() == mapped[field].casefold():
                mapped[field] = native.get(field, "")
        if studio.get("actors"):
            # A group placement cannot be reduced to the speaker's single model.
            # Native actor grammar exists, but its coordinate conversion has not
            # been validated. Keep original native data (or the empty draft value)
            # while exposing the complete actor intent and publication blocker.
            mapped["character"] = native["character"]
        for field, value in mapped.items():
            if native.get(field) != value:
                review.setdefault("overlays", []).append(dict(field=field, before=deepcopy(native.get(field)), after=deepcopy(value)))
                native[field] = value
        text = studio["translation"] or studio["text"]
        if text:
            native["msg_text"] = text
        if studio["speaker"]:
            native["msg_character"] = studio["speaker"]
        if not studio["translation"] and studio["text"]:
            self.fallback_ids.append(native["scenario_id"])

    def original_branches(self, native: dict, studio: dict, review: dict):
        edges = self.sources.edges[studio["id"]]
        for branch in native["branch_list"]:
            side = {1: "", 2: "left", 3: "right"}.get(branch["type"])
            matching = [edge for edge in edges if edge["side"] == side
                        and edge["kind"] == ("next" if side == "" else "choice")]
            if len(matching) != 1:
                self.add_issue(issue("native_graph_preserved", "工作台没有唯一对应连接，保留原稿分支。", severity="warning",
                                     scenarioId=native["scenario_id"], branchId=branch["branch_id"]), review)
                continue
            edge = matching[0]
            proposed = self.transition(edge, branch["uniq_id"], branch["transition_list"][0]["transition_id"])
            old = branch["transition_list"]
            if proposed != old:
                # Studio deliberately omits tutorials and can have divergent
                # restored joins. Importing its edge wholesale would destroy
                # original-only parameter-provider rows and native route data.
                review.setdefault("graphDifferences", []).append(dict(
                    branchId=branch["branch_id"], studioEdgeId=edge["id"],
                    original=deepcopy(old), studioProposal=deepcopy(proposed), action="kept-original"))
                self.add_issue(issue("native_graph_preserved", "工作台连接与原稿不同；保留原稿连接并列出差异供审核。",
                                     severity="warning", scenarioId=native["scenario_id"], branchId=branch["branch_id"]), review)
            if branch["type"] in (2, 3):
                branch["msg_quote_subject"] = edge["label_translation"] or edge["label"] or branch["msg_quote_subject"]
                branch["msg_quote"] = edge["quote_translation"] or edge["quote"] or branch["msg_quote"]
                review.setdefault("branches", []).append(dict(branchId=branch["branch_id"], studioEdgeId=edge["id"],
                    sourceLabel=edge["label"], sourceQuote=edge["quote"],
                    labelTranslation=edge["label_translation"], quoteTranslation=edge["quote_translation"]))

    def transition(self, edge: dict, uniq_id: int, transition_id: int) -> list[dict]:
        tr = edge["transition"]
        if edge["state"] == "missing":
            return []
        result = dict(uniq_id=uniq_id, next_scenario_label=tr["label"],
                      next_scenario_id=0, transition_id=transition_id)
        if tr["label"] == "FINISH":
            section = self.sources.entries.get(tr["section"])
            scene = self.sources.entries.get(tr["scene"])
            if not section:
                return []
            result.update(next_section_id=int(section["native_id"]),
                          next_scene_id=int(scene["native_id"]) if scene else 0)
            if tr["entry"] == "root":
                return [result]
        target = self.sources.nodes.get(edge["target"])
        if target is None or target["review_state"] == "excluded":
            return []
        if tr["label"] != "FINISH" and self.sources.videos[target["video_id"]]["workspace_scene"] != f"scene:{self.spec.id}":
            return []
        result["next_scenario_id"] = target["scenario_id"]
        return [result]

    def reconstructed_branches(self, native: dict, studio: dict, review: dict):
        edges = self.sources.edges[studio["id"]]
        native["branch_list"] = []
        for edge in sorted(edges, key=lambda row: ({"": 0, "left": 1, "right": 2}[row["side"]], row["id"])):
            kind = 1 if edge["kind"] == "next" else {"left": 2, "right": 3}[edge["side"]]
            branch_id, uniq_id, transition_id = self.ids.branch(native["scenario_id"], kind)
            transitions = self.transition(edge, uniq_id, transition_id)
            branch = dict(transition_list=transitions, uniq_id=uniq_id, quote_voice="", branch_id=branch_id,
                          gain_points=[0, 0, 0, 0], msg_quote=edge["quote_translation"] or edge["quote"] or "未設定",
                          msg_quote_subject=(edge["label_translation"] or edge["label"]) if kind != 1 else "未設定", type=kind)
            native["branch_list"].append(branch)
            record = dict(branchId=branch_id, studioEdgeId=edge["id"], sourceLabel=edge["label"], sourceQuote=edge["quote"],
                          labelTranslation=edge["label_translation"], quoteTranslation=edge["quote_translation"], state=edge["state"])
            review.setdefault("branches", []).append(record)
            if not transitions:
                self.unresolved.append(dict(record, scenarioId=native["scenario_id"],
                                            notes=self.sources.public_notes(edge["notes"])))
                self.add_issue(issue("missing_transition", "此分支的后续尚未恢复；保留原生分支与空转移草稿，禁止发布为完整游戏内容。",
                                     scenarioId=native["scenario_id"], branchId=branch_id), review)
        if not native["branch_list"]:
            self.add_issue(issue("missing_outgoing_branch", "节点缺少后续分支。", scenarioId=native["scenario_id"]), review)

    def authored_order(self) -> list[dict]:
        """Use the existing explicit route as authored array order.

        Reconstructed scenes have no recovered native source-array order.
        Studio append order puts later hand-inserted nodes at the end, which
        changes native sparse-background scanning. Following confirmed graph
        edges creates a documented authoring decision, never a claim about
        original ordering. Unreachable surviving rows remain visible at the end.
        """
        nodes = {node["id"]: node for node in self.studio_nodes}
        ordered, visited = [], set()
        root = self.sources.entries[f"scene:{self.spec.id}"]["entry_node"]

        def visit(node_id: str):
            if node_id not in nodes or node_id in visited:
                return
            visited.add(node_id)
            ordered.append(nodes[node_id])
            for edge in self.sources.edges[node_id]:
                if edge["transition"]["label"] != "FINISH":
                    visit(edge["target"])

        visit(root)
        for node in self.studio_nodes:
            if node["id"] not in visited:
                ordered.append(node)
                self.add_issue(issue("unreachable_authored_row", "原生数组保留了当前入口不可达的工作台节点。", scenarioId=node["scenario_id"]))
        return ordered

    def reconstructed_chart(self) -> dict:
        if self.spec.section_id in self.sources.original_charts:
            return deepcopy(self.sources.original_charts[self.spec.section_id])
        rows = []
        for spec in self.sources.specs:
            if spec.section_id != self.spec.section_id:
                continue
            nodes = self.sources.scene_nodes(spec.id)
            edges = [edge for node in nodes for edge in self.sources.edges[node["id"]]]
            exits = []
            for edge in edges:
                tr = edge["transition"]
                if tr["label"] == "FINISH" and tr["scene"] and tr["section"]:
                    pair = dict(section_id=int(self.sources.entries[tr["section"]]["native_id"]),
                                scene_id=int(self.sources.entries[tr["scene"]]["native_id"]))
                    if pair not in exits:
                        exits.append(pair)
            rows.append(dict(branch_num=sum(edge["kind"] == "choice" for edge in edges), scene_id=spec.id,
                             next_scene_list=exits, is_battle=any(node["kind"] == "battle" for node in nodes),
                             branch_condition_list=[]))
        return dict(scene_list=rows)

    def translate_movie_text(self, payload: dict, provenance: dict):
        path = self.sources.root / f"data/localization/zh-CN/main/rezelos-2020-scene-{self.spec.id}.json"
        if not path.exists():
            return
        localized = {video["name"]: video for video in read_json(path).get("video_list", [])}
        changed = 0
        for video in payload["video_list"]:
            other = localized.get(video["name"])
            if not other or len(video["command_list"]) != len(other["command_list"]):
                continue
            for original, translated in zip(video["command_list"], other["command_list"], strict=True):
                if any(original.get(key) != translated.get(key) for key in ("command", "timeline_ms")):
                    raise ValueError("Movie translation changes native timing or command structure")
                for key in ("speaker", "serif"):
                    if translated.get(key) and translated[key] != original.get(key):
                        original[key] = translated[key]
                        changed += 1
        if changed:
            provenance["videoSubtitleTranslation"] = dict(file=str(path.relative_to(self.sources.root)),
                                                         sha256=digest(path.read_bytes()), changedFields=changed)

    def build(self) -> tuple[dict, dict, dict]:
        provenance = dict(source=self.origin, language="zh-CN", workspaceRevision=self.sources.project["revision"],
                          workspaceSha256=self.sources.project_sha, workspaceFile="data/story_studio/project.json",
                          arrayOrder="captured" if self.original else "authored-saved-route",
                          recoveredOriginalOrder=bool(self.original))
        if self.original:
            payload = static_projection(self.original)
            original_path = self.sources.original_paths[self.spec.id]
            provenance.update(originalFile=str(original_path.relative_to(self.sources.root)),
                              originalSha256=digest(original_path.read_bytes()),
                              originalProjectionSha256=digest(encoded(payload)),
                              projectionEncoding="utf-8 JSON ensure_ascii=false indent=2 trailing-newline",
                              preservedNativeFields=sorted(NODE_FIELDS - {"voice", "bg_picture", "bg_music", "motion", "video",
                                                                        "msg_text", "command", "character", "scenario_type",
                                                                        "msg_character", "character_image"}))
            for native in payload["scenario_list"]:
                studio = self.by_number.get(native["scenario_id"])
                review = self.node_review(native, studio)
                if studio:
                    self.overlay(native, studio, review)
                    self.original_branches(native, studio, review)
            self.translate_movie_text(payload, provenance)
        else:
            payload = dict(scenario_list=[], video_list=[], branch_work_list=[], chartmap=self.reconstructed_chart())
            provenance["nativeIdentifierAllocation"] = "scene*100000+scenario; branch_id=scenario*10+type; branch_uid=scene*100000+10000+branch_id; transition_id=branch_id*100+1"
            self.add_issue(issue("native_metadata_unrecovered", "未取得此场景原稿：原生分支编号为稳定编写编号，奖励向量暂为零，分支运行条件未恢复。"))
            root_id = self.sources.entries[f"scene:{self.spec.id}"]["entry_node"]
            for studio in self.authored_order():
                native = dict(voice="", bg_picture="", bg_music="", motion="", branch_list=[], video="", msg_text="",
                              is_root=int(studio["id"] == root_id), scenario_id=studio["scenario_id"], command=["", "", ""],
                              se="", character="", uniq_id=self.ids.node(studio["scenario_id"]), talk_chara="", battle_stage_id=0,
                              position="", scenario_type=KINDS[studio["kind"]], msg_character="未設定", character_image="")
                review = self.node_review(native, studio)
                self.overlay(native, studio, review)
                self.reconstructed_branches(native, studio, review)
                payload["scenario_list"].append(native)
                if native["video"] and not any(row["name"].lower() == native["video"].lower() for row in payload["video_list"]):
                    known = self.sources.movie_metadata.get(native["video"].lower())
                    if known:
                        payload["video_list"].append(dict(deepcopy(known), name=native["video"]))
                    else:
                        payload["video_list"].append(dict(name=native["video"], command_list=[]))
                        self.add_issue(issue("video_metadata_unrecovered", "视频的原生字幕／时序元数据未恢复。", scenarioId=native["scenario_id"]))
        provenance["fallbackScenarioIds"] = self.fallback_ids
        provenance["originalOnlyScenarioIds"] = [node["scenario_id"] for node in payload["scenario_list"]
                                                 if node["scenario_id"] not in self.by_number]
        provenance["excludedStudioNodes"] = [dict(studioNodeId=node["id"], scenarioId=node["scenario_id"],
                                                  sourceText=node["text"], notes=self.sources.public_notes(node["notes"]))
                                                 for node in self.sources.scene_nodes(self.spec.id, include_excluded=True)
                                                 if node["review_state"] == "excluded"]
        review = dict(version=1, sceneId=self.spec.id, provenance=provenance, scenarios=self.review_nodes,
                      unresolvedBranches=self.unresolved, issues=self.issues)
        summary = dict(id=self.spec.id, chapterId=1, sectionId=self.spec.section_id, title=self.spec.title,
                       titleJa=self.spec.title_ja, path=f"native/scenes/{self.spec.id}.json",
                       reviewPath=f"review/scenes/{self.spec.id}.json", nodeCount=len(payload["scenario_list"]),
                       source=self.origin, issues=self.issues,
                       readyForGame=not any(row["severity"] == "blocker" for row in self.issues))
        return payload, review, summary


def validate_seed(payload: dict, review: dict):
    """Reject accidental schema loss while allowing explicitly recorded drafts."""
    assert set(payload) == {"scenario_list", "video_list", "branch_work_list", "chartmap"}
    nodes = payload["scenario_list"]
    ids = {node["scenario_id"] for node in nodes}
    assert len(ids) == len(nodes)
    assert sum(node["is_root"] == 1 for node in nodes) == 1
    missing = {(row["scenarioId"], row["branchId"]) for row in review["unresolvedBranches"]}
    branch_ids = set()
    for node in nodes:
        assert NODE_FIELDS <= set(node), (review["sceneId"], node["scenario_id"], NODE_FIELDS - set(node))
        assert len(node["command"]) == 3 and all(isinstance(value, str) for value in node["command"])
        assert type(node["scenario_id"]) is int and type(node["uniq_id"]) is int
        for branch in node["branch_list"]:
            assert branch["branch_id"] not in branch_ids
            branch_ids.add(branch["branch_id"])
            assert len(branch["gain_points"]) == 4
            if not branch["transition_list"]:
                assert (node["scenario_id"], branch["branch_id"]) in missing
                continue
            assert len(branch["transition_list"]) == 1
            tr = branch["transition_list"][0]
            if tr["next_scenario_label"] == "FINISH":
                assert "next_section_id" in tr and "next_scene_id" in tr
            else:
                assert tr["next_scenario_id"] in ids, (review["sceneId"], node["scenario_id"], tr)


def prepare(root: Path, output: Path) -> dict:
    sources = SeedSources(root)
    files, summaries = {}, []
    for spec in SCENES:
        payload, review, summary = SceneSeed(sources, spec).build()
        validate_seed(payload, review)
        files[summary["path"]] = payload
        files[summary["reviewPath"]] = review
        summaries.append(summary)
    manifest = dict(version=1, title="Stella 剧情共修 · 主线前两话", language="zh-CN",
                    source=dict(workspaceRevision=sources.project["revision"], workspaceSha256=sources.project_sha),
                    chapters=[dict(id=1, title="王都的一日篇", sections=[
                        dict(id=1001, title="第 1 话 · 异世界召唤", titleJa="異世界召喚", sceneIds=[10010020, 10010001, 10010016]),
                        dict(id=1014, title="第 2 话 · 银发的少女", titleJa="銀髪の少女", sceneIds=[10140002, 10140003])])],
                    scenes=summaries, recordings=list(RECORDINGS),
                    recordingMetadataSource="https://api.bilibili.com/x/player/pagelist?bvid=BV1bK4y1a7Fm")
    files["manifest.json"] = manifest
    files["review/conversion-report.json"] = dict(
        version=1, inputProjectSha256=sources.project_sha, workspaceRevision=sources.project["revision"],
        nativePayload="scenario_list, video_list, branch_work_list, chartmap.scene_list",
        scope=[spec.id for spec in SCENES], language="zh-CN", expectedUnresolvedBranchCount=7,
        sceneResults=[dict(id=row["id"], nodeCount=row["nodeCount"], source=row["source"], readyForGame=row["readyForGame"],
                           blockers=sum(item["severity"] == "blocker" for item in row["issues"])) for row in summaries],
        files={name: digest(encoded(value)) for name, value in files.items()},
        limitations=["重建场景没有原始数组顺序、分支奖励与条件的完整证据。",
                     "缺失分支保持空转移草稿，不能发布为完整游戏内容。",
                     "语音延迟、粒子时序覆盖及多角色仿射投影仅在审核记录保留。",
                     "格式与引用检查不等于在原版游戏中完成逐条播放验证。"])
    # Existing asset preparation may share this output root. Own only these
    # exact files, fail before writing if any already exists, and never replace
    # a contributor's edited seed or unrelated assets during regeneration.
    collisions = [str(output / name) for name in files if (output / name).exists()]
    if collisions:
        raise FileExistsError("Seed output already exists: " + ", ".join(collisions))
    for name, value in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded(value))
    if digest(sources.project_path.read_bytes()) != sources.project_sha:
        raise RuntimeError("Source workspace changed during conversion; generated output requires review")
    return dict(output=str(output), files=len(files), scenes=summaries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    result = prepare(root, (args.output or root / "story_crowd_data").resolve())
    print(json.dumps(dict(result, scenes=[{key: row[key] for key in
                     ("id", "nodeCount", "source", "readyForGame")} for row in result["scenes"]]), ensure_ascii=False))


if __name__ == "__main__":
    main()
