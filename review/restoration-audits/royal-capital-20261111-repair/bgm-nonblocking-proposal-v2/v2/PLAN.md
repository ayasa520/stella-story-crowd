# UNAPPLIED v2 native-node BGM submission prototype

This packet proposes one player change for root review. It has not been applied,
served, compiled, activated, or run in a browser. It changes no native fields,
commands, registry, adapters, music components, or production files.

The inspected ordinary native Director path submits SetupBGM before its matched
InitScenario completion signal. The shown Director continuation does not require
the separate music loader-success callback. This supports testing a nonblocking
submission boundary; it does not prove the recording's deployed route, a total
order of resource/CardIn/text completion, or the original cue-zero.

## Exact proposed behavior

`patch.diff` replaces only the await at current `public/player/player.js:376–379`
with `submitNodeMusic(node,generation)`. A new method owns promise diagnostics;
the existing MusicPlayer still owns fetch/decode, request generations, old voices,
replacement, Stop, fades, and audio sample clocks. Detailed English comments in
the candidate state the native evidence and the limits of this proposal.

- Submit the same resource/options/key at the same script position, then continue
  phase0, background/CardIn and text without joining this music promise.
- Publish `state.bg_music` as **desired route state at submission**, while logs
  separately expose the actual current/loading resource. The previous track may
  remain audible. This deliberate state-timing change needs runtime validation.
- Capture immutable owner node, Player entry generation, MusicPlayer generation,
  resource/options key, and submission time. An inherited successor may keep the
  same music request alive. Advancing the story alone must not cancel that load.
- Attach both apply handlers and their terminal observer before the first
  diagnostic sample. `safeReport` encloses sampling, serialization and host
  output; its fallback logger has its own catch. A broken snapshot/logger cannot
  leave the apply rejection unobserved, skip `fail()`, or reject the terminal
  observer promise through this new diagnostic path. Error ownership and error
  delivery are evaluated outside diagnostic sampling. Existing component and
  `fail()` internal loggers are unchanged and are outside this narrow guarantee.
- Log SUBMITTED, SETTLED, FAILED and observer errors with original owner and
  observation context. Timestamp sampling now occurs inside the safe boundary,
  rather than before attaching handlers. Promise settlement is not PLAY or fade
  completion; retain existing STORY_BGM_PLAY/FADE events for those boundaries.
  If both primary and fallback output fail, diagnostics can be lost; that is not
  a claim of successful reporting, but it must not change the music/node policy.
- A rejection still owned by both the current entry and music request invokes
  existing `fail()` behavior. A late rejection is recorded for its original owner
  without invoking `fail()` against a newer node. This is an explicit prototype
  error policy, not a reconstructed original error policy.
- A music generation change means `superseded_or_stopped`; do not invent which
  action caused it. MusicPlayer already suppresses stale prepare rejection, so
  the caller cannot recover/log its hidden underlying cause without a separate
  component-contract change. This proposal makes no such change.
- Random-entry `restoreEntryAudio()` and authored phase `StopBGM` retain their
  existing awaits byte for byte. No Wait/phase/fade/restart value is added.

## Offline verification supplied here

The generator refuses a different player SHA and refuses to overwrite a prior
packet. It references v1's unchanged exact BEFORE source copies in the parent
`revert ...` directory, emits only new v2 files, and verifies reverse equality.
The candidate is syntax checked with `node --check`; that is not runtime QA.
The source-after receipt must match all four BEFORE source hashes. Historical
actual raw controls and failed native slot probes stay unchanged and referenced.

## Future runtime QA, only after root review and sole-browser authorization

First freeze the exact source, selected scene/review guards, compiled programs,
actual music payload and metadata. Validate served source bytes before/after.
Use one fresh named Canary at nice19/CPU22,23, close in `finally` and prove CLI/OS0.
No synthetic media events, seeks, autoplay-policy changes, authored Wait, added
phase, screenshots, or subjective audio claims are required. Keep any failure or
partial output; do not silently rerun. No unit tests are proposed.

1. **Loading/text comparison.** Reuse the existing guarded P25 fade0/1 memory
   variants, each 10170002:7→8→9 once. Rebind current scene guards first. Keep
   the resource and source zero identical to the prior controls. Record submit,
   actual prepare start/settlement, PLAY, phase0, real CardIn events (or absence),
   text_begin, glyph progress, phase2 and successor entry. Record performance,
   shared-clock frame/game time, AudioContext time, source identity/began/sample
   progress and volume. Existing baseline measured command-ready→phase0 waits of
   731.2/677.8ms and PLAY→text_begin 1.8/2.4ms. Do not require a particular new
   millisecond difference: observe whether text can begin during real loading.
   The old outgoing recording mix remains unrestored; these controls only test
   the new cue and scheduling, not complete recorded music reproduction.
