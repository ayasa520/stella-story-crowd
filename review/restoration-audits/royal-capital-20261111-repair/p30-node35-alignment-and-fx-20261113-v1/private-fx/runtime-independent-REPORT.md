# Private FX first draw: independent runtime evidence review

**The bounded attribution/forwarding/cleanup diagnostic passes. Original visual order and phase1/XYZ0 remain unaccepted.** This review reads only retained result, source and scheduling files; it performs no browser action, live process query, network request, capture, decoding, image review, formal edit or Git action.

Input runtime is `../p30-node35-alignment-and-fx-runtime-20261113-v1/`. The private result has one program/manifest/texture request, the reviewed1authored/2compiled command projection, restored whole-program/manifest comparisons and no persistence. The reviewed observer-v2 imports the actual `/player/` classes and returns original results/Promises/throws unchanged. The source uses `performance.now()` for record/call brackets, a separate RAF argument for FX simulation, and the shared capped Normal clock only as a snapshot. Host `Date.wall` delivery and original-video time are not mixed into the intervals below.

## Same-page performance evidence

All values here share observer time origin1794522023766.9. They are CPU method/observation boundaries, not presented pixel timestamps.

| Boundary | Page performance, ms |
|---|---:|
| Stored instance simulation origin |11230.39999999106 |
| Existing START observed after instance insertion |11231.0 |
| Panel entry START observed, inline alpha0 |11232.29999999702 |
| Existing `text_begin` event before private assignment |11232.70000000298 |
| First FX tick: observer before original |11236.70000000298 |
| Second FX tick: observer before original |11471.70000000298 |
| First nonempty Yellow renderer call |11477.79999999702→11478.5 |
| First positive text threshold draw |11478.5→11478.70000000298 |
| Panel entry COMPLETE observed |11723.79999999702 |

Existing activation→Yellow renderer enter/return is246.8–247.5ms; stored instance origin→those boundaries is247.4–248.1ms. The Yellow method bracket lasts0.7ms. Its return and text method entry share11478.5ms at recorded resolution: no positive presented lead duration is established. Text's method bracket lasts0.2ms. The private text-clock assignment remains unknown, bounded by its preassignment event and first positive draw:11232.7–11478.5ms, a245.8ms bracket. This is not a recovered Wait.

There is **one** text-threshold record, with `visible:3`, `reached:[1,2,3]`, Chinese prefix`——啊`, group`adv_tell_illiustration`, inline opacity`0.999999` and translate`0px -6.17604e-07%`. These are coalesced thresholds in one draw, **not three visible frames or separate “—”, “——”, “——啊” submissions**. The record does not timestamp every earlier OriginalScene draw; preparation's visible0 draw is deliberately outside this positive-threshold observation. Panel COMPLETE later clears its inline styles; that is not a computed/pixel alpha observation.

RAF arguments for the first three FX ticks are11233.9,11383.9,11717.3ms, giving elapsed simulation0.0035,0.1535,0.4869s from stored instance origin. Actual callback-entry performance values differ and must not be substituted for those RAF arguments. At tick2, Yellow's first retained geometry has6vertices, max vertex alpha0.8930000029623515, earliest live birth0.10000000149011612s; its layer changes hidden→visible during the original renderer method. The array is attributed to instance1/seed3020188311, matching START. The Normal snapshot changes9.199666686534874→9.366266686534875s (166.6game ms) between activation and this draw, and is identical for Yellow/text at frame375. That is a separate game-clock observation, not the247.5performance-ms interval.

## Why the previous visual rejection remains

The earlier retained source review reports yellow→bars→あ, while the855-frame candidate review reported bars→yellow→啊. Existing code can activate an FX before text yet leave its layer hidden until a later nonempty tick. This run confirms the distinction between activation, delayed particle birth and actual CPU draw. Its tested Yellow delay remains0.1s, and text/panel entry still run without awaiting Yellow output. These are tested candidate/source-code properties, not newly recovered native invocation parameters.

This run instead coalesces the first three text thresholds near the first nonempty Yellow method call. It does not reproduce three separate prefix frames and contains no pixel/GL-call/GPU-presentation proof, so it cannot overturn the earlier visual rejection, prove source order or justify phase/XYZ/Wait/seed/particle-delay changes. Scheduling differences, cause of callback gaps and timing consistency across runs remain unassigned.

## Attribution, forwarding and cleanup

Fourteen records contain one attributed target instance and no attribution-gap/error/drop. The six hook counters are entries/originalCalls: play1/1, console67/67, FXtick65/65, geometry192/192, renderer128/128, OriginalScene.draw53/53; all originalThrows are0. These counters cover the installed observation window, not only node27. They agree with the single-forwarding source.

The FX expires normally. Before28 the observer restores all six descriptors, removes timing/pagehide listeners and its owned slot, with no snapshot error/conflict. The retained handle is disposed, all three routes and both host listeners are removed. At28ready and its tail, picture is hidden,046c restored and FX instances/layers both0. Runner reports all steps0, browserClosedtrue; closure reports browser/CLI/FFmpeg/adapter exited and`matches:[]`.

## Saved scheduling checks

| Saved checkpoint | Chrome/crashpad processes | Thread observations | Actual nice / affinity violations |
|---|---:|---:|---|
| after-open |11 |122 |0; all19 /[0,1] |
| after-alignment |12 |139 |0; all19 /[0,1] |
| after-private-fx |12 |139 |0; all19 /[0,1] |

`inherited-priority-bound.json` records RLIMIT_NICE40/40→1/1, runner nice19 and CPUs0/1. The saved runner source sets both limits before its first CLI subprocess, with no system configuration change. Its snapshot code enumerates all threads in the recorded current-user Chrome/crashpad processes. These are three actual point-in-time checks, not a continuous scheduling trace. This review performs no new process lookup or priority action.

Exact private textBegan, exact GL draw-call time, GPU completion/presentation, original invocation phase/offset and image fidelity remain unknown/unaccepted. Root review/confirmation remain separate.
