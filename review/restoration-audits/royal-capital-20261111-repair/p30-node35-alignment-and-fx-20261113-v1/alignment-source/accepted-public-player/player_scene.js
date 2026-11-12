import {NativePlacedViewer} from './actor_placement.js';
import {ActorAnimation} from './actor_animation.js';
import {textPanelRows,reportTextPanelLayout} from './text_panel_presentation.js';

export async function readJSON(url){
  const response=await fetch(url);
  if(!response.ok)throw new Error(`读取失败：${url} (${response.status})`);
  return response.json();
}
export const loadImage=url=>new Promise((resolve,reject)=>{
  const image=new Image();image.onload=()=>resolve(image);
  image.onerror=()=>reject(new Error('图片读取失败：'+url));image.src=url;
});

export class StoryActor extends NativePlacedViewer {
  async load(detail){
    this.animator=null;
    if(!await super.load(detail))return false;
    const generation=this.loadGeneration;
    const animator=new ActorAnimation(this,this.animationAssets.models[detail.id],this.playerConfig.talk);
    await animator.setup();
    await animator.prepareChoice({...this.playerConfig.choices,...this.assets.choice_motion});
    if(generation!==this.loadGeneration)return false;
    this.animator=animator;return true;
  }
  async applyStoryMotion(selection){
    const generation=++this.generation;this.audio.pause();
    await this.animator.select(selection,()=>generation===this.generation);
  }
  finishLine(){
    this.generation++;this.dialogueVoice.stop();
    this.animator?.endTalk();
  }
  stop(){super.stop();this.animator?.pause();}
  tick(){}
  renderPose(){
    if(!this.animator){super.renderPose();return;}
    try{this.animator.render();}
    catch(error){this.animator=null;this.onError(error);}
  }
}

class NativeFont {
  constructor(data,atlas,config){this.data=data;this.atlas=atlas;this.config=config;this.cache=new Map();}
  glyph(character){
    const glyph=this.data.glyphs[character.codePointAt(0)];
    if(!glyph)throw new Error(`原版字体没有字符「${character}」，请修正文字或补充字库`);
    return glyph;
  }
  measure(character,size,row){
    let spacing=row.character_spacing;
    // Native TMP adds m_characterSpacing before multiplying by the current
    // font/glyph scale (GenerateTextMesh10035f4→1003604). Title opts into those
    // units explicitly; existing dialogue rows keep their design-pixel units.
    // This narrow projection covers ordinary glyphs only, without rich-size,
    // sprite, glyph-scale or width-compression modifiers.
    if(row.character_spacing_units==='native-font'){
      if(!Number.isFinite(this.data.scale)||this.data.scale<=0)throw new Error('原生字体缩放缺失');
      spacing*=size/this.data.point_size*this.data.scale;
    }
    return this.glyph(character)[4]*size/this.data.point_size+spacing;
  }
  bitmap(character,size,color){
    const key=JSON.stringify([character,size,color]);if(this.cache.has(key))return this.cache.get(key);
    const glyph=this.glyph(character),padding=this.data.padding+1;
    const canvas=document.createElement('canvas');canvas.width=glyph[7]+2*padding;canvas.height=glyph[8]+2*padding;
    const context=canvas.getContext('2d',{willReadFrequently:true});
    context.drawImage(this.atlas,glyph[5]-padding,this.data.size[1]-glyph[6]-glyph[8]-padding,
      canvas.width,canvas.height,0,0,canvas.width,canvas.height);
    const pixels=context.getImageData(0,0,canvas.width,canvas.height),scale=size/this.data.point_size;
    // The source is the actual TMP signed-distance atlas, including the
    // installed Chinese extension. Convert only requested glyph rectangles,
    // avoiding multiple 4096x8192 readback buffers for every preview window.
    const smoothing=this.config.sdf_smoothing/scale,edge=this.config.sdf_edge;
    for(let i=0;i<pixels.data.length;i+=4){
      const t=Math.max(0,Math.min(1,(pixels.data[i+3]/255-edge+smoothing)/(2*smoothing)));
      pixels.data[i]=Math.round(color[0]*255);pixels.data[i+1]=Math.round(color[1]*255);pixels.data[i+2]=Math.round(color[2]*255);
      pixels.data[i+3]=Math.round(t*t*(3-2*t)*color[3]*255);
    }
    context.putImageData(pixels,0,0);this.cache.set(key,canvas);return canvas;
  }
  layout(text,row){
    const chars=Array.from(text),font=this.data,r=row.rect;
    const arrange=size=>{
      const lines=[[]];let width=0;
      for(let index=0;index<chars.length;index++){
        const char=chars[index];if(char==='\n'){lines.push([]);width=0;continue;}
        const advance=this.measure(char,size,row),line=lines.at(-1);
        if(line.length&&width+advance>r.width){
          // Japanese kinsoku rules keep closing punctuation with the previous
          // glyph and opening punctuation with the following glyph. They affect
          // auto-sizing, so wrapping must precede the height calculation.
          let carried=[];
          if(this.config.line_start_prohibited.includes(char))carried.push(line.pop());
          if(line.length&&this.config.line_end_prohibited.includes(line.at(-1).char))carried.unshift(line.pop());
          lines.push(carried);width=carried.reduce((n,g)=>n+g.advance,0);
        }
        lines.at(-1).push({char,index,advance});width+=advance;
      }
      const scale=size/font.point_size;
      const lineHeight=(font.line_height+row.line_spacing)*scale;
      const height=(font.ascent-font.descent)*scale+lineHeight*(lines.length-1);
      return {lines,height,lineHeight,size,scale};
    };
    let size=Math.min(row.base_size,row.max_size),result=arrange(size);
    while(result.height>r.height&&size>row.min_size){size=Math.max(row.min_size,Math.round((size-this.config.font_size_step)*100)/100);result=arrange(size);}
    if(result.height>r.height+.1)throw new Error('台词超出原版字幕框，请拆分节点或减少文字');
    return {...result,length:chars.length};
  }
  draw(context,row,layout,visible=Infinity,glyphColor=null){
    const r=row.rect,{size,scale,lines,height,lineHeight}=layout;
    const vertical=row.alignment&0xff00,horizontal=row.alignment&0xff;
    const top=r.y+(vertical===512?(r.height-height)/2:vertical===1024?r.height-height:0);
    for(let lineIndex=0;lineIndex<lines.length;lineIndex++){
      const line=lines[lineIndex],width=line.reduce((n,g)=>n+g.advance,0);
      let x=r.x+(horizontal===2?(r.width-width)/2:horizontal===4?r.width-width:0);
      const baseline=top+this.data.ascent*scale+lineIndex*lineHeight;
      for(const item of line){
        const g=this.glyph(item.char),padding=this.data.padding+1;
        if(item.index<visible&&g[7]&&g[8]){
          // Optional per-glyph policy shares the native SDF renderer with
          // TitleView. Existing dialogue callers retain their row color and
          // visibility/layout behavior; presentation alpha stays on context.
          const color=glyphColor?glyphColor(item,row):row.color;
          const image=this.bitmap(item.char,size,color);
          context.drawImage(image,x+(g[2]-padding)*scale,baseline-(g[3]+padding)*scale,image.width*scale,image.height*scale);
        }
        x+=item.advance;
      }
    }
  }
}

