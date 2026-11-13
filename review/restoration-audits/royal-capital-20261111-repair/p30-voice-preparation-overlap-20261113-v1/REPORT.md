# Let voice readiness overlap native card entry

The transport previously committed a running character motion, then awaited
bank/media preparation before CardIn. Original CardProc instead reaches
PanelSequence after CardIn and phase1; UIController.ShowTextPanel dispatches
PlayNormalVoice at that later boundary. The retained native evidence and
independent source review are in the adjacent voice-preparation-boundary/peer
folders. Original model-load ordering, exact voice phase and native preloading
remain separate unknowns.

The two actual/Studio transports now start one generation-owned preparation
promise at the old location and join the same promise immediately before the
existing speech play. Immediate rejection observation and checks before/after
channel preparation retain cancellation. Motion selection/resume, shared Normal
clock, phase0/Wait, body/face fields, offsets and existing speech APIs are unchanged.

Receiving a replacement program also stops its old generation synchronously
before replacing program/nodes or awaiting effect setup. Both setup awaits check
that generation before continuing. This closes the concrete old-voice window
identified during peer review. Shared DialogueVoice changes only its header.
The three original files are retained under `revert voice preparation barrier`.

One closed continuous actual33→34→35 comparison used the existing single private
body leaf, changing only compiled34.body. Independent review restored that one
field/deleted explicit attribution and compared all5603nodes/5849edges exactly.
No formal body field is installed. Actual held observation is2.15game seconds.
Julius motioncommit→CardIn start is.0167game seconds, compared with.4167 in the
closed previous run. Voice ready/join now occurs after phase1 and before text.
This proves the ordering change, not original timing or a wall-performance fix.
New CardIn still took2238.9wall ms/3game frames; that gap remains unexplained.

The same source draft passed ordinary37→38→39 with the saved original Elsa cue:
one original play/playing/ended, bank/WAV200, real partial progress, native
duration and next/Stop cleanup. Its17listeners were removed. Three further
fresh normal documents exercised Stop before bank completion, Stop at original
media loadstart with pendingPrepare=true, and parent replacement by a real35
program during media preparation. All old generations cancelled, with24actual
follow-up frames retaining the original audio, no voice/pending/play and time0.
Every probe/listener/parent bridge/JSHandle and all CLI/Chrome/server owners
closed. Independent runtime reviews retain the raw events and separate clocks.
Generic unattributed404messages remain in raw logs without a guessed cause.

The official current-source Site build passed0 with inputs unchanged thereafter.
No dependency installation, unit/mock suite, new media/clock, native Wait or
source-data repair belongs to this source change. Existing owner-private Site
audience is preserved. Julius's complete visible entry/exit remains unaccepted:
the old capture lacks the original open-eye entry and gradual exit, and the new
closed recording is under delegated full-frame review. No full chapter or full
restoration claim follows this bounded source ordering/cancellation correction.
