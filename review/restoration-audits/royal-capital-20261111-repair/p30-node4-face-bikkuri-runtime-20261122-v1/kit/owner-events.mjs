/** Browser-owned diagnostic boundary, installed after the real ready event.
 * It does not modify the reviewed tap. Original console methods run exactly
 * once with the original receiver/arguments and their original return/throw.
 * Only afterward does a separate catch retain/forward diagnostic facts.
 */
let installedOnce=false;
export async function installOwner({rootRelease,caseId,runLabel,nodeIds,modelIds,budgets}={}){
  if(installedOnce||window.reviewPrivateOwner)throw Error('One owner/tap installation per fresh document');
  if(rootRelease?.rootConfirmed!==true||!caseId||!runLabel||!budgets)throw Error('Exact owner release/scope required');
  installedOnce=true;
  const {ActorAnimation}=await import('/studio/actor_animation.js');
  const {visualFrameClock}=await import('/studio/visual_frame_clock.js');
  const {installProposedActorReadTapV2}=await import('/__private/tap-v2.mjs');
  const originalRender=ActorAnimation.prototype.render;
  const tap=await installProposedActorReadTapV2({rootRelease,productReady:true,nodeIds,modelIds,
    maximumRows:budgets.tapRowsPerCase,maximumOwnerRows:budgets.ownerEventRowsPerCase});
  tap.arm(caseId,{runLabel});
  const trace=[],errors=[],media=[],checkpoints=[],marks=[],trustedInputs=[],productFatalErrors=[];
  let productFatalSeen=0,productFatalDropped=0;
  // This explicit set is distinct from hitches/cancellations/observer cost.
  // Normal-clock listener failures are info-level product facts in canonical
  // code; their original severity cannot be inferred from console.error alone.
  const fatalProductNames=new Set(['STORY_PLAYER_ERROR','STORY_NORMAL_CLOCK_LISTENER_ERROR','STORY_NORMAL_CLOCK_REPORT_ERROR',
    'STORY_FX_ERROR','STORY_BACKGROUND_ERROR','STORY_PICTURE_ERROR','STORY_BGM_LOAD_FAILED']);
  const latest={commits:{},panelStart:{},panelComplete:{},panelCancelled:{},transitions:{},displays:{}};
  const entered=[],originals=new Map(),wrapped=new Map(),textEncoder=new TextEncoder();
  let sourceSequence=0,traceBytes=0,traceDropped=0,mediaDropped=0,errorDropped=0,closed=false;
  let calls=0,successfulObservationMs=0,maximumObservationMs=0,originalConsoleMs=0;
  const failure=e=>{if(errors.length<32)errors.push(String(e?.stack||e));else errorDropped++;};
  const rawCopy=value=>{
    if(value instanceof Error)return {observerValueType:'Error',name:value.name,message:value.message,stack:value.stack};
    if(value===undefined)return {observerValueType:'undefined'};
    return typeof value==='string'||value===null||typeof value==='number'||typeof value==='boolean'?value:structuredClone(value);
  };
  const generationEvents=new Set(['STORY_NATIVE_INTERVAL_SCENE_LOAD','STORY_NATIVE_INTERVAL_DECISION','STORY_VOICE_PREPARATION']);
  function observe(method,args,callEntryMs,returnedAtMs){
    const originalName=typeof args[0]==='string'?args[0]:null;
    const fatalReason=method==='error'?'original-console.error':fatalProductNames.has(originalName)?'explicit-original-product-fatal-event':null;
    if(!fatalReason&&(!originalName||!/^(?:STORY_|STELLA_|MODEL_|PREVIEW_|VOICE_)/.test(originalName)))return;
    const name=originalName,sequence=sourceSequence++;
    // Classification runs after the original console call, within its existing
    // diagnostic catch. Never recursively log classification through console.
    // Keep a fatal count even if the separate raw-trace budget is exhausted.
    if(fatalReason){
      productFatalSeen++;
      if(productFatalErrors.length<32)productFatalErrors.push({sourceEventSequence:sequence,method,name,reason:fatalReason,
        caseId,runLabel,originalCallEntryMilliseconds:callEntryMs});
      else productFatalDropped++;
    }
    const row={sequence,caseId,runLabel,method,name,rawArguments:args.map(rawCopy),
      originalCallEntryMilliseconds:callEntryMs,originalCallReturnedMilliseconds:returnedAtMs,
      performanceTimeOrigin:performance.timeOrigin,wallEpochMilliseconds:Date.now(),
      node:document.body?.dataset.node||'',phase:document.body?.dataset.phase||'',normal:visualFrameClock.snapshot(),
      forwarded:false,diagnosticCompletedMilliseconds:null,diagnosticDurationMilliseconds:null};
    // Reserve room for the post-copy timestamps and JSON-array separators.
    // This is a conservative byte budget, not a claim of exact serialized size.
    const size=textEncoder.encode(JSON.stringify(row)).length+256;
    if(trace.length>=budgets.consoleRowsPerCase||traceBytes+size>budgets.consoleBytesPerCase){traceDropped++;return;}
    traceBytes+=size;trace.push(row);
    // Keep the original detail string beside its parsed value. A forwarded
    // generation is historical, linked to this exact raw source sequence and
    // call-entry timestamp, never a fabricated current-player accessor.
    if(generationEvents.has(name)){
      if(typeof args[1]!=='string')throw Error('Original generation detail is not the expected JSON string');
      row.forwarded=tap.recordOwnerProductEvent({name,detail:JSON.parse(args[1]),sourceEventSequence:sequence,
        observedWallMilliseconds:callEntryMs});
      if(!row.forwarded)throw Error('Scoped original generation event was not retained');
    }
    if(name==='STORY_PLAYER_ENTER')entered.push(args[1]);
    if(['STORY_NORMAL_MOTION_COMMIT','STORY_PANEL_IN_START','STORY_PANEL_IN_COMPLETE','STORY_PANEL_IN_CANCELLED'].includes(name)){
      const detail=JSON.parse(args[1]);
      const key={'STORY_NORMAL_MOTION_COMMIT':'commits','STORY_PANEL_IN_START':'panelStart',
        'STORY_PANEL_IN_COMPLETE':'panelComplete','STORY_PANEL_IN_CANCELLED':'panelCancelled'}[name];
      const identity=key==='panelCancelled'?detail.group+':'+detail.token:detail.node;
      latest[key][identity]={detail,sourceEventSequence:sequence};
    }
    if(name==='STORY_DISPLAY_COMMIT')latest.displays[args[1]]={kind:args[2],model:args[3],sequence};
    if(name==='STORY_ANIMATOR_TRANSITION')latest.transitions[row.node+':'+args[2]]={model:args[1],token:args[3],sequence};
    row.diagnosticCompletedMilliseconds=performance.now();
    row.diagnosticDurationMilliseconds=row.diagnosticCompletedMilliseconds-returnedAtMs;
  }
  for(const method of ['info','warn','error','log']){
    const original=console[method];originals.set(method,original);
    const replacement=function(...args){
      const callEntryMs=performance.now();
      const result=Reflect.apply(original,this,args); // Original throws stay outside the diagnostic catch.
      const returnedAtMs=performance.now();
      try{observe(method,args,callEntryMs,returnedAtMs);}catch(error){failure(error);}
      const cost=performance.now()-returnedAtMs;
      calls++;successfulObservationMs+=cost;maximumObservationMs=Math.max(maximumObservationMs,cost);
      originalConsoleMs+=returnedAtMs-callEntryMs;
      return result;
    };
    wrapped.set(method,replacement);console[method]=replacement;
  }
  const errorListener=e=>failure(e.error||e.message||'window error');
  const rejectionListener=e=>failure(e.reason||'unhandled rejection');
  const clickListener=e=>{
    const button=e.target.closest('button');if(!button)return;
    if(trustedInputs.length>=256){failure('Trusted input log cap');return;}
    trustedInputs.push({button:button.id,edge:button.dataset.edge||null,isTrusted:e.isTrusted,
      node:document.body?.dataset.node,phase:document.body?.dataset.phase,wallMilliseconds:performance.now()});
  };
  const mediaListener=e=>{
    if(e.target?.id!=='movie')return;
    if(media.length>=512){mediaDropped++;return;}
    const video=e.target;media.push({event:e.type,node:document.body?.dataset.node,phase:document.body?.dataset.phase,
      wallMilliseconds:performance.now(),wallEpochMilliseconds:Date.now(),currentTime:video.currentTime,
      duration:Number.isFinite(video.duration)?video.duration:null,playbackRate:video.playbackRate,
      seeking:video.seeking,paused:video.paused,readyState:video.readyState});
  };
  const mediaNames=['loadedmetadata','playing','ended','error','seeking','seeked','ratechange'];
  window.addEventListener('error',errorListener);window.addEventListener('unhandledrejection',rejectionListener);
  document.addEventListener('click',clickListener,true);
  for(const name of mediaNames)document.addEventListener(name,mediaListener,true);
  function state(){
    return {caseId,runLabel,node:document.body?.dataset.node,phase:document.body?.dataset.phase,
      normal:visualFrameClock.snapshot(),wallMilliseconds:performance.now(),wallEpochMilliseconds:Date.now(),
      entered:[...entered],latest:structuredClone(latest),errors:[...errors],traceRows:trace.length,traceBytes,
      traceDropped,mediaDropped,errorDropped,productFatalSeen,productFatalDropped,
      productFatalErrors:structuredClone(productFatalErrors),media:media.slice(-12),
      autoPressed:document.getElementById('auto').getAttribute('aria-pressed')};
  }
  function checkpoint(label){
    if(checkpoints.length>=budgets.checkpointReadsPerCase)throw Error('Bounded tap checkpoint budget exceeded');
    const began=performance.now(),data=tap.read();
    const row=data.rows.filter(r=>r.node===document.body?.dataset.node).at(-1)||null;
    const item={label,node:document.body?.dataset.node,phase:document.body?.dataset.phase,
      beganMilliseconds:began,completedMilliseconds:performance.now(),row,
      tapRows:data.rows.length,tapErrors:data.errors,tapDropped:data.dropped,tapOwnerDropped:data.ownerDropped};
    item.copyDurationMilliseconds=item.completedMilliseconds-began;
    checkpoints.push(item);return structuredClone(item);
  }
  function finish(){
    if(closed)throw Error('Owner export/restore is one-shot');
    closed=true;tap.disarm();
    const began=performance.now(),tapData=tap.read(),copyCompleted=performance.now();
    tap.stop();
    const restoration={renderRestored:ActorAnimation.prototype.render===originalRender,consoleRestored:true};
    for(const [method,original]of originals){
      if(console[method]===wrapped.get(method))console[method]=original;
      else {restoration.consoleRestored=false;failure('Console ownership changed: '+method);}
    }
    window.removeEventListener('error',errorListener);window.removeEventListener('unhandledrejection',rejectionListener);
    document.removeEventListener('click',clickListener,true);
    for(const name of mediaNames)document.removeEventListener(name,mediaListener,true);
    const traceSerializedBytes=textEncoder.encode(JSON.stringify(trace)).length;
    if(traceSerializedBytes>budgets.consoleBytesPerCase)failure('Actual console archive exceeded its reserved byte budget');
    return {schema:'stella.private-owner-original-trace.v1',caseId,runLabel,trace,traceBytes,traceSerializedBytes,traceDropped,
      traceByteAccounting:'traceBytes is conservative reservation; traceSerializedBytes is actual exported JSON array',
      rawArgumentQualification:'Primitive strings are exact; Error/undefined use explicitly typed observer copies',
      media,mediaDropped,errors,errorDropped,productFatalErrors,productFatalSeen,productFatalDropped,
      fatalProductNames:[...fatalProductNames],hitchesAreNotFatalByName:true,
      checkpoints,marks,trustedInputs,tap:tapData,restoration,
      exportCopy:{beganMilliseconds:began,completedMilliseconds:copyCompleted,durationMilliseconds:copyCompleted-began},
      consoleOverhead:{calls,diagnosticWorkMilliseconds:successfulObservationMs,
        maximumDiagnosticWorkMilliseconds:maximumObservationMs,originalConsoleMilliseconds:originalConsoleMs,
        qualification:'After-return diagnostic work, including error/cap bookkeeping; original-throw path is untouched and excluded. No no-pacing-effect claim.'},
      weakIdentitiesAreNotNativeGeneration:true,currentStoryPlayerGeneration:null,animatorGeneration:null,
      parametersArePostComposePreCorePreGLNotPaint:true,motionAccepted:false};
  }
  window.reviewPrivateOwner={state,checkpoint,finish,mark(name){
    if(marks.length>=128)throw Error('Owner marker budget exceeded');const point={name,...state()};marks.push(point);return point;}};
  return {installed:true,caseId,runLabel,exactlyOneTap:true,currentStoryPlayerGeneration:null};
}
