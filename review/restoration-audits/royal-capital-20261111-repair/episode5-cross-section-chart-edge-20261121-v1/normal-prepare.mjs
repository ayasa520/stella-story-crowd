// Prepare exactly one baseline-owned directory relation through the existing
// canonical editor. This module never writes a checkout, invokes a serializer,
// adopts importer ownership, or turns a preview object into publisher input.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,readdir,realpath} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {getPriority} from 'node:os';
import {readSnapshot,loadCanonicalEditor} from '../adapter-preparation/offline-editor.mjs';

const here=fileURLToPath(new URL('./',import.meta.url)),root=resolve(here,'../../..');
const self=fileURLToPath(import.meta.url),sha=raw=>createHash('sha256').update(raw).digest('hex');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',maxBuffer:32*1024*1024}).trim();
const same=(a,b)=>assert.deepEqual(a,b);
const args=process.argv.slice(2),options=new Map();
assert.equal(args.length,6);
for(let i=0;i<args.length;i+=2){
  assert.ok(['--decision','--decision-sha256','--output'].includes(args[i]));
  assert.ok(args[i+1]&&!options.has(args[i]));options.set(args[i],args[i+1]);
}
assert.equal(getPriority(),19);
assert.match(await readFile('/proc/self/status','utf8'),/^Cpus_allowed_list:\s*(?:0-1|0,1)\s*$/m);
const decisionPath=resolve(options.get('--decision')),decisionRaw=await readFile(decisionPath);
assert.equal(sha(decisionRaw),options.get('--decision-sha256'));
const decision=JSON.parse(decisionRaw);
assert.equal(decision.schema,'stella.episode5-directory-edge-root-decision.v1');
assert.equal(typeof decision.rootConfirmed,'boolean');
assert.equal(sha(await readFile(self)),decision.helperSha256);
const output=resolve(here,options.get('--output'));
assert.ok(output.startsWith(here)&&output!==here.slice(0,-1));
assert.ok(((await realpath(resolve(output,'..')))+sep).startsWith(here));
const guardsRaw=await readFile(decision.guardsPath),intentRaw=await readFile(decision.intentPath);
assert.equal(sha(guardsRaw),decision.guardsSha256);assert.equal(sha(intentRaw),decision.intentSha256);
const guards=JSON.parse(guardsRaw),intent=JSON.parse(intentRaw);
assert.equal(guards.schema,'stella.directory-save-complete-guards.v1');
assert.equal(guards.intentSha256,decision.intentSha256);assert.equal(guards.helperSha256,decision.helperSha256);
assert.equal(intent.schema,'stella.episode5-one-source-directory-edge-intent.v1');
assert.equal(intent.rootConfirmed,false);assert.equal(intent.executionAllowed,false);
same(intent.sceneIds,[10090013,10090014,10090015]);same(guards.sceneIds,intent.sceneIds);
same(guards.readOnlySceneIds,[10020001]);assert.equal(intent.sourceSceneId,10090015);assert.equal(intent.targetSceneId,10020001);
same(intent.expectedFormalPaths,['native/scenes/10090015.json','manifest.json']);
const candidatePath=resolve(intent.sourceCandidate.path),candidateRaw=await readFile(candidatePath);
assert.equal(candidatePath,resolve(here,'../episode5-finish-scene-edge-owner-plan-20261121-v1/candidate.rootfalse.json'));
assert.equal(sha(candidateRaw),intent.sourceCandidate.sha256);
const candidate=JSON.parse(candidateRaw);
assert.equal(candidate.rootConfirmed,false);assert.equal(candidate.executionAllowed,false);
same(intent.edge,candidate.candidateEdge);
assert.equal(intent.edge.id,'scene-edge:10090015:10020001');
assert.equal(intent.edge.source,'scene:10090015');assert.equal(intent.edge.target,'scene:10020001');
same(intent.expectedOwnerNextBefore,[]);
same(intent.expectedOwnerNextAfter,[{scene_id:10020001,section_id:1002}]);

