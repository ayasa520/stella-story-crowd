async page => {
// Function literal for embedding inside the existing run-code QA driver.
// Do not invoke this file as a standalone run-code case: it performs no input
// actions. Every CDP handle, promise and timer is owned by this closure.
function createEntryTrace(page, frame) {
  const meta={captureLimitMs:6000,completionCheckpointMs:5000,completionLimitMs:15000,
    traceBufferKiB:8192,streamLimitBytes:16*1024*1024,streamReadLimitMs:5000,
    maxBufferFraction:0,stopReason:null,hostClock:'Date.now wall time',
    transport:[],eventCounts:{},errors:[],checkpointReached:false};
  const wanted=['toplevel','devtools.timeline','disabled-by-default-devtools.timeline.frame',
    'blink.user_timing','renderer.scheduler','sequence_manager','cc','viz','gpu'];
  let cdp=null,started=false,beginPromise=null,endPromise=null,collection=null,detaching=null;
  let captureTimer,checkpointTimer,completionTimer,stream=null,bytes=0,eof=false;
  let completeResolve,closeResolve,completeValue=null,sessionClosed=false,sessionAbandoned=false;
  const complete=new Promise(resolve=>{completeResolve=resolve;});
  const closed=new Promise(resolve=>{closeResolve=resolve;});
  const chunks=[];
  const note=(stage,detail={})=>{
    const row={stage,hostUnixMs:Date.now(),...detail};
    if(meta.transport.length<32)meta.transport.push(row);
    return row.hostUnixMs;
  };
  const error=(stage,value)=>meta.errors.push({stage,name:value?.name||'Error',message:String(value?.message||value)});
  const bounded=(promise,ms)=>{let timer;return Promise.race([promise,new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(new Error('Diagnostic operation deadline')),ms);
  })]).finally(()=>clearTimeout(timer));};
  const onEvent=({method})=>{
    if(method.startsWith('Tracing.'))meta.eventCounts[method]=(meta.eventCounts[method]||0)+1;
  };
  const onClose=()=>{sessionClosed=true;meta.sessionClosedUnixMs=note('cdp-close');closeResolve(null);};
  const onComplete=result=>{
    if(completeValue)return;
    completeValue=result;
    meta.completeUnixMs=note('named-tracing-complete',{hasStream:!!result.stream,
      traceFormat:result.traceFormat,streamCompression:result.streamCompression,
      dataLossOccurred:result.dataLossOccurred});
    completeResolve(result);
  };
  const onUsage=result=>{
    meta.maxBufferFraction=Math.max(meta.maxBufferFraction,result.percentFull??result.value??0);
    if(started&&meta.maxBufferFraction>=0.85)void stop('buffer-limit');
  };
  function removeTracingListeners(){
    if(!cdp)return;
    cdp.off('event',onEvent);cdp.off('Tracing.tracingComplete',onComplete);
    cdp.off('Tracing.bufferUsage',onUsage);
  }
  function detachOnce(){
    if(detaching)return detaching;
    detaching=(async()=>{
      if(!cdp)return;
      note('detach-request');
      try{await bounded(cdp.detach(),2000);note('detach-complete');}
      catch(value){error('detach',value);}
      finally{cdp.off('close',onClose);}
    })();
    return detaching;
  }
  async function finalize(){
    try{
      // Start this observation budget after the end acknowledgement (or the
      // failed end request). No trace restart or second end request occurs.
      // The first 5s is telemetry, not a premature listener/session teardown.
      const expired=new Promise(resolve=>{
        checkpointTimer=setTimeout(()=>{
          meta.checkpointReached=true;note('completion-5s-checkpoint',{completeSeen:!!completeValue,sessionClosed});
        },meta.completionCheckpointMs);
        completionTimer=setTimeout(()=>{
          note('completion-15s-deadline',{completeSeen:!!completeValue,sessionClosed});resolve(null);
        },meta.completionLimitMs);
      });
      const result=await Promise.race([complete,closed,expired]);
      clearTimeout(checkpointTimer);clearTimeout(completionTimer);
      // Let the installed client emit its generic event after the named event
      // before removing either listener; both paths are counted independently.
      removeTracingListeners();
      if(!result){error('completion',new Error(sessionClosed?'CDP session closed before completion':'No completion within 15s'));}
      else{
        stream=result.stream;meta.dataLossOccurred=result.dataLossOccurred;
        meta.traceFormat=result.traceFormat;meta.streamCompression=result.streamCompression;
        if(!stream||result.streamCompression!=='gzip')throw new Error('Expected gzip trace stream');
        const deadline=Date.now()+meta.streamReadLimitMs;
        while(!eof){
          const remaining=deadline-Date.now();
          if(remaining<=0)throw new Error('Trace stream read deadline');
          const part=await cdp.send('IO.read',{handle:stream,size:65536},{timeout:remaining});
          const chunk=Buffer.from(part.data,part.base64Encoded?'base64':'utf8');
          bytes+=chunk.length;if(bytes>meta.streamLimitBytes)throw new Error('Trace stream size limit');
          chunks.push(chunk);eof=part.eof;
        }
      }
    }catch(value){error('collect',value);}
    finally{
      clearTimeout(captureTimer);clearTimeout(checkpointTimer);clearTimeout(completionTimer);
      removeTracingListeners();
      if(stream){try{await cdp.send('IO.close',{handle:stream},{timeout:2000});}
        catch(value){error('stream-close',value);}}
      await detachOnce();
    }
    // Read and encode the stream exactly once. collect/cleanup return this
    // cached result, never another read, start, end or playback action.
    const usable=eof&&meta.errors.length===0&&!meta.dataLossOccurred&&
      meta.maxBufferFraction<0.85&&meta.stopReason==='node5-ready';
    return {status:usable?'bounded-entry-trace-collected':'trace-incomplete',...meta,
      streamBytes:bytes,eof,traceGzipBase64:eof?Buffer.concat(chunks).toString('base64'):null};
  }
  function stop(reason='node5-ready',readyState=null){
    if(endPromise)return endPromise;
    if(!started)return Promise.resolve({status:'not-started'});
    clearTimeout(captureTimer);meta.stopReason=reason;meta.ready=readyState;
    meta.endRequestedUnixMs=note('end-request',{reason});
    endPromise=(async()=>{
      try{
        await cdp.send('Tracing.end',{}, {timeout:5000});
        meta.endAcknowledgedUnixMs=note('end-ack');
      }catch(value){error('end',value);note('end-error',{name:value.name,message:value.message});}
      finally{if(!collection)collection=finalize().catch(value=>{
        // Also contain final result allocation/encoding errors after the IO
        // finally block, while the formal QA continues independently.
        error('finalize-result',value);
        return {status:'trace-incomplete',...meta,streamBytes:bytes,eof,traceGzipBase64:null};
      });}
      return {status:meta.endAcknowledgedUnixMs?'end-acknowledged':'end-unacknowledged',reason:meta.stopReason};
    })();
    return endPromise;
  }
  function begin(){
    if(beginPromise)return beginPromise;
    if(collection)return Promise.resolve({status:'already-finalized'});
    beginPromise=(async()=>{
      try{
        meta.before=await bounded(frame.evaluate(()=>({now:performance.now(),timeOrigin:performance.timeOrigin,
          node:document.body.dataset.node,phase:document.body.dataset.phase,visibility:document.visibilityState})),2000);
        if(meta.before.node!=='10450054:4'||meta.before.phase!=='ready')throw new Error('Entry trace requires existing node4 ready');
        const sessionRequest=page.context().newCDPSession(page);
        // A raced timeout cannot cancel CDP attachment. If attachment resolves
        // after begin has failed, release that late owned handle as well.
        void sessionRequest.then(async session=>{
          if(sessionAbandoned){note('late-session-detach-request');
            try{await bounded(session.detach(),2000);note('late-session-detach-complete');}
            catch(value){error('late-session-detach',value);}}
        }).catch(()=>{});
        cdp=await bounded(sessionRequest,2000);
        cdp.on('event',onEvent);cdp.on('close',onClose);
        cdp.on('Tracing.tracingComplete',onComplete);cdp.on('Tracing.bufferUsage',onUsage);
        const supported=new Set((await cdp.send('Tracing.getCategories',{}, {timeout:2000})).categories);
        meta.categories=wanted.filter(value=>supported.has(value));
        meta.missingCategories=wanted.filter(value=>!supported.has(value));
        note('start-request');
        await cdp.send('Tracing.start',{transferMode:'ReturnAsStream',streamFormat:'json',streamCompression:'gzip',
          tracingBackend:'chrome',bufferUsageReportingInterval:250,traceConfig:{
            recordMode:'recordUntilFull',traceBufferSizeInKb:meta.traceBufferKiB,
            enableSampling:false,enableSystrace:false,includedCategories:meta.categories,excludedCategories:['*']
          }},{timeout:2000});
        started=true;meta.startAcknowledgedUnixMs=note('start-ack');
        captureTimer=setTimeout(()=>{void stop('time-limit');},meta.captureLimitMs);
        if(meta.maxBufferFraction>=0.85)void stop('buffer-limit');
        // One marker only; no DOM listener/global stash or per-frame observer.
        await bounded(frame.evaluate(()=>performance.mark('p30-entry:trace-begin').startTime),1000)
          .then(value=>{meta.beginMarkerMs=value;},value=>{error('begin-marker',value);});
        return {status:'started'};
      }catch(value){
        sessionAbandoned=true;
        error('begin',value);note('begin-error',{name:value.name,message:value.message});
        if(started)await stop('begin-error');
        else{removeTracingListeners();await detachOnce();}
        return {status:'not-started'};
      }
    })();
    return beginPromise;
  }
  async function collect(){
    // Diagnostic failures are data. No exception escapes into the identity QA.
    if(beginPromise)await beginPromise;
    if(started&&!endPromise)await stop('collect-without-ready-stop');
    else if(endPromise)await endPromise;
    if(collection)return collection;
    if(!collection)collection=(async()=>{
      removeTracingListeners();await detachOnce();
      return {status:'trace-not-started',...meta,streamBytes:0,eof:false,traceGzipBase64:null};
    })();
    return collection;
  }
  async function cleanup(){
    const result=await collect();clearTimeout(captureTimer);return result;
  }
  return {begin,stop,collect,cleanup};
}


  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-four-model-identities-publication-20261112-v1';
  const events=[],shots=[],logs=[];
  page.on('console',message=>{const value=message.text();if(/^(MODEL_READY|STORY_MOTION_BINDING|STORY_PLAYER_TRANSITION|STORY_CHOICE_COMMIT|STORY_NORMAL_FRAME_HITCH) /.test(value))logs.push(value);});
  const player=()=>page.frames().find(f=>f.url().includes('/player/player.html'));
  const ready=async(scene,node)=>{
    await page.waitForFunction(expected=>{const b=document.querySelector('iframe')?.contentDocument?.body;return b?.dataset.node===expected&&['ready','choice'].includes(b.dataset.phase);},scene+':'+node,{timeout:20000});
    events.push(await player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,wall:performance.now()})));
  };
  const shot=async(scene,node)=>{const path=output+'/formal-'+scene+'-'+node+'.png';await page.screenshot({path});shots.push({scene,node,path});};
  let trace=null,traceResult=null;
  try{
    await page.goto('http://127.0.0.1:5192/?scene=10450054&node=3');
    await ready(10450054,3);await page.locator('#advance').click();await ready(10450054,4);await shot(10450054,4);
    trace=createEntryTrace(page,player());await trace.begin();
    await page.locator('#advance').click();await ready(10450054,5);
    await trace.stop('node5-ready',events[events.length-1]);
    await page.locator('#advance').click();await ready(10450054,6);await shot(10450054,6);
    await page.locator('#advance').click();await ready(10450054,7);
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=13');
    const targets=new Set([14,15,16,17,19,20,21,22,23,24,25,28]);
    for(let node=13;node<=29;node++){
      await ready(10450056,node);if(targets.has(node))await shot(10450056,node);
      if(node===29)break;
      if(node===22){
        // Exercise the recorded left choice using the normal keyboard input.
        // The unrecorded right branch remains unavailable and is never filled.
        await player().locator('#viewport').press('ArrowLeft');
        await player().locator('#viewport').press('Enter');
      }else await page.locator('#advance').click();
    }
    if(!logs.some(line=>line.startsWith('STORY_CHOICE_COMMIT 10450056:22:222 left ')))throw new Error('Recorded left choice was not committed');
    if(shots.length!==14)throw new Error('Missing formal character snapshot');
  }finally{
    if(trace)traceResult=await trace.cleanup();
  }
  return {status:'formal_four_model_character_routes_passed',events,shots,logs,trace:traceResult,previewOverrides:false,actingAccepted:false};

}
