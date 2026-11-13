# Next bounded P30 voice candidate: Elsa38

The next existing strong cue candidate after the saved Julius34 is **10450056:38 → `vo_adv_elsa,advg_elza_warai`**, a short laugh waveform. The candidate remains root-unconfirmed and uninstalled. Nodes35–37 are still blank; the historical search has no≥0.55 candidate in their recorded windows, which does not prove silence or absence of a voice.

Current readback is data HEAD471dc375d4da6dd4adca1a753782c35c95e6685c, clean: UID1045005600038, stableKey`s10450056-p30-at0583`, authored native identity, type2, character`live2d/AC_elsa_nomantle01`, voice empty, speaker`エルザ`. JA is `ふふ、さすがね。大技を撃ったあとも、気を抜かずに警戒していたなんて`; ZH is `呵呵，真不愧是你。用过大招之后，还没有松懈，仍然保持警戒。`. Only voice is proposed; no motion/face/command/Wait/offset/gain or other field is changed.

Source binding is retained review/scenes/10450056.json, recording`bili-capital-30`, event`merged-0156`, interval582.999–587.499s. Original video exists at `/home/rikka/Videos/re0/真夜黑兔_Official_王都一日游篇/30 10本篇Ver尤里乌斯 「『最优』的义务」.mp4`. Existing source-frame reference is `/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/ocr/30/root-review/frames/d7d29c63dc09-017610.jpg`; no image was newly inspected. Historical waveform index `../audio/waveform-graphs/p30-d7d29c63dc09/voice-candidate-index.json` and raw `voices-00510.00-00690.00.json` report selected time583.0939/NCC0.980469/active0.4773s from their existing357-cue8kHz search. That search was read, not rerun.

Independent check read only existing source PCM `../p30-bgm-identification-20261113-v1/p30-original-source.wav`,7-second window581–588, and four existing cue WAVs. Exact integer decimation after compensated129-tap low-pass filtering converts48kHz Elsa and32kHz Subaru to4kHz; shared WaveformCorrelation performs local normalized correlation. Five time-separated peaks and signed values are retained for each query in measurements38.json.

| Bounded existing reference | Best absolute NCC | Equivalent cue0 (source PCM seconds) |
| --- | ---: | ---: |
|Elsa `advg_elza_warai`, active0.4775s|0.948993 (+)|583.09425|
|Same complete0.58275s resampled cue|0.948460 (+)|583.09425|
|Elsa `advk_elza_kougeki02`|0.604935 (−)|583.40925|
|Subaru `advg_subaru_douyou`|0.575630 (+)|583.2855|
|Subaru `advk_subaru_kirare`|0.705534 (−)|584.994|

The selected active cue's next time-separated peak is0.516940 at583.9455. Three nonoverlapping pieces give absolute peaks0.946326/0.983508/0.839392 at equivalent zeros583.09425/583.093/583.0955; pieces2/3 have negative best peaks. Thus the short-piece maxima are within2.5ms but are not identical positive-phase alignments. They are retained without upgrading them to exact timing or independent transcript proof. New4kHz and historical8kHz scores are different measurements, not probabilities. No listening, new decoding or bank-wide search occurred.

Original native binding: `/home/rikka/Projects/stella/data/extracted_archives/original/com.sega.stella/files/AssetBundle/assets/vo_adv_elsa.acb`, CueName`advg_elza_warai`, CueIndex/CueId23 → Sequence23 (Type0, one track, PlaybackRatio100) → Track23/Event23 (`07d00400020017000000`) → Synth23 → Waveform23 → Streaming1/StreamAwbId23, mono48000Hz,27963samples. External `vo_adv_elsa.awb` entry23 exists at247232–254496; only table and8-byte header prefix were read, no compressed audio decoded. Existing extracted PCM `data/extracted_archives/limeos/LIMEOS/audio/vo_adv_elsa/advg_elza_warai.wav` has exactly the native sample count/rate and is byte-equal to the retained `../audio/waveform-graphs/p30-d7d29c63dc09/audible-review/native/vo_adv_elsa/advg_elza_warai.wav`.

**Concrete publication prerequisite:** current `story_crowd_data/assets/catalog.json` has no`voices.vo_adv_elsa` bank/cue, and `story_crowd_data/assets/voices/vo_adv_elsa/advg_elza_warai.wav` is absent. Installed binding is therefore false, not assumed. Root can use the existing media path to publish just this cue and its member`LIMEOS/audio/vo_adv_elsa/advg_elza_warai.wav` / intended URL`voices/vo_adv_elsa/advg_elza_warai.wav`, then verify installed bytes against the existing extracted PCM, independently accept the thin draft and test ordinary37→38→39. This package does not install anything.

Two pre-computation failures are retained in exceptions.json: missing published bank lookup, and a mistaken32kHz assertion copied from Julius before measured Elsa48kHz was read. The first numeric attempt never reached correlation; the corrected bounded run exited0 with nice19, CPUs0/1, numerical threads1 and RLIMIT_NICE(1,1). No corruption or external cause was inferred. Original CSV/voice field, trigger phase/start/offset, gain, complete-line speech, listening and whole-chapter acceptance remain unknown/unaccepted.
