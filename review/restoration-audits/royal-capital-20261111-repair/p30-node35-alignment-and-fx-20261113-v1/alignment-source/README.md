# End-marker alignment: source-only proposal

**Not applied or executed.** Root remains the only production writer and browser owner. The four-file unified [production.patch](production.patch) is relative to the canonical checkout `/home/rikka/Projects/stella/artifacts/stella-site-repair-source/.sites-checkout`, observed at817a45f6a24599743cb6ce48028875ee0e1396ba. Exact original copies of the two existing files are retained under `before/`; all proposed files are under `proposed/`. No formal native/review data, shared asset manifest or canonical source was modified.

The full original/actual ending review identified a concrete mismatch: original [source55](../p30-choice26-and-ending-source-review-20261113-v1/ending/frame-0055.jpg) centers「―完―」inside ordinary narration, whereas [actual111](../p30-ending-normal-runtime-20261113-v1/ending-frames/frame-00111.jpg) uses the left inset. The bounded native/current-renderer diagnosis is [p29's report](../p30-node35-text-alignment-investigation-20261113-v1/REPORT.md). Native type1/text, empty speaker and existing ending text stay intact. The original P30 CSV/markup mechanism remains unknown; this is a **source-backed authored presentation profile**, not recovery of an original alignment field.

The patch changes four application files:

- `public/player/text-panel-presentation.json`: one explicit profile keyed by `10450058:35`, guarded kind`text`, speaker`""`, group`adv_tell_system`, exact text path/id739 and exported alignment513. It requests horizontal2; no content-string selector is used.
- `public/player/text_panel_presentation.js`: independent policy resolver and preparation diagnostic. Only the matching row is copied; `(alignment & ~0xff) | 2` preserves vertical512 and produces514. Its rect/font/size/spacing and all other fields remain intact. Unprofiled nodes use their original rows. Layout and draw share the same effective panel rows.
- `public/player/player_config.json`: one static application-resource URL, `/player/text-panel-presentation.json`.
- `public/player/player_scene.js`: import the resolver/diagnostic, load that configuration during existing scene setup, select effective rows before layout, and report prepared layout. A per-scene Map suppresses repeated identical preparation records and is cleared by `scene.clear()`.

This follows existing `readJSON` loading and application presentation-policy separation. `/player/*` is already served from canonical `public/player`; `playerConfigAt` revision-binds only `/player-assets/*.json`, so this presentation JSON remains application configuration. The legacy `public/studio` renderer is not modified. NativeFont's existing center calculation is reused; no font-renderer branch, new native field, rich-text tag, space padding, Wait, command, phase, duration, node type or wording change is proposed.

The diagnostic API for root's next **normal, no-override** capture is:

```js
console.info('STORY_TEXT_PANEL_LAYOUT', JSON.stringify({
  node, language, profile, group, rowPath, rowId,
  nativeAlignment, effectiveAlignment, rect, size, lineCount, lineWidths
}));
```

For35, `profile` is `p30-ending-marker-source-centered-v1`, group`adv_tell_system`, rowPath`/adv_tell_system/anim_root/txt_tell`, rowId739, nativeAlignment513 and effectiveAlignment514. Unprofiled controls use `profile='native-default'` and unchanged native/effective alignment. `nativeAlignment` means the actual exported manifest value, **not** an observed Unity runtime setter. `rect` retains x/y/width/height/scale_x/scale_y; size is the resolved font size and lineWidths sum the already prepared glyph advances. The logger reads no clock, measures no new glyph, schedules no callback and adds no draw/advance/random call. Repeated identical preparation for one node/language/profile/row is suppressed; changed metadata is logged anew. There is no per-frame polling or private wrapper.

Syntax-only `/usr/bin/node --check` passed for both proposed JavaScript files under nice19/CPU0,1. Both JSON files parse; the two `before/` copies match the current selected canonical files byte-for-byte. No module body, compiler, mock, browser, server or unit test was run. Syntax does not establish visual correctness. Root must independently review/apply, then compare ordinary34→35 in Japanese and Chinese, door36→CLEAR37→completion, and an unprofiled ordinary narration control before accepting the alignment.
