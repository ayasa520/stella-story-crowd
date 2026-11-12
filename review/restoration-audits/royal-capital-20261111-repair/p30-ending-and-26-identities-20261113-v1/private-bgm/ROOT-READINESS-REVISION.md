# Root revision: wait for the real player iframe

This v3 derivative retains v2's K1/K2 fixes and changes only the initial iframe
readiness predicate. A newly created about:blank iframe can have a body before
the actual player navigation, so testing body presence alone does not prove
that selecting the `/player/player.html` Frame is safe. The revised predicate
requires that exact same-origin pathname and its actual document body.

The single program response remains gated until observation is installed.
No story node, command phase, audio clock, prototype hook or source projection
changes. All observer/compiler code and the original correct JA guard remain
unchanged. This is a source-supported readiness correction, not a claim that
the earlier race was observed in an executed browser trial.

The v2 author and independent reports are historical context copied unchanged.
They do not describe this additional root hunk. The driver syntax check passes;
no browser, observer or runtime test has been executed. A fresh explicit root
browser release remains necessary. Original listening, source timing, exact
loop-wrap and actual cleanup acceptance remain unproven.