// A true result requires a separate root-authored approval of an exact false
// preview. Its decision SHA must differ from the current decision, and the
// preview has no PublicationFile values to promote. Both branches below still
// recompute the canonical mutation and serializer inputs from the frozen disk.
if(decision.rootConfirmed){
  const approval=decision.approval;
  assert.equal(approval?.rootConfirmed,true);
  assert.equal(approval.action,'prepare-one-source-directory-edge-publication-files');
  for(const key of ['intentSha256','guardsSha256','helperSha256'])assert.equal(approval[key],decision[key]);
  assert.equal(approval.dataHead,guards.dataHead);assert.equal(approval.sourceHead,guards.sourceHead);
  assert.ok(typeof approval.approvalId==='string'&&approval.approvalId.length>=8);
  const previewPath=await realpath(resolve(approval.previewPath));assert.ok(previewPath.startsWith(here));
  const previewRaw=await readFile(previewPath);assert.equal(sha(previewRaw),approval.previewSha256);
  const preview=JSON.parse(previewRaw);
  assert.equal(preview.schema,'stella.offline-editor-publication.v1');
  assert.equal(preview.rootConfirmed,false);assert.equal(preview.publishable,false);assert.equal(preview.previewOnly,true);
  assert.ok(!Object.hasOwn(preview,'files'));
  assert.equal(preview.intentSha256,decision.intentSha256);assert.equal(preview.guardSetSha256,decision.guardsSha256);
  assert.equal(preview.helperSha256,decision.helperSha256);assert.equal(preview.baseSha,guards.dataHead);
  assert.equal(preview.canonicalSha,guards.sourceHead);assert.notEqual(preview.decisionSha256,sha(decisionRaw));
  same(preview.publicationPaths,intent.expectedFormalPaths);
}else assert.equal(decision.approval,null);

const data=resolve(guards.dataRoot),canonical=resolve(guards.sourceRoot);
assert.equal(data,resolve(root,'artifacts/stella-script-continuation-20261121/data-checkout'));
assert.equal(canonical,resolve(root,'artifacts/stella-site-repair-source/.sites-checkout'));
same(guards.ownedSummaryDigestMismatches,[]);assert.equal(guards.ownedSummaryCount,121);
for(const [path,expected]of Object.entries(intent.requiredSourceFileSha256))assert.equal(guards.sourceFiles[path],expected);
assert.equal(git(canonical,'merge-base',intent.requiredSourceFixCommit,guards.sourceHead),intent.requiredSourceFixCommit);

async function inventory(base,prefix=''){
  const names=[];
  for(const entry of await readdir(resolve(base,prefix),{withFileTypes:true})){
    const name=prefix?prefix+'/'+entry.name:entry.name;
    if(entry.isDirectory())names.push(...await inventory(base,name));
    else{assert.ok(entry.isFile(),'Guarded build inventory cannot follow symlinks');names.push(name);}
  }
  return names.sort();
}
async function verify(){
  for(const [path,expected]of [[data,guards.dataHead],[canonical,guards.sourceHead]])assert.equal(git(path,'rev-parse','HEAD'),expected);
  assert.equal(git(data,'status','--short'),guards.dataStatus);assert.equal(git(canonical,'status','--short'),guards.sourceStatus);
  for(const name of ['manifest.json','review/native-restoration.json','assets/catalog.json','assets/package.json'])assert.ok(Object.hasOwn(guards.dataFiles,name));
  for(const [base,map]of [[data,guards.dataFiles],[canonical,guards.sourceFiles],[resolve(canonical,'dist'),guards.distFiles]]){
    assert.ok(Object.keys(map).length>0);
    for(const [name,expected]of Object.entries(map)){
      assert.ok(!name.startsWith('/')&&!name.split('/').some(p=>p==='..'||p==='.'||!p));
      const path=await realpath(resolve(base,name));assert.ok(path.startsWith(base+sep));
      assert.equal(sha(await readFile(path)),expected,name);
    }
  }
  for(const prefix of ['native/scenes','review/scenes','review/restoration-batches']){
    const actual=(await readdir(resolve(data,prefix))).filter(n=>n.endsWith('.json')).map(n=>prefix+'/'+n).sort();
    same(actual,Object.keys(guards.dataFiles).filter(n=>n.startsWith(prefix+'/')).sort());
  }
  const tracked=[];
  for(const path of git(canonical,'ls-files','-z').split('\0').filter(Boolean)){
    await realpath(resolve(canonical,path));tracked.push(path);
  }
  same(tracked.sort(),Object.keys(guards.sourceFiles).sort());
  same(await inventory(resolve(canonical,'dist')),Object.keys(guards.distFiles).sort());
  for(const [path,expected]of [
    [resolve(root,'story_studio/recovery/native_repair.py'),guards.nativeRepairSha256],
    [resolve(root,'story_studio/crowd_seed.py'),guards.crowdSeedSha256],
    [resolve(here,'../adapter-preparation/offline-editor.mjs'),guards.offlineLoaderSha256],
    [resolve(here,'../prepare-publication-patches.py'),guards.serializerSha256],
    [candidatePath,intent.sourceCandidate.sha256],[self,decision.helperSha256],
    [decision.intentPath,decision.intentSha256],[decision.guardsPath,decision.guardsSha256],
    [decisionPath,sha(decisionRaw)],
  ])assert.equal(sha(await readFile(path)),expected,path);
}
await verify();
const loaded=await readSnapshot(data,guards.dataHead,intent.sceneIds);
for(const [name,text]of Object.entries(loaded.files))assert.equal(sha(text),guards.dataFiles[name]);
same(loaded.snapshot.sources.map(s=>s.entry.id),intent.sceneIds);
const ownership=JSON.parse(await readFile(resolve(data,'review/native-restoration.json')));
assert.equal(Object.keys(ownership.scenes).length,121);assert.ok(!Object.hasOwn(ownership.scenes,'10090015'));
const sourceSection=loaded.snapshot.manifest.chapters.flatMap(c=>c.sections).find(s=>s.id===1009);
same(sourceSection.sceneIds,intent.sceneIds);
// The destination is explicitly guarded and inspected, but is never passed to
// readSnapshot or included as an editable source. Its importer ownership and
// any foreign chart copies cannot become this directory edit's write scope.
const targetName='native/scenes/10020001.json',targetRaw=await readFile(resolve(data,targetName));
assert.equal(sha(targetRaw),guards.dataFiles[targetName]);
const target=JSON.parse(targetRaw),targetRoots=target.scenario_list.filter(row=>row.is_root===1);
assert.equal(targetRoots.length,1);assert.equal(targetRoots[0].scenario_id,1);assert.equal(targetRoots[0].uniq_id,1002000100001);
assert.equal(loaded.snapshot.manifest.scenes.find(s=>s.id===10020001).sectionId,1002);
assert.ok(!loaded.snapshot.sources.some(s=>s.entry.id===10020001));
globalThis.fetch=async()=>{throw Error('Directory edge preparation prohibits network and publishing');};
const editor=await loadCanonicalEditor(canonical,{canonicalSha:guards.sourceHead,
  studioNativeSha256:guards.sourceFiles['lib/studio-native.ts'],nativeRepairSha256:guards.nativeRepairSha256});
