// Root review of immutable captures, not another HTTP attempt. Keep the failed
// exact-program comparison and its inputs intact. The one permitted difference
// is recorded as two original values; never normalize either returned program.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

const area='/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121';
const repo=path.join(area,'data-checkout');
const source='/home/rikka/Projects/stella/artifacts/stella-site-repair-source/.sites-checkout';
const capture=path.join(area,'episode5-silent54-production-readback-v1');
const output=path.join(area,'episode5-silent54-root-production-acceptance-v1');
const scriptCommit='1e3bfa85b461484a0a8e3e7478c98aae2ef6c644';
const sourceHead='643f88a0928fe6bda8ac1c6fac9409a2fbdbdf0f';
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const read=file=>JSON.parse(fs.readFileSync(file));
const witness=file=>{const bytes=fs.readFileSync(file);return {path:file,bytes:bytes.length,sha256:hash(bytes)};};
const checked=(file,expected)=>{const result=witness(file);assert.equal(result.sha256,expected);return result;};
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',maxBuffer:64*1024*1024}).trim();
const blob=member=>execFileSync('git',['show',scriptCommit+':'+member],{cwd:repo,maxBuffer:64*1024*1024});
const write=(name,value)=>fs.writeFileSync(path.join(output,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});

assert.equal(fs.existsSync(output),false,'Do not overwrite an earlier decision');
assert.equal(git(repo,'rev-parse','HEAD'),scriptCommit);
assert.equal(git(source,'rev-parse','HEAD'),sourceHead);
assert.equal(git(repo,'status','--porcelain'),'');
assert.equal(git(source,'diff','--name-only','HEAD'),'');
const peerFile=path.join(area,'episode5-silent54-production-scope-review-v1/verification.json');
const peerWitness=checked(peerFile,'4d9fcc24aebc68e567e7f52e7706834045400b8fd620b0e8af291e9567a7060a');
const peer=read(peerFile);
assert.equal(peer.rootConfirmed,false);
const helper=checked(path.join(area,'verify-episode5-silent54-production-scope-v1.mjs'),'4f005c700c0c1bbe81165adbbb8ff63f7cb6e6cd5821025101370a586125b2c8');
const failed=checked(path.join(capture,'failure.json'),'5f0ce298f1fecd0a6556cdf3a9fd25da7f7b58101798de1a09632cbfd2bbe9ad');
const receiptFile=path.join(capture,'http-receipt.json');
const receipt=read(receiptFile);
assert.equal(receipt.records.length,2);
const bodies=receipt.records.map(record=>{
  assert.equal(record.status,200);assert.equal(record.bodyComplete,true);
  const packed=fs.readFileSync(path.join(capture,record.gzipFile));
  assert.equal(hash(packed),record.gzipSha256);
  const raw=zlib.gunzipSync(packed);
  assert.equal(hash(raw),record.decodedResponseSha256);
  assert.equal(raw.length,record.decodedResponseBytes);
  return JSON.parse(raw);
});
const [published,production]=bodies;
assert.equal(published.headSha,scriptCommit);assert.equal(production.headSha,scriptCommit);
const committed=peer.inputs.committedFiles.map(binding=>{
  const raw=blob(binding.path);
  assert.equal(hash(raw),binding.sha256);assert.equal(raw.length,binding.bytes);
  assert.equal(hash(fs.readFileSync(path.join(repo,binding.path))),binding.sha256);
  return {...binding,value:JSON.parse(raw)};
});
assert.deepEqual(published.document,committed.find(x=>x.path.startsWith('native/')).value);
assert.deepEqual(published.review,committed.find(x=>x.path.startsWith('review/')).value);
checked(peer.inputs.referenceGzip.path,peer.inputs.referenceGzip.sha256);
const localRaw=zlib.gunzipSync(fs.readFileSync(peer.inputs.referenceGzip.path));
assert.equal(hash(localRaw),peer.inputs.localRawSha256);
const local=JSON.parse(localRaw);
const owns=id=>id?.startsWith('node:10090015:');
const nodes=production.nodes.filter(node=>owns(node.id));
assert.equal(nodes.length,53);
assert.deepEqual(nodes,local.nodes.filter(node=>owns(node.id)));
const edges=production.edges.filter(edge=>owns(edge.source));
const localEdges=local.edges.filter(edge=>owns(edge.source));
assert.equal(edges.length,54);assert.equal(localEdges.length,54);
const boundaryId=peer.uniqueBoundaryDifference.edgeId;
const ordinary=edges.filter(edge=>edge.id!==boundaryId);
assert.equal(ordinary.length,53);
assert.deepEqual(ordinary,localEdges.filter(edge=>edge.id!==boundaryId));
const boundary=edges.find(edge=>edge.id===boundaryId);
const reference=localEdges.find(edge=>edge.id===boundaryId);
assert.deepEqual(boundary,peer.uniqueBoundaryDifference.productionEdge);
assert.deepEqual(reference,peer.uniqueBoundaryDifference.localEdge);
const {target:productionTarget,...productionContract}=boundary;
const {target:localTarget,...localContract}=reference;
assert.equal(productionTarget,'');assert.equal(localTarget,'node:10020001:1002000100001');
assert.deepEqual(productionContract,localContract);
assert.deepEqual(production.before,local.before);
assert.equal(production.nodes.length,105);assert.equal(local.nodes.length,5620);
assert.equal(boundary.available,true);assert.equal(boundary.flow_action,'section');
assert.equal(boundary.transition.label,'FINISH');
assert.ok(local.nodes.some(node=>node.id===localTarget));
assert.ok(!production.nodes.some(node=>node.id===localTarget));
const nextRaw=blob('native/scenes/10020001.json');
assert.equal(hash(nextRaw),peer.committedNextRoot.nativeFile.sha256);
const roots=JSON.parse(nextRaw).scenario_list.filter(row=>row.is_root===1);
assert.equal(roots.length,1);assert.equal(roots[0].uniq_id,1002000100001);
const excerpts=[];
for(const [member,binding] of Object.entries(peer.sourceContract)){
  const file=path.join(source,member);checked(file,binding.sha256);
  const lines=fs.readFileSync(file,'utf8').split('\n');
  excerpts.push({member,...binding,excerpts:binding.ranges.map(range=>{
    const [first,last=first]=range.split('-').map(Number);
    return {first,last,lines:lines.slice(first-1,last)};
  })});
}
const runtimeClosure=checked(path.join(area,'episode5-silent54-attempt2-root-closure-v1.json'),'f9a52f53f2985eb41eb72012040ebdeb884f3407910c2a2f099d3eca37aae681');
const imageReview=checked(path.join(area,'episode5-silent54-actual-image-review-v1/review.json'),'cd28f85225c01098a5515a77e106fbc6c3ae1e5faed953aeaeedc03463b3add3');
const ack=checked(path.join(area,'episode5-silent54-script-main-ACK-v1.json'),'1cc39cd2827213180e77a17e856c6b75ff8ab6efc7a5564fb7d13fca33993f36');
assert.equal(read(ack.path).finalRead.stdout,scriptCommit+'\trefs/heads/main\n');
assert.equal(witness(failed.path).sha256,failed.sha256);
fs.mkdirSync(output);
write('source-contract-excerpts.json',{sourceHead,rootReadSource:true,rootViewedImages:false,files:excerpts});
write('root-acceptance.json',{
  schema:'stella.episode5.silent54.root-production-acceptance.v1',rootConfirmed:true,
  status:'accepted-bounded-production-readback-with-explicit-scope-difference',scriptCommit,sourceHead,
  productionResponses:receipt.records.map(record=>({method:record.method,url:record.requestedUrl,status:record.status,decodedResponseSha256:record.decodedResponseSha256})),
  nodesExact:53,nonBoundaryEdgesExact:53,totalSourceEdges:54,beforeExact:true,
  boundary:{id:boundaryId,onlyDifferentField:'target',productionTarget,localTarget,allOtherFieldsExact:true,
    available:true,action:'section',transition:boundary.transition,nativeTransition:boundary.native_transition},
  sourceConclusion:'Current-section loading omits the next root. The available FINISH+section completes before generic target lookup; chart links use current-section scene relations. This is supported by the pinned source, not a new production-browser test.',
  productionSectionNodes:105,localFullLibraryNodes:5620,wholeProgramEquivalent:false,
  originalExactAll54EdgesVerifierStillFailed:failed,
  evidence:{independentReview:peerWitness,independentHelper:helper,httpReceipt:witness(receiptFile),runtimeClosure,imageReview,scriptAck:ack},
  formalDataChanged:false,sourceChanged:false,workerRedeployed:false,newHttpPerformed:false,newBrowserPerformed:false,
  rootViewedImages:false,wholeSceneAccepted:false,wholeEpisodeAccepted:false,
  remaining:['vendor45 entry/action','Subaru54 stern face','Subaru46 reaction body/face','fuon01 provider and phase','continuous54-to46 full-frame holding and exact timing','subjective audio audition'],
  fullGoalStatus:'active'
});
console.log(JSON.stringify({output,acceptance:witness(path.join(output,'root-acceptance.json')),excerpts:witness(path.join(output,'source-contract-excerpts.json'))}));
