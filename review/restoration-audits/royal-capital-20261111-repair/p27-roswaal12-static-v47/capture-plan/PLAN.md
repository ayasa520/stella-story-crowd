# Three-case assembled review: offline preparation only

This package is unapproved and unregistered. No browser has been opened for
it. `draft-ready-v2/` is the reviewable current draft; the earlier `draft/`
is retained as preparation history. Whole native/review file hashes are
intentionally absent until a final root freeze. Source/model/aggregate locks
and complete target/neighbour row equality are already checked.

## Bounded order and acceptance limits

1. `roswaal13-character-only-model41-v1`: scene10200006,12→13→14;
   change only13.character to `live2d/AC_roswaal01`. Preserve its original
   blank motion, commands, position and every other field. Capture a settled
   whole-stage PNG, actual actor-canvas PNG and original WebGL RGBA8 buffer,
   with exact model JSON/MOC/texture HTTP identities. Compare costume against
   the existing original13 full-frame witness. This is a static assembled
   resource reference; it signs no motion, geometry, unique original wrapper
   or other Roswaal node.
2. `n9-hohoemu-face-normal-assembled-v2-model41`: scene10150004,8→9→10;
   only9.character=`live2d/AC_subaru_butler01`,
  9.motion=`act_hohoemu,face_normal`.
3. `n9-hohoemu-face-normal02-assembled-v2-model41`: same route/default01,
   only9.character and9.motion, second motion=`act_hohoemu,face_normal02`.

Both face choices remain numerical candidates, not visually accepted states.
The immutable original120-frame entry (409.522–413.489s), its index/review
hashes and all source PNGs remain the comparison. Neither candidate recovers
the original CSV/ID or approves other butler nodes. The older proposals and
receipts are unchanged. A shorter approved execution may use only an ordered
prefix, beginning with Roswaal; maximum3 cases, once each, no automatic retry.

Original texture-atlas decoded RGBA identity and the captured model framebuffer
are different evidence. The former is retained from the original-resource
audit and tied to exact served PNG/MOC bytes; the latter is a new assembled
render for direct costume review. Their hashes are not compared as if they
represented the same pixels.

## Explicit fixture and dimensions

Root clarified the actual playback template is iframe100%×930, while the
older Felt QA explicitly preset a narrow iframe. The new fixture is explicit:
parent1280×1000; after goto, before target advance, set only the iframe outer
box to480×856 in QA DOM. This preset is fixed before comparison, not adjusted
from a result. Template files, inner body/CSS, camera, offset, model scale and
placement stay untouched. All target model instances must be created after
the preset stabilizes; predecessor setup is logged separately.

The production viewport is measured, constrained to the original9:16 ratio,
and then held stable. It is **not** asserted to be856px high: current CSS can
produce853.333px within the480×856 outer iframe. Static CSS arithmetic is not
reported as a runtime measurement. Every actual render logs frameRect,
viewportRect, actor canvas intrinsic size and CSS rect, plus readable PIXI
renderer screen/resolution. Parent HUD is fixed outside the iframe at its
right edge+8, after checking that no existing parent content occupies it.
No diagnostic may overlap game pixels or change game layout.

The PNG, RGBA buffer and compositor image have different boundaries. Offline
geometry comparisons must use each image's actual dimensions/crop and the
logged transforms/normalization factors. The compositor is the parent page;
the stage screenshot is the measured viewport; actor PNG/RGBA use the actual
canvas intrinsic size. No parent-height or iframe-height substitution, unknown
camera fitting, invented offsets, or geometry acceptance is automatic.

## Capture and actual parameter binding

The unique Chrome context closes its initial blank Page, then uses exactly
one fresh Page per case, closing it before creating the next. Init hooks are
installed only on that Page; a per-document duplicate-hook guard also exists.
This prevents two butler variants from inheriting stacked hooks or observers.

Instrument the actual `Live2DModel.from` instances and read parameters directly
before the real Core update. Record same instance/update/game-frame IDs,
actual applied parameter/part values, alpha and transforms after the real
renderer call. Do not sample a later reset parameter array and call it the
applied pose. Full trace cap is2400 actual updates/renders per case; overflow
is retained, not silently accepted.

