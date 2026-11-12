# P29 ending_sequence v2 — concrete authored reconstruction draft

This packet makes the observed final line → complete native door → CLEAR → chapter completion playable using root's explicitly selected authoring convention. It is **not recovered P29 CSV**. The packet is review-only: its four `rootConfirmed` flags are false (packet, terminal and two nodes), and no builder, stage, install, compiler or browser was run. Root can approve a new derivative after reviewing these exact choices. Existing evidence and earlier unconfirmed packets remain unchanged.

## Current guarded suffix and exact projected delta

The installed final array row is scenario49, UID1004005300049, stable key `s10040053-p29-at0740`. Its sole ordinary branch491, UID1004005310491, has an empty transition list. The current `ReviewedRepair.ending_sequence` supports version2 terminal packets, requires exactly one of `terminal` or legacy `finish`, guards the last array row and blank branch, and allocates only an appended suffix. This draft has no `finish` member.

If this exact suffix remains current at staging, the existing allocator will produce:

| Item | Authored number / identity | Behavior |
| --- | --- | --- |
| Existing branch491 transition | transition49101; retained branch UID1004005310491 | Local NEXT to50; no existing row text, performance field or identity changed |
| Door node | scenario50 / UID1004005300050 | VIDEO3, `adv_dive01_out`, commands `["StopBGM","","CardOut"]` |
| Door branch | branch501 / UID1004005310501 / transition50101 | Local NEXT to51 |
| CLEAR node | scenario51 / UID1004005300051 | TITLE0, source`CLEAR`, Chinese`通关`, plain `bgm_btl_adv_win01`, three blank commands |
| CLEAR branch | branch511 / UID1004005310511 / transition51101 | FINISH, next_scenario_id0, both destination fields omitted |

These are projections of `NativeIdentifiers`, not original identities or a manually authored native document. Builder-generated default zeros, empty fields and gain vectors likewise are reconstruction defaults, not recovered values. The builder adds `video_list` membership `{name:"adv_dive01_out",command_list:[]}` if absent; no source-specific native video command timings are asserted. Both resources already exist in the current catalog. No resource copy is needed.

Terminal mode returns before the map propagation block. Expected structural scope is one changed scene10040053, two appended rows, three filled/created transitions, zero map edges, and no1045 destination. The existing four unresolved choice branches in scenes52/53 must remain untouched. Existing scene49 text, command phases and character field remain untouched. The chapter remains a draft; this packet does not accept unrecovered acting, incoming BGM state, original phases, reward presentation or full restoration.

## Why phase0 StopBGM satisfies the selected convention

Canonical `lib/preview-commands.ts:40` compiles a bare `StopBGM` with `config/commands.json`'s default fade1. `player.js:387` runs phase0 before movie CardIn and `movie()`; its music command calls `music.apply('', {fade:1,start:true})` and clears the carried BGM state. `public/studio/music_player.js` schedules the outgoing gain ramp and returns without awaiting the ramp's end. Therefore phase0 initiates a one-second game-clock fade; it does **not** insert a one-second blocking Wait or postpone the movie until the fade finishes. This is consistent with root's requested authoring policy. It is not evidence of P29's exact original trigger or AV origin.

If continuous playback has no inherited active BGM, StopBGM correctly has nothing to fade. Directly starting the door preview suppresses restoration of a newly-created upstream track that its leading stop would immediately discard (`restoreEntryAudio`). That preview behavior is not evidence that the continuous incoming fuon02 state has been reconstructed. The audio report explicitly leaves that upstream state unresolved; this package does not add an earlier fuon02 assignment.

The existing automatic card replacement can finish the preceding actor's CardOut before the new node reaches phase0 (`player.js:334–348`). Thus the chosen stop is before the movie CardIn, but is not promised to begin with the preceding actor's exit. Root's next necessary continuous capture should observe that actual boundary rather than treat the source envelope as a recovered phase0 timestamp.

