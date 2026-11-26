# Source preparation version history

The v1 fc5b413b seal was temporarily edited in place during two SHA-binding guard corrections. Those edits produced intermediate seals 8b4d73b0 and 2438cce7. This was not an immutable update. The initial v1 before bytes have now been restored and its original fc5b413b1407db05c1923dffe1727d0ba029add472db9191004ae04054ecef62 receipt and all 11 payloads reverified exactly.

The complete corrected source lives in this new v2 directory. Historical in-place correction receipt and verification bytes are preserved here solely as history; their old v1 paths do not bind current v1 payloads. The final v2 receipt is the only candidate for the new owner review/release. No current HEAD, runtime inventory or execution release is created by this transition.
