# Draw diagnostic preparation handoff — unexecuted / not acceptance

The proposal is now concrete code for independent offline peer review. It
wraps the actual Core.update, PIXI.Renderer.render and Cubism drawModel/
drawMesh paths, with one original invocation per path. It records input
generations and actual submitted matrix/vertex/index/order/opacity arguments
without a second render, pose evaluation, parameter/time/rate/camera change,
viewport fixture, screenshot or pixel readback.

The prepared files are:

- [instrument.js](instrument.js): bounded per-document runtime patch; actual
  model/internal/core/native/renderer IDs; observed model/settings/texture URLs;
  pre-Core inputs, actual per-mesh arguments, mask/color distinction, matrices,
  viewport, order and retained-generation links; cleanup and watchdog.
- [resource-observer.mjs](resource-observer.mjs): actual existing response-body
  SHA-256, per-load URL/content joins, and required observation coverage audit.
- [run-diagnostic.mjs](run-diagnostic.mjs): callable owner draft; requires a new
  root-reviewed frozen source/program/packet; natural previous → target → next;
  bounded gzip output, stop-on-failure, guaranteed Page close paths.
- [execution-UNRELEASED.json](execution-UNRELEASED.json): intentionally fails
  the execution gate; unknown routes, URLs and program/packet digests stay null.
- [PLAN.md](PLAN.md): exact observable/unobservable boundary, sampling, limits,
  source bindings, owner bridge and process-close requirements.
- [source-audit.json](source-audit.json),
  [shader-matrix-receipt.json](shader-matrix-receipt.json),
  [resource-lock.json](resource-lock.json): bounded exact SDK/QA receipts and
  twenty-two file locks, including nine normal-model resource files.

The code keeps actual PIXI matrices separate from the unavailable original
Unity localToWorld and unavailable neutral reduced-card origin. GPU memory
bytes are not observed. Network hashes are delivery/content hashes; shared
atlases do not acquire fabricated unique requests/uploads for each load.
Missing/conflicting target resource hashes or required matrix/mesh/input
observations produce a partial failure, not a guessed field or acceptance.

Static checks passed for all three JavaScript files, Python AST, JSON,
whitespace and explicit forbidden-call searches. The twenty-two source/model
resource bytes still matched at final source validation. There were no unit
tests, browser sessions, application execution, extractions or production/Git
mutations in this task. All preparation commands used nice19 and CPU22,23.

`static-review.json` retains **static_review_needs_attention_unexecuted**
because the data HEAD changed during authorized root/data-owner progress.
`freeze-boundary.json` preserves the separate time-stamped samples. The old
lock is not overwritten; [VALIDATION_NOTE.md](VALIDATION_NOTE.md) corrects an
inaccurate f774 suffix in the static-check label and an earlier prose shorthand.
Root explicitly confirmed that the data changes were authorized releases.
No further data-head polling or attempt to follow the active writer is needed.

Canonical source remains the inspected `37232806`; it has no native_parent
branch or native actor parser. It cannot be presented as a usable P09
multi-actor runtime. A future execution requires root to choose the reviewed
execution source and freeze its current data/program/source/resource identities
in new evidence after ongoing data work. This preparation enables no capture
and makes no geometry, costume, pose, original-CSV or chapter acceptance claim.

Next: independent peer review of the transparent wrappers, array identity and
mask/color joins, per-load resource-content semantics, caps and failure cleanup.
Any resulting revision belongs in new evidence. The browser owner is assigned
by root only after a concrete new freeze; this subagent did not launch Chrome.
