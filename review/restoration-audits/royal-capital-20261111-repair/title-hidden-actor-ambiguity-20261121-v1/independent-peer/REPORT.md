# TITLE hidden-actor ambiguity v2: independent offline peer pass

`rootConfirmed=false`. Reviewed patch
`da2d4f9ef8e6e6a0f255fd670f44f1074a6f2db1b6b19fe592fc81c9231c6e20`
and existing actual-API proof
`ab8d9be1373ee49b7fc39f3e591e10becea1a2ab87b33a5dbf0660aefa53d702`.
No blocking issue was found for the current scene10100012 TITLE and its
documented node3 reset/node4 explicit re-entry. This is an offline source/API
evidence pass, not a formal fix, HTTP-server, Workers, browser or GPU pass.

- **Scope is narrow.** Filtering requires `kind==="title"`, empty authored
  `model` and no authored `actors`. A title carrying its own solo model or
  cast gets an empty filter set and keeps the previous blocking behavior.
  This matters because both Players can prepare that authored model/cast in
  `enter()` before dispatching `title()`. The guard excludes that path.
- **Only diagnostic projection changes.** The diff touches the final
  `ambiguous` collection. It never writes `before`, `entry`, `display`, `after`,
  native data or selected incoming choices. Labels and derived upstream
  selectors continue to follow the remaining blocking fields. Unknown state
  is preserved rather than silently assigned a motion/default predecessor.
- **Nested fields are handled correctly.** `model/body/face/face_reset/extras/
  actors` are excluded only for this empty-actor title. The extras child loop
  also skips `extras.layer` nulls. The ambient child loop still runs; BG/clut,
  BGM, ambient/cues, wipe fields and junction remain eligible blockers.
  Unsupported command/resource diagnostics and effect processing are unchanged.
- **The actual title path does not consume hidden body state.** Both title()
  methods clear their scene canvas and call display(empty); lighting reads
  only background/clut. The empty authored model/cast avoids actor preparation
  in enter(). clearCommand is not a native Animator reset, and this patch
  does not claim or implement one.
- **Current null-before path has an explicit reset.** start() clones before;
  ActorStage.reset tolerates null with `(states||[])`, and lighting explicitly
  handles unknown BG/clut. Current node3 has no authored actor, installs the
  fruitshop background and its own BGM, skips motionSelection, then clears
  logical model/body/face/face_reset/extras in the empty-foreground branch.
  It also clears cast state. Node4 then explicitly loads Subaru01 and selects
  act_tameiki. No old null body is consumed by this route. This is not a claim
  about every possible later route or about visible same-actor inheritance.

I independently reread all nine baseline/candidate groups from the existing
proof. Each before/entry/display/after and music/phases/unsupported/warnings/
incoming object is equal. Eight complete resolve results and their successful
prepare-program SHA values are equal. The sole changed group is unselected
TITLE2: ambiguous `[bg_picture,body]` becomes `[bg_picture]`; it **still returns
422**. Both selected TITLE routes and all node3/4 cases remain 200. Unselected
node3 already returned a genuine before.body=null and before.bg_picture=null
in the baseline, with a resolved empty actor and explicit background afterward.

The proof uses the real canonical POST handler, studioPost, section projection
and resolver in process: 36 handler invocations across baseline/candidate,
resolve/prepare and nine groups. Its source was reviewed: only Workers env and
repository transport are bridged, readBatch delegates to unchanged validated
read(), and every raw read is fixed to db238432 and byte guards. There is no
override, fabricated program, HTTP listener or GPU. Cloudflare limits, GitHub
auth/GraphQL and the browser are explicitly unexecuted. I did not rerun those
handlers or create synthetic test scenarios; this peer independently validates
their saved results and source/provenance.

Coverage limits remain explicit: the real TITLE has body/BG conflicts, not
separate conflicts in all six hidden fields. Extras sublayers, explicit-title
actor exclusion and absent ambient/effects-conflict cases are source-reviewed,
not separately executed cases. Preserve that boundary in later acceptance.

All 59 source/data/evidence guards were freshly checked. Data remains clean at
`db23843217c80693e893279c1f60760105997510`; canonical HEAD remains7f32a3c with
root's two existing Player retirement edits and pycache preserved exactly.
Candidate state is not applied. No browser/server, build, source/formal write,
stage/install, test-code creation, commit or publication occurred in this peer.
