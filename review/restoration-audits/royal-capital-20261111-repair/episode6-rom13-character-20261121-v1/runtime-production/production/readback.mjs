// One root-released production readback, with no browser, local server, Git,
// business parser rerun, or data/source writes. Use the real default-main
// native/source endpoint, then one ordinary player/prepare request. Preserve
// complete transfer-decoded response bytes and partial failures before parsing
// or asserting. No retry, response repair, program override or before seed exists.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gunzipSync,gzipSync} from 'node:zlib';
import {isDeepStrictEqual} from 'node:util';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {getPriority} from 'node:os';

const HERE=dirname(fileURLToPath(import.meta.url)),ROOT=resolve(HERE,'../../..');
const origin='https://stella-preview.jaoushingan.com';
const expectedHead='82533db262ea63cc970fce5433d26e801c72a93c';
const start='node:10020037:1002003700011',prefix='node:10020037:';
const own=id=>typeof id==='string'&&id.startsWith(prefix);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const options={};
for(let i=2;i<process.argv.length;i+=2){
 const key=process.argv[i];assert.ok(['--release','--release-sha256','--attempt'].includes(key));
 assert.ok(process.argv[i+1]&&!Object.hasOwn(options,key));options[key]=process.argv[i+1];
}
for(const key of ['--release','--release-sha256','--attempt'])assert.ok(options[key]);
assert.equal(options['--attempt'],'attempt-1');
const releasePath=resolve(options['--release']),releaseRaw=await readFile(releasePath),release=JSON.parse(releaseRaw);
assert.equal(sha(releaseRaw),options['--release-sha256']);
assert.equal(release.rootConfirmed,true);assert.equal(release.executionAuthorized,true);
assert.equal(release.networkAuthorized,true);assert.equal(release.browserLaunchAuthorized,false);
assert.equal(release.expectedHead,expectedHead);assert.equal(release.sourceHead,'9d39252bde3b57983fe9a1e9c563f891bb781622');
assert.equal(release.origin,origin);assert.equal(release.start,start);
assert.equal(getPriority(),19);
assert.match(await readFile('/proc/self/status','utf8'),/^Cpus_allowed_list:\s*0-1\s*$/m);
for(const name of ['readback.mjs','README.md'])
 assert.equal(release.runtimeBindings[`${HERE.slice(ROOT.length+1)}/${name}`],sha(await readFile(resolve(HERE,name))));
assert.ok(Object.keys(release.guards).length>=6);
const required=[release.nativePath,release.reviewPath,release.referencePath,release.referenceReceiptPath,release.ackPath,
 'artifacts/stella-site-repair-source/.sites-checkout/lib/studio-api.ts'];
assert.ok(required.every(path=>typeof path==='string'&&Object.hasOwn(release.guards,path)));
async function guardCheck(){for(const collection of [release.guards,release.runtimeBindings])
 for(const [path,wanted]of Object.entries(collection))assert.equal(sha(await readFile(resolve(ROOT,path))),wanted,path);}