Root also identified a concrete audio-state boundary for that same QA: starting at49 has no prior assigned BGM in scene53, so the leading stop may have no AudioContext to operate on; win01 creates its context later. The runtime context's running/suspended state has not been measured for this new suffix. Root will retain CDP WebAudio events and existing console logs during the necessary playback. This report makes no autoplay/silence cause claim and proposes no audio source change; the packet remains plain win01 with the native default fade.

The movie is awaited through its native media `ended` event (`player.js:670–681`), with no trim, seek or duration override. Empty movie text immediately reaches `afterText` (`:437`); phase2 CardOut executes there (`:503`). It sets `cardOut`, invokes the existing transition lifecycle when applicable, and `afterText` automatically calls `advance` (`:528`). Thus no extra post-movie Continue click is required. There is no `Wait,500`, no source-timestamp wait, and no copied first-episode phase claim.

On CLEAR entry the plain music field compiles with native default fade1 and restart=false. The previous stop has cleared the script's BGM state, so this selected cue begins as a new play request. An end TITLE is unmuted, skips the opening chart, shows the native title presentation, then follows its sole terminal edge. The shared compiler emits `flow_action:"complete"`, empty target/destination, and the player returns to the completed section1004 chart with `本话已结束。`, preserving music (`keepMusic:true`). No successor node is entered and no silence/EOF-driven final stop is added. The current settled title implementation still uses the existing1.6-second title flow; this package does not claim the original2.5-second entry animation has been restored.

## Evidence and uncertainty stay separate

The prior full570-frame739.021–757.987 review establishes the final line, complete5.034-second native door, CLEAR with Julius route, chart END, and reward. The native door's complete audio and five subwindows also match. The independent win01 comparison aligns seven one-second windows to source cue-zero751.028125; clean correlations are about0.969–0.989. Correlation is not probability. Approximate outgoing/incoming one-second envelopes support using the native defaults, but do not recover CSV arguments, phase placement, exact movie-init time or any Wait.

Original intro41/102 and ADV GetNext support the no-successor FINISH representation; they do not recover P29's terminal payload. Existing runtime QA already showed omitted fields and -1/-1 completing their own section without successor entry. P29's omitted form, all new IDs, blank unused phases and phase0/phase2 choices remain explicitly authored. No meaningful audio listening was available to this reviewer; continuous root playback/listening remains necessary. Reward is observed evidence only and is not recreated by this packet.

## Root approval, staging and bounded acceptance

`STAGE-COMMAND.txt` gives the exact existing importer invocation. Before it is run, root should create the named **new** approved derivative, changing only the four confirmation flags, `installable:true`, the review status, and the approval-pending annotation; root may append a root-review note without altering node fields or evidence. Keep this false draft immutable. `executionAuthorized` can remain false because it describes this offline preparation; staging still requires root's separate release.

The builder does not enforce the informational `installable` field: the four confirmation flags are its actual gates. Root should use the existing verified JSON-ingress process wrapper if required; `target_run_verified_script_v1.py` is restricted to three unrelated static-kit scripts and must not be repurposed by changing its allowlist. The shown command is the native module's exact interface, not authorization to bypass that ingress evidence or retry a failed write.

Stage into a new, absent output folder, then inspect the actual emitted delta before any installation. Expected counts are `addedEndingNodes:2`, `addedMapEdges:0`, scene10040053 only. `stage()` refreshes derived reviews before comparing them; if unrelated scenes are emitted, root must isolate/review that drift rather than accept it as part of this packet. Confirm retained row/branch identities/order and all chartmaps unchanged; only491 gains its local link, plus the two suffix rows and their sidecars/video membership. This is a bounded package check, not a request for another whole-corpus byte inventory.

After root's formal publication, one necessary continuous QA should start before the final line, play the complete door, automatically show CLEAR, and finish section1004 without a1045 enter. Existing logs can establish phase0 StopBGM/fade1 before `movie_play_begin`, complete movie metadata/`movie_play_complete`, phase2 CardOut, TITLE/end, BGM cue/fade1, terminal `action:complete,target:""`, and `STORY_PLAYER_SECTION_COMPLETE section:1004`. Compare the actual ending presentation/audio with the retained full source review. Do not insert Wait or adjust curves to hide an unexplained difference; collect the relevant boundary logs first.
