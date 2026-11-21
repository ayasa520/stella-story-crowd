// Future preparation only. Root must first bind a published ordinary save.
// This calls the existing compiled handler in-process, without a listening
// server or browser, and preserves the complete original response verbatim.
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
const here=new URL('./',import.meta.url),root=new URL('../../../',here);
const sha=value=>createHash('sha256').update(value).digest('hex');
const load=async name=>JSON.parse(await readFile(new URL(name,here),'utf8'));
const save=async(name,value)=>writeFile(new URL(name,here),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const binding=await load('input-binding.json'),plan=await load('capture-plan.json');
const releasePath=process.env.STELLA_PREPARATION_RELEASE_PATH;
assert.ok(releasePath);
const releaseBytes=await readFile(releasePath),release=JSON.parse(releaseBytes);
assert.equal(sha(releaseBytes),process.env.STELLA_PREPARATION_RELEASE_SHA256);
assert.equal(binding.resourceAndSourceGuards[releasePath],sha(releaseBytes));
assert.equal(release.rootConfirmed,true);assert.equal(release.preparationAuthorized,true);
assert.equal(release.browserLaunchAuthorized,false);
assert.equal(release.publishedRomHead,binding.revision);
assert.equal(process.env.STELLA_REVIEW_REVISION,binding.revision);
assert.equal(process.env.STELLA_HOSTING,undefined);
// Before running the real API, recheck the frozen inputs. A successful freeze
// is not permission to execute a later source/resource revision silently.
for(const [base,files]of [[binding.dataRoot,binding.dataInputs],[binding.sourceRoot,binding.source.sourceFiles],
    [binding.sourceRoot+'/dist',binding.source.distFiles]])
  for(const [path,digest]of Object.entries(files))assert.equal(sha(await readFile(base+'/'+path)),digest,path);
for(const [path,digest]of Object.entries(binding.resourceAndSourceGuards))
  assert.equal(sha(await readFile(path.startsWith('/')?path:new URL(path,root))),digest,path);
const workersModule=new URL('../../stella-local-deployment-3394828/workers-local.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'
  ?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const context={waitUntil(promise){promise.catch(error=>console.error(error));}};
const request={id:plan.start,baseSha:binding.revision,choices:{}};
await save('normal-prepare-request.json',request);
const reply=await worker.fetch(new Request('http://127.0.0.1:5198/api/player/prepare',{
  method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}),env,context);
const raw=await reply.text();
await writeFile(new URL('normal-prepare-body.json.gz',here),gzipSync(raw),{flag:'wx'});
const receipt={status:reply.status,rawResponseSha256:sha(raw),rawResponseBytes:Buffer.byteLength(raw),
  request,serverStarted:false,browserStarted:false,localEnvFalse:true,
  dataHead:binding.dataHead,sourceHead:binding.source.head,programMutated:false};
if(reply.status!==200){
  // Preserve a real ambiguity result including upstreamIncoming. This is a
  // second read-only ordinary API call, never an automatic route selection.
  if(reply.status===422){
    const diagnostic=await worker.fetch(new Request('http://127.0.0.1:5198/api/resolve',{
      method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)}),env,context);
    const text=await diagnostic.text();
    await writeFile(new URL('normal-resolve-body.json.gz',here),gzipSync(text),{flag:'wx'});
    receipt.resolve={status:diagnostic.status,rawResponseSha256:sha(text),rawResponseBytes:Buffer.byteLength(text)};
  }
  await save('normal-prepare-receipt.json',receipt);
  throw Error('Ordinary prepare failed '+reply.status+'; preserved response; no seed/override/retry');
}
const program=JSON.parse(raw);
assert.equal(program.start,plan.start);assert.equal(program.headSha,binding.revision);
assert.equal(program.nodes.length,plan.allLibraryNodes);
assert.equal(program.nodes.filter(n=>n.scene_id==='scene:10020037').length,19);
let inherited=program.before.bg_picture;
assert.equal(typeof inherited,'string','The API must resolve the actual inherited background');
const nodes=[],edges=[];
for(const step of plan.steps){
  const node=program.nodes.find(n=>n.id===step.id);assert.ok(node);
  assert.equal(node.model,step.expectedModel);assert.equal(node.character_image,'');
  if(node.script_background.resource)inherited=node.script_background.resource;
  const edge=program.edges.find(e=>e.source===step.id&&e.id.endsWith(':'+step.branchId));
  assert.ok(edge?.available);assert.deepEqual(edge.native_transition,step.expectedTransition);
  nodes.push({node,expectedEffectiveBackground:inherited});edges.push(edge);
}
const unknown=program.edges.find(e=>e.source===plan.steps[2].id&&e.id.endsWith(':133'));
assert.ok(unknown);assert.equal(unknown.available,false);assert.equal(unknown.state,'missing');assert.equal(unknown.target,'');
assert.equal(edges[2].label_translation,'零食？');
Object.assign(receipt,{programSha256:sha(JSON.stringify(program)),start:program.start,
  headSha:program.headSha,wholeLibraryNodes:program.nodes.length,before:program.before});
await save('normal-prepare-route-check.json',{nodes,edges,unknown,before:program.before});
await save('normal-prepare-receipt.json',receipt);
const runtimeNames=['run.py','play.mjs','worktree-upstream.mjs','freeze-inputs.py','prepare-normal.mjs',
  'input-binding.json','capture-plan.json','normal-prepare-request.json','normal-prepare-body.json.gz',
  'normal-prepare-receipt.json','normal-prepare-route-check.json','README.md'];
const shared=['artifacts/stella-local-deployment-3394828/serve-local.mjs',
  'artifacts/stella-local-deployment-3394828/workers-local.mjs','artifacts/stella-local-deployment-3394828/d1-local.mjs',
  'artifacts/stella-p30-firefox-20261120/bidi.mjs','artifacts/stella-p30-firefox-20261120/render-probe.mjs'];
const runtimeBindings={};
for(const url of [...runtimeNames.map(n=>new URL(n,here)),...shared.map(n=>new URL(n,root))])
  runtimeBindings[fileURLToPath(url).slice(fileURLToPath(root).length)]=sha(await readFile(url));
await save('root-release.prepared.draft.json',{schema:'stella.rom13.saved-runtime-release.v1',
  rootConfirmed:false,executionAuthorized:false,browserLaunchAuthorized:false,browserOwner:binding.browserOwner,
  publishedRomHead:binding.dataHead,sourceHead:binding.source.head,inputBindingSha256:sha(await readFile(new URL('input-binding.json',here))),
  planSha256:sha(await readFile(new URL('capture-plan.json',here))),normalProgramSha256:receipt.programSha256,
  runtimeBindings,attempt:'attempt-1',scope:plan.acceptanceScope});
console.log(JSON.stringify({status:200,start:program.start,programSha256:receipt.programSha256,browserAuthorized:false}));
