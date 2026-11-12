# Private FX observer driver v2 — atomic observer ownership, source only

V1 is preserved. Its verified owner and later retained handle were separated by a host await; a second slot lookup could therefore adopt a replacement. V2 closes that gap with `owner-install-handle.js`: factory invocation, comparison against the factory-returned proof, and retention of that exact handle/proof/uninstall occur in one iframe `evaluateHandle` operation. The later host read obtains only the plain receipt from the retained object. It never selects an observer again. If that read or host validation fails, the thrown error retains the same JSHandle for driver finally cleanup/disposal; unavailable transport requires frame closure. No replacement slot is adopted.

`driver-factory.js` is an uncalled function expression for root's existing sole-browser wrapper. It neither launches/closes Chrome or a server nor records video, captures screenshots, writes files or changes formal assets/data. Root must independently approve it, supply `executionAuthorized:true`, own browser/session/server closure and save its returned diagnostic. All preparation/review/release flags in this proposal remain false.

The only ordinary route is25ready→26→27→28 in10450056. It reuses the already run `p30-cg-panel-entry-runtime-20261113-v1/capture-fx.js` candidate and preserves that driver's800ms hold at26,3500ms observer hold at27 and600ms tail at28. These host observation intervals are not authored/native Waits. Phase1, XYZ0, resource selection, seed behavior and original-source timing are not accepted or repaired by this run. No additional candidate, radial command, SE or seed option is supplied.

Root supplies literal strings in these options, without editing the referenced files:

- `ownerInstallSource`: this directory's `owner-install-handle.js`, the atomic handle-returning bridge variant.
- `observerFactorySource`: that same v2 directory's `observer-factory.js`.
- `candidateManifestSource`: `../p30-node27-fx-source-proposal-20261112-v1/candidate-player-v3/effects-candidate.json` (JSON text, not executable JS).
- `baseUrl`: the released normal loopback adapter origin, with an empty fresh registry. This driver does not start or register it.

Documentation-only invocation: evaluate `driver-factory.js` as a host function expression, then call the resulting function with the existing Playwright `page` and those options plus the explicit execution flag. Evaluating its text without invoking the returned function does not run it. The driver and owner-bridge expressions belong to the host; the reviewed bridge explicitly invokes the observer inside the real player iframe. The driver waits for its actual pathname/body, then25ready before installing; this is initialization/observer setup, not a node-clock change.

The candidate's camera/preview/resources portion was compared offline with the old executed capture's literal and is identical. The full JSON additionally contains its preserved source-only provenance/nonacceptance metadata; that is not copied into formal effects. The only texture route fulfills the unchanged native-derived PNG at `/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-node27-fx-source-proposal-20261112-v1/candidate-player-v3/fx-texture-6509005618617200518.png`. Only one `adv_ef_explosion01` resource is added in browser memory to the actual fetched effect manifest. The old9 resources, camera, preview and all other manifest fields are restored-and-compared against that original.

The actual canonical `/program` response is fetched normally. Guarded node27 has `――ああっ!?`, translated `——啊啊！？`,006 and an empty phase1;26 also has006. The same complete diagnostic CommandRow from the old run is assigned only to27 `command[1]` and `phases[1]`. Restoring both in a complete clone must deep-equal the original program. This is1authored/2compiled fields; no command phase, title, before state, branch, source text or other field is rewritten. Preparation also read current native27 UID1045005600027/stable key`s10450056-p30-at0533`; those native-only identifiers are external release bindings, not falsely claimed browser-program fields.

After25ready the new owner bridge must report six hooks and same-realm owner identity while retaining them atomically. The underlying independently reviewed observer-v2 factory is unchanged. A read-only Playwright JSHandle retains that actual observer/cleanup function through collection; it creates no player or rendering/audio context. A replacement global slot is never adopted at cleanup. Factory partial rollback and verification-failure cleanup remain available as plain receipts in the retained object. After the original27 hold, the existing FX must already have zero instances/layers. Uninstall collects the final snapshot and restores before28. Success requires:

- exactly one attributed activation and matching original START seed/resource/XYZ0;
- exactly one nonempty positive-alpha Yellow batch tied to that instance/seed;
- actual text threshold crossings1/2/3, correct prefix/group, zero observer errors/drops and no attribution gap;
- all six wrappers' nonzero entries equal originalCalls, zero original throws and exactly one `VisualEffects.play`;
- six original descriptors, both listeners and the owned slot restored, with no snapshot/cleanup conflict;
- ordinary28 returns to blue046c with picture hidden and no FX layer/instance at ready or the retained tail.

Missing evidence fails; it is not repaired by a new dwell or Wait. Prefix crossings may coalesce and inline opacity may still be zero. The original v2 limits remain: private exact `textBegan` is unavailable, Yellow is only a draw-method bracket, and neither exact GL presentation nor the original native phase/XYZ/timing is proved. This diagnosis does not revisit or override the earlier visual rejection of phase1/XYZ0.

Every route/listener registration is inside `try`, with attempts tracked before calling the API. `finally` independently attempts pending observer uninstall, handle disposal, each unroute and each listener removal. The driver does not stop or close root's browser: if transport or cleanup fails, root must stop/close its owned iframe/session immediately and retain process closure evidence. No incomplete cleanup is a successful result.

Validation here is syntax-only `/usr/bin/node --check` for the driver and new bridge under nice19/CPU0,1. Candidate/native JSON was read offline; no JS body, browser, compiler, observer, mock/unit test, image or texture decode was executed. Root must peer-review the concrete source before any release. Phase1, XYZ0, the complete candidate CommandRow,9-resource preservation and800/3500/600ms holds are unchanged from v1.
