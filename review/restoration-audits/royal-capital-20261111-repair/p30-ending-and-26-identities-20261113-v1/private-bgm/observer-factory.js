(async function installPrivateMusicObserver(){
  'use strict';
  const slot='__stellaKinpaku02PrivateMusicV1',resource='bgm_adv_kinpaku02_cd2_18';
  if(Object.getOwnPropertyDescriptor(globalThis,slot))throw Error('Private music slot occupied');
  // /player/music_player.js re-exports this exact shared class. Importing it
  // obtains the existing module identity; it does not construct a transport,
  // AudioContext, source, buffer, or a second player.
  const [{StoryMusicPlayer},{MusicVoice}]=await Promise.all([
    import('/studio/music_player.js'),import('/studio/music_voice.js')]);
  if(Object.getOwnPropertyDescriptor(globalThis,slot))throw Error('Private music slot occupied after imports');
  const ownerProof={},events=[],errors=[],patches=[],voices=new Set(),contexts=new Set();
  let owner=null,active=true;
  const describe=error=>String(error?.message||error);
  const record=(kind,detail={})=>{
    try{if(events.length<160)events.push({kind,performanceMs:performance.now(),
      node:document.body.dataset.node,phase:document.body.dataset.phase,...detail});}
    catch(error){if(errors.length<16)errors.push(describe(error));}
  };
  const observe=callback=>{try{callback();}catch(error){if(errors.length<16)errors.push(describe(error));}};
  const voiceInfo=voice=>{
    if(!voice)return null;
    const buffer=voice.source.buffer,context=voice.context,metadata=voice.metadata;
    const nativeDuration=metadata.samples/metadata.sample_rate;
    // Opus preview resampling and decodeAudioData context resampling can each
    // quantize a boundary by a sample. The catalog preview rate is 48000, but
    // the AudioBuffer is deliberately NOT required to have that sample rate.
    const toleranceSeconds=1/48000+1/context.sampleRate+1e-9;
    return {metadata:{...metadata},nativeDuration,bufferDuration:buffer.duration,
      bufferRate:buffer.sampleRate,bufferLength:buffer.length,channels:buffer.numberOfChannels,
      contextRate:context.sampleRate,contextState:context.state,audioTime:context.currentTime,
      began:voice.began,currentTime:voice.currentTime,ended:Boolean(voice.ended),
      loop:voice.source.loop,loopStart:voice.source.loopStart,loopEnd:voice.source.loopEnd,
      volume:voice.volume,toleranceSeconds,
      durationWithinResamplingTolerance:Math.abs(buffer.duration-nativeDuration)<=toleranceSeconds,
      nativeLoopValid:metadata.loop_start>=0&&metadata.loop_start<metadata.loop_end&&metadata.loop_end<=nativeDuration,
      sourceLoopMatches:voice.source.loop===metadata.loop&&voice.source.loopStart===metadata.loop_start&&voice.source.loopEnd===metadata.loop_end};
  };
  const stateChange=event=>record('context-statechange',{state:event.target.state,audioTime:event.target.currentTime});
  const gesture=event=>record('pointerdown',{trusted:event.isTrusted,target:event.target.id,
    contextState:owner?.context?.state||null,audioTime:owner?.context?.currentTime??null});
  function wrap(prototype,key,before,after){
    const descriptor=Object.getOwnPropertyDescriptor(prototype,key);
    if(!descriptor||typeof descriptor.value!=='function'||!descriptor.configurable)throw Error('Unwrappable '+key);
    const original=descriptor.value;
    const wrapped=function(...args){
      if(active&&before)observe(()=>before(this,args));
      // One and only one invocation. The original Promise/value/throw crosses
      // unchanged; no then/catch, replay, await, source start, or resume is added.
      let returned=false;
      try{const value=Reflect.apply(original,this,args);returned=true;return value;}
      finally{if(returned&&active&&after)observe(()=>after(this,args));}
    };
    Object.defineProperty(prototype,key,{...descriptor,value:wrapped});
    patches.push({prototype,key,descriptor,wrapped});
  }
  function snapshot(){
    return {performanceMs:performance.now(),timeOrigin:performance.timeOrigin,
      node:document.body.dataset.node,phase:document.body.dataset.phase,ownerFound:Boolean(owner),
      owner:owner?{active:owner.active,loading:owner.loading,currentResource:owner.current?.resource||null,
        players:owner.players.size,cancelFade:Boolean(owner.cancelFade),muted:owner.muted,
        contextState:owner.context?.state||null,audioTime:owner.context?.currentTime??null,
        outputGain:owner.output?.gain.value??null,configuredVolume:owner.settings?.bgm_volume,
        current:voiceInfo(owner.current?.voice)}:null,
      voices:[...voices].map(voiceInfo),events:[...events],errors:[...errors]};
  }
  function uninstall(reason){
    let result=null,snapshotError=null;const conflicts=[];
    // Snapshot errors must not strand prototype replacements. A conflicting
    // foreign replacement is reported rather than overwritten during cleanup.
    try{result=snapshot();}catch(error){snapshotError=describe(error);}
    finally{
      active=false;
      for(const patch of [...patches].reverse()){
        try{const current=Object.getOwnPropertyDescriptor(patch.prototype,patch.key);
        if(current?.value===patch.wrapped&&current.configurable===patch.descriptor.configurable&&
          current.enumerable===patch.descriptor.enumerable&&current.writable===patch.descriptor.writable)
          Object.defineProperty(patch.prototype,patch.key,patch.descriptor);
        else conflicts.push('descriptor '+patch.key);}catch(error){conflicts.push(describe(error));}
      }
      try{document.removeEventListener('pointerdown',gesture,true);}catch(error){conflicts.push(describe(error));}
      for(const context of contexts)try{context.removeEventListener('statechange',stateChange);}catch(error){conflicts.push(describe(error));}
      try{const current=Object.getOwnPropertyDescriptor(globalThis,slot);
        if(current?.value?.ownerProof===ownerProof)delete globalThis[slot];
        else if(current)conflicts.push('private slot');}catch(error){conflicts.push(describe(error));}
    }
    return {reason,result,snapshotError,cleanup:{allRestored:!conflicts.length,conflicts},
      rootReviewed:false,rootConfirmed:false};
  }
  try{
    wrap(StoryMusicPlayer.prototype,'apply',(receiver,args)=>{
      if(args[0]!==resource)return;
      if(owner&&owner!==receiver){errors.push('More than one matching StoryMusicPlayer');return;}
      owner=receiver;record('apply',{resource:args[0],options:{...args[1]}});
    });
    wrap(StoryMusicPlayer.prototype,'resume',null,receiver=>{
      if(receiver===owner)record('resume-return',{contextState:owner.context?.state||null,
        audioTime:owner.context?.currentTime??null});
    });
    wrap(MusicVoice.prototype,'start',null,voice=>{
      if(!owner?.players.has(voice)||voice.metadata.resource!==resource)return;
      voices.add(voice);
      if(!contexts.has(voice.context)){contexts.add(voice.context);voice.context.addEventListener('statechange',stateChange);}
      record('original-voice-start-return',{voice:voiceInfo(voice)});
    });
    document.addEventListener('pointerdown',gesture,true);
    Object.defineProperty(globalThis,slot,{configurable:true,value:{ownerProof,snapshot,uninstall}});
    return {status:'private_music_observer_installed',slot,ownerProof,methodCount:patches.length,
      rootReviewed:false,rootConfirmed:false};
  }catch(error){
    const receipt=uninstall('partial-install-failure');
    const failure=Error(describe(error)+' '+JSON.stringify(receipt));failure.observerCleanup=receipt;throw failure;
  }
})
