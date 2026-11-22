// Input validation only. This module never starts an API, process or browser.
// A separately approved final inventory may replace the observed C9d design
// snapshot after the known panel-Close publication; no mismatch is waived.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function verifyInputs(binding){
  for(const [base,files] of [[binding.dataRoot,binding.dataInputs],
      [binding.sourceRoot,binding.source.sourceFiles],[binding.sourceRoot+'/dist',binding.source.distFiles]]){
    for(const [name,digest] of Object.entries(files))
      assert.equal(sha(await readFile(resolve(base,name))),digest,name);
  }
  for(const files of [binding.globalGuards,binding.protectedFirstThreeAbsolute,
      binding.resourceAndSourceGuards,binding.toolFiles,binding.kitGuards]){
    for(const [name,digest] of Object.entries(files))
      assert.equal(sha(await readFile(name)),digest,name);
  }
}

// Expand the one immutable root inventory in RAM only. Callers must not
// serialize this view: binding/release/checkpoint logs retain its path+SHA,
// membership/counts and full fresh verification result instead of large maps.
export async function expandInventory(summary){
  const bytes=await readFile(summary.inventory.path);
  assert.equal(sha(bytes),summary.inventory.sha256,'Immutable root inventory changed');
  const inventory=JSON.parse(bytes);
  assert.equal(inventory.dataRoot,summary.dataRoot);assert.equal(inventory.sourceRoot,summary.sourceRoot);
  for(const [name,count]of Object.entries(summary.inventoryCounts))
    assert.equal(Object.keys(inventory[name]).length,count,'Inventory member count '+name);
  return {...summary,dataInputs:inventory.dataInputs,globalGuards:inventory.globalGuards,
    protectedFirstThree:inventory.protectedFirstThree,
    protectedFirstThreeAbsolute:Object.fromEntries(Object.entries(inventory.protectedFirstThree)
      .map(([name,digest])=>[resolve(summary.dataRoot,name),digest])),
    toolFiles:inventory.toolFiles,
    resourceAndSourceGuards:{...inventory.sharedClosure,...inventory.evidenceGuards,...summary.additionalGuards},
    source:{...summary.source,sourceFiles:inventory.sourceFiles,distFiles:inventory.distFiles}};
}
