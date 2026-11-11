# Original background, BGM submission and text boundaries

This supplement adds bounded text/card-start edges to the archived BGM audit.
It does not approve a website change or a new native field. No browser, native
game process or device instrumentation was started. All computations used
nice19 and CPU22/23; old evidence and the one failed-slot probe are preserved.

The native Director has an explicit completion gate. `Main_Init` step0 calls
`ADVPlayer.SendScenarioID` at `0x1711c30`, then installs `Wait(NextStep)`.
The delegate slot `0x2cfb8a8` resolves to `Director.NextStep` through the
original CSharp metadata usage pair. `Wait` registers a callback with
`ScriptManager.SetReturnCallback`; the manager later checks its `isWait` and
`isReturn` latch and schedules `Context.WaitFrame(1, callback)`. The matching
background-completion callback calls `InitScenario`, then `ReturnSuccess`.
`NextStep` clears the completion latch and advances to phase0. This is an
internal continuation mechanism, not an authored script `Wait` duration.

Inside the already audited `InitScenario`, ordinary `SetupBGM` submission
precedes SetLive2D submission. Neither call is shown waiting for music/model
asset completion. In particular, music loading succeeds on the separately
bound `PlayBGM` loader callback before CrossFade/Play. That success callback is
not an inspected prerequisite of the Director text step. This distinguishes
background/init completion, BGM submission and actual music playback.

The exact native Card step table was read from `0x22dc77c`: optional image,
CardIn with completion wait, phase1, SetTextPanel with completion wait, phase2,
user operation, then phase change. Text connects through
`SetTextPanel → UIController.ShowTextPanel → View.ShowTextPanel → TextPanel.Open`.
Open selects immediate text or PlayText; PlayText selects SetAllText or
StartTextAnim according to speed/options. The normal update uses Unity
deltaTime after its CanPlay gate. The finished-text closures return through
the UI and `SetTextPanel` callback to ReturnSuccess. No exact glyph timestamp
is established by these static method calls.

The original HTML is a separate proven producer path. It does not yield
SendScenarioID, but does await phase0 and the ordinary CardProc chain:
conditional SetBG/SetImage, CardIn, phase1, TextPanel completion, phase2.
Toroste sends each request and registers a next resolver by its own callId.
The native request-drain loop itself has no ReturnSuccess-latch gate; this
does not say which future requests JavaScript has actually produced or awaited.

The reference recording's selection between this native Director route and
the archived HTML route was not dynamically established. The exact
`Unity.call`-to-native TextPanel function-table registration was not bound in
this investigation; the native Director direct call must not be relabelled as
that missing bridge. The completion latch is global, so complete concurrency
and stale-callback correlation are also outside this proof. Background prefab,
texture, model, music and text-layout completion still have no universal total
order here. Inline-ready and delayed callbacks must remain distinct cases.

The current memory runs independently measured PLAY before phase0/text after
the website's awaited load. The original aligned resource zero lies inside an
already-started, incomplete text line. These observations and this static
supplement justify a scoped loading-order investigation; they do not authorize
removing every await, adding phase/Wait/PlayBGM, or choosing an original CSV,
literal fade or restart flag. The old BGM report's website wall-clock paragraph
is historical; current372 already uses the independently verified shared
game-clock gain ramp.

`boundary-supplement-evidence.json` binds the original binary/metadata/HTML,
all bounded dumps, delegate/literal slots, decoded jump tables, conditional
facts, missing edges and related current-run receipt. The invalid supplied
VA0x2d090c88 and partial pass3 dump remain untouched; its corrected arithmetic
VA0x2d09c88 was inspected under a new prefix.
