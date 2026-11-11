import {DialogueVoice} from './dialogue_voice.js';
import {OriginalScene,StoryActor,readJSON} from './player_scene.js';
import {StoryMusicPlayer} from './music_player.js';
import {EffectPlayer} from './effects.js';
import {NativeBackground} from './background.js';
import {motionState,heldState,extraLayers} from './motion_names.js';
import {ChoiceView} from './choice_view.js';
import {ChoiceInput} from './choice_input.js';
import {StorySoundPlayer} from './sound_player.js';
import {ChoiceCard} from './choice_card.js';
import {StoryTransitions} from './transitions.js';
import {StoryFlowView} from './flow_view.js';
import {ActorStage} from './actor_stage.js';
import {prepareCommandResources} from './command_resources.js';
import {CommandClock} from './command_clock.js';
import {setMoviePresentation} from './movie_view.js';
import {playerConfigAt} from '/pairing/repository_assets.js';

const $=id=>document.getElementById(id);
document.body.classList.toggle('embedded',new URLSearchParams(location.search).get('embedded')==='1');

// This transport owns an immutable editor snapshot. Native scenario phases
// and explicit graph edges determine execution; recording timestamps are only
// review evidence. Every asynchronous boundary checks the same cancellation
// generation, including resource loading, input waits and movie completion.
class StoryPlayer {
  constructor(){
    this.generation=0;this.phase='idle';this.auto=false;this.pending=new Set();
    this.actor=new StoryActor($('viewport'),$('actor'),()=>{},error=>this.fail(error),{visibleOnLoad:false});
    this.cast=new ActorStage(this.actor);this.actor.cast=this.cast;
    this.scene=new OriginalScene({stage:$('viewport'),canvas:$('subtitles'),viewer:this.actor});
    this.background=new NativeBackground($('card'));
    this.backdrop=new NativeBackground($('backdrop'));
    this.music=new StoryMusicPlayer();this.voice=new Audio();this.dialogueVoice=new DialogueVoice(this.voice);
    this.sounds=new StorySoundPlayer();
    this.transitions=new StoryTransitions({stage:$('viewport'),card:$('cardMotion'),overlays:[$('subtitles')]});
    this.effects=new EffectPlayer({stage:$('viewport'),card:$('card'),button:$('effectContinue'),status:$('effectStatus'),onError:error=>this.fail(error),auto:()=>this.auto});
    this.models=new Map();this.banks=new Map();
    const flowRoot=document.createElement('section');flowRoot.id='storyFlow';flowRoot.hidden=true;$('viewport').append(flowRoot);
    this.flowView=new StoryFlowView(flowRoot);
    $('viewport').addEventListener('pointerdown',()=>this.resumeAudio());
    for(const id of ['advance','viewport'])$(id).addEventListener('click',()=>this.advance().catch(error=>this.fail(error)));
    $('restart').onclick=()=>this.start().catch(error=>this.fail(error));
    $('stop').onclick=()=>{this.stop();this.status('已停止；可从入口重播。');};
    $('close').onclick=()=>{this.stop();parent.postMessage({type:'stella-player-close'},location.origin);};
    $('auto').onclick=()=>{this.auto=!this.auto;$('auto').setAttribute('aria-pressed',String(this.auto));};
    $('language').onchange=()=>{
      if(!['text','ready','choice'].includes(this.phase))return;
      try{
        this.length=this.scene.text(this.node,$('language').value,this.phase==='text'?0:Infinity);this.accessible();
        if(this.phase==='choice'){this.choiceInput.redraw($('language').value);this.choiceChanged(this.choiceInput.selected);}
        if(this.phase==='text'){this.visible=0;this.textBegan=performance.now();if(this.node.actors.length)this.cast.beginTalk();else if(this.node.model)this.actor.animator?.beginTalk();}
      }
      catch(error){this.fail(error);}
    };
    window.addEventListener('keydown',event=>{
      if(event.code==='Space'&&!event.target.closest('button,select')){event.preventDefault();this.advance().catch(error=>this.fail(error));}
    });
    window.addEventListener('pagehide',()=>this.stop());
    new MutationObserver(()=>this.publish()).observe(document.querySelector('aside'),{subtree:true,childList:true,attributes:true,characterData:true});
  }
  async setup(){
    console.info('STELLA_PLAYER_SETUP','begin',performance.now());
    this.config=playerConfigAt(await readJSON('player_config.json'),new URLSearchParams(location.search).get('assetRevision'));
    this.actor.config=await readJSON(this.config.viewer_config);
    [this.motionIndex,this.actor.animationAssets]=await Promise.all([
      readJSON('/pairing/'+this.actor.config.motion_index),readJSON(this.config.animation_manifest),this.scene.setup(this.config)]);
    this.actor.motionIndex=this.motionIndex;
    this.background.setup(this.scene.assets,this.config);
    this.backdrop.setup(this.scene.assets,this.config,{blurred:true});
    this.transitions.height=this.scene.assets.resolution[1];await this.transitions.setup();
    const choiceCard=new ChoiceCard(this.scene,{stage:$('viewport'),card:$('card'),mask:$('cardMask'),mover:$('cardMotion'),frame:$('cardFrame'),backdrop:$('backdrop')});
    this.choiceView=new ChoiceView(this.scene,$('choiceCanvas'),this.config.choices,choiceCard);
    await this.choiceView.setup();
    this.choiceInput=new ChoiceInput($('viewport'),this.choiceView,{
      change:edge=>this.choiceChanged(edge),commit:edge=>this.chooseBranch(edge),error:error=>this.fail(error)});
    this.isReady=true;
    console.info('STELLA_PLAYER_SETUP','ready',performance.now());
    this.status('预览资源已就绪，点击「播放当前草稿」开始。');
  }
  status(message,error=false){$('status').textContent=message;$('status').classList.toggle('error',error);}
  publish(){
    const buttons={};for(const button of document.querySelectorAll('aside button[id]'))
      buttons[button.id]={disabled:button.disabled,hidden:button.hidden,pressed:button.getAttribute('aria-pressed')};
    parent.postMessage({type:'stella-player-state',state:{status:$('status').textContent,error:$('status').classList.contains('error'),
      buttons,language:$('language').value,effect:$('effectStatus').textContent,
      choices:[...$('choices').children].map(button=>({id:button.dataset.edge,text:button.textContent,disabled:button.disabled,
        selected:button.getAttribute('aria-pressed')==='true'}))}},location.origin);
  }
  setPhase(phase){this.phase=phase;document.body.dataset.phase=phase;$('advance').disabled=!['text','ready','chart'].includes(phase);}
  check(generation){if(generation!==this.generation)throw new DOMException('Playback cancelled','AbortError');}
  timing(stage){
    const detail={node:this.node?.id,stage,milliseconds:Math.round(performance.now()-this.nodeBegan)};
    console.info('STORY_PLAYER_TIMING',JSON.stringify(detail));
    document.dispatchEvent(new CustomEvent('stella-player-timing',{detail}));
  }
  fail(error){
    if(error.name==='AbortError')return;
    console.error('STORY_PLAYER_ERROR',this.node?.id,this.phase,error);
    this.stop();this.status(error.message,true);
  }
  stop({keepMusic=false}={}){
    this.generation++;cancelAnimationFrame(this.frame);this.actor.loadGeneration++;
    this.actor.stop();this.dialogueVoice.stop();if(!keepMusic)this.music.stop();this.sounds.stop();this.effects.stop();$('movie').pause();
    this.cast.stop();
    this.background.cancel();
    this.backdrop.cancel();
    this.choiceInput?.close();
    this.transitions.reset();
    this.flowView.close();this.chartContinue=null;
    for(const cancel of this.pending)cancel();
    $('choices').replaceChildren();this.setPhase('stopped');
  }
  async receive(program){
    this.program=program;this.nodes=new Map(program.nodes.map(node=>[node.id,node]));
    this.actor.motionSemantics=program.semantics;
    this.sounds.setup(program.sound_effects,program.semantics);
    this.music.setup(program.semantics);await this.effects.setup(program.semantics.quake_config);
    await this.effects.setupVisual(program.semantics.effect_manifest,this.scene.assets);
    $('restart').disabled=false;await this.start();
  }
  async start(){
    this.stop();this.scene.clear();$('history').replaceChildren();
    this.node=null;this.transitions.hide();
    this.scenarioBackgrounds=new Map(this.program.nodes.map(node=>[node.id,node.bg_picture]));
    this.completedScenes=new Set();
    this.visitedEdges=new Set();
    this.skippedPath=new Set();this.nodeBeforeSkip=null;
    // Replaying an entry has a new route context. Do not reuse layer clocks
    // or assignments from the route that the reviewer just stopped.
    this.actor.ready=false;
    this.state=structuredClone(this.program.before);
    this.cast.reset(this.state.actors);
    const generation=this.generation;
    await this.actor.lighting.apply(this.state);this.check(generation);
    await this.restoreEntryAudio(generation);
    this.check(generation);await this.transitions.restore(this.state);
    this.check(generation);await this.enter(this.program.start);
  }
  async restoreEntryAudio(generation){
    const entry=this.nodes.get(this.program.start),ambient={...this.state.ambient};
    this.music.setMuted(entry.title_mode==='scene'&&this.config.flow.mute_bgm);
    let music=entry.music.action==='inherit'?this.state.bg_music:'';
    // Random-access preview reconstructs upstream loops without replaying the
    // upstream script. Do not create an audible handle that the entry's BGM
    // assignment or leading stop commands immediately discard: StopBGM would
    // otherwise fade a freshly started track, producing a spurious snippet.
    // Inspect only the uninterrupted prefix of stop commands. A wait, effect,
    // sound playback or user-input boundary must retain its inherited audio
    // until the later stop actually executes. End also excludes later commands.
    // This filters restoration only; enter() still executes every authored
    // assignment and command, and continuous playback keeps its native fades.
    for(const row of entry.phases[0]){
      if(row.error||row.terminates_block)break;
      if(row.kind==='music')music='';
      else if(row.kind==='sound'&&row.action==='stop')delete ambient[row.cue];
      else break;
    }
    console.info('STORY_PLAYER_AUDIO_RESTORE',JSON.stringify({node:entry.id,
      inherited:{bg_music:this.state.bg_music,ambient:this.state.ambient},restore:{bg_music:music,ambient}}));
    if(music)await this.music.apply(music,{fade:0,start:true});
    this.check(generation);await this.sounds.restore(ambient);
  }
  async phaseCommands(index,generation){
    this.setPhase('command');
    this.timing('phase_'+index+'_begin');
    const clock=new CommandClock(this.effects);
    for(const row of this.node.phases[index]){
      this.check(generation);
      console.info('STORY_PLAYER_COMMAND',this.node.id,index,row.command);
      if(row.error)throw new Error(row.error);
      if(row.terminates_block){this.transitions.stay();break;}
      if(row.kind==='music'){
        await this.music.apply('',{fade:row.fade,start:true});this.state.bg_music='';
      }else if(row.kind==='lighting'){
        if(row.resource!=='OFF'){this.state.clut=row.resource;await Promise.all([this.actor.lighting.apply(this.state),this.cast.lighting(this.state)]);}
      }else if(row.kind==='wait')await clock.wait(row.duration*1000,row.can_skip);
      else if(row.kind==='sound')await this.sounds.execute(row);
      // ADVFuncs.SetJunction is a flag, not a timed effect. SelectSequence
      // consumes it when the player confirms the next choice.
      else if(row.kind==='junction')this.state.junction=true;
      else if(row.kind==='tap'){
        this.status('等待点击继续；之后执行后续演出。');await this.effects.wait(null,true);
      }
      else if(row.kind==='quake')this.effects.quake(row);
      else if(row.kind==='fx')await this.effects.fx(row,this.node.fx_emission_times);
      else if(row.kind==='wipe'){
        this.status(row.action==='out'?'转场：遮住画面…':'转场：揭开画面…');await this.transitions.wipe(row);
      }
      else if(row.kind==='card_out'){
        this.cardOut=true;
        if(!this.program.edges.some(edge=>edge.source===this.node.id&&edge.kind==='choice')){
          const edge=this.program.edges.find(edge=>edge.source===this.node.id);
          if(!this.skipInOut(this.node,this.nodes.get(edge?.target))){
            this.closePanel().catch(error=>this.fail(error));
            await this.transitions.cardOut();this.effects.cardOut();
          }
        }
      }
      else throw new Error('已保留设置，独立播放器尚未实现演出：'+row.command);
      this.check(generation);
      clock.completed(row);
    }
    this.timing('phase_'+index+'_end');
  }
  async image(element,url,generation){
    const image=new Image();
    await new Promise((resolve,reject)=>{
      const cancel=()=>finish(new DOMException('Playback cancelled','AbortError'));
      const finish=error=>{image.onload=null;image.onerror=null;this.pending.delete(cancel);error?reject(error):resolve();};
      this.pending.add(cancel);image.onload=()=>finish();image.onerror=()=>finish(new Error('图片读取失败：'+url));image.src=url;
    });await image.decode();this.check(generation);element.src=image.src;
  }
  display(kind){
    if(this.actor.model)this.actor.model.visible=kind==='actor'&&!this.node.actors.length;
    this.cast.visible(kind==='actor'&&this.node.actors.length>0);
    $('picture').hidden=kind!=='picture';$('movie').hidden=kind!=='movie';
    if(kind!=='actor')this.actor.animator?.clearCommand();
    console.info('STORY_DISPLAY_COMMIT',this.node.id,kind,this.actor.detail?.id||'');
  }
  cardContent(node){
    if(!node||node.kind==='title')return null;
    // MovieProc shares CardDrop/CardIn with CardProc. A movie is a distinct
    // foreground, so entering one must still retire the preceding actor/CG.
    // Returning null here incorrectly bypasses the native default drop when
    // the author leaves command[2] empty (for example scenario 29 -> 30).
    if(node.kind==='movie')return {kind:'movie',resource:node.movie_resource};
    if(node.character_image)return {kind:'picture',resource:node.character_image};
    // Speaker names and motion commands are not foreground identity. A
    // speaking member can change inside an unchanged group without replacing
    // the card. Compare the model set for both solo and placed actors, ignoring
    // draw order and placement edits; the existing stage owns those details.
    const models=node.actors.length?node.actors.map(row=>row.model):node.model?[node.model]:[];
    return {kind:'actor',models:[...models].sort()};
  }
  skipInOut(current,next){
    if(!current||this.program.edges.some(edge=>edge.source===current.id&&edge.kind==='choice'))return false;
    // ADVPlayer.get_IsSkipInOutEffect (0x124bc94) compares live ScenarioData.
    // A next row with no BG is considered equal before SetScriptParamater
    // visits it. Previously visited rows retain that method's mutation. Keep
    // these runtime values outside the immutable authored preview snapshot.
    const nextBG=next?this.scenarioBackgrounds.get(next.id):'';
    const sameBG=!nextBG||nextBG===this.scenarioBackgrounds.get(current.id);
    const from=this.cardContent(current),to=this.cardContent(next);
    const sameActor=from?.kind==='actor'&&from.models.length&&JSON.stringify(from)===JSON.stringify(to);
    const sameImage=current.character_image&&current.character_image===next?.character_image;
    const onlyBG=node=>node&&!node.model&&!node.actors.length&&!node.character_image&&!node.movie_resource;
    return Boolean((sameActor&&sameBG)||sameImage||(sameBG&&onlyBG(current)&&onlyBG(next))||
      (current.kind==='title'&&current.title_mode!=='end'));
  }
  closePanel(profile='out'){
    if(!this.scene.panel)return Promise.resolve();
    const animation=this.transitions.panelOut(this.scene.canvas,profile);
    this.scene.clear();return animation;
  }
  setScriptBackground(){
    const node=this.node,background=node.script_background;
    if(background.resource){this.state.bg_picture=background.resource;this.state.clut='';}
    this.scenarioBackgrounds.set(node.id,this.state.bg_picture);
    console.info('STORY_SCRIPT_BACKGROUND',JSON.stringify({node:node.id,scenario:node.scenario_id,
      authored:node.bg_picture,...background,effective:this.state.bg_picture}));
  }
  async model(id,generation){
    if(!this.models.has(id))this.models.set(id,await readJSON('/api/model/'+encodeURIComponent(id)));
    this.check(generation);
    if(this.actor.detail?.id!==id||!this.actor.ready)await this.actor.load(this.models.get(id));
    this.check(generation);
  }
  async voiceResource(node,generation){
    if(!node.cue)return null;
    if(!node.bank)throw new Error('所选语音没有音库，请返回编辑修正');
    if(!this.banks.has(node.bank))this.banks.set(node.bank,await readJSON('/api/voices/'+encodeURIComponent(node.bank)));
    this.check(generation);
    const voice=this.banks.get(node.bank).find(row=>row.cue===node.cue);
    if(!voice)throw new Error('语音资源不存在：'+node.bank+'/'+node.cue);
    return voice;
  }
  motionSelection(node){
    if(this.state.model!==node.model)this.state={...this.state,model:node.model,body:'',face:'',face_reset:false,extras:{}};
    // Match the server's graph resolver: native nonempty motion commands
    // clear the previous expression override before applying this command.
    // With no command, the current layers keep running. Do not manufacture
    // a face_* field from act_* or copy a resolved face into the draft.
    if(node.body||node.face||node.extra_motions.length){this.state.face='';this.state.face_reset=true;}
    const held=[],states=this.motionIndex.models[node.model].states;
    const tokens=new Set(this.actor.detail.motions.map(row=>row.token));
    for(const token of node.extra_motions)
      if(!tokens.has(token))throw new Error('所选模型没有动作：'+token);
    for(const kind of ['body','face']){
      if(node[kind])this.state[kind]=node[kind];
      else if(this.state[kind])held.push({layer:this.program.semantics.motion_layers[kind],token:heldState(this.actor.detail,this.state[kind])});
    }
    const layers=new Set(node.extra_motions.flatMap(token=>extraLayers(states,token,this.program.semantics)));
    for(const[layer,token]of Object.entries(this.state.extras))if(!layers.has(layer)&&token)held.push({layer,token:heldState(this.actor.detail,token)});
    for(const token of node.extra_motions)for(const layer of extraLayers(states,token,this.program.semantics))this.state.extras[layer]=token;
    return {body:motionState(this.actor.detail,node.body),face:motionState(this.actor.detail,node.face),
      extra:node.extra_motions,held,
      command:[node.body,node.face,...node.extra_motions].filter(Boolean).join(','),
      clearLayers:this.state.face_reset&&!this.state.face?[this.program.semantics.motion_layers.face]:[],allowStill:true};
  }
  async enter(id){
    cancelAnimationFrame(this.frame);
    const previous=this.nodeBeforeSkip||this.node,generation=++this.generation;this.node=this.nodes.get(id);
    try{
    if(!this.node)throw new Error('此连接没有可播放的目标节点');
    const node=this.node;document.body.dataset.node=id;this.cardOut=false;this.nodeBegan=performance.now();this.timing('enter');
    this.setPhase('loading');this.status('正在读取节点资源…');
    this.choiceInput.close();
    $('choices').replaceChildren();$('accessibleText').textContent='';
    // Keep the current card and its animator alive through resource awaits.
    // Only speech ends at this boundary. Content is replaced once its next
    // resource is ready; Stop/replay still explicitly pause/reset the actor.
    this.actor.finishLine();this.cast.finishLine();this.dialogueVoice.stop();$('movie').pause();
    if(this.program.preview_policy?.skip_node_kinds.includes(node.kind)){
      // Omitted gameplay has no visual card and executes no gameplay-specific
      // commands. Retain the last presented node across a chain of skips so
      // the next real card still performs its normal outgoing transition.
      this.nodeBeforeSkip=previous;
      return this.skipGameplayNode(generation);
    }
    this.nodeBeforeSkip=null;this.skippedPath.clear();
    // An unsupported native parameter must be visible at the affected node.
    // Silently discarding it would make the review preview appear authoritative.
    if(node.native_unsupported)throw new Error(node.native_unsupported);
    if(!this.config.playable_kinds.includes(node.kind))
      throw new Error('此节点为「'+this.program.semantics.scenario_types.find(row=>row.kind===node.kind).label+'」，原版流程尚未实现。请返回编辑，选择已支持的节点作为预览入口。');
    console.info('STORY_PLAYER_ENTER',id,node.kind);
    const from=this.cardContent(previous),to=this.cardContent(node);
    const changing=from!==null&&to!==null&&!this.skipInOut(previous,node)&&this.transitions.cardState==='in';
    console.info('STORY_CARD_CHANGE',JSON.stringify({source:previous?.id||'',target:id,from,to,
      cardState:this.transitions.cardState,animate:changing}));
    if(changing){
      // Automatic character replacement uses the existing card compositor;
      // it is not an authored CardOut command and adds no node/actor flags.
      // Finish fading the outgoing card before changing models, motions or
      // backgrounds. Hold alpha at zero through every resource await, then
      // run the extracted Card_in curve only after the whole cast is ready.
      // An explicit Out has already hidden the card, and End/CardStay retains
      // it; neither path should receive another automatic outgoing animation.
      this.setPhase('transition');this.status('正在切换画面…');this.timing('card_change_begin');
      this.closePanel().catch(error=>this.fail(error));
      await this.transitions.cardOut();this.effects.cardOut();this.check(generation);this.timing('card_change_hidden');
    }
    // Chart/title silence is presentation state, independent of script BGM
    // ownership. Keep the same track advancing while muted; entering the next
    // article restores audibility without seeking or issuing another Play.
    this.music.setMuted(node.title_mode==='scene'&&this.config.flow.mute_bgm);
    let selection=null;
    if(!node.actors.length){
      this.cast.rows=[];this.cast.visible(false);this.cast.present=new Set();this.cast.states.clear();this.state.actors=[];
    }
    // Native ADVPlayer.InitScenario calls UIController.SetLive2DChara before
    // executing the command phases. Motion is not part of PanelSequence:
    // command[1] Wait delays dialogue/voice while the actor keeps animating.
    // Commit motion once here, and never restart it when the text begins.
    if(node.kind!=='movie'&&!node.character_image&&node.actors.length){
      if(!await this.cast.show(node.actors,this.state))this.check(generation);
      this.check(generation);this.state.actors=[...this.cast.states.values()];this.timing('cast_ready');
    }else if(node.kind!=='movie'&&!node.character_image&&node.model){
      await this.model(node.model,generation);selection=this.motionSelection(node);
      await this.actor.applyStoryMotion(selection);this.check(generation);this.timing('motion_ready');
    }
    // UIController.ShowTextPanel (RVA 0x1688970) calls PlayNormalVoice before
    // displaying text. Keep that boundary after phase 1, while preparing its
    // media before any authored effects. Explicit Wait/WaitClick still delay
    // the voice; Quake's visual duration does not delay the command queue.
    const dialogueVoice=selection?this.actor.dialogueVoice:this.dialogueVoice;
    if(node.kind!=='title'){
      this.timing('voice_prepare_begin');
      await dialogueVoice.prepare(await this.voiceResource(node,generation));
      this.check(generation);this.timing('voice_ready');
      this.scene.prepareText(node,$('language').value);this.timing('text_ready');
    }
    await prepareCommandResources(node.phases,this.sounds,this.effects);
    this.check(generation);this.timing('command_resources_ready');
    if(node.music.action!=='inherit'){
      await this.music.apply(node.music.resource,{...node.music,key:id+':'+generation,start:true});
      this.state.bg_music=node.music.resource;
    }
    this.check(generation);
    await this.phaseCommands(0,generation);this.check(generation);
    if(node.kind==='title'){await this.title(generation);return;}
    this.setScriptBackground();
    // CardProc awaits SetBG and CardSetImage together. The latter installs a
    // black display background before loading a CG, independently of the
    // resolved script BG. SetScriptParamater can also resolve black from an
    // unreachable source row; its commands are not part of this route.
    // the hidden foreground and native Card_in curve expose this black frame
    // without inventing a blank scenario or an extra 500 ms script wait.
    // Native CardSetMovie also replaces the display plate with black. Keep
    // both card and backdrop black through movie completion and its authored
    // exit commands; the next node still resolves its own script background.
    const background=node.kind==='movie'?this.program.semantics.movie_background:
      node.character_image?this.program.semantics.illustration_background:this.state.bg_picture;
    if(background===null)throw new Error('背景仍有入线冲突，请返回编辑选择预览入线');
    await Promise.all([this.background.show(background),this.backdrop.show(background),
      this.actor.lighting.apply(this.state),this.cast.lighting(this.state)]);this.check(generation);
    if(node.kind==='movie'){
      if(!node.movie_resource)throw new Error('动画节点尚未选择原始短片资源');
      // MovieProc (adv.html:7173) awaits CardIn before PlayMovie, also present
      // in Director.Movie_Init (0x1712780 -> 0x171282c). The movie surface has
      // no decoded frame during this entry animation. Clear the old foreground
      // and run the extracted Card_wait/Card_in over the black display plate;
      // showing the card immediately erased this pre-movie interval. Do not
      // turn its animation duration into an additional authored Wait command.
      this.state.model='';this.scene.clear();this.display('empty');
      this.setPhase('transition');this.status('正在准备原始动画…');this.timing('movie_card_in_begin');
      await this.transitions.cardIn();this.check(generation);this.timing('movie_card_in_complete');
      if(changing)this.timing('card_change_complete');
      this.setPhase('movie');this.status('原始动画播放中…');this.timing('movie_play_begin');
      await this.movie(node.movie_resource,generation);
      this.check(generation);this.timing('movie_play_complete');
    }else if(node.character_image){
      this.state.model='';await this.image($('picture'),'/picture/'+encodeURIComponent(node.character_image),generation);this.display('picture');
    }else if(node.actors.length||node.model){this.display('actor');}
    else{this.state={...this.state,model:'',body:'',face:'',face_reset:false,extras:{}};this.display('empty');}
    this.check(generation);
    if(node.kind!=='movie')await this.transitions.cardIn();this.check(generation);
    if(changing&&node.kind!=='movie')this.timing('card_change_complete');
    await this.phaseCommands(1,generation);this.check(generation);
    // A restored voice offset belongs to this node's speech clock, not to the
    // command queue or text clock. Keep ordinary zero-delay playback awaited;
    // a positive offset schedules speech while the panel reveals normally.
    const voiceStart=dialogueVoice.play(node.voice_delay_ms);
    voiceStart.catch(error=>{if(generation===this.generation)this.fail(error);});
    if(node.voice_delay_ms===0)await voiceStart;
    this.check(generation);
    this.visible=0;this.length=this.scene.text(node,$('language').value,0);this.accessible();
    this.timing('text_begin');
    const history=document.createElement('li');history.textContent=[node.speaker,node.text].filter(Boolean).join('：');$('history').append(history);
    if(!this.length){await this.afterText(generation);if(generation===this.generation)this.animate(generation);return;}
    this.setPhase('text');this.status('点击补全台词；再次点击继续。');
    if(node.actors.length)this.cast.beginTalk();else if(selection)this.actor.animator.beginTalk();
    this.textBegan=performance.now();this.readySince=null;this.animate(generation);
    }catch(error){
      // Closing or replacing the embedded preview can reject a pending fetch.
      // That rejection belongs to the cancelled node, not the next preview;
      // distinguish it with the same generation used by successful awaits.
      this.check(generation);throw error;
    }
  }
  async skipGameplayNode(generation){
    const node=this.node,definition=this.program.semantics.scenario_types.find(row=>row.kind===node.kind);
    const edges=this.program.edges.filter(edge=>edge.source===node.id&&edge.state!=='excluded');
    const label=definition?.label||node.kind;
    if(this.skippedPath.has(node.id)){
      console.error('STORY_PLAYER_SKIP_CYCLE',JSON.stringify({node:node.id,path:[...this.skippedPath]}));
      throw new Error('教程／战斗的后续连接形成循环，请检查连接。');
    }
    this.skippedPath.add(node.id);
    console.info('STORY_PLAYER_NATIVE_SKIP',JSON.stringify({node:node.id,scenario:node.scenario_id,kind:node.kind,
      edges:edges.map(edge=>({id:edge.id,target:edge.target,available:edge.available,transition:edge.transition})),milliseconds:performance.now()}));
    if(!edges.length)throw new Error(label+'已跳过，但没有后续剧情连接。');
    if(edges.length===1){
      if(!this.available(edges[0]))throw new Error(label+'已跳过，但后续剧情尚未恢复。');
      this.status('已跳过'+label+'，继续剧情…');
      // Yield between omitted nodes, allowing Stop/replay to cancel a chain.
      // Returning the next execution promise preserves its own error context.
      await Promise.resolve();this.check(generation);
      return this.follow(edges[0]);
    }
    // Battles can have several native exits. Skipping gameplay does not pick
    // a win/loss or other route on the reviewer's behalf. Keep those exits as
    // explicit in-frame choices, including disabled, still-missing targets.
    this.setPhase('skipped-choice');this.status(label+'已跳过，请选择后续剧情。');
    this.flowView.continuations(label,edges.map((edge,index)=>({...edge,
      label:edge.label_translation||edge.label||this.nodes.get(edge.target)?.translation||`后续 ${index+1}`})),edge=>{
      if(this.generation!==generation||this.phase!=='skipped-choice'||!this.available(edge))return;
      this.flowView.close();this.setPhase('loading');this.follow(edge).catch(error=>this.fail(error));
    });
  }
  accessible(){
    const language=$('language').value;
    $('accessibleText').textContent=[this.scene.speakerName(this.node,language),language==='zh'?this.node.translation:this.node.text].filter(Boolean).join('\n');
  }
  animate(generation){
    const tick=now=>{
      if(generation!==this.generation)return;
      if(this.phase==='text'){
        this.visible=Math.min(this.length,Math.floor((now-this.textBegan)*this.config.text_speed/1000));this.scene.draw(this.visible);
        if(this.visible===this.length){this.afterText(generation).catch(error=>this.fail(error));}
      }
      if(this.phase==='ready'&&this.auto){
        const speaking=this.actor.dialogueVoice.cancelPlay||this.dialogueVoice.cancelPlay||
          [this.actor.audio,this.voice].some(audio=>!audio.paused&&!audio.ended);
        if(speaking)this.readySince=null;
        else if(this.readySince===null)this.readySince=now;
        else if(now-this.readySince>=this.config.auto_margin_seconds*1000){this.advance().catch(error=>this.fail(error));return;}
      }
      this.frame=requestAnimationFrame(tick);
    };this.frame=requestAnimationFrame(tick);
  }
  async afterText(generation){
    this.actor.animator?.endTalk();
    this.cast.endTalk();
    this.setPhase('command');this.visible=this.length;this.scene.draw(this.visible);
    await this.phaseCommands(2,generation);this.check(generation);
    const edges=this.program.edges.filter(edge=>edge.source===this.node.id);
    const choices=edges.filter(edge=>edge.kind==='choice');
    if(choices.length){
      if(choices.length!==this.config.choice_count||edges.length!==choices.length)
        throw new Error('原版选择流程需要恰好两个选项，且不能混有顺序后续；请返回编辑修正连接');
      this.setPhase('choice');
      for(const edge of [...choices].sort((a,b)=>a.side.localeCompare(b.side))){
        const button=document.createElement('button'),available=this.available(edge);
        button.dataset.edge=edge.id;
        button.disabled=!available;button.textContent=(edge.side==='left'?'← ':'→ ')+(edge.label||'（未填写选项文字）')+(available?(edge.state==='proposed'?' · 待确认':''):' · 未恢复');
        button.onclick=()=>{if(this.phase==='choice')this.choiceInput.select(edge.side);};
        $('choices').append(button);
      }
      // Only executed native commands own this flag. The editor's derived
      // summary cannot bypass End, command errors, or route inheritance.
      this.choiceView.critical=!!this.state.junction;
      console.info('STORY_JUNCTION_CHOICE',JSON.stringify({node:this.node.id,
        marked:this.choiceView.critical,milliseconds:performance.now()}));
      this.choiceInput.open(choices.map(edge=>({...edge,available:this.available(edge)})),$('language').value);
    }else{
      if(edges.length>1)throw new Error('存在多条顺序后续，请返回编辑确定连接');
      this.next=edges[0];this.setPhase('ready');this.readySince=null;
      // CardProc bypasses CardWaitUserDrop only after an explicit CardOut.
      // A blank card without that command still needs the normal user input.
      if(this.cardOut){await this.advance();return;}
      this.status(this.next?(this.available(this.next)?'点击继续'+(this.next.state==='proposed'?' · 下一连接待确认':''):'后续尚未恢复；点击结束本次预览。'):'此片段没有已连接的后续；点击结束本次预览。');
    }
  }
  available(edge){return edge.available;}
  choiceChanged(edge){
    $('advance').disabled=!edge?.available;
    for(const button of $('choices').children){
      const option=this.choiceInput.edges.find(row=>row.id===button.dataset.edge);
      button.setAttribute('aria-pressed',String(option.id===edge?.id));
      button.textContent=(option.side==='left'?'← ':'→ ')+this.choiceView.text(option,'label',$('language').value)+
        (option.available?(option.state==='proposed'?' · 待确认':''):' · 未恢复');
    }
    this.accessible();
    if(!edge){this.status('左右拖动画面选择，展开气泡后松开确认；拖回中间取消。缺失分支保持锁定。');return;}
    // The quote and its translation have their own recording evidence. A
    // missing destination must disable confirmation, not hide known text
    // from either the canvas or the accessible transcript. Keep the exact
    // same selection/commit gate for mouse, keyboard and parent controls.
    const quote=this.choiceView.text(edge,'quote',$('language').value);
    $('accessibleText').textContent+='\n'+this.choiceView.text(edge,'label',$('language').value)+(quote?'\n'+quote:'');
    console.info('STORY_CHOICE_QUOTE',JSON.stringify({edge:edge.id,language:$('language').value,
      available:edge.available,characters:quote.length,milliseconds:performance.now()}));
    if(!edge.available){this.status((quote?'气泡可预览；':'')+'此分支尚未恢复，不能确认；拖回中间可取消。');return;}
    this.status('已展开「'+edge.label+'」；松开拖动确认，或点击「继续」。Esc 取消选择。');
  }
  async chooseBranch(edge){
    if(this.phase!=='choice')return;
    const generation=this.generation;cancelAnimationFrame(this.frame);
    this.setPhase('transition');this.status('正在切换选项后的画面…');
    this.state.junction=false;
    console.info('STORY_JUNCTION_CONSUMED',JSON.stringify({node:this.node.id,
      edge:edge.id,milliseconds:performance.now()}));
    // Native SelectSequence returns only after the selected card has left,
    // CardInit has cleared its foreground and Delay(166) has completed.
    // This applies even when both choices retain the same actor or CG. Keep
    // the interval outside script commands/edges, and retain the background
    // plane: it need not be black until CardSetImage installs a CG's black BG.
    // Stop/replay cancels either awaited boundary before any route is followed.
    this.actor.finishLine();this.cast.finishLine();this.dialogueVoice.stop();
    await this.transitions.cardOut(this.choiceView.card);this.check(generation);
    // SelectedBranch waits for PlaySelectChoiceUI's completion callback;
    // CloseTextPanel(true) starts TextPanel.Decide at the same boundary.
    // These extracted panel animations run over the retained background,
    // before CardInit and the separate HTML Delay(166). Resource/network or
    // reward latency from a recording must not become a fixed black timer.
    this.choiceView.paint(true);
    const quote=this.transitions.panelOut(this.choiceView.canvas,'choice_'+edge.side);
    this.choiceView.canvas.hidden=true;
    await Promise.all([quote,this.closePanel('decide')]);this.check(generation);
    this.choiceInput.close();
    this.effects.cardOut();this.display('empty');this.transitions.hide();
    $('choices').replaceChildren();this.timing('choice_card_init');
    await this.effects.wait(this.config.choices.settle_milliseconds,false);this.check(generation);
    this.timing('choice_settle_complete');
    const row=document.createElement('li');row.textContent=[edge.label,edge.quote].filter(Boolean).join('：');
    $('history').append(row);
    await this.follow(edge);
  }
  resumeAudio(){
    // A preview may prepare sound before the browser grants playback. Retry
    // each owned channel from a real interaction while leaving node entry and
    // native command phases independent of that permission boundary.
    this.music.resume();
    for(const voice of [this.dialogueVoice,this.actor.dialogueVoice])voice.resume().catch(error=>this.fail(error));
  }
  async advance(){
    this.resumeAudio();
    if(this.phase==='chart'){
      this.chartContinue?.();
    }else if(this.phase==='choice'){
      this.choiceInput.confirm();
    }else if(this.phase==='text'){
      this.visible=this.length;await this.afterText(this.generation);
    }else if(this.phase==='ready'){
      cancelAnimationFrame(this.frame);
      if(this.next&&this.available(this.next)){this.setPhase('loading');await this.follow(this.next);}
      else{
        const reason=this.next?.flow_error||(this.next?.transition.label==='FINISH'?'FINISH 的目标节点／场景入口尚未恢复，请在剧情工作区指定入口。':'已到此片段的连接末端。返回编辑可补充后续。');
        this.stop();this.status(reason);
      }
    }
  }
  async follow(edge){
    console.info('STORY_PLAYER_TRANSITION',JSON.stringify({edge:edge.id,action:edge.flow_action,native:edge.native_transition,target:edge.target}));
    this.visitedEdges.add(edge.id);
    if(edge.transition.label==='FINISH'){
      this.completedScenes.add(edge.source_scene);
      if(edge.flow_action==='section'){
        // Native end titles skip the opening interval, then ADVFinish returns
        // to the completed section's chart. Keep its authored victory track
        // playing while disposing card/media work; Stop/replay still owns its
        // cancellation. The final chart retains the route actually traversed.
        const source=this.program.directory.entries.find(row=>row.id===edge.source_scene);
        const section=this.program.directory.entries.find(row=>row.id===source.parent);
        this.stop({keepMusic:true});
        this.flowView.chart(this.program,this.node,this.completedScenes,null,this.config.flow.chart,this.visitedEdges);
        this.setPhase('complete');
        console.info('STORY_PLAYER_SECTION_COMPLETE',section.id,[...this.completedScenes],[...this.visitedEdges]);
        this.status('本话已结束。FINISH 的目标属于另一话，本次预览到此结束。');return;
      }
    }
    if(!this.available(edge))throw new Error(edge.flow_error||'目标节点／场景入口尚未恢复');
    await this.enter(edge.target);
  }
  async title(generation){
    const scene=this.program.directory.entries.find(row=>row.id===this.node.scene_id);
    if(!scene)throw new Error('标题节点需要先归入剧情场景');
    this.scene.clear();this.display('empty');
    // ADVPlayer.IsSkipInterval calls ScenarioUtil.IsEndTitle. A terminal TITLE
    // therefore executes SetTitle immediately; only an ordinary TITLE waits
    // on the opening chart. Never infer this distinction from "CLEAR" text.
    if(this.node.title_mode==='scene'){
      this.setPhase('chart');this.status('流程图：点击「次に進む」后显示标题。');
      console.info('STORY_PLAYER_CHART',scene.id,[...this.completedScenes]);
      await new Promise((resolve,reject)=>{
        const cancel=()=>{this.pending.delete(cancel);reject(new DOMException('Playback cancelled','AbortError'));};
        this.pending.add(cancel);
        this.chartContinue=()=>{this.chartContinue=null;this.pending.delete(cancel);this.flowView.close();this.setPhase('loading');resolve();};
        this.flowView.chart(this.program,this.node,this.completedScenes,this.chartContinue,this.config.flow.chart,this.visitedEdges);
      });
    }
    this.check(generation);
    // After the optional native interval, TitleProc owns phase 1, SetTitle,
    // phase 2 and the first transition. CardIn/text/drop waits do not belong
    // to either kind of title.
    await this.phaseCommands(1,generation);this.check(generation);
    this.setScriptBackground();
    await Promise.all([this.background.show(this.state.bg_picture),this.backdrop.show(this.state.bg_picture),
      this.actor.lighting.apply(this.state)]);this.check(generation);
    this.flowView.title(this.node,$('language').value,scene);this.setPhase('title');this.status(this.node.translation||this.node.text);
    console.info('STORY_PLAYER_TITLE',this.node.id,this.node.title_mode);
    await this.effects.wait(this.config.flow.title_seconds*1000,false);this.check(generation);this.flowView.close();
    await this.phaseCommands(2,generation);this.check(generation);
    const edges=this.program.edges.filter(edge=>edge.source===this.node.id);
    if(edges.length!==1)throw new Error('标题节点需要且只能有一条后续转移');
    if(!this.available(edges[0]))throw new Error(edges[0].flow_error||'标题的后续节点／场景入口尚未恢复');
    await this.follow(edges[0]);
  }
  async movie(id,generation){
    const video=$('movie');setMoviePresentation(video,id,this.config.movies);
    video.src='/movie/'+encodeURIComponent(id);this.display('movie');
    await new Promise((resolve,reject)=>{
      const cancel=()=>finish(new DOMException('Playback cancelled','AbortError'));
      const finish=error=>{video.onended=null;video.onerror=null;video.onloadedmetadata=null;this.pending.delete(cancel);error?reject(error):resolve();};
      video.onloadedmetadata=()=>console.info('STORY_PLAYER_MOVIE',JSON.stringify({node:this.node.id,resource:id,
        source:[video.videoWidth,video.videoHeight],viewport:[video.clientWidth,video.clientHeight],
        presentation:video.dataset.moviePresentation,fit:getComputedStyle(video).objectFit,
        background:this.background.resource,duration:video.duration}));
      this.pending.add(cancel);video.onended=()=>finish();video.onerror=()=>finish(new Error('动画资源读取失败：'+id));
      video.play().catch(finish);
    });this.check(generation);
  }
}

const player=new StoryPlayer();
window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==parent)return;
  if(event.data.type==='stella-player-handshake'&&player.isReady)parent.postMessage({type:'stella-player-ready'},location.origin);
  if(event.data.type==='stella-player-load')player.receive(event.data.program).catch(error=>player.fail(error));
  if(event.data.type==='stella-player-stop')player.stop();
  if(event.data.type==='stella-player-action'){
    const {action,value}=event.data;
    if(action==='language'){$('language').value=value;$('language').dispatchEvent(new Event('change'));player.publish();}
    else if(action==='choice'){
      const button=[...$('choices').children].find(button=>button.dataset.edge===value);if(button&&!button.disabled)button.click();
    }else if(['advance','auto','restart','stop','close','effectContinue'].includes(action)){
      const button=$(action);if(!button.disabled&&!button.hidden)button.click();
    }
  }
});
player.setup().then(()=>parent.postMessage({type:'stella-player-ready'},location.origin)).catch(error=>player.fail(error));
