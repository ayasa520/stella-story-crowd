# Episode 12 source-grounded restoration packets

The formal data checkout is read-only to this reviewer. All packets bind base
`260b660e2fef6e2c14eb697e8123cfc077e1424f`, scene/review SHA-256, original
recording SHA-256, individual full-frame SHA-256 and time, scenario/stable key
and expected old values. Every `rootConfirmed` is false. Root owns approval,
formal import, resource installation, continuous playback and publication.

| Scene | Reviewed packet | New fields |
|---|---|---:|
| 10120001 / P39 | s10120001-character.packet.json | 54 character |
| 10120002 / P39 | s10120002-character.packet.json | 83 character |
| 10120003 / P39 | s10120003-character.packet.json | 34 character |
| 10120003 / P39 | s10120003-still010.packet.json | 9 character_image |
| 10120003 / P39 | s10120003-sparse-background.packet.json | 2 bg_picture |
| 10430012 / P42 | s10430012-character.packet.json | 34 character |
| 10430012 / P42 | s10430012-n24-picture.packet.json | 1 character_image |
| 10430013 / P42 | s10430013-character.packet.json | 36 character |
| 10430013 / P42 | s10430013-n13-picture.packet.json | 1 character_image |
| 10430013 / P42 | s10430013-n25-picture.packet.json | 1 character_image |
| 10430014 / P42 | s10430014-character.packet.json | 33 character |

These are **288 field changes: 274 character, 12 picture and two sparse
background providers**. The reviewer directly inspected every source identity
frame represented by the six character packets. The contact sheets preserve
the full portrait aspect; their individual original images remain evidence.
Motion, expressions, extra layers, geometry and timing are not signed by an
identity decision.

The P42 Elsa model is explicitly mantle-less. Puck's turquoise magic ring is
separate FX. Three apparent named-speaker rows show illustrations rather than
Live2D: ice-covered foot `ADV_pic_103002`, Elsa/Rom attack `ADV_pic_103003`, and
Subaru rescuing Felt `ADV_pic_103004`. Scenario 10430014:38 shows black behind
the unknown-speaker line and stays without a model.

The sparse historical source-frame index placed 10430013:23 outside its card,
on the previous Subaru image. A fresh single-thread decode at 362.5 seconds
shows Felt. A fresh 374.5-second image binds the following short Elsa card.
Historical retimed endpoints sometimes subtract one millisecond. Packets keep
the original image timestamp and explicitly record the 1.1 ms tolerance where
needed; they never relabel the source timestamp.

P39's anonymous customer is `citizen_hood01`; Otto is `otto01`, including the
earlier grey-haired alias. Both were compared with original LIMEOS texture
atlases. Their full moc/texture resources are absent from this base checkout;
the packets enumerate exact external source files and hashes. Root must add
the model payload/catalog support before asserting playable restoration.

P39 10120003:12–20 shows `ADV_still_010`, the mayonnaise bath illustration.
The reviewer inspected all **390 decoded boundary frames** in the two windows
786–792 and 824–831 seconds, plus the nine existing middle-card full frames.
This does not claim that all intermediate hold frames were decoded. The image
enters by a horizontal left-to-right wipe around 789.39–790.02 seconds and
blurs/crossfades into the empty bath around 826.02–826.62 seconds. The matching
background is `bg/bg092d_roswaal`; it becomes the sparse provider at node 21.
Otto is off screen there. The waking narration at node 36 / source 893 seconds
shows the cart, matched directly to `bg/bg161a_carriage`; it is the next sparse
provider. Nodes 39, 41, 46 and 51 keep Otto off screen with no model. Commands,
blur/wipe phases and precise native timings remain unknown.

The ten unobserved choice destinations remain explicitly unresolved: one in
P26, two in P39 and seven in P42. Neither source adjacency nor a convenient
target is used to fill them. Existing terminal sequences in P26/P39/P42 and
their explicit next-episode handoffs were read and retained; none was duplicated.
Their authored StopBGM/Wait/CardOut phases are still not original script proof.

P26's existing 118-observation character review and 83 installed identities
are retained. This reviewer has not re-signed P26 acting, expressions or audio.
The existing bound waveform music/voice candidate ledgers for P26/P39/P42 are
available and stay candidates. No short cue is certified without listening,
and no music query offset is turned into a restart at a dialogue boundary.

Remaining full-restoration work includes source-entry/body/face comparisons,
Puck/Emilia magic rings and ice effects, ice behind Elsa in P42, voice/SE
audition and onset alignment, music boundary/continuity review, exact
transition behavior and actual saved-player playback. No whole scene, route
or episode is declared complete. Heavy helpers use nice 19, CPUs 0–1 and
single-thread FFmpeg/BLAS. No browser, formal write or commit was performed.

`offline-validation.json` records the narrow guard/hash checks and packet
digests. It is an import preflight, not performance acceptance.
