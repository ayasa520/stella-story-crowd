import {readJSON,loadImage} from './player_scene.js';
import {visualFrameClock} from './visual_frame_clock.js';

// CardBehaviour.DropProc owns card alpha, while the Wipe API owns an independent
// scene cover below the dialogue canvas. Native WipeOut keeps the text panel
// visible over the closed eyelids. CardOut must not uncover a completed wipe,
// and replacing an actor/background must not recreate either layer.
export class StoryTransitions {
  constructor({stage,card,overlays=[],clock=visualFrameClock}){
    Object.assign(this,{stage,card,overlays,clock});this.pending=new Set();this.images=new Map();this.panels=new Set();
    this.canvas=document.createElement('canvas');this.canvas.className='story-wipe';
    Object.assign(this.canvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',pointerEvents:'none'});
    // Keep the cover outside the fading card, but insert it before that card's
    // dialogue overlays. DOM paint order then preserves the native separation
    // between the scene wipe and the independently animated text panel.
    // Material previews have no dialogue overlay and append it.
    this.canvas.hidden=true;stage.insertBefore(this.canvas,overlays[0]||null);this.context=this.canvas.getContext('2d');
    this.mask=document.createElement('canvas');this.maskContext=this.mask.getContext('2d',{willReadFrequently:true});
    this.reset();
  }
  async setup(){this.config=await readJSON('/player-assets/transitions.json');}
  animateNormal(seconds,draw){
    return new Promise((resolve,reject)=>{
      const began=this.clock.now();let unsubscribe=()=>{};
      const release=()=>{unsubscribe();this.pending.delete(cancel);};
      const cancel=()=>{release();reject(new DOMException('Playback cancelled','AbortError'));};
      this.pending.add(cancel);
      const tick=()=>{
        try{
          // Card_wait/Card_in are Normal Animator clips in the original APK.
          // Share their capped game-frame time with actor layers, instead of
          // comparing an independent RAF timestamp against a wall-time start.
          // Awaited resources and cancellation never advance this clock.
          const t=seconds?Math.max(0,Math.min(1,(this.clock.now()-began)/seconds)):1;
          draw(t);if(t===1){release();resolve();}
        }catch(error){release();reject(error);}
      };
      try{draw(0);unsubscribe=this.clock.subscribe(tick);}
      catch(error){release();reject(error);}
    });
  }
  animate(seconds,draw){
    // Wipe and panel channels retain their existing wall-time behavior until
    // their owning native clocks are independently audited. A Normal card
    // clock must not silently retime every effect that uses this compositor.
    return new Promise((resolve,reject)=>{
      let frame;const began=performance.now();
      const cancel=()=>{cancelAnimationFrame(frame);this.pending.delete(cancel);reject(new DOMException('Playback cancelled','AbortError'));};
      this.pending.add(cancel);
      const tick=now=>{
        const t=seconds?Math.max(0,Math.min(1,(now-began)/(seconds*1000))):1;draw(t);
        if(t<1)frame=requestAnimationFrame(tick);else{this.pending.delete(cancel);resolve();}
      };
      draw(0);frame=requestAnimationFrame(tick);
    });
  }
  curve(keys,time){
    let key=keys[0];for(const next of keys){if(next.time>time)break;key=next;}
    const t=Math.max(0,time-key.time),[a,b,c,d]=key.coefficients;
    return ((a*t+b)*t+c)*t+d;
  }
  opacity(value){
    this.card.style.opacity=value;
  }
  hide(){this.cardState='out';this.opacity('0');this.card.style.translate='';}
  show(){this.cardState='in';this.opacity('');this.card.style.translate='';}
  async cardIn(){
    if(this.cardState!=='out'){this.cardState='in';return;}
    const cfg=this.config.card;this.cardState='waiting';
    console.info('STORY_NORMAL_TRANSITION_CLOCK',JSON.stringify({stage:'card_wait_start',
      node:document.body.dataset.node,wallMilliseconds:performance.now(),clock:this.clock.snapshot()}));
    console.info('STORY_CARD_WAIT_START',performance.now(),cfg.wait_duration);
    await this.animateNormal(cfg.wait_duration,()=>this.opacity('0'));
    this.cardState='entering';console.info('STORY_CARD_IN_START',performance.now(),cfg.duration);
    console.info('STORY_NORMAL_TRANSITION_CLOCK',JSON.stringify({stage:'card_in_start',
      node:document.body.dataset.node,wallMilliseconds:performance.now(),clock:this.clock.snapshot()}));
    await this.animateNormal(cfg.duration,t=>{
      this.opacity(String(Math.max(0,Math.min(1,this.curve(cfg.opacity,t*cfg.duration)))));
      this.card.style.translate=`0 ${-this.curve(cfg.y,t*cfg.duration)/this.height*100}%`;
    });
    this.opacity('');this.card.style.translate='';this.cardState='in';
    console.info('STORY_CARD_IN_COMPLETE',performance.now());
    console.info('STORY_NORMAL_TRANSITION_CLOCK',JSON.stringify({stage:'card_in_complete',
      node:document.body.dataset.node,wallMilliseconds:performance.now(),clock:this.clock.snapshot()}));
  }
  async cardOut(selected=null){
    if(this.cardState!=='in')return;
    // DropProc (0x1256f6c) decreases alpha at 15/s. A selected card retains
    // its touch mask/UVs and drag rotation while its position falls. Never
    // reset that geometry to a full-screen card before beginning the drop.
    this.cardState='leaving';
    const duration=1/this.config.card.alpha_speed;
    console.info('STORY_CARD_OUT_START',performance.now(),Boolean(selected));
    await this.animateNormal(duration,t=>{
      this.opacity(String(1-t));selected?.drop(t*duration*this.config.card.selected_fall_speed);
    });
    this.cardState='out';console.info('STORY_CARD_OUT_COMPLETE',performance.now());
  }
  async panelOut(source,profile){
    // A snapshot owns the outgoing panel until its own animation finishes.
    // The next card may load/enter concurrently; clearing or redrawing its
    // dialogue canvas must not erase the previous panel's final frames.
    const canvas=document.createElement('canvas'),cfg=this.config.panels[profile];
    canvas.width=source.width;canvas.height=source.height;
    canvas.className='story-panel-out';canvas.dataset.profile=profile;
    Object.assign(canvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',pointerEvents:'none'});
    canvas.getContext('2d').drawImage(source,0,0);source.after(canvas);this.panels.add(canvas);
    console.info('STORY_PANEL_OUT_START',performance.now(),profile,cfg.duration);
    try{
      await this.animate(cfg.duration,t=>{
        canvas.style.opacity=String(this.curve(cfg.opacity,t*cfg.duration));
        if(cfg.y)canvas.style.translate=`0 ${-(this.curve(cfg.y,t*cfg.duration)-this.curve(cfg.y,0))/this.height*100}%`;
      });
      console.info('STORY_PANEL_OUT_COMPLETE',performance.now(),profile);
    }finally{canvas.remove();this.panels.delete(canvas);}
  }
  stay(){if(this.cardState==='in')this.cardState='stay';}
  async image(name){
    if(!this.images.has(name))this.images.set(name,await loadImage('/player-assets/'+name));
    return this.images.get(name);
  }
  async prepare(name,color,generation){
    const resource=this.config.wipes[name],filename=this.config.colors[color];
    if(!resource)throw new Error('尚未提取此原版转场资源：'+name);
    if(!filename)throw new Error('尚未提取此原版转场图片：'+color);
    const [mask,image]=await Promise.all([this.image(resource.file),this.image(filename)]);
    if(generation!==this.generation)throw new DOMException('Playback cancelled','AbortError');
    this.canvas.width=this.mask.width=mask.width;this.canvas.height=this.mask.height=mask.height;
    this.maskContext.clearRect(0,0,mask.width,mask.height);this.maskContext.drawImage(mask,0,0);
    this.pixels=this.maskContext.getImageData(0,0,mask.width,mask.height);
    this.nativeAlpha=new Uint8Array(mask.width*mask.height);
    for(let i=0;i<this.nativeAlpha.length;i++)this.nativeAlpha[i]=this.pixels.data[i*4+3];
    this.wipeResource=resource;this.colorImage=image;
  }
  draw(range){
    const pixels=this.pixels.data,scale=this.wipeResource.scale;
    // Exact UI/Fade Texture fragment alpha: clamp(Range*(a*Scale+2)+a-1).
    // Work at the native mask resolution. CSS scales the finished composition
    // to the same viewport as the scene, without stretching the scene itself.
    for(let i=0;i<this.nativeAlpha.length;i++){
      const sample=this.nativeAlpha[i]/255,a=this.wipeResource.reverse?1-sample:sample;
      pixels[i*4+3]=Math.round(Math.max(0,Math.min(1,range*(a*scale+2)+a-1))*255);
    }
    this.maskContext.putImageData(this.pixels,0,0);
    const c=this.context,w=this.canvas.width,h=this.canvas.height;
    // The build exports _MainTex as RGB, preserving its channels before
    // Canvas premultiplication. Only the mask supplies fragment transparency.
    c.globalCompositeOperation='source-over';c.clearRect(0,0,w,h);c.drawImage(this.colorImage,0,0,w,h);
    c.globalCompositeOperation='destination-in';c.drawImage(this.mask,0,0);c.globalCompositeOperation='source-over';
    this.canvas.hidden=range===0;this.stage.dataset.wipeRange=String(range);
  }
  async wipe(row){
    const generation=this.generation,isOut=row.action==='out';
    const name=isOut?row.resource:row.resource||this.previous.name;
    const color=(row.image||(isOut?'fade_color_black':this.previous.image)).replace(/\.png$/,'');
    await this.prepare(name,color,generation);
    if(isOut)this.previous={name,image:color};
    const start=row.start;
    const animation=this.wipeResource.animations[row.action],duration=animation?animation.duration:this.config.wipe_duration;
    console.info('STORY_WIPE_START',JSON.stringify({action:row.action,name,color,start,duration:duration*(1-start)}));
    await this.animate(duration*(1-start),t=>{
      const value=start+(1-start)*t;
      this.draw(this.rangeAt(row.action,value));
    });
    if(generation!==this.generation)throw new DOMException('Playback cancelled','AbortError');
    if(!isOut)this.previous.image='';
    console.info('STORY_WIPE_COMPLETE',row.action,name,color,start);
  }
  rangeAt(action,progress){
    const animation=this.wipeResource.animations[action];
    return animation?this.legacyCurve(animation.keys,progress*animation.duration):action==='out'?progress:1-progress;
  }
  legacyCurve(keys,time){
    let left=keys[0];
    for(const right of keys){
      if(right.time>time){
        const duration=right.time-left.time,t=(time-left.time)/duration,t2=t*t,t3=t2*t;
        return (2*t3-3*t2+1)*left.value+(t3-2*t2+t)*duration*left.outSlope+
          (-2*t3+3*t2)*right.value+(t3-t2)*duration*right.inSlope;
      }
      left=right;
    }
    return left.value;
  }
  async restore(state){
    this.previous={name:state.wipe_name||'',image:state.wipe_image||''};
    if(state.wipe_covered){
      await this.prepare(this.previous.name,this.previous.image,this.generation);
      // Random-access entry must match the finished Out frame. Legacy clips
      // need not end at range=1: the native blood wipe retains partial alpha.
      this.draw(this.rangeAt('out',1));
    }
  }
  reset(){
    this.generation=(this.generation||0)+1;for(const cancel of this.pending)cancel();
    for(const panel of this.panels)panel.remove();this.panels.clear();
    this.cardState='out';this.previous={name:'',image:''};this.canvas.hidden=true;
    this.opacity('');this.card.style.translate='';delete this.stage.dataset.wipeRange;
  }
}
