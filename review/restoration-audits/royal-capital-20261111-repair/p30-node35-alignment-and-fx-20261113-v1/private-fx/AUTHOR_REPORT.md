# Atomic observer ownership revision — source only

V1 remains unchanged. Its independent peer found that verification and retaining the cleanup handle were separate iframe operations: the second lookup proved only the current slot's self-consistency. V2 replaces that handoff with `owner-install-handle.js`.

One iframe `evaluateHandle` callback now evaluates/invokes the unchanged observer-v2 factory, compares its returned `ownerProof` to the slot candidate by identity, and returns an object retaining that exact candidate, the factory-returned proof and its uninstall function. The host obtains a JSHandle to this object. A later `retained.evaluate` reads only its plain receipt; it does not read the global slot or select another owner. The driver receives the receipt and retained handle together and has no second slot acquisition.

If the host receipt read/validation fails, the helper's error carries the same retained JSHandle and a plain failure/closure receipt. The driver catch preserves it for finally. Factory partial-install rollback and identity-proven validation cleanup remain captured inside the initial iframe operation. A missing proven owner or failed transport is explicit frame-closure work for root, never permission to adopt a replacement slot. Finally disposes the retained handle and independently removes routes/listeners after its owned cleanup attempt.

The observer-v2 factory is an unchanged external dependency. The entire original route/projection, complete candidate CommandRow, manifest9-resource preservation, phase1/XYZ0, unmodified seed and800/3500/600ms holds remain unchanged. There is no screenshot, recording, new story Wait or formal edit. `v1-to-v2.patch` shows the bounded source/document delta and new bridge.

Both new JS files pass `/usr/bin/node --check` under nice19/CPU0,1. No factory body, browser, compiler, observer, mock or unit test was run. All root/release flags remain false; peer source review and explicit root runtime release are still required. GPU presentation, private exact `textBegan`, original phase/XYZ/Wait/timing and full performance remain unaccepted.
