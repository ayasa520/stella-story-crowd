# Independent static review: native ordinary typing clock

## Verdict and reviewed versions

**PASS for bounded source review and the corrected actual-QA plan. No implementation blocker remains from this review. This is not runtime or production acceptance.** Root owns application, the unchanged-source baseline, the sole browser, regression and publication.

The application candidate is the sealed `../native-typewriter-normal-clock-proposal-20261113-v1/production.patch` and its three proposed JavaScript files. The applicable QA instructions are the sealed `../native-typewriter-normal-clock-proposal-20261113-v2/ACTUAL-QA-PLAN.md`; v2 is a QA-only correction and has no replacement application source. Both author receipts, READMEs and the v1-to-v2 QA diff were reviewed. Neither sealed version was edited.

The v1 author receipt names canonical baseline `34cb0adc1c3bf90b88415efb8444ca4eef5bdfec`. Independently, both selected before copies still compare equal to the actual canonical player files during this review. This receipt does not assert a later HEAD or bind a future deployment.

## Native arithmetic and order

Primary evidence remains the separately sealed `../p30-native-textpanel-typewriter-investigation-20261113-v1/REPORT.md` and its bounded native method extracts. Ordinary `TextPanel.UpdateText` at `0x1686ddc` loads stored time, calls the proven `UnityEngine.Time::get_deltaTime()` wrapper at `0x1686e58`, performs the float32 add/store at `0x1686e60/64`, multiplies by stored float speed at `0x1686e94`, uses `fcvtzs` at `0x1686e98`, and clamps against cached length. The proposed helper implements that ordinary nonnegative arithmetic with float32 speed, delta, accumulated sum and product, then truncation/clamp. It consumes the existing shared clock's already capped/scaled delta; it neither accumulates resource-loading wall time nor applies preview speed twice.

`Open` calls `PlayText`/`StartTextAnim` before `Show` starts the Animator entry. The live patch subscribes after synchronous font/text preparation and before its existing non-awaited `panelIn`. It adds no panel-entry await, fixed Wait, one-character-per-frame cap, native field, node/text selector or new speed policy. The direct Studio transport receives the same typing integration without copying unrelated live-player features.

This reproduces the proven ordinary clock operation, not all original TMP behavior. The native conditional invalid-mesh text-info retry, its exact first coroutine/engine dispatch, code-unit/rich-text handling and composited first glyph remain outside the proof. Current configured speed and existing code-point counting are retained. A legitimate delta can expose several glyphs, including three at approximately 0.15 seconds and speed25; this patch cannot promise first count1 or acceptance of the rejected FX phase1/XYZ0 candidate.

## Actual shared clock and lifecycle

The reviewed existing `public/studio/visual_frame_clock.js` samples once per document RAF and snapshots listeners before dispatch. `subscribe` does not invoke a callback immediately; membership is rechecked before each dispatch. Both proposed transports inject their actual `actor.visualClock` into the one shared helper. The helper adds no RAF, sampler, clock configuration, rate lease or disposal of another channel.

The following paths are coherent by source inspection:

- A prepared line records the current frame and consumes only subsequent increasing frame IDs. Starting before the synchronous `setPhase('text')` is safe with the actual non-immediate subscription contract; no event-loop yield is inserted between them.
- Each start first cancels its previous owned state. State identity and generation/phase checks before and after drawing reject old callbacks, including reentrant replacement. Completion invalidates and unsubscribes before entering the transport's `afterText` callback.
- Ordinary node entry, program restart and Stop cancel the owned channel. Pagehide and close use Stop. Error paths remove the active owned subscription before invoking transport failure handling.
- JA/ZH replacement during typing synchronously prepares the new text and starts fresh time/token. Ready/choice language redraws remain fully exposed and create no typing subscription. Initial empty text keeps the existing immediate `afterText` path; a language reset to empty can finish on the next frame.
- Click completion cancels before the existing command/phase2 path and synchronously changes phase, preventing another typing callback from completing the same line. Natural completion likewise removes its subscription first. Choice creation, existing follow edges, talk completion and phase2 remain with their existing owners.

