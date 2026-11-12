"""Publish one prepared native music resource and its bounded asset index delta.

The normal exporter already established waveform length, native loop points and
the Opus readback. Reuse its two completed payloads and provenance; do not build
the project, decode source audio again, or enumerate/hash the existing library.
Only the new payloads and three already changed, explicitly named index entries
are materialized through AssetWriter. Story fields are outside this operation.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile

from story_studio.crowd_assets import AssetWriter


HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
ASSETS = ROOT / "story_crowd_data/assets"
CANDIDATE = R / "p30-bgm-kinpaku02-resource-candidate-20261113-v1"
RESOURCE = "bgm_adv_kinpaku02_cd2_18"
AUDIT = (ROOT / "story_crowd_data/review/restoration-audits/"
         "royal-capital-20261111-repair/p30-kinpaku02-resource-20261113-v1")


def json_document(path):
    return json.loads(path.read_text())


def record_json(path, document):
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")


def publish_file(source, destination):
    """Replace one known destination atomically on its own filesystem."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as incoming:
            shutil.copyfileobj(incoming, stream)
    os.replace(temporary, destination)


def main():
    if os.getpriority(os.PRIO_PROCESS, 0) != 19 or sorted(os.sched_getaffinity(0)) != [0, 1]:
        raise RuntimeError("Run this bounded integration with nice19 / CPU0,1")
    if (HERE / "installed-readback.json").exists():
        raise RuntimeError("Preserve the completed integration; do not rerun it")

    catalog_path, package_path = ASSETS / "catalog.json", ASSETS / "package.json"
    catalog_before, package_before = json_document(catalog_path), json_document(package_path)
    addition = json_document(CANDIDATE / "catalog-additions.json")["additions"]
    exported = json_document(CANDIDATE / "exported-files.json")
    assert len(catalog_before["music"]) == 18
    assert set(exported) == {f"music/{RESOURCE}.opus", f"music/{RESOURCE}.json"}
    assert sum(row["bytes"] for row in package_before["files"].values()) == package_before["bytes"]
    for table, rows in addition.items():
        assert not set(rows) & set(catalog_before[table]), table
    for name in exported:
        assert not (ASSETS / name).exists(), name

    HERE.mkdir(exist_ok=True)
    shutil.copyfile(catalog_path, HERE / "catalog.before.json")
    shutil.copyfile(package_path, HERE / "package.before.json")
    catalog = deepcopy(catalog_before)
    for table, rows in addition.items():
        catalog[table].update(deepcopy(rows))

    # These two previously accepted assets were installed incrementally after
    # the original package export. Reconcile only their known index entries,
    # retaining earlier provenance and linking the accepted delta explicitly.
    accepted_index_updates = {
        "player/transitions.json": "review/restoration-audits/royal-capital-20261111-repair/p30-cg-panel-entry-20261113-v1/scope.json",
        "pictures/ADV_still_006.png": "review/restoration-audits/royal-capital-20261111-repair/p30-still006-20261112-v1/root-acceptance.json",
    }
    for audit in accepted_index_updates.values():
        assert (ROOT / "story_crowd_data" / audit).is_file()

    with tempfile.TemporaryDirectory(prefix="stella-kinpaku02-", dir=ROOT / "artifacts") as temporary:
        writer = AssetWriter(Path(temporary), ROOT)
        writer.json("catalog.json", catalog)
        for name, prepared_record in exported.items():
            shutil.copyfile(CANDIDATE / "assets" / name, writer.target(name))
            writer.record(name)
            # AssetWriter indexes these two newly published files. The existing
            # exporter receipt supplies the unchanged native WAV provenance;
            # rereading that long source would not add a new acceptance fact.
            assert all(writer.files[name][key] == prepared_record[key] for key in ("bytes", "sha256"))
            writer.files[name] = deepcopy(prepared_record)
        for name in accepted_index_updates:
            shutil.copyfile(ASSETS / name, writer.target(name))
            writer.record(name)

        package = deepcopy(package_before)
        for name, record in writer.files.items():
            package["files"][name] = dict(package["files"].get(name, {}), **record)
            if name in accepted_index_updates:
                package["files"][name]["incremental_restoration_audit"] = accepted_index_updates[name]
        package["bytes"] = sum(row["bytes"] for row in package["files"].values())
        writer.json("package.json", package)

        expected_entries = {"catalog.json", *exported, *accepted_index_updates}
        changed_entries = {name for name in set(package["files"]) | set(package_before["files"])
                           if package["files"].get(name) != package_before["files"].get(name)}
        assert changed_entries == expected_entries
        assert {key: value for key, value in package.items() if key not in {"files", "bytes"}} == {
            key: value for key, value in package_before.items() if key not in {"files", "bytes"}}

        # Payloads precede the two descriptors. No existing waveform, native
        # script, review row, protected Studio project or unrelated asset moves.
        for name in [*exported, "catalog.json", "package.json"]:
            publish_file(writer.target(name), ASSETS / name)

    assert json_document(catalog_path) == catalog
    assert json_document(package_path) == package
    AUDIT.mkdir(exist_ok=True)
    for name in ["REPORT.md", "catalog-additions.json", "exported-files.json", "export-commands.json", "native-binding.json"]:
        shutil.copyfile(CANDIDATE / name, AUDIT / ("prepared-" + name))
    for name in ["REPORT.md", "scene-anchor-review.json"]:
        shutil.copyfile(R / "p30-bgm-kinpaku02-onset-review-20261113-v1" / name,
                        AUDIT / ("source-anchor-" + name))
    shutil.copyfile(Path(__file__), AUDIT / "integrate_resource.py")
    receipt = dict(status="one_native_music_resource_installed", resource=RESOURCE,
                   previousMusicCount=18, currentMusicCount=19,
                   catalogKeyAdditions=3, changedPackageEntries=sorted(changed_entries),
                   allOtherCatalogValuesUnchanged=True, allOtherPackageEntriesUnchanged=True,
                   baselineProjectProvenancePreserved=True, fullLibraryRebuilt=False,
                   storyFieldsChanged=False, sourceOnsetOrParametersAccepted=False,
                   audibleOrdinaryPlaybackAccepted=False, previewDecodePreviouslyVerified=True,
                   nativeDurationSeconds=8414915 / 44100,
                   nativeLoopSeconds=[266721 / 44100, 8414915 / 44100])
    record_json(HERE / "installed-readback.json", receipt)
    record_json(AUDIT / "installed-readback.json", receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
