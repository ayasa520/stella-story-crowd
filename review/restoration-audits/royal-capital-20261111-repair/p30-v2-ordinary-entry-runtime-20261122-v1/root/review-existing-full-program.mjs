// Independently inspect the retained ordinary response without invoking the
// Worker, its compiler, another API preparation, or any browser. This review
// does not reconstruct a replacement response: the original gzip and its raw
// JSON digest remain the only runtime comparison baseline. In particular, a
// successful comparison cannot manufacture the omitted provider-event trace.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';

const A='/home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121';
const K=path.join(A,'p30-node4-ordinary-entry-owner-kit-rootfalse-v2');
const O=path.dirname(new URL(import.meta.url).pathname);
const digest=b=>createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p));
const binding=read(path.join(K,'frozen/binding.json'));
const manifest=read(path.join(binding.dataRoot,'manifest.json'));
const semantics=read(path.join(binding.sourceRoot,'config/semantics.json'));
const zipped=fs.readFileSync(path.join(K,'prepared/p30-node4-unchanged-ordinary.raw.json.gz'));
const raw=gunzipSync(zipped),program=JSON.parse(raw);
const receipt=read(path.join(K,'prepared/p30-node4-unchanged-ordinary.receipt.json'));
const http=read(path.join(K,'prepared/p30-node4-unchanged-ordinary.http.json'));
const index=read(path.join(K,'prepared/index.json'));
const casePlan=binding.plans[0];
assert.equal(digest(raw),receipt.rawResponseSha256);
assert.equal(digest(raw),http.rawResponseSha256);
assert.equal(raw.length,receipt.rawResponseBytes);
assert.equal(digest(Buffer.from(JSON.stringify(program))),receipt.programSha256);
assert.deepEqual(index.receipts,[receipt]);
assert.equal(index.bindingSha256,digest(fs.readFileSync(path.join(K,'frozen/binding.json'))));
assert.equal(receipt.status,200);
assert.equal(program.headSha,binding.finalDataHead);
assert.equal(program.revision,parseInt(binding.finalDataHead.slice(0,12),16));
assert.equal(program.start,casePlan.start);
assert.deepEqual(program.before,receipt.before);
assert.equal(program.before.bg_picture,'bg/bg031b_stealshop');
assert.equal(program.before.model,'');
assert.deepEqual(program.before.actors,[]);
assert.equal(program.before.bg_music,'');

