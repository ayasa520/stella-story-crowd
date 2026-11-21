// Execute the canonical editor functions with real repository bytes. These
// controls stay in memory: no publisher, serializer, browser or story write is
// called. Later controls explicitly build on earlier normal mutations; their
// counterfactual redirects/deletions are never source-evidence claims.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
const root='/home/rikka/Projects/stella',area=root+'/artifacts/stella-script-continuation-20261121';
const repo=area+'/data-checkout',canonical=root+'/artifacts/stella-site-repair-source/.sites-checkout';
const output=area+'/directory-edge-owner-normal-audit-v1/execution-1';
const revision='e0fc50f316604d241a08351cd7c0fa63e8f0054a';
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const read=file=>JSON.parse(fs.readFileSync(file));
const git=(cwd,...args)=>execFileSync('git',args,{cwd,maxBuffer:64*1024*1024});
const clone=value=>structuredClone(value),equal=(a,b)=>assert.deepEqual(a,b);
assert.equal(fs.existsSync(output),false);fs.mkdirSync(output);
assert.equal(git(repo,'rev-parse','HEAD').toString().trim(),revision);
assert.equal(git(repo,'status','--porcelain').toString(),'');
const sourceStatus=git(canonical,'status','--porcelain').toString();
const toolRoot=root+'/data/native_recovery/royal-capital-20261110/repair-20261111/target-arm-tools-20261112-v1';
const tools=read(toolRoot+'/toolchain-receipt.json');
for(const descriptor of [tools.tools.node.executable,tools.tools.esbuild.armExecutable])
  assert.equal(hash(fs.readFileSync(descriptor.file)),descriptor.sha256);
