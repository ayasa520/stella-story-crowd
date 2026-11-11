# Original native blink writers: bounded offline audit

Status: **static mechanism established; recorded Felt15 writer and cause unknown**.
This audit did not run Chrome, a native game, a renderer, or new image review.
It wrote only this local evidence directory. No motion field, website code,
registry, shared adapter, archived package, camera, projection, or time offset
was changed. Inspection processes used nice 19 and CPU affinity 22,23.

## Serialized facts and their limit

The previously complete `ac_felt01.prefab` inventory contains one enabled
`CubismEyeBlinkController`, `BlendMode=2`, `EyeOpening=1`, and two enabled
`CubismEyeBlinkParameter` markers on `ParamEyeLOpen` / `ParamEyeROpen`.
The complete actor/base inventories resolve all referenced MonoScripts and
contain no serialized `CubismAutoEyeBlinkInput` or `CubismUpdateController`.
`CubismModel` and the eye controller MonoScripts both have execution order 0.
The actor Animator is enabled, `m_UpdateMode=0`, `m_CullingMode=0`, and
`m_KeepAnimatorControllerStateOnDisable=false` in the saved prefab.

These are serialized configurations, not the active object graph in the
recording. They do not rule out dynamic creation, another field writer, a
different instance configuration, or animation parameter writes. They do not
establish the global Animator / MonoBehaviour callback order.

Prior evidence, retained unchanged:

- `../visual-low/p11-felt15-blink-local-review-v1/original-blink-inventory.json`
- `../visual-low/p11-felt15-blink-local-review-v1/entry-eye-curve-analysis.json`
- `../visual-low/p11-felt15-blink-local-review-v1/local-review-result.json`

## Actual callable write sites in the original ARM64

All addresses below are ELF virtual addresses in the hash-guarded original
`libil2cpp-offline.so`. These are disassembled code sites, **not observed
invocations on the recorded Felt15 instance**.

| Site | Actual operation | Evidence |
| --- | --- | --- |
| `AutoEyeBlinkInput.LateUpdate` `0x16756d4` | Holds controller pointer at instance `+0x28`; writes controller `EyeOpening` (`+0x1c`) at `0x167582c` (`str s0,[x8,#0x1c]`). | `blink-writer-update-capstone.txt` |
| `0x1675754`, `0x167578c` | Both call original `UnityEngine.Time.get_deltaTime` at `0x16689d8`. Waiting subtracts deltaTime; active progression adds deltaTime multiplied by instance `Timescale` (`+0x20`) to `T` (`+0x30`). | same trace, original CoreModule token bindings in JSON |
| `0x1675814` | Calls original `UnityEngine.Random.Range` (`0x1b507dc`) with the deviation range, then adds Mean when resetting the wait. | same trace |
| `0x16757c4` | Calls `0xbb7160`, then takes `fabs`. The math target has not been bound in this audit; no trigonometric function name is inferred. | same trace |
| `EyeBlinkController.OnLateUpdate` `0x1675a54` | Tests `Behaviour.enabled`, reads Destinations, BlendMode and EyeOpening, then tail-calls the real array `BlendToValue` at `0x1675a88`. | same trace |
| Array `BlendToValue`, mode 2 | Multiplies existing destination `CubismParameter.Value` (`+0x24`) by the EyeOpening input; actual destination store is `0x1675af4`. Modes 1/default take add/overwrite paths. | same trace |
| `EyeBlinkController..ctor` `0x1675bb8` | Initializes BlendMode 2 and EyeOpening 1 together at `this+0x18`. | `adjacent-channel-capstone.txt` |
| `ExpressionController.OnLateUpdate` `0x1676ec0` | Uses deltaTime, computes weights, and writes destination Value at `0x1677184`; its original code has add/overwrite/multiply branches. | same adjacent trace |

With the serialized input **1** and mode **2**, the eye controller preserves
the incoming eye-opening value. That configuration alone does not generate
a closure. The callable AutoEyeBlinkInput code can supply a changing input,
but this audit has no runtime evidence that such an instance ran in Felt15.
The SDK ExpressionController path is distinct from the Animator's face
layer; the presence of its method in the binary is not proof of its use.

## UpdateController order, resolved from original type slots

