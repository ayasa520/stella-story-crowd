The new actual rendered references match **Julius01's knight costume** and
**Elsa01's cloaked costume**. I directly viewed both full and actor-viewport
PNGs for each model, then revisited all eight original full frames below.
All eight support guarded **character-only** proposals in scene10450056.

| Ordinal | Node | Original time | Proposed character |
| --- | --- | --- | --- |
| 76 | 15 | 460.999s | `live2d/AC_elsa01` |
| 77 | 16 | 462.999s | `live2d/AC_julius01` |
| 78 | 17 | 468.999s | `live2d/AC_julius01` |
| 81 | 20 | 482.999s | `live2d/AC_julius01` |
| 83 | 22 | 504.999s | `live2d/AC_julius01` |
| 84 | 23 | 513.999s | `live2d/AC_julius01` |
| 85 | 24 | 515.499s | `live2d/AC_julius01` |
| 86 | 25 | 520.499s | `live2d/AC_elsa01` |

Julius matches the lavender swept hair and long central lock, high red-lined
collar, white short cape with black/red edging, gold chest clasp, dark uniform
and pale sleeves. The choice overlay at node22 leaves enough hair, collar,
cape and clasp visible for this costume comparison. Elsa matches the long
braid and side curls, purple rose/feather collar, mantle with round gold clasp,
purple-striped bodice and long gloves. Her mantle is clearly present at both
nodes15/25; no no-mantle variant is inferred.

`actual-reference-binding.json` ties these exact PNG paths to root's actual
requested nodes, private override examples (`persisted:false`), ready state,
opacity1, MODEL_READY/display-commit logs, model3 HTTP200 responses and current
catalog asset-member paths. Existing original model3/MOC/texture/prefab and
controller proofs are linked rather than copied. Old trials remain unchanged.

The actor PNGs include the background/dialogue viewport; they are not isolated
transparent model exports. The existing player exposes no internal
instance/Core identity here, so no such identifier or Core version is asserted.
The actual model IDs, requested resource URLs, ready-state logs and visible
costumes provide the new rendered-reference attribution used by this review.

All eight current character values are empty. `row-decisions.json` binds each
current stable key, unchanged Japanese source text, original frame/event and
decision. `eight-character-only-draft.json` contains exactly six Julius and
two Elsa character changes with `rootConfirmed:false` for root integration.

Normal-pose preview motion is **not accepted** as source acting. Expression
differences (including Elsa25's blush), pose, scale, entry/exit, geometry,
timing, audio, FX and routes remain outside this acceptance. Subaru models and
the two illustrated spell observations were not reviewed in this task. No
browser, extraction, install, formal/source/Git write or inventory was run.
