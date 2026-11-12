# Independent source-only review: PASS, runtime alignment pending

Reviewed the author's final sealed
`../p30-end-marker-alignment-proposal-20261113-v1/production.patch`, README,
author-receipt and all four proposed files. No blocking source finding was
identified. This is permission to consider the reviewed source change within
root's workflow, not a browser release, application, deployment or visual pass.

The before copies of the two existing files match the selected current
canonical files. The author's observed Site base is
`817a45f6a24599743cb6ce48028875ee0e1396ba`. The unified patch changes exactly:
`public/player/player_scene.js`, `player_config.json`, new
`text_panel_presentation.js`, and new `text-panel-presentation.json`.
No native data, compiler, font implementation, shared player manifest, legacy
`public/studio` renderer, type/text/command/timing or ending connection changes
are in that patch. Root owns any later base refresh/application/publication.

## Selection and immutable metadata

The only configured node key is10450058:35. It requires kind`text`, exact empty
speaker, narration group`adv_tell_system`, unique path
`/adv_tell_system/anim_root/txt_tell`, text row id739, and original alignment513.
The policy is not selected by Japanese/Chinese wording. No new ADV field or
invented CSV/rich-text syntax is introduced. Invalid configuration or changed
profile guards throw through the existing scene preparation/setup failure
path; they do not silently apply a fallback or mutate the original resource.

The selected array is recreated with `rows.map`; only the selected row is a
spread copy. It overrides alignment with `(old & ~0xff) | 2`, so513 becomes514
while vertical512 and all other bits remain. Every other property, including
rect/font/color/sizes/spacing, is retained. Other rows retain their original
objects, and unprofiled nodes return the original rows array unchanged. This
does not mutate the shared manifest or carry514 into another narration.

`OriginalScene.prepareText` places those effective rows in `panel.rows` before
layout; `OriginalScene.draw` consumes the same panel rows and associated
layouts. Each Japanese/Chinese preparation resolves afresh against native
`assets.groups[group]`, so language changes do not accumulate overrides.
The existing `NativeFont.draw` already centers horizontal2; it is unchanged.
Native type1/text remains correct, and the source panel/actual marker gap is
exactly the sealed evidence identified by the author. Original P30 CSV or
markup ownership remains explicitly unknown; this is an authored presentation
profile backed by the observed source, not a recovered native field.

## Resource route and ordinary consumers

`player_config.json` adds `/player/text-panel-presentation.json`, and
`OriginalScene.setup` awaits the existing `readJSON` path before text use. A
missing/error response therefore fails setup with its URL/status instead of
using an undefined policy. The helper import is relative to player_scene.

The normal adapter's `serve.py:188` reads `/player/*` from the canonical public
root. The production framework already uses that public static tree; no app
route intercepts `/player`, and package build does not call vendor-player.
The one-time vendor-player bootstrap also refuses an existing player.js, so
it is not a build-time overwrite of these files. No dependency is added.
`playerConfigAt` only revision-pins `/player-assets/*.json`, leaving this new
application presentation JSON in its intended source/config ownership. The
separate `/player-assets` API remains the original shared manifest provider.

These are source/path compatibility findings, not a new build or HTTP test.
Root still needs its actual build/static-resource and ordinary playback checks.

## Diagnostic scope and cleanup

`STORY_TEXT_PANEL_LAYOUT` is emitted after layout from the existing row/layout
values: node/language/profile/group/path/id, native/effective alignment, rect,
size, line count and measured line advances. Defaults also report513. The
logger does not read a clock, recompute glyphs, draw, wait, sample pixels,
schedule RAF/timers or register an observer. Its Map stores a last signature
per node/language/profile/row, suppresses identical repeated preparation and
is cleared by scene.clear. No external listener or wrapper needs disposal.

The policy failure path validates before returning any copied rows; the
diagnostic runs on the same successfully prepared row paths/layouts. It does
not hide a layout error or alter text reveal state. As with existing logging,
unexpected console/serialization exceptions are not given a new fallback;
no new behavior is claimed for those external failures.

## Verification and practical limit

Independent `/usr/bin/node --check` passed for both final JS files. Both final
JSON files parsed, and the exact configured selector/value was inspected.
The complete unified diff was read. No module body, mock, unit test, compiler,
server, native runtime, browser or media decoder was executed. No production
source/data/Git mutation occurred.

Next root-owned actual QA should cover35 Japanese/Chinese, its34 predecessor
and36→37 ending continuation, plus an unprofiled ordinary narration control.
Use the actual layout logs and source/actual pictures to decide alignment;
this static pass accepts neither runtime centering nor exact geometry/timing,
acting, audio or whole-episode restoration. No replay outside that necessary
bounded QA is requested by this review.
