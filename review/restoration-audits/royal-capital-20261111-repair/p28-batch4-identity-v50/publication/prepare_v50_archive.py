"""Archive the last seven accepted P28 identities without accepting pending rows.

Historical observation coverage remains byte-identical. The current-install
supplement checks all 51 confirmed assignments and separately preserves the five
Reinhard requests, the multi-actor row and the no-visible-actor row. Source/model
bindings are copied from the accepted evidence, not inferred from speaker names.
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
BASE = "2a41abadf8448055941acfaa4ebd14f7d99ae5fb"
DEST = DATA / "review/restoration-audits/royal-capital-20261111-repair/p28-batch4-identity-v50"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def audit_current():
    """Keep all pending and outside-recording native rows exactly unchanged."""
    coverage_path = EVIDENCE / "full-part-coverage-manifest.json"
    full = read(coverage_path)
    natives, reviews, before = {}, {}, {}
    for scene in [10040001, 10040002, 10040003, 10040004]:
        name = f"native/scenes/{scene}.json"
        natives[scene] = {x["scenario_id"]: x for x in read(DATA / name)["scenario_list"]}
        reviews[scene] = read(DATA / f"review/scenes/{scene}.json")["scenarios"]
        original = json.loads(subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=DATA))
        before[scene] = {x["scenario_id"]: x for x in original["scenario_list"]}
    installed, pending, keys, ordinals = [], [], [], []
    models = Counter()
    for row in full["rows"]:
        scene, node = row["sceneId"], row["scenarioId"]
        review = reviews[scene][str(node)]
        assert review["stableKey"] == row["stableKey"] and review["sourceText"] == row["sourceText"]
        actual, model = natives[scene][node]["character"], row.get("selectedModel")
        if model:
            assert actual == "live2d/AC_" + model
            installed.append(dict(sceneId=scene, scenarioId=node, character=actual, exactMatch=True))
            models[model] += 1
        else:
            assert natives[scene][node] == before[scene][node]
            pending.append(dict(sceneId=scene, scenarioId=node, status=row["status"], unchanged=True))
        keys.append((scene, node))
        ordinals.append(row["originalObservationOrdinal"])
    assert sorted(ordinals) == list(range(58)) and len(set(keys)) == 58
    assert (len(installed), len(pending)) == (51, 7)
    assert models == Counter(subaru01=33, kadomon01=6, kan01=5, chin01=3, ton01=4)
    assert natives[10040003][4]["character"] == before[10040003][4]["character"] == ""
    assert natives[10040004][6] == before[10040004][6]
    outside = []
    for scene, nodes in natives.items():
        for node, actual in nodes.items():
            if (scene, node) not in keys:
                assert actual == before[scene][node]
                outside.append(dict(sceneId=scene, scenarioId=node, unchanged=True))
    assert len(outside) == 19
    report = dict(status="passed_all51_confirmed_fields_installed_with7_pending_retained",
                  executedBy="/root/p24_background_final_qa", reviewer="/root/p24_background_final_qa",
                  rootExecutedThisAudit=False, baseCommit=BASE, createdUtc=datetime.now(timezone.utc).isoformat(),
                  coverage=dict(file=str(coverage_path), sha256=sha(coverage_path.read_bytes())),
                  allocatedObservations=58, uniqueOrdinals=58, confirmedCharacterModels=51,
                  installedCharacterFields=51, installedByModel=dict(models), installedExactMatches=installed,
                  confirmedButUninstalled=[], pendingUnchanged=pending,
                  pendingCounts=dict(reinhardResourceReference=5, multiActor=1, noVisibleStageActor=1),
                  outsideP28ObservationScopeUnchanged=outside,
                  outsideScopeClassification=dict(titleNarration=14, otherPartsDialogue=5),
                  otherPartsDialogueNodesIn10040002=[14, 15, 16, 17, 18], otherParts=[29, 31, 33, 35],
                  excludedScopeAuthorizesActorClearing=False, nodeIdsStableKeysSourceTextAndOtherNativeFieldsProtected=True,
                  historicalCoverageBytesRewritten=False, motionFaceGeometryCsvOrFullPartAccepted=False,
                  newBrowserOpened=False, newPlaybackVisits=0, compute=dict(nice=19, cpuAffinity=[22, 23]))
    path = R / "p28-current-install-audit-v50.json"
    write(path, report)
    return path


def source_model_bindings():
    """Retain exact accepted frame and original-resource bindings with no new image review."""
    packet_path = R / "visual-high/accepted-p28-batch4-identities-v50.json"
    packet = read(packet_path)
    rows = []
    for change in packet["changes"]:
        evidence = change["evidence"]
        witness = evidence["selectedWitness"]
        frame = Path(witness["file"])
        assert sha(frame.read_bytes()) == witness["sha256"]
        rows.append(dict(sceneId=change["sceneId"], scenarioId=change["scenarioId"],
                         stableKey=change["stableKey"], sourceText=change["sourceText"],
                         model=change["fields"]["character"], selectedWitness=witness,
                         originalExtractedModelFiles=evidence.get("originalExtractedModelFiles"),
                         directlyViewedReferences=evidence.get("directlyViewedReferences"),
                         assembledReferenceBinding=evidence.get("assembledReferenceBinding")))
    path = R / "p28-batch4-source-model-bindings-v50.json"
    write(path, dict(executedBy="/root/p24_background_final_qa", derivedOnlyFromAcceptedEvidence=True,
                     packet=dict(file=str(packet_path), sha256=sha(packet_path.read_bytes())),
                     sourceFramesRehashed=7, newImagesViewed=False, bindings=rows,
                     motionFaceGeometryOrCsvAccepted=False))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-readback", type=Path, required=True)
    parser.add_argument("--resume-partial", action="store_true")
    args = parser.parse_args()
    # A preparation error may leave exact copies without a completed manifest.
    # Resume only that unpublished state, preserve the existing audit timestamp,
    # and compare every existing destination instead of replacing its bytes.
    if DEST.exists():
        assert args.resume_partial and not (DEST / "MANIFEST.json").exists()
        current = R / "p28-current-install-audit-v50.json"
        bindings = R / "p28-batch4-source-model-bindings-v50.json"
    else:
        current, bindings = audit_current(), source_model_bindings()
    files = [(R / "visual-high/accepted-p28-batch4-identities-v50.json", "identity/accepted.json")]
    for name in ["batch4-seven-character-only-draft.json", "batch4-observations45to57-coverage.json", "batch4-delivery-receipt.json"]:
        files.append((EVIDENCE / name, "identity/" + name))
    files.append((bindings, "identity/" + bindings.name))
    for name in ["v50-owner-repair.json", "v50-owner-dryrun.json", "v50-owner-apply.json", "v50-publication-audit.json",
                 "audit_installed_packet.py", current.name, Path(__file__).name]:
        files.append((R / name, "publication/" + name))
    files.append((args.root_readback, "publication/" + args.root_readback.name))
    for name in ["plan.json", "repair-report.json"]:
        files.append((R / "staging-v50-p28-batch4" / name, "staging/" + name))
    manifest = dict(schema="stella.exact_evidence_archive.v1", package="p28-batch4-identity-v50",
                    executedBy="/root/p24_background_final_qa", baseCommit=BASE, newCharacterFields=7,
                    batchModelCounts=dict(kan01=2, subaru01=2, ton01=3), p28Installed=51, p28Confirmed=51,
                    confirmedButUninstalled=0, pending=7, fullPartIdentityAccepted=False,
                    noNewBrowserOrPlayback=True, noAssetsWebsiteOrRegistryChanges=True,
                    historicalReceiptsRewritten=False, copiedFiles=[], existingSharedEvidence=[])
    for source, relative in files:
        raw = source.read_bytes()
        if source.suffix == ".json":
            assert b"data:image/" not in raw, source
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == raw, target
        else:
            target.write_bytes(raw)
        assert target.read_bytes() == raw
        manifest["copiedFiles"].append(dict(source=str(source), archive=relative, bytes=len(raw), sha256=sha(raw),
                                            crlfLines=raw.count(b"\r\n")))
    shared = [
        ("full-part-coverage-manifest.json", "../p28-batch2-identity-v48/identity/"),
        ("outside-part28-native-row-source-scope-addendum.json", "../p28-batch2-identity-v48/identity/"),
        ("source-scene-recording-mapping-receipt.json", "../p28-batch2-identity-v48/identity/"),
        ("batch3-model-reference-bindings.json", "../p28-batch3-identity-v49/identity/"),
        ("batch3-street-versus-prison-original-variant-review.json", "../p28-batch3-identity-v49/identity/"),
    ]
    for name, prefix in shared:
        source = EVIDENCE / name
        archived = DEST / (prefix + name)
        assert source.read_bytes() == archived.read_bytes()
        manifest["existingSharedEvidence"].append(dict(source=str(source), archive=prefix + name,
                                                        bytes=source.stat().st_size, sha256=sha(source.read_bytes())))
    write(DEST / "MANIFEST.json", manifest)
    print(json.dumps(dict(status="archived", copiedFiles=len(files),
                          manifestSha256=sha((DEST / "MANIFEST.json").read_bytes()),
                          crlfFiles=[x["archive"] for x in manifest["copiedFiles"] if x.get("crlfLines")]), indent=2))


if __name__ == "__main__":
    main()
