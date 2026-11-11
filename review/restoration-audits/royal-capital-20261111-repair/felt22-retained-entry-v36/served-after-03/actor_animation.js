import {sample} from '/pairing/motion.js';
import {motionAssignments} from './motion_names.js';
import {visualFrameClock} from './visual_frame_clock.js';

// Unity's Animator keeps independent layer clocks. Body/face idle clips carry
// breathing and hair movement, and one-shot states can transition into loops.
// A dialogue without a new motion therefore keeps playing its existing layer;
// neither the last frame nor a generic synthetic breathing curve is correct.
export class ActorAnimation {
  constructor(viewer,definition,settings){
    Object.assign(this,{viewer,definition,settings});this.layers=new Map();this.clips=new Map();
    this.visualClock=viewer.visualClock||visualFrameClock;
    this.time=0;this.last=this.visualClock.now();this.running=false;this.talking=false;this.lastCommand='';
    this.rows=new Map(viewer.detail.motions.map(row=>[row.token,row]));
  }
  async clip(token){
    if(this.clips.has(token))return this.clips.get(token);
    const row=this.rows.get(token);if(!row)throw new Error('原版动画状态缺少对应曲线：'+token);
    const clip=await this.viewer.motion(row);this.clips.set(token,clip);return clip;
  }
  async prepare(layer,token,seen=new Set()){
    if(seen.has(token))return;seen.add(token);
    const state=layer.states[token];if(!state)throw new Error('原版动画控制器没有状态：'+token);
    if(state.speed_parameter)throw new Error('该动画使用尚未还原的速度参数：'+token);
    await this.clip(token);
    for(const row of state.transitions.filter(row=>!row.conditions.length)){
      if(!row.target)throw new Error('该动作包含尚未还原的跨状态机转换：'+token);
      await this.prepare(layer,row.target,seen);
    }
  }
  async setup(){
    for(const layer of this.definition.layers){
      if(layer.blend_mode!==0&&layer.weight)throw new Error('该模型含尚未还原的叠加动画层：'+layer.name);
      if(layer.weight){await this.prepare(layer,layer.default);this.set(layer,layer.default,layer.weight);}
    }
    const talk=this.definition.layers.find(layer=>layer.name===this.settings.layer);
    if(talk){
      this.talkLayer=talk;
      this.talkTrigger=talk.triggers.find(row=>row.conditions.some(c=>c.name===this.settings.start_trigger));
      if(!this.talkTrigger?.target)throw new Error('该模型没有原版说话触发状态');
      await this.prepare(talk,this.talkTrigger.target);
    }
    this.running=true;
    console.info('STORY_ANIMATOR_READY',this.viewer.detail.id,this.definition.controller,
      JSON.stringify([...this.layers].map(([name,row])=>({name,token:row.token}))));
  }
  async prepareChoice(config){
    this.choiceConfig=config;
    this.choiceLayer=this.definition.layers.find(layer=>layer.name===config.actor_layer);
    this.choiceTree=this.choiceLayer?.states[this.choiceLayer.default]?.selection;
    if(!this.choiceTree)return;
    await Promise.all(this.choiceTree.children.map(row=>this.clip(row.token)));
    this.choice={target:0,value:0,weight:0,enabled:false,last:this.time};
  }
  setChoice(enabled,progress=0){
    if(!this.choice)return;
    this.clock();const choice=this.choice;
    if(choice.enabled!==enabled){
      choice.fade={start:this.time,from:choice.weight,to:enabled?1:0};
      console.info('STORY_CHOICE_ACTOR',this.viewer.detail.id,enabled,this.choiceTree.parameter);
    }
    choice.enabled=enabled;choice.target=-progress;
  }
  renderChoice(){
    const choice=this.choice;if(!choice)return;
    const step=(this.time-choice.last)*this.choiceConfig.slide_speed;choice.last=this.time;
    choice.value+=Math.max(-step,Math.min(step,choice.target-choice.value));
    if(choice.fade){
      const t=Math.min(1,(this.time-choice.fade.start)/this.choiceConfig.layer_transition_seconds);
      choice.weight=choice.fade.from+(choice.fade.to-choice.fade.from)*t;
      if(t===1)delete choice.fade;
    }
    if(!choice.weight)return;
    // View.UpdateLive2DSelectParam negates normalized card displacement and
    // caps its change by mSlideSpeedMax * deltaTime. Blend between the native
    // thresholds while body/face clocks keep running beneath this layer.
    const children=this.choiceTree.children;
    const right=children.find(row=>row.threshold>=choice.value)||children.at(-1);
    const left=children[Math.max(0,children.indexOf(right)-1)];
    const pose=row=>this.clips.get(row.token).curves.map(curve=>({curve,value:sample(curve,
      (this.time+row.offset*row.duration)%row.duration)}));
    const weight=left===right?0:(choice.value-left.threshold)/(right.threshold-left.threshold);
    for(const item of this.blendPoses(pose(left),pose(right),weight))this.apply(item.curve,item.value,choice.weight);
    this.viewer.stage.dataset.choiceActor=JSON.stringify({value:choice.value,weight:choice.weight});
  }
  clock(){
    // Rendering may resume after a long browser scheduling gap. The shared
    // frame clock has already applied the original Normal-mode time limit;
    // reading it here neither adds that gap again nor restarts a layer.
    const now=this.visualClock.now();if(this.running)this.time+=now-this.last;this.last=now;return this.time;
  }
  pause(){this.clock();this.running=false;this.endTalk();}
  resume(){this.last=this.visualClock.now();this.running=true;}
  set(layer,token,weight=1,offset=0){
    this.layers.set(layer.name,{definition:layer,token,start:this.time,offset,weight});
  }
  clearCommand(){this.lastCommand='';}
  async select(selection,isCurrent){
    // Native PlayMotion (0x600187b) ignores an immediately repeated nonempty
    // character+command pair. An empty command clears that comparison but
    // leaves the animator running. Compare script tokens, not resolved poses:
    // an entry state may already have advanced into its resting loop.
    if(selection.command&&selection.command===this.lastCommand){
      console.info('STORY_MOTION_CONTINUE',this.viewer.detail.id,selection.command);
      return;
    }
    const assignments=motionAssignments(selection,this.viewer.motionIndex.models[this.viewer.detail.id].states,this.viewer.motionSemantics),plans=[];
    for(const assignment of assignments){
      const layer=this.definition.layers.find(layer=>layer.name===assignment.layer);
      await this.prepare(layer,assignment.token);plans.push({...assignment,layer});
    }
    // Preparing clips must not clear a visible layer or restart its clock.
    // Commit all assignments together after I/O, and discard a selection
    // whose node was stopped/replaced while its resources were loading.
    if(!isCurrent())return;
    this.clock();
    // Removing the override layer represents Animator.SetLayerWeight(face,0).
    // This must also happen for random-access entries seeded from upstream
    // state, otherwise a model whose prefab enables face by default would
    // resurrect it. The base motion's facial curves remain active underneath.
    for(const name of selection.clearLayers){
      const previous=this.layers.get(name);
      this.layers.delete(name);
      console.info('STORY_EXPRESSION_CLEAR',this.viewer.detail.id,name,previous?.token||'inactive');
    }
    for(const {layer,token,explicit} of plans){
      // A random-access entry has no elapsed upstream clock. Seed it with
      // the reachable resting state; continuous playback retains the exact
      // running layer when the next node leaves its motion field empty.
      if(!explicit&&this.layers.get(layer.name)?.assigned)continue;
      let selected=token,offset=0;
      if(!explicit){
        const seen=new Set();
        while(!layer.states[selected].loop&&!seen.has(selected)){
          seen.add(selected);
          const transition=layer.states[selected].transitions.find(row=>!row.conditions.length&&row.target);
          if(!transition){offset=this.clips.get(selected).duration;break;}
          selected=transition.target;
        }
      }
      const previous=this.layers.get(layer.name);
      const trigger=explicit?layer.triggers.find(row=>row.target===token):null;
      if(trigger)offset=trigger.offset*this.clips.get(selected).duration;
      this.set(layer,selected,1,offset);
      const current=this.layers.get(layer.name);current.assigned=true;
      if(trigger&&previous){
        const duration=trigger.fixed_duration?trigger.duration:trigger.duration*this.clips.get(previous.token).duration;
        if(duration)current.blend={source:previous,start:this.time,duration};
        console.info('STORY_MOTION_BLEND',this.viewer.detail.id,layer.name,previous.token,selected,duration);
      }
    }
    this.lastCommand=selection.command;
    console.info('STORY_MOTION_LAYERS',this.viewer.detail.id,JSON.stringify([...this.layers].map(([layer,row])=>({layer,token:row.token}))));
    console.info('STORY_NORMAL_MOTION_COMMIT',JSON.stringify({model:this.viewer.detail.id,
      node:document.body.dataset.node,wallMilliseconds:performance.now(),clock:this.visualClock.snapshot(),
      command:selection.command,actorSeconds:this.time,
      layers:[...this.layers].map(([layer,row])=>({layer,token:row.token,start:row.start,offset:row.offset,
        blend:row.blend?{start:row.blend.start,duration:row.blend.duration}:null}))}));
    this.resume();
  }
  beginTalk(){
    this.endTalk();if(!this.talkLayer)return;
    this.clock();
    // Use the recovered normal-talk trigger and its original mouth curve.
    // The reviewer requested speech to end with text reveal (including an
    // instant-reveal click), so the subtitle transport owns the stop event.
    // An independent length timer would drift when language/speed changes.
    const layer=this.talkLayer,row=this.talkTrigger;
    this.set(layer,row.target,1,row.offset*this.clips.get(row.target).duration);
    this.layers.get(layer.name).fade={start:this.time,duration:row.fixed_duration?row.duration:row.duration*this.clips.get(row.target).duration};
    this.talking=true;
    console.info('STORY_TEXT_MOUTH_START',this.viewer.detail.id,row.target);
  }
  endTalk(){
    if(this.talking)console.info('STORY_TEXT_MOUTH_STOP',this.viewer.detail.id);
    this.layers.delete(this.settings.layer);this.talking=false;
  }
  pose(layer,token,elapsed){
    const clip=this.clips.get(token),state=layer.states[token];
    const time=state.loop&&clip.duration?elapsed%clip.duration:Math.min(elapsed,clip.duration);
    return clip.curves.map(curve=>({curve,value:sample(curve,Math.max(0,time))}));
  }
  statePose(row){
    const target=this.clipPose(row);
    if(!row.blend)return target;
    const weight=Math.min(1,(this.time-row.blend.start)/row.blend.duration);
    if(weight===1){delete row.blend;return target;}
    // Both source and destination continue to advance during an AnyState
    // transition. Duration/offset come from the recovered AnimatorController,
    // so no fixed preview fade or frozen screenshot is substituted here.
    return this.blendPoses(this.statePose(row.blend.source),target,weight);
  }
  blendPoses(source,target,weight){
    const keys=new Map(source.map(item=>[item.curve.Target+':'+item.curve.Id,item]));
    for(const item of target){
      const key=item.curve.Target+':'+item.curve.Id,old=keys.get(key);
      keys.set(key,{curve:item.curve,value:old?old.value+(item.value-old.value)*weight:item.value});
    }
    return [...keys.values()];
  }
  clipPose(row){
    const layer=row.definition,state=layer.states[row.token],clip=this.clips.get(row.token);
    const elapsed=(this.time-row.start)*state.speed+row.offset+state.offset*clip.duration;
    const transition=state.transitions.find(t=>!t.conditions.length&&t.target&&(!t.has_exit_time||elapsed>=t.exit_time*clip.duration));
    const source=this.pose(layer,row.token,elapsed);
    if(!transition)return source;
    const begins=transition.has_exit_time?transition.exit_time*clip.duration:0;
    const duration=transition.fixed_duration?transition.duration:transition.duration*clip.duration;
    const since=(elapsed-begins)/state.speed,targetClip=this.clips.get(transition.target);
    const offset=transition.offset*targetClip.duration,targetState=layer.states[transition.target];
    if(since>=duration){
      row.token=transition.target;row.start=this.time-since;row.offset=offset;
      console.info('STORY_ANIMATOR_TRANSITION',this.viewer.detail.id,layer.name,row.token);
      return this.pose(layer,row.token,since*targetState.speed+offset+targetState.offset*targetClip.duration);
    }
    const target=this.pose(layer,transition.target,since*targetState.speed+offset+targetState.offset*targetClip.duration);
    const weight=duration?since/duration:1;
    return this.blendPoses(source,target,weight);
  }
  apply(curve,value,weight){
    const core=this.viewer.core;
    if(curve.Target==='Parameter')core.setParameterValueById(curve.Id,core.getParameterValueById(curve.Id)*(1-weight)+value*weight);
    else if(curve.Target==='PartOpacity')core.setPartOpacityById(curve.Id,core.getPartOpacityById(curve.Id)*(1-weight)+value*weight);
    else if(curve.Id==='Opacity')this.viewer.model.alpha=this.viewer.model.alpha*(1-weight)+value*weight;
    else if(['EyeBlink','LipSync'].includes(curve.Id)){
      for(const group of this.viewer.groups.filter(group=>group.Name===curve.Id))
        for(const id of group.Ids)this.apply({Target:'Parameter',Id:id},value,weight);
    }else throw new Error('未识别的模型曲线：'+curve.Id);
  }
  render(){
    this.clock();
    const native=this.viewer.core.getModel();native.parameters.values.set(this.viewer.parameters);
    native.parts.opacities.set(this.viewer.parts);this.viewer.model.alpha=1;
    for(const layer of this.definition.layers){
      if(layer===this.choiceLayer)this.renderChoice();
      const row=this.layers.get(layer.name);if(!row)continue;
      const fade=row.fade?Math.min(1,(this.time-row.fade.start)/row.fade.duration):1;
      for(const item of this.statePose(row))this.apply(item.curve,item.value,row.weight*fade);
    }
  }
}
