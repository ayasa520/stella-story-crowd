# P30 ending audio: bounded source review

**The CLEAR music is `bgm_btl_adv_win01`. The outgoing music is `bgm_adv_only02_cd2_25`.** Independent waveform windows support both identities and their local reference clocks. No native gain, fade, phase, Wait, or authored music field is accepted by this report.

Reused files, all under `../p30-bgm-identification-20261113-v1/`:

- `p30-original-source.wav`: mono s16, 4000Hz, 1006.67775s; only986–1006s read.
- `bgm_btl_adv_win01.wav`: mono s16, 4000Hz, 27.19275s.
- `bgm_adv_only02_cd2_25.wav`: mono s16, 4000Hz, 218.9225s.

No decoding, library scan, browser, image review or formal edit was performed. The existing audio-timeline review records source PTS0 and no packet discontinuities. All exact numbers below remain decoded PCM coordinates. Parent's visual anchors are approximate and were not re-reviewed here: node35「―完―」990.4–993.0, door993.6–999.5, separate CLEAR999.6–1001.9, END chart1003.1 then reward.

## Identity and clock consistency

Centred normalized correlation uses independent non-overlapping1s and2s windows. Scores are waveform similarity, not probabilities. Five peaks at least0.5s apart are retained for every query in `measurements.json`, including weak/competing peaks. Only the two requested existing references were searched.

| Source window, s | Reference | Best reference offset, s | Best NCC | Second NCC | Implied reference zero on source axis, s |
|---|---|---:|---:|---:|---:|
| 986–988 | only02 | 200.348 | .66799 | .35565 | 785.652 |
| 988–990 | only02 | 202.348 | .98965 | .57328 | 785.652 |
| 990–992 | only02 | 204.348 | .91908 | .46367 | 785.652 |
| 992–994 | only02 | 206.348 | .94849 | .53678 | 785.652 |
| 1000–1002 | win01 | .0525 | .92543 | .15654 | 999.9475 |
| 1002–1004 | win01 | 2.0525 | .87788 | .20408 | 999.9475 |
| 1004–1006 | win01 | 4.0525 | .67280 | .36119 | 999.9475 |

The separate1s win01 queries1000/1001/1002/1003/1004/1005s all give exactly the same999.9475s reference zero, with NCC.86342/.97025/.96811/.70394/.53820/.98418. Reverse reference windows0–2,2–4,4–6s independently find source999.9475/1001.9475/1003.9475, NCC.91644/.89441/.66771; their second peaks are.14385/.13218/.20481. Thus the lower1003–1004 scores do not supply evidence of a restart/seek or another cue: the best clock stays consistent, with a very strong match again at1005s.

The1s only02 queries986–993s all give785.652s reference zero; most score about.99. After994s its strong coherent match is lost: the994–996s global best is.15631 at209.8085s, while the coherent208.348s candidate is.14708. The raw994–995s best is an ambiguous.46501 at207.42325s, almost tied by.45666 at209.818s, and must not be turned into a new music clock. Fixed-clock envelope measurements below handle the outgoing tail without selecting such a competing phrase.

The two inferred zeros are **local waveform alignment offsets**, not recovered first-play commands. In particular785.652s does not establish that only02 originally started then, and999.9475s does not prove the exact native CLEAR BGM command/provider/phase. The sampling grid is0.00025s; this grid is not the uncertainty of the original trigger or video sync.

## Measured outgoing decline and incoming rise

`envelope-measurements.json` retains source/reference RMS, centred NCC, residual RMS and the local least-squares recording coefficient in100ms bins. The coefficients compare mixed, encoded signals; they are **not native gain values**. Source RMS alone cannot separate music from overlapping sounds.

| Outgoing only02 source bin start, s | Fitted recording coefficient | NCC |
|---:|---:|---:|
| 993.2 | .07997 | .9952 |
| 993.5 | .07676 | .9852 |
| 993.7 | .06061 | .9900 |
| 993.9 | .04492 | .9871 |
| 994.1 | .03039 | .9853 |
| 994.3 | .01509 | .9609 |
| 994.4 | .00660 | .9339 |
| 994.5 | .00153 | .2865 |

This directly supports a recording decline across roughly993.5–994.5s: the reference remains energetic while the matching contribution falls. The stable matched baseline at991–993.3s is around.08. At994.5s and later the fit approaches the residual floor and no longer reliably isolates the music. The full source mix then contains other energy; its source cannot be identified by this two-reference music comparison.

| Incoming win01 source bin start, s | Fitted recording coefficient | NCC |
|---:|---:|---:|
| 999.9475 | .00383 | .6071 |
| 1000.1475 | .01766 | .6609 |
| 1000.3475 | .03322 | .9059 |
| 1000.5475 | .05002 | .9706 |
| 1000.7475 | .06369 | .9704 |
| 1000.9475 | .07707 | .9801 |
| 1001.1475 | .07723 | .9689 |

This supports a recording rise roughly999.95–1001.0s, then a near-stable matched coefficient around.077. The source250ms RMS also grows from−50.30dBFS at1000.00s to−33.31dBFS at1001.00s, but the fixed-clock reference fit is needed to distinguish that rise from the reference's own musical envelope. The4kHz source contains exact digital zero from999.1425–999.9710s (0.8285s); this is a PCM observation, **not a native Wait or stop interval**. Weak early bins and codec/resampling boundaries prevent turning the first nonzero sample into an exact original play event.

win01 is still strongly present at1005–1006s, after the parent-reported END chart boundary. A win01 exit envelope has not been established within this bounded tail. Its existing catalog metadata is cue0, loop11.689183673469389–27.19278911564626s, startup events empty. Only02 metadata is cue0, loop8.697619047619048–218.9224036281179s, startup events empty. These are existing resource settings, not newly recovered P30 parameters or observed loop wraps.

## Actionable scope

The existing win01 resource is supported for the ending's music identity; no new audio export is needed. The source decline/rise and gap must remain recording evidence until independent native command/sequence evidence establishes how the normal ending sequence owns them. This report does not install a node37 `bg_music`, StopBGM, fade duration, gain, phase or Wait, and does not connect native nodes. Parent can combine this identity evidence with the independently verified door/CLEAR/FINISH sequence while keeping those parameter uncertainties explicit.

Execution was ARM aarch64/NumPy2.4.6, nice19, CPUs0/1, all numerical thread variables1. The main bounded NCC pass completed in1.589s. `rootReviewed:false`, `rootConfirmed:false`; no meaningful listening or browser playback is claimed.