const nodeMap=new Map(program.nodes.map(n=>[n.id,n]));
const edgeMap=new Map(program.edges.map(e=>[e.id,e]));
assert.equal(nodeMap.size,program.nodes.length);
assert.equal(edgeMap.size,program.edges.length);
const expectedNodeIds=[],expectedEdgeIds=[],sources=[];
const visible=v=>v==='未設定'?'':v;
const stable=(scene,row,review)=>`node:${scene}:${review.scenarios[String(row.scenario_id)]?.studioNodeId||row.uniq_id}`;
let checkedNodes=0,checkedEdges=0;
for(const entry of manifest.scenes){
  const nativeBytes=fs.readFileSync(path.join(binding.dataRoot,entry.path));
  const reviewBytes=fs.readFileSync(path.join(binding.dataRoot,entry.reviewPath));
  assert.equal(digest(nativeBytes),binding.dataGuards[entry.path]);
  assert.equal(digest(reviewBytes),binding.dataGuards[entry.reviewPath]);
  const document=JSON.parse(nativeBytes),review=JSON.parse(reviewBytes);
  let background='',backgroundProvider=null;
  for(const row of document.scenario_list){
    const id=stable(entry.id,row,review),actual=nodeMap.get(id);
    assert.ok(actual,id);expectedNodeIds.push(id);
    const side=review.scenarios[String(row.scenario_id)]||{};
    const [body='',face='',...extras]=row.motion.split(',').map(s=>s.trim());
    const [bank='',cue='']=row.voice.split(',').map(s=>s.trim());
    if(row.bg_picture){background=row.bg_picture;backgroundProvider=row.scenario_id;}
    const expected={scenario_id:row.scenario_id,scene_id:`scene:${entry.id}`,
      kind:semantics.scenario_types.find(t=>t.value===row.scenario_type)?.kind,
      speaker:visible(row.msg_character),text:visible(side.sourceText||row.msg_text),
      translation:visible(row.msg_text),model:row.character.replace(/^live2d\/AC_/,''),
      body,face,extra_motions:extras.filter(Boolean),bank,cue,bg_picture:row.bg_picture,
      bg_music:row.bg_music,character_image:row.character_image,command:row.command,
      script_background:{mode:'native_array',resource:background,source_scenario_id:backgroundProvider},
      suppress_lip_motion:row.talk_chara==='0'};
    for(const [field,value]of Object.entries(expected))assert.deepEqual(actual[field],value,`${id}.${field}`);
    for(const branch of row.branch_list){
      const edgeId=`edge:${id}:${branch.uniq_id}:${branch.branch_id}`,edge=edgeMap.get(edgeId);
      assert.ok(edge,edgeId);expectedEdgeIds.push(edgeId);
      const branchReview=(side.branches||[]).find(v=>v.branchId===branch.branch_id)||{};
      const expectedEdge={source:id,source_scene:`scene:${entry.id}`,
        native_transition:branch.transition_list.length===1?branch.transition_list[0]:null,
        kind:branch.type===2||branch.type===3?'choice':'next',side:branch.type===2?'left':branch.type===3?'right':'',
        label:visible(branchReview.sourceLabel??branch.msg_quote_subject),
        quote:visible(branchReview.sourceQuote??branch.msg_quote),
        label_translation:visible(branch.msg_quote_subject),quote_translation:visible(branch.msg_quote),origin:'native'};
      for(const [field,value]of Object.entries(expectedEdge))assert.deepEqual(edge[field],value,`${edgeId}.${field}`);
      if(edge.available&&!['complete','section'].includes(edge.flow_action))assert.ok(nodeMap.has(edge.target),edgeId+' target');
      checkedEdges++;
    }
    checkedNodes++;
  }
  sources.push({sceneId:entry.id,nodes:document.scenario_list.length,nativeSHA256:digest(nativeBytes),reviewSHA256:digest(reviewBytes)});
}
assert.deepEqual(program.nodes.map(n=>n.id),expectedNodeIds);
assert.deepEqual(program.edges.map(e=>e.id),expectedEdgeIds);
assert.equal(checkedNodes,binding.allLibraryNodes);
assert.equal(checkedEdges,5870);
for(const step of casePlan.steps){
  const n=nodeMap.get(step.id);assert.equal(n.model,step.expectedModel);
  assert.deepEqual({body:n.body,face:n.face,extras:n.extra_motions},step.parsedMotion);
}
for(const link of casePlan.links){
  const edge=edgeMap.get(link.id);assert.equal(edge.available,true);
  assert.equal(edge.source,link.source);assert.equal(edge.target,link.target);
  assert.deepEqual(edge.native_transition,link.native_transition);
}
assert.equal(edgeMap.get(casePlan.stop.forbiddenEdge).native_transition.next_scenario_id,6);

const report={schema:'stella.p30.existing-full-program.root-review.v1',createdAt:new Date().toISOString(),
  rootConfirmed:true,preparedRawSHA256:digest(raw),preparedRawBytes:raw.length,
  gzipSHA256:digest(zipped),gzipBytes:zipped.length,
  finalDataHead:binding.finalDataHead,finalSourceHead:binding.finalSourceHead,
  scenes:sources.length,checkedNodes,checkedEdges,
  allOrderedCanonicalIdentitiesAndNativeFieldsExact:true,allOriginalBranchTransitionsExact:true,
  originalBeforeAndThreeNodeRouteExact:true,noReplacementProgramWritten:true,
  omittedTransportPreimport:true,preparationProviderTraceEstablished:false,
  runtimeOrMotionOrPhaseAccepted:false,sources};
const destination=path.join(O,'existing-full-program.root-review.json');
fs.writeFileSync(destination,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({path:destination,bytes:fs.statSync(destination).size,
  sha256:digest(fs.readFileSync(destination)),scenes:sources.length,checkedNodes,checkedEdges}));
