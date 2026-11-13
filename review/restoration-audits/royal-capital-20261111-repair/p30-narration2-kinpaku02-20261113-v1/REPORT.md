# P30 narration2: saved native music cue

Restore exactly one authored field: `10450056:2.bg_music` changes from blank
to bare resource `bgm_adv_kinpaku02_cd2_18`. UID1045005600002, stable key
`s10450056-p30-at0397`, Japanese/Chinese text, empty speaker, native identities,
row order, commands and branches are preserved. The normal importer installed
batch `4ffd624dca4077b1420b`; structural and explicit-resource checks passed.
Reverting only this scalar in the installed native scene reproduces the prior
scene semantically. The library remains140scenes/5603nodes and in-progress.

The source narration is visible396.999–402.499seconds, and the independently
measured cue rise397.59–397.70 lies inside it. This supports an authored cue
placement, not recovery of the original CSV field, phase, command timestamp,
fade, gain or restart. The previously published native cue0 resource retains
8414915samples/44100Hz and loop6.048095238095238–190.81439909297052seconds.
The later14.016second waveform-origin discrepancy remains unresolved; no
seek/restart/Wait is authored to conceal it.

Normal saved-data playback requested `10450056:2` through the production
compiler with no program/resource override. The returned raw field and normal
play projection match the saved cue; node3 remains blank/inherit with the
original branch21→3. Initial normal loading obtained metadata/audioHTTP200;
after normal Stop an owned read-only observer captured an ordinary replay.
That replay called the original apply/start exactly once and retained the
same original player/voice across2→3. Its context was already running: the
trusted viewport input is not claimed to have unlocked it. At node3, context
time5.536→7.541333333333333 and voice time2.901333333333333→4.906666666666666
both advanced. Native loop and decoded-buffer metadata passed their explicit
resampling tolerance. Normal Stop left no current voice, players, loading or
fade; the observed voice ended. All three owned method wrappers, slot, handles
and listeners were cleaned. Root then closed Chrome/CLI and the adapter.

`saved-playback.json` is a lean actual result; its original complete5603-node
program remains in the workspace runtime stdout. Initial resource200 belongs
to warmup, not the observed replay's first receive. This accepts source-backed
cue placement and saved transport only. Listening, full loop wrap, original
phase/onset/fade/gain and full chapter music/restoration remain unaccepted.

Playback source was canonical34cb0adc plus the separately reviewed uncommitted
three-file ordinary-text-clock draft; compiler and music transport were
unchanged. This audit does not claim that draft has been deployed. The user's
first three chapters remain the user-owned acceptance baseline; this increment
does not complete a whole chapter.
