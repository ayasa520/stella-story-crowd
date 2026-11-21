// Run the compiled Worker's real saved prepare handler in-process. There is
// no listening server, browser, repository method override or program edit.
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
const here=new URL('./',import.meta.url);
const binding=JSON.parse(await readFile(new URL('input-binding.json',here),'utf8'));
assert.equal(process.env.STELLA_REVIEW_REVISION,binding.revision);
assert.equal(process.env.STELLA_HOSTING,undefined);
const workersModule=new URL('../../stella-local-deployment-3394828/workers-local.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'
  ?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);
assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const response=await worker.fetch(new Request('http://127.0.0.1:5198/api/player/prepare',{
  method:'POST',headers:{'content-type':'application/json'},
  body:JSON.stringify({id:'node:10430012:1043001200023',baseSha:binding.revision,choices:{}})}),
  env,{waitUntil(promise){promise.catch(error=>console.error(error));}});
const raw=await response.text();
await writeFile(new URL('normal-prepare-body.json.gz',here),gzipSync(raw));
assert.equal(response.status,200,raw.slice(0,1000));
const program=JSON.parse(raw);
assert.equal(program.start,'node:10430012:1043001200023');
assert.equal(program.nodes.length,5619);
assert.equal(program.nodes.filter(n=>n.scene_id==='scene:10430012').length,38);
await writeFile(new URL('normal-prepare-receipt.json',here),JSON.stringify({
  status:response.status,headSha:program.headSha,contentRevision:program.contentRevision,
  start:program.start,programSha256:createHash('sha256').update(JSON.stringify(program)).digest('hex'),
  rootMode:'normal-saved-worker-env-false',serverStarted:false,browserStarted:false,
  allLibraryNodeCount:program.nodes.length,productionScopedEquivalenceAccepted:false,
  sourceHead:binding.source.head,sourceTreeSha256:binding.source.sourceTreeSha256,
  nativeSha256:binding.dataInputs['native/scenes/10430012.json'],
},null,2)+'\n');
console.log(JSON.stringify({status:response.status,start:program.start,nodeCount:program.nodes.length,
  programSha256:createHash('sha256').update(JSON.stringify(program)).digest('hex')}));
