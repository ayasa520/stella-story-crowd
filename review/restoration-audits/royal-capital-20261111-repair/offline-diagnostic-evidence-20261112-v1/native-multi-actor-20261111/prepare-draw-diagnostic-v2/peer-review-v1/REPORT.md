# Independent v2 delta review — static only

Reviewer: `/root/bgm_async_proposal_peer`. Input author receipt SHA-256: `57f45cf45cc8bffc5b8c1feff1692c39703e28b0f1db8607825de05191a92c89`.

**B1–B4 are resolved at the static control-flow level within v2's stated bounds. No remaining tool implementation blocker was found in this review.** This does not release an execution: current source lacks the required P09 native-parent path, the reference lock remains stale, and a new root-reviewed execution/source/data/program/resource/helper freeze and sole browser owner are still prerequisites. Authorized ongoing resource/data publication is not classified as a tool failure.

All file/line references below are relative to `prepare-draw-diagnostic-v2` unless stated otherwise.

## B1: absolute host deadlines and failure cleanup

`deadline.mjs:8–20,30–54` establishes one monotonic start+35s work endpoint and start+45s cleanup endpoint per case. Each work operation checks the same endpoint before scheduling and again before starting; its await races a timeout and the fatal promise, then rejects a completion that arrives beyond that endpoint. Cleanup uses the same hard endpoint with reserves rather than adding fresh unrestricted durations. This is an asynchronous-await bound; synchronous JS, OS scheduling and underlying browser cancellation are expressly outside the guarantee.

The real previous gap is closed: the program response, headers, body and SHA use this deadline (`run-diagnostic.mjs:112–121`; `bounded-response.mjs:50,62,75`). Artifact reads, output preparation, Page creation, init setup, navigation, actions and waits also use `deadline.work`. The owned Page's observer/listener setup is now inside the case try/finally (`run-diagnostic:62–143`); first-Page validation occurs before navigation and any error still enters that Page's cleanup.

Finally marks work ended, detaches observation, attempts iframe export/restore with a 5s reserve and 2.5s cap, drains network work with a 4s reserve and 1s cap, attempts Page close with a 1.5s reserve and 4s cap, then attempts bounded save (`run-diagnostic:143–193`; `resource-observer.mjs:62–67`). Close/export/drain failure stays explicit and does not bypass the later close attempt. File save receives the hard-deadline AbortSignal; if writing fails or times out, a small returned failure receipt remains. The file may itself be absent or incomplete, so returned `evidenceSaved` and failure metadata must be retained.

Late `newPage()` settlement is handled separately (`run-diagnostic:89–103,163,191–198`): its original creation promise is tracked; expiry does not claim cancellation. A later fulfillment requests closure when `closing` is true, while the returned receipt preserves the earlier `creationUnsettled`/`lateCloseRequested`/`closeConfirmed` observations. No next case begins on failure/unconfirmed close. These flags and pending-command labels are evidence of uncertainty, not proof of browser closure. The root owner must still immediately close Chrome/CLI and verify OS processes, including after a timed-out create or close. v2 documents this limitation accurately.

## B2: strict body admission and reservation lifetime

`bounded-response.mjs:48–59` validates a positive frozen exact size/SHA and cap; actual GET/200 URL; confirmed non-Service-Worker provenance; absent/identity Content-Encoding; absent Transfer-Encoding and Content-Range; and exact decimal Content-Length equal to the frozen decoded size. Only then does it reserve the size in the shared 32 MiB ledger and invoke `response.body()` (`59–73`). Resource cap is 8 MiB; the program cap is 16 MiB; both use the same case ledger. Unknown watched bodies are refused (`resource-observer:31–38`).

The side handlers at `bounded-response:68–71` follow the original body promise, not just the host await. A timed-out host await keeps its reservation until that actual read settles; rejection releases it, successful settlement counts actual decoded bytes, and mismatched actual size invalidates the read before SHA acceptance (`19–33,74–76`). An operation that never started releases its unused reservation in `finally` (`80–82`). The side handlers do not produce an unhandled rejection in the inspected native Promise path.

