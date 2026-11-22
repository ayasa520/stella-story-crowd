"""Adopt validated rough native batches into the local restoration library.

This is a local data operation. It neither commits nor publishes the library.
Existing scenes may only be updated when this importer previously installed
them and their complete native/review files still match that recorded version.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile

from story_studio.crowd_seed import digest, encoded
from .native_rough import OfficialDirectory, require, validate_document
from .native_resources import validate_resources


STATE_PATH = "review/native-restoration.json"


def read_object(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value, raw


def safe_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    require(path.is_relative_to(root), f"Batch path escapes its root: {name}")
    return path


def atomic_write(path: Path, raw: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".native-import-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def prepare_batch(staging: Path, target: Path, root: Path) -> tuple[dict, dict[str, bytes], dict[str, bytes]]:
    """Validate the complete batch and snapshot every file before any write.

    The ownership ledger is deliberately narrower than the library manifest.
    The first nineteen manually restored scenes are not adopted implicitly;
    matching IDs or text cannot grant this operation permission to rewrite them.
    Later batches can extend their own drafts, while any intervening human edit
    causes a conflict before the first data file is changed.
    """
    incoming, incoming_raw = read_object(staging / "manifest.json")
    require(incoming.get("structuralValidation") == "passed", "Batch is not structurally validated")
    require(incoming.get("restorationStatus") == "rough", "Only explicit rough batches are accepted")
    require(incoming.get("playbackValidation") == "not-run", "Unexpected batch playback status")
    for name, expected in incoming["files"].items():
        require(digest(safe_path(staging, name).read_bytes()) == expected, f"Staging changed: {name}")
    plan, _ = read_object(staging / "plan.json")
    spec = plan["directory"]
    directory_path = Path(spec["path"] if isinstance(spec, dict) else spec)
    directory_raw = (directory_path if directory_path.is_absolute() else root / directory_path).read_bytes()
    if isinstance(spec, dict) and spec.get("sha256"):
        require(digest(directory_raw) == spec["sha256"], "Official directory changed")
    directory = OfficialDirectory(json.loads(directory_raw), plan["chapterId"])
    manifest, manifest_raw = read_object(target / "manifest.json")
    state_file = target / STATE_PATH
    state, state_raw = read_object(state_file) if state_file.exists() else (dict(version=1, files={}, scenes={}, batches=[]), None)
    # Repair packets are derived from one installed snapshot. Validating only
    # the *current* ownership hashes would allow an older packet to overwrite
    # a newer, correctly installed repair. Bind these packets to the ownership
    # version they actually reviewed, before preparing any destination writes.
    source_ownership = plan.get("sourceOwnershipSha256")
    if source_ownership is not None:
        require(state_raw is not None and digest(state_raw) == source_ownership,
                "Repair snapshot is stale: installed ownership changed")
    previous = {entry["id"]: entry for entry in manifest["scenes"]}
    snapshots = {"manifest.json": manifest_raw}
    if state_raw is not None:
        snapshots[STATE_PATH] = state_raw
    # Reviewed repairs install explicit performance resources, unlike an initial
    # rough text assembly. Require their package to exist before adoption; a
    # structurally valid character field must not become a runtime model 404.
    # Snapshot the catalog with the script inputs so another asset integration
    # cannot change the validated resource inventory during this transaction.
    asset_catalog = None
    if source_ownership is not None:
        asset_catalog, asset_catalog_raw = read_object(target / "assets/catalog.json")
        snapshots["assets/catalog.json"] = asset_catalog_raw
    writes, additions, updates = {}, [], []
    result = deepcopy(manifest)
    next_state = deepcopy(state)
    for entry in incoming["scenes"]:
        identity = str(entry["id"])
        require(entry.get("reviewStatus") == "draft" and entry.get("readyForGame") is False,
                f"Batch must retain draft status: {identity}")
        paths = (f"native/scenes/{identity}.json", f"review/scenes/{identity}.json")
        require((entry["path"], entry["reviewPath"]) == paths, f"Unexpected scene paths: {identity}")
        document, _ = read_object(staging / paths[0])
        validate_document(document, entry["id"], directory)
        if asset_catalog is not None:
            validate_resources(document, asset_catalog, target / "assets", entry["id"])
        require(len(document["scenario_list"]) == entry["nodeCount"], f"Node count mismatch: {identity}")
        old_entry = previous.get(entry["id"])
        owned = identity in state["scenes"]
        require(old_entry is None or owned, f"Scene belongs to existing restoration work: {identity}")
        if owned:
            require(digest(encoded(old_entry)) == state["scenes"][identity], f"Scene summary was edited: {identity}")
            old_review, _ = read_object(target / paths[1])
            new_review, _ = read_object(staging / paths[1])
            old_ids = {row["stableKey"]: row["scenarioId"] for row in old_review["authoredArrayOrder"]}
            new_ids = {row["stableKey"]: row["scenarioId"] for row in new_review["authoredArrayOrder"]}
            # An incremental recording can add an alternate route before an
            # existing row in source-array order. That must not renumber rows
            # already exposed in the library or drop a previously restored
            # route. The builder's persisted allocation provides these IDs;
            # requiring them here also catches an accidentally rebuilt plan
            # that omitted its previousAllocation registry.
            require(all(new_ids.get(key) == number for key, number in old_ids.items()),
                    f"Previously installed rows were removed or renumbered: {identity}")
        for name in paths:
            destination = safe_path(target, name)
            if destination.exists():
                current = destination.read_bytes()
                require(owned and digest(current) == state["files"].get(name), f"Existing scene file was edited: {name}")
                snapshots[name] = current
            else:
                require(not owned, f"Previously installed scene file is missing: {name}")
            raw = safe_path(staging, name).read_bytes()
            writes[name] = raw
            next_state["files"][name] = digest(raw)
        next_state["scenes"][identity] = digest(encoded(entry))
        (updates if owned else additions).append(entry["id"])
        if owned:
            result["scenes"] = [deepcopy(entry) if row["id"] == entry["id"] else row for row in result["scenes"]]
        else:
            result["scenes"].append(deepcopy(entry))
    recordings = {row["id"]: row for row in result.get("recordings", [])}
    for row in incoming.get("recordings", []):
        if row["id"] in recordings:
            for field in ("bvid", "cid", "p"):
                require(recordings[row["id"]].get(field) == row.get(field), f"Recording identity changed: {row['id']}")
        else:
            recordings[row["id"]] = deepcopy(row)
    result["recordings"] = list(recordings.values())
    # A translated scene title also needs its existing directory override
    # updated: the online projection intentionally gives that saved name
    # precedence over the scene summary. Accept only explicit, preconditioned
    # display-text patches for importer-owned scenes in this very batch. This
    # cannot move directory nodes, alter routes/END flags, adopt baseline work,
    # or use a translated title to fabricate an executable connection.
    directory_updates = incoming.get("directoryEntryUpdates", [])
    require(isinstance(directory_updates, list), "Directory entry updates must be an array")
    batch_scenes = {entry["id"] for entry in incoming["scenes"]}
    for change in directory_updates:
        scene = change["sceneId"]
        require(scene in batch_scenes and str(scene) in state["scenes"],
                f"Directory text patch is outside owned batch: {scene}")
        fields, expected = change["fields"], change["expected"]
        require(bool(fields) and set(fields) <= {"name", "description"}, "Unsupported directory text fields")
        current = result.setdefault("studioDirectory", {}).setdefault("entries", {}).setdefault(f"scene:{scene}", {})
        for name, value in fields.items():
            require(name in expected and current.get(name) == expected[name],
                    f"Directory text was edited: {scene}:{name}")
            require(isinstance(value, str) and bool(value), "Directory display text must be nonempty")
            current[name] = value
    batch_id = digest(incoming_raw)[:20]
    report = dict(version=1, batchId=batch_id, staging=str(staging),
                  stagingManifestSha256=digest(incoming_raw), previousManifestSha256=digest(manifest_raw),
                  addedScenes=additions, updatedScenes=updates, importedNodeCount=sum(row["nodeCount"] for row in incoming["scenes"]),
                  librarySceneCount=len(result["scenes"]), libraryNodeCount=sum(row["nodeCount"] for row in result["scenes"]),
                  structuralValidation="passed", restorationStatus="rough", playbackValidation="not-run")
    if asset_catalog is not None:
        report["resourceValidation"] = "explicit-native-references-present"
    if batch_id not in next_state["batches"]:
        next_state["batches"].append(batch_id)
    writes[f"review/restoration-batches/{batch_id}.json"] = encoded(report)
    writes[STATE_PATH] = encoded(next_state)
    writes["manifest.json"] = encoded(result)
    return report, writes, snapshots


def install(staging: Path, target: Path, root: Path, *, apply: bool = False) -> dict:
    staging, target, root = staging.resolve(), target.resolve(), root.resolve()
    if not apply:
        report, _, _ = prepare_batch(staging, target, root)
        return dict(report, applied=False)
    # The exclusive lock serializes this importer's own writes. Snapshots are
    # rechecked immediately before applying; the manifest is written last, so a
    # partially written batch cannot appear as a complete library update.
    lock = target / ".native-restoration.lock"
    with lock.open("x"):
        try:
            report, writes, snapshots = prepare_batch(staging, target, root)
            for name, raw in snapshots.items():
                require(safe_path(target, name).read_bytes() == raw, f"Library changed during validation: {name}")
            for name, raw in writes.items():
                atomic_write(safe_path(target, name), raw)
            return dict(report, applied=True)
        finally:
            lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=Path("story_crowd_data"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(install(args.staging, args.target, args.root, apply=args.apply), ensure_ascii=False))


if __name__ == "__main__":
    main()
