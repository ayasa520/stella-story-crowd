// Future root-released preparation, not a test or an executable release.
// The single start uses the unchanged ordinary Worker. A 422 is retained and stops
// preparation; this code cannot select another entry, inject before, or retry.
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {gzipSync} from 'node:zlib';
import {sha,verifyInputs} from './guards.mjs';
const here=new URL('./',import.meta.url),root=new URL('../../../',here);
const load=async name=>JSON.parse(await readFile(new URL(name,here),'utf8'));
const save=async(name,value)=>writeFile(new URL(name,here),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const binding=await load('input-binding.json'),plan=await load('capture-plan.json');
const releasePath=process.env.STELLA_PREPARATION_RELEASE_PATH;
assert.ok(releasePath);
const releaseBytes=await readFile(releasePath),release=JSON.parse(releaseBytes);
assert.equal(sha(releaseBytes),process.env.STELLA_PREPARATION_RELEASE_SHA256);
assert.equal(release.rootConfirmed,true);assert.equal(release.preparationAuthorized,true);
assert.equal(release.browserLaunchAuthorized,false);
assert.equal(release.publishedHead,binding.revision);
assert.equal(release.sourceHead,binding.source.head);
assert.equal(process.env.STELLA_REVIEW_REVISION,binding.revision);
assert.equal(process.env.STELLA_HOSTING,undefined);
await verifyInputs(binding);
await mkdir(new URL('prepared/',here));
const workersModule=new URL('../../stella-local-deployment-3394828/workers-local.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'
  ?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const context={waitUntil(promise){promise.catch(error=>console.error(error));}};
const programs={};
for(const item of plan.cases){
  await verifyInputs(binding);
  const request={id:item.start,baseSha:binding.revision,choices:{}};
  await save('prepared/'+item.id+'.request.json',request);
  const response=await worker.fetch(new Request('http://127.0.0.1:5198/api/player/prepare',{
    method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}),env,context);
  const raw=await response.text();
  await writeFile(new URL('prepared/'+item.id+'.response.json.gz',here),gzipSync(raw),{flag:'wx'});
  const receipt={caseId:item.id,status:response.status,headers:Object.fromEntries(response.headers),
    request,rawResponseSha256:sha(raw),rawResponseBytes:Buffer.byteLength(raw),
    browserStarted:false,serverStarted:false,programMutated:false};
  // Preserve HTTP facts before parsing or validating a200 body. A later JSON
  // or route assertion must not erase the original status/headers/raw witness.
  await save('prepared/'+item.id+'.http.json',receipt);
  if(response.status!==200){
    // Resolve observes the same ordinary failure. It does not add choices or
    // replace any state, and this single attempt stops after the failure.
    if(response.status===422){
      const resolved=await worker.fetch(new Request('http://127.0.0.1:5198/api/resolve',{
        method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}),env,context);
      const text=await resolved.text();
      await writeFile(new URL('prepared/'+item.id+'.resolve.json.gz',here),gzipSync(text),{flag:'wx'});
      receipt.resolve={status:resolved.status,headers:Object.fromEntries(resolved.headers),
        rawResponseSha256:sha(text),rawResponseBytes:Buffer.byteLength(text)};
    }
    await save('prepared/'+item.id+'.receipt.json',receipt);
    throw Error('Ordinary prepare '+response.status+'; original response retained; no retry/seed/override');
  }
  const program=JSON.parse(raw);
  // A normal before may reveal an additional resource dependency. Expose it
  // after preserving the raw HTTP witness; never seed a convenient model or
  // silently widen the saved upstream transport during an authorized attempt.
  for(const model of [program.before?.model,...(program.before?.actors||[]).map(a=>a.model)].filter(Boolean))
    assert.ok(Object.keys(binding.dataInputs).some(p=>p.startsWith('assets/models/'+model+'/')),
      'Unbound actual normal-before model '+model);
  assert.equal(program.start,item.start);assert.equal(program.headSha,binding.revision);
  assert.equal(program.nodes.length,binding.libraryCounts.libraryNodes);
  assert.equal(program.edges.length,binding.libraryCounts.libraryEdges);
  for(const [scene,count] of Object.entries(binding.sceneCounts))
    assert.equal(program.nodes.filter(n=>n.scene_id==='scene:'+scene).length,count);
  let inherited=program.before.bg_picture;assert.equal(typeof inherited,'string');
  const nodes=[],edges=[];
  for(const [index,step] of item.steps.entries()){
    const node=program.nodes.find(n=>n.id===step.id);assert.ok(node);
    const expected=step.expectedCompiled;
    for(const key of ['kind','title_mode','model','body','face','character_image','movie_resource','bg_music'])
      assert.equal(node[key],expected[key],step.id+':'+key);
    assert.deepEqual(node.command,step.native.command);
    assert.equal(node.translation,step.native.msg_text);
    assert.equal(node.text,step.sourceText||step.native.msg_text);
    assert.equal(node.bg_picture,step.native.bg_picture);
    assert.deepEqual(node.script_background,expected.script_background);
    if(node.script_background.resource)inherited=node.script_background.resource;
    const previous=index?nodes[index-1].node:null;
    const display=node.kind==='movie'?program.semantics.movie_background:
      node.character_image?program.semantics.illustration_background:
      node.title_mode==='end'&&previous?.kind==='movie'&&!node.bg_picture
        ?program.semantics.movie_background:inherited;
    nodes.push({node,expectedEffectiveBackground:inherited,expectedDisplayBackground:display});
    if(step.edge){
      const edge=program.edges.find(e=>e.id===step.edge.id);assert.ok(edge?.available);
      assert.equal(edge.source,step.id);assert.equal(edge.target,step.edge.target);
      assert.equal(edge.flow_action,step.edge.flow_action);
      assert.deepEqual(edge.native_transition,step.edge.native);
      if(index+1<item.steps.length)assert.equal(edge.target,item.steps[index+1].id);
      edges.push(edge);
    }
    if(step.choice){
      const edge=edges.at(-1);
      assert.equal(edge.side,step.choice.side);
      assert.equal(edge.label_translation,step.choice.label);
      assert.equal(edge.quote_translation,step.choice.quote);
    }
  }
  // P22 changes foreground identity twice on the way into the movie. These saved
  // foreground inequalities make skipInOut false independently of a route-BG
  // mutation. Keep that source policy separate from actual OUT event evidence;
  // this case cannot replace the positive381/71 regression witnesses.
  assert.equal(plan.closeCoverage.expectedPositiveWitnesses,0);
  assert.deepEqual(plan.closeCoverage.positiveEdges,[]);
  const closeExclusions=plan.closeCoverage.exclusions.map(value=>{
    const from=program.nodes.find(n=>n.id===value.source),to=program.nodes.find(n=>n.id===value.target);
    const edge=program.edges.find(e=>e.id===value.edge);
    assert.equal(from.kind,'card');assert.equal(edge.kind,'next');
    assert.equal(program.edges.filter(e=>e.source===from.id).length,1);
    assert.deepEqual(from.actors,[]);assert.deepEqual(to.actors,[]);
    assert.equal(from.character_image,'');assert.equal(to.character_image,'');
    assert.equal(from.model,value.from.models[0]);
    if(value.to.kind==='actor'){
      assert.equal(to.kind,'card');assert.equal(to.model,value.to.models[0]);
      assert.notEqual(from.model,to.model);
    }else{
      assert.equal(to.kind,'movie');assert.equal(to.movie_resource,value.to.resource);
    }
    return {...value,skipInOut:false,positiveNativeTapPanelClose:false,
      provenance:'Exact saved foreground identities and guarded canonical skipInOut; not an invented request event'};
  });
  const protectedHandoff=program.edges.find(e=>e.id===plan.protectedHandoff.id);
  assert.ok(protectedHandoff?.available);assert.equal(protectedHandoff.flow_action,'scene');
  assert.equal(protectedHandoff.target,plan.protectedHandoff.target);
  assert.deepEqual(protectedHandoff.native_transition,plan.protectedHandoff.native);
  const unknown=plan.unknownBranches.map(value=>{
    const edge=program.edges.find(e=>e.id===value.edgeId);assert.ok(edge);
    assert.equal(edge.available,false);assert.equal(edge.state,'missing');assert.equal(edge.target,'');
    return edge;
  });
  const final=item.steps.at(-1);
  let forbidden=null;
  if(item.stop.phase==='ready'){
    forbidden=program.edges.find(e=>e.source===final.id&&e.id.endsWith(':101'));
    assert.ok(forbidden?.available);assert.equal(forbidden.native_transition.next_scenario_id,11);
  }else{
    assert.equal(edges.at(-1).flow_action,'complete');assert.equal(edges.at(-1).target,'');
    assert.equal(Object.hasOwn(edges.at(-1).native_transition,'next_section_id'),false);
    assert.equal(Object.hasOwn(edges.at(-1).native_transition,'next_scene_id'),false);
  }
  Object.assign(receipt,{programSha256:sha(JSON.stringify(program)),headSha:program.headSha,
    start:program.start,before:program.before,wholeLibraryNodes:program.nodes.length});
  await save('prepared/'+item.id+'.route.json',{nodes,edges,unknown,forbidden,closeExclusions,protectedHandoff,before:program.before,
    fullProgramUsed:true,programSliced:false,beforeFromActualApi:true});
  await save('prepared/'+item.id+'.receipt.json',receipt);
  programs[item.id]=receipt;
}
await verifyInputs(binding);
await save('normal-prepare-receipt.json',{schema:'stella.p22.one-normal-prepare.v1',
  rootConfirmed:false,programs,allStatus200:true,browserStarted:false,serverStarted:false});
const rootPath=fileURLToPath(root);
const runtimeBindings=Object.fromEntries(Object.entries({...binding.kitGuards,...binding.resourceAndSourceGuards})
  .map(([name,digest])=>[name.startsWith(rootPath)?name.slice(rootPath.length):name,digest]));
for(const name of ['input-binding.json','capture-plan.json','normal-prepare-receipt.json',...plan.cases.flatMap(c=>
  ['request.json','response.json.gz','http.json','route.json','receipt.json'].map(s=>'prepared/'+c.id+'.'+s))]){
  const url=new URL(name,here);runtimeBindings[fileURLToPath(url).slice(fileURLToPath(root).length)]=sha(await readFile(url));
}
await save('root-release.prepared.draft.json',{schema:'stella.p22.ending-normal-qa.runtime-release.v1',
  rootConfirmed:false,executionAuthorized:false,browserLaunchAuthorized:false,browserOwner:binding.browserOwner,
  publishedHead:binding.revision,sourceHead:binding.source.head,inputBindingSha256:sha(await readFile(new URL('input-binding.json',here))),
  planSha256:sha(await readFile(new URL('capture-plan.json',here))),
  normalProgramSha256ByCase:Object.fromEntries(Object.entries(programs).map(([k,v])=>[k,v.programSha256])),
  runtimeBindings,attempt:'attempt-1',scope:plan.acceptanceScope});
console.log(JSON.stringify({prepared:Object.keys(programs),nodes:binding.libraryCounts.libraryNodes,browserAuthorized:false}));