This closes the compressed-body admission gap from v1. It is a strict identity-HTTP profile, not a general compressed/chunked decoder, a streaming implementation, or an upstream browser/network/GPU memory limiter. `Content-Range` is the checked response range field; a mismatched size/body is refused rather than relabelled. Future root freeze must include all predecessor/successor bodies that the observer is allowed to read.

## B3/B4: exact original result, no-throw diagnostics, same-error failure propagation

`instrument.js:318–333` now invokes the factory through `actual()` once, registers side observation with the captured intrinsic `Promise.prototype.then`, and returns the exact original result. The actual SDK's factory returns a native Promise. Its fulfillment side handler only enters no-throw `diagnostic`; its rejection side handler only enters guarded failure recording. Both return undefined to the discarded side chain, while original Promise identity and rejection value remain the caller's. No extra awaited/assimilation result replaces it. This resolves B3; finite observer execution cost remains.

`diagnostic()` catches all wrapped sampling work (`instrument:105–108`); `failNoThrow()` records partial state/runtime failures and requests independently guarded cleanup (`78–103`). `actual()` makes one original Reflect.apply, records original-call failure through the no-throw path, then throws the same original object (`109–115`). It neither retries nor replaces the call/result/error.

Core pre/post timing/append work is inside diagnostics (`221–240`), as are drawModel/mesh pre/post work (`245–312`), factory samples, render frame/stack/export observations (`337–359`), timing and lifecycle callbacks. Thus a sample/append failure can invalidate capture while leaving the one original SDK invocation and its result/exception intact. Actual failure is recorded globally in `runtimeFailures` even when an application caller catches it outside a geometry milestone; owner validation checks that field (`run-diagnostic:168–170`). Cleanup attempts independent restores and reports identity conflicts. Dynamic exception fault behavior was not exercised.

## Unchanged SDK and evidence boundaries

The real SDK identities and call semantics from the v1 review remain applicable: actual Core inputs precede its single update; its later loadParameters restoration is not the evaluated pose; stable native vertices/indices are matched by object identity; draw submission follows actual drawing matrix/MVP setup; mask vertices use mask matrix, color vertices use MVP, and mask UVs use the clip matrix. Input generation, app render, modelDraw and mesh identities remain distinct. Same-frame linkage does not prove a default pose or missing original CSV. PIXI matrices are not Unity localToWorld. Raw opacity/base model color and CPU matrices are not post-GPU uniforms/pixel alpha; mask channel/layout uniforms remain outside this packet.

URL/body-SHA/load/instance association remains content evidence from actual existing responses, without an extra fetch or a fabricated unique request/GPU digest per shared texture. Four ready geometry milestones are observation coverage, not original geometry agreement, complete motion acceptance or a full entry sequence.

## Independent checks and execution boundary

All nine v2 inventoried files match the author receipt. Both v1 peer files, v1 final handoff and all 13 inventoried v1 author files remain byte-identical. The v2 reference lock equals the original v1 lock, all 22 referenced source/resource bytes still match, and all 13 SDK source snippets still match their recorded original byte offsets. Five independent `node --check` commands exited 0 for instrument, deadline, bounded-response, resource-observer and runner. These are parsing/static checks, not application or unit tests.

Direct source inspection still finds no `lib/native-actors.ts` and no `native_parent` branch in canonical player placement. The v2 runner explicitly refuses the old reference lock and requires `root_frozen_execution` plus a root freeze ID, matching helper/instrument/program/private-packet identities and release flags. Those authorization inputs do not manufacture the missing runtime implementation. No active data HEAD was read or polled; no lock was refreshed to follow authorized publication.

Only this new `peer-review-v1` directory was written. Review computation used nice 19 on CPUs 22/23. No Chrome, images, application execution, runtime injection, unit/fault test, author/production/source/data/registry/Git change or refreeze occurred. Runtime transparency, real deadlines, HTTP handling, cap sufficiency, cleanup and actual draw packets remain unobserved.
