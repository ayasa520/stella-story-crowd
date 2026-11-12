# Saved32→33→34: preparation is localized; wall clocks remain separate

The longest proven browser-node intervals are **node33 card-hidden→motion-ready: 13,799ms** and **node34 card-hidden→motion-ready: 6,502ms**. They cover model/animator/motion preparation as one aggregate. The available resource/model messages do not split that aggregate into network, decode, model construction, upload, animator setup or motion selection. No underlying cause is inferred.

The reported33enter→34enter outer `logs[].wall` gap is37,812ms. It is a host console-delivery `Date.now()` interval,not a page-performance or Normal-animation duration. Existing interleaved page timestamps bound the same entry interval at21,326.6–21,328.8ms. These domains must not be substituted for one another.

## Clock provenance and the observed divergence

`capture-body.js` records `logs[].wall` in the outer console listener. `visits[].wall` and `visits[].now` are sampled together inside the player iframe as Date.now/performance.now. `STORY_PLAYER_TIMING.milliseconds` is rounded page performance elapsed from that node's private nodeBegan. Despite its name, `STORY_NORMAL_* .wallMilliseconds` is also page performance.now. Normal `gameSeconds` and `frameTimestampMs` are shared game/frame samples,not console receipt times.

| Paired ready visits,within the iframe | Page Date.now delta | Page performance.now delta |
| --- | --- | --- |
| 32→33 | 18,815ms | 18,814.7ms |
| 33→34 | 38,945ms | 13,787.8ms |

The second pair differs by25,157.2ms even without using host console delivery. The reason for the divergence is unlogged. It is not sufficient to attribute the difference to message delivery,recording,model work or a particular clock adjustment. No common video-frame origin is established by `recording-start.json` alone.

The entry-performance bounds use only source-ordered absolute page marks and rounded node-relative marks. If an absolute markA precedes elapsedM,nodeBegan≥A−(M+0.5); if it follows,nodeBegan≤A−(M−0.5). Node33's CardOutComplete before hidden8ms and CardWaitStart after phase0end13,811ms give nodeBegan[14,249.0,14,250.0]ms. Node34's motion commit before motionReady6,513ms and CardWaitStart after phase0end6,516ms give[35,576.6,35,577.8]ms. Their difference yields the21.327s bound above; it is not an exact logged enter timestamp.

## Browser node-elapsed stages

All values below come from the same node's `STORY_PLAYER_TIMING`,so no Date.wall subtraction is involved. Values are rounded milliseconds.

| Interval | Node32 | Node33 | Node34 |
| --- | ---: | ---: | ---: |
| Enter→card-change-begin | absent(no replacement) | 2 | 1 |
| Card-change-begin→hidden | absent | 6 | 10 |
| Enter/hidden→motion-ready | 583 from enter | **13,799 from hidden** | **6,502 from hidden** |
| Voice-prepare→voice-ready | 0 | 0 | 0 |
| Voice-ready→text-ready | 266 | 4 | 3 |
| Text-ready→command-resources-ready | 0 | 0 | 0 |
| Phase0 begin→end | 0 | 0 | 0 |
| Phase0end→phase1begin/card-change-complete | 779 | 687 | 1,326 |
| Phase1 begin→end | 0 | 0 | 0 |
| Phase1end→text-begin | 1 | 1 | 0 |
| Text-begin→phase2begin | 282 | 1,147 | 411 |
| Enter→phase2end | 1,912 | 15,646 | 8,253 |

The background/display/CardIn block is bounded by phase0end and phase1begin; it is not an authored wait. There is no begin/end network timing or source-side resource decode span inside the two large motion-ready aggregates.

## Card and panel intervals:page performance and Normal samples

The table uses paired `STORY_NORMAL_TRANSITION_CLOCK.wallMilliseconds` for page intervals and their paired `clock.gameSeconds` separately. Game samples can overshoot a clip boundary by a frame; these are observed completion spans,not replacement native clip lengths.

| Interval | Node32 page / game | Node33 page / game | Node34 page / game |
| --- | --- | --- | --- |
| CardWait start→CardIn start | 6.4ms /16.8ms | 34.9ms /49.9ms | 89.6ms /83.3ms |
| CardIn start→complete | 671.6ms /566.633ms | 651.8ms /516.633ms | 1,236.0ms /500.033ms |

The retained CardIn configured duration is0.5s and CardWait0.0166666675s. Logged raw-frame gaps were433.3ms(node32 entry),466.7ms(node33 entry),416.6ms(node33 post-text period) and1,066.6ms(node34 entry),each capped to333.333ms of Normal time. This proves that the Normal clock advanced by less than those raw frame gaps. It does not identify what caused the gaps.

Node33 CardOut scalar page marks span14,254.7→14,257.5=2.8ms; node34 spans35,584.1→35,587.7=3.6ms. Their corresponding game-start/end samples are not logged,so these page spans are not native duration measurements. PanelOut spans14,254.3→14,427.8=173.5ms and35,583.8→35,786.2=202.4ms. The current player launches panelOut without awaiting it,then awaits CardOut; panelOut overlaps subsequent preparation and must not be added to that aggregate.

## Outer Date.wall envelope and model messages

Within host console-delivery timestamps only,the37,812ms33enter→34enter envelope partitions as13,729ms enter→motion-ready,698ms to card-change-complete,1,297ms to phase2end,and22,088ms after that to34enter. This is a partition of receipt timestamps,not a causal runtime attribution.

| Host-delivery model markers only | Node32 | Node33 | Node34 |
| --- | ---: | ---: | ---: |
| Enter→MODEL_TEXTURE_RETAIN | 120ms | 6,781ms | 910ms |
| MODEL_TEXTURE_RETAIN→MODEL_READY | 146ms | 4,085ms | 11,998ms |
| MODEL_READY→ANIMATOR_READY | 71ms | 1,233ms | 985ms |
| ANIMATOR_READY→motion-ready | 102ms | 1,630ms | 1,289ms |

In particular,node34's11,998ms receipt gap must not be called network/decode duration when its page-clock hidden→motion-ready aggregate is6,502ms. MODEL_TEXTURE_RETAIN is a retained-resource marker,not an HTTP-request-start boundary. These messages lack their own browser performance timestamps and separate stage-start markers.

The driver requests an observer-only2,200ms hold after33ready,then clicks the viewport. It does not add a script Wait. From the paired33ready page sample30,115.2ms to the reconstructed34enter is5,461.4–5,462.6ms. Hold start/end,click send/dispatch and follow/enter do not each have paired page/host monotonic marks,so the remainder cannot be assigned to any one step. There are no in-recording screenshots and no program overrides in this saved-data run; those facts do not establish a performance cause.

## Missing boundaries

To split the proven preparation aggregate,the missing information is paired browser-performance begin/end marks for model load,model3/MOC/texture acquisition/decode,model construction/upload,animator setup and applyStoryMotion. To split the post-text interval,the missing marks are ready commitment,observer-hold start/end and click dispatch/receipt. To compare host/page Date versus monotonic time through the divergence,more paired readings at those existing boundaries are needed; the cause is not available in this log. CardOut needs paired Normal endpoints to compare its game duration. No new browser or instrumentation is run by this review.

`log-arithmetic.json` retains the exact selected values,formulas and source-log indices. Only the existing129-log result and its driver were read. No source/data/config/Git change,image review,decode,file-byte audit,CPU increase or new capture was performed. Arithmetic used nice19/CPU0,1. Motion/face/fidelity acceptance remains outside this report.
