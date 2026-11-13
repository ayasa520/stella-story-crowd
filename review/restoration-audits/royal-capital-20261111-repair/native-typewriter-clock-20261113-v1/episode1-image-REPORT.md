# Episode 1: bounded before/after typewriter image regression

**Pass for the reviewed JA/ZH route.** Both recordings visibly reach the same complete dialogue, choice, selected reply, following dialogue, blank transition, and child/dragon-carriage CG. No new missing glyph, clipped final paragraph, duplicate choice, or previous-node/language text contamination was observed. This accepts a limited display regression, not original-game typing cadence or a complete episode.

The route is `10010001:5`, existing branch `1009` to `6`, then `8 → empty 9 → 10`. Both languages were directly reviewed. The retained normal-driver results independently report the expected five enters per language, the selected existing edge, natural completion, no overrides or clock-rate mutation, and no runtime/parse/cleanup errors. Those logs support route identity; they are not a replacement for viewing the images.

## Direct image coverage

- Before: every existing 10 Hz sample **201–880**, nominal recording **20.0–87.9 s**, viewed in order on **29** continuous contact pages.
- After: every existing 10 Hz sample **121–1080**, nominal recording **12.0–107.9 s**, viewed in order on **40** continuous contact pages.
- Total: **1,640 directly viewed sampled frames**, including preparation and repeat holds inside these bounded windows. Contact manifests list the exact indices; all 69 continuous pages were opened directly. Three coarse overview pages were used only to locate the case and episode boundary.
- Original 1280×1000 rechecks: before `1, 200, 469, 699, 794`; after `183, 200, 519, 977, 1075`. These include the whole browser viewport, confirming the story crop `(378,41,902,971)` retains the full 524×930 story stage. Contacts resize that stage to 262×465 without changing its aspect ratio; original files remain untouched.
- No browser, new decode, original 30 fps boundary extraction, source edit, formal-data edit, or Git operation was performed. Root's two closure receipts were read before image work; both report browser/CLI/recorder/adapter exited and empty process matches. Existing decoded JPEGs alone were used, with contact generation under nice 19 / CPU 0,1.

Times below are sample labels `(frame−1)/10`, relative to each recording. They are **not** mapped to `performance.now`, native command times, or a shared before/after origin.

## Observed sequence

| Visible boundary | Before frame(s) / seconds | After frame(s) / seconds |
|---|---|---|
| JA node 5 complete, then choices | 468–469 / 46.7–46.8 | 182–183 / 18.1–18.2 |
| JA selected left reply | 573 / 57.2 | 189 / 18.8 |
| JA node 6 complete | 623 / 62.2 | 234 / 23.3 |
| JA node 8 complete | 655 / 65.4 | 270 / 26.9 |
| JA blank, then node 10 complete | black 679–690; complete 699 / 69.8 | black 323–458; complete 519 / 51.8 |
| JA Stop / restart boundary | black 703–709, then new blurred street 710 | black 575–590, then new blurred street 591 |
| ZH node 5 complete, then choices | 741–742 / 74.0–74.1 | 765 / 76.4 (complete paragraph and choices visible) |
| ZH selected left reply | 753 / 75.2 | 778 / 77.7 |
| ZH node 6 complete | 794 / 79.3 | 977 / 97.6 |
| ZH node 8 complete | 818 / 81.7 | 1017 / 101.6 |
| ZH blank, then node 10 complete | black 840–851; complete 858 / 85.7 | black 1058–1067; complete 1075 / 107.4 |
| Host replaces completed case | 862 onward, host clear by 864 | 1079–1080 / 107.8–107.9 |

Prefixes progress coherently to the same final paragraphs in both versions. Node 5 retains its three-line layout and choices after completion; node 6 retains two lines; node 8 remains the short final Subaru line. Node 10 has the child name and complete `うわーっ!!` / `哇啊！！`, with no Subaru text left over. The blank transition contains no visible placeholder or stray glyph. The later language starts with its own fresh paragraph, and the final host replacement has no visible story text left over. An unchanged canvas may remain during Stop before the normal reset; immediate canvas clearing is not claimed.

The JA paragraph is identical in the original-size before/after choice rechecks. **JA choice labels and selected reply are Chinese in both versions** (`四处探索`, `向人打听`, `先到处逛逛吧！`). This is a retained bilingual-content gap, not newly introduced by the clock change; this review does not accept it as faithful Japanese source content.

After contains visibly longer black/dim/partial-text holds in places, including the JA black interval above and ZH node 6 retaining `看起来，这是` across many sampled frames. Before also has prolonged partial-text holds. The recordings do not establish a common engine/video clock or the cause of any hold. These observations do not attribute a stall to the typewriter, renderer, GPU, observer, or installation state, and do not justify a Wait or curve change. They also do not demonstrate smooth native cadence.

## Limits

This is a before/after, 10 Hz visual regression of one existing selected route in two languages. All original 30 fps frames, exact first-glyph timing, per-frame prefix equality, native rate/cap arithmetic, skip/cancellation callback internals, audio, acting, face/extras, geometry fidelity, unselected branches, and whole-episode/chapter restoration are **not accepted here**. Separate actual rate/cap/cancel QA remains necessary. No additional capture is requested by this report.
