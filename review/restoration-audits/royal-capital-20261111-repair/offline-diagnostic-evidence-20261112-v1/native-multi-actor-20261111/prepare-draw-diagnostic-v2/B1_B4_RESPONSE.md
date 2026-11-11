# Response to peer B1–B4 — static revision only

Input report SHA-256:
`ca834f24db3a0dcc2574d6cccc2843d8fb7c10e280de757eb0e3b5d1cf1b9888`.
Input peer receipt SHA-256:
`53debf4307bc5cb7b8586d248b10a478215f81f012fc49693a3c2a6be4d907ac`.
Both were read completely and verified before editing. Neither peer blocker
was treated as a reproduced player failure.

## B1: one host absolute deadline and owned cleanup

`CaseDeadline` starts before each case's artifact read/Page creation/setup.
Every `work()` uses the same absolute work endpoint, not a fresh duration.
The default endpoints are start+35s for work and start+45s for cleanup.
Program response waiting and its body read are both guarded; its exact URL,
length and SHA come from the future root-frozen case rather than a pathname
match followed by an unguarded body read.

`beginCleanup()` rejects pending host work. Export reserves at least five
seconds, resource drain reserves four, and Page close reserves 1.5 seconds for
a bounded final save. All still share the same start+45s hard endpoint.
File writes receive the hard-deadline AbortSignal. A timeout cannot silently
skip the finally path and continue to another case. A small returned receipt
includes failure, pending-command labels, close confirmation and file-save
confirmation even when the evidence file could not be written.

The first owner Page must be a fresh about:blank Page and is owned inside
try/finally. Later newPage calls, observer attachment and event setup are inside
the same lifetime. A timed-out create may resolve later because Playwright
does not expose cancellation here; a side handler requests closure of that
late Page without extending the host await. `creationUnsettled`,
`lateCloseRequested` and `closeConfirmed` remain separate. No code claims a
timed-out close completed or that Chrome/CLI processes exited. Root's immediate
browser/CLI close and OS verification remain mandatory.

This is a bound on asynchronous waits and permission to start later work, not
a hard-real-time preemption guarantee for JS/OS scheduling or synchronous
bounded hashing/serialization. No runtime deadline experiment was performed.

## B2: strict admitted-body profile and actual decoded accounting

There is one complete-body reader: `readFrozenIdentityBody`. Both program
and resource capture use it. Before `response.body()` it requires:

- a frozen positive exact length and SHA, within the individual cap;
- actual URL equal to the frozen URL, GET and HTTP200;
- confirmed non-Service-Worker provenance;
- absent or exactly identity Content-Encoding;
- a single decimal Content-Length equal to the frozen decoded length;
- no Transfer-Encoding or Content-Range;
- a reservation for that exact decoded footprint in the common 32 MiB ledger.

An unknown model/source URL is refused before reading it. Consequently a
future freeze must also include known sizes/hashes for observed predecessor
and successor model resources. The old three-model reference cannot silently
authorize unknown bodies. Program has its own exact case identity and does
not appear as a duplicate path in the resource map.

Only this admitted identity-HTTP framing profile reaches Playwright's complete
body API. The v1 compressed/unknown-length post-materialization fallback was
removed. This is not a streaming decoder or a claim to bound buffers already
owned upstream by the browser/network process. Actual returned bytes must
equal the reservation before hashing. A violation is partial failure; it is
not normalized, silently truncated, decompressed or accepted.

A host timeout does not release a reservation while the underlying body
Promise can still settle. No-throw side settlement handlers account its actual
length or release a failed read. This avoids admitting more buffers using a
reservation that only the host await, rather than the real read, abandoned.
Actual decoded totals and unresolved reservations are exported separately.
Per-resource cap remains8MiB, program cap16MiB, common decoded total32MiB.

## B3: exact original Promise/result boundary

Factory is a regular function, not async. It takes one original result through
`actual(original,this,args,...)`, registers side reactions with the captured
intrinsic Promise.prototype.then, and executes `return result` verbatim.
Neither the side Promise nor a transformed Promise is returned. No diagnostic
digest or setup is awaited in that return path.

Fulfillment observes the already-produced model in a no-throw diagnostic
boundary. Rejection marks partial failure and returns undefined only to the
discarded side chain. The original Promise's state, identity and rejection
value remain the caller's. Observer work still has finite execution cost;
this is not a claim that microtask CPU cost or wall time is zero.

If side registration/observation fails, capture becomes partial while the
original result is still returned. There is no fallback original call and
no retry. No Promise fault simulation or timing run was executed.

## B4: diagnostic isolation and original exception propagation

`diagnostic(stage, operation)` catches its own errors and calls a defensive
no-throw failure recorder. Every pre/post sample, context/clock/timing read,
append, observer reaction and lifecycle event callback uses that boundary.
In particular, Core's timing read and successful post-call append can no
longer turn a successful real Core update into a throw before SDK loadParameters.

`actual(original,receiver,args,stage)` owns the one real Reflect.apply. Its
catch records a global partial/original-call failure inside a no-throw guard,
then rethrows the same object. It does not swallow, wrap, substitute or retry.
This also applies to factory sync failures, model draw, mesh draw and PIXI
render. The factory's original async rejection is marked by its side observer.
`runtimeFailures` is a separate global summary, so handled upstream exceptions
outside the four ready samples cannot be promoted by coverage to a clean run.

Render-stack removal and model-draw cleanup are themselves guarded post
observations. Restoration reports wrapper-identity conflicts instead of
overwriting a different wrapper. Cleanup attempts each listener/method
restoration independently and cannot replace the result/exception of a
currently unwinding original call. No SDK/model object is destroyed by it.

## Unchanged limits and prerequisites

The original SDK input/draw/typed-array/matrix call sites are those reviewed
in v1; their byte hashes remain bound by the reference lock and peer receipt.
CPU submission matrices/vertices, model color and drawable opacity are not
post-GPU uniform/pixel-alpha readback. Mask channel/layout uniforms remain
outside this packet. PIXI matrices are not Unity localToWorld, and successful
generation/frame links do not identify an original default pose or missing CSV.

All original data/source/registry/Git state is untouched. No current data HEAD
was polled or compiled. Canonical372 still has no native_parent path/parser.
The reference v1 lock remains stale execution evidence; the v2 runner refuses
it and requires a new root_frozen_execution lock plus matching helpers/program/
private packet and sole-browser-owner assignment after peer review.
