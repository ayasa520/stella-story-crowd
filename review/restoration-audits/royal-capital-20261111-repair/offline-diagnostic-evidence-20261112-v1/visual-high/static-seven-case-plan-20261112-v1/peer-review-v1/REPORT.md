# Independent offline review — seven-case static-reference draft

Reviewer: `/root/bgm_async_proposal_peer`. Input preparation receipt SHA-256 `8e3685c971b6ecfecd2cfd8f0bce7b7afd60939083454f24ebd43f8fc846d86c`; active draft SHA-256 `6c8bb3e3ca543d6496d5e1bbc075142279653a0078fba10a85011b8adbaef093`; registry proposal SHA-256 `9704ef72e45dab0a22101a6bf43ee9840d67632ecbd80062b28534ca76376edb`.

**Execution is blocked by the route/choice implementation and bounded-failure issues below.** Scope partitioning, draft authorization boundaries and the distinction between actor bytes and asynchronous whole-stage images are sound. No Chrome, application, compilation, image inspection, runtime injection, unit test or refreeze was performed.

References without a source prefix are files in this package. `S` means the canonical checkout `/home/rikka/Projects/stella/artifacts/stella-site-repair-source/.sites-checkout`; `R` means the restoration repair directory containing `playback` and `visual-high`.

## Required corrections before execution

### S1 — The runner cannot traverse/capture the authorized choice nodes

`capture_cases.js:69–72` waits only for `phase === 'ready'`; target capture additionally requires ready in `instrument.js:100`, and the route-render gate again requires ready (`capture_cases:155–156`). Yet the actual canonical player ends choice nodes in `choice`, not ready (`S/public/player/player.js:493–516`). `ChoiceInput.open()` clears selection, and `confirm()` does nothing until an available side is selected (`S/public/player/choice_input.js:29–38,84–91`). The runner only clicks parent `#advance` (`capture_cases:154`), which sends advance but does not select a branch.

This is a definite static mismatch with the supplied real routes:

- Reinhard node 7 has branches 72/73 and route 7→8 requires branch 73; target 7 itself never settles in ready. Final route node 9 also has branches 92/93 and settles in choice.
- Soldier start node 4 has branches 42/43; route 4→5 requires branch 42. Its initial wait never reaches ready, and Continue alone could not choose the branch even if that wait were broadened.

These facts are in the exact draft native rows/route guards, not inferred from numbering. Freeze an explicit per-edge UI action for the observed branch ID, support the appropriate ready/choice terminal state, and keep one natural transition per authorized edge. Define the static capture point for a choice target explicitly. Do not invent a default branch or rewrite data to make a route sequential. This was not executed to reproduce a timeout.

### S2 — Case/global/cleanup bounds do not form one complete deadline

Work uses `min(globalDeadline, caseStart+75s)` (`capture_cases:12,29–36`), but cleanup starts a fresh `Date.now()+20s` at 174 instead of respecting the overall 540s endpoint. Thus the global bound can be exceeded by cleanup, plus the initial Page-close interval precedes the global clock. Cleanup's `Math.max(1, ...)` continues admitting operations after its endpoint, and its Promise arguments are started before the helper checks any time (`181–197`). Save/trace/CDP cleanup precedes Page close without a reserved close interval. The program's SHA await at 122 is also outside `bounded`.

Use a monotonic common case/global clock, distinct work/cleanup reserves, and operation factories that are refused before starting after expiry. Bound every async hash, body, export/download/save and close wait. A timeout must preserve pending-command/late-creation/unconfirmed-close state and stop later cases. The current late Page side handler at 104 requests closure, but does not prove completion or export a separate pending/close confirmation; the owner's Chrome/CLI close and OS receipt remain essential. Promise races do not cancel underlying browser operations or preempt synchronous JS. No timing or cleanup failure was observed in a live run.

### S3 — A failed evidence save can leave an unhandled download rejection

`save()` creates `page.waitForEvent('download', {timeout:30000})` at `capture_cases:15`, then awaits `page.evaluate` before attaching its later download await at 22. If evaluation fails, or the outer cleanup race abandons save and closes the Page before download, the download promise can reject without an attached rejection handler. That can become an unhandled host rejection while the owner is trying to preserve failure evidence and close the session.

