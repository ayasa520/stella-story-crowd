(spec) => {
  // Read-only per-document instrumentation. The owner creates a fresh Page
  // for every case; this guard additionally rejects stacked init hooks. The
  // actual controller, clock, camera, model transforms and parameters are
  // observed only. Neither this hook nor its caller supplies animation values.
  if (!location.pathname.endsWith('/player/player.html')) return;
  if (window.__assembledReview) throw Error('Duplicate assembled hook in one document');
  const qa = window.__assembledReview = {
    id: spec.id, documentId: spec.id + ':' + performance.timeOrigin,
    instances: [], applied: [], renders: [], timing: [], lifecycle: [], errors: [], observerSkips: [],
    coreUpdates: 0, renderCount: 0, installed: false, clock: null, hud: null,
    traceOverflow: false, staticCapture: null, staticCaptureRequested: false, fixtureReady: false,
  };
  const fail = error => { if (qa.errors.length < 30) qa.errors.push(String(error)); };
  const clock = () => qa.clock?.snapshot() || null;
  const node = () => document.body?.dataset.node || '';
  const matrix = value => value ? {a:value.a,b:value.b,c:value.c,d:value.d,tx:value.tx,ty:value.ty} : null;
  const rect = value => ({left:value.left,top:value.top,right:value.right,bottom:value.bottom,width:value.width,height:value.height});
  const base64 = bytes => {
    let result = '';
    for (let offset = 0; offset < bytes.length; offset += 8192)
      result += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
    return btoa(result);
  };
  const observe = (model, document) => {
    const row = {instance:qa.instances.length+1,model,sourceURL:document?.url || '',destroyed:false,lastApplied:null};
    qa.instances.push(row);
    qa.lifecycle.push({event:'created',instance:row.instance,sourceURL:row.sourceURL,wall:performance.now(),clock:clock(),fixtureReady:qa.fixtureReady});
    model.once('destroy', () => {
      row.destroyed = true;
      qa.lifecycle.push({event:'destroyed',instance:row.instance,wall:performance.now(),clock:clock()});
    });
    const core = model.internalModel?.coreModel;
    if (!core?.getModel || typeof core.update !== 'function') throw Error('Unknown actual Core interface');
    const original = core.update;
    core.update = function (...args) {
      // A positively observed destroy event invalidates parameter reads from
      // that instance. Retain the callback identity separately, still invoke
      // the original method, and never mistake an old-instance read for the
      // new actor's applied values or suppress an original application error.
      if (row.destroyed) {
        if (qa.observerSkips.length<100) qa.observerSkips.push({instance:row.instance,reason:'callback_after_observed_destroy',wall:performance.now(),clock:clock()});
        return Reflect.apply(original,this,args);
      }
      let sample = null;
      if (qa.applied.length < spec.maxTraceFrames) {
        try {
          // PairingViewer.renderPose runs at beforeModelUpdate. Sampling just
          // before the real Core update retains the actual applied values,
          // before a later Cubism loadParameters/reset can hide them.
          const native = this.getModel();
          sample = {sequence:++qa.coreUpdates,instance:row.instance,sourceURL:row.sourceURL,
            wall:performance.now(),clock:clock(),node:node(),phase:documentBodyPhase(),fixtureReady:qa.fixtureReady,
            parameterIds:Array.from(native.parameters.ids),values:Array.from(native.parameters.values),
            partIds:Array.from(native.parts.ids),partOpacities:Array.from(native.parts.opacities),
            modelAlpha:model.alpha,capturePoint:'immediately_before_real_coreModel.update'};
        } catch (error) { fail(error); }
      } else qa.traceOverflow = true;
      const result = Reflect.apply(original, this, args);
      if (sample) { row.lastApplied = sample; qa.applied.push(sample); }
      return result;
    };
  };
  const documentBodyPhase = () => document.body?.dataset.phase || '';
  const afterRender = renderer => {
    if (renderer.view !== document.querySelector('#actor')) return;
    // The original root template is100% x930. Root approved a fixed480x856
    // iframe QA preset, applied before target advance. Do not freeze a layout
    // guard during the predecessor's initial template geometry or hide that
    // explicit fixture change by calling it the unmodified template default.
    if (!qa.fixtureReady) return;
    if (qa.renders.length >= spec.maxTraceFrames) { qa.traceOverflow = true; return; }
    const viewport = document.querySelector('#viewport'), card = document.querySelector('#cardMotion');
    if (!viewport || !card) return;
    const box = viewport.getBoundingClientRect(), style = getComputedStyle(card), now = clock();
    const active = qa.instances.filter(row => !row.destroyed && row.model.parent && row.model.visible);
    const models = active.map(row => {
      const model = row.model, native = model.internalModel.coreModel.getModel();
      return {instance:row.instance,sourceURL:row.sourceURL,lastApplied:row.lastApplied?.sequence || null,
        appliedGameFrame:row.lastApplied?.clock?.frame ?? null,sameGameFrame:row.lastApplied?.clock?.frame === now?.frame,
        position:{x:model.position.x,y:model.position.y},scale:{x:model.scale.x,y:model.scale.y},rotation:model.rotation,
        anchor:{x:model.anchor.x,y:model.anchor.y},modelAlpha:model.alpha,
        worldTransform:matrix(model.worldTransform),localTransform:matrix(model.internalModel.localTransform),
        canvas:{width:native.canvasinfo.CanvasWidth,height:native.canvasinfo.CanvasHeight,ppu:native.canvasinfo.PixelsPerUnit}};
    });
    const record = {render:++qa.renderCount,wall:performance.now(),node:node(),phase:documentBodyPhase(),clock:now,
      cardOpacity:Number(style.opacity),cardTranslate:style.translate,actorHidden:document.querySelector('#actor').hidden,
      viewport:rect(box),models,
      actorCanvas:{intrinsicWidth:renderer.view.width,intrinsicHeight:renderer.view.height,
        cssRect:rect(renderer.view.getBoundingClientRect())},
      renderer:{screen:renderer.screen?{width:renderer.screen.width,height:renderer.screen.height}:null,
        resolution:typeof renderer.resolution==='number'?renderer.resolution:null}};
    record.hudKey = `r${record.render} f${now?.frame ?? '?'} i${models.map(row=>row.instance).join(',') || '-'} u${models.map(row=>row.lastApplied).join(',') || '-'} a${record.cardOpacity.toFixed(6)}`;
    qa.renders.push(record);

    // A diagnostic may occupy only a verified empty parent margin. Measuring
    // both iframe and local viewport prevents an iframe-local left=0 from
    // being mistaken for parent space. No body/iframe/game layout is assigned.
    const frame = window.frameElement, parent = window.parent;
    if (!frame || parent === window) { fail('Same-origin production iframe required'); return; }
    const frameBox = frame.getBoundingClientRect();
    const game = {left:frameBox.left+frame.clientLeft+box.left,top:frameBox.top+frame.clientTop+box.top,
      right:frameBox.left+frame.clientLeft+box.right,bottom:frameBox.top+frame.clientTop+box.bottom};
    record.parentLayout = {frame:rect(frameBox),game,parent:{width:parent.innerWidth,height:parent.innerHeight}};
    qa.layoutGuard ??= {frameWidth:frameBox.width,frameHeight:frameBox.height,width:box.width,height:box.height};
    if (Math.abs(frameBox.width-480)>.1 || Math.abs(frameBox.height-856)>.1 ||
        Math.abs(box.width/box.height-9/16)>.001) {
      fail('Outer480x856 fixture or original9:16 stage aspect mismatch'); return;
    }
    const fixed = qa.layoutGuard;
    if (Math.abs(frameBox.width-fixed.frameWidth)>.1 || Math.abs(frameBox.height-fixed.frameHeight)>.1 ||
        Math.abs(box.width-fixed.width)>.1 || Math.abs(box.height-fixed.height)>.1) {
      fail('Iframe or production viewport geometry changed'); return;
    }
    const left = Math.max(frameBox.right,game.right)+8;
    if (!qa.hud) {
      if (parent.innerWidth-left<293 || parent.innerHeight<1000) { fail('No empty parent side margin outside iframe'); return; }
      // Reject existing parent content in the reserved rectangle instead of
      // treating an empty-looking region as safe based on a screenshot guess.
      for (const element of parent.document.querySelectorAll('body *')) {
        // A full-width HEADER is a layout container; its real child buttons,
        // state text and any direct text are checked independently. Its box
        // alone must not turn empty right-side space into a false collision.
        if (element.tagName==='HEADER' && !Array.from(element.childNodes).some(item=>item.nodeType===3&&item.textContent.trim())) continue;
        const occupied = element.getBoundingClientRect();
        if (occupied.width>0 && occupied.height>0 && occupied.left<left+293 && occupied.right>left && occupied.top<95 && occupied.bottom>8) {
          fail('Parent diagnostic margin contains existing content'); return;
        }
      }
      qa.hud = parent.document.createElement('pre'); qa.hud.dataset.assembledHud = spec.id;
      Object.assign(qa.hud.style,{position:'fixed',left:left+'px',top:'8px',width:'285px',margin:'0',padding:'4px',
        font:'12px monospace',color:'#fff',background:'#111',zIndex:'100000',pointerEvents:'none'});
      parent.document.body.append(qa.hud);
    }
    const hudBox = qa.hud.getBoundingClientRect(); record.parentLayout.hud = rect(hudBox);
    if (hudBox.left<game.right && hudBox.right>game.left && hudBox.top<game.bottom && hudBox.bottom>game.top) {
      fail('Parent HUD overlaps game pixels'); return;
    }
    qa.hud.textContent = `${spec.id}\n${record.node}\n${record.hudKey}\ng${now?.gameSeconds?.toFixed(6) ?? '?'} w${record.wall.toFixed(3)}`;
    if (qa.staticCaptureRequested && !qa.staticCapture && record.node === spec.targetNode && record.phase === 'ready' &&
        record.cardOpacity === 1 && models.length === 1 && models[0].sourceURL.includes('/ac_'+spec.model+'/')) {
      const canvas = renderer.view;
      const staticRecord = {render:record.render,hudKey:record.hudKey,instance:models[0].instance,
        lastApplied:models[0].lastApplied,gameFrame:now?.frame,width:canvas.width,height:canvas.height,
        actorPng:canvas.toDataURL('image/png'),capturePoint:'after_actual_renderer_render_without_redraw'};
      if (spec.rgbaStaticReference) {
        const gl = renderer.gl;
        if (!gl || gl.getParameter(gl.FRAMEBUFFER_BINDING) !== null) throw Error('RGBA reference requires actual default framebuffer');
        const rgba = new Uint8Array(canvas.width*canvas.height*4);
        gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
        staticRecord.rawRgbaBase64 = base64(rgba);
        staticRecord.rawRgbaConvention = 'original WebGL RGBA8 bottom-up framebuffer bytes; no unpremultiply, recolor, fitting or re-render';
      }
      qa.staticCapture = staticRecord;
    }
  };
  const install = () => {
    if (qa.installed || !window.PIXI?.live2d?.Live2DModel || !window.PIXI.Renderer) return;
    try {
      const factory = PIXI.live2d.Live2DModel, originalFrom = factory.from;
      factory.from = async function (...args) {
        const model = await Reflect.apply(originalFrom,this,args);
        try { observe(model,args[0]); } catch (error) { fail(error); }
        return model;
      };
      const originalRender = PIXI.Renderer.prototype.render;
      PIXI.Renderer.prototype.render = function (...args) {
        const result = Reflect.apply(originalRender,this,args);
        try { afterRender(this); } catch (error) { fail(error); }
        return result;
      };
      qa.installed = true;
      import('/studio/visual_frame_clock.js').then(module => qa.clock = module.visualFrameClock).catch(fail);
    } catch (error) { fail(error); }
  };
  document.addEventListener('readystatechange',install);
  document.addEventListener('DOMContentLoaded',install); install();
  document.addEventListener('stella-player-timing',event => {
    if (qa.timing.length<1000) qa.timing.push({...event.detail,wall:performance.now(),clock:clock()});
    else qa.traceOverflow = true;
  });
}