await guardCheck();
const out=resolve(HERE,options['--attempt']);await mkdir(out);
const write=(name,value)=>writeFile(resolve(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const records=[];let stage='local-preflight',inputs,latestResponse;
const saveHttp=()=>writeFile(resolve(out,'http-receipt.json'),JSON.stringify({schema:'stella.rom13.production-http.v1',
 requestDeadlineMs:60000,retries:0,headerRepresentation:'Fetch-exposed headers; body bytes after Fetch transfer decoding',records},null,2)+'\n');
async function request(name,url,body){
 const row={name,method:body?'POST':'GET',requestedUrl:url,request:body??null,startedUtc:new Date().toISOString(),
  deadlineMs:60000,status:null,headers:null,bodyComplete:false};records.push(row);await saveHttp();
 const chunks=[];
 try{
  const response=await fetch(url,{method:row.method,redirect:'manual',credentials:'omit',headers:{
   'user-agent':'Mozilla/5.0 (X11; Linux aarch64; rv:159.0) Gecko/20100101 Firefox/159.0',
   accept:'application/json','accept-encoding':'identity',...(body?{'content-type':'application/json',origin}:{})},
   ...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(60000)});
  row.url=response.url;row.status=response.status;row.statusText=response.statusText;
  row.headers=Object.fromEntries(response.headers.entries());await saveHttp();
  if(response.body)for await(const chunk of response.body)chunks.push(Buffer.from(chunk));
  row.bodyComplete=true;
 }catch(error){
  row.transportError={name:error.name,message:error.message,stack:error.stack,
   cause:error.cause?{name:error.cause.name,message:error.cause.message,code:error.cause.code}:null};throw error;
 }finally{
  // A timeout can follow real headers and partial body delivery. Preserve all
  // received bytes even then, so a failed attempt remains an actual witness.
  const raw=Buffer.concat(chunks),compressed=gzipSync(raw);
  row.decodedResponseBytes=raw.length;row.decodedResponseSha256=sha(raw);
  row.gzipFile=name+'.response.gz';row.gzipBytes=compressed.length;row.gzipSha256=sha(compressed);
  await writeFile(resolve(out,row.gzipFile),compressed,{flag:'wx'});
  assert.ok(gunzipSync(compressed).equals(raw));row.finishedUtc=new Date().toISOString();
  latestResponse={row,raw};await saveHttp();
 }
 assert.equal(row.status,200,name+' HTTP status; original body retained');
 try{return JSON.parse(Buffer.concat(chunks));}
 catch(error){row.parseError={name:error.name,message:error.message};await saveHttp();throw error;}
}
try{
 const ackBytes=await readFile(resolve(ROOT,release.ackPath)),ack=JSON.parse(ackBytes);
 assert.equal(ack.head,expectedHead);assert.equal(ack.exactRemoteAck.head,expectedHead);
 assert.equal(ack.exactRemoteAck.ref,'refs/heads/main');assert.equal(ack.exactRemoteAck.exitCode,0);
 assert.equal(ack.committedBlobsExact,true);
 const nativeRaw=await readFile(resolve(ROOT,release.nativePath)),reviewRaw=await readFile(resolve(ROOT,release.reviewPath));
 const native=JSON.parse(nativeRaw),review=JSON.parse(reviewRaw);
 const referenceCompressed=await readFile(resolve(ROOT,release.referencePath)),referenceRaw=gunzipSync(referenceCompressed);
 assert.equal(sha(referenceRaw),release.referenceDecodedSha256);
 const reference=JSON.parse(referenceRaw),referenceReceipt=JSON.parse(await readFile(resolve(ROOT,release.referenceReceiptPath)));
 assert.equal(referenceReceipt.status,200);assert.equal(referenceReceipt.rawResponseSha256,sha(referenceRaw));
 assert.equal(referenceReceipt.dataHead,expectedHead);assert.equal(referenceReceipt.programMutated,false);
 assert.equal(reference.headSha,expectedHead);assert.equal(reference.start,start);
 const savedNodes=reference.nodes.filter(node=>own(node.id)),savedEdges=reference.edges.filter(edge=>own(edge.source));
 assert.equal(savedNodes.length,19);
 inputs={schema:'stella.rom13.production-input-binding.v1',expectedHead,sourceHead:release.sourceHead,start,
  release:{path:releasePath,sha256:sha(releaseRaw)},runtimeBindings:release.runtimeBindings,guards:release.guards,
  reference:{path:release.referencePath,gzipBytes:referenceCompressed.length,gzipSha256:sha(referenceCompressed),
   decodedBytes:referenceRaw.length,decodedSha256:sha(referenceRaw),libraryNodes:reference.nodes.length,
   targetNodes:savedNodes.length,targetSourceEdges:savedEdges.length},
  ack:{path:release.ackPath,sha256:sha(ackBytes),exactRemoteAck:ack.exactRemoteAck},
  localFiles:{native:{path:release.nativePath,bytes:nativeRaw.length,sha256:sha(nativeRaw)},
   review:{path:release.reviewPath,bytes:reviewRaw.length,sha256:sha(reviewRaw)}},
  localFilesBoundToCommittedSaveByRoot:true,networkRequestsMaximum:2,retries:0,browserStarted:false,serverStarted:false,gitExecuted:false};
 await write('input-binding.json',inputs);
 stage='default-main-native-source';
 const published=await request(stage,origin+'/api/native/source?sceneId=10020037');
 assert.equal(published.headSha,expectedHead,'Actual default main must equal released saved head');
 assert.deepEqual(published.document,native,'Complete saved native object');
 assert.deepEqual(published.review,review,'Complete saved review object');
 stage='normal-saved-player-prepare';
 const requestBody={id:start,baseSha:expectedHead,choices:{}};
 const program=await request(stage,origin+'/api/player/prepare',requestBody);
 assert.equal(program.headSha,expectedHead);assert.equal(program.start,start);
 const nodes=program.nodes.filter(node=>own(node.id)),edges=program.edges.filter(edge=>own(edge.source));
 assert.equal(nodes.length,19);assert.deepEqual(nodes,savedNodes,'All19 complete target scene nodes');
 assert.deepEqual(edges,savedEdges,'Every edge sourced in the target scene');
 const rom13=nodes.find(node=>node.scenario_id===13);assert.equal(rom13.model,'rom01');
 const unknown=edges.find(edge=>edge.source===prefix+'1002003700013'&&edge.id.endsWith(':133'));
 assert.ok(unknown);assert.equal(unknown.available,false);assert.equal(unknown.state,'missing');assert.equal(unknown.target,'');
 const choice=edges.find(edge=>edge.source===prefix+'1002003700013'&&edge.id.endsWith(':132'));
 assert.ok(choice);assert.equal(choice.target,prefix+'1002003700014');assert.equal(choice.label_translation,'零食？');
 // Section-scoped production and library-scoped local programs can have
 // different surrounding nodes. Compare the actual before object separately;
 // keep a real difference visible and never replace it with local state.
 const beforeEqual=isDeepStrictEqual(program.before,reference.before);
 const before={production:program.before,localSavedRuntime:reference.before,fullObjectEqual:beforeEqual,
  differingFields:[...new Set([...Object.keys(program.before),...Object.keys(reference.before)])]
   .filter(key=>!isDeepStrictEqual(program.before[key],reference.before[key])),stateSeededOrModified:false};
 await guardCheck();assert.equal(sha(await readFile(releasePath)),sha(releaseRaw));
 await write('verification.json',{schema:'stella.rom13.production-readback.v1',
  status:beforeEqual?'passed':'passed-target-readback-before-differs',scriptCommit:expectedHead,sourceHead:release.sourceHead,
  defaultMainNativeAndReviewMatchSavedObjects:true,all19TargetNodesEqualSavedRuntime:true,allTargetSourceEdgesEqualSavedRuntime:true,
  targetNodes:nodes.length,targetSourceEdges:edges.length,rom13Model:rom13.model,
  productionSceneIds:[...new Set(program.nodes.map(node=>node.scene_id))].sort(),productionNodes:program.nodes.length,
  localLibraryNodes:reference.nodes.length,wholeProgramScopeEquivalent:false,wholeLibraryProgramEqualityClaimed:false,
  before,initialStateEquivalenceAccepted:beforeEqual,beforeEquivalenceScope:'Returned JSON objects only; no playback equivalence',
  unknown133:{available:unknown.available,state:unknown.state,target:unknown.target},
  choice132:{target:choice.target,labelTranslation:choice.label_translation,executed:false},http:records,inputs,
  allInputGuardsUnchanged:true,programOrBeforeInjected:false,browserStarted:false,serverStarted:false,
  sourceDataOrGitWrites:false,wholeEpisodeAccepted:false,readerAnomalyCauseKnown:false});
 console.log(JSON.stringify({status:beforeEqual?'passed':'passed-target-readback-before-differs',targetNodes:nodes.length,
  targetSourceEdges:edges.length,productionNodes:program.nodes.length,localLibraryNodes:reference.nodes.length,beforeEqual,
  requests:records.length,retries:0,verificationSha256:sha(await readFile(resolve(out,'verification.json')))}));
}catch(error){
 await write('failure.json',{schema:'stella.rom13.production-readback-failure.v1',stage,
  error:{name:error.name,message:error.message,stack:error.stack,cause:error.cause?String(error.cause):null},
  expectedHead,inputs:inputs??null,http:records,retries:0,
  exactLastResponse:latestResponse?{gzipFile:latestResponse.row.gzipFile,decodedResponseSha256:latestResponse.row.decodedResponseSha256,
   bodyComplete:latestResponse.row.bodyComplete}:null,sourceDataOrGitWrites:false,browserStarted:false,serverStarted:false});
 console.error(error.stack||String(error));process.exitCode=1;
}