Attach rejection observation immediately and include the download/evaluation/save lifecycle in the same bounded save ownership. Preserve a small returned failure receipt if the disk payload cannot be saved. Keep the Page-close attempt independent of export failure. This is a static failure-path gap, not a reproduced CLI failure.

### S4 — Original failures are recorded but not promoted to partial failure; some callbacks can throw diagnostics

The factory returns the original Promise/result (`instrument:124–135`) and ordinary factory/Core/render original calls are each invoked once with the same receiver/arguments and rethrow the same exception. Side fulfillment/rejection handlers are no-throw in the actual SDK Promise path. Those are valid B3 improvements.

However, `originalFailure()` writes only `qa.originalFailures` (`instrument:10`); it neither marks `qa.errors` nor disables capture. Waits and route checks inspect `qa.errors`/host errors, and final runtime checks never inspect `trace.originalFailures` (`capture_cases:69–77,159,169,183–196`). An original SDK failure caught by an application caller need not emit pageerror, so it can remain in the raw file while the case summary still reports no failure and proceeds. Every recorded original failure must invalidate the case independently of a global uncaught error or pixel-capture success.

The destroy callback (`instrument:19`) and timing-event callback (`149`) also call clock/append work outside a no-throw diagnostic boundary. The actual SDK emits destroy before completing its own destruction (`cubism4.min.js`, `_render`/destroy region near byte 102403), so a diagnostic exception from that listener can interrupt the real lifecycle. Guard these callbacks and use defensive failure metadata that cannot replace an original result/error. Default clock failure is unobserved; do not present this as an existing player bug.

### S5 — Strict body admission is incomplete

The resource reader correctly checks frozen exact Content-Length, identity response/request encoding, non-SW response, individual 8 MiB and cumulative 16 MiB reservations before `body()` (`capture_cases:49–61`). Its cumulative `resourceBytes` is not released when a host timeout abandons a still-running body, so that particular premature-reuse problem is absent.

It does not reject Transfer-Encoding or Content-Range, or require actual request GET, before body access. Program admission is weaker still: path-only response selection, no SW/framing provenance check, and an unbounded asynchronous SHA await (`113–123`). Complete the exact frozen identity profile before materializing either body; retain separate actual-settlement accounting/pending state when a host race expires. The existing SimpleHTTPRequestHandler adapter normally emits identity Content-Length bodies; this finding concerns the promised strict admission boundary, not an observed encoded response or a claim of an oversized current resource.

## Scope and freeze review: sound boundaries

The active draft contains exactly seven cases, fifteen edge visits, six character-only candidates and one unchanged formal BG case. `prepare_guards.py:24–31,188–199` and the active registry create exactly five `(scene,start,target)` groups:

| Scene | Start | Authored target | Examples |
| --- | --- | --- | --- |
| 10040004 | 6 | 7 | reinhard01-static |
| 10040051 | 4 | 5 | soldier01-static |
| 10040051 | 5 | 6 | julius01-static |
| 10040052 | 3 | 4 | julius-jersey01-static |
| 10040052 | 4 | 5 | the two Subaru shirt variants |

Each group allows only `character`; only the two variants with identical start/target share a scope. There is no scene-wide start/example/target Cartesian cross-authorization in draft-v2. The actual adapter/compiler independently gates scene/start/example and packet SHA, target/field bounds and expected native fields (`R/playback/serve.py:47–76`; `compile.mjs:19–55`). They do not write formal data.

Every active draft expectedNativeRow and packet expected row is null; top-level and packet authorization/freeze flags are false; guardReceipts is empty. This is correctly non-executable. Root must rebind complete current target/neighbour/source/resource rows after authorized publication and separately supply the exact compiled program/packet hashes plus approvedCompiledDifferences. Both templates remain false. Informational data HEAD/old blank rows are not a freeze and are not evidence of a bug when authorized publication changes them.

