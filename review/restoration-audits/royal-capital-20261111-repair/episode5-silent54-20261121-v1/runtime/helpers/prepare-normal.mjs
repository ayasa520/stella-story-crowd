// Run the existing compiled saved handler in-process, without a listener.
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {gzipSync,gunzipSync} from 'node:zlib';
const here=new URL('./',import.meta.url);
const binding=JSON.parse(await readFile(new URL('input-binding.json',here),'utf8'));
const plan=JSON.parse(await readFile(new URL('capture-plan.json',here),'utf8'));
assert.equal(process.env.STELLA_REVIEW_REVISION,binding.revision);
const workersModule=new URL('../../stella-local-deployment-3394828/workers-local.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'
  ?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const context={waitUntil(p){p.catch(error=>console.error(error));}};
const reply=await worker.fetch(new Request('http://127.0.0.1:5198/api/player/prepare',{
 method:'POST',headers:{'content-type':'application/json'},
 body:JSON.stringify({id:plan.start,baseSha:binding.revision,choices:{}})}),env,context);
const raw=await reply.text();await writeFile(new URL('normal-prepare-body.json.gz',here),gzipSync(raw));
assert.equal(reply.status,200,raw.slice(0,1200));const program=JSON.parse(raw);
assert.equal(program.start,plan.start);assert.equal(program.headSha,binding.revision);
assert.equal(program.nodes.length,5620);
const scene=program.nodes.filter(n=>n.scene_id==='scene:10090015');assert.equal(scene.length,53);
for(const step of plan.steps){
 const node=scene.find(n=>n.id===step.id);assert.equal(node.scenario_id,step.scenario);assert.equal(node.model,step.expectedModel);
 const edge=program.edges.find(e=>e.source===step.id&&e.native_transition?.uniq_id===step.native.branch_list[0].transition_list[0].uniq_id);
 assert.ok(edge?.available);assert.deepEqual(edge.native_transition,step.native.branch_list[0].transition_list[0]);
}
const silent=scene.find(n=>n.scenario_id===54);
assert.equal(silent.text,plan.languages[1].expectedText);assert.equal(silent.translation,plan.languages[0].expectedText);
// A changed input guard set has a new real content alias. Compare the saved
// scene/edges/before with the retained prior response, without rewriting either
// program's head or treating this one new preparation as a parser health loop.
const previousHere=new URL('../episode5-silent54-saved-runtime-v1/',here);
const previous=JSON.parse(gunzipSync(await readFile(new URL('normal-prepare-body.json.gz',previousHere))));
const previousReceipt=JSON.parse(await readFile(new URL('normal-prepare-receipt.json',previousHere),'utf8'));
assert.deepEqual(scene,previous.nodes.filter(n=>n.scene_id==='scene:10090015'));
assert.deepEqual(program.edges.filter(e=>e.source.startsWith('node:10090015:')),previous.edges.filter(e=>e.source.startsWith('node:10090015:')));
assert.deepEqual(program.before,previous.before);
const music=await worker.fetch(new Request('http://127.0.0.1:5198/api/music/'+plan.expectedBgm),env,context);
const musicRaw=await music.text();assert.equal(music.status,200,musicRaw.slice(0,1000));
await writeFile(new URL('win01-metadata.json',here),musicRaw);
const sha=x=>createHash('sha256').update(x).digest('hex');
await writeFile(new URL('normal-prepare-receipt.json',here),JSON.stringify({status:200,start:program.start,
 headSha:program.headSha,programSha256:sha(JSON.stringify(program)),rawResponseSha256:sha(raw),
 rawResponseBytes:Buffer.byteLength(raw),wholeLibraryNodes:5620,sceneRows:53,before:program.before,
 previousProfileProgramSha256:previousReceipt.programSha256,previousProfileHead:previous.headSha,
 target53NodesEdgesAndBeforeUnchangedFromV1:true,newProfileGuards615:true,
 sourceHead:binding.source.head,serverStarted:false,browserStarted:false,localEnvFalse:true},null,2)+'\n');
await writeFile(new URL('normal-prepare-route-check.json',here),JSON.stringify({nodes:plan.steps.map(s=>scene.find(n=>n.id===s.id)),
 edges:program.edges.filter(e=>plan.steps.some(s=>s.id===e.source)),before:program.before},null,2)+'\n');
console.log(JSON.stringify({status:200,nodes:5620,sceneRows:53,programSha256:sha(JSON.stringify(program))}));
