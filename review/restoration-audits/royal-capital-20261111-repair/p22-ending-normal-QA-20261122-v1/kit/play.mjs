// Ordinary saved-player input only. The complete program is returned by the
// real API and passed unchanged to its existing load protocol. Passive probes
// observe display ownership and GL submissions; they supply no actor, route,
// initial state, background, animation clock or replacement renderer.
import assert from 'node:assert/strict';
import {readFile,writeFile,appendFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {verifyInputs} from './guards.mjs';
import {connect} from '../../stella-p30-firefox-20261120/bidi.mjs';
import {installRenderProbe} from '../../stella-p30-firefox-20261120/render-probe.mjs';
import {installEndingObserver} from '../episode5-silent54-saved-runtime-v2/ending-observer.mjs';
import {installCaptureReadiness} from '../episode5-silent54-saved-runtime-v2/capture-readiness.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const output=process.env.STELLA_REVIEW_OUTPUT;assert.ok(output);
const load=async name=>JSON.parse(await readFile(new URL(name,here),'utf8'));
const plan=await load('capture-plan.json'),binding=await load('input-binding.json');
const offlinePrepare=await load('normal-prepare-receipt.json');
assert.equal(offlinePrepare.allStatus200,true);
let route,activeCase,traceStart=0;
const driver=await connect(process.argv[2]);
const traces=[],records=[],errors=[],http=[],played=[],captures=[],actions=[],eventWrites=[];
const rawConsole=[],fatalFacts=[],hitches=[],cancellations=[],diagnosticFailures=[];
const fatalProductNames=new Set(['STORY_PLAYER_ERROR','STORY_NORMAL_CLOCK_LISTENER_ERROR','STORY_NORMAL_CLOCK_REPORT_ERROR',
  'STORY_FX_ERROR','STORY_BACKGROUND_ERROR','STORY_PICTURE_ERROR','STORY_BGM_LOAD_FAILED']);
// P22 has no eligible same-foreground ordinary Close edge. Validate the
// two exclusions against real input/transition/entry events below; never use
// an empty witness list to claim the earlier381/71 positive scope was covered.
assert.deepEqual(plan.closeCoverage.positiveEdges,[]);
assert.equal(plan.closeCoverage.expectedPositiveWitnesses,0);
const positiveCloseTargets=new Map(plan.closeCoverage.positiveEdges);
let target,stage='connect',capabilities,prepared,panelConfig,totalCaptureBytes=0;
let firstFailure=null,pendingResult=null,lastKnownDocumentIdentity=null,sessionRetired=false;
const failureExports=[],savedFailureNames=new Set();
function rejectFatalDiagnostics(boundary){
  assert.deepEqual(fatalFacts,[],'Original fatal diagnostics at '+boundary);
  assert.deepEqual(errors,[],'Original exceptions/HTTP failures at '+boundary);
  assert.deepEqual(diagnosticFailures,[],'Diagnostic write/export failures at '+boundary);
}
function queueDiagnosticWrite(name,row){
  // BiDi has already received the original invocation. This handler neither
  // wraps nor rethrows into the product console or its Normal-clock callback.
  const job=appendFile(resolve(output,name),JSON.stringify(row)+'\n').catch(error=>{
    diagnosticFailures.push({operation:'append',name,error:String(error),stack:error.stack});
  });
  eventWrites.push(job);
}
async function flushDiagnosticWrites(){
  let index=0;
  for(let round=0;round<32;round++){
    const batch=eventWrites.slice(index);if(!batch.length)return;
    index=eventWrites.length;await Promise.allSettled(batch);
  }
  throw Error('Diagnostic writes did not quiesce within the bounded flush');
}
function retainFirstFailure(error,boundary){
  if(!firstFailure)firstFailure={boundary,stage,requestedCase:activeCase?.id||null,
    error:String(error),stack:error?.stack||'',observedEpochMilliseconds:Date.now()};
}
const save=async(name,value)=>writeFile(resolve(output,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
async function evaluate(fn,arg){
  const reply=await driver.call('script.evaluate',{target,awaitPromise:true,
    expression:`(async()=>JSON.stringify(await (${fn})(${JSON.stringify(arg)})))()`});
  if(reply.type!=='success')throw Error(reply.exceptionDetails?.text||'Firefox evaluation failed');
  return reply.result.type==='undefined'?null:JSON.parse(reply.result.value);
}
async function snapshot(){return evaluate(()=>{
  const geometry=id=>{const e=document.getElementById(id);return e.dataset.backgroundGeometry?JSON.parse(e.dataset.backgroundGeometry):null;};
  const panel=document.getElementById('subtitles'),actor=document.getElementById('actor'),quote=document.getElementById('choiceCanvas');
  return {epochMilliseconds:Date.now(),performanceMilliseconds:performance.now(),body:{...document.body.dataset},
    status:document.getElementById('status').textContent,accessibleText:document.getElementById('accessibleText').textContent,
    background:geometry('card'),backdrop:geometry('backdrop'),
    choiceGeometry:document.getElementById('viewport').dataset.choiceGeometry||null,
    actor:{visible:actor.checkVisibility({opacityProperty:true,visibilityProperty:true}),width:actor.width,height:actor.height},
    pictureHidden:document.getElementById('picture').hidden,
    picture:{src:document.getElementById('picture').currentSrc,width:document.getElementById('picture').naturalWidth,
      height:document.getElementById('picture').naturalHeight,visible:document.getElementById('picture').checkVisibility({opacityProperty:true,visibilityProperty:true})},
    card:{opacity:getComputedStyle(document.getElementById('cardMotion')).opacity},
    panel:{hidden:panel.hidden,opacity:getComputedStyle(panel).opacity,translate:getComputedStyle(panel).translate},
    choiceSurface:{hidden:quote.hidden,visible:quote.checkVisibility({opacityProperty:true,visibilityProperty:true}),
      opacity:getComputedStyle(quote).opacity,width:quote.width,height:quote.height},
    choices:[...document.querySelectorAll('#choices button')].map(e=>({edge:e.dataset.edge,text:e.textContent,
      disabled:e.disabled,selected:e.getAttribute('aria-pressed')})),advanceDisabled:document.getElementById('advance').disabled,
    render:window.reviewRenderProbe.snapshot(),observer:window.reviewEndingObserver.snapshot(),
    movie:{hidden:document.getElementById('movie').hidden,visible:document.getElementById('movie').checkVisibility({opacityProperty:true,visibilityProperty:true}),
      currentTime:document.getElementById('movie').currentTime,duration:Number.isFinite(document.getElementById('movie').duration)?document.getElementById('movie').duration:null,
      ended:document.getElementById('movie').ended,seeking:document.getElementById('movie').seeking,readyState:document.getElementById('movie').readyState,
      playbackRate:document.getElementById('movie').playbackRate,presentation:document.getElementById('movie').dataset.moviePresentation,
      fit:getComputedStyle(document.getElementById('movie')).objectFit,resource:document.getElementById('movie').currentSrc},
    titleLabel:document.querySelector('#storyFlow .native-title-content')?.getAttribute('aria-label')||''};
});}
async function click(selector){
  rejectFatalDiagnostics('before ordinary input');
  const point=await evaluate(selector=>{
    const e=document.querySelector(selector);if(!e||e.disabled||!e.checkVisibility())return null;
    e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
    return {x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)};
  },selector);assert.ok(point,'Visible enabled ordinary control '+selector);
  actions.push({selector,before:await snapshot()});
  await driver.call('input.performActions',{context:target.context,actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},
    actions:[{type:'pointerMove',origin:'viewport',...point,duration:0},{type:'pointerDown',button:0},{type:'pointerUp',button:0}]}]});
  actions.at(-1).afterEpochMilliseconds=Date.now();
}
async function waitFor(fn,arg,timeout=45000){
  const end=Date.now()+timeout;
  while(Date.now()<end){
    rejectFatalDiagnostics('condition poll');
    const value=await evaluate(fn,arg);if(value)return value;
    for(const selector of ['#movieContinue','#voiceContinue']){
      const blocked=await evaluate(selector=>{const e=document.querySelector(selector);return e&&!e.hidden&&!e.disabled&&e.checkVisibility();},selector);
      if(blocked)await click(selector);
    }
    await delay(70);
  }
  throw Error('Ordinary player condition timed out at '+stage);
}
function parsed(prefix){return traces.slice(traceStart).filter(line=>line.startsWith(prefix)).map(line=>JSON.parse(line.slice(prefix.length)));}
async function waitTrace(test,timeout=15000){
  const end=Date.now()+timeout;
  while(Date.now()<end){rejectFatalDiagnostics('event poll');const value=test();if(value)return value;await delay(50);}
  throw Error('Actual player event timed out at '+stage);
}
async function panelReady(step,node){
  const group=!node.speaker?panelConfig.player.panels.narration:node.character_image?panelConfig.player.panels.picture:panelConfig.player.panels.dialogue;
  const profile=panelConfig.transitions.panel_entries?.[group];
  if(!profile){assert.equal(parsed('STORY_PANEL_IN_START ').filter(e=>e.node===step.id).length,0);return {group,profile:null};}
  // Match the owning node/group/token rather than treating ENTER, ready phase
  // or an arbitrary elapsed delay as evidence that its panel became visible.
  const owner=await waitTrace(()=>parsed('STORY_PANEL_IN_START ').filter(e=>e.node===step.id).at(-1));
  assert.equal(owner.group,group);
  const complete=await waitTrace(()=>{
    assert.ok(!parsed('STORY_PANEL_IN_CANCELLED ').some(e=>e.group===group&&e.token===owner.token),'Owned panel cancelled');
    return parsed('STORY_PANEL_IN_COMPLETE ').find(e=>e.node===step.id&&e.group===group&&e.token===owner.token);
  });
  return {group,profile,owner,complete};
}
async function actorReady(step){
  assert.equal(traces.filter(e=>e.startsWith('STORY_DISPLAY_COMMIT '+step.id+' ')).at(-1),
    'STORY_DISPLAY_COMMIT '+step.id+' actor '+step.expectedModel);
  const before=await evaluate(()=>window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor'));
  assert.ok(before?.attached&&!before.lost);
  // Positive new draw submissions belong to the attached actor canvas. A
  // stale Subaru screenshot, an ENTER event or a scratch GL context cannot
  // satisfy Rom's gate. Actual pixels are reviewed independently after exit.
  return waitFor(draws=>{
    const e=window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor');
    return e?.attached&&!e.lost&&e.draws>draws+3&&document.getElementById('actor')
      .checkVisibility({opacityProperty:true,visibilityProperty:true})&&e;
  },before.draws,10000);
}

function assertVisualSurfaces(state,step){
  // Loss history survives restoration. Current isContextLost() alone cannot
  // certify a previously lost attached actor context. CGs retain independent
  // picture admission and never acquire an actor/draw requirement.
  assert.equal(state.render.losses.filter(e=>e.canvas==='actor'||e.attached).length,0);
  if(!step.native.character_image)assert.equal(state.pictureHidden,true,'No stale picture on a non-CG node');
  else {assert.equal(state.pictureHidden,false);assert.equal(state.picture.visible,true);}
  if(step.expectedModel)assert.equal(state.actor.visible,true);
  if(step.choice)assert.equal(state.choiceSurface.visible,true,'Selected quote canvas is visible');
}
function assertMovieMiddle(state,step,metadata){
  assert.equal(state.body.node,step.id);assert.equal(state.body.phase,'movie');
  assert.equal(state.movie.hidden,false);assert.equal(state.movie.visible,true);
  assert.equal(state.movie.presentation,'door');assert.equal(state.movie.fit,metadata.fit);
  assert.equal(new URL(state.movie.resource).pathname,'/movie/'+encodeURIComponent(metadata.resource));
  assert.equal(state.movie.ended,false);assert.equal(state.movie.seeking,false);
  assert.equal(state.movie.playbackRate,1);assert.ok(state.movie.readyState>=2);
  assert.ok(Number.isFinite(state.movie.duration)&&state.movie.duration>0);
  assert.ok(state.movie.currentTime>=state.movie.duration/3&&state.movie.currentTime<state.movie.duration*.8,
    'The original single JPEG stays within the declared natural middle window');
  assert.ok(Number(state.card.opacity)>=.99);
  const display=traces.slice(traceStart).filter(e=>e.startsWith('STORY_DISPLAY_COMMIT '+step.id+' ')).at(-1);
  assert.ok(display?.startsWith('STORY_DISPLAY_COMMIT '+step.id+' movie '));
}
async function capture(step,gate=null,movieMetadata=null){
  assert.ok(captures.length<plan.captureFormat.count,'At most4 original JPEGs');
  const beforeReadiness=gate?await waitFor(({method,args})=>{
    const value=window.reviewCaptureReadiness[method](args);return value.ready?value:null;
  },gate,20000):null;
  const before=await snapshot();
  assertVisualSurfaces(before,step);
  if(movieMetadata)assertMovieMiddle(before,step,movieMetadata);
  const shot=await driver.call('browsingContext.captureScreenshot',{context:target.context,origin:'viewport',
    format:{type:'image/jpeg',quality:plan.captureFormat.quality}});
  const bytes=Buffer.from(shot.data,'base64'),file=activeCase.id+'-'+String(step.index).padStart(2,'0')+'-'+step.scene+'-'+step.scenario+'.jpg';
  assert.ok(bytes.length<=plan.captureFormat.maximumEachCaptureBytes);
  totalCaptureBytes+=bytes.length;assert.ok(totalCaptureBytes<=plan.captureFormat.maximumCaptureBytes);
  await writeFile(resolve(output,file),bytes,{flag:'wx'});
  const captureRow={caseId:activeCase.id,scenario:step.scenario,file,bytes:bytes.length,
    sha256:createHash('sha256').update(bytes).digest('hex'),model:step.expectedModel,
    kind:step.kind,before,after:null,beforeReadiness,afterReadiness:null,
    admission:{status:'pending',movieMiddle:!!movieMetadata,
      movieSpecification:movieMetadata?{resource:movieMetadata.resource,presentation:'door',fit:movieMetadata.fit,
        phase:'movie',lowerDurationFraction:1/3,upperDurationFractionExclusive:.8}:null}};
  // Retain the one original JPEG and its raw snapshots before post-admission.
  // A late frame fails in place; it is never retaken, sought, paused or hidden.
  captures.push(captureRow);
  try{
    const after=await snapshot();captureRow.after=after;
    assert.equal(before.body.node,step.id);assert.equal(after.body.node,step.id);
    assertVisualSurfaces(after,step);
    if(movieMetadata)assertMovieMiddle(after,step,movieMetadata);
    const afterReadiness=gate?await evaluate(({method,args})=>window.reviewCaptureReadiness[method](args),gate):null;
    captureRow.afterReadiness=afterReadiness;
    if(gate){
      assert.ok(afterReadiness.ready,'Capture stays within its actual native title segment');
      assert.equal(beforeReadiness.generation,afterReadiness.generation);
      assert.equal(beforeReadiness.startSequence,afterReadiness.startSequence);
    }
    captureRow.admission.status='admitted';
  }catch(error){
    captureRow.admission={...captureRow.admission,status:'rejected',error:String(error),stack:error.stack};
    throw error;
  }
}
async function background(step){
  const scriptBackground=await waitTrace(()=>parsed('STORY_SCRIPT_BACKGROUND ').filter(e=>e.node===step.id).at(-1));
  const expected=route.nodes.find(e=>e.node.id===step.id);
  assert.equal(scriptBackground.effective,expected.expectedEffectiveBackground);
  return {scriptBackground,expected};
}
async function mediaEnded(step){
  const ended=await waitFor(id=>window.reviewMediaEvents.findLast(e=>e.node===id&&e.event==='ended'),step.id,45000);
  assert.equal(ended.trusted,true);assert.equal(ended.playbackRate,1);assert.equal(ended.seeking,false);
  assert.ok(Number.isFinite(ended.duration)&&ended.duration>0);
  assert.ok(Math.abs(ended.currentTime-ended.duration)<.001);
  assert.equal(ended.played.length,1);assert.equal(ended.played[0][0],0);
  assert.ok(Math.abs(ended.played[0][1]-ended.duration)<.001);
  const events=await evaluate(id=>window.reviewMediaEvents.filter(e=>e.node===id),step.id);
  assert.equal(events.filter(e=>e.event==='ended').length,1);
  assert.ok(events.every(e=>e.playbackRate===1&&!e.seeking&&!['seeking','seeked','error'].includes(e.event)));
  assert.ok(events.some(e=>e.event==='play')&&events.some(e=>e.event==='playing'));
  return {ended,events};
}
// Export only the existing document's bounded observer archive. Actual href,
// timeOrigin and observer caseName remain distinct from the requested case;
// a failed navigation cannot relabel the previous live document as a new one.
async function exportActualDocument(reason){
  const exported={reason,requestedCase:activeCase?.id||null,exportErrors:[]};
  try{
    exported.document=await evaluate(()=>{
      const exportErrors=[],attempt=(name,read)=>{try{return read();}catch(error){
        exportErrors.push({name,error:String(error),stack:error?.stack||''});return null;}};
      const observerState=attempt('observer.snapshot',()=>window.reviewEndingObserver?.snapshot()||null);
      const finished=attempt('observer.finish',()=>window.reviewEndingObserver?.finish()||null);
      const observer=finished||attempt('observer.data fallback',()=>window.reviewEndingObserver?.data()||null);
      return {identity:{href:location.href,timeOrigin:performance.timeOrigin,
          actualObserverCaseName:observerState?.caseName||null,node:document.body?.dataset.node||'',
          phase:document.body?.dataset.phase||''},observerState,
        observer,
        mediaEvents:attempt('original retained media',()=>window.reviewMediaEvents||[]),
        trustedInputs:attempt('original retained trusted inputs',()=>window.reviewTrustedInputs||[]),
        render:attempt('render history',()=>window.reviewRenderProbe?.snapshot()||null),exportErrors};
    });
  }catch(error){exported.exportErrors.push({operation:'actual-document-export',error:String(error),stack:error.stack});}
  failureExports.push(exported);return exported;
}
async function retainFailureEvidence(name){
  if(savedFailureNames.has(name))return;savedFailureNames.add(name);
  const exported=sessionRetired?{reason:'BiDi session retired; document unavailable to this driver',requestedCase:activeCase?.id||null,
    earlierDocumentExports:failureExports}:await exportActualDocument(name);
  let archive=null,embeddedFallback=null;
  try{
    const raw=JSON.stringify(exported),compressed=gzipSync(raw),file=name.replace(/\.json$/,'.actual-document.json.gz');
    await writeFile(resolve(output,file),compressed,{flag:'wx'});
    archive={file,rawSha256:createHash('sha256').update(raw).digest('hex'),rawBytes:Buffer.byteLength(raw),
      gzipSha256:createHash('sha256').update(compressed).digest('hex'),gzipBytes:compressed.length};
  }catch(error){diagnosticFailures.push({operation:'failure-document-write',error:String(error),stack:error.stack});embeddedFallback=exported;}
  try{await save(name,{firstFailure,documentArchive:archive,documentFallback:embeddedFallback,
    actualDocumentIdentity:exported.document?.identity||null,documentExportErrors:exported.exportErrors||[],
    played,captures,totalCaptureBytes,traces,records,rawConsole,fatalFacts,hitches,cancellations,
    diagnosticFailures,errors,http,actions});}
  catch(error){diagnosticFailures.push({operation:'failure-receipt-write',name,error:String(error),stack:error.stack});}
}
function closeExclusions(item,caseActions,trusted){
  const caseRecords=records.filter(row=>row.sequence>=traceStart);
  assert.equal(route.closeExclusions.length,2);
  return route.closeExclusions.map(policy=>{
    assert.equal(policy.skipInOut,false);assert.equal(policy.positiveNativeTapPanelClose,false);
    const step=item.steps.find(s=>s.id===policy.source);
    assert.equal(step.edge.id,policy.edge);assert.equal(step.edge.target,policy.target);
    const inputs=trusted.filter(e=>e.button==='advance'&&e.node===policy.source);
    const attempts=caseActions.filter(e=>e.selector==='#advance'&&e.before.body.node===policy.source);
    assert.equal(inputs.length,1);assert.equal(attempts.length,1);
    assert.equal(inputs[0].trusted,true);assert.equal(inputs[0].phase,'ready');
    const sourceEnter=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_ENTER '+policy.source+' '));
    const transition=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_TRANSITION ')&&
      JSON.parse(e.line.slice('STORY_PLAYER_TRANSITION '.length)).edge===policy.edge);
    const nextEnter=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_ENTER '+policy.target+' '));
    const change=caseRecords.find(e=>e.line.startsWith('STORY_CARD_CHANGE ')&&
      ((v)=>v.source===policy.source&&v.target===policy.target)(JSON.parse(e.line.slice('STORY_CARD_CHANGE '.length))));
    assert.ok(sourceEnter&&transition&&nextEnter&&change);
    assert.ok(sourceEnter.sequence<transition.sequence&&transition.sequence<nextEnter.sequence);
    const actual=JSON.parse(change.line.slice('STORY_CARD_CHANGE '.length));
    assert.deepEqual(actual.from,policy.from);assert.deepEqual(actual.to,policy.to);
    // Default foreground retirement may emit OUT after follow/ENTER. It must
    // not be relabelled as a NativeTapPanelClose request before this input's
    // transition. Keep original records and never wait for an OUT completion.
    const preFollowOut=caseRecords.filter(e=>e.line.startsWith('STORY_PANEL_OUT_START ')&&
      e.sequence>sourceEnter.sequence&&e.sequence<transition.sequence&&
      Number(e.line.split(/\s+/)[1])>=inputs[0].performanceMilliseconds);
    assert.equal(preFollowOut.length,0,'Excluded Close edge has no source tap OUT before follow');
    return {policy,sourceEnter,trustedInput:inputs[0],inputAttempt:attempts[0],
      transition,nextEnter,foregroundChange:change,preFollowOut,
      positiveCoverageClaimed:false,completionAwaitedBeforeFollow:false};
  });
}
function closeCoverage(item,casePlayed,caseActions,trusted){
  const caseRecords=records.filter(row=>row.sequence>=traceStart),witnesses=[];
  const detail=(row,prefix)=>JSON.parse(row.line.slice(prefix.length));
  const panelRecord=(name,owner)=>caseRecords.find(row=>row.line.startsWith(name+' ')&&
    ((value)=>value.node===owner.node&&value.group===owner.group&&value.token===owner.token)(detail(row,name+' ')));
  for(const [sourceId,targetId]of positiveCloseTargets){
    if(!item.steps.some(s=>s.id===sourceId))continue;
    const step=item.steps.find(s=>s.id===sourceId),from=casePlayed.find(s=>s.id===sourceId),to=casePlayed.find(s=>s.id===targetId);
    assert.equal(step.edge.target,targetId);assert.ok(from?.panel.owner&&from.panel.complete&&to?.panel.owner&&to.panel.complete);
    const sourceOwner=from.panel.owner,nextOwner=to.panel.owner;
    assert.equal(sourceOwner.node,sourceId);assert.equal(nextOwner.node,targetId);
    const inputs=trusted.filter(e=>e.button==='advance'&&e.node===sourceId);
    const attempts=caseActions.filter(e=>e.selector==='#advance'&&e.before.body.node===sourceId);
    assert.equal(inputs.length,1);assert.equal(attempts.length,1);
    assert.equal(inputs[0].trusted,true);assert.equal(inputs[0].phase,'ready');
    assert.equal(attempts[0].before.body.phase,'ready');
    const sourceEnter=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_ENTER '+sourceId+' '));
    const transition=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_TRANSITION ')&&detail(e,'STORY_PLAYER_TRANSITION ').edge===step.edge.id);
    const nextEnter=caseRecords.find(e=>e.line.startsWith('STORY_PLAYER_ENTER '+targetId+' '));
    assert.ok(sourceEnter&&transition&&nextEnter);
    // Target entry can itself retire the previous card after ENTER. Restrict
    // admission to the current source's real trusted-input time, so an older
    // post-follow retirement cannot masquerade as its ordinary tap request.
    const starts=caseRecords.filter(e=>e.line.startsWith('STORY_PANEL_OUT_START ')&&
      e.sequence>sourceEnter.sequence&&e.sequence<transition.sequence&&
      Number(e.line.split(/\s+/)[1])>=inputs[0].performanceMilliseconds);
    assert.equal(starts.length,1,'Exactly one source-owned outgoing request before the exact follow');
    const out=starts[0],fields=out.line.split(/\s+/),outPerformanceMilliseconds=Number(fields[1]);
    assert.equal(fields[2],'out','A choice decide/retirement close cannot substitute for ordinary Close');
    assert.ok(Number.isFinite(outPerformanceMilliseconds)&&outPerformanceMilliseconds>=inputs[0].performanceMilliseconds);
    assert.ok(out.sequence<transition.sequence&&transition.sequence<nextEnter.sequence);
    const sourcePanelComplete=panelRecord('STORY_PANEL_IN_COMPLETE',sourceOwner);
    const nextPanelStart=panelRecord('STORY_PANEL_IN_START',nextOwner),nextPanelComplete=panelRecord('STORY_PANEL_IN_COMPLETE',nextOwner);
    assert.ok(sourcePanelComplete&&sourcePanelComplete.sequence<out.sequence);
    assert.ok(nextPanelStart&&nextPanelComplete&&nextEnter.sequence<nextPanelStart.sequence&&nextPanelStart.sequence<nextPanelComplete.sequence);
    const nextOut=caseRecords.find(e=>e.sequence>out.sequence&&e.line.startsWith('STORY_PANEL_OUT_START '));
    const completion=caseRecords.find(e=>e.sequence>out.sequence&&(!nextOut||e.sequence<nextOut.sequence)&&
      e.line.startsWith('STORY_PANEL_OUT_COMPLETE ')&&e.line.split(/\s+/)[2]==='out')||null;
    witnesses.push({source:sourceId,target:targetId,edge:step.edge.id,
      ownershipProvenance:'Correlation of real source ENTER/panel token, trusted input, original outgoing timestamp/sequence and exact follow; PANEL_OUT has no invented node/generation field',
      sourceEnter,sourcePanelOwner:sourceOwner,sourcePanelComplete,trustedInput:inputs[0],inputAttempt:attempts[0],
      outgoingStart:out,outPerformanceMilliseconds,transition,nextEnter,nextPanelOwner:nextOwner,nextPanelStart,nextPanelComplete,
      outgoingCompletion:{observed:!!completion,record:completion,completionAwaitedBeforeFollow:false,
        provenance:'Separate subsequent original out completion fact; the product emits no completion node/token identity'},
      sameBgTextOrStayCoverage:false});
  }
  assert.equal(witnesses.length,plan.closeCoverage.expectedPositiveWitnesses,'P22 explicitly excludes positive Close coverage');
  return witnesses;
}
try{
  ({capabilities}=await driver.call('session.new',{capabilities:{}}));
  const {contexts}=await driver.call('browsingContext.getTree');target={context:contexts[0].context};
  driver.events((event,value)=>{
    if(event==='log.entryAdded'){
      const line=value.text||'',name=line.split(/\s+/,1)[0];
      const raw={event,rawEntry:value,requestedCaseAtReceipt:activeCase?.id||null,
        lastKnownDocumentIdentity,observedEpochMilliseconds:Date.now()};
      // Original severity and explicit handled fatal names are independent of
      // trace prefixes. Hitches/cancellations stay separate and nonfatal.
      const reason=value.type==='javascript'?'original-javascript-exception':
        value.level==='error'?'original-console.error':
        fatalProductNames.has(name)?'explicit-original-product-fatal-event':null;
      if(reason)fatalFacts.push({...raw,name,reason});
      if(name==='STORY_NORMAL_FRAME_HITCH')hitches.push(raw);
      if(/_CANCELLED$/.test(name))cancellations.push(raw);
      if(rawConsole.length<20000){rawConsole.push(raw);queueDiagnosticWrite('raw-console.jsonl',raw);}
      else errors.push('Original BiDi raw console archive limit exceeded');
      if(/^(?:STORY_|STELLA_|MODEL_|PREVIEW_|VOICE_)/.test(line)){
        traces.push(line);const row={sequence:traces.length-1,eventEpochMilliseconds:value.timestamp,
          observedEpochMilliseconds:Date.now(),line,rawEntry:value};
        records.push(row);queueDiagnosticWrite('events.jsonl',row);
      }
    }
    if(event==='network.responseCompleted'){
      const url=new URL(value.response.url);
      if(url.origin===origin){const row={url:url.href,status:value.response.status,mimeType:value.response.mimeType,
        observedEpochMilliseconds:Date.now()};http.push(row);
        if(row.status>=400&&url.pathname!=='/favicon.ico')errors.push('HTTP '+row.status+' '+row.url);}
    }
  });
  await driver.call('session.subscribe',{events:['log.entryAdded','network.responseCompleted'],contexts:[target.context]});
  for(const fn of [installRenderProbe,installEndingObserver,installCaptureReadiness])
    await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:fn.toString()});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:(()=>{
    window.reviewTrustedInputs=[];window.reviewMediaEvents=[];
    document.addEventListener('click',event=>{const e=event.target.closest('button');if(e)window.reviewTrustedInputs.push({
      button:e.id,edge:e.dataset.edge,trusted:event.isTrusted,node:document.body.dataset.node,phase:document.body.dataset.phase,
      epochMilliseconds:Date.now(),performanceMilliseconds:performance.now()});},true);
    document.addEventListener('DOMContentLoaded',()=>{
      const video=document.getElementById('movie');
      for(const name of ['loadstart','loadedmetadata','loadeddata','canplay','play','playing','pause','waiting','stalled','ended',
        'seeking','seeked','ratechange','volumechange','timeupdate','error'])
        video.addEventListener(name,event=>window.reviewMediaEvents.push({event:name,node:document.body.dataset.node,
          trusted:event.isTrusted,eventTimestamp:event.timeStamp,epochMilliseconds:Date.now(),performanceMilliseconds:performance.now(),
          resource:video.currentSrc,currentTime:video.currentTime,duration:Number.isFinite(video.duration)?video.duration:null,
          playbackRate:video.playbackRate,seeking:video.seeking,ended:video.ended,paused:video.paused,muted:video.muted,volume:video.volume,
          played:Array.from({length:video.played.length},(_,i)=>[video.played.start(i),video.played.end(i)])}));
    },{once:true});
  }).toString()});
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:plan.captureFormat.viewport,devicePixelRatio:1});

  assert.equal(plan.cases.length,1);
  for(const item of plan.cases){
    await flushDiagnosticWrites();rejectFatalDiagnostics('before next case');
    activeCase=item;traceStart=traces.length;
    route=await load('prepared/'+item.id+'.route.json');
    const offline=offlinePrepare.programs[item.id];assert.equal(offline.status,200);
    const firstPlayed=played.length,firstCapture=captures.length,firstAction=actions.length;
    await verifyInputs(binding);
    await flushDiagnosticWrites();rejectFatalDiagnostics('immediately before fresh navigation');
    stage=item.id+'-normal-setup';
    await driver.call('browsingContext.navigate',{context:target.context,
      url:origin+'/player/player.html?assetRevision='+binding.revision,wait:'interactive'});
    await waitFor(()=>window.reviewReady===true);
    await evaluate(()=>window.reviewEndingObserver.attachClock());
    await evaluate(name=>window.reviewEndingObserver.beginCase(name,{scope:'Saved P22 ending23-to26 only'}),item.id);
    lastKnownDocumentIdentity=await evaluate(()=>({href:location.href,timeOrigin:performance.timeOrigin,
      actualObserverCaseName:window.reviewEndingObserver.snapshot().caseName}));
    assert.equal(await evaluate(()=>document.getElementById('language').value),'zh');
    assert.equal(await evaluate(()=>document.getElementById('auto').getAttribute('aria-pressed')),'false');
    panelConfig=await evaluate(async()=>({player:await(await fetch('/player/player_config.json')).json(),
      transitions:await(await fetch('/player-assets/transitions.json')).json()}));
    stage=item.id+'-ordinary-saved-prepare';
    const actual=await evaluate(async({id,revision,expected})=>{
      const response=await fetch('/api/player/prepare',{method:'POST',headers:{'content-type':'application/json'},
        body:JSON.stringify({id,baseSha:revision,choices:{}})});
      const raw=await response.text(),http={status:response.status,headers:Object.fromEntries(response.headers)};
      if(!response.ok)return {...http,raw,loaded:false};
      let program;try{program=JSON.parse(raw);}catch(error){return {...http,raw,loaded:false,parseError:String(error)};}
      const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(program)));
      const programSha256=[...new Uint8Array(digest)].map(e=>e.toString(16).padStart(2,'0')).join('');
      if(programSha256!==expected)return {...http,raw,loaded:false,programSha256};
      // This is the product's unchanged load protocol, carrying the entire
      // ordinary response including its genuine before. No field is altered.
      window.postMessage({type:'stella-player-load',program},location.origin);
      return {...http,raw,loaded:true,programSha256};
    },{id:item.start,revision:binding.revision,expected:offline.programSha256});
    await writeFile(resolve(output,item.id+'-normal-http-prepare.json.gz'),gzipSync(actual.raw),{flag:'wx'});
    await save(item.id+'-normal-http.json',{...actual,raw:undefined});
    if(actual.status===422){
      const diagnostic=await evaluate(async({id,revision})=>{
        const response=await fetch('/api/resolve',{method:'POST',headers:{'content-type':'application/json'},
          body:JSON.stringify({id,baseSha:revision,choices:{}})});
        return {status:response.status,headers:Object.fromEntries(response.headers),raw:await response.text()};
      },{id:item.start,revision:binding.revision});
      await writeFile(resolve(output,item.id+'-normal-resolve.json.gz'),gzipSync(diagnostic.raw),{flag:'wx'});
      await save(item.id+'-normal-resolve-http.json',{...diagnostic,raw:undefined});
    }
    assert.equal(actual.status,200);assert.equal(actual.loaded,true);
    prepared=JSON.parse(actual.raw);assert.equal(prepared.start,item.start);
    assert.equal(prepared.headSha,binding.revision);assert.equal(prepared.nodes.length,binding.libraryCounts.libraryNodes);
    assert.equal(prepared.edges.length,binding.libraryCounts.libraryEdges);
    assert.deepEqual(prepared.before,route.before);
    for(const [index,step] of item.steps.entries()){
      stage=item.id+'-'+step.scene+'-'+step.scenario;
      await waitTrace(()=>traces.slice(traceStart).find(line=>line.startsWith('STORY_PLAYER_ENTER '+step.id+' ')),45000);
      const node=prepared.nodes.find(n=>n.id===step.id);assert.ok(node);
      assert.equal(node.model,step.expectedModel);
      const routeNode=route.nodes[index];assert.equal(routeNode.node.id,step.id);
      if(node.kind==='title'){
        const decision=await waitTrace(()=>parsed('STORY_NATIVE_INTERVAL_DECISION ').find(e=>e.node===step.id));
        // This saved end-title owns its automatic261. Its interval decision
        // remains a real product event; no chart or title state is seeded.
        assert.equal(decision.show,false);
        assert.equal(decision.reason,node.title_mode==='end'?'end-title':'linear-scene');
        const bg=await background(step);
        await capture(step,{method:'title',args:{node:step.id,caseName:item.id,
          referenceWidth:plan.captureReadiness.referenceWidth,
          stableStart:plan.captureReadiness.titleStableStart,stableEnd:plan.captureReadiness.titleStableEnd}});
        const state=captures.at(-1).after;
        assert.equal(state.background?.resource||'',routeNode.expectedDisplayBackground);
        assert.equal(state.backdrop?.resource||'',routeNode.expectedDisplayBackground);
        const complete=await waitTrace(()=>parsed('STORY_NATIVE_TITLE_ENTRY ')
          .find(e=>e.node===step.id&&e.stage==='completed'),20000);
        assert.equal(complete.durationMilliseconds,2500);
        played.push({caseId:item.id,id:step.id,kind:node.kind,decision,complete,...bg,state});
        continue; // The actual P22 title owns261. Never click its edge.
      }
      const bg=await background(step);
      if(node.kind==='movie'){
        assert.equal(step.id,'node:10030006:1003000600025');
        assert.deepEqual(node.command,['','','']);
        const metadata=await waitTrace(()=>parsed('STORY_PLAYER_MOVIE ').find(e=>e.node===step.id),30000);
        assert.equal(metadata.resource,'adv_dive01_out');assert.equal(metadata.presentation,'door');
        assert.equal(metadata.fit,panelConfig.player.movies.door_fit);
        const middle=await waitFor(id=>{
          const video=document.getElementById('movie'),card=document.getElementById('cardMotion');
          return document.body.dataset.node===id&&document.body.dataset.phase==='movie'&&video.readyState>=2&&
            Number.isFinite(video.duration)&&video.currentTime>=video.duration/3&&video.currentTime<video.duration*.8&&
            !video.ended&&!video.seeking&&video.playbackRate===1&&
            video.checkVisibility({opacityProperty:true,visibilityProperty:true})&&Number(getComputedStyle(card).opacity)>=.99&&
            {currentTime:video.currentTime,duration:video.duration,epochMilliseconds:Date.now()};
        },step.id,30000);
        await capture(step,null,metadata);const state=captures.at(-1).after;
        assert.equal(state.background?.resource,routeNode.expectedDisplayBackground);
        assert.equal(state.backdrop?.resource,routeNode.expectedDisplayBackground);
        const natural=await mediaEnded(step);
        await waitTrace(()=>parsed('STORY_PLAYER_TIMING ').find(e=>e.node===step.id&&e.stage==='movie_play_complete'),15000);
        // Saved25 has three empty command phases, like the reviewed P21 door.
        // Real ended and an actual ready state must precede the ordinary251
        // user input. A movie event alone neither advances nor fabricates ready.
        const ready=await waitFor(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready'&&
          document.getElementById('movie').ended&&
          document.getElementById('auto').getAttribute('aria-pressed')==='false'&&
          {epochMilliseconds:Date.now(),performanceMilliseconds:performance.now()},step.id,15000);
        assert.ok(ready.epochMilliseconds>=natural.ended.epochMilliseconds);
        assert.equal(parsed('STORY_PLAYER_TRANSITION ').filter(e=>e.edge===step.edge.id).length,0);
        played.push({caseId:item.id,id:step.id,kind:node.kind,metadata,middle,natural,ready,...bg,state,
          automaticMovieTransitionOwnsNext:false,userReadyAdvanceOwns251:true});
        await click('#advance');
        const movieInput=actions.at(-1);
        assert.equal(movieInput.before.body.node,step.id);
        assert.equal(movieInput.before.body.phase,'ready');
        assert.ok(movieInput.before.epochMilliseconds>=natural.ended.epochMilliseconds);
        const actualEdge=await waitTrace(()=>parsed('STORY_PLAYER_TRANSITION ').find(e=>e.edge===step.edge.id));
        assert.deepEqual(actualEdge.native,step.edge.native);assert.equal(actualEdge.target,item.steps[index+1].id);
        continue;
      }
      const wanted=step.choice?'choice':'ready';
      await waitFor(({id,wanted})=>document.body.dataset.node===id&&document.body.dataset.phase===wanted,{id:step.id,wanted});
      const panel=await panelReady(step,node);
      await waitFor(id=>{
        const card=document.getElementById('cardMotion'),panel=document.getElementById('subtitles'),a=getComputedStyle(card),p=getComputedStyle(panel);
        return document.body.dataset.node===id&&Number(a.opacity)>=.99&&Number(p.opacity)>=.99&&p.translate==='none'&&
          card.checkVisibility({opacityProperty:true,visibilityProperty:true})&&panel.checkVisibility({opacityProperty:true,visibilityProperty:true});
      },step.id);
      let render=null,picture=null;
      if(node.character_image){
        // Display kind and picture resource are separate real logs: the
        // DISPLAY_COMMIT suffix may still name an old actor detail object.
        // Never mistake that suffix for the CG identity or require an actor.
        const layout=await waitTrace(()=>parsed('STORY_PICTURE_LAYOUT ').filter(e=>e.node===step.id).at(-1));
        assert.equal(layout.resource,node.character_image);
        assert.ok(traces.slice(traceStart).filter(e=>e.startsWith('STORY_DISPLAY_COMMIT '+step.id+' picture')).length);
        picture=await waitFor(resource=>{
          const e=document.getElementById('picture');
          return !e.hidden&&e.naturalWidth>0&&e.naturalHeight>0&&
            new URL(e.currentSrc).pathname.endsWith('/'+encodeURIComponent(resource))&&
            e.checkVisibility({opacityProperty:true,visibilityProperty:true})&&
            {src:e.currentSrc,width:e.naturalWidth,height:e.naturalHeight};
        },node.character_image);
        picture={...picture,layout};
      }else if(step.expectedModel)render=await actorReady(step);
      else assert.ok(traces.slice(traceStart).some(e=>e.startsWith('STORY_DISPLAY_COMMIT '+step.id+' empty')));
      let state=await snapshot(),selected=null;
      assert.equal(state.background?.resource,routeNode.expectedDisplayBackground);
      assert.equal(state.backdrop?.resource,routeNode.expectedDisplayBackground);
      assertVisualSurfaces(state,{...step,choice:null});
      if(step.native.msg_text)assert.ok(state.accessibleText.includes(step.native.msg_text));
      if(step.choice){
        const edge=route.edges.find(e=>e.id===step.edge.id);assert.ok(edge?.available);
        assert.equal(edge.side,step.choice.side);assert.equal(edge.label_translation,step.choice.label);
        assert.equal(edge.quote_translation,step.choice.quote);
        for(const unknown of step.choice.unknown){
          const option=state.choices.find(e=>e.edge===unknown.id);
          assert.equal(option?.text,'← '+unknown.label+' · 未恢复');assert.equal(option.selected,'false');
          // Missing option labels may be selectable previews in the product.
          // No missing option is clicked or confirmed by this QA.
        }
        assert.equal(state.advanceDisabled,true);
        await click('#choices button[data-edge='+JSON.stringify(edge.id)+']');
        await waitFor(id=>document.body.dataset.phase==='choice'&&!document.getElementById('advance').disabled&&
          [...document.querySelectorAll('#choices button')].some(e=>e.dataset.edge===id&&e.getAttribute('aria-pressed')==='true'),edge.id);
        const quote=await waitTrace(()=>parsed('STORY_CHOICE_QUOTE ').filter(e=>e.edge===edge.id).at(-1));
        assert.equal(quote.language,'zh');
        const geometry=await waitFor(()=>{
          const raw=document.getElementById('viewport').dataset.choiceGeometry,value=raw&&JSON.parse(raw);
          return value?.pressed&&value.touch===1&&value;
        });
        if(step.expectedModel)render=await actorReady(step);
        state=await snapshot();assert.equal(state.body.node,step.id);
        assert.ok(state.accessibleText.includes(step.choice.quote));
        assert.equal(state.choiceSurface.visible,true);assertVisualSurfaces(state,step);
        selected={edge,quote,geometry};
      }
      await capture(step);
      played.push({caseId:item.id,id:step.id,kind:node.kind,panel,render,picture,...bg,state,selected});
      // This one case ends only at its own automatic title completion.
      // Keep the generic ready-stop branch unchanged; no extra route is added.
      if(index===item.steps.length-1&&item.stop.phase==='ready')break;
      assert.ok(step.edge);await click('#advance');
    }
    let clearMusic=null;
    if(item.stop.phase==='complete'){
      await waitFor(()=>document.body.dataset.phase==='complete',null,20000);
      const ending=item.steps.at(-1);
      const decision=parsed('STORY_NATIVE_INTERVAL_DECISION ').find(e=>e.node===ending.id);
      const command=await waitTrace(()=>parsed('STORY_BGM_COMMAND ').findLast(e=>
        e.resource==='bgm_btl_adv_win01'&&e.key===ending.id+':'+decision.generation));
      const play=await waitTrace(()=>parsed('STORY_BGM_PLAY ').findLast(e=>e.resource==='bgm_btl_adv_win01'));
      assert.equal(command.restart,false);assert.equal(command.fade,1);
      assert.ok(play.samples>0&&play.sampleRate>0);
      clearMusic={command,play,currentTransportOnly:true,originalRequestOrStopPhaseAccepted:false};
    }
    const finalState=await snapshot();
    const enters=traces.slice(traceStart).filter(e=>e.startsWith('STORY_PLAYER_ENTER ')).map(e=>e.split(' ')[1]);
    const transitions=parsed('STORY_PLAYER_TRANSITION ');
    assert.deepEqual(enters,item.steps.map(e=>e.id));
    const wantedEdges=item.steps.filter(s=>s.edge).map(s=>s.edge);
    assert.equal(transitions.length,wantedEdges.length);
    for(const [i,event]of transitions.entries()){
      assert.equal(event.edge,wantedEdges[i].id);assert.equal(event.target,wantedEdges[i].target);
      assert.equal(event.action,wantedEdges[i].flow_action);assert.deepEqual(event.native,wantedEdges[i].native);
    }
    assert.equal(captures.length-firstCapture,item.steps.length);
    if(item.stop.phase==='ready'){
      assert.equal(finalState.body.node,item.stop.node);assert.equal(finalState.body.phase,'ready');
      assert.equal(actions.slice(firstAction).filter(e=>e.selector==='#advance'&&e.before.body.node===item.stop.node).length,0);
      assert.ok(!transitions.some(e=>e.edge===route.forbidden.id));
    }else{
      assert.equal(finalState.body.phase,'complete');
      const complete=traces.slice(traceStart).filter(e=>e.startsWith('STORY_PLAYER_SECTION_COMPLETE '));
      assert.equal(complete.length,1);
      const event=records.find(e=>e.sequence>=traceStart&&e.line===complete[0]);
      assert.equal(event.rawEntry.args[1].value,'section:1003');
      assert.deepEqual(event.rawEntry.args[2].value.map(e=>e.value),[item.stop.completedOwnScene]);
      assert.deepEqual(event.rawEntry.args[3].value.map(e=>e.value),wantedEdges.map(e=>e.id));
      assert.equal(finalState.body.node,item.steps.at(-1).id);
    }
    const trusted=await evaluate(()=>window.reviewTrustedInputs);assert.ok(trusted.every(e=>e.trusted));
    assert.deepEqual(trusted.filter(e=>e.edge).map(e=>e.edge),item.steps.filter(s=>s.choice).map(s=>s.edge.id));
    for(const step of item.steps.filter(s=>s.kind==='title'))
      assert.equal(actions.slice(firstAction).filter(e=>e.selector==='#advance'&&e.before.body.node===step.id).length,0);
    assert.equal(trusted.filter(e=>e.button==='advance').length,3);
    const ordinaryCloseExclusions=closeExclusions(item,actions.slice(firstAction),trusted);
    const ordinaryClose=closeCoverage(item,played.slice(firstPlayed),actions.slice(firstAction),trusted);
    // Stop retires only a completed QA case. Keep the original passive
    // observers alive through it, then archive their complete retained rows
    // before the document can be navigated away. No outgoing animation is
    // awaited to permit follow; Close coverage reads already retained facts.
    await click('#stop');
    const renderHistoryAtBoundary=await evaluate(()=>window.reviewRenderProbe.snapshot());
    assert.equal(renderHistoryAtBoundary.losses.filter(e=>e.canvas==='actor'||e.attached).length,0);
    const observer=await evaluate(()=>window.reviewEndingObserver.finish());
    assert.equal(observer.droppedRecords,0);assert.deepEqual(observer.observerErrors,[]);
    await flushDiagnosticWrites();rejectFatalDiagnostics('completed case before navigation');
    await save(item.id+'-result.json',{caseId:item.id,prepared:{headSha:prepared.headSha,start:prepared.start,
      programSha256:actual.programSha256,before:prepared.before},played:played.slice(firstPlayed),
      captures:captures.slice(firstCapture),enters,transitions,finalState,actions:actions.slice(firstAction),trustedInputs:trusted,
      ordinaryClose,ordinaryCloseExclusions,renderHistoryAtBoundary,observer,clearMusic,scope:plan.acceptanceScope,sourceAutomaticityAccepted:false,originalCommandPhasesAccepted:false});
    await flushDiagnosticWrites();rejectFatalDiagnostics('case output flushed before next case');
  }
  assert.equal(played.length,4);assert.equal(captures.length,4);assert.deepEqual(errors,[]);
  const providerEvents=(await readFile(resolve(output,'provider-events.jsonl'),'utf8')).trim().split('\n').filter(Boolean).map(e=>JSON.parse(e));
  const modelDelivery={};
  const expectedModels=[...new Set(plan.cases.flatMap(c=>c.steps.map(s=>s.expectedModel).filter(Boolean)))];
  for(const model of expectedModels){
    const members=providerEvents.filter(e=>new RegExp('^assets/(?:preview/)?models/'+model+'/').test(e.relative));
    const definition=members.find(e=>/\.model3\.json(?:\.gz)?$/.test(e.relative));
    const moc=members.find(e=>/\.moc3(?:\.gz)?$/.test(e.relative));
    const texture=members.find(e=>e.relative.includes('/textures/'));
    assert.ok(definition&&moc&&texture,'Actual model delivery '+model);
    modelDelivery[model]={definition,moc,texture,members};
  }
  for(const resource of ['adv_dive01_out','bgm_btl_adv_win01'])
    assert.ok(providerEvents.some(e=>e.relative.includes(resource)),'Actual resource delivery '+resource);
  await save('provider-proof.json',{modelDelivery,events:providerEvents});
  await save('image-manifest.json',{format:'original-browser-viewport-jpeg',count:4,totalCaptureBytes,
    captures:captures.map(({caseId,scenario,file,bytes,sha256,model,kind})=>({caseId,scenario,file,bytes,sha256,model,kind})),
    requiresIndependentClosureBeforeReview:true});
  pendingResult={revision:binding.revision,sourceHead:binding.source.head,
    preparedPrograms:offlinePrepare.programs,played,captures,totalCaptureBytes,actions,traces,records,errors,http,
    rawConsole,fatalFacts,hitches,cancellations,diagnosticFailures,requiresTerminalAcceptanceReceipt:true,
    scope:plan.acceptanceScope,sourceAutomaticityAccepted:false,originalCommandPhasesAccepted:false};
}catch(error){
  retainFirstFailure(error,'ordinary case failure');await retainFailureEvidence('failure.json');
}finally{
  // Late product or asynchronous append failures reject before retirement and
  // before any next case. Preserve the first failure while the actual
  // document still exists; diagnostic failures never replace that first cause.
  try{
    await flushDiagnosticWrites();rejectFatalDiagnostics('before session retirement');
    if(pendingResult){
      const finalRender=await evaluate(()=>window.reviewRenderProbe.snapshot());
      assert.equal(finalRender.losses.filter(e=>e.canvas==='actor'||e.attached).length,0);
      pendingResult.finalRenderHistory=finalRender;
    }
  }
  catch(error){retainFirstFailure(error,'pre-retirement flush');}
  if(firstFailure)await retainFailureEvidence('pre-retirement-failure.json');
  try{await driver.call('session.end');sessionRetired=true;}
  catch(error){retainFirstFailure(error,'session.end');}
  finally{try{driver.close();}catch(error){retainFirstFailure(error,'driver.close');}}
}
try{
  // After the acknowledged BiDi session end, drain its retained original
  // events/append facts and recheck after every output await. The browser OS
  // process still belongs to supervisor cleanup; session.end is not its exit
  // proof. A result file alone is never terminal acceptance or an exit0 promise.
  await flushDiagnosticWrites();rejectFatalDiagnostics('after session retirement');
  if(firstFailure)throw Error('An earlier failure is retained');
  assert.equal(sessionRetired,true);assert.ok(pendingResult);
  await save('result.json',pendingResult);
  await flushDiagnosticWrites();rejectFatalDiagnostics('after final result write');
  await save('terminal-acceptance.json',{accepted:true,sessionRetired,diagnosticWritesFlushed:true,
    fatalFacts,hitches,cancellations,diagnosticFailures,rawConsoleCount:rawConsole.length,
    cases:1,entered:4,captures:4,requiresRootIndependentOsClosure:true});
  await flushDiagnosticWrites();rejectFatalDiagnostics('after terminal receipt write');
  console.log(JSON.stringify({cases:1,entered:4,captures:4,totalCaptureBytes,errors,terminalAccepted:true}));
}catch(error){
  retainFirstFailure(error,'terminal diagnostics');await retainFailureEvidence('terminal-failure.json');
  process.exitCode=1;
  console.error(JSON.stringify({firstFailure,played:played.length,captures:captures.length,
    fatalFacts:fatalFacts.length,diagnosticFailures:diagnosticFailures.length}));
}
