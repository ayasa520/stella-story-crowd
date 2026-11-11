(spec) => {
  'use strict';
  // UNEXECUTED DIAGNOSTIC DRAFT. This function is installed before navigation
  // only by the appointed browser owner. It never evaluates a second pose,
  // advances a clock, changes a transform, or requests an additional render.
  if (!location.pathname.endsWith('/player/player.html')) return;
  if (window.__drawDiagnostic || window.__assembledReview) throw Error('Stacked diagnostic hooks');
  const targets = new Set(spec.targetNodes);
  if (!targets.size || targets.size > 2 || ![...targets].every(value => /^\d+:\d+$/.test(value)) ||
      !Number.isInteger(spec.maxRenderFramesPerNode) || spec.maxRenderFramesPerNode > 240 ||
      spec.maxRenderFramesPerNode < 8 || !Number.isInteger(spec.traceByteBudget) ||
      spec.traceByteBudget > 24 * 1024 * 1024 || spec.traceByteBudget < 1024 * 1024 ||
      !Number.isInteger(spec.maxDurationMs) || spec.maxDurationMs > 60000 || spec.maxDurationMs < 1000)
    throw Error('Invalid bounded diagnostic specification');

  const encoder = new TextEncoder(), objects = new WeakMap(), rows = [], restores = [];
  const records = [], errors = [], cleanupConflicts = [], renderStack = [];
  const milestones = new Map();
  let nextObject = 0, nextRecord = 0, renderSequence = 0, loadSequence = 0;
  let bytes = 0, enabled = true, armed = false, installed = false, clockObject = null;
  let status = 'installed_unarmed_not_acceptance', timer = null, cleaned = false;
  const id = object => {
    if (!object || !['object', 'function'].includes(typeof object)) return null;
    if (!objects.has(object)) objects.set(object, ++nextObject);
    return objects.get(object);
  };
  const node = () => document.body?.dataset.node || '';
  const phase = () => document.body?.dataset.phase || '';
  const finite = value => {
    if (typeof value !== 'number' || !Number.isFinite(value)) throw Error('Nonfinite or missing numeric field');
    return value;
  };
  const array = (value, maximum = 80000) => {
    if (!value || !Number.isInteger(value.length) || value.length > maximum) throw Error('Missing or oversized array');
    return Array.from(value, finite);
  };
  const strings = (value, maximum = 512) => {
    if (!value || value.length > maximum) throw Error('Missing or oversized ID schema');
    return Array.from(value, item => {
      if (typeof item !== 'string' || item.length > 256) throw Error('Invalid actual ID');
      return item;
    });
  };
  const affine = value => value ? Object.fromEntries(['a', 'b', 'c', 'd', 'tx', 'ty'].map(key => [key, finite(value[key])])) : null;
  const matrix4 = value => {
    if (!value?.getArray) return null;
    const result = array(value.getArray(), 16);
    if (result.length !== 16) throw Error('Unexpected actual MVP/mask matrix length');
    return result;
  };
  const requiredMatrix4 = value => {
    const result = matrix4(value);
    if (!result) throw Error('Required actual renderer matrix is unavailable');
    return result;
  };
  const point = value => value ? {x: finite(value.x), y: finite(value.y)} : null;
  const rectangle = value => value ? Object.fromEntries(['x', 'y', 'width', 'height'].map(key => [key, finite(value[key])])) : null;
  const clock = () => clockObject?.snapshot() || null;
  const context = () => ({node: node(), phase: phase(), wallMs: performance.now(), clock: clock()});

  function cleanup() {
    if (cleaned) return;
    cleaned = true;
    clearTimeout(timer);
    document.removeEventListener('readystatechange', install);
    document.removeEventListener('DOMContentLoaded', install);
    document.removeEventListener('stella-player-timing', onTiming);
    window.removeEventListener('pagehide', onPageHide);
    for (const restore of restores.reverse()) {
      try { restore(); } catch (error) { cleanupConflicts.push(String(error).slice(0, 512)); }
    }
  }
  function stop(reason, failed = false) {
    if (!enabled) return;
    enabled = false; armed = false;
    status = failed ? 'failed_partial_not_acceptance' : 'stopped_capture_not_acceptance';
    if (failed && errors.length < 16) errors.push(String(reason).slice(0, 512));
    // Restore after the current original invocation has unwound. No original
    // SDK object is destroyed or reset as a side effect of logger cleanup.
    queueMicrotask(cleanup);
  }
  const fail = error => stop(error, true);
  function append(kind, payload) {
    if (!enabled) return null;
    const sequence = ++nextRecord;
    const text = JSON.stringify({sequence, kind, ...payload});
    const cost = encoder.encode(text).byteLength + 1;
    if (records.length >= 6000 || bytes + cost > spec.traceByteBudget - 65536) {
      fail('Trace byte/record budget exceeded'); return null;
    }
    bytes += cost; records.push(text);
    return sequence;
  }
  function wrap(owner, name, decorate) {
    const hadOwn = Object.prototype.hasOwnProperty.call(owner, name);
    const descriptor = Object.getOwnPropertyDescriptor(owner, name), original = owner[name];
    if (typeof original !== 'function') throw Error('Unavailable actual method: ' + name);
    const wrapper = decorate(original);
    owner[name] = wrapper;
    if (owner[name] !== wrapper) throw Error('Method is not writable: ' + name);
    restores.push(() => {
      if (owner[name] !== wrapper) throw Error('Cleanup wrapper identity conflict: ' + name);
      if (hadOwn) Object.defineProperty(owner, name, descriptor);
      else delete owner[name];
    });
  }
  const activeFrame = () => renderStack.at(-1) || null;
  function textureRows(model, renderer) {
    return model.textures.map((texture, index) => {
      const base = texture.baseTexture, resource = base.resource;
      // These are observed resource properties. A missing URL stays null;
      // neither an actor token nor an atlas index invents a resource URL.
      const url = typeof resource?.url === 'string' ? resource.url :
        typeof resource?.source?.currentSrc === 'string' && resource.source.currentSrc ? resource.source.currentSrc : null;
      return {index, texture: id(texture), baseTexture: id(base), uid: base.uid, resource: id(resource),
        actualURL: url, width: base.width, height: base.height, valid: base.valid,
        boundGLTexture: id(renderer?._textures?.[index])};
    });
  }
  function parents(model) {
    const result = [];
    for (let object = model; object; object = object.parent) {
      if (result.length === 8) throw Error('Parent depth exceeds diagnostic bound');
      result.push({object: id(object), parent: id(object.parent), local: affine(object.localTransform),
        world: affine(object.worldTransform), visible: object.visible, alpha: object.alpha});
    }
    return result;
  }
  function chooseGeometry(frame) {
    let state = milestones.get(frame.node);
    if (!state) milestones.set(frame.node, state = {renders: 0, first: 0, readyStart: null, readySamples: []});
    if (++state.renders > spec.maxRenderFramesPerNode) throw Error('Target render-frame bound exceeded');
    if (state.first < 2) return 'first_target_render_' + (++state.first);
    if (frame.phase !== 'ready') return null;
    if (!frame.clock) throw Error('Shared clock is unavailable at target ready');
    state.readyStart ??= frame.clock.gameSeconds;
    const thresholds = [0, 0.25, 0.75, 1.25];
    const next = thresholds[state.readySamples.length];
    if (next !== undefined && frame.clock.gameSeconds - state.readyStart >= next) {
      state.readySamples.push({threshold: next, render: frame.render});
      return 'ready_observed_elapsed_' + next;
    }
    return null;
  }
  function observe(model, supplied, loadStart) {
    if (rows.length >= 12) throw Error('Model-load bound exceeded');
    const internal = model.internalModel, core = internal?.coreModel, renderer = internal?.renderer;
    if (!core?.getModel || !renderer?.getMvpMatrix || !renderer?.drawMesh) throw Error('Unrecognized actual Cubism interfaces');
    const native = core.getModel(), drawables = native.drawables;
    const sourceURL = typeof supplied?.url === 'string' ? supplied.url : null;
    const row = {model, internal, core, native, renderer, destroyed: false, lastUpdate: null,
      load: ++loadSequence, updateGeneration: 0, modelDraw: null,
      identity: {model: id(model), internal: id(internal), core: id(core), native: id(native),
        cubismRenderer: id(renderer)}, sourceURL};
    rows.push(row);
    const references = supplied?.FileReferences;
    append('load', {load: row.load, identity: row.identity, ...context(), loadStart,
      sourceURL, settingsURL: typeof internal.settings?.url === 'string' ? internal.settings.url : null,
      suppliedReferences: references ? {Moc: references.Moc ?? null, Textures: references.Textures ?? null} : null,
      textures: textureRows(model, renderer),
      resourceDigestStatus: 'owner_must_join_actual_response_SHA256_by_observed_URL',
      exactGPUMocOrTextureBytes: {value: null, status: 'not_exposed_by_this_logger'}});
    const schema = append('schema', {load: row.load, identity: row.identity,
      parameterIds: strings(native.parameters.ids), parameterDefaults: array(native.parameters.defaultValues, 512),
      partIds: strings(native.parts.ids), drawableIds: strings(drawables.ids),
      canvasInfo: {width: native.canvasinfo.CanvasWidth, height: native.canvasinfo.CanvasHeight,
        originX: native.canvasinfo.CanvasOriginX, originY: native.canvasinfo.CanvasOriginY,
        pixelsPerUnit: native.canvasinfo.PixelsPerUnit}});
    const destroyed = () => {
      row.destroyed = true;
      append('destroy', {load: row.load, identity: row.identity, ...context()});
    };
    model.on('destroy', destroyed);
    restores.push(() => model.off('destroy', destroyed));

    wrap(core, 'update', original => function (...args) {
      let sample = null;
      const generation = ++row.updateGeneration;
      // This wrapper is downstream of every beforeModelUpdate listener. Its
      // input is precisely what the real core.update will consume, independent
      // of later loadParameters restoration or listener registration order.
      if (enabled && armed && !row.destroyed && targets.has(node())) {
        try {
          if (this !== core || this.getModel() !== native) throw Error('Core/native instance changed');
          sample = {load: row.load, identity: row.identity, schema, generation,
            ...context(), render: activeFrame()?.render ?? null,
            parameters: array(native.parameters.values, 512), parts: array(native.parts.opacities, 512),
            inputStage: 'immediately_before_actual_Core_update', modelAlpha: model.alpha};
        } catch (error) { fail(error); }
      }
      // Exactly one original call; its return value and exception propagate.
      if (sample) sample.actualCoreCallStartWallMs = performance.now();
      const result = Reflect.apply(original, this, args);
      if (sample && enabled) {
        const sequence = append('core_input_completed', {...sample, completedWallMs: performance.now()});
        row.lastUpdate = {sequence, generation: sample.generation, render: sample.render,
          clock: sample.clock, node: sample.node, inputCaptured: sequence !== null};
      } else if (enabled && !row.destroyed) row.lastUpdate = {sequence: null, generation,
        render: activeFrame()?.render ?? null, clock: clock(), node: node(), inputCaptured: false};
      return result;
    });
    wrap(renderer, 'drawModel', original => function (...args) {
      const frame = activeFrame();
      let draw = null;
      if (enabled && frame?.target && !row.destroyed) {
        try {
          if (this !== renderer || renderer.getModel() !== core) throw Error('Renderer/core instance changed');
          draw = {load: row.load, identity: row.identity, ...context(), render: frame.render,
            modelDrawOrdinal: frame.models.length + 1, lastCompletedInput: row.lastUpdate,
            inputSameRender: row.lastUpdate?.render === frame.render,
            inputSameSharedFrame: !!row.lastUpdate?.clock && !!clock() && row.lastUpdate.clock.frame === clock().frame,
            geometryMilestone: frame.geometryMilestone, schema,
            actualMvpColumnMajor: requiredMatrix4(renderer.getMvpMatrix()),
            pixiProjection: affine(frame.renderer.globalUniforms?.uniforms?.projectionMatrix),
            modelLocal: affine(model.localTransform), modelWorld: affine(model.worldTransform),
            internalLocal: affine(internal.localTransform), centering: affine(internal.centeringTransform),
            drawing: affine(internal.drawingMatrix), parentChain: parents(model),
            position: point(model.position), scale: point(model.scale), pivot: point(model.pivot), anchor: point(model.anchor),
            rotation: model.rotation, alpha: model.alpha, visible: model.visible,
            childIndex: model.parent ? model.parent.children.indexOf(model) : null,
            framebufferViewport: rectangle(frame.renderer.framebuffer?.viewport),
            internalViewport: array(internal.viewport, 4), textures: textureRows(model, renderer),
            reducedCardSpaceOrigin: {value: null, status: 'not_exposed_here_do_not_relabel_PIXI_or_Unity_world'},
            unityLocalToWorld: {value: null, status: 'not_observable_in_this_browser_renderer'},
            drawableRenderOrders: array(drawables.renderOrders, 512),
            drawableDrawOrders: drawables.drawOrders ? array(drawables.drawOrders, 512) : null,
            drawableOpacities: array(drawables.opacities, 512),
            drawableDynamicFlags: array(drawables.dynamicFlags, 512)};
          draw.sequence = append('model_draw_enter', draw);
          frame.models.push({load: row.load, model: row.identity.model, modelDraw: draw.sequence,
            sourceURL, lastCompletedInput: row.lastUpdate, geometryMilestone: frame.geometryMilestone});
          row.modelDraw = draw;
        } catch (error) { fail(error); }
      }
      try { return Reflect.apply(original, this, args); }
      finally { if (draw) row.modelDraw = null; }
    });
    wrap(renderer, 'drawMesh', original => function (...args) {
      const frame = activeFrame(), draw = row.modelDraw;
      if (enabled && frame?.geometryMilestone && draw) {
        try {
          if (++frame.meshes > 512 || args.length !== 9) throw Error('Unexpected drawMesh signature or mesh-call bound');
          // SDK doDrawModel and mask setup both call this exact method. Match
          // actual array objects to the native drawable; never infer identity
          // from a token, a visible shape, a sort ordinal, or numeric equality.
          const matches = [];
          for (let index = 0; index < drawables.count; index++)
            if (drawables.indices[index] === args[3] && drawables.vertexPositions[index] === args[4]) matches.push(index);
          if (matches.length !== 1) throw Error('Submitted vertex/index array identity is ambiguous');
          const index = matches[0], mask = renderer.getClippingContextBufferForMask(), clip = renderer.getClippingContextBufferForDraw();
          if (args[3].length !== args[1] || args[4].length !== 2 * args[2]) throw Error('Submitted array/count mismatch');
          append('mesh_submission', {load: row.load, identity: row.identity, render: frame.render,
            modelDraw: draw.sequence, meshOrdinalWithinFrame: frame.meshes, ...context(),
            drawableIndex: index, drawableId: drawables.ids[index],
            renderOrder: drawables.renderOrders[index], drawOrder: drawables.drawOrders?.[index] ?? null,
            textureIndex: args[0], submittedIndexCount: args[1], submittedVertexCount: args[2],
            indices: array(args[3]), evaluatedModelVerticesXY: array(args[4]), uvs: array(args[5]),
            submittedOpacity: args[6], nativeDrawableOpacity: drawables.opacities[index],
            blendMode: args[7], invertedMask: args[8],
            pass: mask ? 'mask' : 'color', actualMvpColumnMajor: requiredMatrix4(renderer.getMvpMatrix()),
            vertexTransformSource: mask ? 'maskMatrixColumnMajor' : 'actualMvpColumnMajor',
            maskMatrixColumnMajor: mask ? requiredMatrix4(mask._matrixForMask) : null,
            clipMatrixColumnMajor: clip ? requiredMatrix4(clip._matrixForDraw) : null,
            maskContext: id(mask), drawClipContext: id(clip),
            actualGLViewport: array(renderer.gl.getParameter(renderer.gl.VIEWPORT), 4),
            framebuffer: id(renderer.gl.getParameter(renderer.gl.FRAMEBUFFER_BINDING)),
            modelColor: renderer.getModelColor(), isPremultipliedAlpha: renderer.isPremultipliedAlpha(),
            arrayStage: 'actual_drawMesh_arguments_before_one_original_call'});
        } catch (error) { fail(error); }
      }
      return Reflect.apply(original, this, args);
    });
  }
  function install() {
    if (!enabled || installed || !window.PIXI?.live2d?.Live2DModel || !window.PIXI.Renderer) return;
    try {
      wrap(PIXI.live2d.Live2DModel, 'from', original => function (...args) {
        const loadStart = context();
        const promise = Reflect.apply(original, this, args);
        // Resource hashing runs in the owner response observer, never in this
        // promise chain. Observation adds no fetch, decode, or awaited digest.
        return promise.then(model => {
          if (enabled) try { observe(model, args[0], loadStart); } catch (error) { fail(error); }
          return model;
        });
      });
      wrap(PIXI.Renderer.prototype, 'render', original => function (...args) {
        if (!enabled || !armed || this.view !== document.querySelector('#actor')) return Reflect.apply(original, this, args);
        const frame = {renderer: this, render: ++renderSequence, ...context(), models: [], meshes: 0,
          target: targets.has(node()), geometryMilestone: null};
        try {
          if (frame.target) frame.geometryMilestone = chooseGeometry(frame);
        } catch (error) { fail(error); }
        renderStack.push(frame);
        let completed = false;
        try { const result = Reflect.apply(original, this, args); completed = true; return result; }
        finally {
          renderStack.pop();
          if (enabled && frame.target) try {
            const canvas = this.view, box = canvas.getBoundingClientRect();
            const card = document.querySelector('#cardMotion'), style = card ? getComputedStyle(card) : null;
            append('app_render_completed', {render: frame.render, node: frame.node, phaseAtEntry: frame.phase,
              clockAtEntry: frame.clock, end: context(), completed, geometryMilestone: frame.geometryMilestone,
              actualModelSubmissionOrder: frame.models, meshSubmissions: frame.meshes,
              canvas: {width: canvas.width, height: canvas.height, css: rectangle(box)},
              rendererResolution: this.resolution, cardOpacity: style ? Number(style.opacity) : null,
              cardTransform: style?.transform ?? null,
              imageBinding: 'numeric_draw_packet_only_no_extra_render_or_readPixels'});
          } catch (error) { fail(error); }
        }
      });
      installed = true;
    } catch (error) { fail(error); }
  }
  function onTiming(event) {
    if (enabled && targets.has(event.detail?.node)) append('timing', {...context(), detail: {...event.detail}});
  }
  const onPageHide = () => stop('pagehide');
  window.__drawDiagnostic = {
    bindClock(value) {
      // The owner imports the already loaded module only after predecessor
      // ready. This avoids changing its initialization order from an init hook.
      if (!value?.snapshot || armed) throw Error('Cannot bind clock at this boundary');
      clockObject = value;
    },
    arm() {
      if (!installed || !clockObject || !enabled) throw Error('Logger is not ready to arm');
      armed = true; status = 'armed_unexecuted_targets_not_acceptance';
    },
    summary() { return {status, installed, armed, bytes, recordCount: records.length, errors: [...errors],
      milestones: Object.fromEntries(milestones), cleaned, cleanupConflicts: [...cleanupConflicts]}; },
    async finish(reason = 'owner_finish') {
      stop(reason); await Promise.resolve();
      return {version: 1, id: spec.id, documentTimeOrigin: performance.timeOrigin,
        ...this.summary(), records: records.map(text => JSON.parse(text)),
        accepted: false, actualNativeUnityCapture: false};
    },
  };
  document.addEventListener('readystatechange', install);
  document.addEventListener('DOMContentLoaded', install);
  document.addEventListener('stella-player-timing', onTiming);
  window.addEventListener('pagehide', onPageHide);
  timer = setTimeout(() => fail('Diagnostic document time bound exceeded'), spec.maxDurationMs);
  install();
}
