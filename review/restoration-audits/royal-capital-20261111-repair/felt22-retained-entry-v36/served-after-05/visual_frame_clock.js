import {NATIVE_TIME_CONFIG} from './native_time_config.js';

// Unity's Normal Animator and BGM gain coroutine use game-frame time, whereas
// script Wait and media sample clocks retain separate time domains. Keep this
// adapter independent of rendering,
// actor count and transition ownership so every Normal consumer observes one
// immutable sample for a browser frame. Async preparation reads now(); it must
// never integrate another performance.now() interval into that same frame.
export class NativeVisualFrameClock {
  constructor(configuration=NATIVE_TIME_CONFIG,{schedule=callback=>requestAnimationFrame(callback),
      cancel=handle=>cancelAnimationFrame(handle),report=(name,value)=>console.info(name,JSON.stringify(value))}={}){
    const maximum=configuration.maximumDeltaSeconds,nativeScale=configuration.timeScale;
    if(!(Number.isFinite(maximum)&&maximum>0)||!(Number.isFinite(nativeScale)&&nativeScale>=0))
      throw new Error('原版动画时钟配置无效');
    Object.assign(this,{configuration,schedule,cancel,report});
    this.seconds=0;this.frame=0;this.lastTimestamp=null;this.rate=1;this.rateOwner=null;
    this.rawDelta=0;this.delta=0;this.listeners=new Set();this.disposed=false;
    this.tick=timestamp=>{
      this.pending=null;if(this.disposed)return;
      try{
        this.sampleFrame(timestamp);
        // Snapshotting prevents newly subscribed channels from consuming an
        // already active frame. Recheck membership as well: an earlier
        // callback can cancel/Stop a later channel before its turn arrives.
        for(const listener of [...this.listeners]){
          if(!this.listeners.has(listener))continue;
          try{listener(this.snapshot());}
          catch(error){
            // One failed visual channel must not permanently stop every
            // actor/card RAF. Remove that callback, retain healthy channels,
            // and record the actual failure rather than assigning a cause.
            this.listeners.delete(listener);
            this.reportEvent('STORY_NORMAL_CLOCK_LISTENER_ERROR',{clock:this.snapshot(),
              error:{name:error?.name||'Error',message:String(error?.message||error),stack:error?.stack||''}});
          }
        }
      }finally{
        if(!this.disposed)this.pending=this.schedule(this.tick);
      }
    };
    this.pending=this.schedule(this.tick);
  }
  sampleFrame(timestamp){
    if(!Number.isFinite(timestamp)||this.lastTimestamp!==null&&timestamp<=this.lastTimestamp)return;
    this.rawDelta=this.lastTimestamp===null?0:(timestamp-this.lastTimestamp)/1000;
    this.lastTimestamp=timestamp;this.frame++;
    // The APK's baseline timeScale is one. First apply its recorded game-time
    // limit, then the existing preview transport rate. The latter is a user
    // playback preference, not a newly inferred native timeScale setting.
    const nativeDelta=Math.min(this.rawDelta*this.configuration.timeScale,
      this.configuration.maximumDeltaSeconds);
    this.delta=nativeDelta*this.rate;this.seconds+=this.delta;
    if(this.rawDelta*this.configuration.timeScale>this.configuration.maximumDeltaSeconds)
      this.reportEvent('STORY_NORMAL_FRAME_HITCH',this.snapshot());
  }
  now(){return this.seconds;}
  snapshot(){return {profile:this.configuration.profile,frame:this.frame,
    frameTimestampMs:this.lastTimestamp,rawDeltaSeconds:this.rawDelta,
    deltaSeconds:this.delta,gameSeconds:this.seconds,previewRate:this.rate,
    maximumDeltaSeconds:this.configuration.maximumDeltaSeconds,
    rateOwner:this.rateOwner?.constructor?.name||null};}
  reportEvent(name,value){
    // Diagnostics themselves are outside the simulation's dependency chain.
    // A failing host logger must not strand the shared frame subscription.
    try{this.report(name,value);}
    catch(error){console.error('STORY_NORMAL_CLOCK_REPORT_ERROR',error);}
  }
  subscribe(listener){
    if(this.disposed)throw new Error('动画时钟已释放');
    this.listeners.add(listener);return()=>this.listeners.delete(listener);
  }
  claimRate(owner){
    if(this.disposed)throw new Error('动画时钟已释放');
    if(!owner)throw new Error('动画速度控制需要明确的播放器');
    if(this.rateOwner===null)this.rateOwner=owner;
    return this.rateOwner===owner;
  }
  releaseRate(owner){
    if(this.rateOwner!==owner)return false;
    // Recreating a primary viewer must not retain a rate lease owned by its
    // disposed predecessor. Secondary releases cannot affect the primary.
    this.rateOwner=null;this.rate=1;return true;
  }
  setRate(rate,owner){
    if(this.disposed)throw new Error('动画时钟已释放');
    if(!(Number.isFinite(rate)&&rate>=0))throw new Error('动画播放速度无效');
    // A document can contain several model viewers sharing this Normal
    // clock. Only its primary transport owns preview speed; a secondary
    // model cannot silently replace the rate chosen by another viewer.
    if(!owner||owner!==this.rateOwner)throw new Error('仅主播放器可以修改共享动画速度');
    this.rate=rate;
  }
  dispose(){
    this.disposed=true;this.cancel(this.pending);this.pending=null;this.listeners.clear();this.rateOwner=null;
  }
}

// ES modules are evaluated before any importing StoryActor/MediaEditor creates
// its PIXI application. Register the frame sampler first, then let transition
// listeners and PIXI's model update read that frame's shared game-time sample.
// Stop/restart cancel their own subscriptions and local actor anchors; they do
// not reset this monotonic document clock or accumulate a second wall-time debt.
export const visualFrameClock=new NativeVisualFrameClock();
