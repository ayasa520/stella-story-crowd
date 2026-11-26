// Future released private host for the unchanged compiled Worker and player.
// Only ordinary prepare/resolve POSTs for the four already checked aliases are
// admitted. Native/check happens earlier against the formal baseline in Node.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {registerHooks} from 'node:module';
import {readFile,realpath} from 'node:fs/promises';
import {resolve,relative,sep,extname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {context,sha,here,parseHeldJson} from './context.mjs';
const {binding,bindingBytes,inventory,output}=await context('runtime');
assert.deepEqual(globalThis[Symbol.for('stella.mimi105.native-transport')],{
  bindingSha256:sha(bindingBytes),aliases:binding.plans.map(plan=>plan.alias)});
const workers=new URL('workers-private.mjs',here).href;
registerHooks({resolve(name,scope,next){return name==='cloudflare:workers'
  ?{url:workers,shortCircuit:true}:next(name,scope);}});
const {env}=await import(workers);
assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const client=await realpath(resolve(binding.sourceRoot,'dist/client')),origin='http://127.0.0.1:5198';
const types={'.js':'text/javascript','.json':'application/json','.html':'text/html; charset=utf-8',
  '.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
async function assets(request){
  if(!['GET','HEAD'].includes(request.method))return null;
  const url=new URL(request.url),ref={
    '/__private/owner-events.mjs':binding.shared.ownerEvents,
    '/__private/tap-v2.mjs':binding.shared.tap
  }[url.pathname];
  if(ref){
    const bytes=await readFile(ref.path);assert.equal(sha(bytes),ref.sha256);
    return new Response(request.method==='HEAD'?null:bytes,{headers:{'Content-Type':'text/javascript','Cache-Control':'no-store'}});
  }
  const candidate=resolve(client,'.'+decodeURIComponent(url.pathname));
  if(!candidate.startsWith(client+sep))return null;
  const path=await realpath(candidate).catch(error=>{
    if(['ENOENT','ENOTDIR'].includes(error.code))return null;throw error;});
  if(!path)return null;
  assert.ok(path.startsWith(client+sep));
  const bytes=await readFile(path),name='client/'+relative(client,path).split(sep).join('/');
  assert.equal(sha(bytes),inventory.distFiles[name],name);
  return new Response(request.method==='HEAD'?null:bytes,{headers:{
    'Content-Type':types[extname(path)]||'application/octet-stream','Content-Length':String(bytes.length)}});
}
createServer(async(incoming,outgoing)=>{
  try{
    if(incoming.headers.host!=='127.0.0.1:5198'){outgoing.writeHead(421).end();return;}
    const url=new URL(incoming.url,origin);assert.equal(url.origin,origin);
    const headers=new Headers(incoming.headers);
    for(const key of [...headers.keys()])if(key.startsWith('oai-authenticated-user-'))headers.delete(key);
    let body;
    if(incoming.method==='POST'){
      if(!['/api/player/prepare','/api/resolve'].includes(url.pathname)){outgoing.writeHead(405).end();return;}
      const chunks=[];let count=0;
      for await(const chunk of incoming){count+=chunk.length;assert.ok(count<=4096);chunks.push(chunk);}
      const raw=Buffer.concat(chunks);
      const value=await parseHeldJson(raw,{path:'original private host request',output});
      const plan=binding.plans.find(plan=>plan.alias===value.baseSha);assert.ok(plan);
      assert.deepEqual(Object.keys(value).sort(),['baseSha','choices','id']);
      assert.equal(value.id,plan.start);assert.deepEqual(value.choices,{});
      body=raw;
    }else if(!['GET','HEAD'].includes(incoming.method)){outgoing.writeHead(405).end();return;}
    const request=new Request(url,{method:incoming.method,headers,...(body===undefined?{}:{body})});
    const response=await assets(request)||await worker.fetch(request,{...env,ASSETS:{fetch:assets}},
      {waitUntil(task){task.catch(error=>console.error('PRIVATE_BACKGROUND_TASK_FAILED',error));}});
    if(outgoing.destroyed){await response.body?.cancel();return;}
    outgoing.writeHead(response.status,Object.fromEntries(response.headers));
    if(response.body&&incoming.method!=='HEAD')await pipeline(Readable.fromWeb(response.body),outgoing);
    else outgoing.end();
  }catch(error){
    if(outgoing.destroyed&&['ERR_STREAM_PREMATURE_CLOSE','ERR_STREAM_UNABLE_TO_PIPE'].includes(error.code))return;
    console.error('PRIVATE_HOST_REQUEST_FAILED',error);
    if(!outgoing.headersSent)outgoing.writeHead(500);
    outgoing.end();
  }
}).listen(5198,'127.0.0.1',()=>console.log('Released private Mimi105 host '+origin));
