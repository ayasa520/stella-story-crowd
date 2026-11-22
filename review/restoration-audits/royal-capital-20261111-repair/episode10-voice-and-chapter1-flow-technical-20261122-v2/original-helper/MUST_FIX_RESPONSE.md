# Preliminary peer M1/M2 response — static only

The preliminary peer read all seven sources and reported only these two necessary corrections. No helper or syntax/test/API/browser/media command was run.

M1 — play.mjs:361: target deliveries now require phase === 'response-complete' before the exact GET URL/status/body digest/byte proof. The complete providers archive still includes every request-started/response/error row. The runner retains started-to-terminated closure; no successful event is manufactured or removed.

M2 — run.py:412: AFTER every owned role is stopped, retain the complete original server.log path/bytes/SHA and reject explicit PRODUCTION_PROXY_REQUEST_FAILED, PRODUCTION_PROXY_TRACE_BUDGET_EXCEEDED, PROXY_ERROR_RECORD_FAILED, PROXY_ERROR_TRACE_FAILED and PRODUCTION_PROXY_REDIRECT_RETAINED markers. Unexpected original server exit also rejects. This covers errors outside or after a trace row and after driver retirement, without classifying normal hitches as fatal. Original log bytes and first-failure archives remain untouched.

No media observer, 1play/1ended/progress, natural6ready→61→7ready/Stop, remote handle/PG/profile, complete canonical program, inventory/guard scope or budget was weakened. All root/runtime flags remain false; final exact independent review and fresh authority remain separate.
