(async function privateKinpakuStoryPlayback(page,options){
  'use strict';
  // REVIEW ONLY: root must supply the reviewed literal source strings and a
  // released, existing adapter URL. This factory neither launches nor closes
  // the sole browser; root retains independent browser/server-finally cleanup.
  if(options?.executionAuthorized!==true)throw Error('Private audition has not been released');
  const base=new URL(options.baseUrl);
  if(!['127.0.0.1','localhost','[::1]'].includes(base.hostname))throw Error('Loopback adapter required');
  const compileMusic=(0,eval)(options.productionCompileMusicSource);
  if(typeof compileMusic!=='function')throw Error('Missing reviewed production projection');
  const resource='bgm_adv_kinpaku02_cd2_18',slot='__stellaKinpaku02PrivateMusicV1';
  const pattern=base.origin+'/program?*',logs=[],requests=[],errors=[],stages=[],observerErrors=[];
  const listenerAttempts=[],hostCleanup={routeAttempted:false,routeRemovalAttempted:false,
    routeRemoved:false,listenerRemovalAttempts:0,listenersRemoved:0};
  let frame=null,installed=false,programCount=0,programProof=null,routeFailure=null,releaseProgram;
  let stopped=false,cleanup=null,result=null;
  const gate=new Promise(resolve=>{releaseProgram=resolve;});
  const jsonEqual=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const log=message=>{const text=message.text();if(text.startsWith('STORY_'))logs.push({hostUnixMs:Date.now(),text});};
  const pageError=error=>errors.push(String(error));
  const response=reply=>{const url=new URL(reply.url());
    if(url.origin===base.origin&&['/music/'+resource,'/api/music/'+resource].includes(url.pathname))
      requests.push({url:reply.url(),status:reply.status(),hostUnixMs:Date.now()});};
  const routeHandler=async route=>{
    try{
      if(++programCount!==1)throw Error('Expected exactly one normal compiled-program GET');
      const reply=await route.fetch(),original=await reply.json();
      if(!reply.ok()||original.start!=='10450056:1'||original.before.bg_music!=='')throw Error('Unexpected normal root/entry state');
      const privateProgram=JSON.parse(JSON.stringify(original));
      const rows=[1,2,3].map(number=>privateProgram.nodes.find(row=>row.id==='10450056:'+number));
      if(rows.some(row=>!row)||rows[0].kind!=='title'||rows[1].kind!=='text')throw Error('Expected Title1/narration2/next3');
      const sourceJA=['力を合わせて','――白熱するユリウスとエルザの戦闘。\nそこにスバルも予期せぬ助っ人が現れる。\n果たして結末は……','――盗品蔵・夕刻'];
      if(rows.some((row,index)=>row.text!==sourceJA[index]))throw Error('Reviewed1→2→3 Japanese identity changed');
      const fadeDefault=original.semantics.bgm_fade_seconds;
      if(!Number.isFinite(fadeDefault)||fadeDefault<0)throw Error('Missing production fade default');
      for(const row of rows)if(row.bg_music!==''||!jsonEqual(row.music,compileMusic('',fadeDefault)))throw Error('Expected blank inherited BGM');
      for(let i=0;i<2;i++){
        const edges=original.edges.filter(edge=>edge.source===rows[i].id);
        if(edges.length!==1||!edges[0].available||edges[0].target!==rows[i+1].id||edges[0].kind!=='next')
          throw Error('Normal1→2→3 edge changed');
      }
      const before={bg_music:rows[1].bg_music,music:JSON.parse(JSON.stringify(rows[1].music))};
      rows[1].bg_music=resource;rows[1].music=compileMusic(resource,fadeDefault);
      // The authoring field has TWO necessary compiled projections. Restoring
      // both, then comparing the complete program, covers edges, commands,
      // phases, text, state, directory and all unrelated nodes without a save.
      const restored=JSON.parse(JSON.stringify(privateProgram));
      Object.assign(restored.nodes.find(row=>row.id==='10450056:2'),before);
      if(!jsonEqual(restored,original))throw Error('Unexpected program delta outside the two projections');
      if(rows[1].music.action!=='play'||rows[1].music.restart!==false||rows[1].music.fade!==fadeDefault)
        throw Error('Production bare-resource projection changed');
      programProof={authoredFieldCount:1,compiledFieldCount:2,node:rows[1].id,
        fields:['bg_music','music'],before,after:{bg_music:rows[1].bg_music,music:rows[1].music},
        restoredWholeProgramDeepEqual:true,otherDerivedSnapshotsChanged:[],persisted:false,
        defaultSource:'program.semantics.bgm_fade_seconds',sourceJA:rows[1].text,
        authoredStableKey:'s10450056-p30-at0397'};
      // Hold this one response until exact iframe-module observation is owned.
      // The gate releases no story node and supplies no synthetic phase Wait.
      if(!await gate){await route.abort();return;}
      await route.fulfill({response:reply,json:privateProgram});
    }catch(error){routeFailure=String(error);await route.abort().catch(()=>{});}
  };
  function requireCleanObserverSnapshot(label,value){
    // Diagnostic errors invalidate original-instance evidence even when the
    // first captured owner keeps playing normally. This includes the observer's
    // explicit second-owner error; it must never be hidden by a good voice.
    if(!Array.isArray(value?.errors)||value.errors.length){
      observerErrors.push({label,errors:Array.isArray(value?.errors)?[...value.errors]:['Observer error array unavailable']});
      throw Error('Observer evidence incomplete at '+label);
    }
  }
  const snapshot=async label=>{
    const value=await frame.evaluate(({slot,label})=>{
      const handle=Object.getOwnPropertyDescriptor(globalThis,slot)?.value;
      if(!handle)throw Error('Missing owned observer');return {label,...handle.snapshot()};
    },{slot,label});
    requireCleanObserverSnapshot(label,value);return value;
  };
  const ready=number=>frame.waitForFunction(number=>document.body.dataset.node==='10450056:'+number&&
    document.body.dataset.phase==='ready',number,{timeout:30000});
  async function normalStop(){
    if(!frame||frame.isDetached())return null;
    await frame.locator('#stop').evaluate(button=>button.click());
    await frame.waitForFunction(()=>document.body.dataset.phase==='stopped',null,{timeout:3000});
    stopped=true;return installed?await snapshot('after-normal-stop'):null;
  }
  try{
    // Record ownership BEFORE each registration attempt. Even a setup call
    // that partially registers and then throws must enter this same finally.
    // Each removal below is independent, so one failure cannot strand others.
    for(const [event,handler] of [['console',log],['pageerror',pageError],['response',response]]){
      listenerAttempts.push({event,handler});page.on(event,handler);
    }
    hostCleanup.routeAttempted=true;await page.route(pattern,routeHandler);
    await page.goto(base.origin+'/?scene=10450056&node=1',{waitUntil:'domcontentloaded'});
    // A newly created iframe's about:blank document can already have a body.
    // Wait for the actual player navigation before selecting its Frame or
    // importing the observation modules. The program response is still gated,
    // so this is initialization readiness, not an authored playback delay.
    await page.waitForFunction(()=>{
      const preview=document.querySelector('#storyPreview');
      try{return preview?.contentWindow?.location.pathname==='/player/player.html'&&
        Boolean(preview.contentDocument?.body);}
      catch{return false;}
    });
    frame=page.frames().find(candidate=>new URL(candidate.url()).pathname==='/player/player.html');
    if(!frame)throw Error('Expected original player iframe');
    const receipt=await frame.evaluate(async source=>{
      const factory=(0,eval)(source);if(typeof factory!=='function')throw Error('Observer is not a factory');
      const installed=await factory(),handle=Object.getOwnPropertyDescriptor(globalThis,installed.slot)?.value;
      const owns=Boolean(installed.ownerProof&&handle?.ownerProof===installed.ownerProof);
      if(installed.status!=='private_music_observer_installed'||installed.methodCount!==3||!owns){
        // Verification failure cannot leave an identity-proven installation
        // active. Foreign slots are never removed; root still closes the frame.
        const cleanup=owns?handle.uninstall('installation-verification-failed'):null;
        throw Error('Observer ownership not verified '+JSON.stringify(cleanup));
      }
      return {status:installed.status,slot:installed.slot,methodCount:installed.methodCount,ownedSlotVerified:true};
    },options.observerFactorySource);
    installed=true;stages.push({label:'observer-installed',receipt});releaseProgram(true);
    await frame.waitForFunction(()=>document.body.dataset.node==='10450056:1'&&document.body.dataset.phase==='chart',null,{timeout:30000});
    await page.locator('#advance').click(); // Actual UI input: normal chart → Title1 → narration2.
    await ready(2);stages.push(await snapshot('narration2-ready-before-fresh-click'));
    // A real viewport pointerdown reaches the production resumeAudio handler.
    // At ready, its click follows the saved edge to3; no private resume/play is
    // called, and node3 inherits the same original channel and source.
    await frame.locator('#viewport').click();
    await ready(3);const first=await snapshot('node3-ready-after-trusted-click');stages.push(first);
    // This is an observer listening interval, never an authored/native Wait.
    // It samples the existing audio clock; it schedules no source or RAF work.
    await page.waitForTimeout(2000);
    const later=await snapshot('node3-observer-listening-end');stages.push(later);
    const current=later.owner?.current,initial=first.owner?.current;
    if(routeFailure||programCount!==1||!programProof)throw Error('Private program response proof failed: '+routeFailure);
    if(errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Story player error');
    if(later.owner?.currentResource!==resource||later.owner.contextState!=='running'||
      !initial||!current||later.voices.length!==1||current.ended||current.audioTime<=initial.audioTime||current.currentTime<=initial.currentTime)
      throw Error('Original source/context did not progress normally after trusted click');
    if(!later.events.some(event=>event.kind==='pointerdown'&&event.trusted&&event.node==='10450056:2'))
      throw Error('Fresh trusted node2 gesture not observed');
    if(!current.durationWithinResamplingTolerance||!current.nativeLoopValid||!current.sourceLoopMatches)
      throw Error('Decoded duration/native loop validation failed');
    if(later.owner.muted||!(later.owner.outputGain>0)||!(current.volume>0))throw Error('Original channel remains muted or zero gain');
    if(current.metadata.samples!==8414915||current.metadata.sample_rate!==44100||
      current.metadata.native_cue_id!==0||current.metadata.loop!==true||current.channels!==2||
      current.metadata.loop_start!==6.048095238095238||current.metadata.loop_end!==190.81439909297052||
      current.metadata.startup_events.length!==0)throw Error('Installed native metadata differs');
    const resources=await frame.evaluate(resource=>performance.getEntriesByType('resource')
      .filter(entry=>['/music/'+resource,'/api/music/'+resource].includes(new URL(entry.name).pathname)).map(entry=>entry.toJSON()),resource);
    for(const prefix of ['/music/','/api/music/'])if(!requests.some(row=>new URL(row.url).pathname===prefix+resource&&row.status===200))
      throw Error('Missing actual story-player resource response '+prefix);
    result={status:'private_original_story_bgm_transport_progress_observed',resources};
  }catch(error){result={status:'private_original_story_bgm_test_failed',failure:String(error)};}
  finally{
    releaseProgram(false);
    try{const state=await normalStop();if(state)stages.push(state);
      if(installed&&(!state?.owner||state.owner.active||state.owner.loading||state.owner.currentResource||
        state.owner.players!==0||state.owner.cancelFade||state.voices.some(voice=>!voice.ended)))throw Error('Normal Stop left BGM work owned');
    }catch(error){errors.push('normal Stop: '+String(error));}
    try{if(installed){
      cleanup=await frame.evaluate(slot=>globalThis[slot].uninstall('driver-finally'),slot);
      // Uninstall performs its own final snapshot before restoring descriptors.
      // Errors first observed during Stop/cleanup must also revoke any earlier
      // transport-success result; restoration remains completed before checking.
      requireCleanObserverSnapshot('uninstall-final-snapshot',cleanup.result);
    }}
    catch(error){errors.push('observer cleanup: '+String(error));}
    if(hostCleanup.routeAttempted){
      hostCleanup.routeRemovalAttempted=true;
      try{await page.unroute(pattern,routeHandler);hostCleanup.routeRemoved=true;}
      catch(error){errors.push('unroute: '+String(error));}
    }
    for(const {event,handler} of [...listenerAttempts].reverse()){
      hostCleanup.listenerRemovalAttempts++;
      try{page.off(event,handler);hostCleanup.listenersRemoved++;}
      catch(error){errors.push('remove listener '+event+': '+String(error));}
    }
  }
  if(errors.length||observerErrors.length||programCount!==1||!stopped||!cleanup?.cleanup.allRestored||cleanup.snapshotError||
    hostCleanup.routeAttempted&&!hostCleanup.routeRemoved||hostCleanup.listenersRemoved!==listenerAttempts.length)
    result={...result,status:'private_original_story_bgm_test_failed',cleanupIncomplete:true};
  return {...result,programProof,programCount,routeFailure,stages,logs,requests,errors,observerErrors,cleanup,hostCleanup,
    persisted:false,authoredFieldCount:1,compiledFieldCount:2,scriptWaitAdded:false,
    audibleListeningAccepted:false,originalOnsetFadeGainRestartAccepted:false,
    loopWrapActuallyObserved:false,rootReviewed:false,rootConfirmed:false};
})
