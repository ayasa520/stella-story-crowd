# github_ssh_paced_v3.py — frozen offline source review

The new **Python** source is ready for root review/use at:

`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/github_ssh_paced_v3.py`

The current source is frozen following root's review. No further edits to that file were made after the freeze confirmation. V2, the route helper, repository configuration, SSH configuration and formal Git state were not modified. This preparation did not import or execute v3, resolve DNS, start SSH, perform push/fetch, or launch a browser.

## What this changes, and what it does not establish

V2's failure cause remains **unknown**. Root reported an earlier128KiB/s success of about2.59MB/55s and a later about4.29MB/139s timeout. The different results do not identify a transport cause. V3 addresses a concrete local loop defect only: after token exhaustion, v2 recomputed `int(tokens)` and could admit one byte, sleep until another byte accrued, and repeat. That needlessly fragmented a large already-read chunk.

V3 replaces token credit with a monotonic `next_allowed` timestamp for each actual available read, at64KiB/s and a maximum16KiB read. On the first successful write of a chunk it reserves `len(chunk)/rate` exactly once. All partial writes finish that admitted chunk by advancing its offset; they do not each wait for newly earned one-byte credit. The next chunk starts at its scheduled time, with no accumulated idle burst credit. A continuously available16KiB stream therefore has nominal0.25-second chunk spacing. A genuinely short producer read or a real partial pipe write can still be short; a small minimum-write statistic alone would not prove recurrence of v2's token-fragmentation defect.

This is a pacing-efficiency correction and a new bounded upload candidate. It does **not** promise to fix SSH, establish the cause of a timeout, confirm remote receive-pack progress or provide a remote ACK. Root's normal exact remote-ref verification remains authoritative.

## Stream and lifecycle review

- `ssh_command(arguments)` is called once, reusing the existing verified route construction and its host-key/certificate checks. The paced upload creates one SSH child. Non-upload and `-G` behavior retains v2's exec delegation.
- SSH stdout and stderr are inherited directly (`stdout=None,stderr=None`); the wrapper neither consumes nor serializes them. It only paces Git-to-SSH stdin.
- **The child's stdin write end is nonblocking.** Git's input fd keeps its existing flags. The event loop calls `os.read` after select indicates readiness and accepts any available short read. It never waits to fill16KiB or buffers the pack wholesale.
- At most one read chunk is pending. The sole child receives `memoryview(pending)[offset:]`; successful partial writes advance offset. An unaccepted remainder stays on that same child/connection. Broken pipe discards the local remainder and waits for that child's result; no input seek, replay, reconnection or second SSH child exists.
- The monotonic900-second deadline bounds the paced child/IO loop independently of producer input, pipe backpressure and SSH keepalives. Select waits are bounded by the remaining deadline and at most0.25 seconds. The existing route helper's separately bounded DNS resolution occurs before this child deadline, as in v2.
- TERM/INT/HUP are recorded and forwarded to the owned SSH process group. `start_new_session=True` isolates that group from Git/caller. Closing the unbuffered input sends EOF once. Cleanup waits up to5 seconds after termination/signaling, then sends KILL and waits to reap the child. The5-second cleanup grace is additional to the upload deadline. Original Python signal handlers are restored in finally paths.
- Normal SSH exit status is propagated, with negative signal return codes normalized to128+signal. A local IO error returns1, a paced deadline returns124, and a received wrapper signal returns128+signal. An unexpected exception still reaches the caller after finally cleanup; it is not converted into a successful SSH result.

## Diagnostics and checks

Start/final records use the existing local route log. Statistics contain only counts/times: read calls/chunks/bytes, write calls/accepted bytes, actual partial/would-block writes, minimum/maximum accepted write sizes, scheduled chunks, pacing waits, and maximum observed waits. `writtenBytes` explicitly means bytes accepted by child stdin, **not bytes acknowledged remotely**. No pack/protocol bytes, upload arguments or credentials are recorded by v3.

Performed source-only checks: Python AST parse and `compile(AST, ..., 'exec')`; static assertions for one Popen site, inherited stdout/stderr, no token bucket or time.sleep loop, direct short-read os.read, partial-write offset, and one whole-chunk length/rate reservation. These passed. Compilation did not execute the module, import the route helper, create bytecode files or invoke application/network code. No transport, timing, signal or subprocess runtime test is claimed.

Root owns the next single logged upload with a command-local core.sshCommand override and the separately specified-vvv/-E diagnostics. No repository config change or retry was performed by this reviewer. Caller-reported remote22e3943/local107a0ec and pack-size observations remain root's evidence; no extra repository audit was run here.
