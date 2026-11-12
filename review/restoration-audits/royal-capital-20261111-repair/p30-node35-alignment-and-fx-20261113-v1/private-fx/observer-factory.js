(async function installP30FxFirstPaintObserver(options){
  'use strict';
  options=options||{};
  // This expression is intended for a later owner-approved frame.evaluate in
  // the already-ready player iframe, never the CLI host. No browser is opened
  // here. These exact modules are already dependencies of that live player;
  // do not substitute query-suffixed URLs that instantiate duplicate classes.
  const slot=options.slot||'__stellaP30FxFirstPaintObserverV2';
  const targetNode='10450056:27',resource='adv_ef_explosion01';
  if(slot in globalThis)throw new Error('Observer slot already exists');
  if(document.body.dataset.node!=='10450056:25'||document.body.dataset.phase!=='ready')
    throw new Error('Install only at the existing node25-ready boundary');
  if(Number(document.getElementById('card')?.dataset.fxInstances||0)!==0)
    throw new Error('Existing FX instance prevents bounded attribution');
  const [{VisualEffects},{ParticleSystem},{ParticleRenderer},{OriginalScene},{visualFrameClock}]=await Promise.all([
    import('/player/visual_effects.js'),import('/player/particle_system.js'),
    import('/player/particle_renderer.js'),import('/player/player_scene.js'),
    import('/studio/visual_frame_clock.js')]);
  // Module resolution is the only installation await. Another installer can
  // acquire this slot while that await is pending. Recheck before any wrapper
  // is installed; everything from this guard to publication is synchronous.
  if(slot in globalThis)throw new Error('Observer slot acquired during module resolution');
  if(document.body.dataset.node!=='10450056:25'||document.body.dataset.phase!=='ready')
    throw new Error('Entry moved during observer-module resolution');

  const records=[],observerErrors=[],patches=[],owners=new Set();
  const instanceMetadata=new WeakMap(),geometryMetadata=new WeakMap(),crossings=new Set();
  const counts={};let active=true,droppedRecords=0,targetInstances=0,textBeginAnchor=null;
  let firstTextDraw=null,yellowBatchObserved=false,handle;
  const ownerProof={}; // Compared by identity inside the iframe, never by JSON.
  const matchesNode=()=>active&&document.body.dataset.node===targetNode;
  const panelStyle=canvas=>({opacity:canvas?.style.opacity??null,translate:canvas?.style.translate??null});
  const record=(kind,data={})=>{
    if(!active)return;
    if(records.length>=64){droppedRecords++;return;}
    records.push({kind,performanceMs:performance.now(),node:document.body.dataset.node,
      normalClock:visualFrameClock.snapshot(),...data});
  };
  const observe=callback=>{
    // Observation failures must not become application failures. Buffer them
    // without logging recursively through the temporarily observed console.
    try{return callback();}
    catch(error){if(observerErrors.length<8)observerErrors.push(String(error));return undefined;}
  };
  const metadataFor=instance=>instanceMetadata.get(instance);

  // Each wrapper has exactly one Reflect.apply of the captured original. It
  // returns that value unchanged, including the original Promise/array object,
  // and rethrows the same original exception. There is no await/.then, extra
  // RAF, timer, advance, geometry call, draw, random sample or pixel readback.
  const plans=[];
  function plan(object,key,label,before,after){
    const descriptor=Object.getOwnPropertyDescriptor(object,key);
    if(!descriptor||typeof descriptor.value!=='function'||!descriptor.configurable)
      throw new Error('Unsupported observation descriptor: '+label);
    const original=descriptor.value;
    counts[label]={entries:0,originalCalls:0,originalThrows:0};
    function wrapper(...args){
      const count=counts[label];count.entries++;
      const context=before?observe(()=>before(this,args)):undefined;
      let result;
      try{count.originalCalls++;result=Reflect.apply(original,this,args);}
      catch(error){count.originalThrows++;throw error;}
      if(after)observe(()=>after(this,args,result,context));
      return result;
    }
    plans.push({object,key,label,descriptor,wrapper});
  }

  plan(VisualEffects.prototype,'play','VisualEffects.play',(owner,args)=>{
    if(!matchesNode()||args[0]?.resource!==resource)return;
    owners.add(owner);
    record('fx_play_call',{ownerGeneration:owner.generation,resource,
      offset:[...(args[0].offset||[])],emissionTimes:[...(args[1]||[])],
      rafAlreadyPending:Boolean(owner.frame)});
  });

  // Existing START is inside play after systems/layers/Set.add and before its
  // RAF request. Observe that existing call synchronously; never attach a
  // Promise continuation just to discover the new instance after the fact.
  plan(console,'info','console.info',(_console,args)=>{
    if(!matchesNode())return;
    if(args[0]==='STORY_FX_START'){
      const message=JSON.parse(args[1]);if(message.resource!==resource)return;
      const candidates=[];
      for(const owner of owners)for(const instance of owner.instances)
        if(instance.resource.id===resource&&!metadataFor(instance))candidates.push({owner,instance});
      if(candidates.length!==1){record('fx_activation_attribution_gap',{candidateCount:candidates.length});return;}
      const {owner,instance}=candidates[0],meta={id:++targetInstances,owner,instance,
        ownerGeneration:owner.generation,seed:message.seed,ticks:0};
      instanceMetadata.set(instance,meta);
      record('fx_activation_existing_start_call',{instance:meta.id,seed:meta.seed,
        ownerGeneration:meta.ownerGeneration,instanceBeganMs:instance.began,
        layers:instance.layers.length,emissionTimes:[...instance.emissionTimes],
        systems:[...instance.systems.values()].map(system=>({id:system.data.id,name:system.data.name,
          effectiveDelay:system.delay,speed:system.data.speed,queuedEvents:system.events.length})),
        activationMeaning:'Existing START call after instance insertion; instanceBegan is its stored simulation origin'});
    }else if(args[0]==='STORY_PANEL_IN_START'||args[0]==='STORY_PANEL_IN_COMPLETE'){
      const message=JSON.parse(args[1]);if(message.node!==targetNode)return;
      record('existing_panel_entry_log',{event:args[0],payload:message,
        panelInlineStyle:panelStyle(document.getElementById('subtitles'))});
    }
  });

  plan(VisualEffects.prototype,'tick','VisualEffects.tick',(owner,args)=>{
    if(!matchesNode()||!owners.has(owner))return;
    for(const instance of owner.instances){
      const meta=metadataFor(instance);
      if(!meta||owner.generation!==meta.ownerGeneration||meta.ticks>=3)continue;
      meta.ticks++;
      record('fx_early_tick_before_original',{instance:meta.id,seed:meta.seed,tick:meta.ticks,
        rafMs:args[0],instanceBeganMs:instance.began,elapsedSeconds:(args[0]-instance.began)/1000,
        systems:[...instance.systems.values()].map(system=>({id:system.data.id,name:system.data.name,
          simulatedTime:system.time,particles:system.particles.length,queuedEvents:system.events.length}))});
    }
  });

  plan(ParticleSystem.prototype,'geometry','ParticleSystem.geometry',null,(system,args,vertices)=>{
    if(!matchesNode()||yellowBatchObserved||system.data.name!=='Yellow')return;
    const meta=metadataFor(system.owner);
    if(!meta||meta.owner.generation!==meta.ownerGeneration||!vertices.length)return;
    // Retain metadata keyed by the exact original array. The renderer receives
    // that same array; geometry is never recomputed to obtain diagnostics.
    let maxAlpha=0;
    for(const vertex of vertices)maxAlpha=Math.max(maxAlpha,vertex.color[3]);
    const data={instance:meta.id,seed:meta.seed,system:system.data.id,simulationTime:args[0],
      vertices:vertices.length,maxVertexAlpha:maxAlpha,
      earliestLiveParticleBirth:system.particles.length?Math.min(...system.particles.map(p=>p.birth)):null};
    geometryMetadata.set(vertices,data);
  });

  plan(ParticleRenderer.prototype,'draw','ParticleRenderer.draw',(_renderer,args)=>{
    if(!matchesNode()||yellowBatchObserved)return null;
    const yellow=args[1].map(entry=>geometryMetadata.get(entry.vertices)).filter(Boolean);
    if(!yellow.length)return null;
    return {drawEnterMs:performance.now(),yellow,hiddenBefore:args[0].hidden};
  },(_renderer,args,_result,context)=>{
    if(!context||!active||yellowBatchObserved)return;
    yellowBatchObserved=true;
    record('yellow_nonempty_draw_batch_returned',{...context,drawReturnMs:performance.now(),
      hiddenAfter:args[0].hidden,
      boundary:'Before/after the unchanged ParticleRenderer.draw containing the exact nonempty Yellow geometry array',
      exactGlDrawArraysTimestampAvailable:false,gpuCompletionOrPresentationProved:false});
  });

  plan(OriginalScene.prototype,'draw','OriginalScene.draw',(scene,args)=>{
    if(!matchesNode()||!scene.panel)return null;
    const visible=args[0],reached=[1,2,3].filter(count=>!crossings.has(count)&&visible>=count);
    if(!reached.length)return null;
    return {drawEnterMs:performance.now(),visible,reached};
  },(scene,_args,_result,context)=>{
    if(!context||!active||!scene.panel)return;
    for(const count of context.reached)crossings.add(count);
    if(firstTextDraw===null)firstTextDraw=context.drawEnterMs;
    const points=Array.from(scene.panel.text),visible=Number.isFinite(context.visible)?context.visible:points.length;
    record('text_visible_thresholds_drawn',{...context,drawReturnMs:performance.now(),
      prefix:points.slice(0,Math.max(0,visible)).join(''),language:document.getElementById('language')?.value,
      textLength:points.length,group:scene.panel.group,panelInlineStyle:panelStyle(scene.canvas),
      exactTextBeganMs:null,textBeganBracketMs:[textBeginAnchor,firstTextDraw],
      textBeganLimit:'StoryPlayer/player are module-private; no exact assignment timestamp is exposed'});
  });

  function timing(event){
    if(!matchesNode()||event.detail?.node!==targetNode)return;
    if(!['enter','phase_1_begin','phase_1_end','text_begin','phase_2_begin'].includes(event.detail.stage))return;
    if(event.detail.stage==='text_begin')textBeginAnchor=performance.now();
    record('existing_player_timing_event',{detail:{...event.detail},
      textBeginAnchorMs:textBeginAnchor,exactTextBeganMs:null,
      anchorMeaning:'Synchronous text_begin event occurs before the private textBegan assignment'});
  }

  function snapshot(){
    return JSON.parse(JSON.stringify({status:'observation_only',rootReviewed:false,rootConfirmed:false,
      targetNode,resource,timeOriginMs:performance.timeOrigin,active,records,observerErrors,droppedRecords,
      originalCallCounts:counts,allOriginalCallCountsEqual:Object.values(counts).every(c=>c.entries===c.originalCalls),
      targetInstances,yellowNonemptyDrawBatchObserved:yellowBatchObserved,
      exactGlSubmissionTimestampAvailable:false,exactTextBeganMs:null,
      textBeganBracketMs:[textBeginAnchor,firstTextDraw],visibleThresholdsObserved:[...crossings],
      noNewSchedulingInsideHooks:true,noExtraAdvanceGeometryOrDrawCalls:true,
      noSeedOrPhaseOrXYZOrWaitChange:true,noPixelReadback:true,gpuPresentationAccepted:false}));
  }
  function describeError(error){
    try{return {name:String(error?.name||'Error'),message:String(error?.message||error)};}
    catch{return {name:'Error',message:'Error details could not be read'};}
  }
  function restoreOwned(reason){
    const restored=[],conflicts=[],listeners=[];
    active=false;
    // Cleanup has no serialization dependency. Each listener, descriptor and
    // the window slot has its own guarded block, so one host failure cannot
    // strand the remaining owners. These operations never stop the player.
    try{document.removeEventListener('stella-player-timing',timing);listeners.push('timing-removed');}
    catch(error){conflicts.push('timing-listener: '+describeError(error).message);}
    try{window.removeEventListener('pagehide',onPageHide);listeners.push('pagehide-removed');}
    catch(error){conflicts.push('pagehide-listener: '+describeError(error).message);}
    for(const patch of [...patches].reverse()){
      try{
        const current=Object.getOwnPropertyDescriptor(patch.object,patch.key);
        if(current?.value===patch.wrapper)Object.defineProperty(patch.object,patch.key,patch.descriptor);
        else if(current?.value!==patch.descriptor.value){
          conflicts.push(patch.label+': later or unknown owner');continue;
        }
        const after=Object.getOwnPropertyDescriptor(patch.object,patch.key);
        if(after?.value!==patch.descriptor.value||after.configurable!==patch.descriptor.configurable||
           after.enumerable!==patch.descriptor.enumerable||after.writable!==patch.descriptor.writable)
          conflicts.push(patch.label+': original descriptor not verified');
        else restored.push(patch.label);
      }catch(error){conflicts.push(patch.label+': '+describeError(error).message);}
    }
    let slotState='unknown';
    try{
      const current=Object.getOwnPropertyDescriptor(globalThis,slot);
      if(!current)slotState='absent';
      else if(current.value===handle&&handle?.ownerProof===ownerProof){
        delete globalThis[slot];
        slotState=Object.getOwnPropertyDescriptor(globalThis,slot)?'not-removed':'removed';
        if(slotState==='not-removed')conflicts.push('window-slot: removal not verified');
      }else{
        slotState='foreign';conflicts.push('window-slot: later or unknown owner');
      }
    }catch(error){conflicts.push('window-slot: '+describeError(error).message);}
    return {reason,restored,listeners,slotState,conflicts,allRestored:conflicts.length===0};
  }
  function uninstall(reason='owner-finally'){
    let result=null,snapshotError=null,cleanup;
    try{
      try{result=snapshot();}
      catch(error){snapshotError=describeError(error);}
    }finally{
      // Snapshot/JSON failure must never be an early exit from restoration.
      // The fallback returned below contains only plain diagnostic metadata,
      // not the offending records that failed to serialize.
      cleanup=restoreOwned(reason);
    }
    return {...(result||{status:'snapshot_failed_cleanup_attempted',rootReviewed:false,rootConfirmed:false}),
      active:false,snapshotError,cleanup,requiresFrameClosure:!cleanup.allRestored};
  }
  const onPageHide=()=>observe(()=>uninstall('pagehide'));

  // Descriptor validation above completes before the first mutation. If any
  // installation step fails, restore already-owned descriptors synchronously.
  try{
    for(const patch of plans){
      Object.defineProperty(patch.object,patch.key,{...patch.descriptor,value:patch.wrapper});patches.push(patch);
    }
    document.addEventListener('stella-player-timing',timing);
    window.addEventListener('pagehide',onPageHide);
    handle={snapshot,uninstall,ownerProof};
    Object.defineProperty(globalThis,slot,{value:handle,configurable:true});
  }catch(error){
    const cleanup=restoreOwned('partial-install-rollback');
    const original=describeError(error);
    // Custom Error fields are available to the owner bridge inside the same
    // iframe. Repeat the plain receipt in message text because a transport
    // may serialize only standard Error fields across the frame boundary.
    const failure=new Error('Observer installation failed: '+original.message+
      '\nObserver rollback receipt: '+JSON.stringify(cleanup));
    failure.name='ObserverInstallationError';failure.observerInstallError=original;
    failure.observerCleanup=cleanup;throw failure;
  }
  return {status:'installed_observer_only',slot,targetNode,resource,rootReviewed:false,rootConfirmed:false,
    methodCount:patches.length,ownerProof,exactTextBeganAvailable:false,exactGlSubmissionTimestampAvailable:false};
})
