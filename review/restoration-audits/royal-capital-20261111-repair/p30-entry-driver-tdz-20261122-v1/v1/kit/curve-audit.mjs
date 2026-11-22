// After the defined observation boundary, compare actual archived decoded
// objects with the exact frozen canonical pure motion decoder. This runs in
// Node, does not sample a curve, and never touches a live actor or its clock.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const sha=b=>createHash('sha256').update(b).digest('hex');
export async function auditCurves(binding,report,plan){
  const parserPath=binding.sourceRoot+'/public/pairing/motion.js',parserBytes=await readFile(parserPath);
  const guarded=binding.fileGuards[parserPath]||binding.fileGuards['artifacts/stella-site-repair-source/.sites-checkout/public/pairing/motion.js'];
  assert.equal(sha(parserBytes),guarded,'Exact canonical pure decoder required');
  const {decodeMotion}=await import('data:text/javascript;base64,'+parserBytes.toString('base64'));
  const catalog=JSON.parse(await readFile(binding.dataRoot+'/assets/catalog.json','utf8')),members=new Map();
  for(const model of Object.values(catalog.models))for(const row of model.motions)
    members.set(row.member,{model:model.id,relative:'assets/'+row.url});
  const proofs=[];
  for(const clip of report.tap.clips){
    const source=members.get(clip.sourceRow?.member);assert.ok(source,'Archived actual clip must identify a catalog member');
    const bytes=await readFile(binding.dataRoot+'/'+source.relative);assert.equal(sha(bytes),binding.dataGuards[source.relative]);
    const expected=decodeMotion(JSON.parse(bytes));assert.deepEqual(clip.actualDecodedClip,expected);
    proofs.push({clipRecordId:clip.id,token:clip.token,...source,rawSha256:sha(bytes),
      actualDecodedSha256:sha(JSON.stringify(clip.actualDecodedClip)),duration:expected.duration,curveCount:expected.curves.length});
  }
  // Empty formal motion is an input fact, not a promise about default
  // weights, loop state or a particular provider. Bind only the clips that the
  // untouched player actually archived, including entry/blend source states.
  assert.equal(plan.id,'p30-node4-unchanged-ordinary');
  const target=plan.steps.find(s=>s.target);assert.equal(target.scenario,4);
  assert.equal(target.native.motion,'');assert.deepEqual(target.parsedMotion,{body:'',face:'',extras:[]});
  const targetPoints=report.checkpoints.filter(c=>c.node===target.id);
  const observations=[];
  function observeLayer(checkpoint,layer,path){
    assert.ok(!layer.depthLimit,'Actual layer archive exceeded its declared observation depth');
    const observation={checkpoint:checkpoint.label,tapSequence:checkpoint.row.sequence,layerPath:path,
      layer:layer.name,token:layer.token,weight:layer.weight,effectiveWeight:layer.effectiveWeight,
      state:layer.state,blend:!!layer.blend,loaded:layer.loadedClip.loaded};
    if(layer.loadedClip.loaded){
      const proof=proofs.find(p=>p.clipRecordId===layer.loadedClip.clipRecordId&&p.token===layer.token&&p.model===checkpoint.row.model);
      assert.ok(proof,'An actual loaded checkpoint layer must resolve to its archived canonical clip');
      observation.proof=proof;
    }
    observations.push(observation);
    if(layer.blend)observeLayer(checkpoint,layer.blend.source,path+'/blend-source');
  }
  for(const checkpoint of targetPoints){
    assert.ok(checkpoint.row);assert.equal(checkpoint.row.model,'subaru_tshirt01');
    for(const layer of checkpoint.row.layers)observeLayer(checkpoint,layer,layer.name);
  }
  return {canonicalParserSha256:sha(parserBytes),proofs,actualCurveObjectsMatch:true,
    actualTargetLayerObservations:observations,requiredTokensWereNotInvented:true,
    noExpectedLoopOrWeightAssertions:true,motionAccepted:false,sourcePhaseAccepted:false,
    notVisualOrPacingAcceptance:true};
}
