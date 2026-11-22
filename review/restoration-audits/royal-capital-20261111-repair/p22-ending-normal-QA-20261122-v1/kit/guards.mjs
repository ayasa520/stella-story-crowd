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
