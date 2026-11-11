"""Archive the approved Roswaal identity increment without changing source receipts.

The archive deliberately separates immutable capture-time evidence from the
current installation audit. Historical guards describe f77434c and must never
be rewritten to describe the later data commit. Pixel-bearing compressed raw
captures stay local; their exact byte bindings remain available in the manifest.
"""

import collections
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
R = Path(__file__).resolve().parent
DATA = ROOT / "story_crowd_data"
BASE = "f77434c9fca7179fcd64043ee5a1c9254b3685ce"
REL = Path("review/restoration-audits/royal-capital-20261111-repair/p27-roswaal12-static-v47")
DEST = DATA / REL
PLAN = R / "visual-high/assembled-three-case-plan-20261112-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prior(name):
    return subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=DATA)


def current_audit():
    """Check all 127 observation identities, including every retained pending row.

    The old full-coverage snapshot remains an immutable historical classification.
    Only the twelve individually accepted Roswaal rows override its pending model
    result. Stable keys and Japanese source text come from the review document;
    the native document owns the actual resource assignment.
    """
    coverage_path = R / "visual-high/agent-reviewed-p27-identity-v1/full-part-coverage-manifest.json"
    coverage = read(coverage_path)
    accepted_path = R / "visual-high/accepted-p27-roswaal12-v47.json"
    accepted = read(accepted_path)
    overrides = {(x["sceneId"], x["scenarioId"]): x for x in accepted["changes"]}
    natives, reviews, originals = {}, {}, {}
    for scene in [10200006, 10200007]:
        name = f"native/scenes/{scene}.json"
        natives[scene] = {x["scenario_id"]: x for x in read(DATA / name)["scenario_list"]}
        originals[scene] = {x["scenario_id"]: x for x in json.loads(prior(name))["scenario_list"]}
        reviews[scene] = read(DATA / f"review/scenes/{scene}.json")["scenarios"]
    ordinals, keys, matches, pending = [], [], [], []
    models = collections.Counter()
    for row in coverage["rows"]:
        scene, node = row["sceneId"], row["scenarioId"]
        key = (scene, node)
        review = reviews[scene][str(node)]
        assert review["stableKey"] == row["stableKey"]
        assert review["sourceText"] == row["sourceText"]
        actual = natives[scene][node]["character"]
        expected = overrides[key]["fields"]["character"] if key in overrides else (
            "live2d/AC_" + row["selectedModel"] if row.get("selectedModel") else None
        )
        if expected:
            assert actual == expected, (key, actual, expected)
            models[expected] += 1
            matches.append(dict(sceneId=scene, scenarioId=node, character=actual,
                                ordinal=row["originalObservationOrdinal"], exactMatch=True))
        else:
            assert natives[scene][node] == originals[scene][node], key
            pending.append(dict(sceneId=scene, scenarioId=node, status=row["status"], unchanged=True))
        ordinals.append(row["originalObservationOrdinal"])
        keys.append(key)
    assert sorted(ordinals) == list(range(127)) and len(set(keys)) == 127
    assert len(matches) == 83 and len(pending) == 44
    excluded = coverage["structuralRowsOutsideAllocatedObservationScope"]
    assert len(excluded) == 8
    for row in excluded:
        assert natives[row["sceneId"]][row["scenarioId"]] == originals[row["sceneId"]][row["scenarioId"]]
    result = dict(status="passed_current83_character_assignments_equal_confirmed_models",
                  executedBy="/root/p24_background_final_qa", reviewer="/root/p24_background_final_qa",
                  rootExecutedThisAudit=False, createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  baseCommit=BASE, historicalCoverage=dict(file=str(coverage_path), sha256=sha(coverage_path.read_bytes())),
                  acceptedPacket=dict(file=str(accepted_path), sha256=sha(accepted_path.read_bytes())),
                  nativeRows=135, uniqueObservationOrdinals=127, nodeIdsStableKeysAndSourceTextProtected=True,
                  installedCharacterFields=83, models=dict(models), confirmedExactMatches=matches,
                  pendingUnchanged=pending, aliasPending=41, lateWipeOrBlurPending=3,
                  roswaalReferencePending=0, excludedRowsUnchanged=True,
                  excludedRowsAuthorizeActorClearing=False, titleNarrationExcludedRows=8,
                  newImagesDecoded=0, browserOpened=False, motionExpressionGeometryOrCsvSigned=False,
                  fullPartIdentityAccepted=False, fullRestorationAccepted=False,
                  compute=dict(nice=19, cpuAffinity=[22, 23]))
    path = R / "p27-current-install-audit-v47.json"
    write(path, result)
    return path


