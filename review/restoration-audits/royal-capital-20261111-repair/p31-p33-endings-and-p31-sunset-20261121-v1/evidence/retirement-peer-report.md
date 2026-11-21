# Independent offline peer review: limited normal path passes; claims need bounds

`rootConfirmed=false`. Reviewed v1 patch SHA
`8fd78e53a87170956ff5ab158ffb9ed7a9e0474e8670db3ad0d43cf0142e015a`
against canonical `7f32a3cde97d9a379828619242d2ba12f94f6514`.
No implementation blocker was found for the stated **same-scene, immediate next,
movie→end TITLE, cardState in, skip false, empty-command** path. This is a
limited static peer pass, not approval to apply/build/run or a playback pass.
The following claim and validation corrections are required before acceptance.

## Findings

1. **CardStay is an existing renderer boundary, not established native no-drop
   semantics.** Original `adv.html:1817` implements End by calling CardStay;
   `:2695` changes In to Stay without setting `isCardOut`. Crucially,
   `ADVFuncs.CardDrop` at `:2618–2633` admits **In or Stay**. MovieProc's default
   branch at `:7195–7205` then calls CardDrop when there is no choice and no
   explicit Out. The unchanged renderer `cardState==='in'` guard suppresses
   the proposal while state is Stay. Preserving that existing behavior is
   valid for the narrow change; it cannot certify native Stay correctness.
   Describe the Stay row as an unchanged renderer guard, leave native Stay
   acceptance false, and do not broaden this patch without its own evidence.

2. **The P31/P33 edge evidence is an actual compiler result, not an observed
   normal saved HTTP prepare.** The existing `compile-preview-result.json`
   uses real canonical `compilePreview` with an unapproved memory projection.
   It gives P31 `10040043:109→110` and P33 `10040036:29→30` as
   `kind=next, flow_action=continue, available=true`; both title→FINISH edges
   are `flow_action=complete` with an empty target. `studioProject` in
   `lib/studio-native.ts:187–198` spreads those edges and remaps source/target
   IDs without replacing `flow_action`. The normal prepare route in
   `lib/studio-api.ts` returns that projection. Thus the intended classification
   is statically supported, including the Studio identity remapping. No
   saved `/api/player/prepare` response for these proposed suffixes exists in
   this review. After an actual approved save, retain the complete real prepare
   response/hash and verify the exact stable IDs, start/route and all three
   actual edge actions. Do not label compiler-only evidence as saved playback.

3. **The new boolean proves structural eligibility, not an executed retirement.**
   `movieEndTitleRetirement` can be true when `animate` is false because state
   is out/stay or skip is true. Require `animate=true`, one corresponding real
   `STORY_CARD_OUT_START/COMPLETE` pair, actual root-alpha descent, and the
   unchanged Normal clock, tied to the exact node/generation/input. Current
   CardOut logs contain wall timestamps and selected-card status, not Normal
   clock or generation. Current `STORY_PLAYER_TIMING` has node/stage and elapsed
   milliseconds, also without generation/clock. A specifically released
   read-only observer must provide the missing witnesses; do not infer them.

4. **Logical target entry precedes visual title presentation.** `enter()` sets
   `this.node`, `body.dataset.node`, timing `enter` and `STORY_PLAYER_ENTER`
   before the new predicate/drop. Their appearance before CardOut is expected.
   The post-drop presentation boundary is `STORY_PLAYER_TITLE`, followed by
   `STORY_NATIVE_TITLE_ENTRY` stages in the production Player. Do not require
   logical ENTER to follow drop, and do not use it as proof that a title was
   already displayed. The Studio twin retains its older generic title hold
   and has no NativeTitleEntry stream; validate the actual served surface.

5. **The change does not cover every default retirement.** Same-scene movie→
   ordinary TITLE, different-scene movie→end TITLE, nonmovie→end TITLE and a
   movie→skipped tutorial→end TITLE chain remain outside this new predicate.
   These are existing scope gaps, not new regressions or additional accepted
   native cases. The edge-source guard intentionally excludes non-immediate
   edges when `nodeBeforeSkip` retains an earlier movie. Keep this limitation
   explicit rather than claiming general movie/default retirement recovery.

## Original HTML and ARM ownership

The primary HTML is the migrated read-only
`/home/rikka/.local/state/stella-migration-20261112/pre-tar-update/files/logs/adv.html`,
SHA `79e45d5f771ca407cfd80b34ac7ef29bcc4350b658ea17b4d984cdb54e941d6e`.
The absent legacy `logs/adv.html` path was resolved through the proposal's
hash-bound input receipt, not replaced with a reconstruction.

