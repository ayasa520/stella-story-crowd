"""Archive only the approved P28 batch-three character increment.

The complete observation manifest is historical, and its earlier installation
snapshot is not rewritten. A separate audit below verifies the actual 44 fields,
the seven confirmed-but-uninstalled rows and seven unresolved observations.
FFmpeg terminal logs use JSON raw strings with an exact UTF-8 byte round trip.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
R = Path(__file__).resolve().parent
DATA = ROOT / "story_crowd_data"
EVIDENCE = R / "visual-high/agent-reviewed-p28-identity-v1"
BASE = "ae12cae623f69200c241775774d86eaf483ffa0b"
DEST = DATA / "review/restoration-audits/royal-capital-20261111-repair/p28-batch3-identity-v49"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def audit_current():
    """Check current installation without turning a multi-actor witness into one model."""
    coverage_path = EVIDENCE / "full-part-coverage-manifest.json"
    full = read(coverage_path)
    natives, reviews, before = {}, {}, {}
    for scene in [10040001, 10040002, 10040003, 10040004]:
        name = f"native/scenes/{scene}.json"
        natives[scene] = {x["scenario_id"]: x for x in read(DATA / name)["scenario_list"]}
        reviews[scene] = read(DATA / f"review/scenes/{scene}.json")["scenarios"]
        original = json.loads(subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=DATA))
        before[scene] = {x["scenario_id"]: x for x in original["scenario_list"]}
    installed, uninstalled, pending, keys, ordinals = [], [], [], [], []
    models = Counter()
    for row in full["rows"]:
        scene, node = row["sceneId"], row["scenarioId"]
        review = reviews[scene][str(node)]
        assert review["stableKey"] == row["stableKey"] and review["sourceText"] == row["sourceText"]
        actual, model = natives[scene][node]["character"], row.get("selectedModel")
        if model:
            expected = "live2d/AC_" + model
            if actual:
                assert actual == expected
                installed.append(dict(sceneId=scene, scenarioId=node, character=actual, exactMatch=True))
                models[model] += 1
            else:
                assert natives[scene][node] == before[scene][node]
                uninstalled.append(dict(sceneId=scene, scenarioId=node, confirmedModel=expected, unchanged=True))
        else:
            assert natives[scene][node] == before[scene][node]
            pending.append(dict(sceneId=scene, scenarioId=node, status=row["status"], unchanged=True))
        keys.append((scene, node))
        ordinals.append(row["originalObservationOrdinal"])
    assert sorted(ordinals) == list(range(58)) and len(set(keys)) == 58
    assert (len(installed), len(uninstalled), len(pending)) == (44, 7, 7)
    assert models == Counter(subaru01=31, kadomon01=6, kan01=3, chin01=3, ton01=1)
    assert natives[10040003][4]["character"] == before[10040003][4]["character"] == ""
    outside = []
    for scene, nodes in natives.items():
        for node, actual in nodes.items():
            if (scene, node) not in keys:
                assert actual == before[scene][node]
                outside.append(dict(sceneId=scene, scenarioId=node, unchanged=True))
    assert len(outside) == 19
    report = dict(status="passed_current44_fields_match_confirmed_models", executedBy="/root/p24_background_final_qa",
                  reviewer="/root/p24_background_final_qa", rootExecutedThisAudit=False, baseCommit=BASE,
                  createdUtc=datetime.now(timezone.utc).isoformat(), coverage=dict(file=str(coverage_path), sha256=sha(coverage_path.read_bytes())),
                  allocatedObservations=58, uniqueOrdinals=58, confirmedCharacterModels=51,
                  installedCharacterFields=44, installedByModel=dict(models), installedExactMatches=installed,
                  confirmedButUninstalled=uninstalled, pendingUnchanged=pending,
                  multiActor10040003Node4UnchangedAndUnaccepted=True,
                  outsideP28ObservationScopeUnchanged=outside,
                  outsideScopeClassification=dict(titleNarration=14, otherPartsDialogue=5),
                  otherPartsDialogueNodesIn10040002=[14, 15, 16, 17, 18], otherParts=[29, 31, 33, 35],
                  excludedScopeAuthorizesActorClearing=False, nodeIdsStableKeysSourceTextAndOtherNativeFieldsProtected=True,
                  historicalCoverageBytesRewritten=False, motionFaceGeometryCsvOrFullPartAccepted=False,
                  newBrowserOpened=False, newPlaybackVisits=0, compute=dict(nice=19, cpuAffinity=[22, 23]))
    path = R / "p28-current-install-audit-v49.json"
    write(path, report)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-readback", type=Path, required=True)
    args = parser.parse_args()
    assert not DEST.exists(), "Never replace an archived receipt."
    current = audit_current()
    files = [(R / "visual-high/accepted-p28-batch3-identities-v49.json", "identity/accepted.json")]
    for name in ["batch3-fourteen-character-only-draft.json", "batch3-observations30to44-coverage.json",
                 "batch3-delivery-receipt.json", "batch3-model-reference-bindings.json",
                 "batch3-earlier-original-frame-index.json", "batch3-viewed-paths.json",
                 "batch3-street-versus-prison-original-variant-review.json"]:
        files.append((EVIDENCE / name, "identity/" + name))
    for name in ["batch3-original-s10040002-n10-298.000.png", "batch3-original-s10040003-n4-349.000.png",
                 "reference-kan01-anchor.png", "reference-chin01-anchor.png", "reference-ton01-anchor.png"]:
        files.append((EVIDENCE / name, "images/" + name))
    for name in ["v49-owner-repair.json", "v49-owner-dryrun.json", "v49-owner-apply.json", "v49-publication-audit.json",
                 "audit_installed_packet.py", current.name, Path(__file__).name]:
        files.append((R / name, "publication/" + name))
    files.append((args.root_readback, "publication/" + args.root_readback.name))
    for name in ["plan.json", "repair-report.json"]:
        files.append((R / "staging-v49-p28-batch3" / name, "staging/" + name))
    manifest = dict(schema="stella.exact_evidence_archive.v1", package="p28-batch3-identity-v49",
                    executedBy="/root/p24_background_final_qa", baseCommit=BASE, newCharacterFields=14,
                    batchModelCounts=dict(subaru01=7, kan01=3, chin01=3, ton01=1),
                    p28Installed=44, p28Confirmed=51, confirmedButUninstalled=7, pending=7,
                    multiActor10040003Node4UnchangedAndUnaccepted=True, fullPartIdentityAccepted=False,
                    noNewBrowserOrPlayback=True, noAssetsWebsiteOrRegistryChanges=True,
                    historicalReceiptsRewritten=False, copiedFiles=[], encodedRawLogs=[], existingSharedEvidence=[])
    for source, relative in files:
        raw = source.read_bytes()
        if source.suffix == ".json":
            assert b"data:image/" not in raw
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        assert target.read_bytes() == raw
        manifest["copiedFiles"].append(dict(source=str(source), archive=relative, bytes=len(raw), sha256=sha(raw),
                                            crlfLines=raw.count(b"\r\n") if source.suffix != ".png" else None))
    for source in sorted(EVIDENCE.glob("batch3-*.ffmpeg.log")):
        raw = source.read_bytes()
        relative = "raw-logs/" + source.name + ".json"
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        write(target, dict(source=str(source), bytes=len(raw), sha256=sha(raw), encoding="utf-8",
                           preservation="Exact raw string; CR and trailing whitespace remain escaped inside JSON.",
                           rawText=raw.decode("utf-8")))
        assert read(target)["rawText"].encode("utf-8") == raw
        manifest["encodedRawLogs"].append(dict(source=str(source), sourceBytes=len(raw), sourceSha256=sha(raw),
                                               archive=relative, archiveBytes=target.stat().st_size,
                                               archiveSha256=sha(target.read_bytes()), exactRawRoundTrip=True))
    for name in ["full-part-coverage-manifest.json", "outside-part28-native-row-source-scope-addendum.json",
                 "source-scene-recording-mapping-receipt.json"]:
        source = EVIDENCE / name
        archived = DEST.parent / "p28-batch2-identity-v48/identity" / name
        assert source.read_bytes() == archived.read_bytes()
        manifest["existingSharedEvidence"].append(dict(source=str(source), archive="../p28-batch2-identity-v48/identity/" + name,
                                                        bytes=source.stat().st_size, sha256=sha(source.read_bytes())))
    write(DEST / "MANIFEST.json", manifest)
    print(json.dumps(dict(status="archived", copiedFiles=len(files), rawLogs=len(manifest["encodedRawLogs"]),
                          manifestSha256=sha((DEST / "MANIFEST.json").read_bytes()),
                          crlfFiles=[x["archive"] for x in manifest["copiedFiles"] if x.get("crlfLines")]), indent=2))


if __name__ == "__main__":
    main()