const base=loaded.snapshot,next=structuredClone(base),beforeProject=editor.api.studioProject(base,loaded.assets);
const ownerBefore=base.sources.find(s=>s.entry.id===10090015),ownRows=ownerBefore.document.chartmap.scene_list;
const ownerIndexes=ownRows.flatMap((row,index)=>row.scene_id===10090015?[index]:[]);assert.equal(ownerIndexes.length,1);
const ownerIndex=ownerIndexes[0];same(ownRows[ownerIndex].next_scene_list,[]);
assert.equal(ownerBefore.document.scenario_list.length,53);
const finish=ownerBefore.document.scenario_list.find(row=>row.scenario_id===47).branch_list.find(b=>b.branch_id===471);
assert.equal(finish.transition_list.length,1);
assert.equal(finish.transition_list[0].next_scenario_label,'FINISH');assert.equal(finish.transition_list[0].next_section_id,1002);
assert.equal(finish.transition_list[0].next_scene_id,10020001);assert.equal(finish.transition_list[0].next_scenario_id,0);
assert.ok(!beforeProject.directory.edges.some(e=>e.id===intent.edge.id||e.source===intent.edge.source&&e.target===intent.edge.target));
const result=editor.api.applyStudioMutation(next,beforeProject,'directory/edit',{
  sceneId:10090015,scopeSceneId:10090015,operation:'save_edge',edge:structuredClone(intent.edge),
});
assert.equal(result.sceneId,10090015);
// Publisher values are obtained ONLY from the normal canonical serializer.
// Expected copies below are assertions about its output, never replacement
// writer logic. In particular, no refreshReviewSummary call belongs to this API.
const files=editor.api.studioPublicationFiles(base,next);
same(files.map(f=>f.path),intent.expectedFormalPaths);
const ownerAfter=next.sources.find(s=>s.entry.id===10090015);
const expectedDocument=structuredClone(ownerBefore.document);
expectedDocument.chartmap.scene_list[ownerIndex].next_scene_list=structuredClone(intent.expectedOwnerNextAfter);
same(ownerAfter.document,expectedDocument);same(ownerAfter.document.scenario_list,ownerBefore.document.scenario_list);
for(const prior of base.sources){
  const current=next.sources.find(s=>s.entry.id===prior.entry.id);same(current.review,prior.review);
  if(prior.entry.id!==10090015)same(current.document,prior.document);
}
const savedEdge={...structuredClone(intent.edge),nativeTarget:{scene_id:10020001,section_id:1002}};
const expectedManifest=structuredClone(base.manifest);
assert.ok(!expectedManifest.studioDirectory.edges.some(e=>e.id===intent.edge.id));
expectedManifest.studioDirectory.edges.push(savedEdge);same(next.manifest,expectedManifest);
// Canonical studioPublicationFiles may refresh a changed scene summary. This
// particular baseline already has that exact status: assert every summary,
// including all121 importer-owned summaries, remains value-identical.
same(next.manifest.scenes,base.manifest.scenes);
for(const id of Object.keys(ownership.scenes))same(next.manifest.scenes.find(s=>s.id===Number(id)),base.manifest.scenes.find(s=>s.id===Number(id)));
const afterProject=editor.api.studioProject(next,loaded.assets);
same(afterProject.nodes,beforeProject.nodes);same(afterProject.edges,beforeProject.edges);
same({...afterProject,directory:beforeProject.directory},beforeProject);
const entryBefore=beforeProject.directory.entries.find(e=>e.id==='scene:10090015');
const entryAfter=afterProject.directory.entries.find(e=>e.id==='scene:10090015');
assert.equal(entryBefore.native_interval.next_scene_count,0);assert.equal(entryAfter.native_interval.next_scene_count,1);
assert.equal(entryBefore.native_interval.next_scene_count>1,false);assert.equal(entryAfter.native_interval.next_scene_count>1,false);
const expectedEntries=structuredClone(beforeProject.directory.entries);
expectedEntries.find(e=>e.id==='scene:10090015').native_interval.next_scene_count=1;
same(afterProject.directory.entries,expectedEntries);
same(afterProject.directory.sources,beforeProject.directory.sources);
same(afterProject.directory.edges,[...beforeProject.directory.edges,savedEdge]);
const sourceNodes=afterProject.nodes.filter(n=>n.scene_id==='scene:10090015');assert.equal(sourceNodes.length,53);
const sourceIds=new Set(sourceNodes.map(n=>n.id)),sourceEdges=afterProject.edges.filter(e=>sourceIds.has(e.source));assert.equal(sourceEdges.length,54);
for(const [path,expected]of Object.entries(editor.sourceHashes))assert.equal(sha(await readFile(path)),expected,path);
await verify();
const audit=[
  {file:'native/scenes/10090015.json',path:['chartmap','scene_list',ownerIndex,'next_scene_list'],before:[],after:intent.expectedOwnerNextAfter},
  {file:'manifest.json',path:['studioDirectory','edges',base.manifest.studioDirectory.edges.length],beforeAbsent:true,after:savedEdge},
];
const common={schema:'stella.offline-editor-publication.v1',baseSha:guards.dataHead,canonicalSha:guards.sourceHead,
  rootConfirmed:decision.rootConfirmed,publishable:decision.rootConfirmed,previewOnly:!decision.rootConfirmed,
  missingResources:[],ownershipAdopted:false,formalDataWritten:false,sourceWritten:false,playbackVerified:false,wholeSceneAccepted:false,
  sceneIds:intent.sceneIds,readOnlySceneIds:[10020001],audit,guardSetSha256:sha(guardsRaw),decisionSha256:sha(decisionRaw),
  intentSha256:sha(intentRaw),helperSha256:decision.helperSha256,sourceHashes:editor.sourceHashes,
  ownershipSha256:guards.dataFiles['review/native-restoration.json'],allDiskGuardsUnchanged:true,
  preservation:{scenarioRows53Unchanged:true,allReviewsUnchanged:true,all139OtherNativeFilesUnchanged:true,
    targetNotEditable:true,all121OwnedSummariesUnchanged:true,ownershipLedgerBytesUnchanged:true},
  projection:{nodesDeepEqual:true,edgesDeepEqual:true,sourceNodes:53,sourceExecutableEdges:54,
    nativeIntervalCount:{before:0,after:1},isBranchPredicate:'next_scene_count > 1',isBranchBefore:false,isBranchAfter:false,
    beforeNotExposedByStudioProject:true,beforeRequiresSeparateNormalPrepareComparison:true,
    wholePrepareObjectEqualityClaimed:false},
};
// False outputs intentionally omit files and publisher base/content objects.
// Approval recomputes files above from current guarded input; nothing is read
// back out of an old preview to construct the approved PublicationFiles.
const publication=decision.rootConfirmed?{...common,files}:{...common,publicationPaths:files.map(f=>f.path)};
await mkdir(output);
await writeFile(resolve(output,decision.rootConfirmed?'publication.json':'preview.rootfalse.json'),JSON.stringify(publication,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({rootConfirmed:decision.rootConfirmed,output,publicationPaths:files.map(f=>f.path),formalDataWritten:false}));
