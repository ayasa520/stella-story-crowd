"""Prepare only a fresh false guard/decision epoch for the fixed scene edge.

The existing crowd_seed encoder owns importer summary digests. This binder
only hashes current inputs; it cannot approve an edge, compute publisher
values, call the editor, serialize patches, or modify either checkout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE.parent / "data-checkout"
SOURCE = ROOT / "artifacts/stella-site-repair-source/.sites-checkout"
sys.path.insert(0, str(ROOT))
from story_studio.crowd_seed import digest, encoded


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert os.sched_getaffinity(0) == {0, 1}
out = (HERE / args.output).resolve()
assert out.is_relative_to(HERE) and out != HERE and not out.exists()
intent_path = HERE / "intent.rootfalse.json"
intent = json.loads(intent_path.read_bytes())
assert intent["rootConfirmed"] is False and intent["executionAllowed"] is False
assert intent["sceneIds"] == [10090013, 10090014, 10090015]
candidate_path = Path(intent["sourceCandidate"]["path"])
assert sha(candidate_path) == intent["sourceCandidate"]["sha256"]
assert json.loads(candidate_path.read_bytes())["candidateEdge"] == intent["edge"]
for name, expected in intent["requiredSourceFileSha256"].items():
    assert sha(SOURCE / name) == expected
assert git(SOURCE, "merge-base", intent["requiredSourceFixCommit"], "HEAD") == intent["requiredSourceFixCommit"]
manifest = json.loads((DATA / "manifest.json").read_bytes())
ownership = json.loads((DATA / "review/native-restoration.json").read_bytes())
summaries = {entry["id"]: entry for entry in manifest["scenes"]}
assert len(ownership["scenes"]) == 121 and "10090015" not in ownership["scenes"]
assert all(digest(encoded(summaries[int(scene)])) == expected
           for scene, expected in ownership["scenes"].items())
assert [entry["id"] for entry in manifest["scenes"] if entry["sectionId"] == 1009] == intent["sceneIds"]
assert summaries[10020001]["sectionId"] == 1002
data_paths = {"manifest.json", "review/native-restoration.json", "assets/catalog.json", "assets/package.json"}
for prefix in ["native/scenes", "review/scenes", "review/restoration-batches"]:
    data_paths.update(str(path.relative_to(DATA)) for path in (DATA / prefix).glob("*.json"))
assert len([name for name in data_paths if name.startswith("native/scenes/")]) == 140
assert len([name for name in data_paths if name.startswith("review/scenes/")]) == 140
source_paths = [name for name in git(SOURCE, "ls-files", "-z").split("\0") if name]
assert all((SOURCE / name).is_file() for name in source_paths)
dist_paths = [str(path.relative_to(SOURCE / "dist")) for path in sorted((SOURCE / "dist").rglob("*")) if path.is_file()]
assert dist_paths, "A root-verified current build is required before binding"
guards = {
    "schema": "stella.directory-save-complete-guards.v1",
    "dataRoot": str(DATA), "sourceRoot": str(SOURCE),
    "dataHead": git(DATA, "rev-parse", "HEAD"), "dataStatus": git(DATA, "status", "--short"),
    "sourceHead": git(SOURCE, "rev-parse", "HEAD"), "sourceStatus": git(SOURCE, "status", "--short"),
    "sceneIds": intent["sceneIds"], "readOnlySceneIds": [10020001],
    "dataFiles": {name: sha(DATA / name) for name in sorted(data_paths)},
    "sourceFiles": {name: sha(SOURCE / name) for name in sorted(source_paths)},
    "distFiles": {name: sha(SOURCE / "dist" / name) for name in dist_paths},
    "nativeRepairSha256": sha(ROOT / "story_studio/recovery/native_repair.py"),
    "crowdSeedSha256": sha(ROOT / "story_studio/crowd_seed.py"),
    "ownedSummaryCount": 121, "ownedSummaryDigestMismatches": [],
    "offlineLoaderSha256": sha(HERE.parent / "adapter-preparation/offline-editor.mjs"),
    "serializerSha256": sha(HERE.parent / "prepare-publication-patches.py"),
    "intentSha256": sha(intent_path), "helperSha256": sha(HERE / "prepare.mjs"),
}
out.mkdir()
write(out / "guards.json", guards)
write(out / "decision.rootfalse.json", {
    "schema": "stella.episode5-directory-edge-root-decision.v1", "rootConfirmed": False,
    "intentPath": str(intent_path), "intentSha256": sha(intent_path),
    "guardsPath": str(out / "guards.json"), "guardsSha256": sha(out / "guards.json"),
    "helperSha256": sha(HERE / "prepare.mjs"), "approval": None,
    "scope": "One author directory edge; source owner native + manifest only; no formal writes",
})
print(json.dumps({"rootConfirmed": False, "decision": str(out / "decision.rootfalse.json"),
                  "decisionSha256": sha(out / "decision.rootfalse.json"), "guardsSha256": sha(out / "guards.json")}))
