# Independent static review: P30 ordinary actual-MKV complete decode

Verdict: **static pass, no code must-fix; separate exact root release and fresh
external resource/input gates remain required**. This report does not execute
or approve execution of the candidate. No AST/syntax test, import, Pillow,
ffprobe, FFmpeg, image review, API/browser, Git or D/C mutation was performed.

The candidate31261B SHA3138b500 is bound to the sealed preparation57a0d018.
Exactly three configuration literals change INPUT, CAPTURE_CLOSURE and CASES;
seven English comment lines explain their scope. Removing those comments and
reversing the three literals restores the complete executed30684B K5 source
7274cb29 byte-for-byte. All functions from request_stop through main/entry
remain28906B SHAa3456d97, exactly equal to the successful K5 kernel. Its
single-complete receipt c516fb5e and independent closure a6bd0307 are checked
as existing metadata, without reading their images or re-running that code.

The exact P30 input is K2/attempt-1/p30-node4-unchanged-ordinary/actual.mkv,
declared1439679B SHA87d2e321. Original capture receipt, recorder command,
capture index and root closurec6db91bd provide the five input bindings. The
MKV itself was statted only; its bytes were not read or rehashed. Recorder
exit255 belongs to the already closed requested stop. It does not establish
either successful or failed container decoding. Actual frame count/timebase,
PTS and containerDecodeVerified remain unknown/false before execution.

The unchanged raw command consumes the complete MKV video stream with copyts,
showinfo and passthrough, without seek, duration/frame truncation, fps, crop or
scale. Native output remains500×1000; each RGB block is1500000B. The453 recorder
samples are a contract being checked: all453 blocks and showinfo records must
actually arrive, followed by an independent one-byte EOF read, producerexit0
and terminal clean stderr. Early, extra or partial bytes fail. Original
integer PTS/timebase and duplicate/decreasing observations are indexed, never
replaced by a predicted30fps timeline. Surface samples are not uniqueGL frames.

Only contact overviews resize to250×500 tiles on1250×2104 sheets. Native JPEGs
keep500×1000, quality95/subsampling0, and each raw frame also receives its own
RGB digest before JPEG encoding. Contacts must cover every produced frame
exactly once and sequentially. No visual/performance/source-phase conclusion
is supplied by decoding or by this static review.

HERE's cumulative output hard cap is128MiB, ordinary writes strictly below
96MiB and emergency margin32MiB; stderr is bounded by8MiB. Every output uses
the shared budget writer after in-memory encoding. No raw stream goes to disk
or accumulates as453 raw frames in RAM. The fixed frame unit, read-copy/image/
JPEG buffers and7.89MB contact canvas are bounded algorithmic allocations,
not a measured total RSS or an RLIMIT_AS/RSS guarantee. Fresh160MiB disk and
256MiB available/cgroup-remaining memory gates are explicit root obligations.
The180s limit governs decode transport; contacts, legacy hashes and cleanup
are outside it. The separate300s whole-attempt monitor is also external.

Deferred stop handling, new owned process registration, original stderr and
exception evidence, TERM/KILL/wait/PID/PG and reader observations, input/code
before/after hashes and all four preserved legacy-tree gates are unchanged.
Future unknown closure means no image review. No live canonical/data snapshot
is a decoder dependency; the existing closed actual capture is the evidence.

The false release template matches the actual kernel's required case, five
inputs, seven tool/Pillow/font paths, four legacy inventories, capture closure,
mechanism proof, code hash and128/32MiB budgets. It cannot pass its root gate
while rootConfirmed/changedRawRGBDecoderAuthorized remain false. A separately
named exact root release and fresh bytes/OS/resource checks are still needed.
Old K5/silent54 message/schema labels are explicitly documented as inherited
mechanism names; P30 caseId, input and closure bind this new attempt.

The preparation remains sealed and run-1 is absent. This peer created only
small metadata in this new peer directory, preserving all older evidence and
the source23 review. Media, toolELF/font/Pillow package bytes were not read.
