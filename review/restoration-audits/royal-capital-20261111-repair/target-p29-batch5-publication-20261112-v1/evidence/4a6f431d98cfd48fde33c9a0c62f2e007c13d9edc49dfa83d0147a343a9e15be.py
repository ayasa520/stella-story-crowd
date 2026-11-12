"""Audit the bounded v17-v20 data publication without editing native inputs."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from story_studio.recovery.native_resources import validate_resources


ROOT = Path(__file__).resolve().parents[4]
LIBRARY = ROOT / "story_crowd_data"
BASE = "eb0cacd57bf78555717c3d53d0781da3c0d67ac4"


def read(path):
    return json.loads(path.read_bytes())


def previous(name, base=BASE):
    return subprocess.check_output(["git", "show", f"{base}:{name}"], cwd=LIBRARY)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-commit", default=BASE)
    parser.add_argument("--expected-character", type=int, default=1422)
    parser.add_argument("--expected-background", type=int, default=143)
    parser.add_argument("--expected-motion", type=int, default=3)
    parser.add_argument("--expected-voice", type=int, default=7)
    parser.add_argument("--new-character", type=int, default=668)
    parser.add_argument("--new-background", type=int, default=12)
    parser.add_argument("--new-motion", type=int, default=0)
    parser.add_argument("--new-voice", type=int, default=0)
    args = parser.parse_args()
    manifest = read(LIBRARY / "manifest.json")
    state = read(LIBRARY / "review/native-restoration.json")
    catalog = read(LIBRARY / "assets/catalog.json")
    fields = dict.fromkeys(("character", "motion", "bg_picture", "bg_music", "voice"), 0)
    new_fields = dict.fromkeys(("character", "bg_picture", "motion", "voice"), 0)
    baseline_files = 0
    owned_nodes = 0

    # These batches only fill explicitly counted sparse performance fields.
    # Requiring empty-to-filled values preserves every earlier approved cue
    # and motion; accepting a new component cannot rewrite an existing one.
    # Comparing every
    # other property also protects node/branch identities, source array order,
    # transitions, text, commands and the manually accepted baseline scenes.
    for entry in manifest["scenes"]:
        path = LIBRARY / entry["path"]
        document = read(path)
        old = json.loads(previous(entry["path"], args.base_commit))
        validate_resources(document, catalog, LIBRARY / "assets", entry["id"])
        assert len(document["scenario_list"]) == entry["nodeCount"]
        if str(entry["id"]) not in state["scenes"]:
            for name in (entry["path"], entry["reviewPath"]):
                assert (LIBRARY / name).read_bytes() == previous(name, args.base_commit), name
                baseline_files += 1
            continue
        owned_nodes += len(document["scenario_list"])
        assert {k: v for k, v in document.items() if k != "scenario_list"} == {
            k: v for k, v in old.items() if k != "scenario_list"
        }, entry["path"]
        assert len(document["scenario_list"]) == len(old["scenario_list"])
        assert entry["reviewStatus"] == "draft" and entry["readyForGame"] is False
        for row, old_row in zip(document["scenario_list"], old["scenario_list"]):
            assert {k: v for k, v in row.items() if k not in new_fields} == {
                k: v for k, v in old_row.items() if k not in new_fields
            }, (entry["id"], row["scenario_id"])
            for field in fields:
                fields[field] += bool(row.get(field))
            for field in new_fields:
                if row.get(field) != old_row.get(field):
                    assert not old_row.get(field) and row.get(field)
                    new_fields[field] += 1
    for name, expected in state["files"].items():
        assert sha((LIBRARY / name).read_bytes()) == expected, name

    # Hash every newly added or changed packaged payload. Existing original
    # model payloads must remain byte-identical; only the aggregate catalog
    # and player inventories may change when these three models are appended.
    package = read(LIBRARY / "assets/package.json")["files"]
    old_package = json.loads(previous("assets/package.json", args.base_commit))["files"]
    assert set(old_package) <= set(package)
    changed_payloads = 0
    original_payloads = 0
    for name, spec in package.items():
        if spec == old_package.get(name):
            continue
        raw = (LIBRARY / "assets" / name).read_bytes()
        assert len(raw) == spec["bytes"] and sha(raw) == spec["sha256"], name
        if name in old_package:
            assert name in ("catalog.json", "player/animation.json", "player/manifest.json", "player/motion_states.json"), name
        source = spec.get("source")
        if source and spec.get("source_sha256"):
            path = Path(source)
            path = path if path.is_absolute() else ROOT / path
            assert sha(path.read_bytes()) == spec["source_sha256"], source
            original_payloads += 1
        changed_payloads += 1
    studio_sha = sha((ROOT / "data/story_studio/project.json").read_bytes())
    assert studio_sha == "ebd974d90f89088fa3a504c1f419ae01c352a24e6bd80209c5ec651295d38522"
    assert (len(state["scenes"]), owned_nodes, baseline_files) == (121, 4998, 38)
    assert fields == dict(character=args.expected_character, motion=args.expected_motion,
                          bg_picture=args.expected_background, bg_music=32, voice=args.expected_voice)
    assert new_fields == dict(character=args.new_character, bg_picture=args.new_background,
                              motion=args.new_motion, voice=args.new_voice)
    report = dict(status="passed", baseCommit=args.base_commit, scenes=len(manifest["scenes"]),
                  ownedNodes=owned_nodes, protectedBaselineFiles=baseline_files,
                  explicitFields=fields, newlyFilledFields=new_fields,
                  changedPayloadsHashed=changed_payloads,
                  originalSourcePayloadsHashed=original_payloads,
                  studioSha256=studio_sha, mainThreadViewedImages=False,
                  fullRestorationAccepted=False)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
