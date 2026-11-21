// Passive pixel/style readiness for screenshots. Reads the already rendered
// 2D canvases; it never paints, changes visibility, holds entry or owns time.
export function installCaptureReadiness(){
  function rect(e){if(!e)return null;const{x,y,width,height}=e.getBoundingClientRect();return{x,y,width,height};}
  function alpha(e){return e?Number(getComputedStyle(e).opacity):0;}
  function effectiveAlpha(e){
    let result=1;
    for(let n=e;n instanceof Element;n=n.parentElement){
      const s=getComputedStyle(n);if(s.display==='none'||s.visibility==='hidden')return 0;
      result*=Number(s.opacity);
    }
    return result;
  }
  function inside(e){
    const r=rect(e),v=rect(document.getElementById('viewport'));
    return !!(r&&v&&r.width>0&&r.height>0&&Math.min(r.x+r.width,v.x+v.width)>Math.max(r.x,v.x)&&Math.min(r.y+r.height,v.y+v.height)>Math.max(r.y,v.y));
  }
  function ink(canvas,logicalRect,referenceWidth){
    const scale=canvas.width/referenceWidth,pad=2;
    const x=Math.max(0,Math.floor(logicalRect.x*scale)-pad),y=Math.max(0,Math.floor(logicalRect.y*scale)-pad);
    const right=Math.min(canvas.width,Math.ceil((logicalRect.x+logicalRect.width)*scale)+pad);
    const bottom=Math.min(canvas.height,Math.ceil((logicalRect.y+logicalRect.height)*scale)+pad);
    if(right<=x||bottom<=y)return {nontransparent:0,bright:0,invalidRect:true};
    const data=canvas.getContext('2d').getImageData(x,y,right-x,bottom-y).data;
    let nontransparent=0,bright=0,minX=right-x,minY=bottom-y,maxX=-1,maxY=-1;
    for(let i=0;i<data.length;i+=4){
      if(data[i+3]>0)nontransparent++;
      if(data[i+3]>16&&Math.max(data[i],data[i+1],data[i+2])>=128){
        bright++;const pixel=i/4,px=pixel%(right-x),py=Math.floor(pixel/(right-x));
        minX=Math.min(minX,px);minY=Math.min(minY,py);maxX=Math.max(maxX,px);maxY=Math.max(maxY,py);
      }
    }
    return {roi:{x,y,width:right-x,height:bottom-y},nontransparent,bright,
      brightBounds:bright?{x:x+minX,y:y+minY,width:maxX-minX+1,height:maxY-minY+1}:null};
  }
  function rows(name){return window.reviewEndingObserver.data().rows.filter(r=>r.state.caseName===name&&r.kind==='product-console');}
  function latest(all,name,node){return all.filter(r=>r.value.name===name&&r.value.detail?.node===node).at(-1);}
  window.reviewCaptureReadiness={
    title({node,caseName,referenceWidth,stableStart,stableEnd}){
      const state=window.reviewEndingObserver.snapshot(),all=rows(caseName);
      const start=all.filter(r=>r.value.name==='STORY_NATIVE_TITLE_ENTRY'&&r.value.detail?.node===node&&r.value.detail.stage==='started').at(-1);
      const layout=latest(all,'STORY_NATIVE_TITLE_LAYOUT',node),decision=latest(all,'STORY_NATIVE_INTERVAL_DECISION',node);
      if(state.node!==node||state.phase!=='title'||!start||!layout||!decision)return {ready:false,reason:'title-entry-not-current'};
      const elapsed=state.normalClock.gameSeconds-start.value.detail.clock.gameSeconds;
      const root=document.querySelector('#storyFlow .native-title-content'),canvases=root?.querySelectorAll('canvas.native-title-text');
      if(!root||canvases.length!==2||elapsed<stableStart||elapsed>=stableEnd)return {ready:false,reason:'outside-stable-native-segment',elapsed,state};
      if(state.generation?.value!==decision.value.detail.generation)return {ready:false,reason:'generation-mismatch'};
      const layers={};
      for(const[index,name]of ['subtitle','title'].entries()){
        const canvas=canvases[index],logicalRect=layout.value.detail.rectangles[name];
        const pixels=ink(canvas,logicalRect,referenceWidth);
        const box=rect(canvas),v=rect(document.getElementById('viewport')),b=pixels.brightBounds;
        const inkRect=b?{x:box.x+b.x*box.width/canvas.width,y:box.y+b.y*box.height/canvas.height,
          width:b.width*box.width/canvas.width,height:b.height*box.height/canvas.height}:null;
        const inkInView=!!(inkRect&&inkRect.width>0&&inkRect.height>0&&Math.min(inkRect.x+inkRect.width,v.x+v.width)>Math.max(inkRect.x,v.x)&&
          Math.min(inkRect.y+inkRect.height,v.y+v.height)>Math.max(inkRect.y,v.y));
        layers[name]={attached:canvas.isConnected,rect:box,inView:inside(canvas),cssAlpha:alpha(canvas),effectiveAlpha:effectiveAlpha(canvas),inkRect,inkInView,
          canvasPixels:[canvas.width,canvas.height],logicalRect,pixels};
      }
      const ready=alpha(root)>=.99&&inside(root)&&Object.values(layers).every(l=>l.attached&&l.inView&&l.inkInView&&l.cssAlpha>=.99&&l.effectiveAlpha>=.99&&l.pixels.nontransparent>0&&l.pixels.bright>0);
      return {ready,node,generation:decision.value.detail.generation,elapsed,rootAlpha:alpha(root),layers,
        startSequence:start.sequence,layoutSequence:layout.sequence,normalClock:state.normalClock,
        observedEpochMilliseconds:state.observedEpochMilliseconds,stableSegment:[stableStart,stableEnd]};
    },
    dialogue({node,caseName,group,hasEntryProfile,referenceWidth,expectedText}){
      const state=window.reviewEndingObserver.snapshot(),all=rows(caseName),canvas=document.getElementById('subtitles');
      if(state.node!==node||state.phase!=='ready')return {ready:false,reason:'dialogue-not-ready'};
      const owner=latest(all,'STORY_PANEL_IN_START',node);
      let complete=null;
      if(hasEntryProfile){
        if(!owner||owner.value.detail.group!==group)return {ready:false,reason:'owned-panel-start-not-observed'};
        const token=owner.value.detail.token;
        if(all.some(r=>r.value.name==='STORY_PANEL_IN_CANCELLED'&&r.value.detail?.group===group&&r.value.detail.token===token))return {ready:false,reason:'owned-panel-cancelled'};
        complete=all.find(r=>r.value.name==='STORY_PANEL_IN_COMPLETE'&&r.value.detail?.node===node&&r.value.detail.group===group&&r.value.detail.token===token);
        if(!complete)return {ready:false,reason:'owned-panel-incomplete'};
      }else if(owner)return {ready:false,reason:'unexpected-entry-token-for-unprofiled-group'};
      const layout=latest(all,'STORY_TEXT_PANEL_LAYOUT',node);
      if(!layout||layout.value.detail.group!==group)return {ready:false,reason:'text-layout-not-observed'};
      const pixels=ink(canvas,layout.value.detail.rect,referenceWidth),text=document.getElementById('accessibleText').textContent;
      const ready=!canvas.hidden&&inside(canvas)&&alpha(canvas)>=.99&&effectiveAlpha(canvas)>=.99&&getComputedStyle(canvas).translate==='none'&&
        pixels.nontransparent>0&&(!expectedText||text.includes(expectedText));
      return {ready,node,group,hasEntryProfile,owner:owner?.value.detail||null,complete:complete?.value.detail||null,
        completeSequence:complete?.sequence??null,layout:layout.value.detail,canvasRect:rect(canvas),cssAlpha:alpha(canvas),effectiveAlpha:effectiveAlpha(canvas),
        pixels,text,normalClock:state.normalClock,observedEpochMilliseconds:state.observedEpochMilliseconds};
    },
  };
  const history=[];
  for(const name of ['title','dialogue']){
    const read=window.reviewCaptureReadiness[name];
    window.reviewCaptureReadiness[name]=function(args){
      const result=read(args);history.push({method:name,...result});if(history.length>64)history.shift();return result;
    };
  }
  window.reviewCaptureReadiness.diagnostics=()=>history;
}
