# Episode3 bilingual before/after image review

**PASS for this bounded visual regression:** no new visible blocker was found on normal `10190004:3→4→22→5`, in JA and ZH. The narration reaches its complete text, the location label completes, empty22 hands off to the same sideways Subaru CG, and the short dialogue completes. The stopped final holds remain stable. This is not original-recording timing, NativeTypewriter formula, acting, audio or whole-episode acceptance.

Both runtime `closure.json` files report browser/CLI/recording/adapter exited with `matches:[]`. I launched no browser, recorder or decoder. Contacts were made from the already extracted JPEGs using Pillow under nice19/CPU0,1.

## Actual coverage

I first viewed original full1280×1000 frames, confirming the entire524×930 stage at `(378,41)–(902,971)` exclusive right/bottom. The top control/status bar is outside that crop and was separately checked in original full frames. Every consecutive10Hz sample in these ranges was then directly viewed through26 labelled contacts, with no subsampling inside the ranges:

| Recording | Consecutive sampled frames | Count | Coverage |
|---|---:|---:|---|
| BEFORE |1691–2217|527|Black preparation, initial ZH warmup, JA restart/full route/Stop, ZH restart/full route/Stop and final hold|
| AFTER |1601–2061|461|Black preparation, initial ZH warmup, JA restart/full route/Stop, ZH restart/full route/Stop and final hold|

`contact-coverage.json` lists every contact's exact first/last frame. All26 listed contacts were viewed. The two locator contacts use every10th sample only to find the region and do **not** constitute complete coverage. Complete coverage comes from the consecutive contacts. These are the supplied10Hz extracts, not all source30fps frames. I did not need further decoding to resolve a blocker and do not accept sub100ms onset/first-glyph/cancellation timing from this review.

Additional original full-page JPEGs viewed: BEFORE1/1800/1950/2025/2097/2120/2122/2160/2217; AFTER1650/1800/1790/1826/1851/1859/1885/2000/2061. The direct originals establish readable final text and visible stopped/ready status; the contacts establish the full sampled sequence.

## Observations

| Item | BEFORE samples | AFTER samples | Result |
|---|---|---|---|
| JA narration3 |Empty panel1940–1947, progressive prefixes1948 onward, final three-line text by2025–2032|Empty panel1764–1765, progressive prefixes1766 onward, final same three-line text1788–1792|Same final glyphs, wrapping, panel placement, background and completion marker; no lost tail or repaint from another line|
| JA location4 / empty22 / CG5 |Location2033–2043; blur then black2044–2058; CG fades in2059 onward; short text2089→2090, final/stopped2097|Location1793–1800; blur then black1801–1814; CG fades in1815 onward; short text1820→1823, final1826|Same sequence and art. Empty22 creates no stray text panel. No old narration appears over the CG|
| ZH narration3 |Restart2098 onward; panel2102, progressive prefixes2103 onward, full text2119–2121|Restart1827 onward; panel1832, progressive prefixes1833 onward, full text1849–1851|Same complete two-line Chinese text and panel wrapping; no clipping or missing punctuation|
| ZH location4 / empty22 / CG5 |Location2122–2129; blur/dark transition2130–2144; CG2145 onward; short line completes2154|Location1852–1859; blur/dark transition1860–1870; CG1871 onward; short line completes1879|Same visible content/transition order and eventual complete line|
| Final stopped hold |Direct stopped status2160 and2217; every stage sample2160–2217 inspected|Direct stopped status1885 and2061; every stage sample1885–2061 inspected|No text continuation/replacement, reappearing previous panel, new gray block or extra actor; completed text/CG intentionally remain visible in both|

The JA final short line is `あ、目が覚めた？`; ZH is `啊，你醒啦？`, both with `？？？` speaker. The JA narration's three lines and Chinese narration's two lines match their respective BEFORE finals. Scene4 preserves its existing JA/Chinese location wording. The stage aspect, alley composition, dark narration panel, light speaker panel and sideways CG crop remain visually consistent.

Prefix histories and hold lengths differ substantially between the recordings. For example, many repeated BEFORE narration prefixes remain unchanged across several samples, whereas AFTER shows a denser progression in this section. I record that visible difference without assigning a cause or converting it into a native speed, Wait, cap or performance verdict. This review does not require identical per-frame prefixes after a clock change.

## Log support and limits

The two `baseline-result.json` files independently record both Episode3 language passes entering exactly3→4→22→5, with real edges31/41/221, naturally reaching `ready`, then `stopped`. Both record empty `errors`, `parseErrors` and `cleanupErrors`. These logs support route identity and final state; their iframe performance clocks were **not** used to force an offset against video frame numbers. The initial Chinese warmup was distinguished visually from the later measured JA/ZH passes.

Images show no old typing paints during the inspected stopped holds. They cannot prove subscription ownership, every cancellation callback or the float32 formula; those require the separate real-clock diagnostics. No conclusion here covers unvisited branches, the whole episode, original source cadence, audio, or all30fps boundary frames. Root retains publication authority and the other episodes' independent reviews.
