# P31 audio review, 2026-11-21

This is an offline resource-identification review. It does not certify a complete
part, original script command phases, subjective listening, or saved-player
transport. No browser or formal data edit was performed by this reviewer.

## Node 9 voice

- Current target: scene `10040043`, scenario `9`, stable key
  `s10040043-p31-at0291`; the saved `voice` was empty at review start.
- Resource: `vo_adv_ricardo,advk_ricardo_kougi`, WAV SHA-256
  `35d8cd6523383045ab55aac5a1537abe054a95e9de47086341b02d65ab9a0881`.
- The historical 8 kHz matcher and newly decoded original recording agree on cue
  zero `291.2615 s`. Fresh signed Pearson correlations at 4/8/16 kHz are
  `0.996854686`, `0.994942585`, `0.994879973` respectively.
- All 35 other shipped Ricardo cues were searched in the same 288–300 s
  recording window. The highest competing signed score is `0.294241212`, at
  297.455 s. Restricting competing cue-zero times to 291.0–291.8 s gives
  `0.191659866`. These are measured similarities, not probabilities.
- The neighboring saved dialogue anchors are node 8 at 288 s and node 10 at
  299 s. Independent visual reviewer `p31_source_review` directly inspected
  `node9-at291p30.jpg`: Ricardo is visible, the panel names `リカード`, and the
  text has started `うおい！`, with no prior card or choice overlay remaining.
- The waveform and current-card witness support this **short interjection**
  resource binding. They do not establish full spoken dialogue or original
  command phase. `node9-voice.packet.json` is provided for root approval and
  normal importer use; root owns its approval flag and subsequent playback.
- There was no callable subjective listening/transcription tool in this review.
  `subjectiveListeningPerformed` remains false. The original source excerpt and
  cue are already available under the prior `audible-review` directory.

Reproduction and detailed controls: `verify_cue.py`, `measurements.json`. The
fresh recording decode covers 288–300 s, rather than reusing a historical clip
as the signal being validated.

## Ending music

Freshly decoded original recording: 815–834 s. Original WAV references were
used, with effects and reward sounds retained in the source. No separation or
generated replacement audio was used.

The previous track is `bgm_adv_every03_cd2_11`: a clean 816–817 s source query
matches reference time 169.310 s with signed correlation `0.997108210`.
This decoded reference contains extra loop repetitions; folding the reference
time by the existing native metadata gives approximately 45.311338 s. The
reference alignment is an analysis coordinate, not a saved node music offset.

The measured old-track gain is approximately 0.113 through 820 s. It falls to
0.07944 in 820.50–820.75 s, 0.04239 in 820.75–821.00 s, and 0.02466 in
821.00–821.25 s, while signed correlations in those windows remain above 0.94.
From 821.25 s onward the old reference no longer correlates consistently with
the recording. Thus the old music is still present after Ricardo's visual
exit at 819.887 s and through the door's first complete frame at 820.521 s.
A reconstruction that stops old music before the door would contradict this
evidence. This does not recover a literal STOP command or native fade value.

The CLEAR music is `bgm_btl_adv_win01`. Matching reference 0.25–5.25 s to the
recording gives cue zero approximately **826.66275 s**. The overall signed
score is 0.78063 because the source gain changes during the opening; the
constant-level 828–830 s interval gives signed correlation 0.90719 and gain
0.07199. Quarter-second windows after 827.5 s generally give correlations
0.87–0.98. The independently witnessed CLEAR background begins 826.387 s and
the full text is visible 826.987 s. The measured music cue zero falls between
those visual events, about 0.276 s after the background first appears.

These are recording measurements. They do not prove an original field,
command phase, exact fade duration, or native wait. If root reconstructs
playable ending commands, their authored status and these limits must remain
explicit. BGM identity is supported; no new BGM field packet is proposed here
because assignment and command timing belong to root's ending reconstruction.

Detailed values: `ending-music-measurements.json`; reproduction:
`verify_ending_music.py`. A 16 kHz source excerpt is retained as
`source-ending-815-834.wav`, SHA-256
`a9e31a511efe4e5febc83353c2345a935c833902f680d7edb703681f81fcd7e6`.

All new decoding and NumPy work ran at nice 19 on CPUs 0 and 1, with one FFmpeg
thread for decoder/filter/encoder and one BLAS/OpenMP thread. No formal data
was written or committed by this reviewer. Only evidence files in this review
directory were added; root retains responsibility for verification and publish.