assert.equal(process.arch,'arm64');
const manifest=read(repo+'/manifest.json'),assets=read(repo+'/assets/catalog.json'),ownership=read(repo+'/review/native-restoration.json');
const dataFiles=['manifest.json','assets/catalog.json','review/native-restoration.json',...manifest.scenes.flatMap(e=>[e.path,e.reviewPath])];
const dataGuards=Object.fromEntries(dataFiles.map(member=>[member,hash(fs.readFileSync(repo+'/'+member))]));
const sources=manifest.scenes.map(entry=>({entry,document:read(repo+'/'+entry.path),review:read(repo+'/'+entry.reviewPath)}));
const base={headSha:revision,manifest,sources};
const transport=[];
globalThis.fetch=async(input,init)=>{
  const request=new Request(input,init),url=new URL(request.url);
  assert.equal(request.method,'GET');assert.equal(url.origin,'https://raw.githubusercontent.com');
  const prefix='/ayasa520/stella-story-crowd/'+revision+'/';assert.ok(url.pathname.startsWith(prefix));
  const member=decodeURIComponent(url.pathname.slice(prefix.length));assert.ok(/^native\/scenes\/\d+\.json$/.test(member));
  const raw=git(repo,'show',revision+':'+member);assert.equal(hash(raw),dataGuards[member]);
  transport.push({member,sha256:hash(raw),bytes:raw.length});return new Response(raw,{headers:{'Content-Type':'application/json'}});
};
const sourceGuards={};
const esbuild=await import(pathToFileURL(toolRoot+'/node_modules/esbuild/lib/main.js'));
let build;
try{
  build=await esbuild.build({entryPoints:[canonical+'/lib/studio-native.ts'],absWorkingDir:canonical,
    bundle:true,platform:'node',format:'esm',target:'node26',write:false,alias:{'@':canonical},logLevel:'silent',
    plugins:[{name:'guarded-cloudflare-editor',setup(builder){
      builder.onResolve({filter:/^cloudflare:workers$/},()=>({path:'workers',namespace:'audit-env'}));
      builder.onLoad({filter:/.*/,namespace:'audit-env'},()=>({contents:'export const env={STELLA_HOSTING:"cloudflare"};',loader:'js'}));
      builder.onLoad({filter:/\.(?:[cm]?js|tsx?|json)$/},args=>{
        const raw=fs.readFileSync(args.path);sourceGuards[args.path]=hash(raw);
        const ext=path.extname(args.path).slice(1);return{contents:raw,loader:['mjs','cjs'].includes(ext)?'js':ext};
      });
    }}]});
}finally{esbuild.stop();}
const api=await import('data:text/javascript;base64,'+Buffer.from(build.outputFiles[0].text).toString('base64'));
const intent=read(area+'/episode5-finish-scene-edge-owner-plan-20261121-v1/candidate.rootfalse.json');
assert.equal(intent.rootConfirmed,false);
const results=[];let stage='setup';
const sourceOf=(snapshot,id)=>snapshot.sources.find(source=>source.entry.id===id);
const chart=(snapshot,id)=>sourceOf(snapshot,id)?.document.chartmap.scene_list.find(row=>row.scene_id===id);
const project=snapshot=>api.studioProject(snapshot,assets);
const edgeIn=(snapshot,id)=>project(snapshot).directory.edges.find(edge=>edge.id===id);
function proveMutation(previous,next,expectedPaths,label){
  const files=api.studioPublicationFiles(previous,next);
  equal(files.map(file=>file.path).sort(),[...expectedPaths].sort());
  for(const old of previous.sources){
    const current=sourceOf(next,old.entry.id);assert.ok(current);
    equal(current.review,old.review);
    equal(current.document.scenario_list,old.document.scenario_list);
    if(old.entry.id!==10090015)equal(current.document,old.document);
  }
  for(const id of Object.keys(ownership.scenes))
    equal(previous.manifest.scenes.find(s=>s.id===Number(id)),next.manifest.scenes.find(s=>s.id===Number(id)));
  results.push({label,publicationPaths:files.map(file=>file.path),allScenarioRowsAndReviewsExact:true,
    allForeignNativeBodiesExact:true,allOwnedSceneSummariesExact:true});
}
function mutate(previous,operation,payload){
  const next=clone(previous),result=api.applyStudioMutation(next,project(previous),'directory/edit',{operation,...clone(payload)});
  return{next,result};
}
try{
  stage='candidate-owner-only-add';
  const added=mutate(base,'save_edge',{edge:intent.candidateEdge});
  assert.equal(added.result.sceneId,10090015);
  equal(chart(added.next,10090015).next_scene_list,[{scene_id:10020001,section_id:1002}]);
  proveMutation(base,added.next,['native/scenes/10090015.json','manifest.json'],stage);
  const addedEdge=edgeIn(added.next,intent.candidateEdge.id);assert.ok(addedEdge);
  equal(addedEdge.nativeTarget,{scene_id:10020001,section_id:1002});

  stage='memory-only-retarget';
  const redirected=mutate(added.next,'save_edge',{edge:{...addedEdge,target:'scene:10020002'}});
  equal(chart(redirected.next,10090015).next_scene_list,[{scene_id:10020002,section_id:1002}]);
  proveMutation(added.next,redirected.next,['native/scenes/10090015.json','manifest.json'],stage);

  stage='id-only-delete-retains-native-provenance';
  const removed=mutate(redirected.next,'delete_edge',{id:addedEdge.id});
  equal(chart(removed.next,10090015).next_scene_list,[]);
  const tombstone=removed.next.manifest.studioDirectory.edges.find(edge=>edge.id===addedEdge.id);
  assert.equal(tombstone.deleted,true);assert.equal(tombstone.source,'scene:10090015');
  equal(tombstone.nativeTarget,{scene_id:10020002,section_id:1002});equal(tombstone.evidence,addedEdge.evidence);
  proveMutation(redirected.next,removed.next,['native/scenes/10090015.json','manifest.json'],stage);

  stage='reimport-cannot-resurrect-deleted-author-edge';
  const imported=clone(removed.next);
  api.applyStudioMutation(imported,project(removed.next),'native/import',{
    sceneId:10090015,document:sourceOf(redirected.next,10090015).document});
  assert.ok(!project(imported).directory.edges.some(edge=>edge.source==='scene:10090015'&&edge.target==='scene:10020002'));
  results.push({label:stage,normalNativeImportUsed:true,deletedCounterpartStillSuppressed:true});

  stage='offscope-author-id-delete-loads-only-owner';
  const offscope=clone(base);offscope.sources=offscope.sources.filter(source=>source.entry.sectionId===1010);
  offscope.manifest.studioDirectory.edges.push({...clone(intent.candidateEdge),
    id:'flow:00000000-0000-4000-8000-000000000005',nativeTarget:{scene_id:10020001,section_id:1002}});
  const beforeSources=offscope.sources.length,requestsBefore=transport.length;
  await api.addStructuralSources(offscope,project(offscope),'directory/edit',{
    operation:'delete_edge',id:'flow:00000000-0000-4000-8000-000000000005'});
  assert.equal(offscope.sources.length,beforeSources+1);assert.equal(transport.length,requestsBefore+1);
  assert.equal(transport.at(-1).member,'native/scenes/10090015.json');
  assert.ok(!offscope.sources.some(source=>source.entry.id===10020001));
  const offscopeRemoved=mutate(offscope,'delete_edge',{id:'flow:00000000-0000-4000-8000-000000000005'});
  proveMutation(offscope,offscopeRemoved.next,['manifest.json'],stage);
  const offTomb=offscopeRemoved.next.manifest.studioDirectory.edges.find(edge=>edge.id==='flow:00000000-0000-4000-8000-000000000005');
  assert.equal(offTomb.source,'scene:10090015');equal(offTomb.nativeTarget,{scene_id:10020001,section_id:1002});

  stage='section-edge-is-metadata-only';
  const sectionPrior=project(base).directory.edges.find(edge=>edge.source==='section:1009'&&edge.target==='section:1002');
  assert.ok(sectionPrior);const sectionChanged=mutate(base,'save_edge',{edge:{...sectionPrior,label:'MEMORY-ONLY-CONTROL'}});
  proveMutation(base,sectionChanged.next,['manifest.json'],stage);

  stage='directory-only-owner-does-not-borrow-foreign-body';
  const absent=clone(base),requestCount=transport.length,sourceCount=absent.sources.length;
  const absentPayload={operation:'save_edge',edge:{id:'control:no-script-owner',source:'scene:20110010',target:'scene:20110020',state:'proposed',notes:'MEMORY ONLY; no source evidence or publication'}};
  await api.addStructuralSources(absent,project(absent),'directory/edit',absentPayload);
  assert.equal(absent.sources.length,sourceCount);assert.equal(transport.length,requestCount);
  const absentChanged=mutate(absent,'save_edge',{edge:absentPayload.edge});
  proveMutation(absent,absentChanged.next,['manifest.json'],stage);

  stage='reject-source-relocation-and-missing-delete';
  for(const payload of [{operation:'save_edge',edge:{...addedEdge,source:'scene:10090014'}},
    {operation:'delete_edge',id:'control:not-existing'}]){
    const unchanged=clone(added.next);let caught;
    try{api.applyStudioMutation(unchanged,project(added.next),'directory/edit',payload);}catch(error){caught=error;}
    assert.ok(caught);assert.ok([400,404].includes(caught.status));equal(unchanged,added.next);
  }
  results.push({label:stage,sourceRelocationRejected:true,unknownDeleteRejected:true,snapshotsUnchanged:true});

  for(const [file,sha]of Object.entries(sourceGuards))assert.equal(hash(fs.readFileSync(file)),sha,file);
  for(const [member,sha]of Object.entries(dataGuards))assert.equal(hash(fs.readFileSync(repo+'/'+member)),sha,member);
  assert.equal(git(repo,'rev-parse','HEAD').toString().trim(),revision);
  assert.equal(git(repo,'status','--porcelain').toString(),'');
  assert.equal(git(canonical,'status','--porcelain').toString(),sourceStatus);
  const receipt={schema:'stella.directory-owner.normal-function-audit.v1',rootConfirmed:false,revision,
    sourceParent:git(canonical,'rev-parse','HEAD').toString().trim(),sourceStatus,sourceGuards,dataGuards,
    results,transport,canonicalFunctionsUsed:['studioProject','addStructuralSources','applyStudioMutation','studioPublicationFiles'],
    cloudflareMode:true,formalWrites:0,networkRequests:0,publisherCalled:false,serializerCalled:false,
    allDiskGuardsExact:true,counterfactualControlsAreMemoryOnly:true,candidateStillUnapproved:true};
  fs.writeFileSync(output+'/verification.json',JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({output,controls:results.length,ownerTransportReads:transport.length,formalWrites:0,sha256:hash(fs.readFileSync(output+'/verification.json'))}));
}catch(error){
  fs.writeFileSync(output+'/failure.json',JSON.stringify({stage,error:{name:error.name,message:error.message,stack:error.stack},results,transport,sourceGuards,dataGuards,retries:0},null,2)+'\n',{flag:'wx'});
  console.error(error.stack);process.exitCode=1;
}
