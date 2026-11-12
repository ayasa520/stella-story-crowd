# P30 private act_punpun: transition timing review

Read-only review of `.playwright-cli/console-2026-11-12T08-51-42-370Z.log` and the existing renderer, transition and background paths. No player, browser, compiler or server was run for this review. This report does not accept the motion visually.

The new logs prove an unmeasured interval between short renderer calls, not a 483 ms first `PIXI.Renderer.render` call. Use the embedded `performance.now()` / RAF values below; the CLI log prefix is a different observation clock.

| Console lines | Observation in player monotonic milliseconds |
| --- | --- |
| 79–82 | Render 1 starts 10422.8, lasts 42.7 ms, and observes card opacity 0. CardIn starts later, at 10468.0. |
| 83–88 | Renders 2 and 3 last 2.0 ms each. Render 4 spans 10492.2–10494.1, with computed card opacity 0.00347141. |
| 89 | RAF frame 327 has timestamp 10971.9 and raw delta 483.3 ms. The shared clock admits the existing native maximum of 333.333 ms. |
| 90–95 | Render 5 starts 10979.8 and lasts 9.4 ms, observing opacity 0.813604. Subsequent observed values are 0.921012 and 0.996473. |
| 96–104 | CardIn completes at 11218.1; the next measured renderer call lasts 1.6 ms, with opacity 1. |

The actor children remain visible, alpha 1 and worldAlpha 1 in all eight measured renders. That is compatible with fading the containing DOM card. `public/studio/transitions.js:22–40,77–81` samples the native opacity curve only when the shared RAF clock advances; the measured large step explains the missing opacity samples. It does not identify what consumed the interval between those samples.

There are two measurement limits. `capture-p30.js:38–43` stops its render duration before `getComputedStyle`, JSON construction and logging in `finally`. Its opacity observer records `wall` before its own `getComputedStyle` call (`:25–26`). Thus “render 4 ended at 10494.1” measures the original render call, not completion of every callback, microtask, browser paint or GPU operation. A returned WebGL render call also does not establish completed GPU work or a displayed frame. The earlier baseline, before these additional observers, already recorded a 466.6 ms RAF interval; the evidence does not support assigning the symptom to the new observer either.

Relevant boundaries remain small: `public/player/background.js:21–26` returns immediately for the unchanged background, while `:53–57` installs the backdrop image's CSS blur. That CSS filter and DOM card opacity are browser composition work outside the measured PIXI call. `public/player/actor_lighting.js:57–75,117–139` performs shader/uniform/texture setup during actual drawable rendering; the measured renderer duration includes synchronous calls there, but not proof of GPU completion. These are boundaries for investigation, not identified culprits. Do not add Wait, change the native curve, remove blur or add a preparation render from this evidence alone.

## Smallest useful next observation

During the next necessary continuous replay, attach one bounded `PerformanceObserver` before ordinary Continue. Prefer `long-animation-frame`; fall back to `longtask`. Keep entries in memory, then serialize once after node5 is ready and the normal observation period has allowed observer delivery. The snippet below records only entries intersecting node5 entry through CardIn completion. It makes no per-frame style reads or console calls and changes no renderer, pose, opacity, clock or command. Existing render wrappers, if retained, should place a cheap `performance.mark(...)` after all diagnostic work for the last pre-gap render/opacity callback; that closes their currently unmeasured tails without another style read.

```js
// Run once in the player iframe before the ordinary node4 -> node5 Continue.
// Return finish()'s result once after node5 is ready; do not log every entry.
(() => {
  const PO = globalThis.PerformanceObserver;
  const types = PO?.supportedEntryTypes || [];
  const type = types.includes('long-animation-frame') ? 'long-animation-frame'
    : types.includes('longtask') ? 'longtask' : null;
  if (!type) return {supported: false, supportedEntryTypes: [...types]};

  const entries = [], limit = 32;
  let start = null, end = null, dropped = 0, finished = null;
  const keep = rows => {
    for (const row of rows) {
      if (start === null || row.startTime + row.duration < start ||
          (end !== null && row.startTime > end)) continue;
      if (entries.length < limit) entries.push(row); else dropped++;
    }
  };
  const observer = new PO(list => keep(list.getEntries()));
  const timing = event => {
    const d = event.detail;
    if (d?.node !== '10450054:5') return;
    if (d.stage === 'enter' && start === null) start = performance.now();
    if (d.stage === 'card_change_complete' && end === null) end = performance.now();
  };
  document.addEventListener('stella-player-timing', timing);
  observer.observe({type, buffered: false});
  globalThis.p30TransitionTiming = {
    finish() {
      if (finished) return finished;
      keep(observer.takeRecords());
      observer.disconnect();
      document.removeEventListener('stella-player-timing', timing);
      const completed = end !== null;
      if (end === null) end = performance.now();
      finished = {type, start, end, completed, dropped, entries: entries
        .filter(e => e.startTime <= end && e.startTime + e.duration >= start)
        .map(e => ({startTime: e.startTime, duration: e.duration,
          blockingDuration: e.blockingDuration, renderStart: e.renderStart,
          styleAndLayoutStart: e.styleAndLayoutStart,
          scripts: e.scripts ? [...e.scripts].slice(0, 8).map(s => ({
            startTime: s.startTime, duration: s.duration,
            executionStart: s.executionStart, invoker: s.invoker,
            invokerType: s.invokerType, sourceURL: s.sourceURL,
            sourceFunctionName: s.sourceFunctionName,
            sourceCharPosition: s.sourceCharPosition,
            forcedStyleAndLayoutDuration: s.forcedStyleAndLayoutDuration,
            pauseDuration: s.pauseDuration})) : undefined,
          attribution: e.attribution ? [...e.attribution].map(a => ({
            name: a.name, containerType: a.containerType,
            containerName: a.containerName, containerId: a.containerId,
            containerSrc: a.containerSrc})) : undefined}))};
      return finished;
    }
  };
  return {supported: true, type, limit};
})()
```

Read the result narrowly: an overlapping script entry with duration/source attribution identifies measured main-thread work to inspect; a long rendering/style phase with little attributed script localizes a browser frame phase, not a particular filter or GPU cause. A longtask fallback supplies coarser task timing and container attribution, not a JavaScript stack. No matching entry, unsupported APIs, or a dropped record leaves the cause unresolved; it does not prove that the GPU/compositor blocked. The next change should follow that observed boundary rather than repeat input/hash audits.
