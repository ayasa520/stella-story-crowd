// A music voice owns the sample clock, waveform loop and rendered-mix gain.
// Web Audio schedules the wrap in the audio renderer; timeupdate/RAF seeking
// would miss the boundary when a tab is busy or hidden and expose the WAV's
// additional decoder repetitions/fade. The source starts at zero once, then
// wraps only between the original ACB loop points, leaving its intro intact.
export class MusicVoice {
  constructor(context,destination,buffer,metadata,volume,onended){
    Object.assign(this,{context,metadata,onended});
    const duration=metadata.samples/metadata.sample_rate;
    if(duration>buffer.duration+1/buffer.sampleRate||metadata.loop&&
      !(metadata.loop_start>=0&&metadata.loop_start<metadata.loop_end&&metadata.loop_end<=duration))
      throw new Error('BGM 原音库循环点超出本地 WAV：'+metadata.resource);
    this.source=context.createBufferSource();this.gain=context.createGain();
    this.source.buffer=buffer;this.source.loop=metadata.loop;
    this.source.loopStart=metadata.loop_start;this.source.loopEnd=metadata.loop_end;
    this.source.connect(this.gain);this.gain.connect(destination);this.volume=volume;
    this.source.onended=()=>this.finish();
  }
  get volume(){return this.gain.gain.value;}
  set volume(value){this.gain.gain.value=value;}
  start(){
    this.began=this.context.currentTime;this.source.start(this.began);
    if(!this.metadata.loop)this.source.stop(this.began+this.metadata.samples/this.metadata.sample_rate);
  }
  get currentTime(){
    const elapsed=this.context.currentTime-this.began,{loop,loop_start:start,loop_end:end}=this.metadata;
    return loop&&elapsed>=end?start+(elapsed-end)%(end-start):elapsed;
  }
  stop(){if(this.ended)return;this.source.stop();this.finish();}
  finish(){
    if(this.ended)return;this.ended=true;
    this.source.disconnect();this.gain.disconnect();this.onended();
  }
}
