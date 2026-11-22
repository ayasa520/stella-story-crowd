// Read saved scene sources through the deployed Worker's ordinary main API.
// Preserve the exact HTTP body before parsing or comparing it, so a transport,
// parser or revision error cannot erase the bytes that caused that decision.
// This tool does not load the player, mutate scripts, retry requests or accept
// acting, audible music, command phases, timing or continuous playback.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';

const a=path.dirname(fileURLToPath(import.meta.url));
const [expectedHead,sceneText,outputName]=process.argv.slice(2);
assert.match(expectedHead,/^[a-f0-9]{40}$/);
assert.match(sceneText,/^\d+(,\d+)*$/);
assert.match(outputName,/^[a-z0-9-]+$/);
const scenes=sceneText.split(',').map(Number);
assert.equal(new Set(scenes).size,scenes.length);
assert.ok(scenes.length>=1&&scenes.length<=3);
const out=path.join(a,outputName),data=path.join(a,'data-checkout');
assert.ok(!fs.existsSync(out),'An existing readback is never overwritten');
fs.mkdirSync(out);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const write=(name,j)=>fs.writeFileSync(path.join(out,name),JSON.stringify(j,null,2)+'\n',{flag:'wx'});

async function readScene(scene){
  const url='https://stella-preview.jaoushingan.com/api/native/source?sceneId='+scene;
  const transport={scene,url,method:'GET',startedUTC:new Date().toISOString(),expectedHead,automaticRetries:0};
  try{
    const response=await fetch(url,{signal:AbortSignal.timeout(60000)});
    const raw=Buffer.from(await response.arrayBuffer());
    Object.assign(transport,{status:response.status,bytes:raw.length,sha256:sha(raw),
      headers:Object.fromEntries(['content-type','cache-control','date','etag','cf-ray']
        .map(k=>[k,response.headers.get(k)]).filter(([,v])=>v!==null))});
    fs.writeFileSync(path.join(out,scene+'.response.json.gz'),gzipSync(raw,{level:6}),{flag:'wx'});
    write(scene+'.transport.json',transport);
    assert.ok(raw.length<=4*1024*1024,'Unexpected source response size; original body retained');
    assert.equal(response.status,200);
    const value=JSON.parse(raw.toString('utf8'));
    assert.equal(value.headSha,expectedHead,'Default main source revision differs');
    const nativeBytes=fs.readFileSync(path.join(data,'native/scenes/'+scene+'.json'));
    const reviewBytes=fs.readFileSync(path.join(data,'review/scenes/'+scene+'.json'));
    assert.deepEqual(value.document,JSON.parse(nativeBytes));
    assert.deepEqual(value.review,JSON.parse(reviewBytes));
    const verified={...transport,observedHead:value.headSha,completeNativeAndReviewExact:true,
      nativeFileSHA256:sha(nativeBytes),reviewFileSHA256:sha(reviewBytes),
      continuousPlaybackOrAudibleListeningAccepted:false};
    write(scene+'.verified.json',verified);
    return verified;
  }catch(error){
    // Failed HTTP/parse/comparison observations are retained once. A later
    // successful request must be a separately reviewed operation, never an
    // automatic retry that overwrites this evidence.
    write(scene+'.failure.json',{...transport,error:String(error),stack:error.stack,
      rawResponseRetained:fs.existsSync(path.join(out,scene+'.response.json.gz'))});
    throw error;
  }
}
const results=await Promise.allSettled(scenes.map(readScene));
const receipt={maximumRequests:scenes.length,retries:0,results:results.map(r=>r.status==='fulfilled'?r:
  {status:'rejected',reason:{error:String(r.reason),stack:r.reason?.stack}})};
write('receipt.json',receipt);
console.log(JSON.stringify({output:out,requests:scenes.length,allSucceeded:results.every(r=>r.status==='fulfilled'),
  completeNativeAndReviewExact:results.filter(r=>r.status==='fulfilled').length,expectedHead}));
if(results.some(r=>r.status==='rejected'))process.exitCode=1;
