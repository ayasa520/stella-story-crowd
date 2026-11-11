import {MusicVoice} from './music_voice.js';
import {visualFrameClock} from './visual_frame_clock.js';

// Native ADVFuncs.PlayBGM defaults to a one-second crossfade and reset=false.
// Keep transport state separate from the editor's raw command and from cue
// auditioning: selecting another dialogue must not recreate the same track.
export class StoryMusicPlayer {
  constructor({clock=visualFrameClock}={}){
    this.clock=clock;this.cancelFade=null;
    this.active=false;this.current=null;this.loading=null;this.generation=0;
    this.players=new Set();this.buffers=new Map();this.applied='';this.muted=false;
  }
  setup(settings){this.settings=settings;}
  resume(){
    if(this.context?.state!=='suspended')return;
    // AudioContext.resume() may remain pending until a trusted interaction.
    // That permission boundary must never hold node entry or hide its image.
    // Keep the real audio clock suspended, then retry from the next player
    // interaction; do not add a script Wait or alter the authored music cue.
    this.context.resume().then(()=>console.info('STORY_BGM_CONTEXT',this.context.state),
      error=>console.warn('STORY_BGM_CONTEXT_RESUME',String(error)));
  }
  async prepare(resource){
    if(!this.context){
      this.context=new AudioContext();this.output=this.context.createGain();this.output.connect(this.context.destination);
      this.output.gain.value=this.muted?0:1;
    }
    this.resume();
    if(!this.buffers.has(resource)){
      // A failed load must be retryable. Successful buffers belong to this
      // player, not to a scene/node, so inherited music keeps one sample clock.
      const loading=Promise.all([fetch('/api/music/'+encodeURIComponent(resource)),fetch('/music/'+encodeURIComponent(resource))])
        .then(async([info,audio])=>{
          if(!info.ok||!audio.ok)throw new Error('BGM 读取失败：'+resource);
          const [metadata,buffer]=await Promise.all([info.json(),audio.arrayBuffer().then(raw=>this.context.decodeAudioData(raw))]);
          if(metadata.startup_events.length)console.warn('STORY_BGM_STARTUP_UNRESOLVED',JSON.stringify({resource,events:metadata.startup_events,
            note:'Original sequence-start behavior remains under investigation; preserving zero-offset introduction.'}));
          return {metadata,buffer};
        }).catch(error=>{this.buffers.delete(resource);throw error;});
      this.buffers.set(resource,loading);
    }
    return this.buffers.get(resource);
  }
  setMuted(muted){
    if(this.muted===muted)return;this.muted=muted;
    // Muting must not interfere with an in-flight crossfade or pending load.
    // A separate output gain leaves each voice's ramp and sample clock intact,
    // including sources prepared while the scene-title chart is muted.
    if(this.output)this.output.gain.value=muted?0:1;
    console.info('STORY_BGM_MUTE',JSON.stringify({muted,resource:this.current?.resource,time:this.current?.voice.currentTime}));
  }
  async apply(resource,{fade,restart=false,key='',start=false}){
    if(resource===null)throw new Error('BGM 来源有分歧，请先选择预览入线');
    if(start)this.active=true;
    if(!this.active)return;
    if(!resource&&!this.current&&!this.loading)return;
    if(resource&&this.current?.resource===resource&&(!restart||key===this.applied)){
      // A later request for the still-playing track supersedes a different
      // track that is only loading. Preserve this source's clock, cancel the
      // pending replacement, and restore any partially faded gain smoothly.
      if(this.loading){
        this.loading=null;const generation=++this.generation;
        this.ramp(this.current.voice,[...this.players].filter(voice=>voice!==this.current.voice)
          .map(voice=>({voice,volume:voice.volume})),fade,generation);
      }
      if(start)this.resume();return;
    }
    console.info('STORY_BGM_COMMAND',JSON.stringify({resource,fade,restart,key}));
    const generation=++this.generation,previous=[...this.players].map(voice=>({voice,volume:voice.volume}));
    this.loading=resource?{resource,generation}:null;
    let next=null;
    if(resource){
      let prepared;
      try{prepared=await this.prepare(resource);}
      catch(error){if(generation!==this.generation)return;this.loading=null;throw error;}
      // Stop or another command may arrive during fetch/decode. Never create
      // an audible source from the superseded operation, including after Stop.
      if(generation!==this.generation){console.info('STORY_BGM_CANCELLED',resource);return;}
      this.loading=null;
      const {metadata,buffer}=prepared;
      next=new MusicVoice(this.context,this.output,buffer,metadata,fade?0:this.settings.bgm_volume,()=>{
        this.players.delete(next);if(this.current?.voice===next)this.current=null;
      });
      this.players.add(next);next.start();
      console.info('STORY_BGM_PLAY',JSON.stringify({resource,loop:metadata.loop,start:metadata.loop_start,end:metadata.loop_end,
        samples:metadata.samples,sampleRate:metadata.sample_rate,audioTime:this.context.currentTime,milliseconds:performance.now()}));
    }
    this.current=next?{voice:next,resource}:null;this.applied=key;
    this.ramp(next,previous,fade,generation);
  }
  ramp(next,previous,fade,generation){
    this.cancelRamp();
    const began=this.clock.now(),initial=next?.volume||0;
    // Original ProcCrossFade.MoveNext (0x1dd7768) interpolates both gains and
    // advances its elapsed value with Unity Time.deltaTime (0x1dd794c). Use
    // the same bounded game-frame sample as Normal actors/cards, including
    // the existing preview-rate owner. The Web Audio source keeps its own
    // sample clock: a visual hitch must not seek, restart or slow the music.
    // Each ramp owns one removable subscription. A superseding command or
    // Stop cancels that subscription without disposing the shared clock or
    // leaving a callback attached after this player's voices are released.
    console.info('STORY_BGM_FADE_BEGIN',JSON.stringify({generation,fade,
      gameSeconds:began,clock:this.clock.snapshot?.(),audioTime:next?.currentTime}));
    const tick=()=>{
      if(generation!==this.generation){this.cancelRamp();return;}
      const elapsed=this.clock.now()-began,progress=fade?Math.min(1,elapsed/fade):1;
      if(next)next.volume=initial+(this.settings.bgm_volume-initial)*progress;
      for(const old of previous)old.voice.volume=old.volume*(1-progress);
      if(progress===1){
        this.cancelRamp();for(const old of previous)old.voice.stop();
        console.info('STORY_BGM_FADE_COMPLETE',JSON.stringify({generation,fade,
          gameElapsedSeconds:elapsed,clock:this.clock.snapshot?.(),audioTime:next?.currentTime}));
      }
    };
    if(fade)this.cancelFade=this.clock.subscribe(tick);
    tick();
  }
  cancelRamp(){this.cancelFade?.();this.cancelFade=null;}
  stop(){this.generation++;this.cancelRamp();this.loading=null;for(const voice of this.players)voice.stop();this.players.clear();this.current=null;this.active=false;this.applied='';this.muted=false;if(this.output)this.output.gain.value=1;}
}