2. **Gain and continuity.** Sample after all synchronous shared-clock listeners
   (the reviewed queueMicrotask phase with trigger/observed snapshots). Assert
   same frame/game time, unchanged music generation, correct gain against the
   component's actual target volume, one source starting at zero, and node8→9
   source/began continuity. Inherited node9 may be entered before prepare settles;
   its new Player generation must not suppress that still-current music load.
3. **Pending Stop.** With an observed real `music.loading` request, use actual
   Stop UI. Record exact request generation and Stop generation. Let that request
   settle; it must not create a late source, restart a fade, or mark a new node
   errored. Repeat playback only if separately needed to test the next scenario.
4. **Pending replacement and return to the old track.** Root must approve a
   separate guarded memory-only fixture using existing catalog resources and a
   real route successor. While load A is observed pending, execute replacement B;
   also cover returning to the already-playing old track. A's late resolution
   must not create an audible source, and existing source/sample time must remain
   continuous when its non-restart assignment wins. No formal music fields are
   inferred from this mechanical control. Compile/guard that fixture before any
   browser, rather than inventing a route or field during the run.
5. **Failures and attribution.** Exercise an active-owner rejection and a
   rejection after inherited successor entry, plus a superseded pending rejection.
   Genuine fetch/decode failures may not occur naturally. If they do not, mark
   these cases **not covered**. A separately approved isolated HTTP failure/hold
   control may test the branch without altering production code; it must be
   labeled fault injection and excluded from original playback timing conclusions.
   Expect FAILED owner metadata; only a still-current owner may stop/error its
   entry. Stale component rejection can surface only as cancelled settlement with
   no underlying cause. No unhandledrejection or duplicate current-node error.
6. **Preserved awaits.** Check a random-entry inherited BGM restoration and an
   actual authored phase StopBGM using an existing real compiled route selected
   before activation. Both call sites remain byte-identical. Verify prefix-stop
   filtering still avoids a spurious restored snippet. Avoid unrelated regressions.
7. **Historical smoke routes in episodes 1/2/3.** The episode labels are
   confirmed by the current manifest, as independently checked by the peer. The
   user has already confirmed full manual acceptance of the first three episodes;
   that acceptance stands and is not being questioned or reopened. This proposed
   code regression QA samples only these historical real edges:
   10010001:5→6 (branch1009), 10140003:3→4, 10190004:7→8→9 (branch82).
   Record compiled IDs, actual branch choice, text, music source, desired/current
   state, unhandledrejection and errors. These sampled routes are rendering/flow
   smoke coverage, not the evidence establishing the user's broader manual
   acceptance or complete branch coverage. Original19 byte protection is also
   a separate scope; it cannot be promoted into manual-acceptance proof. In
   episode2, rows3/4 both explicitly assign the same BGM: if row4 enters while
   row3 still loads, record which music generation owns the one eventual source.
   Do not add unrelated movie trials or new original-video signoff.

Natural loading is preferred. If a pending condition cannot be observed before
the required UI action, record it as inconclusive rather than passing that case.
No extra trial, failure injection, registry activation or browser is authorized
by this proposal. Root should review and scope those separately before execution.

## Acceptance boundaries

Root may accept the prototype only after the loading/continuation/error branches
are covered or explicitly left blocked. Passing these checks validates the
website's new behavior and cancellation integrity. It does not sign an original
CSV, phase, Wait, fade, restart, original runtime rate, original loader latency,
exact cue-zero, the unrestored outgoing mix, or complete original total ordering.
The archived native/HTML graph investigation stops at its already stated limits.

## v2 review delta and remaining policy

This new directory preserves every v1 file. It addresses only the peer's bounded
observer exception-safety issue and the QA scope wording. It does not apply a
production fix or change the desired-state/late-failure policy. If desired A fails
after an inherited successor while old O plays, A may remain desired, O may keep
playing, and an inherited node does not retry A. Root's explicit acceptance and
runtime QA for that policy remain pending. A phase StopBGM can now overlap pending
node loading; preserving its source bytes alone does not validate that overlap.

The no-throw diagnostic argument is a static control-flow review only. No new unit
tests, injected loggers, browser, runtime or production edits were performed.
Separately scoped future mechanical QA can cover snapshot/serialization/logger
failure, including failure of the fallback output, without claiming original
timing evidence. Root must authorize that scope first.
