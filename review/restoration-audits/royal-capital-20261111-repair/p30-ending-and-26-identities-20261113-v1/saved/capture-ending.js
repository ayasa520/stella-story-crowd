async page => {
  const owner='p30-ending-normal-v1',key='__stellaP30EndingNormalV1',probeKey='__stellaP30EndingAudioProbeV1';
  const logs=[],errors=[],responses=[],visits=[],cleanupErrors=[];
  let frame=null,probeInstalled=false,probe=null,handoff=null,result;
  const onConsole=message=>{const text=message.text();if(text.startsWith('STORY_')||text.startsWith('MODEL_'))
    logs.push({wall:Date.now(),text});};
  const onError=error=>errors.push(String(error));
  const onResponse=response=>{if(/\/(movie|music)\/|\/api\/music\/|title-assets/.test(response.url()))
    responses.push({wall:Date.now(),url:response.url(),status:response.status()});};
  const requireCondition=(condition,message)=>{if(!condition)throw Error(message);};
  const state=()=>frame.evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
    language:document.getElementById('language').value,now:performance.now(),timeOrigin:performance.timeOrigin,
    status:document.getElementById('status').textContent,error:document.getElementById('status').classList.contains('error')}));
  const ready=async number=>{
    await frame.waitForFunction(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready',
      '10450058:'+number,{timeout:30000});const value=await state();visits.push(value);
    if(value.error)throw Error(value.status);return value;
  };
  try{
    page.on('console',onConsole);page.on('pageerror',onError);page.on('response',onResponse);
    // There is intentionally no navigation, reload, fetch('/program'), restart,
    // screenshot, recorder, override or replacement player in this continuation.
    frame=page.frames().find(item=>item.url().includes('/player/player.html'));
    requireCondition(frame,'Existing player iframe missing');
    handoff=await frame.evaluate(({key,owner})=>{
      const value=window[key];
      if(!value||value.owner!==owner||value.document!==document||value.timeOrigin!==performance.timeOrigin||value.claimed)
        throw Error('Missing original34 handoff or case already claimed; do not reconstruct/retry');
      if(document.body.dataset.node!=='10450058:34'||document.body.dataset.phase!=='ready'||
        document.getElementById('language').value!=='ja')throw Error('Expected saved34 ready in Japanese');
      value.claimed=true;return{owner:value.owner,timeOrigin:value.timeOrigin,url:value.url,summary:value.summary};
    },{key,owner});
    probeInstalled=true;
    await frame.evaluate(async({probeKey,owner})=>{
      if(Object.hasOwn(window,probeKey))throw Error('Audio probe already exists');
      const {StoryMusicPlayer}=await import('/studio/music_player.js');
      const proto=StoryMusicPlayer.prototype,descriptor=Object.getOwnPropertyDescriptor(proto,'apply');
      if(typeof descriptor?.value!=='function')throw Error('Original music apply method unavailable');
      const original=descriptor.value,movie=document.getElementById('movie'),body=document.body;
      const data={calls:[],movieEvents:[],phaseChanges:[],audioSnapshots:[],observationErrors:[]};
      let channel=null,voice=null,disposed=false,observer=null;
      const safe=callback=>{try{return callback();}catch(error){data.observationErrors.push(String(error));return null;}};
      const voiceState=label=>safe(()=>{
        const current=channel?.current,context=channel?.context;
        const metadata=voice?.metadata;
        const row={label,node:body.dataset.node,phase:body.dataset.phase,now:performance.now(),
          resource:current?.resource||null,sameVoice:!!voice&&current?.voice===voice,
          inOriginalPlayers:!!voice&&channel.players.has(voice),ended:voice?.ended===true,
          currentTime:voice?.currentTime??null,voiceBegan:voice?.began??null,
          contextState:context?.state||null,contextTime:context?.currentTime??null,
          gain:voice?.volume??null,muted:channel?.muted??null,outputGain:channel?.output?.gain.value??null,
          metadata:metadata?{resource:metadata.resource,loop:metadata.loop,loop_start:metadata.loop_start,
            loop_end:metadata.loop_end,samples:metadata.samples,sample_rate:metadata.sample_rate,
            startup_events:metadata.startup_events}:null};
        data.audioSnapshots.push(row);return row;
      });
      // A plain function preserves both synchronous exceptions and the exact
      // Promise returned by the original async method. Observation attaches a
      // separate settled handler; the player still receives the original result.
      // Arguments, this, clocks, gains, context and source are never replaced.
      const wrapped=function(...args){
        const resource=args[0];
        const call=safe(()=>{const row={resource,node:body.dataset.node,now:performance.now(),
          fade:args[1]?.fade,restart:args[1]?.restart,key:args[1]?.key,start:args[1]?.start};
          data.calls.push(row);return row;});
        if(resource==='bgm_btl_adv_win01')channel=this;
        let returned;
        try{returned=Reflect.apply(original,this,args);}
        catch(error){safe(()=>{if(call)call.synchronousError=String(error);});throw error;}
        if(resource==='bgm_btl_adv_win01'){
          const settled=()=>safe(()=>{
            if(disposed)return;
            voice=this.current?.resource===resource?this.current.voice:null;
            if(call)call.resolved=true;voiceState('win01-apply-resolved');
          });
          // Both branches consume only this observational continuation. A
          // rejection still propagates unchanged through the returned original.
          safe(()=>returned.then(settled,error=>safe(()=>{if(!disposed&&call)call.rejection=String(error);}))
            .catch(error=>safe(()=>{if(!disposed)data.observationErrors.push(String(error));})));
        }
        return returned;
      };
      const movieState=event=>safe(()=>{
        if(body.dataset.node!=='10450058:36')return;
        const rect=movie.getBoundingClientRect(),viewport=document.getElementById('viewport').getBoundingClientRect();
        data.movieEvents.push({event,node:body.dataset.node,phase:body.dataset.phase,now:performance.now(),
          source:movie.currentSrc,duration:movie.duration,currentTime:movie.currentTime,ended:movie.ended,
          natural:[movie.videoWidth,movie.videoHeight],presentation:movie.dataset.moviePresentation,
          fit:movie.style.objectFit,rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},
          viewport:{width:viewport.width,height:viewport.height}});
      });
      const onMetadata=()=>movieState('loadedmetadata'),onEnded=()=>movieState('ended');
      const recordPhase=()=>safe(()=>{const row={node:body.dataset.node,phase:body.dataset.phase,now:performance.now()};
        const previous=data.phaseChanges.at(-1);if(!previous||previous.node!==row.node||previous.phase!==row.phase)
          data.phaseChanges.push(row);});
      const cleanup=()=>{
        disposed=true;observer?.disconnect();
        movie.removeEventListener('loadedmetadata',onMetadata);movie.removeEventListener('ended',onEnded);
        const current=Object.getOwnPropertyDescriptor(proto,'apply');let applyRestored=false;
        if(current?.value===wrapped){Object.defineProperty(proto,'apply',descriptor);applyRestored=true;}
        else if(current?.value===original)applyRestored=true;
        else data.observationErrors.push('Music apply owner changed; unrelated replacement not overwritten');
        data.cleanup={observerDisconnected:true,movieListenersRemoved:true,applyRestored};
      };
      // Publish cleanup ownership before installing each reversible hook. An
      // installation exception rolls everything back inside this same realm.
      try{
        Object.defineProperty(window,probeKey,{configurable:true,value:{owner,data,voiceState,cleanup}});
        Object.defineProperty(proto,'apply',{...descriptor,value:wrapped});
        movie.addEventListener('loadedmetadata',onMetadata);movie.addEventListener('ended',onEnded);
        observer=new MutationObserver(recordPhase);
        observer.observe(body,{attributes:true,attributeFilter:['data-node','data-phase']});recordPhase();
      }catch(error){cleanup();delete window[probeKey];throw error;}
    },{probeKey,owner});
    await ready(34);
    await frame.locator('#viewport').click();await ready(35);
    await frame.locator('#viewport').click();
    // Normal movie/CardOut and native title completion own all later advances.
    await frame.waitForFunction(()=>document.body.dataset.node==='10450058:37'&&
      document.body.dataset.phase==='complete',null,{timeout:90000});
    visits.push(await state());
    const complete=await frame.evaluate(probeKey=>window[probeKey].voiceState('completed-chart'),probeKey);
    // This is a short observer-only post-completion sample, not a native Wait,
    // source timing assertion or replay. It cannot delay any script command.
    await page.waitForTimeout(250);
    const later=await frame.evaluate(probeKey=>window[probeKey].voiceState('completed-chart-later'),probeKey);
    probe=await frame.evaluate(probeKey=>window[probeKey].data,probeKey);
    const enters=logs.filter(row=>row.text.startsWith('STORY_PLAYER_ENTER ')).map(row=>row.text.split(' ')[1]);
    requireCondition(JSON.stringify(enters)===JSON.stringify(['10450058:35','10450058:36','10450058:37']),
      'Ending did not follow the existing34→35→36→37 document');
    const transitions=logs.filter(row=>row.text.startsWith('STORY_PLAYER_TRANSITION '))
      .map(row=>JSON.parse(row.text.slice('STORY_PLAYER_TRANSITION '.length)));
    const terminal=transitions.find(row=>row.edge==='10450058:37:371');
    requireCondition(transitions.length===4&&terminal?.action==='complete'&&terminal.target===''&&
      terminal.native?.next_scenario_label==='FINISH'&&terminal.native.next_scenario_id===0&&
      !Object.hasOwn(terminal.native,'next_section_id')&&!Object.hasOwn(terminal.native,'next_scene_id'),
      'Runtime terminal FINISH changed');
    requireCondition(logs.some(row=>row.text==='STORY_PLAYER_TITLE 10450058:37 end')&&
      logs.some(row=>row.text.startsWith('STORY_PLAYER_SECTION_COMPLETE section:1045 ')),'CLEAR/own-section completion log missing');
    const titleEntries=logs.filter(row=>row.text.startsWith('STORY_NATIVE_TITLE_ENTRY '))
      .map(row=>JSON.parse(row.text.slice('STORY_NATIVE_TITLE_ENTRY '.length)));
    requireCondition(titleEntries.length===2&&titleEntries[0].stage==='started'&&
      titleEntries[1].stage==='completed'&&titleEntries.every(row=>row.node==='10450058:37'&&row.mode==='normal')&&
      titleEntries[1].gameElapsedMilliseconds>=2500,'Native CLEAR lifecycle missing');
    const ended=probe.movieEvents.find(row=>row.event==='ended'),metadata=probe.movieEvents.find(row=>row.event==='loadedmetadata');
    requireCondition(metadata&&ended?.ended&&Number.isFinite(ended.duration)&&ended.duration>0&&
      ended.currentTime>=ended.duration-.05&&ended.natural[0]===1334&&ended.natural[1]===1334&&
      ended.presentation==='door'&&ended.fit==='cover'&&ended.viewport.width>0&&ended.viewport.height>0,
      'Complete native door/presentation evidence missing');
    const winCalls=probe.calls.filter(row=>row.resource==='bgm_btl_adv_win01');
    const audioContinuity={singleOriginalApply:winCalls.length===1,sameVoiceAtComplete:complete?.sameVoice===true,
      sameVoiceAfterComplete:later?.sameVoice===true,running:complete?.contextState==='running'&&later?.contextState==='running',
      continued:!!complete&&!!later&&later.currentTime>complete.currentTime&&later.contextTime>complete.contextTime,
      unended:complete?.ended===false&&later?.ended===false,originalPlayersRetained:complete?.inOriginalPlayers===true&&later?.inOriginalPlayers===true};
    requireCondition(errors.length===0&&!logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')), 'Player runtime error');
    requireCondition(probe.observationErrors.length===0,'Observation failed; inspect retained probe evidence');
    const audioPassed=Object.values(audioContinuity).every(Boolean);
    result={status:audioPassed?'saved_ending_completed_audio_voice_continues':'saved_ending_completed_audio_continuity_unconfirmed',
      handoff,visits,enters,transitions,titleEntries,movie:{metadata,ended},audioContinuity,
      audioObservation:probe,logs,errors,responses,previewOverrides:false,formalWrites:false,
      screenshotsTaken:0,audioAuditionPerformed:false,newAudioContextOrSidePlayer:false,
      originalPhaseOrTimingAccepted:false,wholeEpisodeAccepted:false};
  }catch(error){
    result={status:'saved_ending_capture_failed',failure:String(error),handoff,visits,probe,logs,errors,responses,
      previewOverrides:false,formalWrites:false,screenshotsTaken:0,audioAuditionPerformed:false};
  }finally{
    // Cleanup is independent of assertions: retain diagnostic data even if
    // playback failed, then remove only this owner's listeners/wrapper/marker.
    if(frame){try{
      const retained=await frame.evaluate(({probeKey,key,owner})=>{
        const value=window[probeKey];let data=null;
        try{if(value?.owner===owner){data=value.data;value.cleanup();}}
        finally{if(value?.owner===owner)delete window[probeKey];if(window[key]?.owner===owner)delete window[key];}
        return data;
      },{probeKey,key,owner});
      if(result)result.audioObservation=retained||result.audioObservation||probe;
    }catch(error){cleanupErrors.push(String(error));}}
    for(const [event,listener] of [['console',onConsole],['pageerror',onError],['response',onResponse]]){
      try{page.off(event,listener);}catch(error){cleanupErrors.push(String(error));}
    }
  }
  return{...result,probeInstallationAttempted:probeInstalled,cleanupErrors,
    cleanupPassed:cleanupErrors.length===0&&(!probeInstalled||result?.audioObservation?.cleanup?.applyRestored===true)};
}
