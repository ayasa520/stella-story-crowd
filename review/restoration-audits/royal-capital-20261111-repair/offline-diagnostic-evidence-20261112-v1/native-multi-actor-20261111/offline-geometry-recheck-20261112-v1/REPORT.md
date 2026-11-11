# Offline geometry recheck — 2026-11-12

P09's vertical composition remains **unexplained and unaccepted**. This
recheck found no proven transform, anchor or slot-order error in the existing
neutral candidate receipts. It found a concrete distinction needed in the next
logger: the prototype's `world` is an equivalent reduced card-space origin,
not a captured Unity world matrix, and its placement logs are emitted at
`fit()`, before the final draw submission.

This task read local evidence only. No images were opened, no Chrome session
was launched, and no production source/data, registry, Git state or Site was
changed. All new files are confined to this directory. The checked canonical
checkout is clean at `37232806a8180375a4b7a178e27157bb16d12201`.
The local `story_crowd` multi-actor implementation is an unaccepted prototype;
the canonical checkout has no `lib/native-actors.ts` or `native_parent` branch.

## Evidence and independently checked values

The starting evidence was `../REPORT.md`, `../original-layout.json`,
`../original-scaling.json`, `../model-origin-evidence.json`,
`../geometry-channel-evidence.json`, `../geometry-channel-review.json`,
`../canvas-geometry-detached-result.json`, the prior bounded Capstone files,
and the four-case visual-review receipts. Their actual hashes, bounded source
excerpts and this check's calculations are in `receipt.json`.

`recheck.py` freshly decoded only the already identified original scene member
`assets/bin/Data/b5fb3e33e10fc9f4695252e4645bc30c` from the configured APK.
Its SHA-256 is
`d51b1440c39d796fec41c9afaa64c6d66482230cdb027a1772e5af7740dccb7d`,
matching the earlier original-layout receipt. Its Camera serializes FOV 30,
perspective projection, full normalized viewport, and local position
`(0,0,-10)` under the common `CardViewSpace`. These are serialized inputs;
they do not prove P09's runtime camera matrix.

The original binary, metadata, layout, type table, UI_CharaPosition bundle and
three AC_base bundles were rehashed and all match the earlier source receipts.
The previous complete controller/curve/material audit was read, not rerun.

| Recheck | Result |
|---|---|
| All four examples, 12 actor placement records | Every logged slot exactly equals the original Chara3 slot |
| Created entry index versus slot index | 12/12 preserved, including after the candidate draw-order change |
| `PosN * script * CH_top` origin | 12/12 agree with logged origin; residual below `1e-9` |
| Pixels per Unity unit from original serialized camera | 12/12 agree; `173.5403625519528` for 523×930 |
| Detached canvas receipt, 3 models | Centered canvas origins, identity internal matrices and half anchors |
| Detached position and scale recomputation | All agree below `1e-9` |

These are numeric consistency checks, not a new screenshot acceptance. The
equivalent origins remain Kan `(-1,-1.0399999618530273,0)`, Chin
`(-0.07999999821186066,-1.75,0)`, Ton `(1,-1.934999942779541,0)`.
Changing candidate sort order did not reassign those origins or slots.

The prior visual reviewer estimated Kan about 200 source-frame pixels too
high, Chin about 40–60 pixels too high, and Ton approximately consistent.
Those remain the prior review's visual estimates from
`../visual-review/visual-review-result.json`; no new measurement or fitting
was performed here. They must not be converted into script-local offsets.

## Proven telemetry distinctions

1. In `story_crowd/public/studio/actor_placement.js:136–151`, the variable
   `world` contains `PosN * script * CH_top` after omitting the original
   UI_CharaPosition root and the reciprocal RawImage presentation. That is
   exactly the existing neutral, zero-depth reduction. Calling it a Unity
   `localToWorldMatrix` value would be incorrect: the actual native hierarchy
   includes scene ancestors and the dynamic root. Compare full captured
   matrix chains, or explicitly reduce both sides into the same coordinates.

