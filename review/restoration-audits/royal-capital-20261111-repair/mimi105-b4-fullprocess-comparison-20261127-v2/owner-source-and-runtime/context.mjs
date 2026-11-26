// Local immutable-input adapter for this four-case native diagnostic only.
// All large inventory maps are expanded in RAM. No import launches a process,
// invokes a Worker, creates an overlay, or grants preparation/runtime authority.
import assert from 'node:assert/strict';
import {readFile,realpath} from 'node:fs/promises';
import {getPriority} from 'node:os';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {parseHeldJson,readHeldJson,sha,verifyInputs} from '../ui31-runtime-source-kit-rootfalse-20261126-v2/guards.mjs';
export {parseHeldJson,readHeldJson,sha};
export const here=new URL('./',import.meta.url),root=new URL('../../../',here);
export const cases=['mimi105-B1F0','mimi105-B1F1','mimi105-B2F0','mimi105-B2F1'];
export async function cpuGate(){
  assert.equal(getPriority(),19);
  const raw=await readFile('/proc/self/status','utf8');
  assert.match(raw,/^Cpus_allowed_list:\s*0-1\s*$/m);
}
export async function context(mode){
  await cpuGate();
  const output=process.env.STELLA_PRIVATE_OUTPUT||fileURLToPath(new URL('preparation-failures/',here));
  const bindingBytes=await readFile(new URL('frozen/binding.json',here));
  const binding=await parseHeldJson(bindingBytes,{path:fileURLToPath(new URL('frozen/binding.json',here)),output});
  assert.deepEqual(binding.plans.map(plan=>plan.id),cases);
  assert.equal(binding.nativeOnlyOverlay,true);assert.equal(binding.controlledNativeCandidate,true);
  assert.equal(binding.noProgramMutation,true);assert.equal(binding.browserOwner,'/root/ui_browser_owner');
  const runtime=mode==='runtime';
  assert.ok(runtime||mode==='prepare');
  const releasePath=runtime?process.env.STELLA_RUNTIME_RELEASE_PATH:binding.preparationRelease.path;
  const releaseSHA=runtime?process.env.STELLA_RUNTIME_RELEASE_SHA256:binding.preparationRelease.sha256;
  assert.ok(releasePath&&releaseSHA);
  const release=await readHeldJson(releasePath,{output,sha256:releaseSHA});
  assert.equal(release.rootConfirmed,true);assert.equal(release.controlledNativeCandidateAuthorized,true);
  if(runtime){
    for(const flag of ['executionAuthorized','browserLaunchAuthorized','diagnosticInstrumentationAuthorized',
      'continuousRecorderAuthorized','independentRunnerAccepted'])assert.equal(release[flag],true,flag);
    assert.equal(release.bindingSha256,sha(bindingBytes));
    assert.equal(process.env.STELLA_BROWSER_OWNER,binding.browserOwner);
    assert.equal(process.env.STELLA_PRIVATE_ATTEMPT,release.attempt);
  }else{
    assert.equal(release.apiPreparationAuthorized,true);assert.equal(release.browserLaunchAuthorized,false);
  }
  assert.equal(release.finalDataHead,binding.finalDataHead);assert.equal(release.finalSourceHead,binding.finalSourceHead);
  assert.equal(await realpath(process.execPath),await realpath(binding.tools.node.binaryPath));
  assert.equal(sha(await readFile(process.execPath)),binding.tools.node.sha256);
  assert.ok(process.execArgv.includes('--max-old-space-size='+binding.budgets.nodeHeapMiB),
    'The released Node heap bound must be present in its actual argv');
  const inventory=await readHeldJson(binding.inventory.path,{output,sha256:binding.inventory.sha256,bytes:binding.inventory.bytes});
  assert.equal(inventory.dataHead,binding.finalDataHead);assert.equal(inventory.sourceHead,binding.finalSourceHead);
  const allRefs={...inventory.sharedClosure,...inventory.evidenceGuards,...binding.sourceGuards,
    ...(runtime?release.runtimeBindings:{}),[releasePath]:releaseSHA,
    [binding.inventory.path]:binding.inventory.sha256};
  const expanded={dataRoot:binding.dataRoot||inventory.dataRoot,sourceRoot:inventory.sourceRoot,
    dataInputs:inventory.dataInputs,source:{sourceFiles:inventory.sourceFiles,distFiles:inventory.distFiles},
    globalGuards:inventory.globalGuards,toolFiles:inventory.toolFiles,kitGuards:binding.kitGuards,
    resourceAndSourceGuards:allRefs,
    protectedFirstThreeAbsolute:Object.fromEntries(Object.entries(inventory.protectedFirstThree)
      .map(([path,digest])=>[resolve(inventory.dataRoot,path),digest]))};
  const verify=()=>verifyInputs(expanded);
  await verify();
  // These legacy decoder/observer adapters receive this view in RAM only.
  // It must never be serialized into binding, release or ordinary receipts.
  return {binding:{...binding,dataRoot:inventory.dataRoot,sourceRoot:inventory.sourceRoot,
    dataGuards:inventory.dataInputs,fileGuards:{...allRefs,...binding.kitGuards,
      ...Object.fromEntries(Object.entries(inventory.sourceFiles).map(([path,digest])=>[resolve(inventory.sourceRoot,path),digest]))}},
    bindingBytes,release,releasePath,releaseSHA,inventory,verify,output};
}
export async function runtimeGate(_here,consumer){
  const value=await context('runtime');
  for(const url of [import.meta.url,consumer]){
    const path=fileURLToPath(url);
    assert.equal(sha(await readFile(path)),value.release.runtimeBindings[path],path);
  }
  return {...value,releaseSha256:value.releaseSHA};
}
