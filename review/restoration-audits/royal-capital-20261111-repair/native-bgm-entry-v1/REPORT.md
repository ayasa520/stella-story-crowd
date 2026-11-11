# Original BGM setup, loading callback and fade clock

This is a static audit of APK 1.19.7.39168's original ARM64 binary and decrypted
metadata. It does not recover any new node field or measure native runtime
latency. No game, browser, image viewer or device instrumentation was started.

The original entry-order evidence binds `ADVPlayer.InitScenario`'s call at
`0x124d86c` to `CommandUtil.SetupBGM` (`0x17087e0`), before SetLive2D within
InitScenario. InitScenario itself runs from the SendScenarioID background
completion callback. The HTML issues SendScenarioID without awaiting it and
then runs phase 0 / CardProc; those facts do not prove a total order between
all native resource completions and CardIn/text. Setup's ordinary path supplies
`cross_fade = 1.0` and `reset = false` to `Stella.Sound.Player.PlayBGM`
(`0x15a59c4`). The separate command-prefix branch resolves to the original
literal `stopbgm`; it is not evidence for a new PlayBGM script command.

`PlayBGM` preserves the resource, float and reset flag in its closure and
submits `Stella.Sound.Loader.Download` (`0x15ab6b0`). Its delegate construction
GOT slot `0x2d36948` resolves through the original metadata-usage pair to
`<PlayBGM>b__0`, token `0x06008702`, at `0x15ac50c`. The success callback calls
`SGNFW.CRI.Sound.BGM.Player.CrossFade` when the float is positive; otherwise it
calls Play. Download submits two AssetBundleLoader downloads for the useAwb
path. Its completion closure combines success and decrements a count before
notifying its caller. These are completion conditions, not fixed Wait values.
Whether either underlying download callback runs immediately or later in a
particular native session is not measured by this audit.

The original CrossFade signature names the float `duration` and starts
`ProcCrossFade(from0, to0, from1, duration)` as a Unity coroutine. Its MoveNext
initializes elapsed to zero and the reciprocal of duration, interpolates the
new and outgoing node gains with `UnityEngine.Mathf.Lerp`, then advances
elapsed with `UnityEngine.Time.get_deltaTime` (`0x16689d8`). At completion it
sets the final new-node gain and stops the outgoing node. Thus the ordinary
setup path requests a one-second linear fade in Unity game time. This does
not mean a fixed one-second wall-clock delay before text or an audio sample
clock tied to the visual clock.

The current published player already has a one-second music default, but its
node entry awaits fetch/decode and its gain ramp uses performance.now. Those
two implementation differences are now recorded for a separate, scoped
runtime review. Neither difference has been hidden in authored Wait, phase,
restart, resource-offset or fade fields. No runtime change is included here.

The three evidence JSON files contain exact binary/metadata/script receipts,
assembly-specific token bindings, parameter names, metadata-usage mappings and
bounded disassembly receipts. The bounds are the next indexed method address,
not recovered function-size symbols. Indirect and unlabelled calls remain
explicit. The corresponding text dumps and inspector source snapshot are
archived with this report; source input paths refer to the local restoration
workspace, and the snapshot is for review rather than execution in this data
repository.
