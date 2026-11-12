# Single BGM resource candidate prepared

`bgm_adv_kinpaku02_cd2_18` is prepared with the existing `MusicPreviewExporter`,128k stereo Opus plus its unchanged native-metadata representation. The candidate is isolated under `assets/music/` in this folder. No formal catalog/assets/source/config, story field or Git state was changed. Root's subsequent ordinary-player comparison and recording-onset review remain separate.

| Native parameter | Direct ACB evidence |
| --- | --- |
| Cue and references | CueName `bgm_adv_kinpaku02_cd2_18`, CueId0, ReferenceType3 → Sequence0(Type0,one track,PlaybackRatio100) → Track0/Event0 → noteOn2000(`00020000`) → Synth0(Type0,`00010000`) → Waveform0 |
| Native waveform | Streaming AWB ID0,stereo,44,100Hz,8,414,915samples =190.81439909297052s |
| Native loop | LoopFlag2,extension0:266,721→8,414,915samples =6.048095238095238→190.81439909297052s |
| Startup events | This track contains noteOn2000 then end0, **no opcode998**; exported `startup_events:[]`. This does not establish998 semantics in other cues. |

Exact original sources are `data/extracted_archives/original/com.sega.stella/files/AssetBundle/assets/bgm_adv_kinpaku02_cd2_18.{acb,awb}`. The rendered source member is `LIMEOS/audio/bgm_adv_kinpaku02_cd2_18/bgm_adv_kinpaku02_cd2_18.wav`, physically under `data/extracted_archives/limeos/`. `native-binding.json` retains only this cue's exact reference rows, track events, waveform and extension.

The LIMEOS WAV has17,004,109stereo PCM frames at44,100Hz (385.5807029478458s). The original waveform has8,414,915frames. Their difference is8,589,194frames: precisely one8,148,194-frame native loop plus441,000frames (10s), consistent with the rendered extra-loop/fade source handled by the normal exporter. The trim is **sample0 through8,414,915 in the44,100Hz source domain**, before resampling. It is neither a correlation-offset cut nor a trim based on the rendered WAV duration. No gain normalization, tempo change, inferred startup delay or new loop was applied.

The exporter encoded48,000Hz stereo Opus and decoded it back to9,159,092PCM frames,190.81441666666666s. The difference from native duration is0.8435of a48kHz sample, within the established one-sample exporter tolerance. Native loop endpoints fit the decoded preview. Opus is3,029,256bytes, SHA256 `841deac44eb47f029d35fd3eeb05cac1f7559de5cb9ea03743003da01539fa89`; metadata is289bytes, SHA256 `cd4d29c6298377af53252d92a7105c3f2eddb40c9d7454818623255cafbe1037`. `exported-files.json` contains the normal exporter's two file records; `export-commands.json` retains both successful FFmpeg invocations, nice19/CPU0,1 and explicit decode/filter/encode thread bounds. Temporary exporter output was outside the data tree and removed after copying these two completed candidate files.

The earlier identification results are reused, not recomputed: three-second source windows420/480/520s score0.95030595/0.97931047/0.97360157 against the rendered reference. Their reported reference offsets23.251/83.251/137.267s are matching positions in that rendered reference, **not native cue-zero timestamps or a recovered story onset**. No P30 `bg_music` field is proposed here.

The minimum resource integration is the three exact additions in `catalog-additions.json`: one `music[resource]` row and the same original-member→Opus-URL mapping in both `members` and `asset_members`, plus the two payload files. All three keys and both formal payload paths were absent at preparation; recheck those scoped conditions when installing. Preserve the existing18music rows and every unrelated catalog entry. The supplied file records allow the normal package publication step to index these two files without rebuilding the library. No original WAV is added to the public asset payload, and preview URLs never become native story values.

`catalog-additions.json` remains noninstallable and `rootConfirmed:false`. This preparation proves selected native parameters, bounded waveform trimming and successful encoding/readback; it does not accept audible playback, source onset/fade boundaries, native startup-event behavior in other tracks, or complete P30 music performance. No browser, installer, whole-library regeneration or recognition rerun was used.
