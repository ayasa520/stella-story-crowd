// Read-only production verification after root's exact script main ACK.
// Preserve both responses before assertions; never substitute local nodes,
// before-state, fonts, renderer or clocks into the returned normal program.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {isDeepStrictEqual} from 'node:util';

const root='/home/rikka/Projects/stella';
const area=path.join(root,'artifacts/stella-script-continuation-20261121');
const repo=path.join(area,'data-checkout');
const source=path.join(root,'artifacts/stella-site-repair-source/.sites-checkout');
const sourceCommit='643f88a0928fe6bda8ac1c6fac9409a2fbdbdf0f';
const runtime=path.join(area,'episode5-silent54-saved-runtime-v2/attempt-2');
const runtimeResult=path.join(runtime,'result.json');
const referenceProgramSha256='8cfee866f5a09695937da49d5d8271e6f3b11993c4d88954f2ef7e2fe31d1faa';
const origin='https://stella-preview.jaoushingan.com';
const start='node:10090015:node_dae6816ae851';
const sectionSceneIds=[10090013,10090014,10090015];
const routeScenarios=[45,54,46,49,47];
const terminalTarget='node:10020001:1002000100001';
const expectedJa='\u2015\u2015。\n\u2015\u2015\u2015\u2015。\n\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015。';
const expectedZh='\u2014\u2014。\n\u2014\u2014\u2014\u2014。\n\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014。';
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',env:{...process.env,GIT_OPTIONAL_LOCKS:'0'}}).trim();
const witness=file=>{const raw=fs.readFileSync(file);return {path:file,bytes:raw.length,sha256:hash(raw)};};
const write=(out,name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const own=id=>typeof id==='string'&&id.startsWith('node:10090015:');

function argumentsFrom(argv){
  const options={};
  for(let index=0;index<argv.length;index+=2){
    const key=argv[index];
    assert.ok(['--expected-head','--remote-ack-receipt','--out'].includes(key),'Unknown argument '+key);
    assert.ok(argv[index+1]&&!argv[index+1].startsWith('--'),'Missing value for '+key);
    assert.ok(!Object.hasOwn(options,key),'Duplicate argument '+key);options[key]=argv[index+1];
  }
  for(const key of ['--expected-head','--remote-ack-receipt','--out'])assert.ok(options[key],'Required '+key);
  assert.match(options['--expected-head'],/^[a-f0-9]{40}$/,'Expected head must be a full lowercase40hex commit');
  return options;
}

function exactAck(file,expected){
  const raw=fs.readFileSync(file),value=JSON.parse(raw);
  // Match the existing final-main receipt convention. A Boolean, transfer
  // byte count or push exit code cannot replace a successful exact ref read.
  assert.equal(value.main,expected,'ACK receipt main');
  assert.equal(value.finalRead?.exitCode,0,'ACK exact ref read exit');
  assert.equal(typeof value.finalRead?.stdout,'string','ACK must retain actual ref-read stdout');
  assert.match(value.finalRead.stdout,new RegExp('^'+expected+'\\trefs/heads/main\\r?\\n?$'),'ACK must contain exactly the expected main ref');
  return {path:file,bytes:raw.length,sha256:hash(raw),main:value.main,finalRead:value.finalRead};
}

function checkTarget(nodes,edges){
  assert.equal(nodes.length,53);assert.equal(edges.length,54);
  const silent=nodes.filter(n=>n.scenario_id===54);assert.equal(silent.length,1);
  assert.equal(silent[0].id,'node:10090015:node_869b7bc19352');
  assert.equal(silent[0].kind,'card');assert.equal(silent[0].speaker,'スバル');
  assert.equal(silent[0].model,'subaru01');
  assert.equal(silent[0].text,expectedJa);assert.equal(silent[0].translation,expectedZh);
  const route=routeScenarios.map(scenario=>{
    const found=nodes.filter(n=>n.scenario_id===scenario);assert.equal(found.length,1);return found[0];
  });
  assert.equal(route[0].id,start);
  const transitions=route.map((node,index)=>{
    const outgoing=edges.filter(e=>e.source===node.id);assert.equal(outgoing.length,1);
    const edge=outgoing[0];assert.equal(edge.available,true);
    if(index<route.length-1){
      assert.equal(edge.flow_action,'continue');assert.equal(edge.target,route[index+1].id);
      assert.equal(edge.native_transition.next_scenario_id,routeScenarios[index+1]);
    }else{
      assert.equal(edge.flow_action,'section');assert.equal(edge.target,terminalTarget);
      assert.equal(edge.native_transition.next_scenario_id,0);
      assert.equal(edge.native_transition.next_scenario_label,'FINISH');
      assert.equal(edge.native_transition.next_section_id,1002);
      assert.equal(edge.native_transition.next_scene_id,10020001);
    }
    return {source:edge.source,target:edge.target,flow_action:edge.flow_action,native_transition:edge.native_transition};
  });
  return {scenarios:routeScenarios,ids:route.map(n=>n.id),transitions,terminalExecuted:false};
}

const options=argumentsFrom(process.argv.slice(2));
const expected=options['--expected-head'];
const requestedOut=path.resolve(options['--out']);
assert.equal(fs.existsSync(requestedOut),false,'Output directory must not already exist');
const out=path.join(fs.realpathSync(path.dirname(requestedOut)),path.basename(requestedOut));
assert.ok(out.startsWith(fs.realpathSync(area)+path.sep),'Output must be a new evidence directory under A');
assert.ok(out!==repo&&!out.startsWith(repo+path.sep),'Output must not write formal data or Git');
fs.mkdirSync(out); // No recursive mkdir: an absent parent or existing output is an error.
const records=[];let stage='local-preflight',inputs,ack,offline;
let latestResponse;
const saveHttp=()=>fs.writeFileSync(path.join(out,'http-receipt.json'),JSON.stringify({
  schema:'stella.episode5.silent54.production-http.v1',requestDeadlineMs:60000,retries:0,
  headerRepresentation:'Fetch-exposed HTTP headers; body bytes are after Fetch transfer decoding',records,
},null,2)+'\n');

async function request(name,url,body){
  const row={name,method:body?'POST':'GET',requestedUrl:url,request:body??null,
    startedUtc:new Date().toISOString(),deadlineMs:60000,status:null,headers:null,bodyComplete:false};
  records.push(row);saveHttp();
  const chunks=[];
  try{
    const response=await fetch(url,{method:row.method,redirect:'manual',headers:{
      'user-agent':'Mozilla/5.0 (X11; Linux aarch64; rv:159.0) Gecko/20100101 Firefox/159.0',
      accept:'application/json','accept-encoding':'identity',
      ...(body?{'content-type':'application/json',origin}:{}),
    },...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(60000)});
    row.url=response.url;row.status=response.status;row.statusText=response.statusText;
    row.headers=Object.fromEntries(response.headers.entries());
    row.setCookie=response.headers.getSetCookie?.()??[];saveHttp();
    // Preserve partial bytes too if the deadline aborts an in-progress body.
    if(response.body)for await(const chunk of response.body)chunks.push(Buffer.from(chunk));
    row.bodyComplete=true;
  }catch(error){
    row.transportError={name:error.name,message:error.message,stack:error.stack,
      cause:error.cause?{name:error.cause.name,message:error.cause.message,code:error.cause.code}:null};
    throw error;
  }finally{
    const raw=Buffer.concat(chunks),compressed=zlib.gzipSync(raw);
    row.decodedResponseBytes=raw.length;row.decodedResponseSha256=hash(raw);
    row.gzipFile=name+'.response.gz';row.gzipBytes=compressed.length;row.gzipSha256=hash(compressed);
    fs.writeFileSync(path.join(out,row.gzipFile),compressed,{flag:'wx'});
    assert.deepEqual(zlib.gunzipSync(compressed),raw);
    row.finishedUtc=new Date().toISOString();latestResponse={row,raw};saveHttp();
  }
  assert.equal(row.status,200,name+' HTTP status; exact body retained in '+row.gzipFile);
  const raw=Buffer.concat(chunks);
  try{return JSON.parse(raw);}catch(error){row.parseError={name:error.name,message:error.message};saveHttp();throw error;}
}

try{
  assert.equal(git(repo,'cat-file','-t',expected),'commit','Expected head must name an actual local commit');
  assert.equal(git(repo,'rev-parse','HEAD'),expected,'Expected script commit must equal local HEAD');
  assert.equal(git(source,'rev-parse','HEAD'),sourceCommit,'Fixed canonical source head');
  git(source,'diff','--no-ext-diff','--exit-code','HEAD','--');
  const ackFile=fs.realpathSync(path.resolve(options['--remote-ack-receipt']));
  ack=exactAck(ackFile,expected);
  const localFiles={};
  for(const member of ['manifest.json','native/scenes/10090015.json','review/scenes/10090015.json']){
    // The complete manifest is several MiB. Preserve raw Git bytes and bind
    // the output size above Node's default 1 MiB before comparing the section.
    const committed=execFileSync('git',['show',expected+':'+member],{cwd:repo,env:{...process.env,GIT_OPTIONAL_LOCKS:'0'},maxBuffer:64*1024*1024});
    assert.deepEqual(fs.readFileSync(path.join(repo,member)),committed,'Working file differs from committed '+member);
    localFiles[member]={path:member,committedSha256:hash(committed),bytes:committed.length,value:JSON.parse(committed)};
  }
  // Production prepare is section-scoped. Derive its count from this exact
  // committed manifest, independently of the full local saved-runtime library.
  const sectionScenes=localFiles['manifest.json'].value.scenes.filter(s=>s.sectionId===1009).sort((a,b)=>a.id-b.id);
  assert.deepEqual(sectionScenes.map(s=>s.id),sectionSceneIds);
  for(const scene of sectionScenes)assert.ok(Number.isSafeInteger(scene.nodeCount)&&scene.nodeCount>0);
  const sectionCounts=sectionScenes.map(s=>({sceneId:s.id,nodeCount:s.nodeCount}));
  const expectedProductionSectionNodes=sectionScenes.reduce((sum,s)=>sum+s.nodeCount,0);
  assert.equal(sectionScenes.find(s=>s.id===10090015).nodeCount,53);
  const actualRuntime=JSON.parse(fs.readFileSync(runtimeResult));
  assert.deepEqual(actualRuntime.cases.map(c=>c.language),['zh','ja']);
  const gzipFiles=actualRuntime.cases.map(c=>c.prepared.gzipFile);
  assert.equal(gzipFiles[0],gzipFiles[1]);
  assert.equal(gzipFiles[0],'normal-http-'+referenceProgramSha256+'.json.gz');
  for(const entry of actualRuntime.cases){
    assert.equal(entry.prepared.status,200);assert.equal(entry.prepared.start,start);
    assert.equal(entry.prepared.rawSha256,referenceProgramSha256);
    assert.equal(entry.prepared.programSha256,referenceProgramSha256);
  }
  const reference=path.join(runtime,gzipFiles[0]);
  const referenceRaw=zlib.gunzipSync(fs.readFileSync(reference));
  assert.equal(hash(referenceRaw),referenceProgramSha256,'Exact actual attempt2 normal HTTP program');
  offline=JSON.parse(referenceRaw);
  assert.equal(offline.start,start);assert.equal(offline.nodes.length,5620);
  const oldNodes=offline.nodes.filter(n=>own(n.id)),oldEdges=offline.edges.filter(e=>own(e.source));
  checkTarget(oldNodes,oldEdges);
  const localNative=localFiles['native/scenes/10090015.json'].value;
  const nativeSilent=localNative.scenario_list.find(n=>n.scenario_id===54);
  assert.equal(nativeSilent.scenario_type,2);assert.equal(nativeSilent.character,'live2d/AC_subaru01');
  assert.equal(nativeSilent.msg_character,'スバル');assert.equal(nativeSilent.msg_text,expectedZh);
  inputs={schema:'stella.episode5.silent54.production-inputs.v1',expectedHead:expected,sourceCommit,
    helper:witness(fileURLToPath(import.meta.url)),remoteAck:ack,reference:witness(reference),
    actualRuntimeResult:witness(runtimeResult),referenceDecodedProgramSha256:referenceProgramSha256,
    committedFiles:Object.values(localFiles).map(({value,...descriptor})=>descriptor),
    dataStatus:git(repo,'status','--short'),sourceStatus:git(source,'status','--short'),
    productionOrigin:origin,expectedLocalLibraryNodes:5620,expectedProductionSectionNodes,sectionCounts,
    browserStarted:false,sourceDataOrGitWrites:false};
  write(out,'input-binding.json',inputs);
  stage='default-main-native-source';
  const published=await request(stage,origin+'/api/native/source?sceneId=10090015');
  assert.equal(published.headSha,expected,'Actual default-main revision must match exact ACK');
  assert.deepEqual(published.document,localNative,'Complete committed native object');
  assert.deepEqual(published.review,localFiles['review/scenes/10090015.json'].value,'Complete committed review object');
  stage='normal-saved-player-prepare';
  const requestBody={id:start,baseSha:published.headSha,choices:{}};
  const program=await request(stage,origin+'/api/player/prepare',requestBody);
  assert.equal(program.headSha,published.headSha);assert.equal(program.start,start);
  const nodes=program.nodes.filter(n=>own(n.id)),edges=program.edges.filter(e=>own(e.source));
  assert.deepEqual(nodes,oldNodes,'All53 complete target nodes equal actual saved runtime input');
  assert.deepEqual(edges,oldEdges,'All54 source edges equal actual saved runtime input');
  const route=checkTarget(nodes,edges);
  const sceneIds=[...new Set(program.nodes.map(n=>n.scene_id))].sort();
  assert.deepEqual(sceneIds,sectionSceneIds.map(id=>'scene:'+id));
  assert.equal(program.nodes.length,expectedProductionSectionNodes);
  for(const scene of sectionScenes)assert.equal(program.nodes.filter(n=>n.scene_id==='scene:'+scene.id).length,scene.nodeCount);
  // Compare before exactly as returned, independently of target node equality.
  // A real scope-related entry difference is retained, never seeded away.
  const beforeEqual=isDeepStrictEqual(program.before,offline.before);
  const before={production:program.before,localSavedRuntime:offline.before,fullObjectEqual:beforeEqual,
    differingFields:[...new Set([...Object.keys(program.before),...Object.keys(offline.before)])]
      .filter(key=>!isDeepStrictEqual(program.before[key],offline.before[key])),stateSeededOrModified:false};
  assert.equal(git(repo,'rev-parse','HEAD'),expected,'Local head changed during readback');
  assert.equal(git(source,'rev-parse','HEAD'),sourceCommit);git(source,'diff','--no-ext-diff','--exit-code','HEAD','--');
  assert.equal(witness(ackFile).sha256,ack.sha256,'ACK evidence changed during readback');
  for(const member of Object.keys(localFiles))assert.equal(witness(path.join(repo,member)).sha256,localFiles[member].committedSha256);
  const result={schema:'stella.episode5.silent54.production-readback.v1',
    status:beforeEqual?'passed':'passed-target-readback-before-differs',scriptCommit:expected,sourceCommit,
    defaultMainSourceMatchesCommittedNativeAndReview:true,all53TargetNodesAnd54SourceEdgesEqualActualSavedRuntime:true,
    silent54:{kind:'card',speaker:'スバル',model:'subaru01',japanese:expectedJa,chinese:expectedZh},route,
    productionSceneIds:sceneIds,productionSectionNodes:expectedProductionSectionNodes,sectionCounts,
    localSavedRuntimeLibraryNodes:5620,wholeProgramScopeEquivalent:false,before,
    initialStateEquivalenceAccepted:beforeEqual,beforeEquivalenceScope:'Exact returned JSON only; no runtime playback equivalence',
    remoteAck:ack,http:records,inputs,browserStarted:false,frontendWrites:false,workerRedeploy:false,
    programOrBeforeInjected:false,sourceDataOrGitWrites:false,wholeSceneAccepted:false,
    motionFaceOrContinuousActorPerformanceAccepted:false};
  write(out,'verification.json',result);
  console.log(JSON.stringify({status:result.status,scriptCommit:expected,nodes:53,sourceEdges:54,
    productionSectionNodes:expectedProductionSectionNodes,localLibraryNodes:5620,beforeEqual,
    productionBeforeBg:program.before.bg_picture,productionBeforeModel:program.before.model,
    verificationSha256:witness(path.join(out,'verification.json')).sha256}));
}catch(error){
  write(out,'failure.json',{schema:'stella.episode5.silent54.production-readback-failure.v1',stage,
    error:{name:error.name,message:error.message,stack:error.stack,cause:error.cause?String(error.cause):null},
    expectedHead:expected,remoteAck:ack??null,inputs:inputs??null,http:records,
    exactLastResponse:latestResponse?{gzipFile:latestResponse.row.gzipFile,
      decodedResponseSha256:latestResponse.row.decodedResponseSha256,bodyComplete:latestResponse.row.bodyComplete}:null,
    originalFailureBodyRetainedInResponseGzip:latestResponse!==undefined,retries:0,sourceDataOrGitWrites:false});
  console.error(error.stack||String(error));process.exitCode=1;
}
