// Read-only upstream adapter. Only the complete native10450054 file differs
// for a named private alias. Every other returned byte is a frozen baseline
// member. No prepared program, business parser, clock or renderer is replaced.
import assert from 'node:assert/strict';
import {readFile,appendFile,realpath} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
const here=new URL('./',import.meta.url);
const bindingBytes=await readFile(new URL('frozen/binding.json',here)),binding=JSON.parse(bindingBytes);
const root=await realpath(binding.dataRoot),repository='/ayasa520/stella-story-crowd';
const aliases=new Map(binding.plans.map(p=>[p.alias,p]));
const sha=b=>createHash('sha256').update(b).digest('hex');
assert.equal(binding.controlledNativeCandidate,true);assert.equal(binding.nativeOnlyOverlay,true);
assert.equal(binding.noProgramMutation,true);
assert.deepEqual(binding.plans.map(p=>p.id),['p30-node4-face-bikkuri-only']);
const plan=binding.plans[0];assert.equal(plan.aliasIsGitCommit,false);
assert.match(plan.alias,/^[a-f0-9]{40}$/);assert.notEqual(plan.alias,binding.finalDataHead);
assert.equal(await realpath(plan.overlay.path),fileURLToPath(new URL('frozen/p30-node4-face-bikkuri-only/10450054.json',here)));
// This marker proves this exact staged-byte transport was preloaded before a
// Worker request. A missing --import must fail before even the formal baseline;
// a successful remote ordinary response cannot masquerade as provider evidence.
Object.defineProperty(globalThis,Symbol.for('stella.p30.face-bikkuri.native-transport'),{
  value:Object.freeze({kind:'native-only-controlled-face',bindingSha256:sha(bindingBytes),caseId:plan.id,alias:plan.alias})});
let providerRows=0,providerBytes=0;
globalThis.fetch=async(input,init)=>{
  const request=new Request(input,init),url=new URL(request.url);
  assert.equal(request.method,'GET');
  if(url.origin==='https://github.com'&&url.pathname===repository+'/commits/main.atom')
    return new Response(`<id>tag:github.com,2008:Grit::Commit/${binding.finalDataHead}</id>`);
  assert.ok(url.origin==='https://raw.githubusercontent.com'&&url.pathname.startsWith(repository+'/'),'Outbound upstream forbidden');
  const [revision,...parts]=decodeURIComponent(url.pathname.slice(repository.length+1)).split('/');
  const relative=parts.join('/');
  if(![binding.finalDataHead,'main'].includes(revision)&&!aliases.has(revision))return new Response(null,{status:404});
  if(parts.some(p=>!p||p==='.'||p==='..')||!/^(?:manifest\.json|(?:native|review)\/scenes\/\d+\.json|assets\/[-\w./]+)$/.test(relative))
    return new Response(null,{status:404});
  const overlay=aliases.get(revision),substituted=!!overlay&&relative==='native/scenes/10450054.json';
  const path=substituted?overlay.overlay.path:await realpath(resolve(root,relative)).catch(e=>{
    if(['ENOENT','ENOTDIR'].includes(e.code))return null;throw e;});
  if(!path)return new Response(null,{status:404});
  assert.ok(substituted||path.startsWith(root+sep));
  const bytes=await readFile(path),digest=sha(bytes);
  assert.equal(digest,substituted?overlay.overlay.sha256:binding.dataGuards[relative],'Unbound or changed upstream '+relative);
  const folder=process.env.STELLA_PRIVATE_OUTPUT||fileURLToPath(new URL('frozen/',here));
  const record=JSON.stringify({wallEpochMilliseconds:Date.now(),revision,caseId:overlay?.id||null,relative,
    substituted,range:request.headers.get('range'),bytes:bytes.length,sha256:digest})+'\n';
  providerRows++;providerBytes+=Buffer.byteLength(record);
  assert.ok(providerRows<=binding.budgets.providerRowsTotal&&providerBytes<=binding.budgets.providerBytesTotal,
    'Provider trace budget exceeded; do not claim complete delivery');
  await appendFile(resolve(folder,'provider-events.jsonl'),record);
  const headers={'Accept-Ranges':'bytes','Content-Length':String(bytes.length)};
  const range=request.headers.get('range')?.match(/^bytes=(\d*)-(\d*)$/);
  if(range&&(range[1]||range[2])){
    const start=range[1]?Number(range[1]):Math.max(0,bytes.length-Number(range[2]));
    const end=range[1]&&range[2]?Math.min(Number(range[2]),bytes.length-1):bytes.length-1;
    if(start>end)return new Response(null,{status:416});
    return new Response(bytes.subarray(start,end+1),{status:206,headers:{...headers,
      'Content-Length':String(end-start+1),'Content-Range':`bytes ${start}-${end}/${bytes.length}`}});
  }
  return new Response(bytes,{headers});
};
