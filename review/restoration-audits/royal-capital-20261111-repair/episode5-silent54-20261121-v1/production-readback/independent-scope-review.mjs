// Offline review of the two already captured production responses only.
// The earlier exact-all-edges failure remains immutable. This comparison
// permits one explicit scope-dependent target field, without changing either
// returned program or applying a general edge normalization/exception policy.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

const root='/home/rikka/Projects/stella';
const area=path.join(root,'artifacts/stella-script-continuation-20261121');
const repo=path.join(area,'data-checkout');
const source=path.join(root,'artifacts/stella-site-repair-source/.sites-checkout');
const captured=path.join(area,'episode5-silent54-production-readback-v1');
const runtime=path.join(area,'episode5-silent54-saved-runtime-v2/attempt-2');
const out=path.join(area,'episode5-silent54-production-scope-review-v1');
const expected='1e3bfa85b461484a0a8e3e7478c98aae2ef6c644';
const sourceHead='643f88a0928fe6bda8ac1c6fac9409a2fbdbdf0f';
const localRawSha='8cfee866f5a09695937da49d5d8271e6f3b11993c4d88954f2ef7e2fe31d1faa';
const productionRawSha='eb02f98cd4baf5a45a0a3bffc93df8af1ea57d0f8d024eefb865cc3487d06d07';
const boundaryId='edge:node:10090015:node_3e6d1c90667f:1009001510471:471';
const nextRootId='node:10020001:1002000100001';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const witness=p=>{const raw=fs.readFileSync(p);return {path:p,bytes:raw.length,sha256:hash(raw)};};
const json=p=>JSON.parse(fs.readFileSync(p));
const own=id=>typeof id==='string'&&id.startsWith('node:10090015:');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',env:{...process.env,GIT_OPTIONAL_LOCKS:'0'}}).trim();
const committed=member=>{
  // The committed manifest is over4MiB. Retain the original stdout Buffer and
  // explicitly bound git-show buffering; the default1MiB would fail locally
  // before any comparison. No decoder/parser replacement or retry is used.
  const raw=execFileSync('git',['show',expected+':'+member],{cwd:repo,maxBuffer:64*1024*1024,
    env:{...process.env,GIT_OPTIONAL_LOCKS:'0'}});
  return {path:member,bytes:raw.length,sha256:hash(raw),value:JSON.parse(raw)};
};
const sources={
  'lib/preview.ts':{sha256:'a86d28a5fcb8d5e85ff53c8422eaa5d418c4e9b72f6552c6724a612b6ce50af8',ranges:['61-84'],finding:'Root target resolves only from loaded sources; section action remains available without a loaded node target.'},
  'lib/studio-native.ts':{sha256:'1c803e7df178f900f4d5cc0cac1728492703e0f8b4d8e898e2009a2a6507d0c8',ranges:['71-98','185-201'],finding:'Cloudflare loads current section bodies; stable idMap cannot name an unloaded next-section root.'},
  'lib/studio-api.ts':{sha256:'5bc737e5638b1c5f482d375faab08c6e4ebfc426b66922f7b6f5154c7c05b33c',ranges:['130-135','155-162'],finding:'Normal prepare returns section projection and independently resolved before.'},
  'lib/native.ts':{sha256:'90df2675b0fec4e9fa853de0c380fa7b2f2c89a35d54cd2f04322f59dd669015',ranges:['36-65'],finding:'Positive FINISH section/scene pair is validated against the complete manifest directory.'},
  'public/player/player.js':{sha256:'5f2ae9d24449d6dd7d197af05f6ae70fae9e7ca508f65c4ec8584d7920b0548c',ranges:['692','779-802','847-859'],finding:'Title checks edge.available then calls follow; FINISH+section completes/chart/returns before generic target lookup/enter.'},
  'public/player/flow_view.js':{sha256:'5d69218e1e52631f1e3b78fd19cd94abc5021e675c77ab80d0f15329cb410f21',ranges:['23-34','58-67'],finding:'Completed chart uses actual chartLayout and has no successor playback action.'},
  'public/player/flow_layout.js':{sha256:'7ddfc4d29503f6f54c0ccae0fa0b483f56fd890f4b464db9a242a4a90981320f',ranges:['6-15','21-35'],finding:'Current section positions and scene-level relations determine links; cross-section node target is not a chart input.'},
};