Start actual compositor capture before advancing the predecessor. Use
everyNthFrame2, at most300 JPEGs per case, stop on a real overflow and retain
the overflow/drop observation. Continue the natural route through entry,
at least3 actual game seconds from motion_ready, held/static capture and
successor cleanup. This cap is a bound, not a promise every milestone fits.
Missing low-alpha/held/successor pixels remain pending; never add a retry or
substitute numeric alpha for pixels. No clock changes, seeks, forced poses,
artificial load delays or native Wait/commands are added.

Compositor JPEG bytes and metadata are stored in a disk gzip, not CLI output.
Read the pixel HUD offline to bind exact render/applied records; host receipt
time is not a frame match. Locator screenshots retain request intervals and
make no exact applied-frame claim. The static actor PNG/RGBA is captured
immediately after one actual renderer.render without redraw, and carries that
render/update/instance binding. The original WebGL RGBA buffer stays bottom-up,
without recoloring or unpremultiplication.

## Final freeze and execution boundary

Root must review this package, finish unrelated data writes, then create a
fresh local freeze output, for example:

```sh
nice -n 19 taskset -c 22,23 env PYTHONDONTWRITEBYTECODE=1 python data/native_recovery/royal-capital-20261110/repair-20261111/visual-high/assembled-three-case-plan-20261112-v1/prepare_guards.py --freeze --output /home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/visual-high/assembled-three-case-plan-20261112-v1/freeze-v1
```

This rechecks the deep target/neighbour rows and immutable41-model locks,
then hashes the **actual current** whole native/review documents, ownership,
manifest, Studio, selected canonical source/compiler, QA adapter/template and
all capture/owner scripts. Unrelated P27/P28 updates are not bound to an old
draft scene hash. Any target/asset/source mismatch stops generation; it does
not silently refresh those protected values.

Freeze generation does not register anything. Root separately reviews and
registers exactly the two scopes from the frozen registry PROPOSAL, starts or
identifies its own read-only adapter, and assigns the sole browser owner.
Root then creates a fresh release from `root-release-TEMPLATE.json`, supplying
the exact frozen execution-input receipt, adapter PID, session and output
directory. The template's approval booleans remain false and its null fields
are deliberately not executable.

Only after that separate authorization:

```sh
nice -n 19 taskset -c 22,23 env PYTHONDONTWRITEBYTECODE=1 python data/native_recovery/royal-capital-20261110/repair-20261111/visual-high/assembled-three-case-plan-20261112-v1/owner.py --release /absolute/path/to/root-created-release.json --execute-approved-once
```

Owner preflight completes before Chrome open: actual hashes, deep rows,
canonical source, exact registered packets, adapter PID/OS/nice/affinity,
served target model JSON/MOC/texture/detail hashes, baseline/candidate compiled
diffs and pre-existing browser/CLI zero. Compile comparison permits only the
target model/body/face differences described above; all other nodes, edges,
phases, commands and top-level program data must match. Preflight writes no
formal data and does not restart a timed-out or unavailable service.

Any case failure preserves its partial raw evidence and stops remaining cases.
The owner immediately closes its named CLI/Canary in finally, verifies CLI/OS
zero, then rechecks protected bytes. Only after zero does `index_pixels.py`
extract unchanged JPEG/PNG/RGBA bytes and write hashes/dimension indices.
The wrapper prints metadata only. If browser/context failure prevents raw
save, preserve the failure log and explicitly retain the missing pixels.

## Current validation and remaining work

Only Python AST parsing, JavaScript syntax checks, local hash checks and
target/neighbour equality have been run. No adapter registration, compiled
override execution, Chrome, capture, image extraction or visual review has
been run for this package. Runtime behavior of the hooks, downloads, CLI Page
lifecycle and frame coverage remains unvalidated until the approved trial.

Roswaal acceptance is limited to the explicit resource/static costume
reference. Butler full-entry appearance, arm/face behavior, geometry and
earliest-positive pixels remain pending. No installed field or pending count
changes in this preparation.
