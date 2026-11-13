# Julius34 bounded voice identification

**Evidence supports the one-field candidate `vo_adv_julius,advg_julius_kansya` for saved `10450056:34`.** This identifies a matching original cue waveform within the reviewed source-text interval; it does not reconstruct the original CSV, voice trigger phase/offset or audible transcript. `node-fields-draft.json` remains rootfalse and uninstalled.

Target readback: UID1045005600034, stable key`s10450056-p30-at0565p5`, source speaker`ユリウス`, JA`君のおかげで、助かった`, Chinese`多亏你，帮大忙了。`, current character`live2d/AC_julius01`, voice empty. The existing recording binding is565.499–567.999seconds. No new image review was performed.

## Independent local waveform check

Only existing source PCM `../p30-bgm-identification-20261113-v1/p30-original-source.wav` at4kHz, window558–575, and five existing Julius WAVs were read. The32kHz cue PCM was low-pass filtered with a compensated symmetric129-tap filter and decimated8 in memory. The existing `WaveformCorrelation` CPU implementation performed locally mean-normalized absolute NCC; signed peak values are retained too. No video/audio decoding, separation, listening, full-library scan or new audio file occurred.

| Existing cue | Best absolute NCC in local window |
|---|---:|
|`advg_julius_kansya` active0.647s|0.934848|
|`advk_julius_kansya02`|0.201529|
|`advg_julius_hanron`|0.228011|
|`advg_julius_kantan`|0.109289|
|`advg_julius_nattoku`|0.139323|

The selected active cue and its whole0.8485s resampled template both peak at source PCM zero565.88775. Three nonoverlapping pieces0–0.22/0.22–0.44/0.44–0.647s independently give that same equivalent zero, with NCC0.882708/0.948635/0.981493. These are all positive correlations. The selected full-active cue's next time-separated peak is0.106960 at559.623. Five peaks per comparison are retained in `measurements.json`, rather than suppressing competitors. The waveform zero is inside the target text interval, not an authored trigger timestamp.

This independently agrees with the historical8kHz result565.8872/NCC0.931583/active0.6469s. Its already existing357-cue result contains no other≥0.55 match in563–570. That historical search was read, not repeated; the new comparison is explicitly limited to five cues and one17s window. NCC is a signal similarity measure, not a probability or human listening acceptance.

## Original native and installed resource binding

Original `data/extracted_archives/original/com.sega.stella/files/AssetBundle/assets/vo_adv_julius.acb` explicitly maps CueName`advg_julius_kansya`, CueIndex13/CueId13 → Sequence13 (one track, Type0, PlaybackRatio100) → Track13/Event13 → noteOn2000`0002000d`, end0 → Synth13`0001000d` → Waveform13 → Streaming1, StreamAwbId19, mono32000Hz, NumSamples27147, raw LoopFlag1. The selected external AWB entry19 exists; only its table and8-byte header prefix were read. No native decoder/decryption/export was invoked.

Catalog bank`voices.vo_adv_julius` has the exact cue and member`LIMEOS/audio/vo_adv_julius/advg_julius_kansya.wav`, mapped by both `members` and `asset_members` to`voices/vo_adv_julius/advg_julius_kansya.wav`. Its installed mono32kHz WAV has exactly27147samples (0.84834375s), matching the ACB. The selected installed WAV, existing audible-review native copy and extracted original WAV are byte-equal. Cue13 and StreamAwbId19 are distinct IDs; the binding is read from native tables, not inferred from filename ordering.

An aggregate output field initially reused the last piece-loop variable for AWB end. The raw initial JSON is preserved. The selected AWB table end was corrected to106976, with no repeated correlation; `authorCorrection` records the exact change. The reader source now uses a dedicated `selected_end` variable. All reported NCC values are unchanged.

Only `voice` is proposed, guarded by actual UID/stableKey/JA and empty voice plus speaker/Chinese/current character. Motion, face, command, timing, position, gain and other fields are untouched. Root must independently accept/install and verify normal saved playback. Source phase/start/offset, original field text, audible listening and whole-chapter restoration remain unknown/unaccepted.
