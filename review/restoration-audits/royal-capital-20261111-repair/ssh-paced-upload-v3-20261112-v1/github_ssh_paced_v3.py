"""Coarsely pace one Git upload through the existing verified SSH route.

The cause of v2's latest upload timeout is UNKNOWN. This version fixes only a
local efficiency defect: an exhausted token bucket admitted one new byte at a
time, creating tiny writes/sleeps. A whole available read (at most16KiB) is now
scheduled at64KiB/s. This is not a promise to fix SSH or proof of a remote ACK.

Exactly one SSH child inherits stdout/stderr directly. Available short Git
handshakes are read with os.read, never held until a chunk fills. Partial pipe
writes retain their offset on that same connection; no input is logged,
rewound, replayed, re-resolved or reconnected. A single event loop also keeps
deadline/signal cleanup independent of blocked producer or consumer pipes.
"""
import math
import os
import select
import signal
import subprocess
import sys
import time

from github_ssh_route_v1 import log, ssh_command


def _signal_child_group(process, signum):
    # start_new_session makes this the owned child's group, never Git's or
    # the caller's. Include any local SSH helper descendants in cancellation.
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        pass


def _reap(process, already_signaled=False):
    if process.poll() is None:
        if not already_signaled:
            _signal_child_group(process, signal.SIGTERM)
        try:
            return process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _signal_child_group(process, signal.SIGKILL)
    return process.wait()


