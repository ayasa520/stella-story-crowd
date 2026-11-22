// Complete ordinary production preparation through the fixed-origin transport. No alternate revision, route choice, before or resource
// is injected. Preserve the original HTTP body before any parse/assertion.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,realpath,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {gzipSync,gunzipSync} from 'node:zlib';
import {sha,verifyInputs,expandInventory} from './guards.mjs';
import {forwardProduction,productionOrigin} from './production-proxy.mjs';
const here=new URL('./',import.meta.url),root=new URL('../../../',here);
const load=async name=>JSON.parse(await readFile(new URL(name,here),'utf8'));
const save=async(name,value)=>writeFile(new URL(name,here),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const binding=await expandInventory(await load('input-binding.json')),plan=await load('capture-plan.json');
const releasePath=process.env.STELLA_PREPARATION_RELEASE_PATH;
assert.ok(releasePath);
const releaseBytes=await readFile(releasePath),release=JSON.parse(releaseBytes);
assert.equal(sha(releaseBytes),process.env.STELLA_PREPARATION_RELEASE_SHA256);
assert.equal(release.rootConfirmed,true);assert.equal(release.preparationAuthorized,true);
assert.equal(release.browserLaunchAuthorized,false);
assert.equal(release.productionProxyPreparationApproved,true);
assert.equal(release.productionBaselineApproved,true);assert.equal(release.fullCanonicalHostedScopeApproved,true);
assert.equal(release.publishedHead,binding.revision);assert.equal(release.sourceHead,binding.source.head);
assert.equal(binding.productionOrigin,productionOrigin);
assert.equal(await realpath(process.execPath),await realpath(binding.tools.node.binaryPath));
assert.equal(sha(await readFile(process.execPath)),binding.tools.node.sha256);
await verifyInputs(binding);
await mkdir(new URL('prepared/',here));
const baselineRaw=gunzipSync(await readFile(binding.productionBaseline.raw.path));
assert.equal(sha(baselineRaw),binding.productionBaseline.rawBodySha256);
const baseline=JSON.parse(baselineRaw);
assert.equal(plan.cases.length,1);
const item=plan.cases[0],request={id:item.start,baseSha:binding.revision,choices:{}},programs={};
try{
  await save('prepared/'+item.id+'.request.json',request);
  const response=await forwardProduction(new Request('http://127.0.0.1:5198/api/player/prepare',{
    method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}));
  const raw=await response.text(),compressed=gzipSync(raw);
  await writeFile(new URL('prepared/'+item.id+'.response.json.gz',here),compressed,{flag:'wx'});
  const receipt={caseId:item.id,status:response.status,headers:Object.fromEntries(response.headers),
    request,rawResponseSha256:sha(raw),rawResponseBytes:Buffer.byteLength(raw),
    browserStarted:false,serverStarted:false,programMutated:false,productionOrigin};
  await save('prepared/'+item.id+'.http.json',receipt);
  if(response.status!==200){
    if(response.status===422){
      const resolved=await forwardProduction(new Request('http://127.0.0.1:5198/api/resolve',{
        method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}));
      const text=await resolved.text();
      await writeFile(new URL('prepared/'+item.id+'.resolve.json.gz',here),gzipSync(text),{flag:'wx'});
      receipt.resolve={status:resolved.status,headers:Object.fromEntries(resolved.headers),
        rawResponseSha256:sha(text),rawResponseBytes:Buffer.byteLength(text)};
    }
    await save('prepared/'+item.id+'.receipt.json',receipt);
    throw Error('Ordinary production prepare '+response.status+'; original response retained; no retry/auth change/fallback');
  }
  assert.ok(compressed.length<=binding.budgets.programGzipBytes,'Complete original body retained before size failure');
  const program=JSON.parse(raw);
  // Compare complete original objects and original key order. No metadata
  // deletion, alias normalization, before seed or section slicing is allowed.
  assert.deepEqual(Object.keys(program),Object.keys(baseline));
  assert.deepEqual(program,baseline);
  assert.deepEqual(program.scopeSceneIds,binding.scopeSceneIds);
  for(const model of [program.before?.model,...(program.before?.actors||[]).map(a=>a.model)].filter(Boolean))
    assert.ok(Object.keys(binding.dataInputs).some(p=>p.startsWith('assets/models/'+model+'/')),
      'Unbound actual normal-before model '+model);
  assert.equal(program.start,item.start);assert.equal(program.headSha,binding.revision);
  assert.equal(program.revision,parseInt(binding.revision.slice(0,12),16));
  assert.equal(program.nodes.length,binding.programCounts.programNodes);
  assert.equal(program.edges.length,binding.programCounts.programEdges);
  for(const [scene,count] of Object.entries(binding.sceneCounts))
    assert.equal(program.nodes.filter(n=>n.scene_id==='scene:'+scene).length,count);
  assert.ok(program.before&&typeof program.before==='object');
  const nodes=[],edges=[];
  for(const step of item.steps){
    const node=program.nodes.find(n=>n.id===step.id);assert.ok(node);
    assert.equal(node.kind,'card');assert.equal(node.model,step.expectedModel);
    assert.equal(node.body,'');assert.equal(node.face,'');assert.deepEqual(node.extra_motions,[]);
    assert.equal(node.character_image,'');assert.equal(node.movie_resource,'');
    assert.deepEqual(node.command,step.native.command);
    assert.equal(node.translation,step.native.msg_text);assert.equal(node.text,step.sourceText);
    assert.equal(node.speaker,step.native.msg_character);assert.equal(node.suppress_lip_motion,false);
    assert.equal(node.bank,step.scenario===6?plan.cue.bank:'');
    assert.equal(node.cue,step.scenario===6?plan.cue.cue:'');
    assert.equal(node.voice_delay_ms,0);
    nodes.push(node);
    if(step.edge){
      const edge=program.edges.find(e=>e.id===step.edge.id);assert.ok(edge?.available);
      assert.equal(edge.source,step.id);assert.equal(edge.target,step.edge.target);
      assert.equal(edge.flow_action,step.edge.flow_action);assert.deepEqual(edge.native_transition,step.edge.native);
      assert.equal(program.edges.filter(e=>e.source===step.id).length,1);
      edges.push(edge);
    }
  }
  const forbidden=program.edges.find(e=>e.id===item.stop.forbiddenEdge);
  assert.ok(forbidden?.available);assert.equal(forbidden.target,item.stop.forbiddenNode);
  assert.equal(forbidden.native_transition.next_scenario_id,8);
  Object.assign(receipt,{programSha256:sha(JSON.stringify(program)),headSha:program.headSha,
    start:program.start,before:program.before,wholeLibraryNodes:program.nodes.length,wholeLibraryEdges:program.edges.length});
  await save('prepared/'+item.id+'.route.json',{nodes,edges,forbidden,before:program.before,
    fullProgramUsed:true,programSliced:false,beforeFromActualApi:true});
  await save('prepared/'+item.id+'.receipt.json',receipt);
  programs[item.id]=receipt;
  await verifyInputs(binding);
  await save('normal-prepare-receipt.json',{schema:'stella.p30.voice58-6.normal-prepare.v1',
    rootConfirmed:false,programs,allStatus200:true,browserStarted:false,serverStarted:false,productionOrigin});
  const rootPath=fileURLToPath(root);
  // The full root inventory is authoritative and checked in RAM. This small
  // release binds its reference, new kit/approval files and actual new outputs.
  const runtimeBindings=Object.fromEntries(Object.entries({...binding.kitGuards,...binding.additionalGuards})
    .map(([name,digest])=>[name.startsWith(rootPath)?name.slice(rootPath.length):name,digest]));
  for(const name of ['input-binding.json','capture-plan.json','normal-prepare-receipt.json',
      ...['request.json','response.json.gz','http.json','route.json','receipt.json'].map(s=>'prepared/'+item.id+'.'+s)]){
    const url=new URL(name,here);runtimeBindings[fileURLToPath(url).slice(rootPath.length)]=sha(await readFile(url));
  }
  async function bindPrepared(directory){
    for(const entry of await readdir(directory,{withFileTypes:true})){
      const child=new URL(entry.name+(entry.isDirectory()?'/':''),directory);
      if(entry.isDirectory())await bindPrepared(child);
      else runtimeBindings[fileURLToPath(child).slice(rootPath.length)]=sha(await readFile(child));
    }
  }
  await bindPrepared(new URL('prepared/',here));
  await save('root-release.prepared.draft.json',{schema:'stella.p30.voice58-6.production-runtime-release.v1',
    rootConfirmed:false,executionAuthorized:false,browserLaunchAuthorized:false,
    diagnosticInstrumentationAuthorized:false,productionProxyAuthorized:false,
    browserOwner:binding.browserOwner,publishedHead:binding.revision,sourceHead:binding.source.head,
    productionOrigin,inputBindingSha256:sha(await readFile(new URL('input-binding.json',here))),
    planSha256:sha(await readFile(new URL('capture-plan.json',here))),
    normalProgramSha256ByCase:Object.fromEntries(Object.entries(programs).map(([k,v])=>[k,v.programSha256])),
    runtimeBindings,attempt:'attempt-1',maximumDriverSeconds:binding.budgets.maximumDriverSeconds,scope:plan.acceptanceScope});
  console.log(JSON.stringify({prepared:Object.keys(programs),nodes:binding.programCounts.programNodes,browserAuthorized:false}));
}catch(error){
  await save('preparation-failure.json',{error:String(error),stack:error.stack,request,noRetry:true,
    productionOrigin,authChanged:false,wavFallbackAllowed:false,localWorkerImported:false}).catch(recordError=>
    console.error('PREPARATION_FAILURE_RECORD_FAILED',{originalError:String(error),originalStack:error.stack,
      recordError:String(recordError),recordStack:recordError.stack}));
  throw error;
}
