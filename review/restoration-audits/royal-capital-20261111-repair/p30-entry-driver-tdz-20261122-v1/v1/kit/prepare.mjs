// One fresh ordinary full-program preparation. No alternate revision/native
// file exists in this kit. Preserve raw HTTP before parsing, and let a real422
// stop the scope rather than manufacturing before or choosing a root prefix.
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
assert.equal(binding.noNativeOverlay,true);assert.equal(binding.noProgramMutation,true);
assert.deepEqual(binding.plans.map(p=>p.id),['p30-node4-unchanged-ordinary']);
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
const plan=binding.plans[0],request={id:plan.start,baseSha:binding.finalDataHead,choices:{}};
try{
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
  assert.equal(program.headSha,binding.finalDataHead);assert.equal(program.start,plan.start);
  assert.equal(program.revision,parseInt(binding.finalDataHead.slice(0,12),16));
  assert.equal(program.nodes.length,binding.allLibraryNodes);
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
  for(const expected of plan.links){
    const edge=program.edges.find(e=>e.id===expected.id);assert.ok(edge?.available);
    assert.equal(edge.source,expected.source);assert.equal(edge.target,expected.target);
    assert.deepEqual(edge.native_transition,expected.native_transition);
  }
  const forbidden=program.edges.find(e=>e.id===plan.stop.forbiddenEdge);assert.ok(forbidden?.available);
  assert.equal(forbidden.native_transition.next_scenario_id,6);
  Object.assign(receipt,{start:program.start,headSha:program.headSha,programSha256:sha(JSON.stringify(program)),
    before:program.before,wholeLibraryNodes:program.nodes.length,wholeLibraryEdges:program.edges.length});
  await save(plan.id+'.receipt.json',receipt);
  await finishBackground();
  await verify();
  await save('index.json',{schema:'stella.p30.ordinary-owner-preparation.v1',rootConfirmed:false,
    allSucceeded:true,receipts:[receipt],bindingSha256:sha(bindingBytes),browserStarted:false,serverStarted:false});
  const runtimeBindings={...binding.fileGuards};
  const files=['common.py','freeze.py','prepare.mjs','transport.mjs','server.mjs','workers-private.mjs','node-guards.mjs',
    'owner-events.mjs','curve-audit.mjs','driver.mjs','run.py','README.md','plan.rootfalse.json','static-report.rootfalse.json',
    'frozen/binding.json','frozen/plan.json','prepared/index.json',
    ...['request.json','http.json','receipt.json','raw.json.gz'].map(s=>'prepared/'+plan.id+'.'+s)];
  for(const name of files){const url=new URL(name,here);runtimeBindings[fileURLToPath(url)]=sha(await readFile(url));}
  await writeFile(new URL('root-release.prepared.draft.json',here),JSON.stringify({
    schema:'stella.p30.ordinary-owner-runtime-release.v1',rootConfirmed:false,executionAuthorized:false,
    browserLaunchAuthorized:false,diagnosticInstrumentationAuthorized:false,continuousRecorderAuthorized:false,
    finalDataHead:binding.finalDataHead,finalSourceHead:binding.finalSourceHead,browserOwner:binding.browserOwner,
    attempt:'attempt-1',bindingSha256:sha(bindingBytes),normalPreparationIndexSha256:sha(await readFile(new URL('index.json',out))),
    runtimeBindings},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({prepared:1,ordinaryFullProgram:true,wholeLibraryNodes:binding.allLibraryNodes,browserAuthorized:false}));
}catch(error){
  await save('failure.json',{error:String(error),stack:error.stack,request,backgroundErrors,noRetry:true,noEntryFallback:true});
  throw error;
}
