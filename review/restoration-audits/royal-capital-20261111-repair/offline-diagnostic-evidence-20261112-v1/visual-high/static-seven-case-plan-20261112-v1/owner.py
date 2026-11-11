"""Run one later-approved case prefix, then close before indexing any pixels.

This file is a draft, not browser authorization. Root must separately freeze
formal bytes, register exact packets, approve every compiled model consequence
(including inherited nodes), and assign the sole browser owner. No retry,
registry mutation, server restart, formal write or runtime patch is implemented.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
ROOT = R.parents[3]
DATA = ROOT / "story_crowd_data"
SITE = ROOT / "artifacts/stella-site-repair-source/.sites-checkout"


def read(path): return json.loads(Path(path).read_bytes())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def rec(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    assert path.is_relative_to(ROOT)
    return dict(path=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha(raw))
def write(path,value):
    with path.open("x") as stream: json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")
def git(path,*args): return subprocess.check_output(["git","-C",str(path),*args],text=True).strip()


def processes():
    """Record only browser/CLI ownership; unrelated QQ crashpad is excluded."""
    rows=[]
    for path in Path("/proc").iterdir():
        if not path.name.isdigit(): continue
        try:
            exe=str((path/"exe").readlink())
            if exe.startswith("/opt/QQ/"): continue
            argv=(path/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace")
            browser="/chrome-canary/" in exe or Path(exe).name in ["chrome","chromium","chrome_crashpad_handler"]
            cli="node" in Path(exe).name and "playwright" in argv and "run-server" in argv
            if not (browser or cli): continue
            pid=int(path.name);fields=(path/"stat").read_text().rsplit(")",1)[1].split()
            rows.append(dict(pid=pid,ppid=int(fields[1]),startTicks=fields[19],exe=exe,
                             kind="browser" if browser else "cli",nice=os.getpriority(os.PRIO_PROCESS,pid),
                             cpus=sorted(os.sched_getaffinity(pid))))
        except (OSError,ProcessLookupError): pass
    return rows


def verify_guards(records):
    assert records, "No final byte guards"
    for row in records:
        path=(ROOT/row["path"]).resolve()
        assert path.is_relative_to(ROOT) and rec(path)==row,("Changed guard",row["path"])


def fetch(base,route,limit,expected=None):
    request=Request(base+route,headers={"Accept-Encoding":"identity"})
    with urlopen(request,timeout=40) as response:
        assert response.status==200 and response.url==base+route
        headers={k.lower():v for k,v in response.headers.items()}
        assert headers.get("content-encoding","identity").lower()=="identity"
        length=int(headers["content-length"]);assert 0<=length<=limit
        if expected: assert length==expected["bytes"]
        raw=response.read(length+1);assert len(raw)==length
    if expected: assert sha(raw)==expected["sha256"]
    return raw,headers


def preflight(base,cases):
    """Validate each distinct start independently and list every model consequence.

    Programs for two starts in one scene have different start/before metadata.
    Caching by scene alone would compare different baselines. Each candidate is
    compared with its exact scene/start baseline, and the complete model-only
    difference list must equal root's separately approved list without trimming
    inherited nodes to the authored target.
    """
    records=[]
    for spec in cases:
        route="/program?scene="+str(spec["scene"])+"&node="+str(spec["route"][0])
        before_raw,_=fetch(base,route,64*1024*1024);before=json.loads(before_raw)
        if spec["kind"]=="character":
            raw,_=fetch(base,route+"&nativePreview="+quote(spec["id"]),64*1024*1024)
            candidate=json.loads(raw)
            assert candidate["edges"]==before["edges"]
            assert {k:v for k,v in candidate.items() if k not in ["nodes","review_only_overrides"]}=={
                k:v for k,v in before.items() if k not in ["nodes","review_only_overrides"]}
            assert len(candidate["nodes"])==len(before["nodes"])
            differences=[]
            for current,old in zip(candidate["nodes"],before["nodes"]):
                assert current["id"]==old["id"]
                if current!=old:
                    keys={k for k in set(current)|set(old) if current.get(k)!=old.get(k)}
                    assert keys=={"model"} and current["id"].startswith(str(spec["scene"])+":")
                    differences.append(dict(node=current["id"],before=old.get("model"),after=current.get("model"),changedKeys=["model"]))
            assert differences==spec["approvedCompiledDifferences"] and differences
            actual=next(row for row in candidate["nodes"] if row["id"]==str(spec["scene"])+":"+str(spec["target"]))
            assert actual["model"]==spec["model"]
            override=candidate["review_only_overrides"]
            assert override["exampleId"]==spec["id"] and override["packetSha256"]==spec["packetSha256"] and override["persisted"] is False
            responses=spec["resourceBinding"]["responses"];assert len(responses)==4
        else:
            raw=before_raw;candidate=before;differences=[];responses=[]
            assert spec["approvedCompiledDifferences"]==[]
            plate=spec["backgroundBinding"];assert plate["available"]
            responses=[dict(role="background",route=plate["route"],local=plate["local"])]
        assert sha(raw)==spec["programSha256"]
        for a,b in zip(spec["route"],spec["route"][1:]):
            source,target=str(spec["scene"])+":"+str(a),str(spec["scene"])+":"+str(b)
            assert len([r for r in candidate["edges"] if r["source"]==source and r["target"]==target])==1
        served=[];total=0
        for row in responses:
            expected=row["local"];assert expected["bytes"]<=8*1024*1024
            payload,headers=fetch(base,row["route"],8*1024*1024,expected)
            assert payload==(ROOT/expected["path"]).read_bytes();total+=len(payload);assert total<=16*1024*1024
            served.append(dict(role=row["role"],url=base+row["route"],bytes=len(payload),sha256=sha(payload),headers=headers))
        records.append(dict(id=spec["id"],programSha256=sha(raw),programBytes=len(raw),compiledNodeCount=len(candidate["nodes"]),
                            compiledEdgeCount=len(candidate["edges"]),allModelDifferences=differences,
                            compiledRoute=[r for r in candidate["nodes"] if r["id"] in [str(spec["scene"])+":"+str(n) for n in spec["route"]]],
                            actualServedIdentityResponses=served))
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release",type=Path,required=True)
    parser.add_argument("--execute-approved-once",action="store_true")
    args=parser.parse_args()
    assert args.execute_approved_once
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    release=read(args.release)
    assert release["scopeApprovedByRoot"] is True and release["singleBrowserOwnerAssignedByRoot"] is True
    assert release["browserOwner"]=="/root/p24_background_final_qa"
    frozen=(ROOT/release["frozenExecutionInput"]["path"]).resolve()
    assert frozen.is_relative_to(HERE) and rec(frozen)==release["frozenExecutionInput"]
    inputs=read(frozen);assert inputs["freezeComplete"] and inputs["maxCases"]==7
    ids=release["selectedCaseIds"];assert 1<=len(ids)<=7
    assert ids==[c["id"] for c in inputs["cases"][:len(ids)]]
    cases=inputs["cases"][:len(ids)]
    assert all(c["approvedCompiledDifferences"] is not None and c["programSha256"] for c in cases)
    base=release["baseURL"];assert re.fullmatch(r"http://127\.0\.0\.1:\d+",base)
    session=release["session"];assert re.fullmatch(r"static-seven-[a-z0-9-]+",session)
    output=(HERE/release["freshOutputDirectory"]).resolve()
    assert output.is_relative_to(HERE) and not output.exists();output.mkdir()
    registry=R/"playback/approved-memory-previews.json"
    lifecycle=dict(session=session,ownerPid=os.getpid(),release=rec(args.release),frozenInput=rec(frozen),
                   before=processes(),commands=[],browserOpened=False,failure=None)
    opened=False;registry_before=None;summary=None
    def call(arguments,label,timeout):
        argv=["playwright-cli","-s="+session,*arguments]
        try:
            result=subprocess.run(argv,cwd=SITE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
            raw,code=result.stdout,result.returncode
        except subprocess.TimeoutExpired as error:
            raw,code=error.stdout or b"",None
        path=output/(label+".txt");path.write_bytes(raw)
        lifecycle["commands"].append(dict(argv=argv,exitCode=code,log=rec(path)))
        print(json.dumps(dict(step=label,exitCode=code,log=str(path))),flush=True)
        assert code==0,("CLI failed or timed out; do not reopen",label,code)
        return raw.decode(errors="replace")
    try:
        assert not lifecycle["before"]
        verify_guards(inputs["guardReceipts"])
        assert git(DATA,"rev-parse","HEAD")==inputs["dataHeadObserved"] and git(SITE,"rev-parse","HEAD")==inputs["sourceCommit"]
        registry_before=rec(registry);scopes=read(registry)
        for scope in inputs["requiredScopes"]: assert scope in scopes
        health=json.loads(fetch(base,"/health",1024*1024)[0])
        assert health["kind"]=="stella-readonly-production-adapter" and health["siteRoot"]==str(SITE) and health["pid"]==release["adapterPid"]
        pid=health["pid"];server=Path("/proc")/str(pid)
        command=(server/"cmdline").read_bytes().replace(b"\0",b" ").decode()
        assert str(R/"playback/serve.py") in command and str(SITE) in command
        assert os.getpriority(os.PRIO_PROCESS,pid)==19 and set(os.sched_getaffinity(pid))<={22,23}
        actual=preflight(base,cases);verify_guards(inputs["guardReceipts"])
        write(output/"preflight.json",dict(health=health,registry=registry_before,cases=actual,completeBeforeOpen=True))
        executable_cases=[dict(c,programBytes=next(r["programBytes"] for r in actual if r["id"]==c["id"])) for c in cases]
        config=dict(scopeApproved=True,singleBrowserOwnerAssigned=True,freezeComplete=True,baseURL=base,
                    outputRoot=str(output),cases=executable_cases,instrumentationSource=(HERE/"instrument.js").read_text())
        text=(HERE/"capture_cases.js").read_text();assert text.count("__APPROVED_EXECUTION__")==1
        runner=output/"approved-runner.js";runner.write_text(text.replace("__APPROVED_EXECUTION__",json.dumps(config,ensure_ascii=False)))
        subprocess.run(["node","--check",str(runner)],check=True)
        assert "(no browsers)" in call(["list"],"cli-before",30)
        assert not processes()
        opened=True;call(["open","about:blank","--config="+str(R/"playback/canary.json")],"open",60)
        lifecycle["browserOpened"]=True;lifecycle["live"]=processes()
        assert any(r["kind"]=="browser" for r in lifecycle["live"])
        assert all(r["nice"]==19 and set(r["cpus"])<={22,23} for r in lifecycle["live"])
        summary=json.loads(call(["--raw","run-code","--filename="+str(runner)],"capture",600))
        if summary["stoppedOnFirstFailure"]:raise RuntimeError("Partial capture preserved; no retry or later case")
    except Exception as error:
        lifecycle["failure"]=dict(type=type(error).__name__,message=str(error))
    finally:
        # Close immediately, before hashes, decoding, or offline image review.
        if opened:
            try:call(["close"],"close",60)
            except Exception as error:lifecycle["closeFailure"]=str(error)
        lifecycle["after"]=processes();lifecycle["taskCanaryAndCliOsZero"]=not lifecycle["after"]
        try:lifecycle["cliZero"]="(no browsers)" in call(["list"],"cli-after",30)
        except Exception as error:lifecycle["cliZero"]=False;lifecycle["listFailure"]=str(error)
        try:
            verify_guards(inputs["guardReceipts"])
            if registry_before:assert rec(registry)==registry_before
            assert rec(args.release)==lifecycle["release"] and rec(frozen)==lifecycle["frozenInput"]
            assert git(DATA,"rev-parse","HEAD")==inputs["dataHeadObserved"] and git(SITE,"rev-parse","HEAD")==inputs["sourceCommit"]
            lifecycle["guardAfter"]=True
        except Exception as error:lifecycle["guardAfter"]=False;lifecycle["guardFailure"]=str(error)
        write(output/"browser-lifecycle.json",lifecycle)
    if summary:write(output/"capture-summary.json",summary)
    if opened and lifecycle["taskCanaryAndCliOsZero"] and lifecycle["cliZero"]:
        subprocess.run([sys.executable,str(HERE/"index_pixels.py"),"--output",str(output)],check=True)
    print(json.dumps(dict(lifecycle=rec(output/"browser-lifecycle.json"),failure=lifecycle["failure"],
                         taskCanaryAndCliOsZero=lifecycle["taskCanaryAndCliOsZero"],cliZero=lifecycle["cliZero"],
                         guardAfter=lifecycle["guardAfter"],visualAccepted=False,automaticRetry=False)),flush=True)
    if lifecycle["failure"] or not lifecycle["guardAfter"] or not lifecycle["taskCanaryAndCliOsZero"] or not lifecycle["cliZero"]:sys.exit(1)


if __name__=="__main__":main()
