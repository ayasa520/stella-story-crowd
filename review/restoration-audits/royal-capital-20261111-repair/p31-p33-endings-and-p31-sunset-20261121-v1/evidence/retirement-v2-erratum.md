# Movie→end-TITLE proposal v2: claim and validation corrections

**Unapplied, rootConfirmed=false; no build, runtime release, browser, formal source/data edit or commit.** This addendum accompanies the new `movie-end-title-retirement.v2.patch`. It preserves every v1 file, including patch SHA256`8fd78e53a87170956ff5ab158ffb9ed7a9e0474e8670db3ad0d43cf0142e015a` and its receipt SHA256`96439991029e215d9d4ac5e259d88adba9eb6c39a1a75e1ae9b1da6a469c6b19`.

The full independent review was read before this addendum was prepared: `../movie-end-title-retirement-peer-20261121-v1/REPORT.md`, SHA256`b417c2c930ef2638c8ec48640b880a48f4f0ca8ad8567a6ffe043ffd3c80a0ae`; structured review SHA256`f7ae3bfa67027e066638ec46fc1098931381cc9b00443024a22b01b2083a91d9`. Its limited static pass found no new blocker in the empty-command, same-scene immediate next, movie→endTITLE, in-state, skip-false path. It did not release execution or accept playback. All findings F1–F5 below remain mandatory.

## F1 — Stay preserves an existing renderer limit

The v1 phrase “retain native stay” was inaccurate. Original HTML CardDrop2618–2633 accepts **In or Stay**, and MovieProc's no-choice/non-Out default calls that operation. The existing renderer's `cardState==='in'` guard suppresses its compositor while Stay is set. Retaining that guard limits this small change; it does **not** establish native Stay correctness.

The v2 patch changes only the two English comment lines in each candidate Player. They now say that the shared skip/cardState guards preserve the **existing renderer's stay/hidden/explicit-Out limits** and the existing choice-owned drop path. The predicate, diagnostics, every executable token and the intended narrow behavior remain identical to v1. No Stay fix is added, and native Stay acceptance remains false.

## F2 — Actual compiler projection is not saved HTTP prepare

The existing `compile-preview-result.json` is an actual source7f `compilePreview` result over an **unapproved memory projection**. It statically supports P31 109→110 and P33 29→30 as next/continue/available, followed by complete with empty target. Independent peer inspection of `lib/studio-native.ts:187–198` confirms that normal Studio identity mapping remaps the IDs while preserving `flow_action`. Neither proves that those proposed suffixes have been approved, saved or returned by a real `/api/player/prepare` request.

After a separate parent release and normal save, preserve the complete real prepare response and its hash. Check the returned entry, stable/native identities, source/target IDs and all three edge actions against that saved data. Do not substitute the artifact's memory projection, force a returned program or describe compiler-only evidence as saved playback. The f8 candidate file guards remain their original frozen-base guards; this comment-only source v2 does not rebind them to later parent commits.

## F3 — Structural eligibility is not an executed drop

`movieEndTitleRetirement=true` can coexist with `animate=false`, for example when the old card is out/stay or skip is true. An execution claim requires **animate=true, one matching actual STORY_CARD_OUT_START/COMPLETE pair, actual card-root alpha descent and actual Normal-clock samples**, bound to the source/target/edge, entry generation and genuine continuation input.

Current CardOut logs provide wall timestamps/selected-card status; current STORY_PLAYER_TIMING provides node/stage/elapsed wall time. They do **not** provide Normal-clock/generation fields. The new boolean cannot fill those missing observations. No production instrumentation or test/observer implementation is introduced in this packet.

The next released browser owner must use a **read-only observer** for the missing witnesses. Record the existing title interval-decision event's actual node/generation, the real transition/input, DOM node/phase and card-root computed alpha, video currentTime/duration/paused/ended/hidden, and snapshots of the existing shared Normal clock. Do not reset, advance, replace or seek a clock, monkeypatch cardOut, alter commands or add a script wait. Capture samples before, through and after the real compositor interval. Preserve trigger time and observation time separately; an asynchronous read after a console event is not a sample taken at that event's timestamp. If the observer cannot establish generation ownership or Normal-clock coverage, mark that requirement uncovered instead of inferring it from wall duration or a black frame.

## F4 — Logical entry precedes visual title presentation

`enter()` assigns the logical target, body dataset, timing-enter and STORY_PLAYER_ENTER **before** the new retirement predicate/drop. Those early records are expected and must not be used to assert that a title was already visible.

For the production Player, require actual **STORY_PLAYER_TITLE** and subsequent **STORY_NATIVE_TITLE_ENTRY** stages to occur after the matching drop completes. The existing logical entry/interval generation can identify the owner without becoming a presentation witness. The Studio twin retains its older generic title hold and has no NativeTitleEntry stream; identify which served surface actually ran and do not transfer its timing claims to the production Player.

Natural movie ended, ready, one real Continue and the compositor interval remain distinct boundaries. This proposal changes no ready/advance/auto policy and does not claim automatic story continuation at natural movie end.

## F5 — Retain the exact small scope and first-three regression

The new execution case is limited to a normal **same-scene, immediate sequential next/continue edge from movie to endTITLE**, cardState in and skip false. Same-scene movie→ordinary TITLE, different-scene movie→endTITLE, nonmovie→endTITLE and movie→skipped tutorial→endTITLE remain outside it. These existing gaps are not accepted or fixed by this v2, and the retained Stay limitation is not native Stay signoff.

Original first-episode10010001:30 uses the real phase2 `Wait,500\nCardOut`, then tutorial31→CLEAR32. The explicit Out leaves cardState out; the incoming edge source31 also differs from retained previous movie30. Both exclude an added automatic drop. Keep those first-three script bytes and their original wait/Out unchanged. Validate one genuine existing explicit-Out regression after parent release, without turning that case into evidence for the new empty-phase path.

The existing runtime plan is amended by F2–F4: real saved prepare first, then complete natural movie, ready/genuine continuation, structural decision **and** actual drop/alpha/Normal-clock ownership, then actual title presentation/native entry, terminal complete and own-route chart. Preserve failed/uncovered cases and the independent source/data publication boundaries. No application, framework build, browser, normal save or observer execution is authorized by this addendum.
