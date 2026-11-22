# Independent static review: node22 bounded source capture

Verdict: **static pass; no must-fix finding in this six-literal adaptation**.
This is not an execution or installation approval. The candidate was not
imported, compiled, AST-parsed, tested or executed. No source video, image,
texture, MOC, Python/FFmpeg ELF or Pillow package bytes were read by this peer.

Both complete445-line scripts were inspected as text. The candidate SHA is
`1d7135622f82b39a8ba7c0c7698cc1d27f2f5a4aaf2a94a1e4a77a19e19cc962`.
Only lines1/38/144/239/361/426 differ from the executed node20 base
`9151cdad8699aba7e0f73f3c3e43290edf029226e5fd9b6511f2da3853cc15b7`.
The six replacements are individually unique, their recorded unified diff
matches actual changed lines, and reversing them recovers the complete base
bytes exactly. The base successful run's before/after script hashes are
checked from its existing JSON receipt, not by re-executing it.

The current full node22 row/sidecar, UID1004005200022, array index21,
`s10040052-p29-at0294p5`, source text and13 current expected fields match the
owner guards and previously sealed next-window metadata9c408cdd. Character
is still empty, no model is chosen, and fieldsProposed remains empty.

The unchanged kernel enforces the original isolated ARM venv with `-I -B`,
nice19/CPU0,1, single native/decoder threads, fixed480×856 RGB24 blocks and
integer PTS multiplied by the actual showinfo timebase. `[292,301)` is
consistent in constants, FFmpeg select predicate and independent integer-PTS
gate. No sampling, scaling, cropping, interpolation or PTS rewrite is added.

Budget lines82–110 charge all preparation files and outputs under the new
HERE to one96MiB limit. Payloads encode in RAM before a synchronized write
check, ordinary writes stop below80MiB and16MiB is reserved for failure
evidence. Stderr has its own1MiB bound. The120s deadline governs capture
transport; bounded cleanup and whole-input hash observations are additional
work, so this peer does not describe120s as an end-to-end CLI limit.

Lines282–287 require1–299 complete frames, no truncated RGB block, producer
exit0, terminal clean stderr and matching PTS/RGB counts. Reaching300 is
failure, not successful truncation. `naturalEOFBelowFrameCap` means the
selected producer stream reached EOF below its cap. It is neither physical
whole-video EOF nor proof that node22's visual exit or the desired successor
boundary was captured. The script records complete-unreviewed/source accepted
false; the owner plan retains visual sufficiency as unknown and forbids
automatic expansion or joining across the old source gap.

Owned process registration and signal handling preserve the original cleanup
path: only the newly created PID/session is stopped; TERM/KILL/wait, PID/PG
absence and stderr-reader termination are separately observed. Original
errors remain attached when cleanup or after-observations also fail. Input
script, whole source, tool and Pillow hashes are checked before/after by a
future invocation; this static peer only verifies their existing metadata
bindings. Current runtime/tool hashes or future OS closure are not claimed.

All new preparation approval flags remain false, run-1 is absent at review,
and writes in the inspected capture code target the fresh new HERE/run-1.
The JSON flags are not a built-in CLI permission gate; an exact root execution
instruction remains separate. No old authorization is reused by this review.
No D/C, old evidence, Git, API/browser or business helper was changed or used.
