// Ordinary read-only upstream adapter: every native/review/asset byte comes
// from the formal final-HEAD package and its released digest. The diagnostic
// host cannot substitute a native row, revision, prepared program or renderer.
import assert from 'node:assert/strict';
import {readFile,appendFile,realpath} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
const here=new URL('./',import.meta.url);
const binding=JSON.parse(await readFile(new URL('frozen/binding.json',here),'utf8'));
const root=await realpath(binding.dataRoot),repository='/ayasa520/stella-story-crowd';
const sha=b=>createHash('sha256').update(b).digest('hex');
let providerRows=0,providerBytes=0;
globalThis.fetch=async(input,init)=>{
  const request=new Request(input,init),url=new URL(request.url);
  assert.equal(request.method,'GET');
  if(url.origin==='https://github.com'&&url.pathname===repository+'/commits/main.atom')
    return new Response(`<id>tag:github.com,2008:Grit::Commit/${binding.finalDataHead}</id>`);
  assert.ok(url.origin==='https://raw.githubusercontent.com'&&url.pathname.startsWith(repository+'/'),'Outbound upstream forbidden');
  const [revision,...parts]=decodeURIComponent(url.pathname.slice(repository.length+1)).split('/');
  const relative=parts.join('/');
  if(![binding.finalDataHead,'main'].includes(revision))return new Response(null,{status:404});
  if(parts.some(p=>!p||p==='.'||p==='..')||!/^(?:manifest\.json|(?:native|review)\/scenes\/\d+\.json|assets\/[-\w./]+)$/.test(relative))
    return new Response(null,{status:404});
  const path=await realpath(resolve(root,relative)).catch(e=>{
    if(['ENOENT','ENOTDIR'].includes(e.code))return null;throw e;});
  if(!path)return new Response(null,{status:404});
  assert.ok(path.startsWith(root+sep));
  const bytes=await readFile(path),digest=sha(bytes);
  assert.equal(digest,binding.dataGuards[relative],'Unbound or changed upstream '+relative);
  const folder=process.env.STELLA_PRIVATE_OUTPUT||fileURLToPath(new URL('frozen/',here));
  const record=JSON.stringify({wallEpochMilliseconds:Date.now(),revision,caseId:binding.plans[0].id,relative,
    range:request.headers.get('range'),bytes:bytes.length,sha256:digest})+'\n';
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
