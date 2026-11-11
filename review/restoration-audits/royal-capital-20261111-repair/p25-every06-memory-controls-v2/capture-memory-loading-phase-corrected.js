async page=>{
  // This function is prepared for root's explicitly owned single browser.
  // It never launches a browser, changes formal data, wraps media/fetch, seeks
  // audio, injects delay, or modifies the player's clock/rate. Named fixtures
  // must already be approved in the read-only adapter registry.
  const resource='bgm_adv_every06_cd3_10',examples=["p25-every06-fade0-v37","p25-every06-fade1-v37"],baseURL='http://127.0.0.1:5189';
  const packetSha='e5d577f7e44bde637b99f368ae516942728a70d0c575ef53c21c22b3b6478a5c',out="/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/audio/p25-p26-bgm-evidence-v1/p25-every06-envelope-v1/executable-memory-v2/";
  const results=[],logs=[],network=[],errors=[],responseTasks=[];
  let example='',cdp=null,frame=null;
  const consoleListener=message=>{
    const text=message.text();if(text.startsWith('STORY_'))logs.push({example,hostWall:Date.now(),type:message.type(),text});
    if(text.startsWith('STORY_PLAYER_ERROR'))errors.push({example,error:text});
  };
  const requestListener=request=>{
    if(request.url().includes('/music/')||request.url().includes('/api/music/'))
      network.push({example,type:'request',hostWall:Date.now(),url:request.url(),method:request.method()});
  };
  const responseListener=response=>{
    if(!response.url().includes('/music/')&&!response.url().includes('/api/music/'))return;
    const named=example;network.push({example:named,type:'response',hostWall:Date.now(),url:response.url(),status:response.status()});
    responseTasks.push(response.finished().then(error=>network.push({example:named,type:'body-finished',hostWall:Date.now(),url:response.url(),error:error?String(error):null})));
  };
  const errorListener=error=>errors.push({example,error:String(error)});
  page.on('console',consoleListener);page.on('request',requestListener);page.on('response',responseListener);page.on('pageerror',errorListener);
  const stopObserver=async()=>{
    if(!frame)return null;
    return frame.evaluate(()=>{const a=globalThis.__p25LoadingAudit;if(!a)return null;a.remove();return {samples:a.samples,prepared:a.prepared,timing:a.timing,notes:a.notes};});
  };
  const observe=async()=>{
    cdp=await page.context().newCDPSession(page);const contexts=[];
    cdp.on('Runtime.executionContextCreated',event=>contexts.push(event.context));await cdp.send('Runtime.enable');
    const tree=await cdp.send('Page.getFrameTree');const playerFrame=tree.frameTree.childFrames.find(row=>row.frame.url.includes('/player/player.html'));
    const context=contexts.find(row=>row.auxData?.frameId===playerFrame.frame.id&&row.auxData.isDefault);
    if(!context)throw Error('Default production iframe context missing');
    const prototype=await cdp.send('Runtime.evaluate',{contextId:context.id,awaitPromise:true,
      expression:"import('/studio/music_player.js').then(module=>module.StoryMusicPlayer.prototype)"});
    const objects=await cdp.send('Runtime.queryObjects',{prototypeObjectId:prototype.result.objectId});
    const installed=await cdp.send('Runtime.callFunctionOn',{objectId:objects.objects.objectId,returnByValue:true,
      functionDeclaration:`function(){
        if(this.length!==1)throw Error('Expected exactly one actual StoryMusicPlayer');
        const m=this[0];if(m.current||m.loading||m.buffers.has('bgm_adv_every06_cd3_10'))throw Error('Silent predecessor unexpectedly already owns/prepares target BGM');
        const a=globalThis.__p25LoadingAudit={player:m,samples:[],prepared:[],timing:[],notes:[],promises:new Set(),ids:new WeakMap(),nextId:1};
        const snap=()=>({wall:performance.now(),node:document.body.dataset.node,phase:document.body.dataset.phase,
          game:m.clock.snapshot(),contextState:m.context?.state,audioContextTime:m.context?.currentTime});
        const onTiming=event=>a.timing.push({...snap(),observationStage:'synchronous_player_timing_event',detail:{...event.detail}});
        document.addEventListener('stella-player-timing',onTiming);
        const unsubscribe=m.clock.subscribe(triggerSnapshot=>{
          const triggerAt=performance.now(),triggerGeneration=m.generation;
          // This subscriber existed before the real ramp subscriber. Do not
          // read a pre-ramp gain and label it with the current frame. The
          // microtask runs after this clock tick's synchronous listeners, with
          // no production listener reordered and no clock/gain/media write.
          queueMicrotask(()=>{
          if(a.closed)return;
          const observedSnapshot=m.clock.snapshot();
          const sameSharedFrame=triggerSnapshot.frame===observedSnapshot.frame;
          const sameGameSeconds=triggerSnapshot.gameSeconds===observedSnapshot.gameSeconds;
          if(!sameSharedFrame||!sameGameSeconds)a.notes.push({kind:'observation_frame_mismatch',triggerSnapshot,observedSnapshot});
          if(a.samples.length>5000)return;
          const promise=m.buffers.get('bgm_adv_every06_cd3_10');
          if(promise&&!a.promises.has(promise)){
            a.promises.add(promise);const attached=snap();
            a.prepared.push({type:'existing-buffer-promise-observer-attached',...attached});
            promise.then(value=>a.prepared.push({type:'buffer-promise-fulfilled-observed',...snap(),
              resource:value.metadata.resource,bufferDuration:value.buffer.duration,bufferSamples:value.buffer.length,bufferRate:value.buffer.sampleRate,
              note:'Passive then observer; callback time is an observation bound, not proof of exact earlier settlement or ordering with other promise continuations.'}),
              error=>a.prepared.push({type:'buffer-promise-rejected-observed',...snap(),error:String(error)}));
          }
          const voices=[...m.players].map(voice=>{if(!a.ids.has(voice))a.ids.set(voice,a.nextId++);
            return {id:a.ids.get(voice),resource:voice.metadata.resource,beganAudioTime:voice.began,currentTime:voice.currentTime,
              gain:voice.volume,ended:!!voice.ended,loop:voice.source.loop,loopStart:voice.source.loopStart,loopEnd:voice.source.loopEnd};});
          a.samples.push({...snap(),observationStage:'microtask_after_shared_clock_synchronous_listeners',triggerSnapshot:{...triggerSnapshot},observedSnapshot,sameSharedFrame,sameGameSeconds,triggerAt,triggerGeneration,generationUnchanged:triggerGeneration===m.generation,generation:m.generation,loading:m.loading&&{...m.loading},pendingFade:!!m.cancelFade,
            currentResource:m.current?.resource||'',voices,semanticText:document.querySelector('#accessibleText').textContent,
            cardOpacity:getComputedStyle(document.querySelector('#cardMotion')).opacity});
          });
        });
        a.remove=()=>{a.closed=true;unsubscribe();document.removeEventListener('stella-player-timing',onTiming);};
        return {instances:this.length,timeOrigin:performance.timeOrigin,clock:m.clock.snapshot(),note:'Passive observer only; no media, fetch, clock or transport APIs replaced.'};
      }`});
    if(installed.exceptionDetails)throw Error(JSON.stringify(installed.exceptionDetails));
    return {context,contexts:contexts.map(row=>({id:row.id,name:row.name,origin:row.origin,auxData:row.auxData})),playerFrame:playerFrame.frame,installed:installed.result.value};
  };
  let failure=null;
  try{
    for(const name of examples){
      example=name;const url=baseURL+'/?scene=10170002&node=7&nativePreview='+name;
      // Fail fast if root has not activated the exact bounded fixture. This
      // probe deliberately performs no server restart or registry mutation.
      const check=await page.request.get(baseURL+'/program?scene=10170002&node=7&nativePreview='+name);
      if(!check.ok())throw Error('Named bounded fixture unavailable: '+check.status());
      const program=await check.json();const compiledNodes=program.nodes.filter(row=>/^10170002:(7|8|9)$/.test(row.id));const node=program.nodes.find(n=>n.id==='10170002:8');
      const fade=name.includes('fade0')?0:1;
      if(program.review_only_overrides?.packetSha256!==packetSha||program.review_only_overrides?.exampleId!==name||program.review_only_overrides?.persisted!==false)throw Error('Exact v2 private fixture identity mismatch');
      if(program.start!=='10170002:7'||node.music.resource!==resource||node.music.fade!==fade||node.music.restart!==false)
        throw Error('Compiled memory-only fixture differs from named hypothesis');
      await page.goto(url);
      await page.waitForFunction(()=>{const body=document.querySelector('iframe')?.contentDocument?.body;return body?.dataset.node==='10170002:7'&&body.dataset.phase==='ready';},null,{timeout:20000});
      frame=page.frames().find(row=>row.url().includes('/player/player.html'));
      if(!frame)throw Error('Actual production iframe missing after atomic predecessor readiness');
      await frame.waitForFunction(()=>document.body.dataset.node==='10170002:7'&&document.body.dataset.phase==='ready',null,{timeout:20000});
      await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({type:'stella-player-action',action:'language',value:'ja'},location.origin));
      await frame.waitForFunction(()=>document.querySelector('#language').value==='ja');
      const observer=await observe();
      await frame.locator('#viewport').click({position:{x:220,y:350}});
      await frame.waitForFunction(()=>{
        const a=globalThis.__p25LoadingAudit,m=a.player;
        return document.body.dataset.node==='10170002:8'&&document.body.dataset.phase==='ready'&&
          m.current?.resource==='bgm_adv_every06_cd3_10'&&m.current.voice.currentTime>=2.3&&!m.cancelFade;
      },null,{timeout:20000});
      const at8=await frame.evaluate(()=>{const m=globalThis.__p25LoadingAudit.player;return {node:document.body.dataset.node,phase:document.body.dataset.phase,
        text:document.querySelector('#accessibleText').textContent,resource:m.current.resource,voiceId:globalThis.__p25LoadingAudit.ids.get(m.current.voice),beganAudioTime:m.current.voice.began,contextTime:m.context.currentTime,audioTime:m.current.voice.currentTime,clock:m.clock.snapshot()};});
      await frame.locator('#viewport').click({position:{x:220,y:350}});
      await frame.waitForFunction(()=>document.body.dataset.node==='10170002:9'&&document.body.dataset.phase==='ready',null,{timeout:20000});
      const at9=await frame.evaluate(()=>{const m=globalThis.__p25LoadingAudit.player;return {node:document.body.dataset.node,phase:document.body.dataset.phase,
        text:document.querySelector('#accessibleText').textContent,resource:m.current?.resource,voiceId:globalThis.__p25LoadingAudit.ids.get(m.current?.voice),beganAudioTime:m.current?.voice.began,contextTime:m.context?.currentTime,audioTime:m.current?.voice.currentTime,clock:m.clock.snapshot()};});
      if(at8.voiceId!==at9.voiceId||at8.beganAudioTime!==at9.beganAudioTime||!(at9.contextTime>at8.contextTime))throw Error('Node9 did not retain the same naturally advancing MusicVoice');
      const observed=await stopObserver();results.push({example:name,fadeHypothesis:fade,url,compiledNodes,overrides:program.review_only_overrides,observer,at8,at9,...observed});
      await cdp.detach();cdp=null;frame=null;
    }
  }catch(error){failure={name:error.name,message:String(error.message),stack:error.stack};}
  finally{
    if(frame){try{results.push({example,partial:true,observed:await stopObserver()});}catch(error){errors.push({example,error:'observer teardown: '+String(error)});}}
    if(cdp)await cdp.detach();await Promise.allSettled(responseTasks);
    await page.goto('about:blank');
    page.off('console',consoleListener);page.off('request',requestListener);page.off('response',responseListener);page.off('pageerror',errorListener);
  }
  const payload={failure,results,logs,network,pageErrors:errors,productionPath:'/player/player.html',
    observerOnly:true,autoplayPolicyChanged:false,mediaAPIsReplaced:false,artificialLoadDelay:false,nativeFieldsChanged:0,
    screenshotsTaken:false,originalPhaseOrWaitRecovered:false,sourceRecordingSpeedRecovered:false,priorOriginalMusicMixRestored:false,
    note:'Root must close the sole browser immediately after capture and independently verify source/formal hashes and OS/CLI zero.'};
  const download=page.waitForEvent('download',{timeout:60000});
  await page.evaluate(async payload=>{const blob=await new Response(new Blob([JSON.stringify(payload)],{type:'application/json'}).stream().pipeThrough(new CompressionStream('gzip'))).blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='actual-bgm-memory-v2.json.gz';a.click();},payload);
  await (await download).saveAs(out+'actual-bgm-memory-v2.json.gz');
  return {failure,variants:results.map(row=>({example:row.example,partial:row.partial||false,samples:row.samples?.length,timingEvents:row.timing?.length,at8:row.at8,at9:row.at9})),pageErrors:errors,rawPayload:'actual-bgm-memory-v2.json.gz',pageBlank:true,needsImmediateBrowserClose:true};
}
