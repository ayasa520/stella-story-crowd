import {readFile, mkdir, writeFile, stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {attachResourceObserver, bindLoadDigests, auditPacketCoverage} from './resource-observer.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const digest = value => createHash('sha256').update(value).digest('hex');
const approvedTargets = new Set(['10020002:5', '10020002:15']);

// UNEXECUTED OWNER DRAFT. Importing defines this function but starts no browser,
// navigation or capture. The owner must supply a new frozen execution object.
// In particular, canonical372 currently cannot compile the P09 native_parent
// candidates, so the checked-in template intentionally cannot pass this gate.
export async function runDrawDiagnostic(initialPage, execution) {
  if (!execution?.rootReleased || !execution.singleBrowserOwnerAssigned || !execution.freezeComplete ||
      !execution.reviewedMultiActorExecutionAvailable ||
      !/^http:\/\/127\.0\.0\.1:\d+$/.test(execution.baseURL || '') ||
      !Array.isArray(execution.cases) || execution.cases.length < 1 || execution.cases.length > 2)
    throw Error('No concrete root-released multi-actor diagnostic execution');
  const instrumentText = await readFile(path.join(HERE, 'instrument.js'), 'utf8');
  const lockText = await readFile(path.join(HERE, 'resource-lock.json'), 'utf8');
  if (digest(instrumentText) !== execution.instrumentSha256 || digest(lockText) !== execution.resourceLockSha256)
    throw Error('Prepared diagnostic or frozen resource-lock hash differs');
  const lock = JSON.parse(lockText);
  const output = path.resolve(execution.outputRoot || '');
  if (!output.startsWith(HERE + '/runs/') || output === HERE + '/runs') throw Error('Output is outside a new diagnostic run');
  try { await stat(output); throw Error('Preserve existing run evidence; output already exists'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  await mkdir(output, {recursive: true});
  const browserContext = initialPage.context();
  if (browserContext.pages().length !== 1) throw Error('Expected one owner initial Page');
  await initialPage.close();
  const summaries = [];
  for (const spec of execution.cases) {
    if (!/^[a-z0-9-]{1,90}$/.test(spec.id || '') || !approvedTargets.has(spec.targetNode) ||
        spec.route?.length !== 3 || spec.route[1] !== spec.targetNode ||
        !spec.url?.startsWith(execution.baseURL + '/?') || !spec.programSha256 || !spec.packetSha256 ||
        !Number.isInteger(spec.programBytes) || spec.programBytes > 16 * 1024 * 1024)
      throw Error('Missing concrete previous/target/next route or frozen program');
    if (browserContext.pages().length !== 0) throw Error('Previous diagnostic Page remains');
    const page = await browserContext.newPage();
    let trace = null, network = null, bindings = null, coverage = null, program = null, failure = null;
    const errors = [], consoleErrors = [];
    let rejectFatal;
    const fatal = new Promise((_, reject) => { rejectFatal = reject; });
    fatal.catch(() => {});
    const fatalError = error => {
      if (errors.length < 16) errors.push(String(error).slice(0, 700));
      rejectFatal(error);
    };
    const guard = promise => Promise.race([promise, fatal]);
    const observer = attachResourceObserver(page, {baseURL: execution.baseURL, lock, onFailure: fatalError});
    const onPageError = error => fatalError(error);
    const onConsole = message => {
      if (message.type() === 'error' && consoleErrors.length < 16) consoleErrors.push(message.text());
    };
    page.on('pageerror', onPageError); page.on('console', onConsole);
    const frame = () => {
      const matches = page.frames().filter(item => {
        try { return new URL(item.url()).pathname === '/player/player.html'; } catch { return false; }
      });
      if (matches.length !== 1) throw Error('Expected one actual production player iframe');
      return matches[0];
    };
    const waitReady = node => guard(frame().waitForFunction(expected => {
      const qa = window.__drawDiagnostic;
      if (qa?.summary().errors.length || document.body?.dataset.phase === 'error') throw Error('Runtime diagnostic/player failure');
      return document.body?.dataset.node === expected && document.body.dataset.phase === 'ready';
    }, node, {timeout: 30000}));
    try {
      await page.addInitScript({content: '(' + instrumentText + ')(' + JSON.stringify({id: spec.id,
        targetNodes: [spec.targetNode], traceByteBudget: 20 * 1024 * 1024,
        maxRenderFramesPerNode: 240, maxDurationMs: 45000}) + ');'});
      const responsePromise = page.waitForResponse(response => new URL(response.url()).pathname === '/program', {timeout: 30000});
      responsePromise.catch(() => {});
      // No viewport, iframe style, camera, rate, source, registry, or data
      // fixture is assigned by this runner. Its actual geometry is observed.
      await guard(page.goto(spec.url, {waitUntil: 'domcontentloaded', timeout: 30000}));
      const response = await guard(responsePromise), headers = response.headers();
      if (response.status() !== 200 || Number(headers['content-length']) !== spec.programBytes)
        throw Error('Actual program declared size/status differs from frozen preflight');
      const body = await response.body();
      if (body.length !== spec.programBytes || digest(body) !== spec.programSha256) throw Error('Actual program hash/size differs');
      program = JSON.parse(body.toString('utf8'));
      if (program.review_only_overrides?.packetSha256 !== spec.packetSha256) throw Error('Actual private packet differs');
      const target = program.nodes.find(row => row.id === spec.targetNode);
      const actualModels = target?.actors?.map(row => row.model).sort();
      if (JSON.stringify(actualModels) !== JSON.stringify(['chin01', 'kan01', 'ton01']))
        throw Error('Reviewed three-model target is not available in this frozen program');
      await waitReady(spec.route[0]);
      await guard(frame().evaluate(async () => {
        // The predecessor already rendered via NativePlacedViewer, which
        // imported this module. This is a cached module read, not clock setup.
        const {visualFrameClock} = await import('/studio/visual_frame_clock.js');
        const qa = window.__drawDiagnostic;
        if (!qa?.summary().installed) throw Error('Init instrumentation missed actual factories');
        qa.bindClock(visualFrameClock); qa.arm();
      }));
      await guard(page.locator('#advance').click());
      await waitReady(spec.targetNode);
      await guard(frame().waitForFunction(target => {
        const qa = window.__drawDiagnostic, summary = qa.summary();
        if (summary.errors.length) throw Error(summary.errors.join('; '));
        return summary.milestones[target]?.readySamples.length === 4;
      }, spec.targetNode, {timeout: 15000}));
      await guard(page.locator('#advance').click());
      await waitReady(spec.route[2]);
    } catch (error) { failure = {message: String(error), stack: String(error.stack || '').slice(0, 2000)}; }
    finally {
      try {
        try { trace = await frame().evaluate(() => window.__drawDiagnostic?.finish('owner_finally') || null); }
        catch (error) { failure ??= {message: 'Trace/cleanup export failed: ' + error}; }
        network = await observer.finish();
        if (trace) {
          bindings = bindLoadDigests(trace, network, lock, execution.baseURL);
          coverage = auditPacketCoverage(trace, lock, execution.baseURL, spec.targetNode);
          if (coverage.failures.length || bindings.targetBindingFailures.length || !trace.cleaned ||
              trace.cleanupConflicts.length || trace.errors.length)
            failure ??= {message: 'Resource/coverage/observer/cleanup packet is partial; inspect retained errors'};
          // Every frozen source response must actually be present and hashed.
          // A hash in a manifest alone never establishes the delivered source.
          for (const source of lock.resources.filter(row => row.kind === 'source'))
            if (!network.records.some(row => new URL(row.url).pathname === source.pathname && row.matchesFrozen))
              failure ??= {message: 'Required actual source response digest missing: ' + source.pathname};
        } else failure ??= {message: 'No draw trace'};
        if (errors.length || consoleErrors.length || network.errors.length || network.pending)
          failure ??= {message: 'Actual browser/resource errors retained'};
        const payload = {status: failure ? 'partial_failed_not_acceptance' : 'captured_requires_offline_audit_not_acceptance',
          id: spec.id, failure, trace, network, loadResourceBindings: bindings, observationCoverage: coverage,
          browserErrors: errors, consoleErrors, expectedExecution: spec, actualFrozenProgramSha256: spec.programSha256,
          actualRouteNodes: program?.nodes.filter(row => spec.route.includes(row.id)),
          noAdditionalRenderOrModelUpdate: true, screenshotsTaken: 0, accepted: false};
        // Write only new run evidence; no pixel/base64 data or full trace is
        // sent to CLI. Closing the Page is guaranteed even if export fails.
        const raw = Buffer.from(JSON.stringify(payload));
        if (raw.length > 24 * 1024 * 1024) throw Error('Final packet byte budget exceeded');
        await writeFile(path.join(output, spec.id + '.json.gz'), gzipSync(raw, {level: 1}), {flag: 'wx'});
      } catch (error) {
        failure ??= {message: 'Diagnostic export/processing failed: ' + error};
        // A bounded separate failure receipt survives even when the main
        // packet could not be serialized or the evidence directory rejected it.
        await writeFile(path.join(output, spec.id + '.failure.json'), JSON.stringify({id: spec.id,
          failure, traceSummary: trace ? {status: trace.status, bytes: trace.bytes, errors: trace.errors,
            cleaned: trace.cleaned, cleanupConflicts: trace.cleanupConflicts} : null,
          errors, consoleErrors, accepted: false}), {flag: 'wx'}).catch(() => {});
      }
      finally {
        if (!network) await observer.finish().catch(error => { failure ??= {message: String(error)}; });
        page.off('pageerror', onPageError); page.off('console', onConsole);
        if (!page.isClosed()) await page.close();
      }
      summaries.push({id: spec.id, failure, accepted: false});
    }
    if (browserContext.pages().length !== 0) throw Error('Diagnostic Page did not close');
    if (failure) break;
  }
  return {cases: summaries, browserPagesRemaining: browserContext.pages().length,
    needsImmediateOwnerChromeAndCliClose: true, accepted: false};
}
