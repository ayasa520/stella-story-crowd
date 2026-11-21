// Artifact-only passive observations for the normal production player iframe.
// Install before navigation, but attachClock() only after its ready handshake:
// importing the already-evaluated module then cannot initialize game time early.
// No transport, media, command, renderer or clock method is replaced here.
export function installEndingObserver() {
  const rows=[],generations=new Map(),observerErrors=[];
  const originalInfo=console.info;
  let clock=null,unsubscribe=null,cardObserver=null,phaseObserver=null;
  let caseName='setup',configuration=null,activeDrop=null,dropSerial=0,sequence=0,droppedRecords=0;
  const maximumRecords=20000;
  window.addEventListener('message',event=>{
    if(event.source===window&&event.origin===location.origin&&event.data?.type==='stella-player-ready')window.reviewReady=true;
  });

  function rectangle(node){
    if(!node)return null;
    const {x,y,width,height}=node.getBoundingClientRect();
    return {x,y,width,height};
  }
  function state(){
    const node=document.body?.dataset.node||'';
    const card=document.getElementById('cardMotion');
    const video=document.getElementById('movie');
    const flow=document.getElementById('storyFlow');
    const title=flow?.querySelector('.native-title-content');
    const actor=document.getElementById('actor');
    // Read the existing surfaces at each original event/mutation sample. This
    // does not create a frame loop or claim unobserved inter-frame continuity.
    let actorAncestorAlpha=1;
    for(let element=actor;element instanceof Element;element=element.parentElement){
      const style=getComputedStyle(element);
      actorAncestorAlpha*=Number(style.opacity);
      if(style.display==='none'||style.visibility==='hidden')actorAncestorAlpha=0;
    }
    const actorGL=window.reviewRenderProbe?.snapshot().contexts.find(row=>row.canvas==='actor')||null;
    const now=performance.now();
    return {observedPerformanceMilliseconds:now,observedEpochMilliseconds:performance.timeOrigin+now,
      caseName,node,phase:document.body?.dataset.phase||'',generation:generations.get(node)||null,
      generationProvenance:generations.has(node)?'actual existing generation-bearing console event':'unobserved',
      generationIsLastObservedEventValueNotPrivateCurrentValue:true,
      normalClock:clock?.snapshot()||null,
      card:card?{inlineAlpha:card.style.opacity,computedAlpha:Number(getComputedStyle(card).opacity),
        translate:getComputedStyle(card).translate,rect:rectangle(card)}:null,
      actor:actor?{attached:actor.isConnected,hidden:actor.hidden,
        visible:actor.checkVisibility({opacityProperty:true,visibilityProperty:true}),
        effectiveAncestorAlpha:actorAncestorAlpha,rect:rectangle(actor),GL:actorGL}:null,
      video:video?{currentTime:video.currentTime,duration:Number.isFinite(video.duration)?video.duration:null,
        paused:video.paused,ended:video.ended,hidden:video.hidden,seeking:video.seeking,
        playbackRate:video.playbackRate,defaultPlaybackRate:video.defaultPlaybackRate,
        muted:video.muted,volume:video.volume,readyState:video.readyState,currentSrc:video.currentSrc,
        mozHasAudio:typeof video.mozHasAudio==='boolean'?video.mozHasAudio:null,
        exposedAudioTrackCount:video.audioTracks?.length??null}:null,
      title:{flowHidden:flow?.hidden??null,flowClass:flow?.className||'',
        nativeElementAttached:!!title?.isConnected,rootAlpha:title?Number(getComputedStyle(title).opacity):null,
        label:title?.getAttribute('aria-label')||'',rect:rectangle(title)},
      advanceDisabled:document.getElementById('advance')?.disabled??null,
      autoPressed:document.getElementById('auto')?.getAttribute('aria-pressed')||null,
      activeDrop:activeDrop?{...activeDrop}:null};
  }
  function record(kind,trigger,value){
    if(rows.length>=maximumRecords){droppedRecords++;return;}
    // Observer failures cannot escape into the product's console or clock
    // listener. They remain explicit uncovered evidence for the audit.
    try{rows.push({sequence:sequence++,kind,trigger,value,state:state()});}
    catch(error){observerErrors.push({kind,error:String(error),observedPerformanceMilliseconds:performance.now()});}
  }
  function parse(value){
    if(typeof value!=='string')return null;
    try{return JSON.parse(value);}catch{return null;}
  }
  function consoleObservation(args,trigger){
    const name=args[0];
    if(typeof name!=='string'||!/^STORY_(?:CARD_|CHOICE_|PANEL_IN_|TEXT_PANEL_LAYOUT|PLAYER_|NATIVE_|NORMAL_TRANSITION_CLOCK|VOICE_PREPARATION)/.test(name))return;
    const detail=parse(args[1]);
    if(detail?.node&&Number.isInteger(detail.generation)&&
        /^(?:STORY_NATIVE_INTERVAL_SCENE_LOAD|STORY_NATIVE_INTERVAL_DECISION|STORY_VOICE_PREPARATION)$/.test(name)){
      generations.set(detail.node,{value:detail.generation,source:name,sourceDetail:detail,
        observedAtPerformanceMilliseconds:performance.now()});
    }
    if(name==='STORY_CARD_OUT_START'){
      activeDrop={serial:++dropSerial,node:document.body?.dataset.node||'',
        generation:generations.get(document.body?.dataset.node||'')||null,
        productReportedWallMilliseconds:args[1],selected:args[2]};
    }
    record('product-console',trigger,{name,args:args.slice(1),detail});
    if(name==='STORY_CARD_OUT_COMPLETE')activeDrop=null;
  }

  // Preserve the real console invocation and return value. Snapshot immediately
  // after it, retaining its own call-entry/observation times separately. This
  // is not an asynchronous sample retroactively stamped with a product time.
  console.info=function(...args){
    const invoked=performance.now();
    const result=originalInfo.apply(this,args);
    try{consoleObservation(args,{kind:'synchronous-console-call',
      hookEntryPerformanceMilliseconds:invoked,
      productReportedWallMilliseconds:typeof args[1]==='number'?args[1]:null});}
    catch(error){observerErrors.push({kind:'console-observation',error:String(error),observedPerformanceMilliseconds:performance.now()});}
    return result;
  };

  document.addEventListener('DOMContentLoaded',()=>{
    const card=document.getElementById('cardMotion');
    cardObserver=new MutationObserver(mutations=>{
      // MutationObserver has no original write timestamp. These are delivered
      // mutation/read samples on the unchanged current Normal frame; do not
      // relabel them as samples taken at a previous CardOut event timestamp.
      record('card-alpha-mutation',{kind:'mutation-delivery',originalWriteTimeUnobserved:true},
        {mutations:mutations.map(m=>({attribute:m.attributeName,oldInlineStyle:m.oldValue}))});
    });
    cardObserver.observe(card,{attributes:true,attributeOldValue:true,attributeFilter:['style']});
    const video=document.getElementById('movie');
    for(const name of ['loadstart','loadedmetadata','play','playing','timeupdate','ended','pause',
      'seeking','seeked','ratechange','volumechange','emptied','error']){
      video.addEventListener(name,event=>record('media-event',{
        kind:'browser-media-event',eventType:name,eventTimestamp:event.timeStamp,isTrusted:event.isTrusted},null));
    }
    document.addEventListener('click',event=>{
      const button=event.target.closest('button');if(!button)return;
      record('input',{kind:'dom-input-capture',eventTimestamp:event.timeStamp,isTrusted:event.isTrusted},
        {button:button.id,edge:button.dataset.edge||'',label:button.textContent});
    },true);
    phaseObserver=new MutationObserver(mutations=>{
      record('body-state-mutation',{kind:'mutation-delivery',originalWriteTimeUnobserved:true},
        {mutations:mutations.map(m=>({attribute:m.attributeName,oldValue:m.oldValue}))});
    });
    phaseObserver.observe(document.body,{attributes:true,attributeOldValue:true,attributeFilter:['data-node','data-phase']});
    window.addEventListener('pagehide',()=>phaseObserver.disconnect(),{once:true});
  },{once:true});

  window.reviewEndingObserver={
    async attachClock(){
      if(!window.reviewReady)throw Error('Attach observer only after normal player ready');
      if(clock)return state();
      ({visualFrameClock:clock}=await import('/studio/visual_frame_clock.js'));
      // This listener reads the current immutable sample. It never calls
      // sampleFrame/setRate/now integration or schedules another RAF chain.
      // Listener ordering is retained: alpha mutations below are the primary
      // post-write witnesses, while this may observe a pre-write frame state.
      unsubscribe=clock.subscribe(()=>{
        if(activeDrop)record('normal-clock-sample',{kind:'existing-clock-read-only-listener',
          mayPrecedeProductAlphaWriteInSameFrame:true},null);
      });
      record('observer-clock-attached',{kind:'explicit-observer-read'},null);
      return state();
    },
    beginCase(name,expected){
      // This resets only observer bookkeeping. Preserve the unmatched start
      // as evidence; it is never a read of the engine's active operation.
      const previousUnmatchedObservedStart=activeDrop;activeDrop=null;
      caseName=name;configuration=expected;
      record('case-begin',{kind:'driver-observer-boundary'},{expected,previousUnmatchedObservedStart});
      return state();
    },
    snapshot(){return state();},
    data(){return {schema:'stella.movie-end-title.passive-observer.v1',rows,droppedRecords,observerErrors,
      normalClockAttached:!!clock,configuration,scope:'Observed event/alpha/Normal-clock/input ownership only; no native timing or full-frame video acceptance.'};},
    finish(){
      unsubscribe?.();cardObserver?.disconnect();phaseObserver?.disconnect();
      if(console.info===this.consoleWrapper)console.info=originalInfo;
      return this.data();
    },
    consoleWrapper:console.info,
  };
}