assert.equal(fs.existsSync(out),false,'New independent output only');fs.mkdirSync(out);
let stage='read-captured-inputs';
const originalFailure=witness(path.join(captured,'failure.json'));
try{
  assert.equal(git(repo,'rev-parse','HEAD'),expected);
  assert.equal(git(source,'rev-parse','HEAD'),sourceHead);
  for(const [member,proof]of Object.entries(sources))assert.equal(witness(path.join(source,member)).sha256,proof.sha256);
  const receipt=json(path.join(captured,'http-receipt.json'));
  assert.equal(receipt.records.length,2);assert.deepEqual(receipt.records.map(r=>r.status),[200,200]);
  assert.ok(receipt.records.every(r=>r.bodyComplete));
  const bodies=receipt.records.map(record=>{
    const gzip=fs.readFileSync(path.join(captured,record.gzipFile));
    assert.equal(hash(gzip),record.gzipSha256);const raw=zlib.gunzipSync(gzip);
    assert.equal(raw.length,record.decodedResponseBytes);assert.equal(hash(raw),record.decodedResponseSha256);
    return JSON.parse(raw);
  });
  const [published,production]=bodies;
  assert.equal(receipt.records[0].method,'GET');
  assert.equal(receipt.records[0].requestedUrl,'https://stella-preview.jaoushingan.com/api/native/source?sceneId=10090015');
  assert.equal(receipt.records[1].method,'POST');
  assert.deepEqual(receipt.records[1].request,{id:'node:10090015:node_dae6816ae851',baseSha:expected,choices:{}});
  assert.equal(receipt.records[1].decodedResponseSha256,productionRawSha);
  assert.equal(published.headSha,expected);assert.equal(production.headSha,expected);
  const manifest=committed('manifest.json'),native=committed('native/scenes/10090015.json'),review=committed('review/scenes/10090015.json');
  assert.deepEqual(published.document,native.value);assert.deepEqual(published.review,review.value);
  const actualRuntime=json(path.join(runtime,'result.json'));
  assert.deepEqual(actualRuntime.cases.map(c=>c.language),['zh','ja']);
  assert.ok(actualRuntime.cases.every(c=>c.prepared.rawSha256===localRawSha));
  const gzipFile=actualRuntime.cases[0].prepared.gzipFile;
  assert.equal(gzipFile,actualRuntime.cases[1].prepared.gzipFile);
  const localRaw=zlib.gunzipSync(fs.readFileSync(path.join(runtime,gzipFile)));
  assert.equal(hash(localRaw),localRawSha);const local=JSON.parse(localRaw);
  stage='exact-target-and-single-scope-boundary';
  assert.equal(production.start,local.start);
  const localNodes=local.nodes.filter(n=>own(n.id)),nodes=production.nodes.filter(n=>own(n.id));
  assert.equal(nodes.length,53);assert.deepEqual(nodes,localNodes);
  const localEdges=local.edges.filter(e=>own(e.source)),edges=production.edges.filter(e=>own(e.source));
  assert.equal(edges.length,54);assert.equal(localEdges.length,54);
  assert.deepEqual(edges.map(e=>e.id),localEdges.map(e=>e.id));
  assert.equal(edges.filter(e=>e.id===boundaryId).length,1);
  const boundary=edges.find(e=>e.id===boundaryId),localBoundary=localEdges.find(e=>e.id===boundaryId);
  const nonBoundary=edges.filter(e=>e.id!==boundaryId),localNonBoundary=localEdges.filter(e=>e.id!==boundaryId);
  assert.equal(nonBoundary.length,53);assert.deepEqual(nonBoundary,localNonBoundary);
  // Destructure a comparison projection only. Neither original program nor
  // either target is assigned, seeded or rewritten; retain both full edges.
  const {target:productionTarget,...productionOther}=boundary;
  const {target:localTarget,...localOther}=localBoundary;
  assert.deepEqual(productionOther,localOther);assert.equal(productionTarget,'');assert.equal(localTarget,nextRootId);
  assert.equal(boundary.source,'node:10090015:node_3e6d1c90667f');
  assert.equal(boundary.available,true);assert.equal(boundary.state,'confirmed');assert.equal(boundary.flow_action,'section');
  assert.deepEqual(boundary.transition,{label:'FINISH',section:'section:1002',scene:'scene:10020001',entry:'root'});
  assert.equal(boundary.target_scene,'scene:10020001');
  assert.deepEqual(boundary.native_transition,{uniq_id:1009001510471,transition_id:47101,next_scenario_id:0,
    next_scenario_label:'FINISH',next_section_id:1002,next_scene_id:10020001});
  assert.deepEqual(production.before,local.before);
  stage='committed-next-root-and-production-scope';
  const nextEntry=manifest.value.scenes.find(s=>s.id===10020001);assert.equal(nextEntry.sectionId,1002);
  const owningSection=manifest.value.chapters.flatMap(c=>c.sections).find(s=>s.id===1002);
  assert.ok(owningSection.sceneIds.includes(10020001));
  const nextNative=committed(nextEntry.path),roots=nextNative.value.scenario_list.filter(n=>n.is_root===1);
  assert.equal(roots.length,1);assert.equal(roots[0].scenario_id,1);assert.equal(roots[0].uniq_id,1002000100001);
  const localRoot=local.nodes.find(n=>n.id===nextRootId);assert.equal(localRoot.scene_id,'scene:10020001');assert.equal(localRoot.scenario_id,1);
  assert.ok(!production.nodes.some(n=>n.id===nextRootId||n.scene_id==='scene:10020001'));
  const sectionScenes=manifest.value.scenes.filter(s=>s.sectionId===1009).sort((a,b)=>a.id-b.id);
  assert.deepEqual(sectionScenes.map(s=>s.id),[10090013,10090014,10090015]);
  const productionSectionNodes=sectionScenes.reduce((sum,s)=>sum+s.nodeCount,0);
  assert.equal(productionSectionNodes,105);assert.equal(production.nodes.length,105);assert.equal(local.nodes.length,5620);
  assert.deepEqual([...new Set(production.nodes.map(n=>n.scene_id))].sort(),sectionScenes.map(s=>'scene:'+s.id));
  for(const scene of sectionScenes)assert.equal(production.nodes.filter(n=>n.scene_id==='scene:'+scene.id).length,scene.nodeCount);
  const currentDirectory=production.directory.entries.find(e=>e.id==='scene:10090015');assert.equal(currentDirectory.parent,'section:1009');
  assert.ok(production.directory.entries.some(e=>e.id==='section:1009'));
  assert.equal(witness(originalFailure.path).sha256,originalFailure.sha256);
  const result={schema:'stella.episode5.silent54.offline-production-scope-review.v1',rootConfirmed:false,
    status:'offline-target-readback-equal-with-one-source-proven-scope-target-difference',scriptCommit:expected,sourceHead,
    all53TargetNodesExact:true,all53NonBoundaryEdgesExact:true,totalSourceEdges:54,
    uniqueBoundaryDifference:{edgeId:boundaryId,allowedDifferentField:'target',allOtherFieldsExact:true,
      localTarget,productionTarget,localEdge:localBoundary,productionEdge:boundary},
    before:{fullObjectEqual:true,production:production.before,localSavedRuntime:local.before,stateModified:false},
    scope:{productionSectionNodes,localFullLibraryNodes:5620,sectionScenes:sectionScenes.map(s=>({id:s.id,nodeCount:s.nodeCount})),
      nextSectionLoaded:false,wholeProgramEquivalent:false,actualProductionPlaybackPerformed:false},
    committedNextRoot:{sectionId:1002,sceneId:10020001,scenarioId:roots[0].scenario_id,uniqId:roots[0].uniq_id,
      localStableNodeId:localRoot.id,nativeFile:{path:nextNative.path,bytes:nextNative.bytes,sha256:nextNative.sha256}},
    sourceContract:sources,staticConclusion:'Expected loaded-scope representation difference. Title follows an available edge; FINISH+section completes before generic node lookup. The chart uses the current section and scene-level relations, not this node target.',
    originalExactAll54EdgeFailure:{...originalFailure,stillFailed:true,unchanged:true,notRewrittenAsPass:true},
    inputs:{httpReceipt:witness(path.join(captured,'http-receipt.json')),httpResponses:receipt.records,
      runtimeResult:witness(path.join(runtime,'result.json')),referenceGzip:witness(path.join(runtime,gzipFile)),
      localRawSha256:localRawSha,productionRawSha256:productionRawSha,
      committedFiles:[manifest,native,review].map(({value,...p})=>p)},
    noNewHttpBrowserServerOrWorker:true,noProgramBeforeTargetSourceFormalDataOrGitWrite:true,noParserReplacementOrRetry:true,
    runtimePlaybackOrMotionFaceAcceptance:false};
  const file=path.join(out,'verification.json');fs.writeFileSync(file,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({file,sha256:witness(file).sha256,nodes:53,exactNonBoundaryEdges:53,soleDifferentField:'target',beforeEqual:true}));
}catch(error){
  fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({rootConfirmed:false,stage,error:{name:error.name,message:error.message,stack:error.stack},originalFailure,noNewHttp:true},null,2)+'\n',{flag:'wx'});
  console.error(error.stack||String(error));process.exitCode=1;
}
