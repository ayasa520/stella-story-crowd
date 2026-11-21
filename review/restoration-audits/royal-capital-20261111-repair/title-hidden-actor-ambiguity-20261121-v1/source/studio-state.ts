import semantics from "@/config/semantics.json";
import previewPolicy from "@/config/preview-policy.json";
import {clone,same} from "./native";
import {compileCommands,compileMusic} from "./preview-commands";
import {initialPreviewState} from "./preview";
import {RepositoryError} from "./errors";
import type {AssetCatalog,MotionIndex} from "./resources";
import type {StudioRecord} from "./studio-native";

const excludedLayers=new Set([...Object.values(semantics.motion_layers),...semantics.excluded_motion_layers]);
const unknownState=()=>Object.fromEntries(Object.keys(initialPreviewState()).map(key=>[key,null]));
const stateLabels:Record<string,string>={bg_picture:"背景",clut:"光照",bg_music:"背景音乐",model:"人物",
  body:"身体动作",face:"表情",face_reset:"表情状态",extras:"附加动作",actors:"人物演出",ambient:"环境音",
  wipe_name:"转场",wipe_image:"转场画面",wipe_covered:"遮罩状态",junction:"分支提示"};

/** This is the server's pure counterpart of StorySemantics in the desktop
 * workbench. Random-access inspection follows actual graph predecessors, not
 * recording time, and unresolved joins stay unknown instead of borrowing an
 * arbitrary branch. The resulting state is never written into native files.
 */
