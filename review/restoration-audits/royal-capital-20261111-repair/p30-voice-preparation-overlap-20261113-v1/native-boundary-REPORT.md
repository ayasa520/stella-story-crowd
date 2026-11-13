# Julius34: voice preparation and native motion-entry boundary

**A concrete extra ordering constraint exists in StoryPlayer.enter:** the browser waits for dialogue media preparation after committing a running body motion and before starting CardIn. The retained original control flow puts normal speech dispatch at the later TextPanel boundary. This supports investigating a deferred voice-preparation join in the transport owner; it does not support freezing hidden character animation, restarting all motions at CardIn, or adding a Wait/offset.

## Primary retained native evidence

All paths below are existing evidence; no new native-wide scan/disassembly or native execution was performed.

- `../native-motion-entry-20261111/entry-order-native-capstone.txt`: InitScenario0x124d7b0 calls SetLive2DChara at0x124d950. UIController.SetLive2DChara0x16891e0 stops prior HCA speech at0x1689240 and dispatches View.ShowLive2D; its completion argument is null. Existing-model Util.Play can call PlayMotion0x128a5ac immediately; a new model's asynchronous completion calls PlayMotion0x1320048. The retained `REPORT.md` distinguishes these requests/completions. This is not a universal awaited model-ready or motion-restart-at-CardIn barrier.
- `logs/adv.html:7000` PlayScenario sends the scenario ID without awaiting that expression, then awaits phase0. **CardProc at7216** awaits SetBG+SetImage, then CardIn, then command[1], then PanelSequence. **PanelSequence at2233** dispatches the native TextPanel request. This HTML order does not establish a total order between every independent native model-load completion and CardIn.
- Native UIController.ShowTextPanel0x1688970 calls **PlayNormalVoice at0x1688a54**, then View.ShowTextPanel at0x1688a8c. Inside PlayNormalVoice0x1688c80, **0x1688cac calls ADVUtil.PlayVoiceFromScript**; the following character path dispatches lip motion at0x1688cdc. Thus normal voice dispatch is after CardIn and phase1, immediately before text-panel opening—not a mandatory speech-ready join before CardIn.
- Original CardBehaviour.In/Card_wait→Card_in updates the card animator. The retained original Animator configuration and control chain do not establish a blanket pause of the character animator while hidden. Phase0/native Wait can consume time while that character continues animating. Preserve this known behavior.

This evidence does **not** prove that the original performs no earlier preload, no cached audio lookup or no internal I/O. It proves the shown executable speech-dispatch boundary and provides no original prerequisite requiring browser HTML media readiness before CardIn.

## Actual local ordering and measured slice

Read-only canonical `public/player/player.js`≈375–456 selects/resumes the actor motion, then awaits `dialogueVoice.prepare(await voiceResource(...))`, prepares text/command resources, runs phase0, awaits background/lighting, and only then CardIn. The later speech play boundary remains after phase1. `/player/dialogue_voice.js` re-exports `public/studio/dialogue_voice.js`; `prepare` stops the prior cue and can await the original HTMLAudioElement's canplay/error/cancellation event. The corresponding Studio transport has the same placement. The clock and actor animator are separate owners and need not change to remove this serial dependency.

The retained v3 `../p30-julius34-body-hold-runtime-20261113-v3/body-result.json` records:

| Boundary | Actual value |
|---|---|
| Julius act_egao commit | frame491, Normal game14.949334686534876, wall17086.90000000596ms |
| CardIn start | frame516, game15.366034686534864, wall17495.40000000596ms |
| Between these boundaries | **0.4166999999999881 game seconds**,408.5 wall ms |
| Transport voice_prepare_begin→voice_ready | node-relative1753→2148ms (**395ms**) |
| DialogueVoice's inner prepare log |270.5ms; bank lookup/other scheduling is outside that inner measurement |
| Following preparation | text_ready2149ms; command_resources_ready/phase0 begin/end2150ms |

The entire commit→CardIn slice includes this awaited bank/media preparation and the subsequent short work; it is not independently partitioned into per-task game-time contributions. The measured395ms transport interval must not be called solely audio decode time. CardIn's following own animation also advances the actor. These logs explain an avoidable browser ordering dependency, not the whole visual difference or an OS/GPU cause.

## Smallest source-backed candidate change, not implemented

Keep the current body selection/resume point and current dialogue-channel choice. At the existing post-model/motion preparation position, **start one generation-owned voice preparation promise without awaiting it there**. Keep its actual metadata lookup and prepare operation; join that same promise only after CardIn+phase1, immediately before the existing play/text boundary. This permits voice readiness to overlap independent entry/commands and prevents readiness alone from holding a hidden running motion before CardIn. It preserves voice readiness before actual speech and introduces no new audio instance, native field, Wait, speed, offset or motion-clock policy.

Implementation belongs to **StoryPlayer.enter orchestration**, with DialogueVoice retaining media readiness/Stop cancellation. Check the player generation immediately before assigning a resource to the channel; a stopped/stale bank response must not prepare a newer node's audio. Retain a rejection handler immediately so no rejected promise is orphaned; actual failure must still stop/report through the current generation, and Stop must cancel pending prepare. Do not prepare the actor's audio before a model-load/stop operation that would invalidate that same channel. Both player and direct-Studio transports need the same bounded ordering change. Other resource barriers remain separate, unproven concerns.

Log one preparation begin/settled/join boundary with the existing node/generation and clock snapshot if Root implements this candidate. The next necessary comparison should verify the first actually visible Julius entry and full body process against the retained source, plus normal voice once/ended/Stop. **Motion remains unaccepted** until that image verdict. Removing this barrier is not a guarantee that act_egao will match the original open-eye entry.

No production/formal source, story data, Git, browser, compile, images or decoder were touched. The two original-versus-actual body observations are reviewer/Root findings reused here, not a new image acceptance by this investigator.
