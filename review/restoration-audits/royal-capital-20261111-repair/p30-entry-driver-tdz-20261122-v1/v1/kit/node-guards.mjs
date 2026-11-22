// Runtime consumers must validate the actual separate root release, rather
// than turning a prepared binding or a hash-shaped observer argument into
// execution authority. This module performs local reads only.
import assert from 'node:assert/strict';
import {readFile,realpath} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {getPriority} from 'node:os';
import {fileURLToPath} from 'node:url';
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function cpuGate(){
  assert.equal(getPriority(),19);
  const status=await readFile('/proc/self/status','utf8'),mask=status.match(/^Cpus_allowed_list:\s*(.+)$/m)?.[1];
  assert.ok(mask,'Actual Linux CPU mask is required');
  const cpus=mask.trim().split(',').flatMap(part=>{
    const [a,b=a]=part.split('-').map(Number);return Array.from({length:b-a+1},(_,i)=>a+i);
  });
  assert.deepEqual(cpus,[0,1]);
}
export async function runtimeGate(here,consumer){
  await cpuGate();
  const path=process.env.STELLA_RUNTIME_RELEASE_PATH,expected=process.env.STELLA_RUNTIME_RELEASE_SHA256;
  assert.ok(path&&expected,'Only the released supervisor may supply runtime authority');
  const bytes=await readFile(path),release=JSON.parse(bytes);assert.equal(sha(bytes),expected);
  for(const flag of ['rootConfirmed','executionAuthorized','browserLaunchAuthorized','diagnosticInstrumentationAuthorized',
    'continuousRecorderAuthorized'])assert.equal(release[flag],true,flag);
  const bindingBytes=await readFile(new URL('frozen/binding.json',here)),binding=JSON.parse(bindingBytes);
  assert.equal(await realpath(process.execPath),await realpath(binding.tools.node.binaryPath));
  assert.equal(sha(await readFile(process.execPath)),binding.tools.node.sha256);
  assert.equal(sha(bindingBytes),release.bindingSha256);
  assert.deepEqual(binding.plans.map(p=>p.id),['p30-node4-unchanged-ordinary']);
  assert.equal(binding.noNativeOverlay,true);assert.equal(binding.noProgramMutation,true);
  for(const plan of binding.plans){
    assert.deepEqual(plan.steps.map(s=>s.scenario),[3,4,5]);
    assert.equal(plan.stop.scenario,5);assert.equal(plan.stop.phase,'ready');
    assert.equal(plan.stop.forbiddenNext,6);assert.ok(plan.stop.forbiddenEdge.endsWith(':51'));
    assert.equal(plan.ordinaryBaseline,true);
    const target=plan.steps.find(s=>s.target);assert.equal(target.scenario,4);
    assert.equal(target.native.character,'live2d/AC_subaru_tshirt01');
    assert.equal(target.native.motion,'');
    assert.deepEqual(target.parsedMotion,{body:'',face:'',extras:[]});
  }
  assert.equal(sha(await readFile(new URL('prepared/index.json',here))),release.normalPreparationIndexSha256);
  assert.equal(process.env.STELLA_BROWSER_OWNER,release.browserOwner);assert.equal(release.browserOwner,binding.browserOwner);
  assert.equal(process.env.STELLA_PRIVATE_ATTEMPT,release.attempt);
  assert.equal(release.finalDataHead,binding.finalDataHead);assert.equal(release.finalSourceHead,binding.finalSourceHead);
  for(const url of [import.meta.url,consumer])assert.equal(sha(await readFile(new URL(url))),release.runtimeBindings[fileURLToPath(url)]);
  for(const [file,digest]of Object.entries(release.runtimeBindings)){
    const resolved=file.startsWith('/')?file:new URL(file,new URL('../../../',here));
    assert.equal(sha(await readFile(resolved)),digest,file);
  }
  return {release,binding,bindingBytes,releaseSha256:expected};
}
