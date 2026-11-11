"""Preserve P28 batch-two evidence and audit its narrow current installation.

Source FFmpeg logs contain carriage returns and trailing spaces. They are stored
as JSON raw strings, then decoded and compared with the original bytes. This
keeps Git whitespace normalization from altering historical process evidence.
The historical full-coverage manifest still describes its earlier 15-installed
snapshot; the current audit below records the distinct 30-installed state.
"""

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
BASE = "72bace5056b95eeb694caa15ac227eb6ca3670c7"
DEST = DATA / "review/restoration-audits/royal-capital-20261111-repair/p28-batch2-identity-v48"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def audit_current():
    """Keep confirmation, installation and outside-recording scope independent."""
    full = read(EVIDENCE / "full-part-coverage-manifest.json")
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
        actual = natives[scene][node]["character"]
        model = row.get("selectedModel")
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
    assert (len(installed), len(uninstalled), len(pending)) == (30, 21, 7)
    assert models == Counter(subaru01=24, kadomon01=6)
    outside = []
    for scene, nodes in natives.items():
        for node, actual in nodes.items():
            if (scene, node) not in keys:
                assert actual == before[scene][node]
                outside.append(dict(sceneId=scene, scenarioId=node, unchanged=True))
    assert len(outside) == 19
    report = dict(status="passed_current30_fields_match_confirmed_models", executedBy="/root/p24_background_final_qa",
                  reviewer="/root/p24_background_final_qa", rootExecutedThisAudit=False, baseCommit=BASE,
                  createdUtc=datetime.now(timezone.utc).isoformat(), allocatedObservations=58, uniqueOrdinals=58,
                  confirmedCharacterModels=51, installedCharacterFields=30, installedByModel=dict(models),
                  installedExactMatches=installed, confirmedButUninstalled=uninstalled, pendingUnchanged=pending,
                  outsideP28ObservationScopeUnchanged=outside, outsideScopeClassification=dict(titleNarration=14, otherPartsDialogue=5),
                  otherPartsDialogueNodesIn10040002=[14, 15, 16, 17, 18],
                  otherParts=[29, 31, 33, 35], excludedScopeAuthorizesActorClearing=False,
                  nodeIdsStableKeysSourceTextAndOtherNativeFieldsProtected=True,
                  historicalCoverageBytesRewritten=False, motionFaceGeometryCsvOrFullPartAccepted=False,
                  newBrowserOpened=False, newPlaybackVisits=0, compute=dict(nice=19, cpuAffinity=[22, 23]))
    path = R / "p28-current-install-audit-v48.json"
    write(path, report)
    return path


def main():
    assert not DEST.exists(), "Never replace an archived receipt."
    current = audit_current()
    files = [(R / "visual-high/accepted-p28-batch2-identities-v48.json", "identity/accepted.json")]
    for name in ["batch2-fifteen-character-only-draft.json", "batch2-observations15to29-coverage.json",
                 "batch2-delivery-receipt.json", "batch2-model-reference-bindings.json",
                 "batch2-earlier-original-frame-index.json", "batch2-viewed-paths.json",
                 "full-part-coverage-manifest.json", "full-part-delivery-receipt.json",
                 "outside-part28-native-row-source-scope-addendum.json", "source-scene-recording-mapping-receipt.json"]:
        files.append((EVIDENCE / name, "identity/" + name))
    for name in ["batch2-original-s10040002-n4-228.000.png", "batch2-original-s10040002-n8-270.500.png",
                 "reference-subaru01-anchor.png", "reference-kadomon01-anchor.png"]:
        files.append((EVIDENCE / name, "images/" + name))
    for name in ["v48-owner-repair.json", "v48-owner-dryrun.json", "v48-owner-apply.json", "v48-publication-audit.json",
                 "v48-root-readback-v2.json", "v48-root-readback-count-correction.json", "audit_installed_packet.py",
                 current.name, Path(__file__).name]:
        files.append((R / name, "publication/" + name))
    for name in ["plan.json", "repair-report.json"]:
        files.append((R / "staging-v48-p28-batch2" / name, "staging/" + name))
    manifest = dict(schema="stella.exact_evidence_archive.v1", package="p28-batch2-identity-v48",
                    executedBy="/root/p24_background_final_qa", baseCommit=BASE, newCharacterFields=15,
                    batchModelCounts=dict(subaru01=13, kadomon01=2), p28Installed=30, p28Confirmed=51,
                    confirmedButUninstalled=21, pending=7, fullPartIdentityAccepted=False,
                    noNewBrowserOrPlayback=True, noAssetsWebsiteOrRegistryChanges=True,
                    historicalReceiptsRewritten=False, copiedFiles=[], encodedRawLogs=[])
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
    for source in sorted(EVIDENCE.glob("batch2-*.ffmpeg.log")):
        raw = source.read_bytes()
        relative = "raw-logs/" + source.name + ".json"
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        record = dict(source=str(source), bytes=len(raw), sha256=sha(raw), encoding="utf-8",
                      preservation="Exact raw string; CR and trailing whitespace remain escaped inside JSON.",
                      rawText=raw.decode("utf-8"))
        write(target, record)
        assert read(target)["rawText"].encode("utf-8") == raw
        manifest["encodedRawLogs"].append(dict(source=str(source), sourceBytes=len(raw), sourceSha256=sha(raw),
                                               archive=relative, archiveBytes=target.stat().st_size,
                                               archiveSha256=sha(target.read_bytes()), exactRawRoundTrip=True))
    rootproof = R / "root-static-identity-preflight-20261112-v1.json"
    manifest["existingRootPreflight"] = dict(source=str(rootproof), sha256=sha(rootproof.read_bytes()),
                                            archive="../p27-roswaal12-static-v47/publication/" + rootproof.name,
                                            scope="193 references; this increment installs only P28 batch two.")
    write(DEST / "MANIFEST.json", manifest)
    print(json.dumps(dict(status="archived", path=str(DEST.relative_to(DATA)), copiedFiles=len(files),
                          rawLogs=len(manifest["encodedRawLogs"]), manifestSha256=sha((DEST / "MANIFEST.json").read_bytes()),
                          crlfFiles=[x["archive"] for x in manifest["copiedFiles"] if x.get("crlfLines")]), indent=2))


if __name__ == "__main__":
    main()
