# P42 scene10430012: fresh normal snapshot passed, root approval remains false

The 34-character candidate was freshly rebound at formal data HEAD
`f8a8441229ef579400830d117b31cbd43a30a26e`, canonical HEAD
`7f32a3cde97d9a379828619242d2ba12f94f6514`. The five pending files belong to
root's separately approved P43 scene10490016 batch `392fc8b485f75909c108`.
Their exact status and current SHA values are preserved in `preflight.json`.
Global clean status was not required, and this task did not modify those files.

`prepare.py` directly instantiated the existing normal `InstalledSnapshot`.
The original reader, JSON parser, constructor and ownership guards were used.
A code-object-scoped `sys.settrace` observer read the constructor's local byte
receiver immediately before each original `json.loads` call. No implementation
was replaced. A future parsing failure would retain the exact receiver bytes,
file path, SHA, exception position and traceback, then propagate normally.

This normal constructor succeeded for 121 owned scenes: 121 native files,
121 review files, manifest and ownership, totaling 244 observed JSON receivers.
`normal-snapshot-read-receivers.json` records every receiver and implementation
digest. `unchanged_on_disk()` also passed after target checks. No stage, normal
node-fields mutation gate, install or browser was invoked.

## The earlier failure remains preserved and unexplained

The original evidence is untouched at
`../p42-next-scene-preflight-20261121-v1/first-attempt-failure.json`:

```text
JSONDecodeError: Expecting property name enclosed in double quotes:
line 53010 column 23 (char 2739956)
```

That constructor did not retain the failing path or byte receiver. Their exact
identity cannot be recovered from the preserved exception. The old narrowed
candidate `review/scenes/10040001.json` must not be promoted to the observed
original failure input. Its current 4,157,168 bytes, SHA
`13b23235b7734c3bee3224a0b4e245573192ab9bef92f01155e97a4debbfc8a9`, match
the v1 subsequent diagnostic and current committed blob exactly. This time
those same bytes were observed going into and successfully through the normal
constructor's JSON parser. This passes the fresh normal-read prerequisite;
it neither reproduces nor explains the unretained old failure. No cause is
attributed to P43 pending edits, cache, installation or any writer.

## Character-only scope and route

The immutable source package and independent audit remain unchanged. The
fresh proposal has these 34 fields:

| Original model | Character fields |
| --- | ---: |
| `live2d/AC_rom01` | 3 |
| `live2d/AC_subaru01` | 5 |
| `live2d/AC_elsa_nomantle01` | 13 |
| `live2d/AC_emilia01` | 3 |
| `live2d/AC_pack01` | 10 |

All 65 prior resource/source guards were rehashed, including 34 original
frame witnesses, 15 installed/original model payload pairs, and the existing
P42 recording. The five model catalog entry digests still match the audit.
No new video decoding, frame extraction or visual acceptance occurred here.

After the normal snapshot succeeded, the normal `snapshot.node` identity
lookup checked each source row. A disposable copy passed existing
`validate_document` and `validate_resources`; its exact differences are the
34 requested `character` fields. IDs, authored order, text, motion/face,
commands, voices, branches/transitions, all non-character fields and review
objects remain unchanged. Excluded node24 stays unchanged: its ice-foot
illustration is outside this character package. Node6's stage actor is Elsa;
node19's stage actor is Rom. Neither is replaced by a Subaru response portrait.

`runtime-plan.json` retains the exact observed route:

- Start scene10430012 at root scenario1, native UID1043001200001, actual Studio
  fallback ID `node:10430012:1043001200001`.
- Visit all 38 nodes in order with 37 internal transitions.
- Choose node6/branch62 `关于重量`; node6/branch63 `关于准备` stays unresolved with
  an empty transition list.
- Choose node19/branch193 `祈祷`; node19/branch192 `焦急` stays unresolved with
  an empty transition list.
- Node38/branch381 keeps its existing FINISH to section1043/scene10430013,
  native root sentinel0. The destination exists and its actual root is1.
  A later bounded saved-state capture stops before entering that next scene.

All approval flags remain false. This is a read-only preflight and proposal,
not an installable or executed stage. It grants no motion, expression, FX,
geometry, timing, voice/BGM, saved playback, unseen branch or whole-scene
acceptance. Root alone can approve fields and run the normal publication path;
global metadata and ownership must be freshly checked again at that time.