`owner.py:78–129` compares each exact scene/start baseline independently; checks all top-level properties, complete node arrays and all edges; permits only model changes in changed nodes; and requires the full ordered list to equal root's separately approved list. It does not truncate differences to the target. This is the right gate for any real inherited consequences.

The plan's advance declaration of Reinhard8 inheritance is an **unsupported expectation requiring v3 wording/assertion correction**: the currently inspected canonical compiler maps each raw character directly to model (`S/lib/preview.ts:41`), and the draft row8 character is empty. The player displays empty for an empty-model node (`S/public/player/player.js:359–361,415–416`). This scope authorizes only node7's character memory override and its static resource reference; it does not authorize model8 or an additional row8 override. Node8 remains an unrepaired story field/current empty display. A natural6→7→8→9 pass cannot sign node8's original-video appearance. Background sparse inheritance must not be projected onto character semantics, and this peer review makes no new claim about native-original character rules or a needed runtime repair. The future exact baseline/difference list must report actual behavior and must not manufacture a model8 change from the old inherit wording. Root's stated later sequence—independent static resource review, then separately approved per-node installation, including8—remains outside this diagnostic's install scope. Later formal row/source changes require fresh binding.

## Actor pixels, compositor and resource evidence limits

The real PairingViewer applies renderPose at beforeModelUpdate; the inspected SDK then calls Core.update followed by loadParameters. The Core hook copies the consumed input and assigns `lastApplied` only after the original update returns. The renderer wrapper reads after its one real render returns. At the one allowed character capture, default-framebuffer RGBA readPixels and that canvas's PNG occur synchronously in the same JS turn, with same-instance/game-frame metadata and no extra application render or pose update (`instrument:100–118`). Equality is not assumed: `index_pixels.py:33–45` compares decoded PNG RGBA with raw framebuffer RGBA after row reversal only and records mismatches without recoloring/unpremultiplying/fitting.

Whole-stage JPEGs are asynchronous compositor candidates. The rolling HUD changes on every real actor render and records exact render/frame/instance/applied IDs; candidate timestamps alone do not bind them. At most eight candidates per window are retained, three BG windows plus six character windows, at most72 retained overall. The index preserves exact JPEG bytes/dimensions and leaves HUD reading/equality pending (`index_pixels:47–55`). No current candidate exists, and no whole-stage same-frame acceptance is signed here. The public image reviewer must be delegated after browser closure; root must not inspect pixels.

The four target identity bodies are observed from existing browser responses, not fetched again by the instrumentation. The separate pre-Chrome owner preflight HTTP comparison is explicit in the plan. Natural application motion/config requests are not read as additional identity bodies. Actual sourceURL/instance and actual response SHA are useful resource-content bindings, not a GPU/MOC memory digest or pose/original-ID uniqueness proof.

The outer parent/iframe size assignments and parent-margin HUD are explicit QA fixture changes; no game CSS/body, parameter, seek, rate, camera offset or manual fit/render call is present. A normal ResizeObserver can naturally react to the outer preset. The hook imports the real shared-clock module; initialization order and runtime overhead still need observation and do not establish original timing fidelity.

## Owner lifecycle and independent checks

The owner requires an ordered prefix, one named profile, no existing browser/CLI processes, assigned owner ID, source/data/registry/health/compiled/resource guards, nice19/CPU22,23 for itself/server/browser processes, and finally closes the named CLI/browser before source guard-after and offline indexing (`owner.py:133–222`). `index_pixels` requires both OS-zero and CLI-zero receipts. These are useful execution gates; they do not compensate for S1–S5 or prove unconfirmed late/failed Page closure by themselves. Actual CLI/OS receipts remain required for a future run.

Independent checks matched all36 inventoried author files and all15 source/API audit hashes. Two `node --check` commands exited0; four Python files parsed with AST. No draft generator/compiler/owner/indexer was run. No active data HEAD was queried or refreshed, and ongoing resource/P29/P36 publication is preserved as authorized work. Only this new peer-review-v1 directory was written; author/production/source/data/registry/Git files were untouched. Substantial computation used nice19 on CPUs22,23.
