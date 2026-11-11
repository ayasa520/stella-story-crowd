"""Record bounded source/API review and syntax checks without running a browser.

The current repository status is informational while ROOT owns ongoing formal
publications. No clean-worktree requirement is imposed on this read-only draft.
No command in this preparation script freezes or registers a memory proposal.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
R=HERE.parents[1]
ROOT=R.parents[3]
DATA=ROOT/"story_crowd_data"
SITE=ROOT/"artifacts/stella-site-repair-source/.sites-checkout"


def read(path):return json.loads(path.read_bytes())
def rec(path):
    raw=path.read_bytes();return dict(path=str(path.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(path,value):
    with path.open("x") as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")
def git(path,*args):return subprocess.check_output(["git","--no-optional-locks","-C",str(path),*args],text=True).strip()


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    paths=[SITE/("public/"+name) for name in ["pairing/viewer.js","pairing/model_resources.js","pairing/vendor/cubism4.min.js",
        "pairing/vendor/pixi.min.js","pairing/vendor/live2dcubismcore.min.js","studio/player.js","studio/player_scene.js",
        "studio/actor_placement.js","studio/background.js","studio/visual_frame_clock.js","player/player.html"]]
    paths += [R/"playback/compile.mjs",R/"playback/serve.py",R/"playback/index.html",R/"playback/canary.json"]
    sdk=(SITE/"public/pairing/vendor/cubism4.min.js").read_text()
    order='this.emit("beforeModelUpdate"),o.update(),o.loadParameters()'
    assert order in sdk
    viewer=(SITE/"public/pairing/viewer.js").read_text()
    assert "model.internalModel.on('beforeModelUpdate', () => this.renderPose())" in viewer
    placement=(SITE/"public/studio/actor_placement.js").read_text()
    assert "this.stage.clientHeight/(2*distance*Math.tan" in placement
    source_audit=dict(status="offline_primary_source_review_only",reviewer="/root/p24_background_final_qa",
        sourceCommit=git(SITE,"rev-parse","HEAD"),files=[rec(p) for p in paths],
        updateOrder=dict(exactSdkSequence=order,renderPoseHook="beforeModelUpdate",samplePoint="before original Core.update",postPoint="after original renderer return"),
        sourceFacts=["NativePlacedViewer uses original actor CH_top and camera, not generic fit-to-window",
            "Model loader uses Live2DModel.from and a shared texture lease; instrumentation returns the original factory Promise",
            "PIXI actor framebuffer is distinct from viewport CSS and from source-image bounds",
            "NativeBackground derives3:4 plane from original Quad, then fills measured9:16 stage",
            "Adapter wrapper default is100%x930;480x856 is an explicit QA outer preset",
            "compile.mjs applies only registered exact packet examples to private source objects before canonical compilePreview"],
        sameFrameLimit="Whole-stage asynchronous capture cannot be automatically equated with actor PNG/RGBA; readable exact rolling HUD tuple required",
        priorInstrument=rec(R/"visual-high/assembled-three-case-plan-20261112-v1/instrument.js"),
        priorLifecycle=rec(R/"visual-high/assembled-three-case-plan-20261112-v1/run-v1/browser-lifecycle.json"),
        noNewRuntimeEvidence=True,browserOpened=False,formalWrites=False)
    write(HERE/"source-api-audit.json",source_audit)
    checks=[]
    for path in sorted(HERE.glob("*.py")):
        ast.parse(path.read_text(),filename=str(path));checks.append(dict(kind="python_ast",file=path.name,passed=True))
    for name in ["instrument.js","capture_cases.js"]:
        result=subprocess.run(["node","--check",str(HERE/name)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        assert result.returncode==0,result.stdout.decode(errors="replace")
        checks.append(dict(kind="node_syntax",file=name,exitCode=result.returncode))
    inputs=read(HERE/"draft-v2/execution-input-DRAFT.json")
    assert len(inputs["cases"])==7 and len(inputs["requiredScopes"])==5
    assert not inputs["freezeComplete"] and not inputs["scopeApproved"] and not inputs["singleBrowserOwnerAssigned"] and not inputs["browserAuthorized"]
    assert sum(len(c["routeGuard"]["edges"]) for c in inputs["cases"])==15
    for scope in inputs["requiredScopes"]:
        matching=[c for c in inputs["cases"] if c["id"] in scope["exampleIds"]]
        assert len({(c["scene"],c["route"][0],c["target"]) for c in matching})==1
    for template in ["root-release-TEMPLATE.json","root-freeze-binding-TEMPLATE.json"]:
        value=read(HERE/template)
        assert not value.get("scopeApprovedByRoot") and not value.get("rootAuthorizesFreshGuardBinding")
    files=[p for p in HERE.rglob("*") if p.is_file() and p.name!="offline-preparation-receipt.json"]
    receipt=dict(status="drafts_prepared_for_root_peer_review_no_execution",executedBy="/root/p24_background_final_qa",
        createdUtc=datetime.now(timezone.utc).isoformat(),activeDraft=rec(HERE/"draft-v2/execution-input-DRAFT.json"),
        olderDraftV1Preserved=True,dataHeadObserved=git(DATA,"rev-parse","HEAD"),dataStatusInformationalOnly=git(DATA,"status","--porcelain"),
        sourceHeadObserved=git(SITE,"rev-parse","HEAD"),cases=7,naturalEdgeVisits=15,exactCharacterRegistryScopeProposals=5,
        files=[rec(p) for p in sorted(files)],syntaxChecks=checks,
        correctedSyntaxCommandPathAttempt=dict(oldPath="repair-20261112/.../capture_cases.js",result="MODULE_NOT_FOUND",actualSourcePathCheck="passed"),
        peerSelfAudit=dict(B1="case/global/body absolute deadlines and bounded cleanup; not runtime-validated",
            B2="identity encoding plus declared/decoded byte budgets; four bounded body reads per character",
            B3="return original factory Promise; detached diagnostic observation",
            B4="diagnostic exceptions swallowed/partial, originals recorded/rethrown; Page setup inside cleanup try"),
        pending=["ROOT independent peer review","tshirt02 formal availability if still missing","Fresh root-approved data/source freeze and expected-field binding",
            "ROOT registration of five exact character scopes","Canonical baselines and all inherited model-only consequences individually approved",
            "Separate sole-browser-owner authorization","Actual runtime/response/byte/geometry receipts","Delegated offline static-appearance review; same-frame stage matching may remain pending"],
        browserOpened=False,actualFreezeGenerated=False,registryChanged=False,formalDataSourceOrGitWrites=False,
        allApprovalTemplatesRemainFalse=True,compute=dict(nice=19,cpuAffinity=[22,23]))
    write(HERE/"offline-preparation-receipt.json",receipt)
    print(json.dumps(dict(receipt=rec(HERE/"offline-preparation-receipt.json"),activeDraft=receipt["activeDraft"],files=len(files),cases=7,routeEdges=15,scopes=5,browserOpened=False)))


if __name__=="__main__":main()
