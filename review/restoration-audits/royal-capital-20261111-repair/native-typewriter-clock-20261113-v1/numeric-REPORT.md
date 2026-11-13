# Independent audit of actual typewriter numeric samples

**No arithmetic or recorded lifecycle discrepancy found in this capture.** This is an offline numeric audit of `../native-typewriter-diagnostics-runtime-20261113-v1/diagnostics-result.json`, not a new runtime test or image review. `arithmetic-receipt.json` preserves each comparison and all reconstructed frame counts; `analyze_actual_samples.py` reproduces the calculation from those retained actual samples under nice 19 / CPU 0,1. No mock, player import, new clock, browser, video/image read, formal-data/source change, or Git operation occurred.

The native reference is the retained `TextPanel.UpdateText` at **0x1686ddc**, specifically `fadd s8,s8,s0` at 0x1686e60, `fmul s0,s8,s9` at 0x1686e94, `fcvtzs w0,s0` at 0x1686e98, then Clamp at 0x1686ea8. For the recorded nonnegative finite values, the independent reconstruction is `t=f32(t+f32(delta)); visible=clamp(trunc(f32(t*f32(speed))),0,length)`. It starts at zero and excludes the already-current start frame. This matches the native single-precision operation boundaries; it does not certify every original native text-info/retry branch.

## Complete sampled clock domains

| Document | Independent timeOrigin (ms) | Actual frames | Samples |
|---|---:|---:|---:|
| `/player/player.html` | 1794531064746.9 | 218–1424 | 1207 |
| `/studio/player.html` direct endpoint | 1794531127962.4 | 201–356 | 156 |

All **1,363** samples independently satisfy sequential frame numbering, raw delta recomputed from adjacent RAF timestamps, `delta=min(raw,0.3333333432674408)×previewRate`, and previous game time plus that delta. There are no independent gaps, duplicates, or formula mismatches. Each observer also reports zero gaps/duplicates/errors, no truncation, successful removal of its own subscription, retained actual owner, and restored original viewer speed/clock rate of 1. The two documents and their token/frame numbers were never combined.

The player's startup ZH token 1 (frames179–205) and direct Studio's startup ZH token1 (161–187) predate their observers. Their sparse logs are retained but are **excluded** from independent reconstruction.

## Actual token comparisons

**12 fully covered tokens**, consuming **256 actual frame samples**, yield **53 exact binary32 matches** against all their recorded started/progress/terminal states. Every start is visible0/elapsed0. All eight natural completions occur on the first frame at which the independent sum reaches the text length; no earlier complete is predicted. Each covered token has one terminal record, subscribed=false, and no later recorded event for that same token.

| Surface / token | Language | Start → terminal frame | Result |
|---|---|---|---|
| player2 | JA | 349→376 | natural44, first predicted completion376 |
| player3 | JA | 489→530 | zero-rate case, natural44 at530 |
| player4 | JA | 635→660 | positive rates, natural44 at660 |
| player5 | JA | 791→814 | induced task/cap, natural44 at814 |
| player6 | JA | 920→926 | replaced at10/44 |
| player7 | ZH | 926→933 | replaced at13/42 |
| player8 | JA | 933→960 | fresh reset, natural44 at960 |
| player9 | JA | 1071→1095 | click cancels clock at39/44 |
| player10 | JA | 1146→1159 | normal next node8, natural21 at1159 |
| player11 | JA | 1274→1283 | Stop at15/44 |
| player12 | JA | 1388→1415 | replay, fresh0→44 at1415 |
| direct Studio2 | JA | 320→347 | natural44, independent domain |

The actual helper records only sparse token states, not visible count on every frame. Thus the 256 per-frame counts in the receipt are **predictions from independently verified actual deltas**, compared at all 53 available actual states and at natural-completion boundaries. They must not be described as 256 individually measured glyph submissions or pixels. Identical sparse endpoints also cannot exclude every hypothetical unlogged transient callback.

## Targeted findings

- **Clock-only zero:** actual frames495–508 are14 consecutive samples with rate0, delta0 and unchanged game time. This contains the requested12-frame window496–507. Reconstruction remains elapsed0.33329999446868896/count8 throughout, consistent with the actual progress8 at495 and resumed progress9 at509. Phase remains text during the requested window. Viewer/audio speed remains1 in control snapshots; no `setSpeed(0)` was used. This proves the recorded clock freeze and compatible token endpoints, not per-frame pixel immobility.
- **Positive rate once:** frames641–652 use0.5 and653–663 use2. Each recorded delta equals capped raw×rate exactly; the typewriter sum applies no second multiplier. Token4 predicts count9 at641,21 at653 and44 at660, matching actual events. The owner API also changes its audio playbackRate and wall anchor, as declared; it is not a pure all-media clock experiment. Both are restored to1 afterward.
- **750 ms real task:** retained task start32534.70000000298/end33284.70000000298 is exactly750ms in that document. Subsequent RAF frame799 has raw0.8166000000000022s and delta **0.3333333432674408s**. The independent float32 state changes from count11/elapsed0.4666000008583069 at798 to count19/elapsed0.7999333143234253 at799, matching the actual hitch progress record. It permits an eight-character increase and provides no one-character cap. This is an intentionally induced diagnostic task, not an explanation of earlier unlocalized production stalls.
- **Control snapshots are not new samples:** changing rate can leave the current frame's old delta in a mark while showing the new rate. E.g. the frame494 mark has rate0 with the previous nonzero delta; actual observer frame494 was rate1 and the first zero sample is495. Reconstruction uses the immutable observer records, not those mutable-between-frame marks. The same distinction applies at640/652 and restoration.
- **JA→ZH→JA:** actual tokens6→7→8 start afresh at920/926/933. The replaced token state and fresh zero start share the replacement frame, which is excluded from the new token's accumulation. No later old-token events occur in the retained observation.
- **Click/afterText/normal next:** token9 ends as `finished-or-skipped` at39 rather than claiming natural completion. Normal ready follows, then exactly one retained normal edge `10140002:6:61 → 10140002:8`; token10 starts and naturally completes. Retained timing logs show one phase2 begin/end pair for node6 and one for node8 in this case. This corroborates the observed lifecycle, not a direct count of all internal callbacks or a pixel review of click completion.
- **Stop/replay:** token11 is stopped at1283. All12 explicit idle samples1288–1299 remain stopped; no later token11 event appears. Normal replay creates token12 at zero and completes. The diagnostic observer's actual removal is recorded through `clock.listeners.has(onFrame)==false`; individual native-typewriter listener handles were not independently enumerated. Their source unsubscribe path, subscribed=false terminal records and later token/phase behavior are compatible, with that measurement limit preserved.

Driver `errors`, `cleanupErrors`, and both observer error lists are empty. **Two generic console error records say HTTP404**, without URL: initialization and click/normal-next. They are not clock/listener/player exceptions, but this audit cannot identify their resource or certify an entirely error-free console. No cause is assigned.

This numeric capture does not accept pixels, hearing, original frame cadence, exact text-info conditional retry timing, all chapters/transports beyond the two observed paths, or whole-episode restoration. No additional capture is requested by this audit.
