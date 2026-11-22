// A narrow local host for the unchanged compiled Worker and frozen public
// assets. The only extra GETs deliver the exact private diagnostic modules;
// mutation endpoints are rejected before reaching the normal Worker.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {resolve,sep,extname} from 'node:path';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {runtimeGate} from './node-guards.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const {binding}=await runtimeGate(here,import.meta.url);
const workersModule=new URL('workers-private.mjs',here).href;
registerHooks({resolve(specifier,context,next){return specifier==='cloudflare:workers'?{url:workersModule,shortCircuit:true}:next(specifier,context);}});
const {env}=await import(workersModule);assert.equal(env.STELLA_HOSTING,undefined);
const worker=(await import(pathToFileURL(binding.sourceRoot+'/dist/server/index.js'))).default;
const client=resolve(binding.sourceRoot,'dist/client');
const types={'.js':'text/javascript','.json':'application/json','.html':'text/html; charset=utf-8',
  '.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
async function assets(request){
  if(!['GET','HEAD'].includes(request.method))return null;
  const url=new URL(request.url),diagnostic={
    '/__private/owner-events.mjs':new URL('owner-events.mjs',here),
    '/__private/tap-v2.mjs':pathToFileURL(binding.tap.path)}[url.pathname];
  if(diagnostic){
    const bytes=await readFile(diagnostic);
    const expected=url.pathname.endsWith('tap-v2.mjs')?binding.tap.sha256:binding.fileGuards[fileURLToPath(diagnostic)];
    assert.equal(createHash('sha256').update(bytes).digest('hex'),expected);
    return new Response(request.method==='HEAD'?null:bytes,{headers:{'Content-Type':'text/javascript','Cache-Control':'no-store'}});
  }
  const path=resolve(client,'.'+decodeURIComponent(url.pathname));
  if(!path.startsWith(client+sep))return null;
  const file=await stat(path).catch(e=>{if(['ENOENT','ENOTDIR'].includes(e.code))return null;throw e;});
  if(!file?.isFile())return null;
  return new Response(request.method==='HEAD'?null:await readFile(path),{headers:{
    'Content-Type':types[extname(path)]||'application/octet-stream','Content-Length':String(file.size)}});
}
createServer(async(incoming,outgoing)=>{
  try{
    if(incoming.headers.host!=='127.0.0.1:5198'){outgoing.writeHead(421).end();return;}
    const url=new URL(incoming.url,origin);
    if(url.origin!==origin){outgoing.writeHead(400).end();return;}
    const headers=new Headers(incoming.headers);
    for(const name of [...headers.keys()])if(name.startsWith('oai-authenticated-user-'))headers.delete(name);
    let body;
    if(incoming.method==='POST'){
      if(!['/api/player/prepare','/api/resolve'].includes(url.pathname)){outgoing.writeHead(405).end();return;}
      const chunks=[];let length=0;
      for await(const chunk of incoming){length+=chunk.length;assert.ok(length<=4096);chunks.push(chunk);}
      body=Buffer.concat(chunks).toString('utf8');
      const value=JSON.parse(body),plan=binding.plans[0];
      assert.equal(value.baseSha,binding.finalDataHead,'Only the published ordinary revision is admitted');assert.deepEqual(Object.keys(value).sort(),['baseSha','choices','id']);
      assert.equal(value.id,plan.start);assert.deepEqual(value.choices,{});
    }else if(!['GET','HEAD'].includes(incoming.method)){outgoing.writeHead(405).end();return;}
    const request=new Request(url,{method:incoming.method,headers,...(body===undefined?{}:{body})});
    const response=await assets(request)||await worker.fetch(request,{...env,ASSETS:{fetch:assets}},
      {waitUntil(p){p.catch(e=>console.error('PRIVATE_BACKGROUND_TASK_FAILED',e));}});
    if(outgoing.destroyed){await response.body?.cancel();return;}
    outgoing.writeHead(response.status,Object.fromEntries(response.headers));
    if(response.body&&incoming.method!=='HEAD')await pipeline(Readable.fromWeb(response.body),outgoing);
    else outgoing.end();
  }catch(error){
    if(outgoing.destroyed&&['ERR_STREAM_PREMATURE_CLOSE','ERR_STREAM_UNABLE_TO_PIPE'].includes(error.code))return;
    console.error('PRIVATE_HOST_REQUEST_FAILED',error);if(!outgoing.headersSent)outgoing.writeHead(500);outgoing.end();
  }
}).listen(5198,'127.0.0.1',()=>console.log('Ordinary P30 diagnostic host listening '+origin));