export function resolveStudioState(project:StudioRecord,id:string,choices:StudioRecord,assets:AssetCatalog,motionIndex:MotionIndex){
  function layers(model:string,token:string):string[]{
    const states=motionIndex.models[model]?.states;
    if(!states?.[token])throw new RepositoryError(`角色 ${model} 的控制器未收录动作 ${token}。`,422);
    return states[token].map(row=>row.layer).filter(layer=>!excludedLayers.has(layer));
  }
  const nodes=new Map<string,StudioRecord>(project.nodes.filter((node:StudioRecord)=>node.review_state!=="excluded").map((node:StudioRecord)=>[node.id,node]));
  if(!nodes.has(id))throw new RepositoryError("节点不存在或已排除。",422);
  const incomingByTarget=new Map<string,StudioRecord[]>(),choiceSources=new Set<string>();
  for(const edge of project.edges){
    if(!edge.available||edge.flow_action==="section"||!nodes.has(edge.source)||!nodes.has(edge.target))continue;
    const incoming=incomingByTarget.get(edge.target);
    if(incoming)incoming.push(edge);else incomingByTarget.set(edge.target,[edge]);
    if(edge.kind==="choice")choiceSources.add(edge.source);
  }
  const sounds=new Map(Object.values(assets.sound_effects).map(row=>[row.cue,row]));
  const warnings:string[]=[],cache=new Map<string,StudioRecord>(),visiting=new Set<string>();
  const joins:{node:string;incoming:StudioRecord[];conflicts:Set<string>}[]=[];
  function applyCommands(state:StudioRecord,rows:StudioRecord[]){
    for(const row of rows){
      if(row.terminates_block)break;
      if(row.kind==="music"){state.bg_music="";state.music_source="";}
      else if(row.kind==="junction")state.junction=true;
      else if(row.kind==="lighting"&&row.resource!=="OFF")state.clut=row.resource;
      else if(row.kind==="wipe"){
        if(row.action==="out")Object.assign(state,{wipe_name:row.resource,wipe_image:(row.image||"fade_color_black").replace(/\.png$/,""),wipe_covered:true});
        else Object.assign(state,{wipe_image:"",wipe_covered:false});
      }else if(row.kind==="sound"&&row.cue){
        if(state.ambient===null)continue;
        if(row.action==="stop")state.ambient[row.cue]=false;
        else if(sounds.get(row.cue)?.loop)state.ambient[row.cue]=true;
      }
    }
  }
  function apply(node:StudioRecord,before:StudioRecord){
    // The preview intentionally omits native gameplay nodes. They preserve
    // incoming presentation state rather than making every downstream field
    // unknown or executing battle/tutorial-only effects. This is the same
    // policy consumed by StoryPlayer; the authored script remains untouched.
    if(previewPolicy.skip_node_kinds.includes(node.kind))return {
      before,entry:clone(before),display:clone(before),after:clone(before),
      music:compileMusic("",semantics.bgm_fade_seconds),phases:[[],[],[]],unsupported:[],skipped:true,
    };
    const state=clone(before),phases=node.command.map((block:string)=>compileCommands(block,assets.visual_effects));
    const definition=semantics.scenario_types.find(type=>type.kind===node.kind)!;
    const background=node.script_background.resource,music=compileMusic(node.bg_music,semantics.bgm_fade_seconds);
    if(music.action==="stop")Object.assign(state,{bg_music:"",music_source:""});
    else if(music.action==="play"){
      if(music.restart||state.bg_music!==music.resource)state.music_source=node.id;
      state.bg_music=music.resource;
    }
    const unsupported=phases.flat().filter((row:StudioRecord)=>row.kind==="unsupported").map((row:StudioRecord)=>row.command);
    if(node.native_unsupported)unsupported.push(node.native_unsupported);
    if(definition.player==="title"){
      applyCommands(state,phases[0]);const entry=clone(state);applyCommands(state,phases[1]);
      if(background)Object.assign(state,{bg_picture:background,clut:""});
      const display=clone(state);applyCommands(state,phases[2]);
      return {before,entry,display,after:state,music,phases,unsupported};
    }
    if(!definition.preview)return {before,entry:unknownState(),display:unknownState(),after:unknownState(),music:compileMusic("",semantics.bgm_fade_seconds),phases,unsupported:["节点类型："+definition.label]};
    applyCommands(state,phases[0]);
    if(background)Object.assign(state,{bg_picture:background,clut:""});
    if(node.model!==state.model)Object.assign(state,{model:node.model,body:"",face:"",face_reset:false,extras:{}});
    const previous=new Map<string,StudioRecord>((state.actors||[]).map((actor:StudioRecord)=>[actor.model,actor]));
    state.actors=node.actors.map((actor:StudioRecord)=>{
      const resolved=clone(actor),prior=previous.get(actor.model);
      resolved.face_reset=!!(actor.body||actor.face||actor.extra_motions.length);
      if(prior){
        if(!actor.body)resolved.body=prior.body;
        if(!resolved.face_reset){resolved.face=prior.face;resolved.face_reset=prior.face_reset;}
        resolved.extra_motions=[...prior.extra_motions];
      }
      for(const token of actor.extra_motions){
        const replacing=new Set(layers(actor.model,token));
        resolved.extra_motions=resolved.extra_motions.filter((old:string)=>!layers(actor.model,old).some(layer=>replacing.has(layer))).concat(token);
      }
      return resolved;
    });
    // Native Motion.PlayMotion clears the face layer whenever any explicit
    // motion token is present. An entirely empty command retains that layer.
    if(node.body||node.face||node.extra_motions.length)Object.assign(state,{face:"",face_reset:true});
    for(const key of ["body","face"])if(node[key])state[key]=node[key];
    for(const token of node.extra_motions)for(const layer of layers(node.model,token))if(state.extras!==null)state.extras[layer]=token;
    const entry=clone(state);let display:StudioRecord;
    if(node.kind==="movie"){
      display={...clone(state),bg_picture:semantics.movie_background};applyCommands(state,phases[1]);
    }else{
      applyCommands(state,phases[1]);display=clone(state);
      if(node.character_image)display.bg_picture=semantics.illustration_background;
    }
    applyCommands(state,phases[2]);
    if(choiceSources.has(node.id))state.junction=false;
    return {before,entry,display,after:state,music,phases,unsupported};
  }
  function visit(key:string):StudioRecord{
    if(cache.has(key))return cache.get(key)!;
    if(visiting.has(key)){warnings.push("存在循环，需通过已选路线确定进入状态");return {after:unknownState()};}
    visiting.add(key);
    const incoming=incomingByTarget.get(key)||[];
    const selected=choices[key]?incoming.filter((edge:StudioRecord)=>edge.id===choices[key]):incoming;
    if(choices[key]&&!selected.length)throw new RepositoryError("所选预览入线已不存在。",422);
    const parents=selected.map((edge:StudioRecord)=>visit(edge.source).after);
    if(selected.some((edge:StudioRecord)=>edge.state==="proposed"))warnings.push("预览包含尚未确认的连接");
    const before:StudioRecord=initialPreviewState();
    // Record where predecessor states diverge. An inherited null passing
    // through a node with a single incoming edge cannot be resolved there.
    // Keep the upstream join available after a choice so it can be changed.
    const conflicts=new Set<string>();
    const merge=(field:string,values:unknown[])=>{
      if(values.every(value=>same(value,values[0])))return clone(values[0]);
      conflicts.add(field);return null;
    };
    if(parents.length)for(const field of Object.keys(before)){
      const values=parents.map((parent:StudioRecord)=>parent[field]);
      if(["extras","ambient"].includes(field)&&values.every((value:unknown)=>value!==null&&typeof value==="object"&&!Array.isArray(value))){
        before[field]={};
        for(const layer of new Set<string>(values.flatMap((value:StudioRecord)=>Object.keys(value)))){
          const tokens=values.map((value:StudioRecord)=>Object.hasOwn(value,layer)?value[layer]:(field==="ambient"?false:""));
          before[field][layer]=merge(`${field}.${layer}`,tokens);
        }
      }else before[field]=merge(field,values);
    }
    if(key!==id&&incoming.length>1)joins.push({node:key,incoming,conflicts});
    const result={...apply(nodes.get(key)!,before),incoming};cache.set(key,result);visiting.delete(key);return result;
  }
  const result=visit(id);result.warnings=[...new Set(warnings)];
  // An empty-actor title hides foreground and skips actor preparation.
  // Filter only its blocking diagnostics; preserve all incoming/resolved
  // state so later nodes still receive unknown predecessor values.
  // Background, music, ambient sound and command effects remain relevant.
  const target=nodes.get(id)!;
  const hiddenFields=target.kind==="title"&&!target.model&&!target.actors.length?
    new Set(["model","body","face","face_reset","extras","actors"]):new Set<string>();
  result.ambiguous=Object.entries(result.display).filter(([key,value])=>value===null&&key!=="music_source"&&!hiddenFields.has(key)).map(([key])=>key);
  for(const field of ["extras","ambient"]){
    if(hiddenFields.has(field))continue;
    for(const [layer,value]of Object.entries(result.display[field]||{}))if(value===null)result.ambiguous.push(`${field}.${layer}`);
  }
  // Keep machine-readable field identities for route resolution. Presentation
  // labels are a separate projection so explaining a conflict never changes
  // the merge result or silently chooses a predecessor on the user's behalf.
  result.ambiguous_labels=[...new Set(result.ambiguous.map((field:string)=>stateLabels[field.split(".")[0]]||"演出状态"))];
  const unresolved=(field:string)=>result.ambiguous.some((key:string)=>key===field||key.startsWith(`${field}.`)||field.startsWith(`${key}.`));
  result.upstreamIncoming=joins.reverse().filter(({node,conflicts})=>choices[node]||[...conflicts].some(unresolved))
    .map(({node,incoming})=>({node,incoming:incoming.map(({id,source,label,state})=>({id,source,label,state}))}));
  return result;
}