def paced_command(command, rate=64*1024, chunk_size=16*1024, timeout=900):
    if not math.isfinite(rate) or rate <= 0 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Pacing rate and timeout must be finite and positive')
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError('Chunk size must be a positive integer')
    began = time.monotonic()
    deadline = began + timeout
    process = None
    child_code = None
    requested_signal = None
    prior_handlers = {}
    reason = 'starting'
    error = None
    input_closed = False
    pending = b''
    offset = 0
    chunk_started = False
    queued_at = began
    next_allowed = began
    stats = dict(readCalls=0, readChunks=0, readBytes=0, writeCalls=0,
                 writtenBytes=0, partialWrites=0, wouldBlockWrites=0,
                 minWriteBytes=None, maxWriteBytes=0, scheduledChunks=0,
                 pacingWaitCalls=0, maxPlannedPacingWaitSeconds=0.0,
                 maxChunkFirstWriteDelaySeconds=0.0, maxSelectWaitSeconds=0.0)

    def forward(signum, _frame):
        nonlocal requested_signal
        if requested_signal is None:
            requested_signal = signum
        if process is not None and process.poll() is None:
            _signal_child_group(process, signum)

    def close_input():
        nonlocal input_closed
        if process is not None and not input_closed:
            # Unbuffered child stdin owns no Python buffer to flush. Closing
            # it sends EOF once; do not close/reopen or seek Git's input fd.
            input_closed = True
            process.stdin.close()

    try:
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            prior_handlers[signum] = signal.signal(signum, forward)
        if requested_signal is None:
            process = subprocess.Popen(command, stdin=subprocess.PIPE,
                stdout=None, stderr=None, bufsize=0, start_new_session=True)
            os.set_blocking(process.stdin.fileno(), False)
            input_fd = sys.stdin.fileno()
            output_fd = process.stdin.fileno()
            reason = 'running'
            log(dict(status='paced_upload_started', version=3, child=process.pid,
                     rate=rate, chunkSize=chunk_size, timeout=timeout,
                     pacing='one-deadline-per-available-chunk', stdinReplay=False))

            while True:
                if requested_signal is not None:
                    reason = 'signal'
                    # Also covers a signal delivered between the pre-spawn
                    # check and Popen assigning the sole child handle.
                    if process.poll() is None:
                        _signal_child_group(process, requested_signal)
                    break
                if process.poll() is not None:
                    reason = 'ssh_exit'
                    break
                now = time.monotonic()
                if now >= deadline:
                    reason = 'deadline'
                    log(dict(status='paced_upload_deadline_exceeded', version=3,
                             child=process.pid, timeout=timeout))
                    break

                reads, writes = [], []
                wait = min(0.25, deadline-now)
                if pending:
                    if chunk_started or now >= next_allowed:
                        writes = [output_fd]
                    else:
                        # Wait for this complete read's scheduled turn, not
                        # for one byte of refilled credit. A partial write of
                        # an admitted chunk never pays this delay again.
                        wait = min(wait, next_allowed-now)
                        stats['pacingWaitCalls'] += 1
                elif not input_closed:
                    reads = [input_fd]
                waited_at = time.monotonic()
                readable, writable, _ = select.select(reads, writes, [], wait)
                stats['maxSelectWaitSeconds'] = max(stats['maxSelectWaitSeconds'],
                                                    time.monotonic()-waited_at)
                if requested_signal is not None:
                    continue

                if readable:
                    stats['readCalls'] += 1
                    # os.read returns whatever is available, including a
                    # short pkt-line. Never accumulate to chunk_size before
                    # permitting the SSH response/advertisement handshake.
                    chunk = os.read(input_fd, chunk_size)
                    if not chunk:
                        close_input()
                        continue
                    pending, offset, chunk_started = chunk, 0, False
                    queued_at = time.monotonic()
                    stats['readChunks'] += 1
                    stats['readBytes'] += len(chunk)
                    stats['maxPlannedPacingWaitSeconds'] = max(
                        stats['maxPlannedPacingWaitSeconds'], max(0.0, next_allowed-queued_at))

                if writable:
                    written_at = time.monotonic()
                    stats['writeCalls'] += 1
                    try:
                        count = os.write(output_fd, memoryview(pending)[offset:])
                    except BlockingIOError:
                        stats['wouldBlockWrites'] += 1
                        continue
                    except BrokenPipeError:
                        # SSH remains authoritative for remote/exit status.
                        # Discard unsent local remainder without replay, then
                        # await that SAME child's exit or overall deadline.
                        reason = 'ssh_closed_input'
                        pending, offset = b'', 0
                        close_input()
                        continue
                    if count <= 0:
                        raise OSError('Child stdin accepted no bytes')
                    if not chunk_started:
                        # Reserve the whole actual read exactly once. The
                        # first chunk is immediate; idle time never builds
                        # extra burst credit. A real short read can produce a
                        # short write, but the limiter never splits a16KiB
                        # read into artificial one-token/one-byte writes.
                        next_allowed = max(next_allowed, written_at) + len(pending)/rate
                        chunk_started = True
                        stats['scheduledChunks'] += 1
                        stats['maxChunkFirstWriteDelaySeconds'] = max(
                            stats['maxChunkFirstWriteDelaySeconds'], written_at-queued_at)
                    remaining = len(pending)-offset
                    stats['partialWrites'] += int(count < remaining)
                    stats['writtenBytes'] += count
                    stats['minWriteBytes'] = count if stats['minWriteBytes'] is None else min(stats['minWriteBytes'], count)
                    stats['maxWriteBytes'] = max(stats['maxWriteBytes'], count)
                    offset += count
                    if offset == len(pending):
                        pending, offset = b'', 0
    except OSError as exception:
        # Metadata only: never include upload bytes, arguments or protocol
        # content in diagnostics. Cleanup below still owns the only child.
        reason = 'local_io_error'
        error = dict(type=type(exception).__name__, errno=exception.errno)
    finally:
        try:
            if process is not None:
                try:
                    close_input()
                finally:
                    child_code = _reap(process, already_signaled=requested_signal is not None)
        finally:
            for signum, handler in prior_handlers.items():
                signal.signal(signum, handler)

    if requested_signal is not None:
        code = 128 + requested_signal
    elif reason == 'deadline':
        code = 124
    elif error is not None:
        code = 1
    else:
        code = child_code if child_code >= 0 else 128-child_code
    log(dict(status='paced_upload_exited', version=3,
             child=process.pid if process is not None else None,
             exitCode=code, sshExitCode=child_code, reason=reason,
             elapsedSeconds=time.monotonic()-began, statistics=stats,
             pendingUnsentBytes=len(pending)-offset,
             sentBytesMeaning='accepted by child stdin, not a remote ACK',
             feederError=error, stdinReplay=False, reconnect=False))
    return code


def main():
    arguments = sys.argv[1:]
    command = ssh_command(arguments)
    if '-G' not in arguments and any('git-receive-pack' in value for value in arguments):
        raise SystemExit(paced_command(command))
    os.execv(command[0], command)


if __name__ == '__main__':
    main()
