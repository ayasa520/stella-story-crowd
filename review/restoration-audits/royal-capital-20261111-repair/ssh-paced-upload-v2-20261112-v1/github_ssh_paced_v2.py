"""Pace one Git upload over the existing strict, freshly resolved SSH route.

The observed failed sockets stopped advancing with about555KiB unsent and
99% receive-window limitation after a short initial burst. This candidate
limits upload input to128KiB/s with a16KiB burst; it is not a diagnosis of the
remote implementation. SSH stdout remains directly connected to Git, so
advertisements/ACKs and small request/response handshakes remain full duplex.
No input is buffered wholesale, sought, logged, replayed or sent to another
connection. The caller still verifies the normal remote ref transaction.
"""
import os
import signal
import subprocess
import sys
import threading
import time

from github_ssh_route_v1 import log, ssh_command


def paced_command(command, rate=128*1024, burst=16*1024, timeout=900):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, bufsize=0)
    state = {'sent': 0, 'error': None}
    began = time.monotonic()

    def feed():
        tokens, sampled = float(burst), time.monotonic()
        try:
            while True:
                # os.read forwards even a single available protocol byte.
                # A buffered read(size) could wait for a full chunk while Git
                # waits for the remote reply, deadlocking a short handshake.
                chunk = os.read(sys.stdin.fileno(), burst)
                if not chunk:
                    break
                offset = 0
                while offset < len(chunk):
                    now = time.monotonic()
                    tokens = min(burst, tokens + (now-sampled)*rate)
                    sampled = now
                    count = min(len(chunk)-offset, int(tokens))
                    if count == 0:
                        time.sleep(min(.02, (1-tokens)/rate))
                        continue
                    count = os.write(process.stdin.fileno(), chunk[offset:offset+count])
                    tokens -= count
                    offset += count
                    state['sent'] += count
        except BrokenPipeError:
            # SSH owns the authoritative remote/exit status. Its normal or
            # failed close may race an input producer; never open a second
            # connection or replay the partially consumed Git stream.
            pass
        except OSError as error:
            state['error'] = str(error)
            if process.poll() is None:
                process.terminate()
        finally:
            process.stdin.close()

    def forward(signum, _frame):
        if process.poll() is None:
            process.send_signal(signum)

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, forward)
    worker = threading.Thread(target=feed, daemon=True)
    log(dict(status='paced_upload_started', child=process.pid, rate=rate, burst=burst))
    worker.start()
    # A responsive SSH transport is not proof that receive-pack is making
    # progress. Bound the whole child lifetime independently of keepalives;
    # deadline failure preserves the local commit and never retries/replays.
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        log(dict(status='paced_upload_deadline_exceeded', child=process.pid, timeout=timeout))
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill();process.wait()
        code = 124
    log(dict(status='paced_upload_exited', child=process.pid, exitCode=code,
             elapsedSeconds=time.monotonic()-began, sentBytes=state['sent'],
             sentBytesMeaning='accepted by child stdin, not a remote ACK',
             feederError=state['error'], stdinReplay=False))
    return code if code else int(state['error'] is not None)


def main():
    arguments = sys.argv[1:]
    command = ssh_command(arguments)
    if '-G' not in arguments and any('git-receive-pack' in value for value in arguments):
        raise SystemExit(paced_command(command))
    os.execv(command[0], command)


if __name__ == '__main__':
    main()