def main():
    assert not DEST.exists(), "Create a fresh archive; never replace frozen archive bytes."
    current = current_audit()
    files = [(R / "visual-high/accepted-p27-roswaal12-v47.json", "identity/accepted.json")]
    for name in ["roswaal12-character-only-draft.json", "roswaal12-individual-static-review-receipt.json",
                 "fresh-static-model-binding.json", "roswaal12-delivery-receipt.json"]:
        files.append((R / "visual-high/agent-reviewed-p27-roswaal-followup-v1" / name, "identity/" + name))
    for name in ["root-static-identity-preflight-20261112-v1.json", "root-static-identity-preflight-20261112-v1.py",
                 "v47-owner-dryrun.json", "v47-owner-apply.json", "v47-publication-audit.json",
                 "v47-root-readback.json", current.name, Path(__file__).name]:
        files.append((R / name, "publication/" + name))
    for name in ["PLAN.md", "owner.py", "capture_cases.js", "instrument.js", "index_pixels.py",
                 "prepare_guards.py", "offline-preparation-receipt.json", "model41-lock.json", "target-deep-guards.json",
                 "roswaal13-character-only-model41-v1.json"]:
        files.append((PLAN / name, "capture-plan/" + name))
    for name in ["execution-input.json", "root-compiled-scope-preflight.json", "root-authorized-release-v1.json",
                 "root-registration-receipt.json", "root-data-write-freeze-release-v1.json"]:
        files.append((PLAN / "freeze-v1" / name, "historical-freeze/" + name))
    for name in ["browser-lifecycle.json", "capture-summary.json", "pixel-index.json", "preflight.json",
                 "cli-before.txt", "cli-after.txt", "open.txt", "capture.txt"]:
        files.append((PLAN / "run-v1" / name, "capture/" + name))
    for name in ["FINAL-REVIEW.json", "REPORT.md", "final-freeze-recheck.json",
                 "roswaal13-static-reference-review.json", "normal-entry-review.json", "normal02-entry-review.json",
                 "geometry-final-observations.json", "earliest-readable-entry-observations.json",
                 "console-http-diagnostics.json", "inspection-index.json", "prepare_contacts.py"]:
        files.append((PLAN / "run-v1/offline-review-v1" / name, "offline-review/" + name))
    files.extend([
        (PLAN / "run-v1/pixels/roswaal13-character-only-model41-v1/actual-actor.png", "roswaal-static/actual-actor.png"),
        (PLAN / "run-v1/roswaal13-character-only-model41-v1-held.png", "roswaal-static/whole-stage-held.png"),
    ])
    local_only = list((PLAN / "run-v1").glob("*-raw.json.gz"))
    local_only += [PLAN / "run-v1/close.txt", PLAN / "run-v1/pixels/roswaal13-character-only-model41-v1/actual-actor-bottom-up.rgba"]
    manifest = dict(schema="stella.exact_evidence_archive.v1", package="p27-roswaal12-static-v47",
                    executedBy="/root/p24_background_final_qa", installationScope="12 character fields only",
                    baseCommit=BASE, historicalCaptureDataCommit=BASE,
                    historicalCaptureSourceCommit="37232806a8180375a4b7a178e27157bb16d12201",
                    rawPixelBase64Copied=False, historicalReceiptsRewritten=False,
                    p28NewFieldsInstalled=0, butlerFieldsAccepted=False,
                    motionFaceGeometryCsvOrChapterAccepted=False,
                    cumulativeRestorationPlaybackVisits=207, experimentalCaptureVisitsNotAdded=9,
                    copiedFiles=[], localOnlyEvidence=[])
    for source, relative in files:
        raw = source.read_bytes()
        if source.suffix == ".json":
            assert b"data:image/" not in raw, source
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        assert target.read_bytes() == raw
        manifest["copiedFiles"].append(dict(source=str(source), archive=relative, bytes=len(raw), sha256=sha(raw),
                                            crlfLines=raw.count(b"\r\n") if source.suffix != ".png" else None))
    for source in local_only:
        raw = source.read_bytes()
        manifest["localOnlyEvidence"].append(dict(source=str(source), bytes=len(raw), sha256=sha(raw),
                                                  copied=False, reason="Raw pixels, redundant close text, or raw RGBA remain local; indexed by exact digest."))
    write(DEST / "MANIFEST.json", manifest)
    print(json.dumps(dict(status="archived", path=str(REL), copiedFiles=len(files),
                          copiedBytes=sum(x["bytes"] for x in manifest["copiedFiles"]),
                          manifestSha256=sha((DEST / "MANIFEST.json").read_bytes()),
                          crlfFiles=[x["archive"] for x in manifest["copiedFiles"] if x.get("crlfLines")]), indent=2))


if __name__ == "__main__":
    main()
