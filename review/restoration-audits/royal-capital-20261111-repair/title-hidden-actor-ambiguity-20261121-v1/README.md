# Empty-actor TITLE route conflicts

The fourth-episode title at scene10100012/node2 inherited different Subaru body motions from two predecessors. It displays no actor and its next text node explicitly clears actor state, so that old body conflict did not describe a required title presentation input.

The deployed source now omits hidden actor fields only from blocking diagnostics for TITLE nodes whose authored model and actors are both empty. It preserves every before/entry/display/after value. Background, music, ambient sound and effects retain their existing conflict checks. It does not clear authored fields or implement an actor lifecycle reset.

Independent review passed nine real-scene route groups: all four resolved states remain equal, and all eight successful complete prepare programs are byte-identical. Those calls executed the actual POST handler in memory with a hash-bound I/O bridge; they are not described as HTTP-server or GPU tests.

Actual production HTTP before/after checks confirm the unselected title changes from [bg_picture,body] to [bg_picture], and prepare remains422 for the real background conflict. Choosing route19/181 still returns200. Its entire1,174,438-byte program has the same SHA before and after deployment; all four resolved states remain equal. This is a diagnostic correction, not original motion, exact animation, audio or whole-episode acceptance.

Canonical source commit4aeff7c was built and deployed to the existing stella-preview Worker, version fc8e36aa-db74-4f96-97c4-5460772a418b. Only lib/studio-state.ts changed. The two unvalidated movie-retirement Player edits were separately stashed and excluded from this deployment. Existing configured Site access returned project_not_found; the already authorized direct Worker route was retained without inventing a Site or source remote.

Review receipt.json, applied-source.patch, source-review/, independent-peer/ and production/. Raw production responses are losslessly gzip-compressed with their uncompressed SHA in the receipts. Native/review scene data, IDs, branch targets, protected originals and resources are unchanged.
