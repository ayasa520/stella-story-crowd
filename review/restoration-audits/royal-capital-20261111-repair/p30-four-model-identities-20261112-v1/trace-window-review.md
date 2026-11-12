# P30 formal QA trace: CardIn gap is outside the captured window

Offline analysis only, using nice19/CPU0,1 and standard-library gzip/JSON reads. No browser/replay, new capture, production edit or image review. The14 saved character fields and22-node formal QA remain separate from this diagnostic.

**Conclusion:** the gzip stream was collected successfully, but its six-second watchdog stopped recording immediately before node5 CardIn. It does not contain the observed2.5498s CardIn RAF gap, so that gap's cause remains unlocalized. Do not infer it from the trace prefix or change a player Wait/curve.

## Exact alignment and coverage

Input: `p30-four-model-identities-publication-20261112-v1/entry-trace.json.gz`, its `trace-meta.json`, and `.playwright-cli/console-2026-11-12T10-52-49-220Z.log`.

The trace's `p30-entry:trace-begin` user-timing mark has trace timestamp48008327801µs and browser startTime9242.2ms. Its offset is therefore47999085601µs: `browser_ms = (trace_us − 47999085601) / 1000`. This uses the in-trace mark and browser timing, not host Date.now or CLI-prefix clock subtraction. Displayed values are rounded to the available precision.

| Boundary | Browser performance-clock ms |
| --- | ---: |
| First positive trace-event timestamp | 9110.661 |
| Begin marker | 9242.200 |
| Last recorded trace-event timestamp/end | 15297.182 |
| Node5 motion commit / motion-ready boundary | 15301.000 |
| Card wait starts | 15308.100 |
| CardIn starts | 15316.200 |
| RAF immediately before the large gap | 15359.500 |
| Next RAF / FRAME_HITCH523, raw delta2549.8ms | 17909.300 |
| CardIn completes | 18064.000 |
| Formal ready observation | 19690.400 |

The trace ends approximately19.018ms before CardIn and62.318ms before the gap begins. Console lines123–127 bind the CardIn/gap/completion clocks. The gap's beginning is calculated directly from the logged next RAF timestamp17909.3 minus raw delta2549.8. Trace-tail open begin events belong to tracing producer/IO threads; they do not extend coverage into the later CardIn interval.

The valid stream has eof true, no reported data loss and no collector errors. Its incomplete status accurately records `stopReason:"time-limit"`, not stream failure. End acknowledgement→completion is1.835s in this run, with one named and one generic completion event. This does not retrospectively explain the earlier v1 five-second timeout; that diagnosis remains distinct.

## Measured prefix observations, not the missing-gap cause

The trace identifies renderer main2623/2623, renderer compositor2623/2644, GPU main2554/2554 and Viz compositor2554/2581. Examples from the captured preparation interval:

| Thread / measured span | Browser start–end ms | Observation |
| --- | --- | --- |
| Renderer main task → BeginMainFrame | 9850.951–9915.866 | 64.915ms task. |
| Its LayerTreeHost::DoUpdateLayers → GLES2::ReadPixels | 9853.191–9911.154 / 9853.217–9910.758 | Update/readback consumes most of that task. |
| Its CommandBufferProxyImpl::WaitForGetOffset | 9853.236–9910.585 | 57.349ms wait, command offset12789. |
| GPU service scheduler → WebGL/CommandBufferStub::OnAsyncFlush | 9853.271–9910.388 | 57.117ms service task; flush put_offset12789 matches the renderer wait. This supports a synchronous command-buffer wait in this prefix, not a hardware GPU-duration claim. |
| Nearby Viz Display::DrawAndSwap | 9842.613–9851.075 | 8.462ms recorded draw/swap slice. Its overlap alone does not prove a dependency. |
| Renderer PIXI `_tick` FunctionCall | 11745.763–11807.635 | 61.872ms, including WaitForAvailableEntries11748.561–11807.311 and WaitForGetOffset11748.562–11807.308. |

These are real measured costs while the next model/animation was being prepared. They establish neither a2.55s task nor the cause of an interval recorded after the trace stopped. No kernel scheduling or hardware GPU execution trace was collected.

## Same-run lifecycle timestamps for a future necessary QA trigger

Some original console messages do not log performance.now. Keep their actual retained CLI-prefix times separate instead of inventing a browser-clock value:

| Event | Console line / retained prefix ms | Embedded browser-clock value |
| --- | --- | --- |
| MODEL_READY felt01, visible=false | 104 /13680 | Not logged by that message. |
| Motion commit, followed by motion_ready | 110–111 /15809 | Commit15301.000; motion_ready logs5458ms rounded since node entry. |
| DISPLAY_COMMIT actor felt01 | 120 /15816 | No own timestamp; immediately followed by card_wait_start15308.100. |
| CardIn start | 123–124 /15824 | 15316.200 start;15316.300 clock diagnostic. |

In the retained prefix clock, MODEL_READY→motion_ready is2129ms, motion_ready→DISPLAY_COMMIT7ms, and DISPLAY_COMMIT→CardIn8ms. These are message-observation intervals, not recovered native phase timings. The embedded browser clock independently places motion commit only15.2ms before CardIn; arming a host CDP start that late could miss the start again. MODEL_READY supplies an earlier lifecycle point with approximately2.14s of observed lead in this run. If root later changes the collector during another already-required QA, that matching model-ready boundary is more useful to examine than extending a node4-ready timeout blindly. Any such derivative must record its actual start acknowledgement/coverage; no replay or player change is requested by this report.
