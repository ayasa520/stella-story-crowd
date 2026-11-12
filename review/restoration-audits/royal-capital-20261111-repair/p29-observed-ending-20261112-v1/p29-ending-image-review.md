# P29 complete ending capture — bounded visual pass

**Pass for the authored ending's visible playback sequence and native-core title entry. No blocking visual finding for this bounded change.** This is not acceptance of the whole P29 performance or an assertion that its original CSV was recovered.

`closure.json` reports zero browser/CLI/recorder processes, the owned server stopped, and image review permitted. The reviewer created six ordered contact sheets from the existing321 JPEG frames under `review/p29-ending/frames` and directly viewed every sheet: frames0001–0321, with none skipped. The derived pages are `review/p29-ending/peer-contacts-v1/contact-01.jpg` through `contact-06.jpg`; creation used nice19/CPU0,1 and single-thread environment settings, with no video extraction. Full runtime frames0125,0165,0308 and the auxiliary `p29-clear.png` / `p29-completed-chart.png` were also directly viewed. No browser, server or player was run by the reviewer.

The comparison reuses the earlier complete739.021–757.987 original-tail and complete native-door review. Original frame0240 at746.987 seconds was directly re-viewed for the door, together with the separately established CLEAR-to-black evidence in `../target-p29-clear-exit-layer-review-20261112-v1/REPORT.md`.

## Visible sequence

- Frames0001–0045 show the final Felt line in the weapon shop. This establishes that the capture starts before the ending transition; it does not accept her motion, expression or dialogue-panel fidelity.
- The following black interval leads to the bright native movie entry around frame0070. The full white opening, moving doors, central light/star, closed-door hold and darkening all appear in order. The doors fill the portrait viewport and remain centered, with the expected pillar/beam/door-panel composition and no spurious letterbox or exposed shop. Full frames0125/0165 agree with the previously reviewed native resource and source composition. This is a visual framing comparison, not a sample-exact AV registration.
- After the door darkens, the native normal collage appears around frame0243, then the route/title fades into view. The source-matched Subaru/paper/pen/photograph/fountain collage, pale-purple `本編：ユリウスVer.` subtitle, purple first Chinese glyph and remaining white `通关` text are complete, centered and readable. This is the correct Julius route, not the generic `正篇` subtitle from the earlier baseline-scene test.
- Frames0304–0308 darken the complete collage and text together. Full0308 is near-black, retaining only very faint title-image residue; it does not expose the previous weapon-shop scene or the chart. Frame0309 then shows the completed chart. This agrees with the original's visible fade-to-black direction and fixes the specifically reviewed risk of revealing the script background. The recording does not reproduce the original network `Connecting` hold, and no such hold or Wait is required by this visual acceptance.
- Frames0309–0321 show the existing chapter chart and its completion state. The auxiliary full chart has the current final Julius scene marked complete and the footer `本话剧情播放结束` / `本话完成`. It is the current full-chapter chart presentation, not a visual reproduction of the original cropped END/thumbnail/reward screen.

## Runtime evidence supporting the visual review

The existing `playback-result.json` records only `10040053:49 → :50 → :51` for this case. It records complete `adv_dive01_out`, source1334×1334, viewport523×930, door presentation/cover, duration=currentTime5.034 and ended=true. Phase0 executes bare StopBGM and phase2 executes CardOut before the transition to51; the movie automatically proceeds to CLEAR.

For node51, the native-core title entry reports2500ms and completes at2516.6ms of the existing game clock. This capture therefore exercises the new2.5-second entry path, unlike the earlier static1.6-second checkpoint. It is not a claim that every native material effect or loader-size side effect has been projected. The final transition is FINISH with next_scenario_id0, both destination fields omitted, `action:"complete"`, and an empty target. `STORY_PLAYER_SECTION_COMPLETE section:1004` follows. There is no1045 or guessed successor enter in this case.

The CDP audio events for this ending show its realtime context created suspended at wall1794487394995 and changed to running at1794487394996. Existing logs request plain `bgm_btl_adv_win01`, fade1/restartfalse, and report fade completion with audioTime1.0026667. These are positive runtime state/clock observations; no audio-cause repair was needed or is inferred. The CLI recording used `-an` and contains no audio track, so this reviewer makes **no listening, audible mix, volume or synchronization acceptance**. The incoming route BGM remains unknown.

## Boundaries retained

All new ending IDs, internal links, StopBGM/CardOut placement, blank unused phases and the omitted-destination terminal choice are the explicitly approved authored reconstruction. Original P29 CSV, command phases, exact StopBGM trigger, exact movie AV origin and unknown Wait values remain unrecovered. No Wait500,1045/map edge or reward node is accepted or implied.

The original reward popup, original chart artwork/layout, actor motion/expression/entry, unresolved choices, incoming BGM state and meaningful audio listening remain outside this pass. No production source, formal data or Git state was modified by the reviewer. The bounded ending-flow and title-entry findings can be published without describing P29 as fully restored.
