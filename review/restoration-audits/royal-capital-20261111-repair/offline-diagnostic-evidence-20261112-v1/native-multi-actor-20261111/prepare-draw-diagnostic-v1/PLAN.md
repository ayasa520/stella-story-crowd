# Prepared draw diagnostic — unexecuted, not acceptance

This directory contains a concrete init-script patch and owner runner draft.
It contains no capture result. No Chrome, application execution, extra render,
parameter evaluation, unit test, source/data/registry/Git change, or publication
was performed while preparing it.

## Minimum observable packet and remaining unavailable facts

| Observable at an existing real call | Not supplied or inferred |
|---|---|
| `Core.update` input parameter and part arrays immediately before its single original call; completion and generation identity | A later restored input array is not relabelled as the applied pose |
| Actual PIXI app render ordinal; actual model draw order and Cubism `drawModel` entry MVP/matrices | No additional render, manual Animator/Core update or forced clock/frame |
| Actual `drawMesh` arguments: evaluated XY vertices, triangle indices, UVs, texture index, opacity, blend and mask flags | No reconstructed vertices from parameters or imported clip bounds |
| Actual current MVP, mask matrix, clip UV matrix, GL viewport and framebuffer identity at that mesh call | No claim to post-execution GPU uniform contents or GPU memory bytes |
| Supplied real model-document URL/references; actual settings URL and texture resource URL/UID when exposed | Missing fields remain null/error; model names do not supply missing URLs |
| SHA-256 of existing actual network response bodies; per-load observed-URL joins | No second fetch; no unique network request/upload asserted for every shared texture load |
| Actual PIXI model/parent matrices, pivot, anchor, local/internal/centering/drawing matrices | Unity `localToWorld` and the neutral reduced card-space origin are unavailable in this browser hook and explicitly separate |

The body hash is a delivery/content measurement, not a hash read from GPU
texture or MOC memory. A shared atlas may legitimately reuse one delivery.
Every matching observed body must agree; missing/conflicting digests fail the
target binding. A load carries all observed request IDs and does not invent a
unique causal request when several same-URL deliveries exist.

The original native packet in `../NATIVE_GEOMETRY_LOG_PLAN.md` is still needed
to compare to original runtime matrices, successful Cubism generations,
evaluated vertices, camera projection and final RawImage/UV presentation.
This browser-only draft cannot determine missing original P09 CSV or poses.

## Inspected source and execution prerequisite

Source was read directly from the clean canonical Site checkout at
`37232806a8180375a4b7a178e27157bb16d12201`. The lock's actual read-only
preparation data-head sample was
`72bace5056b95eeb694caa15ac227eb6ca3670c7`; this is not a frozen-capture approval.
`source-audit.json` retains bounded snippets, exact byte offsets and full file
hashes for the original SDK and the previous three-case QA instrumentation.

The inspected SDK blobs are:

- `cubism4.min.js`: `af1267e6d52759b245766c578d905bfa025b532d5c3cc727c370957c4409e21b`.
- `live2dcubismcore.min.js`: `25ae938cb4fe282ce189b357bcc97e603d1e1f7ec78bf04150d401c23cdc792f`.
- `pixi.min.js`: `403f2f2ee8145fa17f60c5c89403056efe2680e5096ec2762036486914ed19c5`.

The existing QA's `instrument.js:33–62` demonstrates wrapping the actual Core
update; lines 157–174 demonstrate wrapping the real PIXI render. This draft
keeps those boundaries, adds real Cubism draw/mesh observation, and removes
HUDs, PNG/RGBA reads, layout assignments and screenshots from this numeric
diagnostic.

**Canonical372 does not contain `lib/native-actors.ts` or a `native_parent`
renderer branch.** Its presence on disk cannot be treated as a usable P09
multi-actor execution. `resource-lock.json` describes the actual canonical372
module graph and current normal-model resources; it must not silently validate
the different unaccepted `story_crowd` prototype. A future root-reviewed
execution source/program and its matching new locks are a required independent
step. No such source or registry change is included here.

## Concrete files

- `instrument.js`: an init-script function. It observes the real factory and
  installs per-instance wrappers on Core.update, renderer.drawModel/drawMesh,
  plus one PIXI.Renderer.render wrapper. Each path invokes its original once
  with the same `this` and arguments and preserves its result/exception.
- `resource-observer.mjs`: a host response observer and per-load digest join.
  It reads existing response bodies and records hashes, never requests a
  second copy or intercepts/fulfils a request.
