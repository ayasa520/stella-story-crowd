// One ordinary final-HEAD P30 document, observed from predecessor through
// the unchanged target's complete entry/typing/hold/exit and accepted boundary.
// QA input delays add no script Wait, clock/layer change, token or ready state.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,appendFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {createInterface} from 'node:readline';
import {setTimeout as delay} from 'node:timers/promises';
import {connect} from '../../stella-p30-firefox-20261120/bidi.mjs';
import {installRenderProbe} from '../../stella-p30-firefox-20261120/render-probe.mjs';
import {auditCurves} from './curve-audit.mjs';
import {runtimeGate} from './node-guards.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const {release:runtimeRelease,bindingBytes,binding,releaseSha256}=await runtimeGate(here,import.meta.url),budgets=binding.budgets;
const preparations=JSON.parse(await readFile(new URL('prepared/index.json',here),'utf8'));
const output=process.env.STELLA_PRIVATE_OUTPUT;assert.ok(output);
const sha=b=>createHash('sha256').update(b).digest('hex');
// Match the owner classifier independently against retained original facts.
// Hitches, cancellation and observation overhead are deliberately separate.
const fatalProductNames=new Set(['STORY_PLAYER_ERROR','STORY_NORMAL_CLOCK_LISTENER_ERROR','STORY_NORMAL_CLOCK_REPORT_ERROR',
    'STORY_FX_ERROR','STORY_BACKGROUND_ERROR','STORY_PICTURE_ERROR','STORY_BGM_LOAD_FAILED']);
