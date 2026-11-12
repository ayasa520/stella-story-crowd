# Node35 end-marker alignment: bounded read-only diagnosis

The saved renderer's left alignment is explained by an existing resource row,
not by an incorrect node type. No native field, text, type, shared asset or
production source was changed during this investigation.

The sealed source witness is
`../p30-choice26-and-ending-source-review-20261113-v1/ending/frame-0055.jpg`:
the ordinary narration box centers`―完―`. The sealed actual witness is
`../p30-ending-normal-runtime-20261113-v1/ending-frames/frame-00111.jpg`:
the marker starts at the left text inset. The prior ending review already
records this gap and excludes alignment acceptance. No new image work was
needed to diagnose the code path.

## Actual path and the precise current value

The retained normal `characters-result.json`, `programs[0].suffixNodes`, gives
node10450058:35 as kind`text`, speaker`""`, text`―完―`, translation`——完——`,
model`""`, character_image`""`, title_mode`""`. Numeric native type1 remains
correct TEXT/narration. Canonical `lib/native.ts:20` and `lib/preview.ts:35`
plus `config/semantics.json` establish that mapping; it does not dispatch
NativeTitle.

All canonical paths below are under
`artifacts/stella-site-repair-source/.sites-checkout/`:

1. `public/player/player_scene.js:136` loads the configured asset manifest.
   `public/player/player_config.json:2` names`/player-assets/manifest.json`;
   its`:15` maps narration to`adv_tell_system`.
2. The reviewed adapter's `serve.py:154` maps that URL to the actual retained
   `story_crowd_data/assets/player/manifest.json`.
3. `OriginalScene.prepareText`, `player_scene.js:162–180`, selects narration
   at`:168` when `node.speaker` is empty. It constructs `panel.rows` directly
   from `assets.groups[group]`, prepares native font layouts and glyphs.
4. That group's text row is `/adv_tell_system/anim_root/txt_tell`, id739,
   rect`(140,215,800,150)`, alignment513(`0x201`), font GUID
   `2e9342cddd60d334bbf5ea96d148f7a4`, base40/min24/max36. The extractor
   `story_studio/player_assets.py:101` reads TMP alignment using the recorded
   serialized offset in `story_studio/config/player_assets.json:113`.
5. `NativeFont.draw`, `player_scene.js:109–115`, already uses the low byte for
   horizontal alignment and high byte for vertical alignment.513 is
   middle-left: x starts at rect.x140.514(`0x202`) preserves vertical middle
   and computes x as`140 + (800 - measuredLineWidth)/2`.
6. `OriginalScene.draw`, `player_scene.js:190–200`, draws the prepared
   `panel.rows`. There is no per-node effective-alignment resolver or layout
   diagnostic log in this path today.

There is no explicitly declared ADV alignment field in the current native
scenario fields/`native_repair` STRING_FIELDS, nor an alignment projection in
`compilePreview`. Generic unknown-key storage is not an execution mechanism.
`prepareText:167` expressly rejects every`<...>`rich-text tag, so adding an
invented`<align=center>`to either retained language string is not supported.

## Bounded native API evidence and limits

Offline metadata and existing CSharp method pointers resolve these inspected
methods in `data/libil2cpp-offline.so`:

| Method/token | RVA | Bounded native observation |
|---|---|---|
|TextPanel.Open /0x06003e4c|0x1685c60|Initializes the selected panel and forwards name/message to SetText or PlayText|
|TextPanel.Init /0x06003e53|0x1685dc8|Initializes object/arrow/trigger state; no inspected alignment change|
|TextPanel.SetText /0x06003e4d|0x1685e80|At0x1686014–0x1686024 loads mText(+0x28), forwards original message argument and calls TMP set_text|
|UIController.SetCurrentTextPanel /0x06003f73|0x1688fbc|Forwards the supplied name/message to TextPanel.SetText|

The `Unity.TextMeshPro.dll` code-generation module has method count1452 and
table`0x2f140d0`; metadata token0x06000304 resolves TMP_Text.set_text to
`0xfcd9bc`, matching the actual SetText call. Native TMP also exposes
set_alignment(token0x06000337,RVA`0xfce91c`) and
set_richText(token0x06000356,RVA`0xfcf044`). These are component APIs, **not
evidence of an ADV JSON field or a recovered P30 command**.

No alignment setter/change was found in the four bounded caller bodies above.
This does not prove that every native caller or TMP rich-text path lacks a
runtime policy. The lost P30 raw CSV, any original alignment markup/spacing
and exact cause of the original centered marker remain unknown. Only the
original visible centering and the current deterministic left-aligned path
are established. No managed/native application code was executed: metadata
read and LLVM disassembly only, nice19/CPU0,1, no dependency installation.

## Narrow next change supported by the evidence

Use a source-backed **presentation profile**, owned by player configuration
and an independent resolver, with exact selector`node.id=10450058:35` guarded
by kind`text`, empty speaker and the expected narration txt_tell resource row.
Do not select a policy by comparing the string`完`, infer all anonymous text
should center, or add a new native field.

The resolver can return a copied selected row whose horizontal bits change
from1 to2 while its vertical bits remain512. Put that copy in this panel's
`rows` before layout/draw; leave the shared native manifest row513 and other
panels/nodes untouched. The existing font layout/draw already supports the
necessary centered x calculation, so it needs no new font renderer, string
padding or changes to the shared drawing defaults. Node35 keeps its existing
type, source/translated text, IDs, card lifecycle and ending continuation.
The profile must say source-backed/authored presentation, not original CSV
recovery. This is a proposed policy, not an implemented or runtime-passed fix.

A single preparation-time layout record is sufficient for the next necessary
QA: node id, language, selected profile, group, row path, native/effective
alignment, rect, resolved size, line count and measured line widths. Emit once
per node/language/profile rather than per glyph/frame; no getComputedStyle
sampling or new observer framework is needed. Existing `text_ready` and
`STORY_PLAYER_ENTER` logs identify timing/kind but do not contain that layout
selection. Root can compare the next ordinary source/actual marker position
after applying a separately reviewed source patch.

Diagnosis shared directly with `/root/p30_felt_entry_review`, who owns the
separate source-only patch proposal. Old source/runtime reports remain sealed.
No Chrome, decoder, server, compiler, formal data/source or Git mutation.
