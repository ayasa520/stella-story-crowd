// Extracted from the actually closed cde844 saved-voice driver's retained
// media closure. Only IDs, current pendingPlay, revision/blob identity and
// compressed-byte proof are adapted. This function locates an existing owner;
// it constructs no Audio/context/decoder, samples no clock and wraps no method.
export async function installSavedVoiceObserver(cue){
  const {visualFrameClock:clock}=await import('/studio/visual_frame_clock.js');
  const owner=clock.rateOwner,channel=owner?.dialogueVoice,audio=channel?.audio;
  if(document.body.dataset.node!==cue.beforeId||document.body.dataset.phase!=='ready'||
      !owner||owner.visualClock!==clock||owner.constructor.name!=='StoryActor'||audio!==owner.audio||
      !(audio instanceof HTMLAudioElement)||channel.voice||!audio.paused||channel.cancelPrepare||
      channel.cancelPlay||channel.pendingPlay||channel.blockedPlayback)
    throw Error('Existing idle StoryActor dialogue channel unavailable at predecessor');
  const sourceURL=new URL('/asset/'+cue.member.split('/').map(encodeURIComponent).join('/'),location.origin);
  sourceURL.searchParams.set('revision',cue.revision);
  const events=[],failures=[],removals=[],startedAt=performance.now();
  let active=true,overflow=false,settled=false,resolveEnd,rejectEnd;
  let diagnosticMilliseconds=0,maximumDiagnosticMilliseconds=0;
  const naturalEnd=new Promise((resolve,reject)=>{resolveEnd=resolve;rejectEnd=reject;});naturalEnd.catch(()=>{});
  const identity=()=>clock.rateOwner===owner&&owner.dialogueVoice===channel&&owner.audio===audio&&channel.audio===audio;
  const sourceIdentity=()=>channel.objectUrl
    ?audio.currentSrc===channel.objectUrl&&channel.objectUrl.startsWith('blob:'+location.origin+'/')
    :audio.currentSrc===sourceURL.href;
  const snapshot=()=>({performanceMs:performance.now(),timeOrigin:performance.timeOrigin,
    node:document.body.dataset.node,phase:document.body.dataset.phase,sameOwnerAndAudio:identity(),
    model:owner.detail?.id||null,generation:channel.generation,voice:channel.voice?{...channel.voice}:null,
    pendingPrepare:Boolean(channel.cancelPrepare),delayedPlay:Boolean(channel.cancelPlay),
    pendingPlay:Boolean(channel.pendingPlay),blockedPlayback:Boolean(channel.blockedPlayback),
    objectUrl:channel.objectUrl||null,sourceIdentity:sourceIdentity(),
    audio:{src:audio.src,currentSrc:audio.currentSrc,duration:Number.isFinite(audio.duration)?audio.duration:null,
      currentTime:audio.currentTime,paused:audio.paused,ended:audio.ended,readyState:audio.readyState,
      networkState:audio.networkState,playbackRate:audio.playbackRate,volume:audio.volume,muted:audio.muted,loop:audio.loop,
      error:audio.error?{code:audio.error.code,message:audio.error.message}:null}});
  const record=(kind,extra={})=>{
    if(!active)return;
    const began=performance.now();
    try{
      const row={kind,...snapshot(),...extra};events.push(row);
      // The crossing event is retained before failing coverage. No original
      // error or media payload is shortened to make a byte/event budget pass.
      if(!identity())throw Error('Retained original voice channel identity changed');
      if(events.length>cue.maximumEvents||performance.now()-startedAt>120000){
        overflow=true;throw Error('Voice observation bound reached; complete crossing event retained');
      }
      if(kind==='error')throw Error('Original media error '+JSON.stringify(row.audio.error));
      if(kind==='ended'&&row.node===cue.targetId&&row.voice?.cue===cue.cue&&row.sourceIdentity&&!settled){
        settled=true;resolveEnd(row);
      }
    }catch(error){failures.push({error:String(error),stack:error.stack});if(!settled){settled=true;rejectEnd(error);}}
    finally{const elapsed=performance.now()-began;diagnosticMilliseconds+=elapsed;
      maximumDiagnosticMilliseconds=Math.max(maximumDiagnosticMilliseconds,elapsed);}
  };
  const gesture=event=>record('pointerdown',{trusted:event.isTrusted,target:event.target.id,
    button:event.target.closest('button')?.id||'',withinViewport:document.getElementById('viewport').contains(event.target)});
  function cleanup(){
    let final=null;const errors=[];
    try{final=snapshot();}catch(error){errors.push({error:String(error),stack:error.stack});}
    finally{
      active=false;
      for(const remove of removals.reverse())try{remove();}catch(error){errors.push({error:String(error),stack:error.stack});}
      if(!settled){settled=true;rejectEnd(Error('Owned voice observation removed before natural end'));}
    }
    return {final,events:[...events],errors,failures:[...failures],overflow,listenerCount:removals.length,
      listenersRemoved:errors.length===0,methodsWrapped:0,globalSlotsCreated:0,
      overhead:{diagnosticMilliseconds,maximumDiagnosticMilliseconds,
        qualification:'Observer callback work only; no claim of unchanged scheduling or source phase'}};
  }
  async function proveSource(){
    if(!identity()||!sourceIdentity()||channel.voice?.cue!==cue.cue||channel.voice.member!==cue.member)
      throw Error('Current original cue/source identity is not the bound target');
    const current=snapshot();
    if(!channel.objectUrl)return {mode:'original-media-url',current,expectedURL:sourceURL.href,
      providerDigestRequired:true,extraNetworkRead:false};
    // Reading the ORIGINAL retained blob is a byte digest, not decoding or
    // reloading an audio element. It cannot choose a different media source.
    // This completes before normal next revokes that owner's object URL.
    const retained=channel.objectUrl,reply=await fetch(retained);
    if(!reply.ok)throw Error('Original retained blob read failed '+reply.status);
    const bytes=await reply.arrayBuffer(),digest=await crypto.subtle.digest('SHA-256',bytes);
    const sha256=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(!identity()||channel.objectUrl!==retained||audio.currentSrc!==retained)
      throw Error('Original blob ownership changed during its byte proof');
    if(bytes.byteLength!==cue.opus.bytes||sha256!==cue.opus.sha256)
      throw Error('Original media blob does not match the bound default Opus bytes');
    return {mode:'original-prefetched-blob',current,blobURL:retained,bytes:bytes.byteLength,sha256,
      mimeType:reply.headers.get('content-type'),providerDigestRequired:true,extraNetworkRead:false,
      originalBlobReadOnly:true,mediaDecodedByObserver:false};
  }
  const api={snapshot,installationFailure:null,waitForNaturalEnd:()=>naturalEnd,
    result:()=>({events:[...events],failures:[...failures],overflow,sourceURL:sourceURL.href,
      overhead:{diagnosticMilliseconds,maximumDiagnosticMilliseconds}}),proveSource,cleanup};
  try{
    for(const kind of ['loadstart','loadedmetadata','durationchange','loadeddata','canplay','play','playing',
        'timeupdate','pause','ended','error','waiting','stalled','emptied','seeking','seeked']){
      const handler=()=>record(kind);removals.push(()=>audio.removeEventListener(kind,handler));
      audio.addEventListener(kind,handler);
    }
    removals.push(()=>document.removeEventListener('pointerdown',gesture,true));
    document.addEventListener('pointerdown',gesture,true);
  }catch(error){
    api.installationFailure={error:String(error),stack:error.stack};failures.push(api.installationFailure);
  }
  return api;
}
