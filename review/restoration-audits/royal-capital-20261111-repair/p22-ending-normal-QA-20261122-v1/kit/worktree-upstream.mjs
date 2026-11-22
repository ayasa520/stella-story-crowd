// Transport only: the unchanged compiled Worker consumes the exact saved files.
// A missing or unbound member fails closed instead of falling back to network,
// another revision or an invented resource. Nothing edits a prepared program.
import {readFile,realpath,appendFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const here=new URL('./',import.meta.url);
const binding=JSON.parse(await readFile(new URL('input-binding.json',here),'utf8'));
const root=await realpath(binding.dataRoot),revision=process.env.STELLA_REVIEW_REVISION;
assert.equal(revision,binding.revision);
assert.match(revision,/^[0-9a-f]{40}$/);
const repository='/ayasa520/stella-story-crowd';
globalThis.fetch=async(input,init)=>{
  const request=new Request(input,init),url=new URL(request.url);
  assert.equal(request.method,'GET','Saved upstream is read-only');
  if(url.origin==='https://github.com'&&url.pathname===repository+'/commits/main.atom')
    return new Response(`<id>tag:github.com,2008:Grit::Commit/${revision}</id>`);
  assert.ok(url.origin==='https://raw.githubusercontent.com'&&url.pathname.startsWith(repository+'/'),
    'Outbound upstream is forbidden: '+url.origin+url.pathname);
  const [ref,...parts]=decodeURIComponent(url.pathname.slice(repository.length+1)).split('/');
  const relative=parts.join('/');
  if(![revision,'main'].includes(ref)||parts.some(p=>!p||p==='.'||p==='..')||
      !/^(?:manifest\.json|(?:native|review)\/scenes\/\d+\.json|assets\/[-\w./]+)$/.test(relative))
    return new Response(null,{status:404});
  const path=await realpath(resolve(root,relative)).catch(error=>{
    if(['ENOENT','ENOTDIR'].includes(error.code))return null;throw error;});
  if(!path?.startsWith(root+sep))return new Response(null,{status:404});
  const bytes=await readFile(path),sha256=createHash('sha256').update(bytes).digest('hex');
  assert.equal(sha256,binding.dataInputs[relative],'Unexpected or changed saved upstream member '+relative);
  await appendFile(resolve(process.env.STELLA_REVIEW_OUTPUT||fileURLToPath(here),'provider-events.jsonl'),
    JSON.stringify({epochMilliseconds:Date.now(),url:request.url,relative,revision:ref,
      range:request.headers.get('range'),completeFileBytes:bytes.length,sha256})+'\n');
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
