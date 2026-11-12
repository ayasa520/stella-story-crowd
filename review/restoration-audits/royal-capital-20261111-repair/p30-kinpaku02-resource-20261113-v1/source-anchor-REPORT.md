# P30 early music anchor: narration2

The measured beginning of `bgm_adv_kinpaku02_cd2_18` lies in **10450056:narration2**, stableKey `s10450056-p30-at0397`, current UID1045005600002. Its Japanese text begins `――白熱するユリウスとエルザの戦闘。`. The existing first-text sample is396.999s and the completed panel remains visible at402.499s. The recording's measurable music rise is around397.59–397.70s. No field or native parameter was authored.

The prepared native-trimmed Opus was decoded once to4kHz mono; the already retained original P30 PCM was reused. Independent8s windows support a common **waveform-zero alignment coordinate396.749s**:

| Recording PCM window | Best reference offset | NCC | Separated runner-up NCC |
| --- | --- | --- | --- |
| 397–405 | 0.251 | 0.986649 | 0.475850 |
| 405–413 | 8.251 | 0.474400 | 0.137870 |
| 413–421 | 16.251 | 0.600556 | 0.135914 |
| 421–429 | 24.251 | 0.822364 | 0.162931 |
| 445–453 | 48.251 | 0.529131 | 0.241860 |
| 477–485 | 80.251 | 0.920900 | 0.187027 |

Reverse queries using reference0–8,8–16,16–24 and24–32s also return396.749s after subtracting each reference start. Their best scores are0.985361/0.493627/0.610631/0.816307. The low-scoring windows are retained, not presented as clean music isolation. `measurements.json` preserves five peaks per query separated by at least1s, competing early overlapping windows and the score at the independently proposed early clock. NCC is not a probability.

**396.749 is not the audible rise or an original play-command timestamp.** The rendered reference begins with a very quiet prefix. In the retained4kHz s16 recording PCM, literal zeros occupy396.699–397.58925s; this observation does not establish a native stop/mute command. The first nonzero sample after that interval is397.58925. With20ms RMS windows stepped10ms, the source crosses−80dBFS in397.63–397.65 and−40dBFS in397.68–397.70. From397.68 onward,20ms source/reference correlations are about0.999 and fitted coefficients are near0.080–0.082; the rise follows the rendered reference envelope. These coefficients are mixture measurements, **not native volume/fade values**. The original LIMEOS WAV's first nonzero sample is0.568073s, at extremely low amplitude; codec/quantization and the source mix prevent treating different first-nonzero thresholds as a new wait. This cue has no998 event;998 semantics in other cues remain unknown.

The source mixture's quarter-second RMS falls from−40.36dBFS at393.5–393.75 to−68.58 at395–395.25,−86.86 at396–396.25 and−98.41 at396.5–396.75. This is an observed mixed-audio decline; the present analysis does not identify a prior track, a native fade-out or an authored silence. `early-boundary-measurements.json` retains the exact sample limits and all20ms onset bins.

I directly viewed the existing title full frame394.999 (`ocr/30/root-review/frames/d7d29c63dc09-011850.jpg`), narration crops396.999/397.999/398.999, narration full frame402.499 (`...-012075.jpg`) and location-caption full frame404.999 (`...-012150.jpg`). The title collage reads `力を合わせて`; the later panel is the three-line narration above the shop background. The actual measurable music rise falls within that narration panel, supporting narration2 as the review anchor. Sampled images do not establish the exact native title-exit/entry boundary or command phase. Paths and current empty `bg_music` guard are in `scene-anchor-review.json`; they are not a field packet.

Clock boundary: original audio is44.1kHz,start0; retained PCM spans1006.67775s versus stream1006.677256s. Root's `../p30-bgm-identification-20261113-v1/audio-timeline-review.json` checked43,354AAC packets and reports no>5ms gaps/overlaps; `source-audio-packet-timeline.json` retains the packet evidence. Thus the early PCM coordinates can be compared with recording time at the documented sample precision. This analysis's search grid is0.25ms, not proof of submillisecond native command timing. Video start is0.023s; no additional23ms shift was applied to the existing image timestamps.

The later discrepancy remains separate:505–513 and520–528s8s windows best-match offsets122.267/137.267, scores0.908815/0.973009, implying waveform-zero coordinate382.733 rather than396.749. At the early-clock offsets their local scores are only0.052832/0.048741. This difference persists with longer templates, so it cannot be dismissed merely as the earlier3s ambiguity. Root's packet evidence excludes the suggested PCM-axis gap explanation. Its actual cause is unknown; no seek, restart, native silence, phase, gain or Wait is inferred, and the early anchor is not extrapolated across that boundary.

All work was offline,nice19/CPU0,1 with numerical worker counts1 and FFmpeg decode/filter/encode1thread. No full-library rescan, source-video decode, browser, formal asset/catalog/story edit, native command installation or Git mutation occurred. The review remains `rootConfirmed:false` and noninstallable; ordinary playback comparison remains root's next step.