`CubismUpdateController.Refresh` (`0x1675ebc`) discovers components and
constructs conditional `ICubismUpdatable.OnLateUpdate` delegates. Original
metadata usage pairs bind each tested type; original mscorlib's separately
validated method table binds `Action..ctor` (`0x1ea9cec`),
`Delegate.Combine` (`0x1ec02c0`) and `Action.Invoke` (`0x1ea9cfc`).

The conditional append order is:

1. Fade (`0x1676414`)
2. Pose (`0x16764dc`)
3. Expression (`0x1676594`)
4. EyeBlink (`0x1676648`)
5. Mouth (`0x16766fc`)
6. HarmonicMotion (`0x16767b4`)
7. Look (`0x1676868`)
8. Render (`0x167691c`)
9. Mask (`0x16769d4`)

These addresses are the actual delegate combine sites. Only discovered
components are appended. `UpdateController.LateUpdate` saves parameters if
its parameter store exists (`0x1676a9c`), then invokes its delegate at
`0x1676ab4`. `EyeBlinkController.LateUpdate` returns when
`_hasUpdateController` (`+0x28`) is true; otherwise it directly calls
`OnLateUpdate` at `0x1675bb4`.

Thus Expression precedes EyeBlink within this particular delegate when both
are present. **No serialized UpdateController was found on the inspected
Felt prefabs**, so this order cannot be assigned to the recorded instance
without runtime object/delegate evidence. Generic MethodRef slots used by
AutoEyeBlinkInput.Start and EyeBlinkController.Refresh remain numerically
preserved, not decoded into assumed generic component types.

See `update-controller-type-usage-slots.json`, `delegate-call-bindings.json`,
and the original raw trace for the complete bounded chain.

## Animator, face channels and model transfer

The prior original-resource curve analysis records explicit left/right
eye-opening channels in both body and face clips. In particular,
`face_nayamu` is 1 through 0.533 native clip seconds and reaches 0 at 0.767;
`act_tameiki` has an earlier blink but later returns to open eyes. Those
curve shapes do not by themselves recover the recording's active state,
layer weight, entry phase, or initial low-alpha closure/reopening.
This audit retains their exact source file hashes; it does not substitute
an SDK expression controller for the Animator face layer or install a token.

The original model code exposes a separate transfer boundary:
`CubismModel.OnRenderObject` checks `Time.frameCount` (calls `0x16705a8` /
`0x16705c4`) and calls `CubismTaskableModel.TryWriteParametersAndParts`
at `0x1670600`. That method calls the original parameter/part `WriteTo`
overloads at `0x1670dd4` / `0x1670de4`. Model.Update also has task-read and
parameter-restore paths. This establishes real transfer sites, not the
recording's exact ordering against Animator or every possible parameter
writer. No global order is inferred from script execution order 0.

The prefab's `L2D_Eye` name is not used as blink evidence. Its inspected Init
path sets `CubismLookController.Target` at `0x1b3c0ec`; its SetTargetActive
path calls `GameObject.SetActive`. These selected methods show look-target
setup, not an EyeOpening store. This is a bounded finding, not an exhaustive
absence proof across the executable.

## Remaining discriminating evidence

There is no original runtime trace in this packet. To distinguish writers
without inventing a blink cause, a future authorized original-runtime trace
would need the same model/controller instance identity and frame for:

- Dynamic creation / presence and enabled state of AutoEyeBlinkInput and
  UpdateController, plus the actual delegate invocation list.
- EyeOpening and both destination values immediately before/after eye
  OnLateUpdate; every observed EyeOpening write with its caller/instance.
- AutoEyeBlinkInput T/phase/Timescale and deltaTime if its LateUpdate runs.
- Animator active body/face state, normalized time, layer weight and eye
  parameter values, then values at the model transfer boundary and card alpha.

Until those observations exist, **Felt15 early-blink cause remains unknown**.
This report does not recover its original CSV, sign a replacement motion,
change timing, approve a visible reproduction, or reduce any pending count.

## Integrity and reproducibility

The four original binary/metadata inputs match the earlier inventory's
SHA-256 values and were checked before and after disassembly. `receipt.json`
lists all new evidence files with SHA-256/bytes, the reused source receipts,
the observed repository state, the exact offline commands and verification.
The raw traces are 42,739 and 14,187 bytes, bounded to 24 selected methods
total. Method end addresses are next-indexed-method upper bounds, not
recovered function-size symbols; indirect and unresolved targets stay explicit.
