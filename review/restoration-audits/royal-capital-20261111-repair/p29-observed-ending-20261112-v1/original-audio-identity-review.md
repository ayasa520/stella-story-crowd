# P29 ending audio: cue identity established by waveform, phases unconfirmed

This review advances the ending audio evidence: **the CLEAR/ending-chart mixture contains `bgm_btl_adv_win01` from its introduction, with an approximately one-second rising envelope; the preceding music is `bgm_adv_fuon02_cd2_14` and falls over approximately one second. The complete door resource's audio is also present.** These are waveform-supported resource/envelope findings. Meaningful listening was not performed: no audio-listening/playback or transcription tool was available in this agent's tools. No auditory acceptance, native command-phase recovery or formal installation is claimed. `cue-proposal-unconfirmed.json` retains that boundary.

No browser, dependency installation, formal data/source/Git write or full-chapter extraction occurred. Existing ARM `.venv-video-ocr` supplied NumPy without modification. All processing ran nice19 on CPU0,1, with BLAS/OpenMP threads1; FFmpeg input decoder, audio encoder and filters explicitly used one thread. Scripts, exact requests, stderr, derived PCM and numeric results are retained here.

## Reused evidence and bounded new comparison

The full original-tail review already covers all570 frames739.021–757.987 and the complete native door resource. This task reused its evidence, then directly re-viewed existing source contact pages03,04,06,07 and native-door page01 for timing context; it did not repeat the full visual review or decode new images.

The old three-second CLEAR candidate0.8819 was not the strongest retained evidence. Existing `audio/waveform-graphs/endings/p29-ending-1/clear-short-window-music.json` searched65 original tracks: five adjacent one-second windows751.498–754.498 match win01 at0.9332–0.956, all implying cue-zero751.028s. The other returned candidates are at most0.2661 in that result. Those scores are waveform correlations, never probabilities.

New independent comparison used only the selected current catalog music resources and the complete native door audio. It decoded the source739.000→758.038 audio tail, win01's first8s, fuon02 track88→104s, and the5.034s native door audio; no other source interval was decoded. Audio was mapped explicitly, with video disabled. All derived WAVs are16kHz mono PCM. `measure_tail.py` performs normalized linear waveform correlation with local DC/energy normalization; `refine_measurements.py` reuses those PCM files without extracting again.

## Resource identity and continuity

- **Win01:** seven independent one-second reference windows beginning at track0.5,1,2,3,4,5,6s all align to the same source cue-zero **751.028125s**, on the16kHz sample grid. Clean-window correlations are0.96927,0.98514,0.98726,0.98659 and0.98914. Windows at source754.028 and755.028 have lower0.71964/0.54315 correlations but retain exactly the same offset; their residual audio is not identified or assigned to a sound-effect cue here.
- The clean matches at source756.028–758.028 retain the same introduction phase. Thus the cue continues under the ending chart/reward through the available recording tail. This provides no evidence of a terminal StopBGM after EOF and does not exercise a music loop wrap.
- **Preceding fuon02:** existing searches at734/736/740/744s named this track. Fresh one-second comparisons at741/742/743/744s give0.96688/0.96477/0.98390/0.91818 and consistent track positions. At source740s the aligned native track position is91.04756s; voice/other mixture components lower some earlier short-window correlations. No earlier start node is assigned from this offset.
- **Door audio:** the full native `adv_dive01_out.mp4` audio matches the source at0.95644. Five separate subwindows imply resource-audio zero745.149375–745.149563s, with correlations0.84108–0.99313. This verifies the matching sound content, not a source-native MovieProc start time or a recovered wait. Its relation to the first white/door visual witness is not an exact AV registration here.

Current `story_crowd_data/assets/catalog.json` resolves win01 to `assets/music/bgm_btl_adv_win01.opus`. Its native ACB metadata gives44.1kHz,1199202 samples, loop start11.689183673s and end27.192789116s, with no listed startup events. The current Opus preview carries the full27.19279s introduction/loop interval. Fuon02 similarly resolves to its own current Opus/ACB metadata. These are exact resource IDs; the current scene10040053 has no nonempty authored BGM rows, so the measured outgoing track does not prove the restored player's incoming route state is already correct.

## Observable envelopes and visual boundaries

To avoid mistaking a cue's own instrumentation/envelope for a player fade, the measured source mixture was regressed against the time-aligned reference signals in100ms windows. Local gains are observational and may be contaminated by speech/effects; near-silent references yield unreliable coefficients. The reported linear fits use the retained windows and a nearby stable gain baseline, not a silence threshold alone.

| Observation | Measured interval / context |
| --- | --- |
| Outgoing fuon02 gain falls | Approx744.60→745.59s, fitted duration0.991s; normalized gain-fit RMSE0.0233. Treat boundaries at roughly0.1s precision. |
| Final card exits | Existing frames show dimming around744.154–744.254, then black; first white witness744.787. The outgoing music decline overlaps the black/white transition and early door presentation. |
| Incoming win01 gain rises | Approx751.01→752.02s, fitted duration1.012s; normalized gain-fit RMSE0.0100. Cue waveform zero is independently751.028s. |
| CLEAR presentation | Collage begins appearing in the existing frames around750.7s; CLEAR letters appear during751.x, with the prior full-frame CLEAR/route witness at751.987. The cue rises with this ending-title presentation. |
| Completed chart / reward | Prior full review establishes chart END at754.454 and reward through757.987. The aligned win01 component continues through them. |

The fitted boundaries are not sample-exact native trigger times. Source silence/near-zero energy before the cue is only mixture evidence; it does not determine a StopBGM phase, absence of another sound or a script Wait. No exact door/video-start correction is derived from the audio offset.

## Native semantics and a concrete root-review candidate

Captured original scene10010001 has door node30 with `command:["StopBGM","","Wait,500\nCardOut"]` and TITLE32 `CLEAR` with `bg_music:"bgm_btl_adv_win01"` and three blank command phases. This is an original example of this cue on CLEAR; its door phases/500ms wait are not P29's recovered code.

Original `logs/adv.html:2329–2353` defaults PlayBGM to crossfade1s and reset=false when optional CSV arguments are absent. `:2056–2067` maps StopBGM's omitted argument to STOP,1. Current `compileMusic`/shared music player preserve the one-second default and independent audio sample clock. P29's measured approximately one-second envelopes agree with that native convention, but do not reveal whether its original CSV used an omitted default or explicit1, nor which command phase owned the outgoing stop.

The concrete candidate for root review is therefore the proposed CLEAR node's **plain resource field `bg_music:"bgm_btl_adv_win01"`**, using the documented native default if root approves that reconstruction. This is supported by the independent continuous waveform match, visible CLEAR context, native cue metadata and original TITLE example. The packet is unconfirmed/noninstallable: no fade CSV, restart flag, native IDs, command-phase values, StopBGM, Wait or terminal audio stop is authored by this task. The final-line incoming fuon02 state, any additional residual sounds, AV registration and actual listening/continuous restored playback remain separate work.

Primary numeric evidence is `measurements.json` / `refinements.json`. Listening materials are the bounded `source-p29-0739-to-eof.wav`, `catalog-win01-first8s.wav`, `catalog-fuon02-088-to104.wav` and `native-door-complete.wav`; they are retained for a reviewer with meaningful playback access. This report does not describe having heard them.
