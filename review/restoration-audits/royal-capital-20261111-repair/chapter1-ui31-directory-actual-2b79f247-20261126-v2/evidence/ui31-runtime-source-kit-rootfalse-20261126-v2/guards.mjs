// Input validation only. This module never starts an API, process or browser.
// A separately approved final inventory may replace the observed C9d design
// snapshot after the known panel-Close publication; no mismatch is waived.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {gzipSync} from 'node:zlib';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

// Keep the exact first-read bytes alive through validation and JSON parsing.
// On failure, archive that same buffer and the parser's original document and
// position without rereading, trimming, repairing NULs, or retrying the source.
export async function parseHeldJson(raw,options={}){
  const {path,output,sha256,bytes}=options;
  const original=Buffer.isBuffer(raw)?raw:Buffer.from(raw,'utf8');
  const proof={path,bytes:original.length,sha256:sha(original)};
  let doc=null;
  try{
    if(Object.hasOwn(options,'sha256'))assert.equal(proof.sha256,sha256,path);
    if(bytes!==undefined)assert.equal(proof.bytes,bytes,path);
    doc=typeof raw==='string'?raw:new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(original);
    return JSON.parse(doc);
  }catch(error){
    const fact={...proof,error:String(error),stack:error.stack,doc,
      position:error.pos??(/position (\d+)/.exec(error.message||'')?.[1]??null)};
    try{
      const stem=resolve(output,'json-first-read-'+process.hrtime.bigint());
      await writeFile(stem+'.raw.gz',gzipSync(original,{level:1}),{flag:'wx'});
      await writeFile(stem+'.failure.json.gz',gzipSync(JSON.stringify(fact)+'\n',{level:1}),{flag:'wx'});
      console.error('JSON_FIRST_READ_FAILED '+JSON.stringify({...proof,error:String(error),stack:error.stack,
        rawArchive:stem+'.raw.gz',failureArchive:stem+'.failure.json.gz'}));
    }catch(archiveError){
      console.error('JSON_FIRST_READ_ARCHIVE_FAILED '+JSON.stringify({...fact,rawBase64:original.toString('base64'),
        archiveError:String(archiveError),archiveStack:archiveError.stack}));
    }
    throw error;
  }
}
export async function readHeldJson(path,options){
  const raw=await readFile(path);
  return parseHeldJson(raw,{...options,path});
}

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
export async function expandInventory(summary,inventory){
  // The caller parsed its one held, hash-verified inventory read above.
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