- `run-diagnostic.mjs`: a callable owner draft, with no top-level invocation.
  It accepts an already-open owner Page; it starts no Chrome. It checks the
  frozen program/packet, uses the natural previous → target → next controls,
  exports bounded gzip evidence and closes each Page in `finally`.
- `resource-lock.json`: nine current normal model JSON/MOC/texture files and
  thirteen actual `/player/`/shared source responses, each with exact size and
  digest. The delivered bodies must be observed and checked at capture time.
- `execution-UNRELEASED.json`: intentionally fails the runner's release gate.
  Unknown route, server URL, program/packet hashes and byte counts stay null.
  It does not contain guessed original CSV, slot fields or motion tokens.
- `prepare-lock.py`: offline lock/source-receipt preparation. It writes fresh
  files only; do not rerun over the current receipts.

The callable owner bridge, after a separate root release and new frozen
execution file, is concretely:

```js
async page => {
  const {runDrawDiagnostic} = await import('file:///home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/native-multi-actor-20261111/prepare-draw-diagnostic-v1/run-diagnostic.mjs');
  return runDrawDiagnostic(page, ROOT_FROZEN_EXECUTION);
}
```

This is a bridge draft, not a command executed during preparation. The single
browser owner remains responsible for closing Chrome and the CLI immediately
after capture and verifying OS process counts are zero before image review.

## Sampling, joins and budgets

Only the assigned target node's Core inputs and frame/draw records are kept.
Model load/schema/destroy metadata also records predecessor/successor identities
within a twelve-load bound so their arrays cannot be mistaken for the target.
Each case uses one fresh Page and one target, with at most two P09 cases.

For each target, full mesh arguments are retained for at most six real app
renders: the first two target-labelled renders and four ready renders after
observed ready elapsed times 0, 0.25, 0.75 and 1.25 seconds. The shared clock is
read, never advanced. A stale predecessor frame can remain among the first
two; it stays labelled by its actual instance/URL. These samples are a numeric
diagnostic, not a complete entry or motion acceptance.

The shared clock module is imported by the owner only after predecessor ready,
when the actual NativePlacedViewer has already loaded it. The init hook does
not initialize that clock early. A private logger `arm()` changes only logger
state and precedes the one natural advance to target.

Every draw joins model/internal/core/native/Cubism-renderer IDs, load ID,
app render ID, model-draw ordinal, mesh ordinal and latest completed input
generation. A retained geometry draw may lack a fresh update. The packet keeps
`inputSameRender`, `inputSameSharedFrame` and `inputCaptured` separate; it never
turns a missing or cross-node input into an applied-pose assertion.

The SDK uses the mask matrix for mask-pass vertex positions, and the renderer
MVP for color positions. The clip matrix is retained separately for mask UVs.
`mesh_submission.pass` and `vertexTransformSource` prevent their conflation.
Matrices are actual copied CPU submission values; no camera fit is calculated.

Hard bounds per Page are 45 seconds, 240 target app renders, twelve model
loads, 512 mesh calls per retained app render, 80,000 numeric elements per
individual array, 6,000 records and a 20 MiB trace budget with metadata reserve.
Network hashing permits 64 relevant responses, 8 MiB per declared/decoded
body and 32 MiB total; missing Content-Length fails before body materialization.
Final output is capped at 24 MiB before gzip. Runtime read/copy/serialization
has nonzero cost; its wall times and actual shared clock are retained.

Any missing required matrix/interface, ambiguous submitted-array identity,
budget overflow, target load digest mismatch, runtime error, changed frozen
source/program, or cleanup conflict retains a partial/failure state. It does
not tune a field or continue to the next case. Wrappers/listeners are restored
after the current original call unwinds; cleanup identity conflicts are
reported instead of overwriting someone else's wrapper. A watchdog and
pagehide cleanup cover abnormal endings; owner `finally` also closes the Page.

## Static validation and review limits

Only JavaScript syntax, Python AST, JSON structure, whitespace, current source
hashes and explicit forbidden-call searches are checked during preparation.
No unit test or browser/application execution is run. A syntax pass establishes
that the draft parses; it does not prove event order, API availability in a
live session, budget sufficiency or fidelity.

Status remains **unexecuted / not acceptance**. The former costume recheck
supports the visible normal-model family prerequisite for the old P09 frames;
the new logger must still prove its own actual delivered resources and actual
submission identities when a future root-reviewed execution is available.

The ending data-head sample differed from the prepared sample. See
`freeze-boundary.json` and `VALIDATION_NOTE.md`: the current data/program
freeze must be supplied by root later. The thirteen source files and nine
model-resource bytes still match their recorded hashes. No lock or execution
scope was silently updated to follow ongoing data work.
