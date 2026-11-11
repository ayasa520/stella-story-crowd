# Proposed minimal joined geometry capture

Proposal only. Do not adjust a camera, transform, scale, clock, pose, motion
token or resource to collect it. It adds no original P09 values and authorizes
no browser session. The existing full plan is `../NATIVE_GEOMETRY_LOG_PLAN.md`.

First capture the same two private P09 candidates, nodes 10020002:5 and :15,
under the one browser owner appointed by root. Preserve previous → group →
next playback. A third neutral candidate or new offset experiment is not
needed to answer the present fit-versus-draw question.

## Browser: three observation points, one identity chain

Use WeakMap identities for the StoryActor/viewer, Animator, PIXI model,
internal model, core, underlying native model and renderer; bind each to
the exact model/MOC/texture digests once. Keep slot creation ordinal separate
from child draw order. Record shared-clock frame, node, phase, monotonic time,
update generation and actual draw ordinal in every joined record.

1. After the existing viewer `beforeModelUpdate` handler, append one passive
   observer to the actual internal model. The handler is registered at
   `public/pairing/viewer.js:111`; it dispatches through
   `public/studio/player_scene.js:35–38`, and applies layers at
   `public/studio/actor_animation.js:230–240`. Verify listener order and
   `viewer.animator` identity on every emission. Capture the actual parameter
   ID/index/value arrays, part opacities, Animator state/weights/times and
   shared frame at this boundary; mark these **input**, not evaluated vertices.
   Missing IDs stay missing. Never call Animator.render/clock again.

2. At the real `internalModel.renderer.drawModel` entry, before invoking the
   original once, record the existing renderer MVP via `getMvpMatrix().getArray()`
   copied immediately. This call is made by vendor internal `draw`, line 1,
   byte offset 113831, after `setMvpMatrix` and `setRenderState` (the exact call
   offset is in receipt.json). Record `drawingMatrix`, internal local and
   centering matrices, PIXI model local/world matrices, pivot, anchor, scale,
   position, rotation, visibility/alpha, stage child index, framebuffer viewport,
   and app/canvas CSS/backing dimensions. Keep equivalentCardSpaceOrigin from
   fit separate from all actual matrices.

   At that same draw entry, copy read-only native drawable IDs, render orders,
   visibility/opacities, per-drawable vertex AABBs and vertex digests. Preserve
   full vertices for at most three head/body drawables per actor only at the
   retained milestones; choose their names from the real ID list. This observes
   the geometry consumed by this renderer. Do not derive it from the restored
   parameter inputs, clip bounds or `getBounds()`.

3. The scene/frame record after the real app render returns should list the
   actual draw ordinal for every actor that rendered, plus the existing image
   capture reference if one is being collected. Record both (a) whether an
   update occurred in this draw and (b) which previously observed update
   generation its vertices use. Vendor `_render` at byte offset 102403 only
   updates when deltaTime is nonzero; do not demand a fresh generation for a
   legitimate repeated draw. Keep cross-node or missing-generation rows
   explicitly unpaired. An independent rAF timestamp alone is insufficient.

All wrappers must call their original function exactly once, preserve this,
arguments, return values and exceptions, and be removed at the end. Do not
trigger update, rendering, extra screenshots or synchronous GL readbacks.
Flush buffered numeric records outside the draw call.

Bound retention to the existing seven native-plan milestones per card:
placement completion, settled Card_wait, first Card_in render, completed
Card_in and two settled frames, plus the original SetLive2D invocation.
Keep small change-only matrix/order traces through entry. Log geometry and
parameter schemas once; use digests for unchanged large arrays. No large
frame set is requested by this proposal.

## Native: join the equivalent stages, do not compare unlike coordinates

| Existing original method/call | Observation needed |
|---|---|
| `ADVUtil.SetLive2D`, RVA `0x1dee348` | Raw character/motion once; raw line count and created ordinal |
| `Live2D.Util.SetTransform`, RVA `0x128a838`; new-model call at `0x131feac` | Inputs and resulting base Transform; actual chain from CardViewSpace through UI_CharaPosition/PosN/AC_base/CH_top/model/drawable, with complete matrices |
| `CardScaleCharaPosition.Recive`, RVA `0x1257e40` | Actual argument and resulting root matrix; R/G and touch/UI state |
| `TryWriteParametersAndParts`, RVA `0x1670d80`, called at `0x1670600` | Input arrays and success Boolean; attempted writes are not successful generations |
| `CubismTaskableModel.Execute`, RVA `0x1671aec`; Update `0x1671b74`, transfer `0x1671b88` | Successful generation/completion linkage, without blocking worker-owned arrays |
| `CubismRenderer.OnDrawableVertexPositionsDidChange`, RVA `0x12086c8` | Consumer vertices, drawable identity/order and actual object matrix |
| Actual linked camera pre-render, plus return of CardUVSetter.LateUpdate `0x1705108` | Actual CPU/GPU camera matrices and RT identity; final RawImage rect/UV/corners/Canvas/masks |

Do not call ForceUpdateNow or ForceUpdateCanvases. The worker and camera may
consume different generations; preserve that result rather than forcing them
to complete together. The actual camera must be joined to RawImage through
the texture instance, not selected only by name.

The existing disassemblies are bound to binary SHA-256
`54c97bce616bdb062f12b0bccba47b1c6ff17f61da450d8bd0efa403f8822c05`.
`../geometry-native-capstone.txt:492`, `:550`, `:663` retain the render/write/
execute paths; `../model-origin-native-capstone.txt:1282` retains the original
placement call. The full source hashes and excerpts are in receipt.json.

## What the packet would distinguish

- Fit matches, actual browser draw matrix differs: local browser placement or
  lifecycle mutation between preparation and submission.
- Matrix chain matches, evaluated native/browser vertex shapes differ:
  parameter/state/phase or deformation boundary; identify the first differing
  accepted generation before assigning a motion cause.
- Object matrices and evaluated geometry match, clip coordinates differ:
  camera projection or render-target transform.
- Clip coordinates match, screen mapping differs: RT/UV/RawImage/Canvas/crop.
- Only draw order differs: inspect actual child and native sorting orders;
  keep slot assignment unchanged.

Without native runtime logs, the browser packet can validate its own
submission and close the fit-time gap. It cannot determine which missing P09
CSV or original evaluated pose was active. Preserve that limit.
