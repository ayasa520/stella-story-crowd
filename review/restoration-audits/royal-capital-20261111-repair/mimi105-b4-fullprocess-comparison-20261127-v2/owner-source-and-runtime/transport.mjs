// Existing native-only alias pattern, bounded to complete10040043 overlays.
// It substitutes input bytes, never a projected program or renderer state.
import assert from 'node:assert/strict';
import {readFile,appendFile,mkdir,realpath} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {context,sha,here} from './context.mjs';
const mode=process.env.STELLA_RUNTIME_RELEASE_PATH?'runtime':'prepare';
const {binding,bindingBytes}=await context(mode);
const data=await realpath(binding.dataRoot),repository='/ayasa520/stella-story-crowd';
const aliases=new Map(binding.plans.map(plan=>[plan.alias,plan]));
for(const plan of binding.plans){
  assert.equal(plan.aliasIsGitCommit,false);assert.match(plan.alias,/^[a-f0-9]{40}$/);
  assert.notEqual(plan.alias,binding.finalDataHead);
  assert.equal(await realpath(plan.overlay.path),fileURLToPath(new URL('frozen/'+plan.id+'/10040043.json',here)));
}
Object.defineProperty(globalThis,Symbol.for('stella.mimi105.native-transport'),{
  value:Object.freeze({bindingSha256:sha(bindingBytes),aliases:[...aliases.keys()]})});
let providerRows=0,providerBytes=0;
globalThis.fetch=async(input,init)=>{
  const request=new Request(input,init),url=new URL(request.url);
  assert.equal(request.method,'GET');
  if(url.origin==='https://github.com'&&url.pathname===repository+'/commits/main.atom')
    return new Response(`<id>tag:github.com,2008:Grit::Commit/${binding.finalDataHead}</id>`);
  assert.ok(url.origin==='https://raw.githubusercontent.com'&&url.pathname.startsWith(repository+'/'),
    'No outbound fallback is permitted');
  const [revision,...parts]=decodeURIComponent(url.pathname.slice(repository.length+1)).split('/');
  const relative=parts.join('/');
  if(![binding.finalDataHead,'main'].includes(revision)&&!aliases.has(revision))return new Response(null,{status:404});
  if(parts.some(part=>!part||part==='.'||part==='..')||
      !/^(?:manifest\.json|(?:native|review)\/scenes\/\d+\.json|assets\/[-\w./]+)$/.test(relative))
    return new Response(null,{status:404});
  const plan=aliases.get(revision),substituted=!!plan&&relative==='native/scenes/10040043.json';
  const path=substituted?plan.overlay.path:await realpath(resolve(data,relative)).catch(error=>{
    if(['ENOENT','ENOTDIR'].includes(error.code))return null;throw error;});
  if(!path)return new Response(null,{status:404});
  assert.ok(substituted||path.startsWith(data+sep));
  const bytes=await readFile(path),digest=sha(bytes);
  assert.equal(digest,substituted?plan.overlay.sha256:binding.dataGuards[relative],relative);
  const folder=process.env.STELLA_PRIVATE_OUTPUT||fileURLToPath(new URL('frozen/',here));
  await mkdir(folder,{recursive:true});
  const row=JSON.stringify({wallEpochMilliseconds:Date.now(),revision,caseId:plan?.id||null,
    relative,substituted,range:request.headers.get('range'),bytes:bytes.length,sha256:digest})+'\n';
  await appendFile(resolve(folder,'provider-events.jsonl'),row);
  providerRows++;providerBytes+=Buffer.byteLength(row);
  // Retain the complete crossing row before the fatal budget check.
  assert.ok(providerRows<=binding.budgets.providerRowsTotal&&providerBytes<=binding.budgets.providerBytesTotal,
    'Complete provider trace crossed its original budget');
  return new Response(bytes,{headers:{'content-type':relative.endsWith('.json')?'application/json':'application/octet-stream'}});
};
