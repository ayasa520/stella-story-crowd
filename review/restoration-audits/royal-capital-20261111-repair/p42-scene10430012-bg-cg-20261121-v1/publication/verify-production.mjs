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
const reference=path.join(area,'p42-six-visual-saved-runtime-v1/attempt-1/normal-http-prepare.json.gz');
const referenceProgramSha256='2b15057bb95408b4377ad7e059c686543388677b9bdb2c86ce6e279033b70494';
const origin='https://stella-preview.jaoushingan.com';
const start='node:10430012:1043001200023';
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const git=(cwd,...args)=>execFileSync('git',args,{cwd,encoding:'utf8',env:{...process.env,GIT_OPTIONAL_LOCKS:'0'}}).trim();
const witness=file=>{const raw=fs.readFileSync(file);return {path:file,bytes:raw.length,sha256:hash(raw)};};
const write=(out,name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const own=id=>typeof id==='string'&&id.startsWith('node:10430012:');
const fields=[
  {scenarioId:24,field:'character_image',expected:'ADV_pic_103002'},
  {scenarioId:28,field:'bg_picture',expected:'bg/bg070b_stealshop'},
  {scenarioId:29,field:'bg_picture',expected:'bg/bg031b_stealshop'},
  {scenarioId:31,field:'bg_picture',expected:'bg/bg070b_stealshop'},
  {scenarioId:33,field:'bg_picture',expected:'bg/bg031b_stealshop'},
  {scenarioId:38,field:'bg_picture',expected:'bg/bg070b_stealshop'},
];

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
  schema:'stella.p42.six-visual.production-http.v1',requestDeadlineMs:60000,retries:0,
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
  for(const member of ['native/scenes/10430012.json','review/scenes/10430012.json']){
    const committed=execFileSync('git',['show',expected+':'+member],{cwd:repo,env:{...process.env,GIT_OPTIONAL_LOCKS:'0'}});
    assert.deepEqual(fs.readFileSync(path.join(repo,member)),committed,'Working file differs from committed '+member);
    localFiles[member]={path:member,committedSha256:hash(committed),bytes:committed.length,value:JSON.parse(committed)};
  }
  const referenceRaw=zlib.gunzipSync(fs.readFileSync(reference));
  assert.equal(hash(referenceRaw),referenceProgramSha256,'Exact saved-runtime normal HTTP program');
  offline=JSON.parse(referenceRaw);
  assert.equal(offline.start,start);assert.equal(offline.nodes.length,5619);
  assert.equal(offline.before.bg_picture,'bg/bg031b_stealshop');assert.equal(offline.before.model,'pack01');
  const oldNodes=offline.nodes.filter(n=>own(n.id)),oldEdges=offline.edges.filter(e=>own(e.source));
  assert.equal(oldNodes.length,38);assert.equal(oldEdges.length,40);assert.equal(oldNodes.filter(n=>n.model).length,34);
  const localNative=localFiles['native/scenes/10430012.json'].value;
  for(const field of fields){
    const native=localNative.scenario_list.find(n=>n.scenario_id===field.scenarioId);
    assert.equal(native[field.field],field.expected,'Committed six-field value');
    assert.equal(oldNodes.find(n=>n.scenario_id===field.scenarioId)[field.field],field.expected,'Saved capture six-field value');
  }
  for(const number of [24,25])assert.equal(localNative.scenario_list.find(n=>n.scenario_id===number).bg_picture,'','Preserve sparse background');
  inputs={schema:'stella.p42.six-visual.production-inputs.v1',expectedHead:expected,sourceCommit,
    helper:witness(fileURLToPath(import.meta.url)),remoteAck:ack,reference:witness(reference),
    referenceDecodedProgramSha256:referenceProgramSha256,
    committedFiles:Object.values(localFiles).map(({value,...descriptor})=>descriptor),
    dataStatus:git(repo,'status','--short'),sourceStatus:git(source,'status','--short'),
    productionOrigin:origin,expectedLocalLibraryNodes:5619,expectedProductionSectionNodes:120,
    browserStarted:false,sourceDataOrGitWrites:false};
  write(out,'input-binding.json',inputs);
  stage='default-main-native-source';
  const published=await request(stage,origin+'/api/native/source?sceneId=10430012');
  assert.equal(published.headSha,expected,'Actual default-main revision must match exact ACK');
  assert.deepEqual(published.document,localNative,'Complete committed native object');
  assert.deepEqual(published.review,localFiles['review/scenes/10430012.json'].value,'Complete committed review object');
  stage='normal-saved-player-prepare';
  const requestBody={id:start,baseSha:published.headSha,choices:{}};
  const program=await request(stage,origin+'/api/player/prepare',requestBody);
  assert.equal(program.headSha,published.headSha);assert.equal(program.start,start);
  const nodes=program.nodes.filter(n=>own(n.id)),edges=program.edges.filter(e=>own(e.source));
  assert.equal(nodes.length,38);assert.equal(edges.length,40);assert.equal(nodes.filter(n=>n.model).length,34);
  assert.deepEqual(nodes,oldNodes,'All38 complete scene nodes equal saved runtime input');
  assert.deepEqual(edges,oldEdges,'All40 source edges equal saved runtime input');
  for(const field of fields)assert.equal(nodes.find(n=>n.scenario_id===field.scenarioId)[field.field],field.expected);
  const sceneIds=[...new Set(program.nodes.map(n=>n.scene_id))].sort();
  assert.deepEqual(sceneIds,['scene:10430012','scene:10430013','scene:10430014']);assert.equal(program.nodes.length,120);
  for(const [scenario,branch]of [[6,63],[19,192]]){
    const edge=edges.find(e=>e.source===`node:10430012:${1043001200000+scenario}`&&e.id.endsWith(':'+branch));
    assert.equal(edge.available,false);assert.equal(edge.state,'missing');assert.equal(edge.target,'');
  }
  const terminal=edges.find(e=>e.source==='node:10430012:1043001200038');
  assert.ok(terminal.id.endsWith(':381'));assert.equal(terminal.target,'node:10430013:1043001300001');
  const cg=nodes.find(n=>n.scenario_id===24),next=nodes.find(n=>n.scenario_id===25);
  assert.equal(cg.speaker,'エルザ');assert.equal(cg.character_image,'ADV_pic_103002');
  assert.equal(cg.bg_picture,'');assert.equal(next.bg_picture,'');
  assert.equal(cg.script_background.resource,'bg/bg031b_stealshop');
  assert.equal(next.script_background.resource,'bg/bg031b_stealshop');
  assert.equal(program.semantics.illustration_background,'bg/bg001_black');
  // Compare before as returned. Scope differences can produce a real entry
  // difference even when the38 nodes/40 edges agree; never seed it away.
  const beforeEqual=isDeepStrictEqual(program.before,offline.before);
  const before={production:program.before,localSavedRuntime:offline.before,fullObjectEqual:beforeEqual,
    productionMatchesExpectedBgAndModel:program.before.bg_picture==='bg/bg031b_stealshop'&&program.before.model==='pack01',
    differingFields:[...new Set([...Object.keys(program.before),...Object.keys(offline.before)])]
      .filter(key=>!isDeepStrictEqual(program.before[key],offline.before[key])),stateSeededOrModified:false};
  assert.equal(git(repo,'rev-parse','HEAD'),expected,'Local head changed during readback');
  assert.equal(git(source,'rev-parse','HEAD'),sourceCommit);git(source,'diff','--no-ext-diff','--exit-code','HEAD','--');
  assert.equal(witness(ackFile).sha256,ack.sha256,'ACK evidence changed during readback');
  for(const member of Object.keys(localFiles))assert.equal(witness(path.join(repo,member)).sha256,localFiles[member].committedSha256);
  const result={schema:'stella.p42.six-visual.production-readback.v1',
    status:beforeEqual?'passed':'passed-target-readback-before-differs',scriptCommit:expected,sourceCommit,
    defaultMainSourceMatchesCommittedNativeAndReview:true,all38SceneNodesAnd40SourceEdgesEqualSavedRuntime:true,
    actorModels:34,sixFields:fields,productionSceneIds:sceneIds,productionSectionNodes:120,
    localSavedRuntimeLibraryNodes:5619,wholeProgramScopeEquivalent:false,before,
    initialStateEquivalenceAccepted:beforeEqual,beforeEquivalenceScope:'Exact returned JSON only; no runtime playback equivalence',
    cg24:{resource:cg.character_image,speaker:cg.speaker,rawBackground:cg.bg_picture,
      scriptBackground:cg.script_background,expectedDisplayPlate:program.semantics.illustration_background},
    node25:{rawBackground:next.bg_picture,scriptBackground:next.script_background},
    terminal:{target:terminal.target,executed:false},unknownBranchesUnchanged:true,
    remoteAck:ack,http:records,inputs,browserStarted:false,frontendWrites:false,workerRedeploy:false,
    programOrBeforeInjected:false,sourceDataOrGitWrites:false,wholeSceneAccepted:false};
  write(out,'verification.json',result);
  console.log(JSON.stringify({status:result.status,scriptCommit:expected,nodes:38,sourceEdges:40,actors:34,
    productionSectionNodes:120,localLibraryNodes:5619,beforeEqual,
    productionBeforeBg:program.before.bg_picture,productionBeforeModel:program.before.model,
    verificationSha256:witness(path.join(out,'verification.json')).sha256}));
}catch(error){
  write(out,'failure.json',{schema:'stella.p42.six-visual.production-readback-failure.v1',stage,
    error:{name:error.name,message:error.message,stack:error.stack,cause:error.cause?String(error.cause):null},
    expectedHead:expected,remoteAck:ack??null,inputs:inputs??null,http:records,
    exactLastResponse:latestResponse?{gzipFile:latestResponse.row.gzipFile,
      decodedResponseSha256:latestResponse.row.decodedResponseSha256,bodyComplete:latestResponse.row.bodyComplete}:null,
    originalFailureBodyRetainedInResponseGzip:latestResponse!==undefined,retries:0,sourceDataOrGitWrites:false});
  console.error(error.stack||String(error));process.exitCode=1;
}
