# Kinpaku02 private runtime: independent evidence review

**Pass for the bounded original-player transport observation.** The supplied `private-bgm-result.json` and `root-bgm-transport-readback.json` are consistent with the reviewed v3 driver/observer/compiler projection. No new browser, decoding, audio measurement, capture or formal/Git edit was performed. Audible output, full loop wrap and original P30 timing/phase/gain remain unaccepted.

The inputs are the two named JSON files under `p30-ending-normal-runtime-20261113-v1`. Source review used `p30-kinpaku02-private-playback-proposal-20261113-v3/{driver-factory.js,observer-factory.js,production-compileMusic.js}` and its readiness-revision note. V3 retains K1/K2 and adds the real-player pathname/body guard before installing observation; it does not alter playback/projection/hook behavior.

## Projection and original ownership

Exactly one normal program GET is recorded, with no route failure. Its proof names10450056:2 / stable key`s10450056-p30-at0397` and exactly two compiled fields: raw `bg_music` changes from empty to the bare resource, while `music` changes from inherit to play. Fade1 and restartfalse come from the production projection/default, not extra test parameters. Restoring both fields deep-compared equal to the whole fetched program; no other derived snapshot changed and `persisted:false` remains set. This is1authored/2compiled, with no authored Wait added.

The observer imports the shared classes actually reexported by the player, constructs no alternate channel, and captures the production apply receiver and the voice already present in its `players` set. Actual evidence contains one apply and one original-voice-start event, one retained voice, no observer errors, and the same resource/voice `began` value0.6506666666666666 across node2 and both node3 snapshots. Current music remains active, unmuted, output gain1, with recorded voice gain0.4000000059604645.

## Resource, decoded duration and loop configuration

| Existing runtime evidence | Recorded value |
|---|---|
| Metadata GET | `/api/music/bgm_adv_kinpaku02_cd2_18`, HTTP200,289body bytes,47.7ms ResourceTiming |
| Audio GET | `/music/bgm_adv_kinpaku02_cd2_18`, HTTP200,3029256body bytes,84.4ms ResourceTiming |
| Native metadata |8414915samples /44100Hz =190.81439909297052s; cue0,looptrue,startup events empty |
| Actual decoded buffer |9159092frames /48000Hz =190.81441666666666s,stereo |
| Actual context / buffer rate |48000 /48000Hz, observed rather than imposed |
| Source loop |6.048095238095238→190.81439909297052s, exactly matching metadata |

Decoded duration exceeds native by0.000017573696141s, within the source's0.000041667666667s tolerance (one installed-preview sample plus one actual-context sample and epsilon). Buffer-length/rate and native-samples/rate arithmetic independently agree with the recorded durations. Loop endpoints are valid inside the native duration. HTTP timings are network ResourceTiming only, not decode CPU cost.

## Gesture, progress and cleanup

A trusted viewport pointerdown at node2ready is recorded at performance11149.2ms; the existing player then follows its normal edge to3. **The context was already running before this click**, including the node2ready snapshot. Therefore this run demonstrates trusted input plus running transport, not that this fresh click caused a suspended context to unlock.

At the two node3ready samples, context time3.552→5.557333333333333 and existing voice progress2.9013333333333335→4.906666666666666 increase by2.005333333333333s and2.0053333333333327s respectively. The separate root readback reproduces both differences and the same buffer, metadata, source loop and gain. The source-progress getter is not an audio-output analyser or audible listening proof.

Normal Stop reaches `phase:stopped`, `active:false`, no loading/current resource/current voice, zero players and no fade subscription. The retained original voice is ended. Its reusable AudioContext remains running, which is compatible with production Stop and does not imply an active source. Uninstall reports no snapshot error, `allRestored:true` and no conflicts; source cleanup covers the three original descriptors, pointer/state listeners and owned slot. Route removal succeeds and all three host listeners are removed. Driver, observer, route and final-snapshot error arrays are empty.

This audit accepts only the supplied run's bounded transport/configuration/cleanup evidence. It does not newly audit OS/process closure, replay the story, observe a190second wrap, listen, or recover the original onset/fade/gain/restart/phase. Root review/confirmation remain separate.