`MovieProc:7159–7209` awaits natural PlayMovie completion, command phase1,
PanelSequence, phase2, SelectSequence and its default CardDrop before returning
the selected transition. `Play:6980ff` awaits PlayScenario before GetNext.
TitleProc performs interval decision, phase1, SetTitle, phase2 and its edge.
This establishes separate natural-end and user-operation boundaries. It does
not authorize automatic story advancement on natural movie completion.

Independent byte-level inspection of the original ARM ELF matched **759
instruction words** in the complete lower-chain excerpt, checked **16 methods**
against their own Assembly-CSharp.dll token table, and decoded **13 direct
branch targets** from actual instruction words. `native-chain.json` retains
the exact addresses, tokens, module, upper bounds and branch witnesses:

- Movie_Init `0x1712720` tails StartUserOperation `0x1712678` at `0x17128a4`.
- StartUserOperation distinguishes selection, the explicit prior-Out byte,
  and default CardWaitUserDrop. Its default call is `0x17126f8→0x124f604`,
  followed by Director.Wait; prior-Out invokes the continuation and clears
  the flag rather than adding a second default drop.
- CardWaitUserDrop calls IsSkipInOutEffect at `0x124f64c`; skip branches to
  CardWaitUserTap, otherwise `0x124f6c0→UIController.CardDrop 0x1689c04`.
- UIController→View.CardDrop→CardBehaviour.Input(Discard2)→ExecClick→
  DropState5→DropProc alpha descent→FinishProc callback→drop completion
  `0x1251830`→ReturnSuccess `0x159c9ac`→CardInit `0x124f32c` is intact.

No ARM code, game runtime or proposed JavaScript was executed. This inspection
accepts ownership/control flow, not exact original request-boundary timing,
pixel composition, actor performance or subjective audio.

## Source flow and regression review

Both proposed Player copies contain the same added predicate. It uses kind,
title mode, same scene, explicit continue/next edge and preserved source ID;
there is no resource-name, scene-ID, native-field, command or music special
case. `from!==null`, skipInOut and in-state continue to control the shared
compositor. Existing movie→card/text replacement and ordinary scene-title
retirement remain on their old paths. Choice transitions already perform their
own drop/init before following the edge; out state and edge kind prevent a
duplicate. `edge-and-scope.json` records the manual guard matrix; no executable
synthetic predicate test was created.

At target entry the old video is paused, not removed. Production prepareTitle
prepares fonts and a detached NativeTitleView; configureNativeTitle disposes
only an old title view. It does not clear the movie, call display or move the
card. The awaited shared `cardOut()` completes before later `title()` invokes
scene.clear/display(empty). The movie is inside cardMotion, while the title
overlay is a separate presentation. Empty-movie text produces no outgoing
panel snapshot; movie-with-text uses the existing concurrent panel lifecycle.

Stop/replay cancels the transition subscription through reset and invalidates
the Player generation. The awaited drop's rejection/check blocks the old
title path. This is source-level support; a real interruption still needs an
observed post-release cancellation record. No new title/background/audio
cancellation guarantee beyond those existing owners is accepted here.

Original first-three scene10010001 was checked directly: node30 is the real
`adv_dive01_out` with phase0 StopBGM and phase2 `Wait,500\nCardOut`, then node31
tutorial and node32 CLEAR. Executed explicit Out leaves cardState out. With the
existing tutorial skip, the incoming edge source31 also differs from preserved
previous movie30. Both independently exclude a new automatic drop. The source
patch changes no script bytes and must not remove the original wait/Out.

## Required actual playback boundaries after a separate root release

Use one normal saved P31 or P33 suffix, an actual preceding dialogue, empty
movie/title command phases, the unmodified returned program, and the real
movie through natural `ended`. With auto off, record the natural end, ready,
one trusted Continue, transition, predicate/animate decision, one drop with
real alpha/Normal-clock samples, card_change_hidden, actual title presentation,
native entry completion, terminal complete and the route's completed chart.
Logical target ENTER may occur before the drop. Record video `currentTime`,
duration, paused/ended/hidden, card state, source/target/edge, generation and
raw skip operands/result. A final black movie frame cannot prove the fade.

Check the original 29→30→31→32 first-three path for its explicit Out and absence
of an additional drop, plus existing ordinary movie successors/scene-title
retirement. Check available real choice/out/stay/hidden cases as existing
renderer regressions only; report unavailable script cases as uncovered.
Observe one real Stop/replay interruption of the new drop if that cancellation
branch remains unobserved. Do not create scripts, delay requests, fire synthetic
ended, substitute a clock or patch a returned program to manufacture coverage.
Close all owned browser/capture/server processes before delegated image review.

After successful bounded source regression, normal saved suffix verification
is still separate. Root alone decides whether to revise/apply/build/release
the proposal, then publish each verified small source/data result normally.
