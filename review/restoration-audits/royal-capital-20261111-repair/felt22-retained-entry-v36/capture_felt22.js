async page => {
  const out = '/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/visual-low/p11-felt21-production-review-v1/fresh-felt22-v31/';
  const packetSha = 'e090a6e842a46ed618eda27f9f6b37bd737c8433c1a666335f4a480d628f70ed';
  const exampleId = 'felt22-ikaru-from-formal21-v31', base = 'http://127.0.0.1:5189';
  const events = [], failures = [], responses = [], visits = [];
  const listener = message => {if (/STORY_|STELLA_PLAYER_|Error/.test(message.text()))
    events.push({epoch: Date.now(), type: message.type(), value: message.text()});};
  const pageError = error => failures.push({epoch: Date.now(), value: String(error)});
  const responseListener = response => {if (response.status() >= 400)
    responses.push({epoch: Date.now(), status: response.status(), url: response.url()});};
  const saveJson = async (name, payload) => {
    const download = page.waitForEvent('download', {timeout: 180000});
    await page.evaluate(async ({name, payload}) => {
      const blob = await new Response(new Blob([JSON.stringify(payload)], {type: 'application/json'})
        .stream().pipeThrough(new CompressionStream('gzip'))).blob();
      const url = URL.createObjectURL(blob), link = document.createElement('a');
      link.href = url; link.download = name; link.click();
      // Revoking after the task lets the download consume its actual Blob.
      setTimeout(() => URL.revokeObjectURL(url), 0);
    }, {name, payload});
    await (await download).saveAs(out + name);
  };
  page.on('console', listener); page.on('pageerror', pageError); page.on('response', responseListener);
  let frame = null, program = null, nodes = [], trace = null, runError = null;
  try {
    await page.setViewportSize({width: 480, height: 895});
    await page.goto(base + '/?scene=10280014&node=20&nativePreview=' + exampleId);
    await page.evaluate(() => {const iframe = document.querySelector('iframe'); iframe.style.width = '480px'; iframe.style.height = '856px';});
    await page.waitForFunction(() => {const body = document.querySelector('iframe')?.contentDocument?.body;
      return body?.dataset.node === '10280014:20' && body.dataset.phase === 'ready';}, null, {timeout: 60000});
    program = await page.evaluate(async key => {
      const response = await fetch('/program?scene=10280014&node=20&nativePreview=' + key);
      if (!response.ok) throw new Error('Bounded program HTTP ' + response.status);
      return response.json();
    }, exampleId);
    if (program.review_only_overrides?.packetSha256 !== packetSha || program.review_only_overrides?.persisted !== false
        || program.review_only_overrides?.exampleId !== exampleId)
      throw new Error('v31 packet identity or memory-only status mismatch.');
    nodes = program.nodes.filter(row => /^10280014:(20|21|22|23)$/.test(row.id));
    const a = nodes.find(row => row.id === '10280014:21'), b = nodes.find(row => row.id === '10280014:22');
    if (nodes.length !== 4 || a?.model !== 'felt01' || b?.model !== 'felt01'
        || a?.body !== 'act_normal' || a?.face !== 'face_shinken' || b?.body !== 'act_ikaru' || b?.face !== 'face_shinken')
      throw new Error('Compiled formal21 / private22 motion or retained model mismatch.');
    frame = page.frames().find(item => item.url().includes('/player/player.html'));
    if (!frame) throw new Error('Actual player iframe not found.');
    await frame.evaluate(async () => {
      const {visualFrameClock} = await import('/studio/visual_frame_clock.js');
      const {ActorAnimation} = await import('/studio/actor_animation.js');
      const trace = window.felt31Trace = {
        timing: [], alpha: [], raf: [], actorClockCalls: [], images: [],
        parameterSchemas: [], parameterObserverRegistrations: [], preUpdate: [], entrySnapshots: [], samplingIssues: [],
        recording: 'One actual production case. Passive event/style/rAF observations and every observed21/22 actor-canvas PNG; no fixed capture rate, synthetic CardOut, parameter writes, extra clock integration or render calls.'
      };
      const card = document.querySelector('#cardMotion'), actor = document.querySelector('#actor');
      const capture = document.createElement('canvas'), counts = new Map(), identities = new WeakMap(), observed = new WeakMap(), registrations = [];
      const parameterIds = ['ParamAngleX', 'ParamAngleY', 'ParamAngleZ', 'ParamEyeLOpen', 'ParamEyeROpen',
        'ParamBrowLAngle', 'ParamBrowRAngle', 'ParamBrowLForm', 'ParamBrowRForm', 'ParamBrowLY', 'ParamBrowRY',
        'ParamUpperArmL', 'ParamUpperArmR', 'ParamForeArmL', 'ParamForeArmR', 'ParamHandL', 'ParamHandR',
        'ParamBodyAngleX', 'ParamBodyAngleY', 'ParamBodyAngleZ', 'ParamShoulder', 'ParamShoulderL', 'ParamShoulderR'];
      let enabled = true, previous = null, nextIdentity = 1, rafHandle = null;
      const id = object => {
        if (!object || (typeof object !== 'object' && typeof object !== 'function')) return null;
        if (!identities.has(object)) identities.set(object, nextIdentity++);
        return identities.get(object);
      };
      const finite = value => Number.isFinite(value) ? value : null;
      const binding = animation => {
        const viewer = animation.viewer, internal = viewer.model?.internalModel, core = viewer.core;
        const native = core?.getModel();
        return {animation: id(animation), viewer: id(viewer), model: id(viewer.model), internal: id(internal),
          core: id(core), native: id(native), modelId: viewer.detail?.id || null};
      };
      const state = animation => ({time: animation.time, last: animation.last, running: animation.running,
        model: animation.viewer.detail?.id, layers: [...animation.layers].map(([layer, row]) =>
          ({layer, token: row.token, start: row.start, offset: row.offset, weight: row.weight,
            blend: row.blend ? {start: row.blend.start, duration: row.blend.duration, sourceToken: row.blend.source.token} : null}))});
      const read = animation => {
        const native = animation.viewer.core.getModel(), parameters = native.parameters;
        // Raw array access cannot create synthetic Cubism parameters. A missing
        // key remains explicitly missing; it is never converted to numeric0.
        const rows = parameterIds.map(name => {
          const index = parameters.ids.indexOf(name), exists = index >= 0;
          return {id: name, index, exists, value: exists ? finite(parameters.values[index]) : null,
            defaultValue: exists ? finite(parameters.defaultValues[index]) : null,
            minimumValue: exists ? finite(parameters.minimumValues[index]) : null,
            maximumValue: exists ? finite(parameters.maximumValues[index]) : null,
            viewerTemplateValue: exists ? finite(animation.viewer.parameters[index]) : null,
            sdkSavedValue: exists ? finite(animation.viewer.core._savedParameters?.[index]) : null};
        });
        return {rows, flat: Object.fromEntries(rows.filter(row => row.exists).map(row => [row.id, row.value]))};
      };
      const issue = (kind, detail) => {
        if (!trace.samplingIssues.some(row => row.kind === kind && row.detail?.node === detail?.node))
          trace.samplingIssues.push({kind, detail, at: performance.now(), clock: visualFrameClock.snapshot()});
      };
      const fnSource = fn => Function.prototype.toString.call(fn);
      const inspectOrder = registration => {
        const listeners = registration.internal.listeners('beforeModelUpdate');
        const viewerIndex = listeners.indexOf(registration.viewerHandler), observerIndex = listeners.indexOf(registration.listener);
        return {viewerIndex, observerIndex, listenerCount: listeners.length,
          verified: viewerIndex >= 0 && observerIndex > viewerIndex && listeners.filter(fn => /(?:\(\)|function\s*\([^)]*\))\s*(?:=>)?\s*(?:\{\s*)?this\.renderPose\(\)/.test(fnSource(fn))).length === 1};
      };
      const ensureObserver = animation => {
        const viewer = animation.viewer, internal = viewer.model?.internalModel;
        if (!internal || observed.has(internal)) return;
        if (typeof internal.listeners !== 'function' || typeof internal.on !== 'function') {
          issue('missing_event_emitter_api', {node: document.body.dataset.node, instance: binding(animation)}); return;
        }
        const listeners = internal.listeners('beforeModelUpdate');
        const matches = listeners.filter(fn => /(?:\(\)|function\s*\([^)]*\))\s*(?:=>)?\s*(?:\{\s*)?this\.renderPose\(\)/.test(fnSource(fn)));
        const instance = binding(animation), parameters = viewer.core.getModel().parameters;
        trace.parameterSchemas.push({schema: instance.native, instance, at: performance.now(), clock: visualFrameClock.snapshot(),
          count: parameters.count, ids: Array.from(parameters.ids),
          defaults: Array.from(parameters.defaultValues), minimums: Array.from(parameters.minimumValues), maximums: Array.from(parameters.maximumValues),
          viewerTemplate: Array.from(viewer.parameters), sdkSavedArrayPresent: !!viewer.core._savedParameters,
          sdkSavedAtRegistration: Array.from(viewer.core._savedParameters || []),
          selectedIds: parameterIds, selected: read(animation).rows});
        const registration = {internal, animation, instance, viewerHandler: matches.length === 1 ? matches[0] : null,
          renderOrdinal: 0, latest: null, listener: null};
        const record = {instance, at: performance.now(), clock: visualFrameClock.snapshot(),
          listenersBefore: listeners.map((fn, index) => ({index, source: fnSource(fn)})), viewerHandlerMatches: matches.length};
        registration.listener = () => {
          if (!enabled) return;
          try {
            const order = inspectOrder(registration), current = binding(animation), now = performance.now();
            const sameInstance = Object.keys(instance).every(key => instance[key] === current[key]);
            const animatorStillBound = viewer.animator === animation;
            const row = {index: trace.preUpdate.length, renderOrdinal: ++registration.renderOrdinal,
              node: document.body.dataset.node, at: now, phase: document.body.dataset.phase,
              shared: visualFrameClock.snapshot(), instance: current, schema: instance.native, order,
              sameInstance, animatorStillBound, actor: state(animation), parameters: read(animation).rows,
              stage: 'beforeModelUpdate_after_existing_viewer_handler_before_sdk_core_update',
              appliedStageSupported: order.verified && sameInstance && animatorStillBound};
            trace.preUpdate.push(row); registration.latest = row;
            if (!row.appliedStageSupported) issue('pre_update_binding_or_listener_order_unverified', {node: row.node, index: row.index, order, sameInstance, animatorStillBound});
          } catch (error) {issue('pre_update_observer_error', {node: document.body.dataset.node, error: String(error)});}
        };
        // Append to the already installed viewer event list. The production
        // render handler is never replaced or called by this observer. Order
        // is measured again during every real emission before its label can
        // support an applied-pose read. Registration during a clock call may
        // miss that emission; such a first image must remain unpaired.
        internal.on('beforeModelUpdate', registration.listener);
        record.orderAfter = inspectOrder(registration);
        trace.parameterObserverRegistrations.push(record);
        registrations.push(registration); observed.set(internal, registration);
        if (!record.orderAfter.verified) issue('registration_order_unverified', {node: document.body.dataset.node, record});
      };
      const originalClock = ActorAnimation.prototype.clock;
      ActorAnimation.prototype.clock = function(...args) {
        const before = this.time, priorLast = this.last, running = this.running;
        const shared = this.visualClock.snapshot(), now = this.visualClock.now();
        // Exactly one original call. Observing must not advance the shared
        // clock, invoke render, or reapply an input parameter or motion.
        const result = originalClock.apply(this, args);
        window.felt31Actor = this;
        trace.actorClockCalls.push({node: document.body.dataset.node, model: this.viewer.detail?.id,
          instance: binding(this), before, after: this.time, priorLast, running, shared, sharedNow: now,
          sameClockObject: this.visualClock === visualFrameClock,
          expectedAfter: before + (running ? now - priorLast : 0), at: performance.now()});
        try {ensureObserver(this);} catch (error) {issue('observer_registration_error', {node: document.body.dataset.node, error: String(error)});}
        return result;
      };
      const timingListener = event => {
        const eventRow = {at: performance.now(), epoch: Date.now(), detail: {...event.detail},
          opacity: Number(getComputedStyle(card).opacity), clock: visualFrameClock.snapshot()};
        trace.timing.push(eventRow);
        if (event.detail.stage === 'enter' && ['10280014:21', '10280014:22'].includes(event.detail.node)) {
          const animation = window.felt31Actor, previousImage = trace.images.at(-1);
          // Player.enter emits before motion selection. Keep the prior actor
          // and last PNG reference without inserting a transition or touching
          // Animator state. Its raw read stage is deliberately not relabelled.
          trace.entrySnapshots.push({...eventRow, instance: animation ? binding(animation) : null,
            actor: animation ? state(animation) : null, rawRead: animation ? read(animation).rows : null,
            lastImageIndex: previousImage ? trace.images.length - 1 : null,
            lastImageNode: previousImage?.node || null, lastImageSharedFrame: previousImage?.shared.frame ?? null,
            label: 'enter_event_before_motion_selection_later_raw_array_read'});
        }
      };
      document.addEventListener('stella-player-timing', timingListener);
      const alphaObserver = new MutationObserver(() => trace.alpha.push({at: performance.now(), node: document.body.dataset.node,
        opacity: Number(getComputedStyle(card).opacity), clock: visualFrameClock.snapshot()}));
      alphaObserver.observe(card, {attributes: true, attributeFilter: ['style']});
      const tick = timestamp => {
        if (!enabled) return;
        const at = performance.now(), node = document.body.dataset.node, shared = visualFrameClock.snapshot();
        const row = {node, at, rafTimestamp: timestamp, callbackLag: at - timestamp,
          deltaFromPrevious: previous === null ? null : at - previous,
          opacity: Number(getComputedStyle(card).opacity), shared, phase: document.body.dataset.phase};
        const animation = window.felt31Actor;
        if (animation) {
          row.actor = state(animation); row.instance = binding(animation);
          const raw = read(animation); row.parameters = raw.flat;
          row.parameterReadback = {stage: 'later_rAF_raw_read_not_dynamically_proven_post_restore', schema: row.instance.native, rows: raw.rows};
          const pre = observed.get(animation.viewer.model?.internalModel)?.latest;
          const paired = !!pre && pre.shared.frame === shared.frame && pre.instance.animation === row.instance.animation
            && pre.instance.model === row.instance.model && pre.instance.core === row.instance.core
            && pre.instance.native === row.instance.native && pre.at <= at;
          row.preUpdateLink = {paired, index: pre?.index ?? null, renderOrdinal: pre?.renderOrdinal ?? null,
            sameSharedFrame: !!pre && pre.shared.frame === shared.frame,
            preNode: pre?.node || null, sameNode: !!pre && pre.node === node,
            preAt: pre?.at ?? null, rawReadAt: at, appliedStageSupported: paired && pre.node === node && pre.appliedStageSupported};
        }
        const ready = trace.timing.find(item => item.detail.node === node && item.detail.stage === 'motion_ready');
        row.elapsedGame = ready ? shared.gameSeconds - ready.clock.gameSeconds : null;
        row.elapsedWall = ready ? at - ready.at : null;
        if (['10280014:21', '10280014:22'].includes(node)) {
          const count = counts.get(node) || 0;
          if (count >= 600 || ready && row.elapsedGame > 8) {
            issue('bounded_window_limit_reached', {node, images: count, elapsedGame: row.elapsedGame});
          } else {
            // Every observed frame is preserved, even before motion_ready or
            // while the previous model leaves21. Extraction anchors these raw
            // timestamps afterwards; no negative pre-roll time is discarded.
            const copyStart = performance.now();
            capture.width = actor.width; capture.height = actor.height;
            capture.getContext('2d').drawImage(actor, 0, 0);
            trace.images.push({...row, index: trace.images.length, copyStart, png: capture.toDataURL('image/png'),
              copyEnd: performance.now(), canvas: {width: actor.width, height: actor.height}});
            counts.set(node, count + 1);
          }
        }
        row.end = performance.now(); trace.raf.push(row); previous = at; rafHandle = requestAnimationFrame(tick);
      };
      rafHandle = requestAnimationFrame(tick);
      window.stopFelt31Trace = () => {
        enabled = false; cancelAnimationFrame(rafHandle); alphaObserver.disconnect();
        document.removeEventListener('stella-player-timing', timingListener);
        for (const registration of registrations) registration.internal.off('beforeModelUpdate', registration.listener);
        ActorAnimation.prototype.clock = originalClock;
        trace.cleanup = {at: performance.now(), clock: visualFrameClock.snapshot(), clockWrapperRestored: ActorAnimation.prototype.clock === originalClock,
          observerListenersRemoved: registrations.every(row => !row.internal.listeners('beforeModelUpdate').includes(row.listener))};
      };
    });
    const record = async node => {
      const state = await page.evaluate(() => ({node: document.querySelector('iframe').contentDocument.body.dataset.node,
        phase: document.querySelector('iframe').contentDocument.body.dataset.phase, state: window.latestPlayerState}));
      if (state.node !== '10280014:' + node || state.phase !== 'ready') throw new Error('Atomic ready visit mismatch for ' + node);
      visits.push(state);
    };
    await record(20);
    for (const node of [21, 22, 23]) {
      // A real iframe pointer gesture also gives production audio its normal
      // interaction boundary. Never fake a media event or alter autoplay policy.
      await frame.locator('#viewport').click({position: {x: 220, y: 320}});
      await page.waitForFunction(id => {const body = document.querySelector('iframe')?.contentDocument?.body;
        return body?.dataset.node === id && body.dataset.phase === 'ready';}, '10280014:' + node, {timeout: 60000});
      if (node === 21 || node === 22) await frame.waitForFunction(id => {
        const trace = window.felt31Trace, ready = trace.timing.find(item => item.detail.node === id && item.detail.stage === 'motion_ready');
        const last = trace.raf.at(-1), held = id.endsWith(':21') || last?.actor?.layers.some(row => row.layer === 'motion' && row.token === 'act_ikaru_w');
        return ready && last?.node === id && last.elapsedGame >= 3.5 && held;
      }, '10280014:' + node, {timeout: 60000});
      await record(node);
    }
  } catch (error) {
    runError = {name: error.name, message: String(error.message || error), stack: error.stack || ''};
    failures.push({epoch: Date.now(), value: runError.message});
  } finally {
    try {
      if (frame && !frame.isDetached()) trace = await frame.evaluate(() => {window.stopFelt31Trace?.(); return window.felt31Trace || null;});
      const payload = {key: exampleId, previewKey: exampleId, nodes, overrides: program?.review_only_overrides || null,
        visits, trace, console: events, failures, httpErrors: responses,
        playerClockWrapperRestored: trace?.cleanup?.clockWrapperRestored === true,
        runError, success: !runError && failures.length === 0 && responses.length === 0
          && !events.some(row => row.type === 'error') && trace?.samplingIssues.length === 0};
      await saveJson(exampleId + '-shared-clock.json.gz', payload);
    } finally {
      page.off('console', listener); page.off('pageerror', pageError); page.off('response', responseListener);
      // Release Live2D immediately. The sole browser owner must then close the
      // session and prove CLI/OS Chrome0 before any offline PNG review.
      await page.goto('about:blank');
    }
  }
  return {key: exampleId, visits, images: trace?.images.length || 0, preUpdateSamples: trace?.preUpdate.length || 0,
    observerRegistrations: trace?.parameterObserverRegistrations || [], samplingIssues: trace?.samplingIssues || [],
    cleanup: trace?.cleanup || null, failures, httpErrors: responses, runError,
    needsImmediateBrowserClose: true, dynamicVisualVerdict: 'pending_after_raw_extraction_and_direct_review'};
}