export class OriginalScene {
  constructor({stage,canvas,viewer}){Object.assign(this,{stage,canvas,viewer});this.context=canvas.getContext('2d');this.images=new Map();this.tints=new Map();this.textPanelLayoutReports=new Map();}
  async setup(config){
    this.config=config;this.assets=await readJSON(config.manifest);
    this.speakerTranslations=(await readJSON(config.speaker_translations)).speakers;
    this.textPanelPresentation=await readJSON(config.text_panel_presentation);
    this.viewer.assets=this.assets;this.viewer.playerConfig=config;
    await this.viewer.lighting.setup(config);
    const [width,height]=this.assets.resolution;this.canvas.width=width;this.canvas.height=height;
    this.stage.style.aspectRatio=`${width}/${height}`;
    this.fonts=new Map(await Promise.all(Object.entries(this.assets.fonts).map(async([id,font])=>
      [id,new NativeFont(font,await loadImage(config.asset_root+font.atlas),config)])));
    const groups=[...Object.values(config.panels),...config.choices.groups];
    const files=new Set(groups.flatMap(group=>this.assets.groups[group].filter(r=>r.type==='image').map(r=>r.sprite.file)));
    files.add(this.assets.choice_card.frame.sprite.file);
    await Promise.all([...files].map(async name=>this.images.set(name,await loadImage(config.asset_root+name))));
  }
  clear(){this.context.clearRect(0,0,this.canvas.width,this.canvas.height);this.panel=null;this.textPanelLayoutReports.clear();}
  speakerName(node,language){
    // Speaker identities remain verbatim OCR evidence in the workspace. Resolve
    // display names from the translation catalog at presentation time so the
    // Japanese preview, matching anchors, and anonymous identities are intact.
    // Canvas subtitles and accessible text share this resolution rule.
    if(language==='ja'||!node.speaker)return node.speaker;
    const name=this.speakerTranslations[node.speaker];
    // Crowd-authored speaker fields are canonical native content. A custom
    // name may already be translated; preserve it verbatim when no glossary
    // alias exists instead of blocking an otherwise valid native edit.
    return name||node.speaker;
  }
  prepareText(node,language){
    let text=language==='zh'?node.translation:node.text;
    if(language==='zh'&&!text&&node.text)throw new Error('本条尚无中文译文，请切换日文或返回编辑补充');
    for(const separator of this.config.text_breaks)text=text.split(separator).join('\n');
    if(!text)return null;
    if(/<[^>]+>/.test(text))throw new Error('台词包含尚未支持的原版富文本标记，请先在编辑器核对');
    const group=!node.speaker?this.config.panels.narration:node.character_image?this.config.panels.picture:this.config.panels.dialogue;
    const speaker=this.speakerName(node,language);
    const rows=textPanelRows(node,group,this.assets.groups[group],this.textPanelPresentation);
    const panel={group,rows,speaker,text,layouts:new Map()};
    for(const row of panel.rows)if(row.type==='text'){
      const value=row.path.endsWith('/'+this.config.dialogue_name)?speaker:text;
      const font=this.fonts.get(row.font),layout=font.layout(value,row);
      panel.layouts.set(row.path,layout);
      // Native-font rasterization is synchronous. Warm every visible glyph
      // during node preparation, without replacing or drawing the current
      // panel, so first-use canvas work cannot stall the hit/quake frame.
      for(const line of layout.lines)for(const item of line)font.bitmap(item.char,layout.size,row.color);
    }
    reportTextPanelLayout({node,language,panel,nativeRows:this.assets.groups[group],
      textRowName:this.config.dialogue_text,settings:this.textPanelPresentation},this.textPanelLayoutReports);
    return panel;
  }
  text(node,language,visible=Infinity){
    this.panel=this.prepareText(node,language);
    if(!this.panel){this.clear();return 0;}
    this.panel.visible=visible;
    this.draw(visible);return Array.from(this.panel.text).length;
  }
  draw(visible){
    this.context.clearRect(0,0,this.canvas.width,this.canvas.height);if(!this.panel)return;
    const context=this.context;
    for(const row of this.panel.rows){
      if(row.path.includes(this.config.full_voice))continue;
      if(row.path.includes(this.config.page_arrow)&&visible<Array.from(this.panel.text).length)continue;
      if(row.type==='image')this.sprite(row);
      else this.fonts.get(row.font).draw(context,row,this.panel.layouts.get(row.path),row.path.endsWith('/'+this.config.dialogue_name)?Infinity:visible);
    }
  }
  sprite(row,context=this.context){
    let image=this.images.get(row.sprite.file);const r=row.rect,c=context;
    // Unity UI Image multiplies vertex RGB as well as alpha. The purple
    // selection track and balloon therefore cannot use the bare white sprite.
    if(row.color.slice(0,3).some(v=>v!==1)){
      const key=row.sprite.file+':'+row.color.slice(0,3).join(',');
      if(!this.tints.has(key)){
        const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
        const tint=canvas.getContext('2d');tint.drawImage(image,0,0);
        tint.globalCompositeOperation='multiply';tint.fillStyle=`rgb(${row.color.slice(0,3).map(v=>Math.round(v*255)).join(',')})`;tint.fillRect(0,0,canvas.width,canvas.height);
        tint.globalCompositeOperation='destination-in';tint.drawImage(image,0,0);this.tints.set(key,canvas);
      }
      image=this.tints.get(key);
    }
    const w=Math.abs(r.width*r.scale_x),h=Math.abs(r.height*r.scale_y);
    c.save();c.translate(r.x,r.y);c.scale(Math.sign(r.scale_x),Math.sign(r.scale_y));
    c.globalAlpha=row.color[3];
    if(row.mode===1){
      const [left,bottom,right,top]=row.sprite.border;
      const sx=[0,left,image.width-right,image.width],sy=[0,top,image.height-bottom,image.height];
      const dx=[0,left,w-right,w],dy=[0,top,h-bottom,h];
      for(let y=0;y<3;y++)for(let x=0;x<3;x++){
        const sw=sx[x+1]-sx[x],sh=sy[y+1]-sy[y];
        if(sw>0&&sh>0)c.drawImage(image,sx[x],sy[y],sw,sh,dx[x],dy[y],dx[x+1]-dx[x],dy[y+1]-dy[y]);
      }
    }else c.drawImage(image,0,0,w,h);
    c.restore();
  }
}
