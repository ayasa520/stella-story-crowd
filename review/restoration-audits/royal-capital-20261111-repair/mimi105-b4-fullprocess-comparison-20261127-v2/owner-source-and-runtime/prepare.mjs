// Future root-released ordinary native/check and complete program comparison.
// This module is syntax-checked only while source is being prepared.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {gzipSync} from 'node:zlib';
import {context,sha,here,readHeldJson,parseHeldJson} from './context.mjs';
const {binding,bindingBytes,verify}=await context('prepare');
assert.deepEqual(globalThis[Symbol.for('stella.mimi105.native-transport')],{
  bindingSha256:sha(bindingBytes),aliases:binding.plans.map(plan=>plan.alias)});
assert.equal(process.env.STELLA_HOSTING,undefined);
const out=new URL('prepared/',here);await mkdir(out);
const save=(name,value)=>writeFile(new URL(name,out),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const workers=new URL('workers-private.mjs',here).href;
registerHooks({resolve(name,scope,next){return name==='cloudflare:workers'
  ?{url:workers,shortCircuit:true}:next(name,scope);}});
const {env}=await import(workers);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const tasks=[],backgroundErrors=[];
async function request(name,path,body){
  await save(name+'.request.json',body);
  const response=await worker.fetch(new Request('http://127.0.0.1:5198'+path,{method:'POST',
    headers:{'content-type':'application/json'},body:JSON.stringify(body)}),env,{waitUntil(job){
      tasks.push(Promise.resolve(job).catch(error=>{backgroundErrors.push({error:String(error),stack:error.stack});}));
    }});
  const raw=Buffer.from(await response.arrayBuffer());
  // Status/headers and the FIRST response bytes precede status, size or parse
  // assertions. Validation failures and ordinary422 are original evidence.
  await writeFile(new URL(name+'.raw.json.gz',out),gzipSync(raw,{level:1}),{flag:'wx'});
  const http={request:body,status:response.status,headers:Object.fromEntries(response.headers),
    rawBytes:raw.length,rawSha256:sha(raw),programMutated:false};
  await save(name+'.http.json',http);
  assert.ok(raw.length<=25000000,'Complete ordinary response crossed the existing raw cap');
  const value=await parseHeldJson(raw,{path:name+' original Worker response',output:out.pathname});
  return {value,http,raw};
}
function diff(left,right,path=''){
  if(left!==null&&right!==null&&typeof left==='object'&&typeof right==='object'){
    assert.equal(Array.isArray(left),Array.isArray(right),path);assert.deepEqual(Object.keys(left),Object.keys(right),path);
    return Object.keys(left).flatMap(key=>diff(left[key],right[key],path+'/'+key));
  }
  return Object.is(left,right)?[]:[{path,before:left,after:right}];
}
const sort=rows=>[...rows].sort((a,b)=>a.path.localeCompare(b.path));
const receipts=[];let stage='baseline-native-check';
try{
  const formal=await readHeldJson(binding.dataRoot+'/native/scenes/10040043.json',{
    output:out.pathname,sha256:binding.dataGuards['native/scenes/10040043.json']});
  const baselineCheck=await request('baseline.native-check','/api/native/check',{
    baseSha:binding.finalDataHead,sceneId:10040043,document:formal});
  assert.equal(baselineCheck.http.status,200);assert.deepEqual(baselineCheck.value.changes,[]);
  assert.ok(Array.isArray(baselineCheck.value.issues));
  // Check against the FORMAL revision, not the candidate alias. Otherwise a
  // candidate checked against itself would misleadingly produce no changes.
  for(const plan of binding.plans){
    stage=plan.id+':native-check';
    const document=await readHeldJson(plan.overlay.path,{output:out.pathname,sha256:plan.overlay.sha256});
    const checked=await request(plan.id+'.native-check','/api/native/check',{
      baseSha:binding.finalDataHead,sceneId:10040043,document});
    await save(plan.id+'.native-check-comparison.json',{baselineIssues:baselineCheck.value.issues,
      completeResponse:checked.value,expectedChanges:plan.expectedNativeCheckChanges,
      semanticDiff:plan.expectedSemanticDiff,wholeValidationAccepted:false});
    assert.equal(checked.http.status,200);
    assert.deepEqual(checked.value.changes,plan.expectedNativeCheckChanges);
    assert.deepEqual(checked.value.issues,baselineCheck.value.issues,'Any new issue rejects preparation');
    assert.ok(!checked.value.issues.some(issue=>['schema','duplicate_id','duplicate_uid'].includes(issue.code)));
  }
  stage='formal-complete-prepare';
  const start=binding.plans[0].start;
  assert.equal(start,'node:10040043:1004004300104');
  const base=await request('baseline','/api/player/prepare',{id:start,baseSha:binding.finalDataHead,choices:{}});
  if(base.http.status===422)await request('baseline.resolve','/api/resolve',{
    id:start,baseSha:binding.finalDataHead,choices:{}});
  assert.equal(base.http.status,200,'Ordinary failure retains raw; no root/entry fallback');
  const baseline=base.value;
  assert.equal(baseline.headSha,binding.finalDataHead);assert.equal(baseline.start,start);
  assert.equal(baseline.nodes.length,binding.allLibraryNodes);assert.equal(baseline.edges.length,binding.allLibraryEdges);
  assert.equal(baseline.nodes.filter(node=>node.scene_id==='scene:10040043').length,binding.sceneRows);
  assert.ok(baseline.before&&typeof baseline.before==='object');
  assert.equal(baseline.semantics.effect_manifest,'/player-assets/effects.json?revision='+binding.finalDataHead);
  await save('baseline.receipt.json',{...base.http,programSha256:sha(JSON.stringify(baseline)),before:baseline.before,
    wholeLibraryNodes:baseline.nodes.length,wholeLibraryEdges:baseline.edges.length});
  for(const plan of binding.plans){
    stage=plan.id+':complete-prepare';
    const originalRequest={id:plan.start,baseSha:plan.alias,choices:{}};
    const candidate=await request(plan.id,'/api/player/prepare',originalRequest);
    if(candidate.http.status===422)await request(plan.id+'.resolve','/api/resolve',originalRequest);
    assert.equal(candidate.http.status,200,'Retain original failure; no override/seed/retry');
    const program=candidate.value;
    assert.equal(program.headSha,plan.alias);assert.equal(program.start,start);
    assert.equal(program.nodes.length,binding.allLibraryNodes);assert.equal(program.edges.length,binding.allLibraryEdges);
    assert.deepEqual(program.before,baseline.before,'The received complete before is never reconstructed');
    for(const step of plan.steps){
      const node=program.nodes.find(node=>node.id===step.id);assert.ok(node);
      assert.equal(node.kind,step.kind);assert.equal(node.model,step.expectedModel);
      // This is an audit projection only. Never rename extra_motions or patch
      // any property of the complete received program passed to StoryPlayer.
      assert.deepEqual({body:node.body,face:node.face,extras:node.extra_motions},step.parsedMotion);
      assert.deepEqual(node.command,step.native.command);assert.equal(node.translation,step.native.msg_text);
      assert.equal(node.suppress_lip_motion,step.expectedSuppressLipMotion);
    }
    const index=baseline.nodes.findIndex(node=>node.id===plan.steps[1].id);assert.ok(index>=0);
    const target=plan.steps[1];
    const expected=[{path:'/headSha',before:binding.finalDataHead,after:plan.alias},
      {path:'/revision',before:baseline.revision,after:parseInt(plan.alias.slice(0,12),16)},
      {path:'/semantics/effect_manifest',before:baseline.semantics.effect_manifest,
        after:'/player-assets/effects.json?revision='+plan.alias},
      ...['body','face'].map(key=>({path:'/nodes/'+index+'/'+key,
        before:baseline.nodes[index][key],after:target.parsedMotion[key]}))].filter(row=>!Object.is(row.before,row.after));
    const actual=diff(baseline,program);
    await save(plan.id+'.complete-program-diff.json',{actual,expected,originalObjectsMutated:false,
      baselineRawSha256:sha(base.raw),candidateRawSha256:sha(candidate.raw),wholeBeforeExact:true,
      wholeLibraryNodes:program.nodes.length,wholeLibraryEdges:program.edges.length,motionAccepted:false});
    assert.deepEqual(sort(actual),sort(expected));
    for(const expectedEdge of plan.links){
      const edge=program.edges.find(edge=>edge.id===expectedEdge.id);assert.ok(edge?.available);
      assert.equal(edge.source,expectedEdge.source);assert.equal(edge.target,expectedEdge.target);
      assert.deepEqual(edge.native_transition,expectedEdge.native_transition);
    }
    const next=program.edges.find(edge=>edge.id===plan.stop.forbiddenEdge);
    assert.ok(next?.available);assert.equal(next.native_transition.next_scenario_id,107);
    const receipt={...candidate.http,caseId:plan.id,programSha256:sha(JSON.stringify(program)),
      before:program.before,candidateOnly:true,aliasIsGitCommit:false,motionAccepted:false};
    await save(plan.id+'.receipt.json',receipt);receipts.push(receipt);
  }
  for(let index=0,round=0;round<32;round++){
    const jobs=tasks.slice(index);if(!jobs.length)break;index=tasks.length;await Promise.allSettled(jobs);
    assert.ok(round<31,'Worker background diagnostics did not quiesce');
  }
  assert.deepEqual(backgroundErrors,[]);await verify();
  await save('index.json',{rootConfirmed:false,allSucceeded:true,receipts,
    bindingSha256:sha(bindingBytes),browserStarted:false,programObjectsMutated:false,motionAccepted:false});
  // This is still an entirely false draft. Its small immutable-source map
  // binds the complete prepared artifacts once, never the large D inventory.
  const runtimeBindings={...binding.sourceGuards,...binding.kitGuards};
  runtimeBindings[fileURLToPath(new URL('frozen/binding.json',here))]=sha(bindingBytes);
  const visit=async folder=>{
    for(const row of await readdir(folder,{withFileTypes:true})){
      const url=new URL(row.name+(row.isDirectory()?'/':''),folder);
      if(row.isDirectory())await visit(url);
      else if(row.isFile()&&!row.name.endsWith('.sqlite')&&!row.name.includes('.sqlite-'))
        runtimeBindings[fileURLToPath(url)]=sha(await readFile(url));
    }
  };
  await visit(out);await visit(new URL('frozen/',here));
  await writeFile(new URL('root-release.prepared.draft.json',here),JSON.stringify({
    schema:'stella.mimi105-four-case-runtime-release.v1',rootConfirmed:false,
    executionAuthorized:false,browserLaunchAuthorized:false,diagnosticInstrumentationAuthorized:false,
    continuousRecorderAuthorized:false,controlledNativeCandidateAuthorized:false,independentRunnerAccepted:false,
    attempt:'attempt-1',browserOwner:binding.browserOwner,finalDataHead:binding.finalDataHead,
    finalSourceHead:binding.finalSourceHead,budgets:binding.budgets,bindingSha256:sha(bindingBytes),
    normalPreparationIndexSha256:sha(await readFile(new URL('index.json',out))),runtimeBindings},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({preparedCases:4,wholePrograms:true,browserStarted:false}));
}catch(error){
  await save('failure.json',{stage,error:String(error),stack:error.stack,backgroundErrors,
    noRetry:true,noEntryFallback:true,originalResponsesRetained:true}).catch(writeError=>
      console.error('PREPARATION_FAILURE_SINK_FAILED',{originalError:String(error),originalStack:error.stack,
        writeError:String(writeError),writeStack:writeError.stack}));
  throw error;
}