function rejectOriginalProductErrors(){
  assert.deepEqual(active.productFatalErrors,[],'Original product fatal diagnostics reject this case');
  assert.equal(active.productFatalDropped,0,'Original product fatal collection overflow');
}
const save=async(folder,name,value)=>writeFile(resolve(folder,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const driver=await connect(process.argv[2]);
let target,active=null,stage='session',capabilities,ipcSequence=0,firstFailure=null,sessionRetired=false;
const pending=new Map(),reader=createInterface({input:process.stdin});
reader.on('line',line=>{try{const value=JSON.parse(line),job=pending.get(value.replyTo);if(job){pending.delete(value.replyTo);clearTimeout(job.timer);
  value.ok?job.resolve(value):job.reject(Error(value.error||'Supervisor IPC failure'));}}catch(error){if(active)active.errors.push(String(error));}});
function supervisor(type,caseId){return new Promise((resolve,reject)=>{
  const id=++ipcSequence,timer=setTimeout(()=>{pending.delete(id);reject(Error('Supervisor '+type+' timeout'));},20000);
  pending.set(id,{resolve,reject,timer});process.stdout.write('OWNER_IPC '+JSON.stringify({id,type,caseId})+'\n');
});}
async function evaluate(fn,arg){
  const reply=await driver.call('script.evaluate',{target,awaitPromise:true,
    expression:`(async()=>JSON.stringify(await (${fn})(${JSON.stringify(arg)})))()`});
  if(reply.type!=='success')throw Error(reply.exceptionDetails?.text||'Firefox evaluation failed');
  return reply.result.type==='undefined'?null:JSON.parse(reply.result.value);
}
async function state(){return evaluate(()=>window.reviewPrivateOwner?.state()||null);}
async function waitFor(fn,arg,timeout=45000){
  const end=Math.min(Date.now()+timeout,active.deadline);
  while(Date.now()<end){
    if(active.errors.length)throw Error(active.errors.at(-1));
    rejectOriginalProductErrors();
    const owner=await state();
    if(owner?.errors.length||owner?.traceDropped||owner?.mediaDropped||owner?.errorDropped)throw Error('Owner diagnostic error/drop; preserve original evidence');
    if(owner?.productFatalSeen||owner?.productFatalDropped||owner?.productFatalErrors.length)
      throw Error('Original product fatal diagnostic observed; preserve raw evidence and abort later cases');
    if(owner?.entered.some(id=>!active.plan.steps.some(s=>s.id===id)))throw Error('Natural route crossed declared boundary; retained without pause/cancel');
    const found=await evaluate(fn,arg);if(found)return found;
    for(const selector of ['#voiceContinue','#movieContinue']){
      const permission=await evaluate(selector=>{const e=document.querySelector(selector);return e&&!e.hidden&&!e.disabled&&e.checkVisibility();},selector);
      if(permission)await click(selector,null,null);
    }
    await delay(70);
  }
  throw Error('Bounded ordinary condition timed out: '+stage);
}
async function click(selector,node,phase){
  const point=await evaluate(({selector,node,phase})=>{
    if(node&&(document.body.dataset.node!==node||document.body.dataset.phase!==phase))throw Error('Normal control no longer belongs to expected ready node');
    const e=document.querySelector(selector);if(!e||e.disabled||!e.checkVisibility())return null;
    const r=e.getBoundingClientRect();return{x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)};
  },{selector,node,phase});assert.ok(point,selector);
  active.actions.push({selector,node,phase,before:await state()});
  await driver.call('input.performActions',{context:target.context,actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},
    actions:[{type:'pointerMove',origin:'viewport',...point,duration:0},{type:'pointerDown',button:0},{type:'pointerUp',button:0}]}]});
}
async function mark(name){const value=await evaluate(name=>window.reviewPrivateOwner.mark(name),name);active.marks.push(value);return value;}
async function checkpoint(label,step){
  const item=await evaluate(label=>window.reviewPrivateOwner.checkpoint(label),label);
  assert.ok(item.row,'Actual primary actor post-compose row required');assert.equal(item.row.node,step.id);assert.equal(item.row.model,step.expectedModel);
  assert.equal(item.row.primaryStoryActor.actualBacklinkVerified,true);assert.equal(item.row.normal.previewRate,1);
  assert.equal(item.row.actualProductFields.storyPlayerCurrentGeneration.value,null);
  assert.equal(item.row.actualProductFields.animatorGeneration.value,null);
  assert.equal(item.tapDropped,0);assert.equal(item.tapOwnerDropped,0);assert.deepEqual(item.tapErrors,[]);
  active.checkpoints.push(item);return item;
}
async function surface(){
  return evaluate(()=>{
    const actor=document.getElementById('actor'),card=document.getElementById('cardMotion'),panel=document.getElementById('subtitles');
    return {node:document.body.dataset.node,phase:document.body.dataset.phase,wallMilliseconds:performance.now(),
      card:{opacity:Number(getComputedStyle(card).opacity),visible:card.checkVisibility({opacityProperty:true,visibilityProperty:true})},
      panel:{opacity:Number(getComputedStyle(panel).opacity),translate:getComputedStyle(panel).translate,
        visible:panel.checkVisibility({opacityProperty:true,visibilityProperty:true})},
      actorVisible:actor.checkVisibility({opacityProperty:true,visibilityProperty:true}),
      pictureHidden:document.getElementById('picture').hidden,text:document.getElementById('accessibleText').textContent,
      render:window.reviewRenderProbe.snapshot()};
  });
}
function verifySurface(value,step){
  assert.equal(value.node,step.id);assert.equal(value.pictureHidden,true);
  assert.equal(value.render.losses.filter(e=>e.canvas==='actor'||e.attached).length,0,
    'Actor/attached-context loss history survives restoration');
  if(step.expectedModel)assert.equal(value.actorVisible,true);
}
async function visibleTarget(step){
  const observed=await waitFor(({id,model})=>{
    const s=window.reviewPrivateOwner.state(),actor=document.getElementById('actor'),card=document.getElementById('cardMotion');
    const gl=window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor');
    return s.node===id&&s.latest.commits[id]?.detail.model===model&&
      s.latest.displays[id]?.kind==='actor'&&s.latest.displays[id]?.model===model&&
      Number(getComputedStyle(card).opacity)>0&&card.checkVisibility({opacityProperty:true,visibilityProperty:true})&&
      actor.checkVisibility({opacityProperty:true,visibilityProperty:true})&&gl?.attached&&!gl.lost&&gl.draws>0&&
      {draws:gl.draws,phase:s.phase,normal:s.normal,wallMilliseconds:performance.now()};
  },{id:step.id,model:step.expectedModel});
  const visual=await surface();verifySurface(visual,step);
  const point=await checkpoint('4-first-observed-visible',step);
  // This sampled marker is not the exact first paint or native phase zero.
  // The X recording predates program load and retains the earlier fade. Never
  // reset animator time/layers to make this observational anchor look native.
  return {observed,visual,point};
}
async function readySurface(step,configuration){
  await waitFor(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready',step.id);
  const group=step.native.msg_character?configuration.player.panels.dialogue:configuration.player.panels.narration;
  const profile=configuration.transitions.panel_entries?.[group];
  const owned=await waitFor(({id,model,group,profile,command})=>{
    const s=window.reviewPrivateOwner.state(),card=document.getElementById('cardMotion'),panel=document.getElementById('subtitles');
    const start=s.latest.panelStart[id]?.detail,complete=s.latest.panelComplete[id]?.detail;
    const panelOwned=!profile||(start&&complete&&start.node===id&&complete.node===id&&
      start.group===group&&complete.group===group&&start.token===complete.token&&!s.latest.panelCancelled[group+':'+start.token]);
    const display=s.latest.displays[id],commit=s.latest.commits[id]?.detail;
    const gl=window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor');
    const foreground=model?display?.kind==='actor'&&display.model===model&&commit?.model===model&&commit.command===command&&
      gl?.attached&&!gl.lost&&document.getElementById('actor').checkVisibility({opacityProperty:true,visibilityProperty:true}):
      display?.kind==='empty';
    return s.node===id&&s.phase==='ready'&&foreground&&panelOwned&&Number(getComputedStyle(card).opacity)>=.99&&
      Number(getComputedStyle(panel).opacity)>=.99&&getComputedStyle(panel).translate==='none'&&
      panel.checkVisibility({opacityProperty:true,visibilityProperty:true})&&
      {start:start||null,complete:complete||null,group,profile:profile||null,draws:model?gl.draws:null,display,commit:commit||null};
  },{id:step.id,model:step.expectedModel,group,profile:profile||null,
    command:[step.parsedMotion.body,step.parsedMotion.face,...step.parsedMotion.extras].filter(Boolean).join(',')});
  if(step.expectedModel)await waitFor(draws=>{
    const gl=window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor');return gl?.attached&&!gl.lost&&gl.draws>draws+3;
  },owned.draws);
  const visual=await surface();verifySurface(visual,step);assert.equal(visual.phase,'ready');
  assert.ok(visual.text.includes(step.native.msg_text));
  const value={scenario:step.scenario,owned,visual};active.surfaces.push(value);return value;
}
async function narrationObservation(step,configuration){
  assert.equal(step.expectedModel,'');
  const ready=await readySurface(step,configuration),began=await mark('3-natural-ready-actorless');
  await waitFor(({node,target})=>{const s=window.reviewPrivateOwner.state();
    return s.node===node&&s.phase==='ready'&&s.normal.gameSeconds>=target;
  },{node:step.id,target:began.normal.gameSeconds+active.plan.observation.narrationNormalSeconds});
  const ended=await mark('3-pre31-actorless-boundary'),visual=await surface();verifySurface(visual,step);
  return {scenario:3,ready,began,ended,visual,actorCheckpointRequired:false,reviewNormalHoldOnly:true,scriptWaitAdded:false};
}
async function targetObservation(step,configuration){
  assert.equal(step.native.motion,'');assert.deepEqual(step.parsedMotion,{body:'',face:'',extras:[]});
  const visible=await visibleTarget(step),ready=await readySurface(step,configuration);
  const readyPoint=await checkpoint('4-first-natural-ready',step);
  assert.equal(readyPoint.row.observerIdentity.animator,visible.point.row.observerIdentity.animator);
  const required=Math.max(visible.point.row.actorSeconds+active.plan.observation.targetVisibleActorSeconds,
    readyPoint.row.actorSeconds+active.plan.observation.targetReadyActorSeconds);
  let current=readyPoint;const observations=[];
  for(let attempt=0;attempt<active.plan.observation.maximumActorHoldChecks;attempt++){
    // Normal time schedules the next bounded read only. The actual Actor
    // checkpoint, with the same animator/model identity, alone satisfies8/2.
    // A stopped/reset/slow actor is retained rather than repaired by the test.
    const remaining=Math.max(0,required-current.row.actorSeconds);
    const reached=await waitFor(({node,target})=>{const s=window.reviewPrivateOwner.state();
      return s.node===node&&s.phase==='ready'&&s.normal.gameSeconds>=target&&s.normal;
    },{node:step.id,target:current.row.normal.gameSeconds+remaining});
    await waitFor(({node,frame})=>{const s=window.reviewPrivateOwner.state();
      return s.node===node&&s.phase==='ready'&&s.normal.frame>frame;
    },{node:step.id,frame:reached.frame});
    current=await checkpoint('4-hold-observation-'+(attempt+1),step);observations.push(current);
    assert.equal(current.row.observerIdentity.animator,visible.point.row.observerIdentity.animator);
    if(current.row.actorSeconds>=required){
      const visual=await surface();verifySurface(visual,step);assert.equal(visual.phase,'ready');
      return {scenario:4,visible,ready,readyPoint,ended:current,observations,visual,
        measuredActorSecondsSinceVisible:current.row.actorSeconds-visible.point.row.actorSeconds,
        measuredActorSecondsSinceReady:current.row.actorSeconds-readyPoint.row.actorSeconds,
        minimumActorSecondsSinceVisible:8,minimumActorSecondsSinceReady:2,
        noExpectedTokenWeightLoopOrBlendState:true,sourcePhaseAccepted:false};
    }
  }
  throw Error('Actual Actor-time minima not observed within bounded checkpoints; preserve unchanged capture');
}
function verifyOwner(report,plan){
  assert.deepEqual(report.productFatalErrors,[]);assert.equal(report.productFatalSeen,0);assert.equal(report.productFatalDropped,0);
  assert.ok(!report.trace.some(r=>r.method==='error'||fatalProductNames.has(r.name)),
    'Original error/fatal events cannot pass zero-error verification');
  assert.deepEqual(report.errors,[]);assert.equal(report.traceDropped,0);assert.equal(report.mediaDropped,0);assert.equal(report.errorDropped,0);
  assert.deepEqual(report.tap.errors,[]);assert.equal(report.tap.dropped,0);assert.equal(report.tap.ownerDropped,0);
  assert.equal(report.restoration.renderRestored,true);assert.equal(report.restoration.consoleRestored,true);
  const raw=new Map(report.trace.map(r=>[r.sequence,r])),forwarded=new Map(report.tap.ownerEvents.map(e=>[e.sourceEventSequence,e]));
  for(const event of report.tap.ownerEvents){
    const original=raw.get(event.sourceEventSequence);assert.ok(original?.forwarded);
    assert.equal(original.caseId,plan.id);assert.equal(original.runLabel,report.runLabel);assert.equal(original.name,event.name);
    assert.equal(original.originalCallEntryMilliseconds,event.observedWallMilliseconds);
    assert.deepEqual(JSON.parse(original.rawArguments[1]),event.actualEventDetail);
  }
  function layers(values){for(const layer of values){
    assert.ok(!layer.depthLimit,'Actual layer observation cannot be silently truncated');
    if(layer.blend)layers([layer.blend.source]);
  }}
  for(const row of report.tap.rows){
    assert.equal(row.caseName,plan.id);assert.equal(row.ownerRunLabel,report.runLabel);
    assert.equal(row.observerIdentity.namespace,'artifact-local-object-identity-not-native-generation');
    assert.equal(row.actualProductFields.storyPlayerCurrentGeneration.value,null);assert.equal(row.actualProductFields.animatorGeneration.value,null);
    assert.equal(row.normal.previewRate,1);assert.equal(row.primaryStoryActor.actualBacklinkVerified,true);layers(row.layers);
    if(row.externalOwnerProductEvent){assert.ok(raw.has(row.externalOwnerProductEvent.sourceEventSequence));
      assert.deepEqual(row.externalOwnerProductEvent,forwarded.get(row.externalOwnerProductEvent.sourceEventSequence));}
  }
  // Loading can still belong to the previous actor. Preserve it as observed;
  // only the explicit owned-model checkpoints are assigned to tshirt/Felt.
  assert.ok(report.trustedInputs.every(i=>i.isTrusted));
  const enters=report.trace.filter(r=>r.name==='STORY_PLAYER_ENTER').map(r=>r.rawArguments[1]);
  assert.deepEqual(enters,plan.steps.map(s=>s.id));
  const transitions=report.trace.filter(r=>r.name==='STORY_PLAYER_TRANSITION').map(r=>JSON.parse(r.rawArguments[1]));
  assert.deepEqual(transitions.map(e=>e.edge),plan.links.map(e=>e.id));
  for(const [index,event]of transitions.entries()){
    assert.equal(event.target,plan.links[index].target);assert.deepEqual(event.native,plan.links[index].native_transition);
  }
  const advances=report.trustedInputs.filter(i=>i.button==='advance');
  assert.deepEqual(advances.map(i=>i.node),plan.steps.slice(0,-1).map(s=>s.id));assert.ok(advances.every(i=>i.phase==='ready'));
  assert.ok(!advances.some(i=>i.node===plan.stop.node));assert.ok(!transitions.some(e=>e.edge===plan.stop.forbiddenEdge));
}
async function exportOwner(folder){
  assert.ok(!active.ownerExportAttempted,'Owner export is not retried');active.ownerExportAttempted=true;
  const started=Date.now(),report=await evaluate(()=>window.reviewPrivateOwner.finish());
  const raw=JSON.stringify(report),bytes=Buffer.byteLength(raw),compressed=gzipSync(raw);
  if(bytes>budgets.tapRawBytesPerCase||compressed.length>budgets.tapGzipBytesPerCase){
    await writeFile(resolve(folder,'over-budget-owner-prefix.txt'),raw.slice(0,64000),{flag:'wx'});
    await save(folder,'owner-over-budget.json',{originalBytes:bytes,originalSha256:sha(raw),gzipBytes:compressed.length,truncated:true});
    throw Error('Owner archive budget exceeded; full-coverage claim rejected');
  }
  await writeFile(resolve(folder,'owner-original-trace.json.gz'),compressed,{flag:'wx'});
  await save(folder,'owner-archive.json',{rawBytes:bytes,rawSha256:sha(raw),gzipBytes:compressed.length,gzipSha256:sha(compressed),
    exportRoundTripWallMilliseconds:Date.now()-started,parameterPhase:report.tap.rows[0]?.observedAt,
    traceDropped:report.traceDropped,tapDropped:report.tap.dropped,ownerDropped:report.tap.ownerDropped,
    consoleOverhead:report.consoleOverhead,exportCopy:report.exportCopy,checkpointCopies:report.checkpoints.map(c=>({label:c.label,milliseconds:c.copyDurationMilliseconds}))});
  return report;
}
function retainFirstFailure(error){
  if(!firstFailure)firstFailure={stage,error:String(error),stack:error?.stack||'',caseId:active?.plan.id||null};
}
async function failureState(){
  try{return {owner:await state(),surface:await surface()};}
  catch(error){return {observationFailure:String(error),stack:error.stack};}
}
try{
  ({capabilities}=await driver.call('session.new',{capabilities:{}}));
  const {contexts}=await driver.call('browsingContext.getTree');assert.equal(contexts.length,1,'One owned browser context required');
  target={context:contexts[0].context};
  driver.events((event,value)=>{
    if(!active)return;
    if(event==='log.entryAdded'){
      const line=value.text||'',name=line.split(/\s+/,1)[0];
      // Retain original severity/handled fatal names independently of archive
      // limits. A console.info Normal listener failure is still an original
      // fatal fact; hitches/cancellations are not promoted by their prefix.
      if(value.level==='error'||value.type==='javascript'||fatalProductNames.has(name)){
        if(active.productFatalErrors.length<32)active.productFatalErrors.push({name,level:value.level,
          originalTimestamp:value.timestamp,source:value.source,rawEntry:value});
        else active.productFatalDropped++;
      }
      const entry={event,source:value.source,timestamp:value.timestamp,line,rawEntry:value,caseActiveAtReceipt:active.plan.id};
      const bytes=Buffer.byteLength(JSON.stringify(entry));
      if(value.type==='javascript')active.errors.push(line);
      if(active.bidi.length>=budgets.consoleRowsPerCase||active.bidiBytes+bytes>budgets.consoleBytesPerCase){
        active.errors.push('Original raw BiDi archive cap; coverage rejected');active.bidiDropped++;return;}
      active.bidiBytes+=bytes;active.bidi.push(entry);
    }
    if(event==='network.responseCompleted'){
      if(active.http.length>=budgets.httpRowsPerCase){active.errors.push('HTTP trace cap');return;}
      const response=value.response,url=new URL(response.url);active.http.push({url:url.href,status:response.status,mimeType:response.mimeType});
      if(url.origin===origin&&response.status>=400&&url.pathname!=='/favicon.ico')active.errors.push('HTTP '+response.status+' '+url.href);
    }
  });
  await driver.call('session.subscribe',{events:['log.entryAdded','network.responseCompleted'],contexts:[target.context]});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:installRenderProbe.toString()});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:(()=>{
    window.reviewReady=false;window.addEventListener('message',event=>{
      if(event.source===window&&event.origin===location.origin&&event.data?.type==='stella-player-ready')window.reviewReady=true;});
  }).toString()});
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:{width:500,height:1000},devicePixelRatio:1});
  assert.equal(binding.plans.length,1);
  for(const plan of binding.plans){
    const folder=resolve(output,plan.id);await mkdir(folder);
    active={plan,folder,deadline:Date.now()+budgets.caseWallSeconds*1000,errors:[],bidi:[],bidiBytes:0,bidiDropped:0,
      http:[],actions:[],marks:[],checkpoints:[],holds:[],surfaces:[],productFatalErrors:[],productFatalDropped:0};
    let recording=false,exported=false,captureEndRequested=false;
    try{
      stage=plan.id+':fresh-document';
      await driver.call('browsingContext.navigate',{context:target.context,url:origin+'/player/player.html?assetRevision='+binding.finalDataHead,wait:'interactive'});
      await waitFor(()=>window.reviewReady===true);
      assert.equal(await evaluate(()=>document.getElementById('auto').getAttribute('aria-pressed')),'false');
      assert.equal(await evaluate(()=>document.getElementById('language').value),'zh');
      const viewport=await evaluate(()=>({innerWidth,innerHeight,outerWidth,outerHeight,screenX,screenY,timeOrigin:performance.timeOrigin}));
      assert.equal(viewport.innerWidth,500);assert.equal(viewport.innerHeight,1000);await save(folder,'viewport.json',viewport);
      const runLabel=process.env.STELLA_PRIVATE_ATTEMPT+':'+plan.id+':'+viewport.timeOrigin;
      const installed=await evaluate(async args=>(await import('/__private/owner-events.mjs')).installOwner(args),{
        rootRelease:{rootConfirmed:runtimeRelease.rootConfirmed,bindingSha256:sha(bindingBytes),observerSha256:binding.tap.sha256,releaseSha256},
        caseId:plan.id,runLabel,nodeIds:plan.steps.map(s=>s.id),modelIds:['subaru_tshirt01','felt01'],budgets});
      assert.equal(installed.exactlyOneTap,true);
      const configuration=await evaluate(async()=>({
        player:await(await fetch('/player/player_config.json')).json(),
        transitions:await(await fetch('/player-assets/transitions.json')).json()}));
      const expected=preparations.receipts.find(r=>r.caseId===plan.id);assert.ok(expected);
      assert.deepEqual(expected.request,{id:plan.start,baseSha:binding.finalDataHead,choices:{}});
      stage=plan.id+':normal-prepare';
      const response=await evaluate(async({request,expectedSha})=>{
        const reply=await fetch('/api/player/prepare',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)});
        const raw=await reply.text(),http={status:reply.status,headers:Object.fromEntries(reply.headers)};
        if(!reply.ok)return {...http,raw,stored:false};
        let program;try{program=JSON.parse(raw);}catch(error){return {...http,raw,parseError:String(error),stored:false};}
        const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(program)));
        const programSha256=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
        if(programSha256===expectedSha)window.reviewPrivatePreparedProgram=program;
        return {...http,raw,programSha256,stored:programSha256===expectedSha};
      },{request:expected.request,expectedSha:expected.programSha256});
      await writeFile(resolve(folder,'normal-http-program.json.gz'),gzipSync(response.raw),{flag:'wx'});
      await save(folder,'normal-http-receipt.json',{...response,raw:undefined});
      if(response.status===422){
        const diagnostic=await evaluate(async request=>{
          const reply=await fetch('/api/resolve',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)});
          return {status:reply.status,headers:Object.fromEntries(reply.headers),raw:await reply.text()};
        },expected.request);
        await writeFile(resolve(folder,'normal-resolve.json.gz'),gzipSync(diagnostic.raw),{flag:'wx'});
        await save(folder,'normal-resolve-receipt.json',{...diagnostic,raw:undefined});
      }
      assert.equal(response.status,200);assert.equal(response.stored,true);assert.equal(response.programSha256,expected.programSha256);
      const program=JSON.parse(response.raw);
      assert.equal(program.headSha,binding.finalDataHead);assert.equal(program.start,plan.start);
      assert.equal(program.nodes.length,binding.allLibraryNodes);assert.deepEqual(program.before,expected.before);
      assert.equal(program.nodes.filter(n=>n.scene_id==='scene:10450054').length,52);
      assert.deepEqual((await state()).entered,[],'No product entry before continuous recording begins');
      await supervisor('capture-start',plan.id);recording=true;
      await mark('before-complete-ordinary-program-load');
      await evaluate(()=>{const program=window.reviewPrivatePreparedProgram;if(!program)throw Error('No untouched full ordinary program');
        window.postMessage({type:'stella-player-load',program},location.origin);delete window.reviewPrivatePreparedProgram;return true;});
      for(const [index,step]of plan.steps.entries()){
        stage=plan.id+':node-'+step.scenario;
        await waitFor(id=>window.reviewPrivateOwner.state().entered.includes(id),step.id);
        if(step.scenario===3)active.holds.push(await narrationObservation(step,configuration));
        else if(step.target)active.holds.push(await targetObservation(step,configuration));
        else{
          const ready=await readySurface(step,configuration),point=await checkpoint('5-own-natural-ready-boundary',step);
          active.holds.push({scenario:5,ready,point,FeltPerformanceReaccepted:false,extraHoldRequired:false});
        }
        if(index===plan.steps.length-1)break;
        await mark('normal-advance-from-'+step.scenario);await click('#advance',step.id,'ready');
      }
      const finalState=await state();assert.equal(finalState.node,plan.stop.node);assert.equal(finalState.phase,'ready');
      const finalSurface=await surface();verifySurface(finalSurface,plan.steps.at(-1));
      await mark('ordinary-observation-complete-no51');
      const report=await exportOwner(folder);exported=true;verifyOwner(report,plan);
      // Keep the held observation separate from the outer BiDi context target.
      // A block-scoped `target` here would shadow earlier target.context reads
      // throughout this try block, including navigation before initialization.
      const targetHold=active.holds.find(h=>h.scenario===4);
      await save(folder,'actual-empty-motion-baseline.json',{nativeMotion:'',derivedMotion:{body:'',face:'',extras:[]},
        visible:targetHold.visible,ready:targetHold.readyPoint,ended:targetHold.ended,observations:targetHold.observations,
        tokensSelectedByHelper:false,layersOrWeightsMutatedByHelper:false,
        bodyWinner:null,faceWinner:null,motionAccepted:false,sourcePhaseAccepted:false});
      await save(folder,'actual-decoded-curve-proof.json',await auditCurves(binding,report,plan));
      assert.deepEqual(active.errors,[]);rejectOriginalProductErrors();
      await save(folder,'result.json',{status:'ordinary-unchanged-observation-pending-source-review',
        motionAccepted:false,sourcePhaseAccepted:false,requiresTerminalAcceptanceReceipt:true,
        plan,prepared:expected,finalState,finalSurface,holds:active.holds,surfaces:active.surfaces,marks:active.marks,actions:active.actions,
        bidi:active.bidi,http:active.http,browser:capabilities,runLabel,rawGenerationLinksVerified:true,currentStoryPlayerGeneration:null,
        ownerRows:report.trace.length,tapRows:report.tap.rows.length,tapClips:report.tap.clips.length,
        bidiBytes:active.bidiBytes,bidiDropped:active.bidiDropped,
        productFatalErrors:active.productFatalErrors,productFatalDropped:active.productFatalDropped,
        normalHitches:report.trace.filter(r=>r.name==='STORY_NORMAL_FRAME_HITCH').length});
      captureEndRequested=true;await supervisor('capture-end',plan.id);recording=false;
      // A handled original failure received during recorder/guard shutdown
      // still prevents this case from falling through into the next document.
      assert.deepEqual(active.errors,[]);rejectOriginalProductErrors();
      console.error('CASE_COMPLETE '+plan.id);
    }catch(error){
      retainFirstFailure(error);
      if(!exported&&!active.ownerExportAttempted){try{await exportOwner(folder);}catch(exportError){active.errors.push('Owner export: '+String(exportError));}}
      await save(folder,'failure.json',{firstFailure,stage,error:String(error),stack:error.stack,plan,state:await failureState(),holds:active.holds,surfaces:active.surfaces,marks:active.marks,
        checkpoints:active.checkpoints,actions:active.actions,bidi:active.bidi,bidiBytes:active.bidiBytes,bidiDropped:active.bidiDropped,
        http:active.http,errors:active.errors,productFatalErrors:active.productFatalErrors,
        productFatalDropped:active.productFatalDropped,noAutomaticRetry:true});
      if(recording&&!captureEndRequested){captureEndRequested=true;await supervisor('capture-end',plan.id).catch(e=>console.error(String(e)));}
      throw error; // A failed case never falls through into another case.
    }
  }
}catch(error){
  retainFirstFailure(error);console.error(JSON.stringify({firstFailure,noRetry:true}));process.exitCode=1;
}finally{
  reader.close();process.stdin.pause();
  try{await driver.call('session.end');sessionRetired=true;}
  catch(error){retainFirstFailure(error);process.exitCode=1;}
  finally{try{driver.close();}catch(error){retainFirstFailure(error);process.exitCode=1;}}
}
// Capture-end/guard IPC and session end have completed. Recheck all retained
// late original fatal facts after the final await. A BiDi session end is not
// browser OS exit proof; independent supervisor/root closure remains required.
try{
  if(active){assert.deepEqual(active.errors,[]);rejectOriginalProductErrors();}
  if(firstFailure)throw Error('An earlier original failure is retained');
  assert.equal(sessionRetired,true);
  await save(output,'terminal-acceptance.json',{accepted:true,sessionRetired,
    originalFatalFactsEmpty:true,requiresRootIndependentOsPortsGuards:true,caseId:binding.plans[0].id});
  if(active){assert.deepEqual(active.errors,[]);rejectOriginalProductErrors();}
  console.log('ORDINARY_P30_CASE_COMPLETE_PENDING_INDEPENDENT_SOURCE_REVIEW');
}catch(error){
  retainFirstFailure(error);process.exitCode=1;
  await save(output,'terminal-failure.json',{firstFailure,sessionRetired,errors:active?.errors||[],
    productFatalErrors:active?.productFatalErrors||[],productFatalDropped:active?.productFatalDropped||0,
    bidi:active?.bidi||[],noRetry:true}).catch(writeError=>console.error('TERMINAL_RECORD_FAILURE '+String(writeError)));
  console.error(JSON.stringify({firstFailure,sessionRetired,noRetry:true}));
}
