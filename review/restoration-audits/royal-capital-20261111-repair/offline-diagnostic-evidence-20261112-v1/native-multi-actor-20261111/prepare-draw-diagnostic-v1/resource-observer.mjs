import {createHash} from 'node:crypto';

// UNEXECUTED OWNER HELPER. Hash the existing browser responses; never fetch the
// resource again, intercept/fulfil a request, or return its body to CLI output.
export function attachResourceObserver(page, {baseURL, lock, onFailure}) {
  const records = [], pending = new Set(), errors = [];
  const requestIds = new WeakMap();
  let nextRequest = 0, detached = false, reservedBytes = 0, actualBytes = 0;
  const origin = new URL(baseURL).origin;
  const expected = new Map(lock.resources.map(row => [row.pathname, row]));
  const maxBodyBytes = 8 * 1024 * 1024, maxTotalBytes = 32 * 1024 * 1024;
  const watched = value => {
    const url = new URL(value);
    if (url.origin !== origin) return false;
    return expected.has(url.pathname) || /\/models\/ac\/ac_[a-z0-9_]+\/ac\/(?:ac\.model3\.json|ac\.moc3|textures\/texture_\d+\.png)$/.test(url.pathname);
  };
  const fail = error => {
    if (errors.length < 16) errors.push(String(error).slice(0, 700));
    onFailure?.(error);
  };
  const requestId = request => {
    if (!requestIds.has(request)) requestIds.set(request, ++nextRequest);
    return requestIds.get(request);
  };
  const response = response => {
    if (detached || !watched(response.url())) return;
    if (records.length >= 64) { fail(Error('Resource response-count bound exceeded')); return; }
    const request = response.request(), headers = response.headers();
    const row = {request: requestId(request), url: response.url(), status: response.status(),
      hostResponseWallMs: Date.now(), requestTiming: request.timing(),
      contentLength: headers['content-length'] ?? null, contentEncoding: headers['content-encoding'] ?? null,
      bodySha256: null, bodyBytes: null, error: null};
    records.push(row);
    const task = (async () => {
      try {
        // Require a bounded declared body before Playwright materializes it.
        // The local adapter supplies Content-Length. Unknown transfer lengths
        // remain failures instead of silently permitting an unbounded read.
        if (row.status !== 200) throw Error('Resource status is not 200: ' + row.url);
        if (!/^\d+$/.test(row.contentLength || '')) throw Error('Resource has no bounded Content-Length');
        const declared = Number(row.contentLength);
        if (declared > maxBodyBytes || reservedBytes + declared > maxTotalBytes) throw Error('Resource byte budget exceeded');
        reservedBytes += declared;
        const body = await response.body();
        if (body.length > maxBodyBytes || actualBytes + body.length > maxTotalBytes) throw Error('Decoded resource body budget exceeded');
        actualBytes += body.length;
        row.bodyBytes = body.length;
        row.bodySha256 = createHash('sha256').update(body).digest('hex');
        row.hashStage = 'actual_Playwright_response_body_no_second_request';
        const frozen = expected.get(new URL(row.url).pathname);
        row.expected = frozen ? {bytes: frozen.bytes, sha256: frozen.sha256} : null;
        row.matchesFrozen = frozen ? body.length === frozen.bytes && row.bodySha256 === frozen.sha256 : null;
        if (frozen && !row.matchesFrozen) throw Error('Actual resource differs from frozen file: ' + row.url);
      } catch (error) { row.error = String(error); fail(error); }
    })();
    pending.add(task); task.finally(() => pending.delete(task));
  };
  const failed = request => {
    if (watched(request.url())) fail(Error('Actual resource request failed: ' + request.url()));
  };
  page.on('response', response); page.on('requestfailed', failed);
  return {
    async finish() {
      detached = true;
      page.off('response', response); page.off('requestfailed', failed);
      let timeout;
      await Promise.race([Promise.allSettled([...pending]), new Promise(resolve => {
        timeout = setTimeout(() => { fail(Error('Resource hashing did not settle within 5s')); resolve(); }, 5000);
      })]);
      clearTimeout(timeout);
      return {records, errors, pending: pending.size, actualBytes, reservedBytes,
        additionalRequestsMade: 0, responseBodiesRetained: false};
    },
  };
}

