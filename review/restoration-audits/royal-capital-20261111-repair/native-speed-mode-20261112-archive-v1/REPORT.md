# Original ADV speed switch and recording comparison boundary

This static audit uses the same original APK 1.19.7.39168 binary, metadata and
assembly-specific method tables as the entry-order audit. It changes no player,
native field or preview rate and does not run a game or browser. Root inspected
only code, numbers, object records and file digests.

`ADVPlayer.get_IsSpeedMode` reads a Boolean at instance offset 0x99; its setter
only stores that Boolean. `get_SpeedModeTimeScale` reads the configured float
at 0x1c. `GetTimeScale` (0x124cedc) returns one when speed mode is off or a card
is being selected, otherwise the configured float. `UpdateTimeScale`
(0x124c8fc) has an additional Boolean argument: its true branch directly uses
the configured float, so an OFF indicator alone is not an unconditional
measurement of global Unity time throughout all transitions.

The update calls `TimeScaleManager.SetTimeScale` (0x13280ac), which stores the
requested scalar and calls `UnityEngine.Time.set_timeScale` at 0x1668b78.
ResetTimeScale writes one to Unity; RestoreTimeScale writes the stored scalar;
ClearTimeScaleSetting resets both stored and Unity values to one. These calls
establish that the native mode can affect Normal Animators and deltaTime-based
gain ramps. They do not measure the active scalar in any particular recording.

`View.SetSpeedModeView` (0x168d464) activates its first referenced GameObject
using the mode Boolean and its second using the inverse. The original extracted
root-menu inventory separately contains OFF and ON button groups, and BOTH
contain the value text `×5.0`. OFF text is approximately RGB
(0.9373, 0.9569, 0.9647), using btn_sub_menu_01; ON text is approximately
(1, 0.1647, 0.5020), using btn_sub_menu_02. The six exact rows, source-manifest
digest and two sprite-file digests are in original-speed-menu-witnesses.json.
Thus the numeral by itself cannot establish that speed mode was enabled.
The inventory's flattened active flags are not a recorded runtime state.

This changes the next comparison step: inspect the original full-frame ON/OFF
appearance before using a recording's label as a timing clue. Continue judging
complete visible motion trajectories independently of lost CSV uniqueness.
Any per-recording mode conclusion must be attributed to the actual subagent
image reviewer, and neither a mode indicator nor a nominal timeScale alone
recovers command onset, native frame deltas or Animator-local speed.

The traces use next-indexed-method upper bounds rather than recovered function
size symbols. The original scene's custom MonoBehaviour typetrees could not be
fully read by UnityPy; those exact diagnostic errors are retained and no custom
serialized field values are claimed decoded by that attempt. An initial lookup
of nonexistent ADVPlayer.Update also failed before producing evidence; the
actual named time-scale methods above were subsequently resolved. No installed
data, native performance acceptance or chapter completion is implied.
