// One fixed-origin read-only transport, not a Worker/renderer implementation.
// The response body delivered by Node fetch is forwarded unchanged. In
// particular, neither JSON nor asset paths/quality/revision are reconstructed.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,writeFile,appendFile,mkdir,realpath,stat} from 'node:fs/promises';
import {resolve,sep,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {gzipSync} from 'node:zlib';
import {sha,verifyInputs,expandInventory} from './guards.mjs';
export const productionOrigin='https://stella-preview.jaoushingan.com';
const here=new URL('./',import.meta.url);
const binding=await expandInventory(JSON.parse(await readFile(new URL('input-binding.json',here),'utf8')));
const plan=JSON.parse(await readFile(new URL('capture-plan.json',here),'utf8'));
assert.equal(binding.productionOrigin,productionOrigin);assert.equal(plan.productionOrigin,productionOrigin);
const localOrigin='http://127.0.0.1:5198';
const evidenceRoot=process.env.STELLA_REVIEW_OUTPUT||fileURLToPath(new URL('prepared/proxy/',here));
let sequence=0,traceBytes=0;
const hopByHop=['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade'];
function cleanHeaders(original){
  const copy=new Headers(original);
  for(const token of (copy.get('connection')||'').split(',').map(s=>s.trim()).filter(Boolean))copy.delete(token);
  for(const name of hopByHop)copy.delete(name);
  return copy;
}
async function record(row){
  await mkdir(evidenceRoot,{recursive:true});
  const line=JSON.stringify(row)+'\n';await appendFile(resolve(evidenceRoot,'proxy-events.jsonl'),line);
  traceBytes+=Buffer.byteLength(line);
  if(traceBytes>binding.budgets.providerTraceBytes){
    // Keep the complete crossing row and original errors, then fail coverage.
    // The output estimate never authorizes silently dropping a response fact.
    console.error('PRODUCTION_PROXY_TRACE_BUDGET_EXCEEDED',{traceBytes});
    throw Error('Production proxy trace budget exceeded; crossing record retained');
  }
}
export async function forwardProduction(request){
  const local=new URL(request.url);
  assert.equal(local.origin,localOrigin);assert.equal(local.username,'');assert.equal(local.password,'');
  assert.ok(['GET','HEAD','POST'].includes(request.method),'Only read-only production requests are allowed');
  const id=String(++sequence).padStart(6,'0'),began=Date.now();
  await mkdir(evidenceRoot,{recursive:true});
  let requestBody;
  if(request.method==='POST'){
    assert.ok(['/api/player/prepare','/api/resolve'].includes(local.pathname),'Mutation endpoint forbidden');
    requestBody=Buffer.from(await request.arrayBuffer());
    await writeFile(resolve(evidenceRoot,id+'.request.body.bin'),requestBody,{flag:'wx'});
    assert.ok(requestBody.length<=4096);
    assert.deepEqual(JSON.parse(requestBody.toString('utf8')),{id:plan.cases[0].start,baseSha:binding.revision,choices:{}});
  }
  const upstreamURL=new URL(local.pathname+local.search,productionOrigin);
  assert.equal(upstreamURL.origin,productionOrigin);
  const headers=cleanHeaders(request.headers);
  headers.delete('host');headers.delete('content-length');
  for(const name of [...headers.keys()])if(name.startsWith('oai-authenticated-user-'))headers.delete(name);
  // Ask for identity explicitly. Fetch can still expose a decoded body while
  // retaining upstream Content-Encoding/Length. Record both original headers
  // and observed bytes, strip those representation headers before forwarding,
  // and set a new length only for a body actually transferred to the browser.
  headers.set('accept-encoding','identity');
  const base={id,requestEpochMilliseconds:began,method:request.method,url:local.href,upstreamURL:upstreamURL.href,
    forwardedRequestHeaders:Object.fromEntries(headers),requestBodyBytes:requestBody?.length||0,
    requestBodySha256:requestBody?sha(requestBody):null,fixedProductionOrigin:true,redirectMode:'manual'};
  await record({...base,phase:'request-started'});
  try{
    const response=await fetch(upstreamURL,{method:request.method,headers,body:requestBody,
      redirect:'manual',signal:AbortSignal.timeout(45000)});
    const body=Buffer.from(await response.arrayBuffer()),originalHeaders=Object.fromEntries(response.headers);
    const outgoingHeaders=cleanHeaders(response.headers);
    outgoingHeaders.delete('content-encoding');outgoingHeaders.delete('content-length');
    if(request.method!=='HEAD'&&![204,205,304].includes(response.status))
      outgoingHeaders.set('content-length',String(body.length));
    // These are application-delivered bytes, not a claim about compressed
    // wire frames. A digest mismatch fails the caller before any player load.
    const row={...base,phase:'response-complete',responseEpochMilliseconds:Date.now(),status:response.status,statusText:response.statusText,
      upstreamHeaders:originalHeaders,upstreamSetCookie:response.headers.getSetCookie(),
      forwardedResponseHeaders:Object.fromEntries(outgoingHeaders),
      // HEAD and body-forbidden statuses transfer no response body; keep
      // the original status/headers and observed zero-byte body facts intact.
      bodyBytes:body.length,bodySha256:sha(body),bodyTransferred:request.method!=='HEAD'&&![204,205,304].includes(response.status),
      observedBody:'Node fetch delivered bytes; no application decode/rewrite',
      upstreamContentEncoding:response.headers.get('content-encoding')||null};
    const targetPath='/asset/'+plan.cue.member.split('/').map(encodeURIComponent).join('/');
    if(request.method==='POST'||response.status>=400||local.pathname===targetPath){
      const file=id+'.response.body.gz',compressed=gzipSync(body);
      await writeFile(resolve(evidenceRoot,file),compressed,{flag:'wx'});
      row.bodyArchive={file,bytes:compressed.length,sha256:sha(compressed)};
    }
    await record(row);
    // 304 is a conditional representation response, not a redirect.
    if([301,302,303,307,308].includes(response.status))
      console.error('PRODUCTION_PROXY_REDIRECT_RETAINED',row);
    return new Response(request.method==='HEAD'||[204,205,304].includes(response.status)?null:body,{
      status:response.status,statusText:response.statusText,headers:outgoingHeaders});
  }catch(error){
    const failure={...base,phase:'transport-error',error:String(error),stack:error.stack,responseEpochMilliseconds:Date.now()};
    await writeFile(resolve(evidenceRoot,id+'.transport-error.json'),JSON.stringify(failure,null,2)+'\n',{flag:'wx'})
      .catch(recordError=>console.error('PROXY_ERROR_RECORD_FAILED',{original:failure,recordError:String(recordError),stack:recordError.stack}));
    await record(failure).catch(recordError=>console.error('PROXY_ERROR_TRACE_FAILED',{original:failure,recordError:String(recordError),stack:recordError.stack}));
    throw error;
  }
}
async function localStatic(request){
  if(!['GET','HEAD'].includes(request.method))return null;
  const pathname=new URL(request.url).pathname;
  // Only frozen canonical executable/static code is local. Ordinary JSON,
  // models, fonts, images and audio go to the same real production path.
  if(!/\.(?:html|js|css)$/.test(pathname))return null;
  const client=await realpath(resolve(binding.sourceRoot,'dist/client'));
  const name=resolve(client,'.'+decodeURIComponent(pathname));
  assert.ok(name.startsWith(client+sep));
  const entry=await stat(name).catch(error=>{if(['ENOENT','ENOTDIR'].includes(error.code))return null;throw error;});
  if(!entry?.isFile())return new Response('Frozen canonical static file missing',{status:404});
  const bytes=await readFile(name),relative='client/'+name.slice(client.length+1);
  assert.equal(sha(bytes),binding.source.distFiles[relative],'Unbound canonical static code '+relative);
  return new Response(request.method==='HEAD'?null:bytes,{headers:{
    'content-type':{'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.html':'text/html; charset=utf-8'}[extname(name)],
    'content-length':String(bytes.length)}});
}
async function serve(){
  const releasePath=process.env.STELLA_RUNTIME_RELEASE_PATH;
  assert.ok(releasePath);
  const bytes=await readFile(releasePath),release=JSON.parse(bytes);
  assert.equal(sha(bytes),process.env.STELLA_RUNTIME_RELEASE_SHA256);
  for(const flag of ['rootConfirmed','executionAuthorized','browserLaunchAuthorized','diagnosticInstrumentationAuthorized',
      'productionProxyAuthorized'])assert.equal(release[flag],true,flag);
  assert.equal(release.inputBindingSha256,sha(await readFile(new URL('input-binding.json',here))));
  await verifyInputs(binding);
  createServer(async(incoming,outgoing)=>{
    try{
      if(incoming.headers.host!=='127.0.0.1:5198'){outgoing.writeHead(421).end();return;}
      if(!['GET','HEAD','POST'].includes(incoming.method)){outgoing.writeHead(405).end();return;}
      const url=new URL(incoming.url,localOrigin);
      if(url.origin!==localOrigin){outgoing.writeHead(400).end();return;}
      if(incoming.method==='POST'&&!['/api/player/prepare','/api/resolve'].includes(url.pathname)){
        outgoing.writeHead(405).end();return;
      }
      const request=new Request(url,{method:incoming.method,headers:incoming.headers,
        ...(incoming.method==='POST'?{body:Readable.toWeb(incoming),duplex:'half'}:{})});
      const response=await localStatic(request)||await forwardProduction(request);
      if(outgoing.destroyed){await response.body?.cancel();return;}
      const forwarded=Object.fromEntries(response.headers),cookies=response.headers.getSetCookie();
      if(cookies.length)forwarded['set-cookie']=cookies;
      outgoing.writeHead(response.status,forwarded);
      if(response.body&&incoming.method!=='HEAD')await pipeline(Readable.fromWeb(response.body),outgoing);
      else outgoing.end();
    }catch(error){
      console.error('PRODUCTION_PROXY_REQUEST_FAILED',error);
      if(outgoing.destroyed)return;
      if(!outgoing.headersSent)outgoing.writeHead(502,{'content-type':'text/plain; charset=utf-8'});
      outgoing.end(String(error));
    }
  }).listen(5198,'127.0.0.1',()=>console.log('Read-only production proxy http://127.0.0.1:5198'));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))await serve();
