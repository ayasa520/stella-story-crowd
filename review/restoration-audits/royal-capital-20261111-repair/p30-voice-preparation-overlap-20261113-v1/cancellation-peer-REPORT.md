# Actual voice-preparation cancellation: independent mechanical review

**Pass for the three recorded cancellation cases.** Read only the retained `../p30-voice-preparation-stop-runtime-20261113-v1/probe-result.json` and closure; no new source review, runtime, image, decode, browser or formal/Git change. Independently checked every one of the24 follow-up samples, event/production-log boundaries, original-channel identity and cleanup. Case results alone were not used as proof.

| Case | Direct recorded boundary | Independently checked follow-up |
|---|---|---|
| A |34.voice_prepare_begin, original voice/src absent; actual Stop changes channel generation7→8. Bank result is200; old transport generation4→5 logs cancelled. |8 consecutive frames290–297:34 stopped, original owner/audio, src empty, no voice/pending/blocked playback, paused/currentTime0. |
| B |Original loadstart has pendingPrepare=true and the real cue. Stop changes channel8→9 and clears it; old transport4→5 cancels. |8 consecutive frames280–287:34 stopped, no voice/pending/blocked playback, paused/currentTime0. Late canplay and retained src do not restart playback. |
| C |The real ordinary35 response is200 with private attribution absent. The passive receive-entry event observes34 already stopped, channel9, pending false and voice null; old transport4→5 cancels. |Normal35 ready, then8 consecutive frames570–577: same original owner/audio, no old voice/pending/blocked playback, paused/currentTime0. |

The three child document timeOrigins are1794545338062.3,1794545348259.8 and1794545359456.5ms; they remain separate. Each follow-up frame is newer than its case's cancellation frame, sequential, rate1 and in that same child document. Case C's parent queue timestamp has a separate timeOrigin and is not subtracted from child times. The immediate queued-message snapshot still has pending media, which is compatible with the stated cancellation boundary: **synchronous receive entry**, not message queueing.

Across the retained case media events there are no play/playing events and no production STORY_VOICE_PLAY. Each old34 preparation has started then cancelled, without old ready/joined. Node35's fresh no-cue preparation is a new generation and is not counted as an old completion. A/B remain stopped; C reaches35 ready and the final normal Stop clears it.

Each probe reports its10 owned listeners/subscription removed with empty probe/cleanup error arrays; the C parent bridge reports sent=true/removed=true. Host cleanup errors, playerErrors and page error list are empty; cleanup returns without handle-disposal errors. One generic console404 in A has no resource URL and remains unattributed. It does not justify an entirely error-free-console claim. Closure reports CLI/browser/adapter exited, matches[], no recording, and all steps0.

This accepts mechanical cancellation for these actual bank/media/receive paths only. It does not accept original timing/CSV/phase, audible listening, Julius body/face, whole episode, or an exhaustive future-race guarantee. The separately reviewed ordinary voice/ordering run is outside this receipt.
