(spec) => {
  // Observe the actual production document. A fresh Page owns one installation;
  // no writer supplies pose values, transforms, timing or a replacement render.
  if (!location.pathname.endsWith('/player/player.html')) return;
  if (window.__staticReference) throw Error('Duplicate static-reference hook');
  const qa=window.__staticReference={id:spec.id,instances:[],lifecycle:[],timing:[],errors:[],
    installed:false,clock:null,fixtureReady:false,renderCount:0,updateCount:0,
    lastRender:null,request:null,captures:[],actorReadbacks:0,hud:null,originalFailures:[]};
  const fail=error=>{try{if(qa.errors.length<30)qa.errors.push(String(error));}catch{}};
  const originalFailure=(method,error)=>{try{qa.originalFailures.push({method,error:String(error)});}catch{}};
  const clock=()=>qa.clock?.snapshot()||null;
  const rect=element=>{const b=element.getBoundingClientRect();return {left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height};};
  const matrix=m=>m?{a:m.a,b:m.b,c:m.c,d:m.d,tx:m.tx,ty:m.ty}:null;
  const base64=bytes=>{let result='';for(let i=0;i<bytes.length;i+=8192)result+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(result);};
  const observe=(model,document)=>{
    const row={instance:qa.instances.length+1,model,sourceURL:document?.url||'',destroyed:false,lastApplied:null};
    qa.instances.push(row);
    qa.lifecycle.push({event:'created',instance:row.instance,sourceURL:row.sourceURL,clock:clock(),fixtureReady:qa.fixtureReady});
    model.once('destroy',()=>{row.destroyed=true;qa.lifecycle.push({event:'destroyed',instance:row.instance,clock:clock()});});
    const core=model.internalModel?.coreModel;
    if(!core?.getModel||typeof core.update!=='function')throw Error('Unrecognized actual Core interface');
    const original=core.update;
    core.update=function(...args){
      // The shipped SDK calls beforeModelUpdate -> Core.update -> loadParameters.
      // PairingViewer applies its pose at beforeModelUpdate, so this read records
      // the actual writer result before Core consumes it or loadParameters resets
      // it. Keep only the latest sample per instance, rather than a long trace.
      let sample=null;
      if(!row.destroyed){
        try{
          const native=this.getModel();
          sample={sequence:++qa.updateCount,instance:row.instance,sourceURL:row.sourceURL,
            node:documentBodyNode(),clock:clock(),wall:performance.now(),
            parameterIds:Array.from(native.parameters.ids),values:Array.from(native.parameters.values),
            partIds:Array.from(native.parts.ids),partOpacities:Array.from(native.parts.opacities),
            capturePoint:'immediately_before_actual_core_update'};
        }catch(error){fail(error);}
      }
      let result;
      try{result=Reflect.apply(original,this,args);}
      catch(error){originalFailure('core.update',error);throw error;}
      try{if(sample)row.lastApplied=sample;}catch(error){fail(error);}
      return result;
    };
  };
  const documentBodyNode=()=>document.body?.dataset.node||'';
  const geometry=renderer=>{
    const frame=window.frameElement, viewport=document.querySelector('#viewport'),actor=document.querySelector('#actor');
    if(!frame||!viewport||!actor)throw Error('Missing same-origin game fixture');
    return {frameRect:rect(frame),frameClientBorder:{left:frame.clientLeft,top:frame.clientTop},viewportRect:rect(viewport),actorCanvas:{width:actor.width,height:actor.height,cssRect:rect(actor)},
      renderer:{screen:renderer.screen?{width:renderer.screen.width,height:renderer.screen.height}:null,
        resolution:typeof renderer.resolution==='number'?renderer.resolution:null},
      parentViewport:{width:window.parent.innerWidth,height:window.parent.innerHeight}};
  };
  const writeHud=record=>{
    const parent=window.parent, frame=record.geometry.frameRect, stage=record.geometry.viewportRect;
    const border=record.geometry.frameClientBorder;
    const game={left:frame.left+border.left+stage.left,top:frame.top+border.top+stage.top,
      right:frame.left+border.left+stage.right,bottom:frame.top+border.top+stage.bottom};
    const left=Math.max(frame.right,game.right)+8;
    if(!qa.hud){
      if(parent.innerWidth-left<380)throw Error('No verified parent side margin');
      // Only the parent margin is assigned. Reject occupied child content while
      // ignoring a header container whose actual children are checked separately.
      for(const element of parent.document.querySelectorAll('body *')){
        if(element.tagName==='HEADER'&&!Array.from(element.childNodes).some(n=>n.nodeType===3&&n.textContent.trim()))continue;
        const b=element.getBoundingClientRect();
        if(b.width&&b.height&&b.left<left+370&&b.right>left&&b.top<110&&b.bottom>8)throw Error('HUD margin is occupied');
      }
      qa.hud=parent.document.createElement('pre');qa.hud.dataset.staticReferenceHud=spec.id;
      Object.assign(qa.hud.style,{position:'fixed',left:left+'px',top:'8px',width:'360px',margin:'0',padding:'4px',
        font:'14px monospace',background:'#111',color:'#fff',zIndex:'100000',pointerEvents:'none'});
      parent.document.body.append(qa.hud);
    }
    record.hudKey=`r${record.render} f${record.clock?.frame??'?'} i${record.models.map(m=>m.instance).join(',')||'-'} u${record.models.map(m=>m.lastApplied).join(',')||'-'}`;
    // Update on EVERY actual render, including after the one actor readback.
    // A frozen capture token would falsely label later compositor images.
    qa.hud.textContent=`${spec.id}\n${record.node}\n${record.hudKey}\ng${record.clock?.gameSeconds?.toFixed(6)??'?'}`;
    record.hudRect=rect(qa.hud);
    const h=record.hudRect;
    if(h.left<game.right&&h.right>game.left&&h.top<game.bottom&&h.bottom>game.top)throw Error('HUD overlaps game pixels');
  };
  const afterRender=renderer=>{
    if(renderer.view!==document.querySelector('#actor')||!qa.fixtureReady)return;
    const now=clock(),card=document.querySelector('#cardMotion'),geometryNow=geometry(renderer);
    const f=geometryNow.frameRect,v=geometryNow.viewportRect;
    if(Math.abs(f.width-480)>.1||Math.abs(f.height-856)>.1||Math.abs(v.width/v.height-9/16)>.001)throw Error('Fixture/aspect changed');
    const active=qa.instances.filter(r=>!r.destroyed&&r.model.parent&&r.model.visible);
    const models=active.map(row=>({instance:row.instance,sourceURL:row.sourceURL,lastApplied:row.lastApplied?.sequence||null,
      appliedGameFrame:row.lastApplied?.clock?.frame??null,sameGameFrame:row.lastApplied?.clock?.frame===now?.frame,
      position:{x:row.model.position.x,y:row.model.position.y},scale:{x:row.model.scale.x,y:row.model.scale.y},
      rotation:row.model.rotation,alpha:row.model.alpha,worldTransform:matrix(row.model.worldTransform),
      internalTransform:matrix(row.model.internalModel?.localTransform)}));
    const record={render:++qa.renderCount,node:documentBodyNode(),phase:document.body?.dataset.phase,
      wall:performance.now(),clock:now,cardOpacity:Number(getComputedStyle(card).opacity),models,geometry:geometryNow,
      backgrounds:Array.from(document.querySelectorAll('#card>img,#backdrop>img')).map(image=>({src:image.currentSrc||image.src,
        hidden:image.hidden,naturalWidth:image.naturalWidth,naturalHeight:image.naturalHeight,rect:rect(image),
        container:image.parentElement.id,backgroundGeometry:image.parentElement.dataset.backgroundGeometry||null}))};
    writeHud(record);qa.lastRender=record;
    if(!qa.request||qa.request.node!==record.node||record.phase!=='ready'||record.cardOpacity!==1)return;
    const capture={...record,capturePoint:'after_actual_actor_renderer_render_no_redraw',beforeClock:clock(),
      wholeStageSameFrameAccepted:false,wholeStageMatchingRule:'Offline exact rolling HUD render/frame/instance/applied match only'};
    if(spec.kind==='character'){
      if(models.length!==1||!models[0].sourceURL.includes('/ac_'+spec.model+'/'))throw Error('Static target instance/model mismatch');
      if(!models[0].sameGameFrame)throw Error('Core sample is not from this rendered game frame');
      if(qa.actorReadbacks!==0)throw Error('A second actor readback is forbidden');
      const row=active[0],canvas=renderer.view,gl=renderer.gl;
      if(!gl||gl.getParameter(gl.FRAMEBUFFER_BINDING)!==null)throw Error('Actual default framebuffer required');
      const rgba=new Uint8Array(canvas.width*canvas.height*4);
      gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
      capture.actorPng=canvas.toDataURL('image/png');capture.rawRgbaBase64=base64(rgba);
      capture.width=canvas.width;capture.height=canvas.height;capture.lastApplied=row.lastApplied;
      capture.rawRgbaConvention='Actual WebGL RGBA8 bottom-up, no recolor/unpremultiply/fit; PNG equality checked offline';
      qa.actorReadbacks++;
    }
    capture.afterClock=clock();
    if(capture.beforeClock?.frame!==capture.afterClock?.frame)throw Error('Game frame changed inside synchronous readback');
    qa.captures.push(capture);qa.request=null;
  };
  const install=()=>{
    if(qa.installed||!window.PIXI?.live2d?.Live2DModel||!window.PIXI.Renderer)return;
    try{
      const factory=PIXI.live2d.Live2DModel,from=factory.from;
      factory.from=function(...args){
        // Return the ORIGINAL promise/result, preserving identity and exception
        // behavior. The detached observation branch never becomes the caller's
        // promise, and diagnostic failures cannot reject production loading.
        let result;
        try{result=Reflect.apply(from,this,args);}
        catch(error){originalFailure('Live2DModel.from',error);throw error;}
        try{
          if(result&&typeof result.then==='function')result.then(model=>{try{observe(model,args[0]);}catch(error){fail(error);}},error=>originalFailure('Live2DModel.from.reject',error));
          else observe(result,args[0]);
        }catch(error){fail(error);}
        return result;
      };
      const render=PIXI.Renderer.prototype.render;
      PIXI.Renderer.prototype.render=function(...args){
        let result;
        try{result=Reflect.apply(render,this,args);}
        catch(error){originalFailure('Renderer.render',error);throw error;}
        try{afterRender(this);}catch(error){fail(error);}
        return result;
      };
      qa.installed=true;import('/studio/visual_frame_clock.js').then(m=>qa.clock=m.visualFrameClock).catch(fail);
    }catch(error){fail(error);}
  };
  document.addEventListener('readystatechange',install);document.addEventListener('DOMContentLoaded',install);install();
  document.addEventListener('stella-player-timing',event=>{if(qa.timing.length<150)qa.timing.push({...event.detail,clock:clock()});else fail('Timing cap reached');});
}
