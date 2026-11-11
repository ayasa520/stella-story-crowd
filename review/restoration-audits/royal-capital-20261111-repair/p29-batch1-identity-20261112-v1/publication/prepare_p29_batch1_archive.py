"""Archive five P29 character fields with immutable source snapshots.

The old full98 manifest describes36 new drafts, one shared existing identity and
61 pending observations. Preserve those bytes and report the actual five-field
installation separately. Neither the27 outside-scope rows nor empty/occluded
observations authorize actor clearing. Historical reference acting is not signed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[4]
R=Path(__file__).resolve().parent
DATA=ROOT/"story_crowd_data"
EVIDENCE=R/"visual-high/agent-reviewed-p29-identity-v1"
BASE="a179b9b193830f963fe24b2fe5ce9f67204466cd"
DEST=DATA/"review/restoration-audits/royal-capital-20261111-repair/p29-batch1-identity-20261112-v1"


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")


def audit_current():
    """Match every confirmed/shared row and preserve pending/outside native rows."""
    full_path=EVIDENCE/"full-part98-coverage-manifest.json";full=read(full_path)
    packet_path=R/"visual-high/accepted-p29-batch1-identities-20261112-v1.json";packet=read(packet_path)
    changed={(r["sceneId"],r["scenarioId"]):r for r in packet["changes"]}
    current,before,reviews={},{},{}
    for scene in [10040002,10040051,10040052,10040053]:
        name=f"native/scenes/{scene}.json"
        current[scene]={r["scenario_id"]:r for r in read(DATA/name)["scenario_list"]}
        old=json.loads(subprocess.check_output(["git","--no-optional-locks","show",f"{BASE}:{name}"],cwd=DATA))
        before[scene]={r["scenario_id"]:r for r in old["scenario_list"]}
        reviews[scene]=read(DATA/f"review/scenes/{scene}.json")["scenarios"]
    installed,uninstalled,shared,pending,ordinals,keys=[],[],[],[],[],[]
    models=Counter()
    for row in full["decisions"]:
        scene,node=row["sceneId"],row["scenarioId"];key=(scene,node)
        review=reviews[scene][str(node)]
        assert review["stableKey"]==row["stableKey"] and review["sourceText"]==row["sourceText"]
        actual=current[scene][node]
        entry=dict(sceneId=scene,scenarioId=node,ordinal=row["ordinal"],stableKey=row["stableKey"],sourceText=row["sourceText"])
        if row["classification"]=="confirmed_identity_new_field":
            expected="live2d/AC_"+row["candidateModel"]
            if key in changed:
                assert actual["character"]==expected==changed[key]["fields"]["character"]
                installed.append(dict(entry,character=expected,exactMatch=True));models[row["candidateModel"]]+=1
            else:
                assert actual==before[scene][node] and not actual["character"]
                uninstalled.append(dict(entry,confirmedCharacter=expected,unchanged=True))
        elif row["classification"]=="already_installed_identity_reconfirmed":
            expected="live2d/AC_"+row["candidateModel"]
            assert actual==before[scene][node] and actual["character"]==expected
            shared.append(dict(entry,character=expected,unchanged=True))
        else:
            assert actual==before[scene][node]
            pending.append(dict(entry,classification=row["classification"],unchanged=True))
        keys.append(key);ordinals.append(row["ordinal"])
    assert sorted(ordinals)==list(range(98)) and len(set(keys))==98
    assert (len(installed),len(uninstalled),len(shared),len(pending))==(5,31,1,61)
    assert models==Counter(subaru01=5)
    outside=[]
    for row in full["outsidePart29ObservationScope"]:
        scene,node=row["sceneId"],row["scenarioId"]
        assert current[scene][node]==before[scene][node]
        outside.append(dict(sceneId=scene,scenarioId=node,classification=row["classification"],unchanged=True))
    assert len(outside)==27 and sum(len(v) for v in current.values())==125
    result=dict(status="passed5_new_installed31_uninstalled1_shared61_pending",executedBy="/root/p24_background_final_qa",
        reviewer="/root/p24_background_final_qa",rootExecutedThisAudit=False,baseCommit=BASE,createdUtc=datetime.now(timezone.utc).isoformat(),
        historicalCoverage=dict(file=str(full_path),sha256=sha(full_path.read_bytes())),
        acceptedPacket=dict(file=str(packet_path),sha256=sha(packet_path.read_bytes())),
        mappedNativeRows=125,allocatedObservations=98,uniqueOrdinals=98,reviewedObservations=98,
        confirmedNewCharacterDrafts=36,newlyInstalledCharacterFields=5,confirmedButUninstalled=31,preexistingSharedIdentity=1,
        totalInstalledAssignmentsWithinObservationScope=6,installedByModel=dict(models),installedExactMatches=installed,
        uninstalledConfirmedRows=uninstalled,sharedExistingRows=shared,pendingUnchanged=pending,
        pendingByClassification=dict(Counter(r["classification"] for r in pending)),outsideScopeUnchanged=outside,
        outsideScopeAuthorizesDeletionOrActorClearing=False,historicalSnapshotBytesRewritten=False,
        nodeIdsStableKeysAndSourceTextProtected=True,motionFaceGeometryOriginalCsvOrFullPartAccepted=False,
        newBrowserOpened=False,newPlaybackVisits=0,compute=dict(nice=19,cpuAffinity=[22,23]))
    path=R/"p29-current-install-batch1-v1.json";write(path,result);return path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--root-readback",type=Path,required=True);args=parser.parse_args()
    assert not DEST.exists(),"Never replace archived bytes"
    current=audit_current()
    files=[(R/"visual-high/accepted-p29-batch1-identities-20261112-v1.json","identity/accepted.json")]
    for name in ["batch1-five-character-only-draft.json","batch1-first15-coverage.json","batch1-first15-direct-review-receipt.json",
        "batch1-delivery-receipt.json","subaru01-assembled-original-binding.json","subaru01-current-catalog-row.json",
        "subaru01-original-controller.json","source-snapshot-provenance.json","p29-scene-recording-mapping.json",
        "full-part98-coverage-manifest.json","full-part98-delivery-receipt.json","full-part-current-source-snapshot-provenance.json"]:
        files.append((EVIDENCE/name,"identity/"+name))
    # Archive original raw snapshots, including the pre-publication source and
    # later full98 base snapshots; do not normalize their historical differences.
    for folder in ["source-snapshots","full-part-source-snapshots"]:
        files.extend((p,folder+"/"+p.name) for p in sorted((EVIDENCE/folder).iterdir()) if p.is_file())
    for name in ["p29-batch1-root-model-binding-v1.json","p29-batch1-root-reference-preflight-v1.json",
        "p29-batch2-root-reference-preflight-v1.json","p29-remaining-identities-root-preflight-v1.json",
        "root_p29_remaining_identity_preflight_v1.py","audit_installed_packet.py","p29-batch1-owner-repair-v1.json",
        "p29-batch1-owner-dryrun-v1.json","p29-batch1-owner-apply-v1.json","p29-batch1-publication-audit-v1.json",current.name,Path(__file__).name]:
        files.append((R/name,"publication/"+name))
    files.append((args.root_readback,"publication/"+args.root_readback.name))
    for name in ["plan.json","repair-report.json"]:
        files.append((R/"staging-p29-batch1-20261112-v1"/name,"staging/"+name))
    manifest=dict(schema="stella.exact_evidence_archive.v1",package="p29-batch1-identity-20261112-v1",executedBy="/root/p24_background_final_qa",
        baseCommit=BASE,newCharacterFields=5,model="subaru01",reviewed98=True,newConfirmedDrafts=36,newInstalled=5,
        confirmedButUninstalled=31,preexistingSharedInstalled=1,pending=61,outsideScopeNativeRows=27,
        historicalCoverageSnapshotRewritten=False,motionFaceGeometryCsvOrFullPartAccepted=False,
        noNewBrowserPlaybackAssetsWebsiteOrRegistry=True,copiedFiles=[],existingSharedEvidence=[],localOnlyEvidence=[])
    for source,relative in files:
        raw=source.read_bytes()
        if source.suffix==".json":assert b"data:image/" not in raw,source
        target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);assert target.read_bytes()==raw
        manifest["copiedFiles"].append(dict(source=str(source),archive=relative,bytes=len(raw),sha256=sha(raw),crlfLines=raw.count(b"\r\n")))
    binding=read(EVIDENCE/"subaru01-assembled-original-binding.json")
    anchor=Path(binding["anchor"]["file"]);archived=DEST.parent/"p28-batch2-identity-v48/images/reference-subaru01-anchor.png"
    assert anchor.read_bytes()==archived.read_bytes() and sha(anchor.read_bytes())==binding["anchor"]["sha256"]
    manifest["existingSharedEvidence"].append(dict(source=str(anchor),archive="../p28-batch2-identity-v48/images/reference-subaru01-anchor.png",bytes=anchor.stat().st_size,sha256=sha(anchor.read_bytes())))
    manifest["localOnlyEvidence"].append(dict(binding["capture"],copied=False,reason="Historical raw capture with embedded pixels; exact anchor already archived. Body/face context is not a motion signature."))
    write(DEST/"MANIFEST.json",manifest)
    print(json.dumps(dict(status="archived",copiedFiles=len(files),copiedBytes=sum(x["bytes"] for x in manifest["copiedFiles"]),
        manifestSha256=sha((DEST/"MANIFEST.json").read_bytes()),crlfFiles=[x["archive"] for x in manifest["copiedFiles"] if x["crlfLines"]]),indent=2))


if __name__=="__main__":main()
