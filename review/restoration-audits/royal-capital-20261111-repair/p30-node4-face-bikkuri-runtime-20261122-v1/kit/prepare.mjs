// One formal baseline and one controlled native face alias, both projected
// by the unchanged complete Worker. Preserve original raw/status/headers first.
// No program field is rewritten, no before is seeded and no request is retried.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,realpath} from 'node:fs/promises';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {cpuGate} from './node-guards.mjs';
await cpuGate();
const here=new URL('./',import.meta.url),root=new URL('../../../',here);
const sha=b=>createHash('sha256').update(b).digest('hex');
const bindingBytes=await readFile(new URL('frozen/binding.json',here)),binding=JSON.parse(bindingBytes);
assert.equal(await realpath(process.execPath),await realpath(binding.tools.node.binaryPath));
assert.equal(sha(await readFile(process.execPath)),binding.tools.node.sha256);
const releaseBytes=await readFile(binding.preparationRelease.path),release=JSON.parse(releaseBytes);
assert.equal(sha(releaseBytes),binding.preparationRelease.sha256);
assert.equal(release.rootConfirmed,true);assert.equal(release.apiPreparationAuthorized,true);
assert.equal(release.browserLaunchAuthorized,false);
assert.equal(release.controlledNativeCandidateAuthorized,true);
assert.equal(binding.nativeOnlyOverlay,true);assert.equal(binding.controlledNativeCandidate,true);
assert.equal(binding.noProgramMutation,true);
assert.deepEqual(binding.plans.map(p=>p.id),['p30-node4-face-bikkuri-only']);
assert.deepEqual(globalThis[Symbol.for('stella.p30.face-bikkuri.native-transport')],{
  kind:'native-only-controlled-face',bindingSha256:sha(bindingBytes),
  caseId:binding.plans[0].id,alias:binding.plans[0].alias});
assert.equal(process.env.STELLA_HOSTING,undefined);
const verify=async()=>{for(const[path,digest]of Object.entries(binding.fileGuards))
  assert.equal(sha(await readFile(path.startsWith('/')?path:new URL(path,root))),digest,path);};
