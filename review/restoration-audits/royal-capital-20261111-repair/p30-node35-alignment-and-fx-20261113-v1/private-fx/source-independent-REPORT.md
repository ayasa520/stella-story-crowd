# Concrete FX observer driver v2: independent static review

**Source review passes; no remaining blocker found in the bounded v1→v2 change.** Driver F1 is resolved. This is not runtime or execution authorization. V1 remains rejected/proposal-only. No browser, JS body, compiler, syntax runner, mock/unit test, decoder or image work was executed by this review; no formal source/data or Git action occurred.

Reviewed the stable executable files `p30-fx-observer-driver-proposal-20261113-v2/{driver-factory.js,owner-install-handle.js}`, their complete difference from v1, and the existing observer-v2 cleanup contract. Earlier full candidate/production-module/old-capture comparisons remain applicable because those sections did not change.

## F1 resolved

The new installer uses one iframe `evaluateHandle` callback to evaluate and invoke the reviewed observer factory, compare its returned `ownerProof` by identity with the slot candidate, and retain `{handle, proof, uninstall, receipt}`. The proof is taken from the factory result. The later host read obtains only the plain receipt from this retained object; the driver does not re-read the global slot after the host await. Therefore another current slot object is not adopted as the installed owner during handoff.

If installation/validation fails inside the iframe, the existing partial-rollback receipt is preserved. Only an identity-proven handle may be cleaned. When verification already produced `validationCleanup`, the driver's later cleanup returns that receipt without invoking successful rollback again. A failed/unknown cleanup stays failed and requires frame closure.

If the later host receipt read or validation fails after a JSHandle was retained, the host Error carries that same handle and the plain failure receipt. The driver catches and retains it for `finally`; it uses the captured original uninstall and proof, or reports that no proven cleanup function is available. Transport loss before a handle is obtained explicitly requires frame closure. The handle is disposed independently after cleanup attempts, and each route/listener removal is still attempted independently. No incomplete evidence/cleanup becomes a successful result.

## Scope preserved

The candidate resource, native-derived texture, exact CommandRow,1authored/2compiled projections, whole-program/manifest restoration comparisons and three bounded routes remain as reviewed in v1. Normal25→26→27→28 and800/3500/600ms observer dwell are unchanged. The actual `/player/` module identities and reviewed six-hook observer are unchanged; no additional hook, original-method call, RAF/timer, geometry/draw, seed, phase, XYZ or authored Wait is added. Observer errors/drops, ambiguous attribution, unmatched prefix/seed, wrong forwarding counts or incomplete restoration still fail.

Actual iframe execution/JSHandle transport, real records, Stop/session closure and restoration remain untested. Exact private `textBegan`, exact GL/GPU presentation, candidate source phase/offset/resource identity and original visual order remain unaccepted. Root must supply the new v2 `owner-install-handle.js` as `ownerInstallSource`, independently bind the source packet and decide the sole browser release. Root review/confirmation and execution authorization remain false in this receipt.
