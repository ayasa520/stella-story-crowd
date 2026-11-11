import {readFile, mkdir, writeFile, stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {CaseDeadline} from './deadline.mjs';
import {DecodedBodyBudget, readFrozenIdentityBody} from './bounded-response.mjs';
import {createResourceObserver, bindLoadDigests, auditPacketCoverage} from './resource-observer.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EVIDENCE_ROOT = path.dirname(HERE);
const digest = value => createHash('sha256').update(value).digest('hex');
const targets = new Set(['10020002:5', '10020002:15']);

// UNEXECUTED V2. No top-level browser action. A false/unknown release template
// is rejected before Page ownership transfers; its caller still owns Chrome.
export async function runDrawDiagnostic(initialPage, execution) {
  if (!execution?.rootReleased || !execution.singleBrowserOwnerAssigned || !execution.freezeComplete ||
      !execution.reviewedMultiActorExecutionAvailable || !/^http:\/\/127\.0\.0\.1:\d+$/.test(execution.baseURL || '') ||
      !Array.isArray(execution.cases) || execution.cases.length < 1 || execution.cases.length > 2)
    throw Error('No root-released consistent multi-actor execution freeze');
  for (const spec of execution.cases)
    if (!/^[a-z0-9-]{1,90}$/.test(spec.id || '') || !targets.has(spec.targetNode) ||
        spec.route?.length !== 3 || spec.route[1] !== spec.targetNode ||
        !spec.url?.startsWith(execution.baseURL + '/?') || !spec.programURL?.startsWith(execution.baseURL + '/program?') ||
        !Number.isSafeInteger(spec.programBytes) || spec.programBytes <= 0 || spec.programBytes > 16 * 1024 * 1024 ||
        !/^[a-f0-9]{64}$/.test(spec.programSha256 || '') || !spec.packetSha256)
      throw Error('Unknown actual route/program identity; no navigation authorized');
  const context = initialPage.context(), summaries = [];
  let prepared = null;
  for (let index = 0; index < execution.cases.length; index++) {
    const spec = execution.cases[index], deadline = new CaseDeadline(), bodyBudget = new DecodedBodyBudget();
    // All Page creation, observer attachment and event setup below belong to
    // this try/finally. The first owner Page must be fresh about:blank; later
    // Pages are created only after the previous owned Page closed.
    let page = index === 0 ? initialPage : null, creation = null, closing = false;
    let observer = null, trace = null, network = null, program = null, failure = null;
    let bindings = null, coverage = null, closeConfirmed = false, evidenceSaved = false;
    let output = null, creationUnsettled = false, lateCloseRequested = false;
    const errors = [], consoleErrors = [];
    const fail = error => {
      try { if (errors.length < 16) errors.push(String(error).slice(0, 700)); } catch {}
      try { deadline.fail(error); } catch {}
    };
    const onPageError = error => fail(error);
    const onConsole = message => {
      try { if (message.type() === 'error' && consoleErrors.length < 16) consoleErrors.push(message.text().slice(0, 700)); }
      catch (error) { fail(error); }
    };
    const frame = () => {
      const matches = page.frames().filter(value => {
        try { return new URL(value.url()).pathname === '/player/player.html'; } catch { return false; }
      });
      if (matches.length !== 1) throw Error('Expected one real player iframe');
      return matches[0];
    };
    const waitReady = node => deadline.work('ready:' + node, () => frame().waitForFunction(expected => {
      const summary = window.__drawDiagnostic?.summary();
      if (summary?.errors.length || document.body?.dataset.phase === 'error') throw Error('Diagnostic/player failure');
      return document.body?.dataset.node === expected && document.body.dataset.phase === 'ready';
    }, node, {timeout: Math.max(1, deadline.remaining())}));
    try {
      if (!prepared) {
        if (context.pages().length !== 1 || initialPage.url() !== 'about:blank') throw Error('Owner must provide one fresh blank Page');
        const instrumentText = await deadline.work('read prepared instrument', () => readFile(path.join(HERE, 'instrument.js'), 'utf8'));
        if (digest(instrumentText) !== execution.instrumentSha256) throw Error('Prepared instrument hash differs');
        const lockPath = path.resolve(execution.resourceLockPath || '');
        if (!lockPath.startsWith(EVIDENCE_ROOT + '/') || lockPath.includes('reference-resource-lock-v1.json'))
          throw Error('Only a new explicit root execution lock is allowed; the v1 reference is stale');
        const lockText = await deadline.work('read new root execution lock', () => readFile(lockPath, 'utf8'));
        if (digest(lockText) !== execution.resourceLockSha256) throw Error('Root execution lock hash differs');
        const lock = JSON.parse(lockText);
        if (lock.status !== 'root_frozen_execution' || !lock.rootFreezeId) throw Error('Reference bytes are not a current execution freeze');
        if (!Array.isArray(lock.resources) || new Set(lock.resources.map(value => value.pathname)).size !== lock.resources.length ||
            lock.resources.some(value => value.pathname === '/program'))
          throw Error('Execution resources need unique paths; program identity belongs to its case');
        for (const name of ['deadline.mjs', 'bounded-response.mjs', 'resource-observer.mjs', 'run-diagnostic.mjs']) {
          const body = await deadline.work('read prepared helper:' + name, () => readFile(path.join(HERE, name)));
          if (digest(body) !== execution.helperSha256?.[name]) throw Error('Prepared helper hash differs: ' + name);
        }
        output = path.resolve(execution.outputRoot || '');
        if (!output.startsWith(HERE + '/runs/')) throw Error('Output is not a new v2 evidence run');
        try { await deadline.work('check new output', () => stat(output)); throw Error('Existing run must remain immutable'); }
        catch (error) { if (error.code !== 'ENOENT') throw error; }
        await deadline.work('create new output', () => mkdir(output, {recursive: true}));
        prepared = {instrumentText, lock, output};
      } else {
        if (context.pages().length !== 0) throw Error('Previous owned Page remains');
        page = await deadline.work('create case Page', () => {
          creationUnsettled = true;
          creation = context.newPage();
          creation.then(value => {
            creationUnsettled = false;
            // A timed-out create is not cancellable through Playwright's API.
            // If it later resolves, request closure without extending the host
            // case await. Root must still close Chrome/CLI and verify OS zero.
            if (closing) {
              lateCloseRequested = true;
              try { value.close({runBeforeUnload: false}).catch(() => {}); } catch {}
            } else page = value;
          }, () => { creationUnsettled = false; });
          return creation;
        });
      }
      output = prepared.output;
      observer = createResourceObserver({baseURL: execution.baseURL, lock: prepared.lock, deadline, budget: bodyBudget});
      observer.attach(page);
      page.on('pageerror', onPageError); page.on('console', onConsole);
      await deadline.work('install init observer', () => page.addInitScript({content: '(' + prepared.instrumentText + ')(' +
        JSON.stringify({id: spec.id, targetNodes: [spec.targetNode], traceByteBudget: 20 * 1024 * 1024,
          maxRenderFramesPerNode: 240, maxDurationMs: 45000}) + ');'}));
      const responsePromise = page.waitForResponse(value => value.url() === spec.programURL,
        {timeout: Math.max(1, deadline.remaining())});
      responsePromise.catch(() => {});
      await deadline.work('navigate frozen private preview', () => page.goto(spec.url,
        {waitUntil: 'domcontentloaded', timeout: Math.max(1, deadline.remaining())}));
      const response = await deadline.work('await frozen program response', () => responsePromise);
      const result = await readFrozenIdentityBody(response, {expected: {url: spec.programURL,
        bytes: spec.programBytes, sha256: spec.programSha256}, deadline, budget: bodyBudget,
        label: 'frozen program', maxBodyBytes: 16 * 1024 * 1024});
      program = await deadline.work('parse frozen program', () => JSON.parse(result.body.toString('utf8')));
      if (program.review_only_overrides?.packetSha256 !== spec.packetSha256) throw Error('Private packet identity differs');
      const target = program.nodes.find(value => value.id === spec.targetNode);
      if (JSON.stringify(target?.actors?.map(value => value.model).sort()) !== JSON.stringify(['chin01', 'kan01', 'ton01']))
        throw Error('Frozen program does not provide the reviewed actual three-model target');
      await waitReady(spec.route[0]);
      await deadline.work('bind already loaded clock and arm logger', () => frame().evaluate(async () => {
        const {visualFrameClock} = await import('/studio/visual_frame_clock.js');
        const qa = window.__drawDiagnostic;
        if (!qa?.summary().installed) throw Error('Observer missed the actual factory');
        qa.bindClock(visualFrameClock); qa.arm();
      }));
      await deadline.work('natural advance to target', () => page.locator('#advance').click({timeout: Math.max(1, deadline.remaining())}));
      await waitReady(spec.targetNode);
      await deadline.work('await bounded target observations', () => frame().waitForFunction(expected => {
        const summary = window.__drawDiagnostic.summary();
        if (summary.errors.length) throw Error(summary.errors.join('; '));
        return summary.milestones[expected]?.readySamples.length === 4;
      }, spec.targetNode, {timeout: Math.max(1, deadline.remaining())}));
      await deadline.work('natural advance to successor', () => page.locator('#advance').click({timeout: Math.max(1, deadline.remaining())}));
      await waitReady(spec.route[2]);
    } catch (error) { failure = {message: String(error).slice(0, 1500)}; }
    finally {
      closing = true; deadline.beginCleanup();
      // Detach first, then bounded export/drain, then attempt Page closure with
      // its reserved time. Never let a diagnostic/export error skip closure.
      try { observer?.detach(); } catch (error) { fail(error); }
      if (page) {
        try {
          trace = await deadline.cleanup('export and restore iframe observer', () => frame().evaluate(() =>
            window.__drawDiagnostic?.finish('owner_finally') || null), {reserveMs: 5000, maxMs: 2500});
        } catch (error) { failure ??= {message: 'Observer export/cleanup unconfirmed: ' + error}; }
      }
      try { if (observer) network = await observer.finish(); }
      catch (error) { failure ??= {message: 'Network observer drain unconfirmed: ' + error}; }
      if (page) {
        try { page.off('pageerror', onPageError); page.off('console', onConsole); } catch (error) { fail(error); }
        try {
          if (!page.isClosed()) await deadline.cleanup('close owned case Page', () => page.close({runBeforeUnload: false}),
            {reserveMs: 1500, maxMs: 4000});
          closeConfirmed = page.isClosed();
        } catch (error) { failure ??= {message: 'Owned Page close unconfirmed; owner Chrome close required: ' + error}; }
      } else closeConfirmed = !creationUnsettled;
      try {
        if (trace && prepared && network) {
          bindings = bindLoadDigests(trace, network, prepared.lock, execution.baseURL);
          coverage = auditPacketCoverage(trace, prepared.lock, execution.baseURL, spec.targetNode);
          if (coverage.failures.length || bindings.targetBindingFailures.length || trace.errors.length ||
              trace.runtimeFailures?.length || !trace.cleaned || trace.cleanupConflicts.length)
            failure ??= {message: 'Partial observation/identity/original-call/cleanup failure'};
          for (const source of prepared.lock.resources.filter(value => value.kind === 'source'))
            if (!network.records.some(value => new URL(value.url).pathname === source.pathname && value.matchesFrozen))
              failure ??= {message: 'Required actual source response hash missing: ' + source.pathname};
        } else failure ??= {message: 'Incomplete draw/network packet'};
        if (!closeConfirmed || errors.length || consoleErrors.length || network?.errors.length || network?.pending || bodyBudget.failures.length)
          failure ??= {message: 'Runtime/network/deadline/decoded-budget/cleanup errors retained'};
        const payload = {status: failure ? 'partial_failed_not_acceptance' : 'captured_requires_offline_audit_not_acceptance',
          id: spec.id, failure, trace, network, loadResourceBindings: bindings, observationCoverage: coverage,
          errors, consoleErrors, bodyBudget: bodyBudget.snapshot(), deadline: deadline.snapshot(), closeConfirmed,
          creationUnsettled, lateCloseRequested, actualRouteNodes: program?.nodes.filter(value => spec.route.includes(value.id)),
          accepted: false, actualNativeUnityCapture: false};
        if (output) await deadline.cleanup('save bounded packet', async () => {
          const raw = Buffer.from(JSON.stringify(payload));
          if (raw.length > 24 * 1024 * 1024) throw Error('Final packet byte budget exceeded');
          await writeFile(path.join(output, spec.id + '.json.gz'), gzipSync(raw, {level: 1}), {flag: 'wx', signal: deadline.signal});
          evidenceSaved = true;
        }, {maxMs: 1500});
      } catch (error) { failure ??= {message: 'Bounded export/save failed: ' + error}; }
      // This small returned receipt is retained even if disk export timed out.
      // It never includes arrays/pixels and never claims an unconfirmed close.
      summaries.push({id: spec.id, failure, closeConfirmed, creationUnsettled, lateCloseRequested,
        evidenceSaved, deadline: deadline.snapshot(), accepted: false});
      deadline.dispose();
    }
    if (failure || !closeConfirmed) break;
  }
  return {cases: summaries, browserPagesRemaining: context.pages().length,
    needsImmediateOwnerChromeAndCliCloseAndOSVerification: true, accepted: false};
}