await verify();
const workersModule=new URL('workers-private.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'
  ?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const out=new URL('prepared/',here);await mkdir(out);
const save=async(name,value)=>writeFile(new URL(name,out),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const backgroundTasks=[],backgroundErrors=[];
const invoke=(path,request)=>worker.fetch(new Request('http://127.0.0.1:5198'+path,{method:'POST',
  headers:{'content-type':'application/json'},body:JSON.stringify(request)}),env,{waitUntil(p){
    backgroundTasks.push(Promise.resolve(p).catch(error=>{
      backgroundErrors.push({error:String(error),stack:error?.stack||''});console.error(error);
    }));
  }});
async function finishBackground(){
  let index=0;
  for(let round=0;round<32;round++){
    const batch=backgroundTasks.slice(index);if(!batch.length){assert.deepEqual(backgroundErrors,[]);return;}
    index=backgroundTasks.length;await Promise.allSettled(batch);
  }
  throw Error('Ordinary preparation background diagnostics did not quiesce');
}
// Compare the original objects directly: deleting metadata or reconstructing
// before would hide extra differences. This is the existing K5 leaf comparator.
function differences(left,right,path=''){
  if(left!==null&&right!==null&&typeof left==='object'&&typeof right==='object'){
    assert.equal(Array.isArray(left),Array.isArray(right),path);
    assert.deepEqual(Object.keys(left),Object.keys(right),path);
    return Object.keys(left).flatMap(key=>differences(left[key],right[key],path+'/'+key));
  }
  return Object.is(left,right)?[]:[{path,before:left,after:right}];
}
const plan=binding.plans[0],request={id:plan.start,baseSha:plan.alias,choices:{}};
assert.equal(plan.aliasIsGitCommit,false);assert.notEqual(plan.alias,binding.finalDataHead);
let stage='formal-baseline';
try{
  const baselineRequest={id:plan.start,baseSha:binding.finalDataHead,choices:{}};
  await save('baseline.request.json',baselineRequest);
  const baselineReply=await invoke('/api/player/prepare',baselineRequest),baselineRaw=await baselineReply.text();
  await writeFile(new URL('baseline.raw.json.gz',out),gzipSync(baselineRaw),{flag:'wx'});
  const baselineReceipt={request:baselineRequest,status:baselineReply.status,headers:Object.fromEntries(baselineReply.headers),
    rawResponseSha256:sha(baselineRaw),rawResponseBytes:Buffer.byteLength(baselineRaw),
    browserStarted:false,serverStarted:false,programMutated:false};
  await save('baseline.http.json',baselineReceipt);
  if(baselineReply.status!==200){
    if(baselineReply.status===422){
      const diagnostic=await invoke('/api/resolve',baselineRequest),text=await diagnostic.text();
      await writeFile(new URL('baseline.resolve.json.gz',out),gzipSync(text),{flag:'wx'});
      baselineReceipt.resolve={status:diagnostic.status,headers:Object.fromEntries(diagnostic.headers),sha256:sha(text),bytes:Buffer.byteLength(text)};
    }
    await save('baseline.receipt.json',baselineReceipt);
    throw Error('Formal baseline prepare '+baselineReply.status+'; retain original raw and stop without retry/seed');
  }
  assert.ok(Buffer.byteLength(baselineRaw)<=25000000);
  const baseline=JSON.parse(baselineRaw);
  assert.equal(baseline.headSha,binding.finalDataHead);assert.equal(baseline.start,plan.start);
  assert.equal(baseline.revision,parseInt(binding.finalDataHead.slice(0,12),16));
  assert.equal(baseline.nodes.length,binding.allLibraryNodes);assert.equal(baseline.edges.length,binding.allLibraryEdges);
  assert.equal(baseline.nodes.filter(n=>n.scene_id==='scene:10450054').length,52);
  assert.ok(baseline.before&&typeof baseline.before==='object');
  assert.ok(Object.hasOwn(baseline.semantics,'effect_manifest'));
  assert.equal(baseline.semantics.effect_manifest,'/player-assets/effects.json?revision='+binding.finalDataHead);
  Object.assign(baselineReceipt,{programSha256:sha(JSON.stringify(baseline)),before:baseline.before,
    headSha:baseline.headSha,wholeLibraryNodes:baseline.nodes.length,wholeLibraryEdges:baseline.edges.length});
  await save('baseline.receipt.json',baselineReceipt);
  stage='controlled-native-candidate';
  await save(plan.id+'.request.json',request);
  const response=await invoke('/api/player/prepare',request),raw=await response.text();
  await writeFile(new URL(plan.id+'.raw.json.gz',out),gzipSync(raw),{flag:'wx'});
  const receipt={caseId:plan.id,request,status:response.status,headers:Object.fromEntries(response.headers),
    rawResponseSha256:sha(raw),rawResponseBytes:Buffer.byteLength(raw),
    browserStarted:false,serverStarted:false,programMutated:false};
  await save(plan.id+'.http.json',receipt);
  if(response.status!==200){
    if(response.status===422){
      const diagnostic=await invoke('/api/resolve',request),text=await diagnostic.text();
      await writeFile(new URL(plan.id+'.resolve.json.gz',out),gzipSync(text),{flag:'wx'});
      receipt.resolve={status:diagnostic.status,headers:Object.fromEntries(diagnostic.headers),sha256:sha(text),bytes:Buffer.byteLength(text)};
    }
    await save(plan.id+'.receipt.json',receipt);
    throw Error('Ordinary prepare '+response.status+'; retain original raw/resolve and stop without entry fallback');
  }
  assert.ok(Buffer.byteLength(raw)<=25000000,'Unexpected complete program size');
  const program=JSON.parse(raw);
  assert.equal(program.headSha,plan.alias);assert.equal(program.start,plan.start);
  assert.equal(program.revision,parseInt(plan.alias.slice(0,12),16));
  assert.equal(program.nodes.length,binding.allLibraryNodes);
  assert.equal(program.edges.length,binding.allLibraryEdges);
  assert.equal(program.nodes.filter(n=>n.scene_id==='scene:10450054').length,52);
  assert.ok(program.before&&typeof program.before==='object');
  // A genuine before is retained, never reconstructed from the source PTS or
  // inserted from a neighbouring node. Any actual extra model dependency must
  // already be frozen; it cannot silently widen transport during capture.
  for(const model of [program.before.model,...(program.before.actors||[]).map(a=>a.model)].filter(Boolean))
    assert.ok(Object.keys(binding.dataGuards).some(p=>p.startsWith('assets/models/'+model+'/')),'Unbound ordinary-before model '+model);
  for(const step of plan.steps){
    const node=program.nodes.find(n=>n.id===step.id);assert.ok(node);
    assert.equal(node.kind,step.kind);assert.equal(node.model,step.expectedModel);
    assert.deepEqual({body:node.body,face:node.face,extras:node.extra_motions},step.parsedMotion);
    assert.deepEqual(node.command,step.native.command);assert.equal(node.translation,step.native.msg_text);
    assert.equal(node.suppress_lip_motion,step.expectedSuppressLipMotion);
  }
  // The staged CSV preserves an empty body slot. Only canonical node4.face
  // may change; actual physical body parameters remain an observation because
  // the untouched player owns face/body blends. No runtime winner is asserted.
  const target=plan.steps.find(s=>s.target),targetIndex=baseline.nodes.findIndex(n=>n.id===target.id);
  assert.ok(targetIndex>=0);assert.equal(program.nodes[targetIndex].id,target.id);
  assert.equal(target.native.motion,'');assert.equal(target.candidateMotion,',face_bikkuri');
  assert.deepEqual(target.parsedMotion,{body:'',face:'face_bikkuri',extras:[]});
  assert.equal(baseline.nodes[targetIndex].face,'');assert.equal(program.nodes[targetIndex].face,'face_bikkuri');
  assert.equal(program.nodes[targetIndex].body,'');assert.deepEqual(program.nodes[targetIndex].extra_motions,[]);
  assert.deepEqual(program.before,baseline.before);
  // This is the actual existing nested semantics field, not a top-level
  // effect_manifest or a sidecar. Require its exact original schema and URL;
  // missing keys/unknown differences are retained raw and rejected, not added.
  assert.ok(Object.hasOwn(program.semantics,'effect_manifest'));
  assert.equal(program.semantics.effect_manifest,'/player-assets/effects.json?revision='+plan.alias);
  const expectedDiff=[
    {path:'/headSha',before:binding.finalDataHead,after:plan.alias},
    {path:'/revision',before:baseline.revision,after:parseInt(plan.alias.slice(0,12),16)},
    {path:'/semantics/effect_manifest',before:baseline.semantics.effect_manifest,after:program.semantics.effect_manifest},
    {path:'/nodes/'+targetIndex+'/face',before:'',after:'face_bikkuri'}
  ].filter(row=>!Object.is(row.before,row.after));
  let actualDiff;
  try{actualDiff=differences(baseline,program);}
  catch(error){
    // Diagnostic persistence must not replace the original schema assertion.
    await save(plan.id+'.complete-program-diff.json',{comparisonError:String(error),stack:error.stack,
      expectedDiff,originalObjectsMutated:false,rawResponsesRetained:true,motionAccepted:false}).catch(recordError=>
        console.error('PREPARATION_DIFF_RECORD_FAILED',{originalError:String(error),originalStack:error.stack,
          recordError:String(recordError),recordStack:recordError.stack}));
    throw error;
  }
  await save(plan.id+'.complete-program-diff.json',{actualDiff,expectedDiff,
    baselineRawSha256:sha(baselineRaw),candidateRawSha256:sha(raw),wholeLibraryNodes:program.nodes.length,
    wholeLibraryEdges:program.edges.length,originalObjectsMutated:false,wholeBeforeExact:true,
    candidateOnly:true,aliasIsGitCommit:false,motionAccepted:false,sourcePhaseAccepted:false});
  const sorted=rows=>[...rows].sort((a,b)=>a.path.localeCompare(b.path));
  assert.deepEqual(sorted(actualDiff),sorted(expectedDiff),
    'Only exact target.face and existing headSha/revision/nested effect_manifest alias URL may differ');
  for(const expected of plan.links){
    const edge=program.edges.find(e=>e.id===expected.id);assert.ok(edge?.available);
    assert.equal(edge.source,expected.source);assert.equal(edge.target,expected.target);
    assert.deepEqual(edge.native_transition,expected.native_transition);
  }
  const forbidden=program.edges.find(e=>e.id===plan.stop.forbiddenEdge);assert.ok(forbidden?.available);
  assert.equal(forbidden.native_transition.next_scenario_id,6);
  Object.assign(receipt,{start:program.start,headSha:program.headSha,programSha256:sha(JSON.stringify(program)),
    before:program.before,wholeLibraryNodes:program.nodes.length,wholeLibraryEdges:program.edges.length,
    candidateOnly:true,aliasIsGitCommit:false,formalDataHead:binding.finalDataHead,overlay:plan.overlay});
  await save(plan.id+'.receipt.json',receipt);
  await finishBackground();
  await verify();
  const providerPath=new URL('frozen/provider-events.jsonl',here),providerBytes=await readFile(providerPath);
  const providerRows=providerBytes.toString('utf8').trim().split('\n').filter(Boolean).map(row=>JSON.parse(row));
  assert.ok(providerRows.some(row=>row.relative==='native/scenes/10450054.json'&&row.substituted===false&&row.sha256===plan.formalNative.sha256));
  assert.ok(providerRows.some(row=>row.relative==='native/scenes/10450054.json'&&row.substituted===true&&
    row.caseId===plan.id&&row.revision===plan.alias&&row.sha256===plan.overlay.sha256));
  await save('index.json',{schema:'stella.p30.face-native-candidate-preparation.v1',rootConfirmed:false,
    allSucceeded:true,receipts:[receipt],baseline:baselineReceipt,bindingSha256:sha(bindingBytes),
    providerTraceSha256:sha(providerBytes),candidateOnly:true,browserStarted:false,serverStarted:false});
  const runtimeBindings={...binding.fileGuards};
  const files=['common.py','freeze.py','prepare.mjs','transport.mjs','server.mjs','workers-private.mjs','node-guards.mjs',
    'owner-events.mjs','curve-audit.mjs','driver.mjs','run.py','README.md','plan.rootfalse.json','static-report.rootfalse.json',
    'frozen/binding.json','frozen/plan.json','frozen/provider-events.jsonl','prepared/index.json',
    'prepared/baseline.request.json','prepared/baseline.http.json','prepared/baseline.receipt.json','prepared/baseline.raw.json.gz',
    'prepared/'+plan.id+'.complete-program-diff.json',
    ...['request.json','http.json','receipt.json','raw.json.gz'].map(s=>'prepared/'+plan.id+'.'+s)];
  for(const name of files){const url=new URL(name,here);runtimeBindings[fileURLToPath(url)]=sha(await readFile(url));}
  await writeFile(new URL('root-release.prepared.draft.json',here),JSON.stringify({
    schema:'stella.p30.face-native-candidate-runtime-release.v1',rootConfirmed:false,executionAuthorized:false,
    browserLaunchAuthorized:false,diagnosticInstrumentationAuthorized:false,continuousRecorderAuthorized:false,
    controlledNativeCandidateAuthorized:false,
    finalDataHead:binding.finalDataHead,finalSourceHead:binding.finalSourceHead,browserOwner:binding.browserOwner,
    attempt:'attempt-1',bindingSha256:sha(bindingBytes),normalPreparationIndexSha256:sha(await readFile(new URL('index.json',out))),
    runtimeBindings},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({prepared:1,ordinaryFullProgram:true,wholeLibraryNodes:binding.allLibraryNodes,browserAuthorized:false}));
}catch(error){
  // Keep the first preparation error authoritative even if the original raw
  // response or a failure-record write exhausts the separately bounded disk.
  await save('failure.json',{error:String(error),stack:error.stack,stage,request,backgroundErrors,noRetry:true,noEntryFallback:true})
    .catch(recordError=>console.error('PREPARATION_FAILURE_RECORD_FAILED',{originalError:String(error),originalStack:error.stack,
      recordError:String(recordError),recordStack:recordError.stack}));
  throw error;
}
