# P33 ending audio identity and overlap

Reviewer `/root/p31_route_evidence` freshly decoded source560–580s and original
WAV references at4kHz mono, under nice19/CPU0,1 and single FFmpeg decoder,
filter and encoder threads; BLAS/OpenMP were limited to one thread. The ARM
`.venv-video-ocr` interpreter was verified as aarch64 before its NumPy use.
`verify_p33_ending_music.py` adapts the retained P31 review's signed-correlation
procedure but uses this recording's own source, candidate identities, alignment
and measured envelopes. No P31 timing or gain curve was transplanted.

The old track is **bgm_adv_comical02_cd2_09**. The fresh recording566–567s query
matches original reference146.3385s with signed correlation0.998739. This is
a reference coordinate, not an authored playback offset; the original decoded
reference contains loop repeats. Quarter-second fitted gains remain near0.050
through567.5s, then fall to0.0460 at567.5–567.75,0.0332 at567.75–568,0.0252 at
568–568.25,0.0102 at568.25–568.5 and0.00276 at568.5–568.75. Reference correlation
ceases to support the old track after568.75. A low correlation alone is not
proof of silence, but the prior strong match and declining envelope do prove
that the old track survives the final Felis exit and overlaps the first white
door frames. A hard stop before the movie contradicts the source. No original
STOP literal, phase or precise fade duration is recovered.

The CLEAR cue is **bgm_btl_adv_win01**, original WAV SHA-256
13d0882fe95186594df852bb5e68a00fb5e5fd7eb6e4784db653c5be01577c53.
The0.25–5.25s template aligns cue-zero **573.96975s**, signed correlation0.747743
over the changing opening gain. Independent reference windows1–2s,2–3s,3–4s
all produce exactly the same cue-zero (correlations0.881502,0.863001,0.632478).
The575–576s interior window gives0.880021. Other same-context references
bgm_btl_win01,bgm_btl_adv_lose01 and bgm_adv_every03_cd2_11 score only0.06183,
0.05648 and0.06466. Scores are similarities, not confidence probabilities.
The new cue starts between the directly reviewed CLEAR montage first visible
at573.690s and readable text574.256s. Fitted gain grows from0.00598 at574–574.25
to approximately0.044 by575s; these are video measurements rather than authored
native gain values or exact fade arguments.

The original **adv_dive01_out** audio also matches: its1.25–4.75s template gives
signed correlation0.939798 and cue-zero568.19225s. Three independent resource
windows1.25–2.25,2.25–3.25,3.25–4.25 all return that same zero with correlations
0.923036,0.939862,0.967959. This confirms the audible resource identity, alongside
the complete150-frame visual resource review. Its audio alignment is0.33625s
later than the first fully white source frame567.856s. The cause of that AV
coordinate difference is **not established**. It must remain explicit; the
white-frame witness is not permission to claim a frame-exact native movie-init
time, and no delay/trim/sync correction is proposed to hide the difference.

The retained16kHz source excerpt `p33-ending-source-560-580.wav` has SHA-256
d6e60a2e7ceb4798dee94584bfeb1eaf434530f9bad73466a62b64fc11a14b8a.
Detailed alignments, envelopes, hashes and controls are in
`p33-ending-music-measurements.json`. No subjective listening/transcription was
available, so `subjectiveListeningPerformed:false` is retained. No browser,
formal data edit or original-command/phase recovery is claimed.

The ending-sequence draft now accepts the movie and win01 **identities**, with
its phase0 default fade / phase2CardOut / plainwin01 choices still explicitly
authored and root approval pending. Saved continuous playback must observe
old-track overlap, complete movie end, independent CLEAR then own END chart;
resource identity alone does not accept the timing or current player output.
