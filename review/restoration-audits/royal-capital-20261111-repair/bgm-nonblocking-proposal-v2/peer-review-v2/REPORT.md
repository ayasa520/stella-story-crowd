# Independent v2 delta review

Reviewer: `/root/bgm_async_proposal_peer`. Scope: static v1→v2 delta only; no runtime activation approved.

**v2 resolves the conditional observer exception-safety gap identified in peer-review-v1. No new unconditional static blocker was found in this delta.** This is a control-flow conclusion, not an observed fault-injection or browser result. The default logger/clock failure discussed in v1 remains unobserved.

Evidence refers to `native-bgm-loading-prototype-20261112/v2/proposal/public/player/player.js`:

- Both apply settlement handlers are attached at lines 203–217, followed by the terminal observer at 220–223. State publication and the first diagnostic sample occur only afterward, at 227–228. A failing new SUBMITTED sample cannot prevent attachment of the apply rejection observer.
- `safeReport` encloses sampling, JSON serialization, host logger lookup/output and fallback output (183–189). Its fallback has its own catch. This covers failures of `observation()`, `describeError()` and either logger when invoked through this helper.
- On apply rejection, FAILED reporting is isolated at 210–211. Error delivery is outside `safeReport`, and ownership is freshly checked after reporting at 216. A diagnostic exception alone therefore cannot skip the call to existing `fail()` for the current entry/current music request.
- The terminal observer at 220–223 only calls the guarded reporter and returns no rejecting work. The v1 terminal diagnostic rejection escape is closed within this new helper boundary.
- The current `MusicPlayer.apply()` and existing `StoryPlayer.fail()` have their own unchanged internal logging. v2 PLAN lines 29–41 and 152–156 correctly limit the new no-throw argument to observer diagnostics. This does not claim those existing internals are logger-fault-proof, and this review does not expand into changing them.

Independent byte/hash checks: the five supplied v2 artifact hashes match; candidate SHA-256 is `c25e7a73be61c25dc897a13eed8d581b4021dd4f3bb7f818e95c53a1689030f6`. All 15 frozen v1 files match their preserved-file receipt. Candidate bytes outside `submitNodeMusic()` are identical to v1. Both awaited restoration/phase method slices remain identical to the canonical source. All four canonical source hashes and four native plus four review guards match. Canonical remains clean at `37232806a8180375a4b7a178e27157bb16d12201`.

v2 PLAN lines 113–126 correctly describe the selected historical smoke routes in episodes 1/2/3, preserve the user's completed manual acceptance, distinguish original19 protection, and retain the same-resource pending assignment observation for episode 2. No manual acceptance is reopened.

Remaining QA and policy boundaries are unchanged: desired resource is published before proven audibility; a still-current request failing after an inherited successor logs for its original owner without stopping/retrying that successor. v2 PLAN lines 142–150 explicitly leaves that policy pending. Real pending Stop/replacement/return-to-current, inherited continuation, active/late/superseded errors, phase StopBGM overlap, source/gain continuity and unhandled-rejection observations remain required or explicitly uncovered. Diagnostic-fault execution would be a separately scoped mechanical check, not original timing evidence.

The matched native Director BG/Init completion evidence still does not prove concurrent global-latch association, the recording producer path, universal BGM/CardIn/text ordering or exact timing. No native field, phase, Wait, fade, restart or cue-zero is accepted here.

Only this new `peer-review-v2` directory was written. No Chrome, images, injection, unit tests, source/data/website/registry or Git mutation was used. Available affinity includes CPUs 22/23; Python verification used nice 19 and CPUs 22/23.
