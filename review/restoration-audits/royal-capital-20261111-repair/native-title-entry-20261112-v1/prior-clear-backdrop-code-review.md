The replacement clear-backdrop implementation has no concrete source blocker
in this bounded review. It supersedes the temporary canvas/painter arrangement
preserved in `sharp-canvas-superseded.patch` and the earlier canvas-specific
handoff concern. No production source was edited or browser started by me.

NativeBackground keeps its configured radius in `blurRadius`. `setBlurred()` is
idempotent and changes the presentation filter through the existing fit path;
it does not replace the decoded resource, request another image, change the
native crop/aspect, or affect card/actor visibility. A hidden/empty background
retains the selected blur state, which fit applies when a later image commits.
Resize continues through the same native fit owner.

The ordinary title holds the clear backdrop through its own2.5s entry, resource
preparation and the next native Card_wait/Card_in. The non-movie path releases
only after the awaited CardIn and generation check. The movie path releases
after its separate CardIn and before PlayMovie; its later common release is a
safe no-op. If a card is already in, CardIn returns with that opaque state and
release remains appropriate. Skipped-node chains retain the lease until a real
card, terminal Stop or error Stop. No actor/cardMotion is shown early.

Stop releases the lease; fail calls Stop for actual errors, and replay starts
with Stop. The end-title path explicitly selects blurred backdrop and clears
the ordinary flag while retaining the CSS black backplane. Repeated release is
safe. The old stage canvas, injected painter, paintTo and sourceImage additions
are absent from the current production files.

The direct Title1 bg_picture evidence remains independent in
`title1-background-review.json`; correcting unsupported stage-precondition
syntax does not expand that accepted field. Runtime acceptance remains open:
the next video must show the correct sharp room under the ordinary exit and
continuously afterward, no intervening blur flash, unchanged end fade to black,
and clean IF/baseline capture intervals without simultaneous screenshots.
This was a short source-path review only; no broad layout checks or repeated
build/test suite was run.