2. `STORY_NATIVE_ACTOR_PROJECTION` is emitted at `actor_placement.js:153–164`.
   `ActorStage.show` calls `fit()` at `actor_stage.js:52`, then awaits motion
   and lighting preparation; the final child reorder and reveal occur at
   lines 77–78. The four existing groups' three fit calls span roughly
   1.24–1.37 seconds each. These receipts preserve intended placement and
   preparation order, not the actual matrices, drawable vertices or order of
   all three actors in one submitted frame.

3. The actual browser model update is driven by the vendor `_render` path.
   The current vendor blob updates the internal model when `deltaTime` is
   nonzero, then composes the PIXI projection with `worldTransform`, calls
   `internalModel.updateTransform`, and draws. A frame may draw retained
   geometry without a new update; a logger needs both an update generation
   and a draw ordinal.

4. The SDK calls `core.update()` and then `core.loadParameters()` after the
   `beforeModelUpdate` handlers. The later input array can therefore differ
   from the inputs that produced the current evaluated drawable geometry.
   The fresh Felt22 audit already pairs verified pre-update inputs with
   later records: for example its first active row records ParamHandL/R
   `-0.7475200295448303` before update and 0 in the later raw read. This is
   evidence that observation phase matters, not evidence of a P09 pose or
   a P09 animation failure. No old unpaired `raw0` record is treated as an
   applied pose.

The Felt22 reference is
`../../visual-low/p11-felt21-production-review-v1/fresh-felt22-v31/fresh-numeric-audit.json`.
Its first-active pairing has shared frame 376, pre-update index 126,
render ordinal 86 and the same Felt model/core identities. This recheck did
not open its images or decompress its large capture.

## Exact source bindings

The full SHA-256 and bounded excerpts are preserved in `receipt.json`.

| Local prototype file | Relevant lines | SHA-256 |
|---|---|---|
| `story_crowd/lib/native-actors.ts` | 126–164 | `24af3fb866baf763c8d0106104fc61c4eaeffd34077af925edbc9eacc821eafa` |
| `story_crowd/public/studio/actor_placement.js` | 110–164 | `be0d32ae4bf34088abf41b280ff9fac3f5336a52980d19f34edc8b1c3647ec70` |
| `story_crowd/public/studio/actor_stage.js` | 47–79 | `eda6d7a15abc5a357b3b09322a177ed98f07f6cf90d2c6d0dcc47dfd183db29c` |
| `story_crowd/public/pairing/viewer.js` | 100–115 | `d3178fb7512a9b87de833be4ad49c08dbfcbb149cc620bd1610973c7e2b6f6bd` |
| `story_crowd/public/studio/actor_animation.js` | 230–240 | `644de9daca3be02601c6e316bfb741de8b7af98812702dfbbe2c088763da441c` |

The vendor `story_crowd/public/pairing/vendor/cubism4.min.js` is SHA-256
`af1267e6d52759b245766c578d905bfa025b532d5c3cc727c370957c4409e21b`.
It is a single-line file; zero-based byte offsets, rather than invented line
numbers, identify its `_render` (102403), pre-core emission/update/restore
sequence (113134), internal draw (113831), and final renderer.drawModel call
(114055). Exact needle/offset pairs in `receipt.json` take precedence.

## Next discriminating evidence

`DIAGNOSTIC_PROPOSAL.md` narrows the existing full native plan to one joined
browser draw packet plus the corresponding native placement/accepted-input/
vertex/camera/UI packet. It is a proposal only, with no executable hook
installed and no new rendering request made by this subagent.

Matching static prefab geometry does not recover the active P09 CSV, runtime
parent matrices, pose generation, motion phase, rate, exact equal-sort
behavior, camera or UI state. None of those unknowns is assigned as the cause.
P09 remains pending; P28's newly identified three-person composition also
remains pending. The tiny Subaru CHOICE avatar is not added to actor count.
No variant substitution, camera adjustment, per-model correction or data write
is supported by this recheck.

Reproduction: `nice -n 19 taskset -c 22,23 uv run --offline --no-project --with UnityPy --with capstone python <this-directory>/recheck.py`.
The completed receipt records nice 19 and affinity `[22,23]`.
