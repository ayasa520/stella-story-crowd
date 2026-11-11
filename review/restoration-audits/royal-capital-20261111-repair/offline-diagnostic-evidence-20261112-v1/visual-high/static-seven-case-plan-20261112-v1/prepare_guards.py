"""Prepare reviewable drafts; bind final bytes only under a later root freeze release.

Draft observations are informational, including target rows that may legitimately
change during the separate P29 publication queue. A later binding reads every
target and neighbour afresh, while preserving the original request text/frame
identity. This script writes only a fresh child directory beside itself. It never
registers previews, edits formal data/source, starts a server or opens a browser.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
ROOT = R.parents[3]
DATA = ROOT / "story_crowd_data"
SITE = ROOT / "artifacts/stella-site-repair-source/.sites-checkout"
P29 = R / "visual-high/agent-reviewed-p29-identity-v1"
P28 = R / "visual-high/agent-reviewed-p28-identity-v1"
P27BG = R / "visual-high/agent-reviewed-p27-background-boundary-v1"
CASE_ROWS = [
    ("p27-hall-formal", 10200006, [7, 8, 9], 8, None, "background", None),
    ("reinhard01-static", 10040004, [6, 7, 8, 9], 7, "reinhard01", "character", P28 / "reinhard01-resource-assembled-reference-request.json"),
    ("soldier01-static", 10040051, [4, 5, 6], 5, "soldier01", "character", P29 / "soldier01-exact-static-assembled-reference-request.json"),
    ("julius01-static", 10040051, [5, 6, 7], 6, "julius01", "character", P29 / "julius01-exact-static-assembled-reference-request.json"),
    ("julius-jersey01-static", 10040052, [3, 4, 5], 4, "julius_jersey01", "character", P29 / "julius_jersey01-exact-static-assembled-reference-request.json"),
    ("subaru-tshirt01-static", 10040052, [4, 5, 6], 5, "subaru_tshirt01", "character", P29 / "subaru_tshirt01-exact-static-assembled-reference-request.json"),
    ("subaru-tshirt02-static", 10040052, [4, 5, 6], 5, "subaru_tshirt02", "character", P29 / "subaru_tshirt02-exact-static-assembled-reference-request.json"),
]


def read(path): return json.loads(Path(path).read_bytes())
def digest(raw): return hashlib.sha256(raw).hexdigest()
def rec(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    assert path.is_relative_to(ROOT)
    return dict(path=str(path.relative_to(ROOT)), bytes=len(raw), sha256=digest(raw))
def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write("\n")
def git(path, *args): return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def scene_guard(scene, route):
    native = read(DATA / f"native/scenes/{scene}.json")
    review = read(DATA / f"review/scenes/{scene}.json")["scenarios"]
    rows = {row["scenario_id"]: row for row in native["scenario_list"]}
    result = dict(sceneId=scene, route=route, rows=[], edges=[])
    for node in route:
        result["rows"].append(dict(scenarioId=node, nativeRow=rows[node],
            reviewIdentity={key:review[str(node)][key] for key in ["stableKey", "sourceText", "recordings", "branches"]}))
    for a, b in zip(route, route[1:]):
        matches = [(branch, edge) for branch in rows[a]["branch_list"] for edge in branch["transition_list"]
                   if edge["next_scenario_id"] == b]
        assert len(matches) == 1, ("Route is not a unique existing edge", scene, a, b)
        branch, edge = matches[0]
        observed = [r for r in review[str(a)]["branches"] if r["branchId"] == branch["branch_id"]]
        assert len(observed) == 1 and observed[0]["state"] == "confirmed" and observed[0]["verification"] == "observed"
        result["edges"].append(dict(source=a, target=b, branchId=branch["branch_id"], transition=edge))
    return result


def source_comparison(model, request):
    if model is None:
        return dict(request=rec(P27BG / "p27-hall-bg-picture-only-draft.json"),
                    directReview=rec(P27BG / "p27-hall-boundary-direct-review.json"),
                    availabilityRequest=rec(P27BG / "bg096b-resource-availability-request.json"))
    document = read(request)
    if model == "reinhard01":
        witnesses = [row for row in document["pendingNodes"] if row["scenarioId"] in [7, 8]]
        assert len(witnesses) == 2
        frames = [row["originalFullFrame"] for row in witnesses]
        target = witnesses[0]
    else:
        target = document["target"]
        witness = target["sourceWitness"]
        frames = [dict(file=witness.get("file", witness.get("frame")),
                       sha256=witness.get("sha256", witness.get("frameSha256")),
                       video=witness["video"], videoSha256=witness["videoSha256"], time=witness["time"])]
    for frame in frames:
        assert rec(frame["file"])["sha256"] == frame["sha256"]
    return dict(request=rec(request), originalTargetIdentity={key:target[key] for key in ["sceneId", "scenarioId", "stableKey", "sourceText"]},
                originalFullFrames=frames, oldExpectedNativeFieldsAreHistoricalOnly=True)


def resources(model):
    """Bind exactly four identity responses; reject an unbudgeted texture layout."""
    catalog = read(DATA / "assets/catalog.json")
    row = catalog["models"].get("live2d/AC_" + model)
    if row is None: return dict(model=model, available=False, pending="Formal resource availability required before root freeze")
    document = read(DATA / "assets" / row["model_url"])
    refs = document["FileReferences"]
    assert len(refs["Textures"]) == 1, "This four-response capture budget requires one original texture"
    parent = Path(row["member"]).parent
    entries = [("model-json", row["member"]), ("MOC", str(parent / refs["Moc"])), ("texture", str(parent / refs["Textures"][0]))]
    result = []
    for role, member in entries:
        result.append(dict(role=role, route="/asset/" + member, local=rec(DATA / "assets" / catalog["asset_members"][member])))
    result.append(dict(role="detail", route="/api/model/" + model, local=rec(DATA / "assets" / row["detail_url"])))
    assert len(result) == 4 and sum(r["local"]["bytes"] for r in result) <= 16*1024*1024
    assert all(r["local"]["bytes"] <= 8*1024*1024 for r in result)
    return dict(model=model, available=True, catalogRow=row, actor=read(DATA / "assets/player/manifest.json")["actors"][model], responses=result)


def assemble(frozen):
    cases = []
    for identity, scene, route, target, model, kind, request in CASE_ROWS:
        guard = scene_guard(scene, route)
        comparison = source_comparison(model, request)
        identity_from_request = comparison.get("originalTargetIdentity")
        target_row = next(r for r in guard["rows"] if r["scenarioId"] == target)
        if identity_from_request:
            assert target_row["reviewIdentity"]["stableKey"] == identity_from_request["stableKey"]
            assert target_row["reviewIdentity"]["sourceText"] == identity_from_request["sourceText"]
        case = dict(id=identity, scene=scene, route=route, target=target, kind=kind, model=model,
            captureNodes=route if kind == "background" else [target],
            routeGuard=guard, sourceComparison=comparison,
            fields={} if kind == "background" else {"character":"live2d/AC_"+model},
            expectedNativeRow=target_row["nativeRow"] if frozen else None,
            observedNativeRowInformationalOnly=target_row["nativeRow"],
            rebindAllExpectedFieldsAtFinalFreeze=True, defaultOriginalAdvProjectionUnmodified=True,
            cameraOverride=None, offsetOverride=None, scaleOverride=None,
            installable=False, scopeApproved=False, browserAuthorized=False,
            acceptanceScope="plate_identity_boundary_inheritance_only" if kind == "background" else "static_visible_costume_resource_reference_only",
            motionFaceGeometryOriginalWrapperCsvOrFullChapterAccepted=False,
            expectedCompiledDifferencesToBindAfterRootRegistration=None)
        if model:
            case["resourceBinding"] = resources(model)
        else:
            background = read(P27BG/"p27-hall-bg-picture-only-draft.json")["changes"][0]["fields"]["bg_picture"]
            plate = read(DATA/"assets/catalog.json")["backgrounds"].get(background)
            case["expectedBackground"] = background
            case["backgroundBinding"] = dict(resource=background,available=plate is not None,
                route="/background/"+background.replace("/","%2F"),
                local=rec(DATA/"assets"/plate["url"]) if plate else None)
        if frozen:
            if model: assert case["resourceBinding"]["available"]
            else:
                assert case["backgroundBinding"]["available"]
                assert target_row["nativeRow"]["bg_picture"] == case["expectedBackground"]
                assert next(r for r in guard["rows"] if r["scenarioId"] == 9)["nativeRow"]["bg_picture"] == ""
        cases.append(case)
    return cases


def frozen_file_guards(cases):
    paths = {DATA/"manifest.json",DATA/"review/native-restoration.json",DATA/"README.md",
             DATA/"review/restoration-audits/royal-capital-20261111-repair/progress.json",ROOT/"data/story_studio/project.json"}
    for entry in read(DATA/"manifest.json")["scenes"]: paths.update([DATA/entry["path"],DATA/entry["reviewPath"]])
    for prefix in ["public/player","public/pairing","public/studio","lib"]:
        paths.update(p for p in (SITE/prefix).rglob("*") if p.is_file() and p.suffix in [".js",".ts",".json",".html",".css"])
    paths.update(DATA/("assets/"+n) for n in ["catalog.json","package.json","player/manifest.json","player/animation.json","player/motion_states.json"])
    paths.update(p for c in cases if c["model"] for p in (DATA/"assets/models"/c["model"]).rglob("*") if p.is_file())
    paths.update(ROOT/c["backgroundBinding"]["local"]["path"] for c in cases if not c["model"])
    paths.update(p for p in HERE.iterdir() if p.is_file())
    paths.update([R/"playback/serve.py",R/"playback/compile.mjs",R/"playback/index.html",R/"playback/canary.json"])
    # Historical request catalog/native hashes are intentionally not rebound as
    # original evidence. Their current formal files are guarded above. Original
    # request bytes and the exact decoded source frames remain immutable inputs.
    for case in cases:
        comparison=case["sourceComparison"]
        for value in comparison.values():
            if isinstance(value,dict) and "path" in value: paths.add(ROOT/value["path"])
        for frame in comparison.get("originalFullFrames",[]): paths.add(Path(frame["file"]))
    return [rec(p) for p in sorted(paths)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root-freeze-release", type=Path)
    args = parser.parse_args()
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19 and sorted(os.sched_getaffinity(0)) == [22, 23]
    output = args.output.resolve(); assert output.is_relative_to(HERE) and not output.exists()
    frozen = args.root_freeze_release is not None
    if frozen:
        release = read(args.root_freeze_release)
        assert release["rootAuthorizesFreshGuardBinding"] is True and release["browserAuthorized"] is False
        assert release["formalDataAndSourceWriteFrozen"] is True
        assert git(DATA,"rev-parse","HEAD") == release["dataHead"] and git(SITE,"rev-parse","HEAD") == release["sourceHead"]
    cases = assemble(frozen); output.mkdir()
    guards = frozen_file_guards(cases) if frozen else []
    for case in cases: write(output / (case["id"]+".json"), case)
    packets, scopes = [], []
    # Group only variants with the SAME scene/start/target. Grouping a whole
    # scene would accidentally authorize the cross-product of other starts and
    # examples, beyond the requested seven routes.
    for scene,start,target in sorted({(c["scene"],c["route"][0],c["target"]) for c in cases if c["model"]}):
        group = [c for c in cases if (c["scene"],c["route"][0],c["target"]) == (scene,start,target) and c["model"]]
        packet = dict(schema="stella.noninstallable.bounded-memory-packet.v2", installable=False,
                      registered=False, scopeApproved=False, freezeComplete=frozen, guardReceipts=guards,
                      examples=[dict(id=c["id"],changes=[dict(scenarioId=c["target"],expected=c["expectedNativeRow"],fields=c["fields"])]) for c in group])
        path = output / (f"s{scene}-start{start}-target{target}-memory-packet-PROPOSAL.json"); write(path,packet); packets.append(rec(path))
        scopes.append(dict(sceneId=scene,allowedStarts=sorted({c["route"][0] for c in group}),
            exampleIds=[c["id"] for c in group],allowedTargets=sorted({c["target"] for c in group}),allowedFields=["character"],
            packet=str(path.relative_to(R)),sha256=rec(path)["sha256"]))
    write(output/"registry-PROPOSAL.json", scopes)
    write(output/"execution-input-DRAFT.json", dict(status="root_binding_only_still_not_browser_authorized" if frozen else "informational_draft_not_frozen",
        scopeApproved=False,singleBrowserOwnerAssigned=False,browserAuthorized=False,freezeComplete=frozen,
        maxCases=7,dataHeadObserved=git(DATA,"rev-parse","HEAD"),sourceCommit=git(SITE,"rev-parse","HEAD"),
        cases=cases,requiredScopes=scopes,guardReceipts=guards,packets=packets,
        compiledBaselinesAndExactInheritedModelDiffsPending=True,
        policy=dict(singleProfile=True,newPagePerCase=True,closeOldPageBeforeNew=True,noRetries=True,
                    maxCompositorFramesPerStaticCapture=8,staticActorReadbacksPerCase=1,
                    expectedIdentityResponsesPerCharacterCase=4,maxResponseBytes=8*1024*1024,maxIdentityBytesPerCase=16*1024*1024)))
    if frozen:
        assert git(DATA,"rev-parse","HEAD") == release["dataHead"] and git(SITE,"rev-parse","HEAD") == release["sourceHead"]
        for row in guards: assert rec(ROOT/row["path"]) == row
    print(json.dumps(dict(output=str(output),cases=7,frozen=frozen,browserAuthorized=False,
                         executionInput=rec(output/"execution-input-DRAFT.json"))))


if __name__ == "__main__": main()
