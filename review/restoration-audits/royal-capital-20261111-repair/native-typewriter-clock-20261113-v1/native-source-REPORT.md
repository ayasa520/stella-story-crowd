# Original TextPanel order and typing clock — source evidence only

**Confirmed: ordinary native typing accumulates Unity `Time.deltaTime`, not
elapsed RAF/performance time. The inspected opening path does not wait for the
panel entry clip to finish before preparing/starting typing.** This supports
a bounded typing-clock fidelity fix, not approval of the rejected FX phase1 /
XYZ0 candidate or a new Wait/phase/card change.

This investigation read original metadata and bounded method bodies from
`data/libil2cpp-offline.so`. The13 first-selected bodies, two directly followed
TextPanel bodies and `method-bindings.json` are retained beside this report.
`extract_native_methods.py` indexes established method tables and only invokes
LLVM disassembly. No managed/native application code, browser, compiler,
decoder, runtime/global scan, mock or new test was executed. Heavy work used
nice19/CPU0,1. Existing formal/source/CSV and all sealed runtime receipts stay
unchanged.

## Hard call/order evidence

| Native method | Exact evidence |
|---|---|
|UIController.ShowTextPanel(scenario,callback),0x1688cf0|Selects a panel and tail-calls TextPanel.Open at0x1688e88; w5 is explicitly0 at0x1688e80, selecting ordinary typed opening|
|TextPanel.Open,0x1685c60|The typed branch calls PlayText at0x1685d98, then Show(false) at0x1685db8; no animation-completion await between them|
|TextPanel.PlayText,0x1686050|0x168609c/60a0 clear mTime(+0x48) and mIsPlaying(+0x45);0x16861d0 stores cached message(+0x58)/completion callback(+0x60), then clears calculation callback(+0x68). The ordinary non-fast branch tail-calls StartTextAnim at0x1686228; fast/immediate branches use SetAllText separately|
|TextPanel.StartTextAnim,0x16868a8|Stores an Action at mOnFinishedCalc(+0x68), then stops/restarts a named coroutine: StopCoroutine(string)0x1b46828 and StartCoroutine(string)0x1b46250, resolved via CoreModule method tokens0x06000624/061e|
|TextPanel.Show,0x168623c|Sets an Animator trigger at0x16862b4, then plays a selected Animator state at0x1686308. Direct icall strings resolve0x19ba2dc to SetTriggerString and0x19bad74→0x19bace0 to Animator.Play(Int32,Int32,Single). These are synchronous calls, not a clip-duration await|
|TextPanel.OnAnimEnd,0x168679c|Only checks the closing flag(+0x44), deactivates a closing object and clears that flag. No typing-start callback here|

The metadata-named `<StartTextAnim>b__34_0` body at0x1687070 calls
GetTextSpeed, stores mSpeed(+0x4c) at0x1687088 and sets mIsPlaying true at
0x168708c. `get_CanPlay` at0x1685a3c first requires that playing flag and a
nonempty cached message, followed by an additional UI-availability check;
Update calls UpdateText only after this gate.

The identified `CalcTextInfoCoroutine.MoveNext` at0x1687198 requests text info,
checks `IsValidTextMesh`, calculates font/line information and invokes the
mOnFinishedCalc field at0x168739c–73a0. Its invalid-mesh branches can yield a
frame or a retry object initialized with0.25s at0x1687404–7410. The latter
constructor is exactly UnityEngine.WaitForSeconds(token0x06000691,
RVA0x1799e38). **This is conditional mesh preparation, not a universal panel
delay or recovered script Wait.** No Wait250 is warranted.

The callback/compiler-generated name, field protocol and coroutine body
support a preparation-readiness gate. The named-coroutine/Animator-state
literals and delegate initializer point into BSS not present in this offline
ELF payload; they were not reconstructed by a new scan. Exact first-yield
engine scheduling and first composited glyph versus entry alpha therefore
remain unknown. What is directly established is the Open call order, the
absence of a clip-completion wait in that path, and that OnAnimEnd is not the
typing-start gate. Do not replace this uncertainty with "await full panelIn".

## Exact ordinary typing arithmetic

`TextPanel.Update` at0x1686fcc–6fdc gates and calls UpdateText. In its ordinary
branch:

- 0x1686e50 loads accumulated mTime;
- 0x1686e58 calls0x16689d8, CoreModule token0x060006f4. The wrapper's exact
  direct icall string at0x22b1010 is `UnityEngine.Time::get_deltaTime()`;
- 0x1686e60–6e64 add the returned delta and store mTime;
- 0x1686e74 loads mSpeed;0x1686e94 multiplies accumulated time by speed;
- 0x1686e98 uses `fcvtzs` to truncate the nonnegative result, then0x1686ea8
  clamps it to0..cachedLength. The prefix is taken and passed to TMP text;
- At cachedLength,0x1686f6c–6f74 invokes mOnFinished, then0x1686f78–6f7c clear
  mTime and mIsPlaying.

The API is deltaTime, distinct from unscaledDeltaTime/realtime getters; no
raw wall-origin subtraction appears in this UpdateText body. Engine-internal
timeScale/clamp behavior was not re-audited here. `GetTextSpeed` at0x1686ccc
has ordinary mode0/1 branches using settings+0x20/+0x24 multiplied by10; a
full-voice flag has a separate×7 branch. This does not authorize choosing new
numeric settings or modifying the current speed/skip/voice policies.

The current canonical `public/player/player.js:470` sets
`textBegan=performance.now()`, and`:516` uses elapsed **RAF timestamp**
`now-textBegan` times configured speed. Thus "raw wall clock" here means
unbounded elapsed RAF/performance-domain time, not Date.now or the draw-call
entry timestamp. The native accumulated-delta path is a concrete difference.

## What the new FX observation does and does not establish

Retained `private-fx-result.json` reports one observed draw call with
drawEnter11478.5ms, drawReturn11478.7ms, visible3 and prefix`——啊`, crossing
thresholds1/2/3 together. Its Normal clock has delta0.15s, frame timestamp
11383.9ms and gameSeconds9.3662666865. Exact textBegan remains null; only its
bracket[11232.7,11478.5]ms is available. A text_begin event before assignment
cannot establish the missing exact value, and draw calls are not proof of a
separately presented compositor frame.

**Native arithmetic itself permits multiple glyphs in one update.** At speed25,
one delta0.15s can already truncate to3. Therefore changing the time source
alone cannot promise a first count of1, identify the stall/compositor cause,
or resolve this FX/source rejection. Do not cap glyphs at1 or insert a Wait
to conceal it. The source FX command phase, offsets, exact AV/glyph/entry
relationship and original CSV remain unknown; phase1/XYZ0 stays unaccepted.

The next source-only change can isolate typing's accumulated Normal-clock
state/reset/completion from unchanged panel/card/phase/FX ownership. Its
eventual ordinary necessary QA must evaluate actual source performance again;
this report grants no runtime, effect identity, audio or whole-episode pass.
