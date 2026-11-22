# P30 voice58/6: two helper fixes — STATIC ONLY

This is a partial source revision proposal, not a runnable kit or release. It contains ONLY play.mjs and production-proxy.mjs plus their complete GNU diffs and byte proof. No other helper, guard map, frozen/prepared data or attempt is copied. All new root/execution flags remain false; final HEADs remain null. The old sealed package and failed session62388/exit1 remain unchanged.

The first real failure was the helper's expected production URL retaining local :5198. The new builder uses the original local pathname+search with the fixed binding.productionOrigin; the original exact full-href equality still rejects any host/port/path/query difference. No request or business data is changed.

The other refusal came from classifying HTTP304 as a redirect. Only301/302/303/307/308 now emit the existing redirect-fatal marker. Actual304 status, original headers and zero body stay unchanged. bodyTransferred now excludes HEAD and204/205/304, matching the existing null-body return. True redirect/error handling and the runner's complete-log fatal gate remain intact.

The original media-owner/one-play/one-ended/progress/natural-ready/next/Stop, Opus byte proof, full-program/before, inventory, budgets and OS cleanup are unchanged. Five surrounding source segments (41,291 bytes) are byte-exact. No actual outcome is reclassified as passing and no source phase/gain/loop/body/face/listening claim is added.

Only static text/byte utilities were used: cat, GNU diff, sed, sha256sum and wc. No Node/Python/helper/kernel import, evaluation, syntax/AST/test/build, freeze/prepare/API/browser/renderer/media work occurred. A future complete case requires separate root composition, fresh guards/review and a new explicit release. There is no runtime command in this partial proposal.
