# Draw diagnostic v2 — prepared, unexecuted, not acceptance

This revision addresses B1–B4 from the complete independent v1 peer review.
It changes only new files in this directory. All v1 author/peer files remain
unchanged; the old data lock is retained as a reference and is never refreshed
to follow the active data writer.

| Peer blocker | v2 implementation |
|---|---|
| B1: unbounded host waits | `deadline.mjs` supplies one absolute case clock: 35 seconds for work, then cleanup within a total 45 seconds. Program headers/body/hash, navigation/actions/waits, artifact reads, Page creation, export/drain/close/save all use that clock. Page setup is inside its lifetime try/finally. A small returned partial receipt survives a failed disk export. |
| B2: compressed/post-materialization byte checks | `bounded-response.mjs` admits only frozen GET/200 bodies with exact URL/size/SHA, absent or identity Content-Encoding, one exact Content-Length, no Transfer-Encoding/Content-Range, and no Service Worker. It reserves the exact decoded length before asking for a complete body. Unknown/encoded/chunked/unfrozen bodies are refused before body(). Actual byte accounting is checked before hashing, and pending reservations survive an abandoned host await until the original body Promise settles. Program and resources share one 32 MiB decoded ledger. |
| B3: changed factory Promise | The factory wrapper returns the exact `result` of its one original invocation. An intrinsic Promise.then registers no-throw side observers; that side Promise is never returned or awaited by the caller. Original sync exceptions and async rejection reasons are not replaced. |
| B4: diagnostic exceptions or hidden original failures | All wrapper pre/post/context/timing work runs through the no-throw `diagnostic()` boundary. The central `actual()` helper marks any wrapped original failure as partial, then throws the same object. This classification does not depend on pageerror or four-ready-frame coverage. Factory/draw/update/render and lifecycle callbacks use the same separation. Page creation and observer/listener setup now occur inside case cleanup ownership. |

`B1_B4_RESPONSE.md` explains the exact control flow and remaining limits. The
geometry observation points, native typed-array identity matching, input
generation links, mask/color/clip matrix distinction, and per-load content/URL
association remain the v1 design that the peer found statically supported.

The runtime patch is [instrument.js](instrument.js). The owner draft is
[run-diagnostic.mjs](run-diagnostic.mjs), with host helpers
[deadline.mjs](deadline.mjs), [bounded-response.mjs](bounded-response.mjs) and
[resource-observer.mjs](resource-observer.mjs). No file has a top-level capture
invocation. `execution-UNRELEASED.json` fails the execution gate.

The reference twenty-two source/model files are checked by bytes, without
polling or re-freezing the active data HEAD. Canonical372 still lacks a native
actor parser and native_parent renderer path. A matching old byte lock is not
a usable P09 multi-actor source or current execution freeze. Any future run
requires root's separately reviewed source and new consistent data/program/
packet/resource/helper freeze, including every predecessor/successor body
that the response observer will read.

The strict body profile bounds admitted identity-HTTP body buffers through
known framing and pre-reserved frozen lengths. It is not an upstream browser
network-memory limiter or a general compressed/chunked streaming decoder.
Mismatched actual body length is a protocol/profile failure, never accepted
or hashed. Host deadlines bound awaits and prevent new work after expiry;
they do not cancel arbitrary Playwright commands or preempt synchronous JS.
Unconfirmed Page closure or a late creation remains explicit. Root must always
close Chrome/CLI and verify OS zero after a future callable returns or fails.

No Chrome, application, capture, runtime injection, unit test or dynamic fault
simulation was run. Checks are syntax, static control-flow/source inspection,
JSON and hash integrity only. No extra draw/update, parameter/time/rate/camera
write, new fetch or response interception was added. All preparation commands
with computation use nice19 and CPU22,23.

Status remains **requires fresh independent peer review / unexecuted /
not acceptance**. The fresh receipt inventories v2 and binds the unchanged
v1/peer inputs. It does not assert that the v2 runtime behavior or limits have
been exercised, nor recover any original P09 CSV, pose, timing or camera.