export function bindLoadDigests(trace, network, lock, baseURL) {
  const normalize = (value, base = baseURL) => {
    if (typeof value !== 'string') return null;
    try { return base ? new URL(value, base).href : new URL(value).href; }
    catch { return null; }
  };
  const normalModels = new Map(lock.models.map(row => [normalize(row.modelJSONPath), row]));
  const result = [], failures = [];
  for (const load of trace.records.filter(row => row.kind === 'load')) {
    const source = normalize(load.sourceURL), modelLock = normalModels.get(source);
    const binding = {load: load.load, identity: load.identity, sourceURL: source,
      targetModelLock: modelLock?.model ?? null, resources: [], errors: []};
    const add = (kind, url) => {
      const matching = network.records.filter(row => row.url === url && row.status === 200 && row.bodySha256);
      const digests = [...new Set(matching.map(row => row.bodySha256))];
      const value = {kind, url, sha256: digests.length === 1 ? digests[0] : null,
        observedRequests: matching.map(row => row.request),
        uniqueRequestForThisLoadProven: false,
        bindingMethod: 'observed_source_or_texture_URL_and_all_recorded_response_bodies_for_that_URL_agree'};
      binding.resources.push(value);
      if (!url || digests.length !== 1) binding.errors.push('Missing or conflicting actual response digest: ' + url);
    };
    add('modelJSON', source);
    const references = load.suppliedReferences;
    add('MOC', source && references?.Moc ? normalize(references.Moc, source) : null);
    const declared = (references?.Textures || []).map(value => source ? normalize(value, source) : null);
    for (const texture of load.textures) {
      const observed = normalize(texture.actualURL, source);
      if (!declared.includes(observed)) binding.errors.push('Actual texture URL does not match supplied FileReferences');
      add('texture', observed);
    }
    if (load.textures.length !== declared.length) binding.errors.push('Texture reference/instance count mismatch');
    if (modelLock) {
      const paths = new Map(lock.resources.filter(row => row.model === modelLock.model).map(row => [normalize(row.pathname), row]));
      for (const resource of binding.resources) {
        const expected = paths.get(resource.url);
        if (!expected || resource.sha256 !== expected.sha256) binding.errors.push('Target per-load resource binding differs from lock');
      }
    }
    // Shared PIXI atlases can have one delivery used by several loads. The
    // digest is a content/URL binding; a unique physical upload or distinct
    // network request for every load is deliberately never asserted.
    binding.gpuBytesDigest = {value: null, status: 'not_observable_here'};
    if (modelLock && binding.errors.length) failures.push({load: binding.load, errors: binding.errors});
    result.push(binding);
  }
  return {loads: result, targetBindingFailures: failures, accepted: false};
}

export function auditPacketCoverage(trace, lock, baseURL, targetNode) {
  // This audits only whether the requested observations exist and join. It
  // cannot validate their geometric agreement with an original recording.
  const expectedURLs = lock.models.map(row => new URL(row.modelJSONPath, baseURL).href).sort();
  const bySequence = new Map(trace.records.map(row => [row.sequence, row]));
  const ready = trace.records.filter(row => row.kind === 'app_render_completed' && row.node === targetNode &&
    row.phaseAtEntry === 'ready' && row.geometryMilestone?.startsWith('ready_observed_elapsed_'));
  const failures = [];
  if (ready.length !== 4) failures.push('Four bounded ready geometry milestones were not captured');
  for (const frame of ready) {
    const urls = frame.actualModelSubmissionOrder.map(row => row.sourceURL).sort();
    if (!frame.completed || JSON.stringify(urls) !== JSON.stringify(expectedURLs))
      failures.push('Actual ready frame did not submit exactly the three locked model URLs: ' + frame.render);
    for (const submission of frame.actualModelSubmissionOrder) {
      const draw = bySequence.get(submission.modelDraw), input = bySequence.get(draw?.lastCompletedInput?.sequence);
      if (!draw || !draw.actualMvpColumnMajor || !draw.modelWorld || !draw.modelLocal ||
          !draw.internalLocal || !draw.centering || !draw.drawing || !draw.parentChain?.length)
        failures.push('Missing required submitted matrix chain for model draw: ' + submission.modelDraw);
      if (!input || input.kind !== 'core_input_completed' || input.identity.native !== draw?.identity.native ||
          input.generation !== draw?.lastCompletedInput?.generation || input.node !== targetNode)
        failures.push('Submitted geometry has no joined actual target Core input: ' + submission.modelDraw);
      if (!trace.records.some(row => row.kind === 'mesh_submission' && row.modelDraw === submission.modelDraw &&
          row.evaluatedModelVerticesXY?.length && row.indices?.length))
        failures.push('No actual full mesh argument submission for model draw: ' + submission.modelDraw);
    }
  }
  return {status: failures.length ? 'partial_missing_observations' : 'requested_observations_joined',
    readyGeometryFrames: ready.map(row => row.render), failures, accepted: false};
}
