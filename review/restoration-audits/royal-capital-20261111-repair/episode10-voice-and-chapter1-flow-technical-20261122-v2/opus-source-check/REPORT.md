# P30 voice58/6 Opus versus accepted cue PCM

One authorized local Opus decode completed naturally to EOF: exec chunk `3d6f68`, exit0; decoder PID/PGID25931, supervisor PID/PGID25930. Both streams reached EOF, no forced stop or retry. A later OS read found both PIDs and process groups absent and no FFmpeg process. Full 839 B stderr and original argv are retained.

The compressed preview is quantitatively consistent with the accepted `vo_adv_julius/advk_julius_emilia` cue. Original pinned `read_pcm`, 129-tap Hamming/sinc1800Hz `to_4k`, and `measure` definitions were reused; NCC uses the unchanged `WaveformCorrelation` CPU module. The original WAV active/whole signed NCC values were reproduced exactly (0.9913230675051048 / 0.9863980569267277). At4k both cue arrays contain3279 samples; their whole-cue signed NCC is0.991505774437285 at lag0.

In the existing source PCM window811–818s, decoded Opus active/whole signed NCC is0.9819307649091797 / 0.977041476092342. Both whole cues, both active cues and all three disjoint898-sample pieces peak at the same cue-zero coordinate812.39275s (window-relative5571 samples at4k). All five original source-search peaks, signs, template counts and lags remain in measurements.json. These coordinates identify waveform content; they are not authored trigger offsets.

Full natural-EOF Opus PCM is39346 samples at48000Hz versus original WAV26230 at32000Hz. This is one48000Hz sample more than the rate-scaled39345 count (difference1/48000s); cause remains unknown. No retry, truncation, padding, alternate resampler or codec experiment was performed. Raw PCM78692 B is preserved as a61040 B exact gzip, with uncompressed SHA256 and gzip readback proof.

The unchanged original five-peak reducer was also used on the direct whole-cue comparison, which has only one possible lag. Its four later absolute-score-zero placeholder rows are retained; they are not four more matches.

All original inputs, tool and algorithm files are exact before/after/final. No listening, source-video decode, browser/API, original CSV/phase/offset/gain recovery, codec-quality acceptance or whole-scene acceptance occurred. Raw measurements leave root identity review pending; the identity statement above is the metadata author's inference from the measured content comparison. Root decides acceptance/publication.
