# Episode9 other routes — bounded source review

Reviewer `/root/episode9_other_routes`; formal data read-only at
`260b660e2fef6e2c14eb697e8123cfc077e1424f`. No browser, formal write,
commit or publication was performed. The first three episodes are excluded.

## First actionable gap:10150006:12 hall background

`p23-hall-background.packet.json` proposes exactly one field, guarded by its
empty value, stable key, Japanese source, native/review hashes, source-video
hash and original-plate hash. It remains `rootConfirmed:false`.

I directly inspected all449 retained source frames at original cadence,
875.022–889.955s, through all15 complete contact sheets, plus the original
`ADV_bg125d_crusch.png`. This includes the outgoing garden Subaru, complete
black wipe, empty hall reveal, location title, complete Crusch entry and exit,
and following butler Subaru entry. The original title is over the fully
visible hall. Its central gold lion crest/fireplace, paired square lamp
plinths, teal bands, cream arches, hexagon frieze and large green floor
diamonds match125d directly. Current scene6 contains only the garden provider
at2;12 and all its later nodes have empty `bg_picture`. The packet restores
the first observed hall provider at12. It does not write inferred inheritance
into later empty rows.

Source timing is measured from retained decoder showinfo, not a native
timer: first faint hall pixels frame112=878.722s; full reveal by132=879.389s;
location title full witness170=880.655s; following Crusch witness241=883.022s.
The wipe is observed, but its original command phases and parameters are not
recovered. No new Wait/CardOut or timing command is proposed. Crusch13's body
has hands on hips; her brief facial/neck movement is visible through entry,
hold and exit, but no body/face token is accepted from the background review.

## Preserved uncertainty and continuing scope

Section1006 contains directory scenes10060001–4, absent from the published
manifest and with no matching local Felt IF route recording. Directory names
alone cannot supply dialogue, performances or links. No正文 is fabricated.

Section1015 is P23 and has four installed draft scenes10150003–6. Existing
identity review is reused as an index, not promoted to acting acceptance.
The30 butler Subaru rows remain unresolved because visual-equal
subaru_butler01/02 bodies do not identify the original controller/resource.
Scene10150005:17–24 shows a three-subject composite and must not be replaced
by the current speaker's Live2D. That previously unresolved resource is now
directly identified as`ADV_still_045`; see the separate picture packet below.

The four empty alternative choice branches (10150003:43 weather,
10150004:22 boast,10150005:30 blue seed,10150006:22 decline) were not travelled
by the local recording. They remain explicit missing route content, not
connected by guessed adjacency. Existing witnessed cross-scene transitions
3→4→5→6 and onward10160007 are retained. Motion, face, audio, effects and full
continuous actual playback remain unaccepted for this route. The full
restoration goal remains active.

## Second actionable gap:10150005:17–24 original composite

`p23-still045-picture.packet.json` proposes eight`character_image` fields and
describes the missing original resource integration. I viewed the full-size
original still045 and all eight existing full-size source witnesses, including
their Japanese dialogue. Each matches the same illustration: foreground
Wilhelm raises two tied paper bags; butler Subaru behind left pours seed into
his palm; flushed Crusch behind right leans in; the green-handled trowel lies
across the bottom flowerbed edge. The white manor and individual tall trees
match as well. The asset is1536×2048, SHA-256
`ac4fb619fc61b8743bf332f2cdbc56901eb24f32403d75adb2e934a40ba3dd4b`.

I directly inspected entry frames1–180 (724.022–729.989s), and exit frames1–180
(766.022–771.989s). These retain every source frame of the CG reveal and its
departure through black to the next garden Subaru entry. The remaining179
frames from each extracted12s window are retained but not claimed reviewed.
The intervening entire40s sequence was not reviewed frame by frame; the eight
same-node witnesses establish the resource separately on each proposed row.
The entry is an observed left-to-right reveal. It is fully exposed by725.922s;
source17's dialogue starts afterwards. The picture is blurred at767.922s,
then black by768.022s. Normal garden Subaru is first faintly revealed at
769.822s and fully present by770.522s. No time is converted to a scripted wait.

The formal catalog currently lacks045. Its original PNG and catalog member
must be integrated and its compressed preview published before the eight
fields can be considered playable. The packet is intentionally not marked
root-confirmed. All eight rows already have scenario_type2 and empty
character/character_image; only`character_image` is proposed. No CG is put
into`bg_picture`, and no invented Live2D body is assigned.

Motion, face, geometry, background timing, wipe commands, audio and continuous
actual playback remain unaccepted. A root-owned normal16→17→18 and
23→24→25 continuous run, with the published original picture present, is the
next relevant actual check; it cannot be replaced by this offline review.

## Audio continuation points, not accepted fields

Reuse`audio/waveform-graphs/p23-cde8f107bc86/music-candidates.json` and
`music-review-index.json`; no full-video OCR/audio rerun is needed. Both files
explicitly describe candidates rather than acceptance. Current drafts have no
scene music providers apart from the clear cue. Three particularly concrete
next onset checks are scene10150004:3 (384s) and10150005:3 (645s), both
`bgm_adv_comical02_cd2_09` candidates, and10150006:13 (883s), candidate
`bgm_adv_every03_cd2_11`. Matching follow-up samples reach.8944 at387s,
.9732 at648s and.9969 at888s respectively, with coherent track-clock advance.
Those numerical results identify useful source windows; I have not listened
to them or established original start nodes, so this packet assigns no BGM.

For the first scene,42–88s has coherent every02 candidates and119s onward
every01 candidates. Exact starts and the garden transition remain the useful
boundary checks. Short voice-cue candidates and retained audible-review WAVs
already exist in that same P23 directory. No voice or SE is accepted merely
from a high correlation or speaker name. All four scenes still need body/
face/extra, voice/BGM/SE, native phases/effects and continuous actual playback
review; this contribution closes only the two source-identity investigations
above, pending root integration and actual playback.

## Validation and formal-state guard

`validate_packets.py` passed all nine exact stable keys, Japanese sources,
declared old field values, owned native/review file hashes, eight pre-existing
source-witness hashes, three hall-witness hashes and the original045 PNG hash.
`validation.json` retains the result. The root writer advanced unrelated
formal work to4845704 during this review; owned files still match the packet
base260b660. Accordingly the receipt explicitly requires root HEAD/catalog
rebind and does not authorize installation. Packet bytes were preserved.
Python AST parsing and scoped`git diff --check` passed. All delegated extract/
contact-generation processes are terminal. No Chrome session was created.