The transport RAF remains responsible for the existing ready/auto margin. Its old raw-RAF typing branch and `textBegan` anchor are removed from both proposed transports. No auto-margin, audio sample clock, command Wait, FX, card, panel, title or BGM implementation/configuration is changed. Actual scheduling relative to painting and other consumers still needs the planned playback checks; source inspection is not compositor evidence.

## Coverage and resource path

This is a generic ordinary-text change across chapters, not a P30-only repair. React `components/reference-panel.tsx` and `public/studio/player_panel.js` both embed `/player/player.html`; they are two entry surfaces for the same live implementation. Retained `/studio/player.html` has its own patched transport and imports the same `/studio/native_typewriter.js` helper. The helper follows the already used static `/studio` module path and requires no catalog or asset-API change. Direct Studio has other historical feature differences; this review does not claim that those features were ported or accepted.

The separate read-only Python/Qt `story_studio/ui/player.js` is explicitly identified as retaining its previous clock. It is not falsely included in the canonical patch's coverage. Bootstrap/vendor code is neither invoked nor an additional writer.

## Corrected QA mechanism and meaningful checks

One concrete v1 QA defect was reported and resolved in the sealed v2 plan: `owner.setSpeed(0)` is not a valid clean pause diagnostic. The actual base viewer writes `audio.playbackRate` and computes `time/speed`; zero can produce a nonfinite wall anchor, and browser media-rate0 behavior was not established. V2 correctly uses the existing `clock.setRate(0, retainedActualOwner)` with independent restoration of the original actual clock rate. Owner replacement or restoration failure fails the case and closes the frame; it does not adopt a new owner or acquire a lease. The unchanged baseline is not assumed to freeze its old raw-wall typing.

Positive0.5/2 tests use the supported actual owner's `setSpeed` API. V2 explicitly declares its owned audio-element and wall-anchor effects and separately restores viewer speed and the actual original clock rate. This is not a claim about every voice/BGM channel. A single deliberately induced foreground task longer than the existing maximum delta is a supported actual scheduling diagnostic; it is not a mock clock, native performance result, identified hitch cause or authored Wait.

The first-three explicit routes in the plan match the current native edge forms already inspected for this review:

| Case | Supported bounded route / guards |
| --- | --- |
| Section1001 | `10010001:5`, choose existing branch1009 to6, then8,9,10. Preserve alternative branch1010. Node9's `未設定` source is the existing compiler-normalized empty path. |
| Section1014 | `10140002:3→4→5→6`; node6 actually continues to8, so no guessed7 is authorized. |
| Section1019 | `10190004:3→4→22→5`; node22 is empty; node5 actually continues to23, not assumed6. |

These are bounded baseline/regression samples, not a new acceptance of all branches or all three episodes. The plan also appropriately covers both actual entry implementations, JA/ZH, language reset, click completion, Stop/replay, program replacement and closure, plus current live CG and ending controls. It retains source/program guards and excludes original phase/timing/audio-listening/whole-episode claims.

`STORY_NATIVE_TEXT_CLOCK` is intentionally sparse. Its early-crossing and boundary records can independently check visible count against the logged float32 elapsed/product and show the actual capped/rate-boundary sample. Sparse start/end records alone cannot independently reconstruct every consumed nonuniform delta. If the actual driver claims a per-frame recurrence proof, it must make a bounded observation/accumulator on the **existing actual clock**; no synthetic samples, second clock or broader diagnostic framework is required. This is a limit on the strength of a future QA claim, not an implementation blocker.

## Independent checks and remaining release boundary

All three proposed JS files passed independent `/usr/bin/node --check`, each under nice19/CPU0,1, exit0. Both selected before/canonical comparisons exited0. No module body, mock/unit test, compiler, server, browser, decoder, native application, Git operation or formal/source mutation was performed. Only this new peer report and receipt were written.

Root must still capture the unchanged-source baseline, deliberately apply the reviewed patch, run the bounded actual regression/rate/cap/cancellation cases and obtain post-closure delegated image review before accepting runtime behavior. The native conditional text-info retry, exact initial dispatch/presentation and full-performance fidelity remain unproven. No player Wait, native phase, audio policy or FX placement is proposed to cover those unknowns.
