"""One unexecuted P29 node22 source-window adapter, prepared for an exact root release.

The P30 extract-source.py copyts/select/showinfo mechanism supplies original
timestamps. The existing strict RGB/JPEG writer supplies bounded transport,
shared output accounting and owned-process cleanup. No old script is imported
or modified, and this adapter has no browser/API/story-publication capability.
"""
import argparse
from fractions import Fraction
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path('/home/rikka/Projects/stella')
HERE = Path(__file__).resolve().parent
OUT = HERE / 'run-1'
SOURCE = Path('/home/rikka/Videos/re0/真夜黑兔_Official_王都一日游篇/29 9本篇「结束与开始」Ver尤里乌斯.mp4')
SOURCE_SHA = '2301181cfd466b5126f1a37df45194b6b1fac71c15ffdd7ee90146f5109e6a90'
FFMPEG = Path('/usr/bin/ffmpeg')
FFMPEG_SHA = 'fc5db7b88a2a96e9a9036fbc9533d8b3ec16abbc31526b285e996ae1d81b9fcd'
PYTHON = Path('/home/rikka/.local/share/stella/python311/bin/python3.11')
PYTHON_SHA = 'ae4d2688a80846776aff8045a17a980b57027318e33a68c17f5c2b280c6aa84a'
VENV = ROOT / '.venv-video-ocr'
PIL_DIR = VENV / 'lib/python3.11/site-packages/PIL'
PIL_TREE_SHA = '4c32f6181e53b8aa29c77529bb75c225f23526dae31965b1d700a02e27fc4d5e'
WIDTH, HEIGHT, BLOCK = 480, 856, 480 * 856 * 3
START, END, MAX_FRAMES = 292, 301, 300
CAP, RESERVE, STDERR_CAP = 96 * 1024**2, 16 * 1024**2, 1024**2
STOP = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def record(path):
    return dict(path=str(path), bytes=Path(path).stat().st_size, sha256=digest(path))


def source_stat():
    s = SOURCE.stat()
    return dict(dev=s.st_dev, ino=s.st_ino, bytes=s.st_size,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)


def pillow_record():
    files = [dict(path=p.relative_to(PIL_DIR).as_posix(), bytes=p.stat().st_size, sha256=digest(p))
             for p in sorted(PIL_DIR.rglob('*')) if p.is_file() and p.suffix in ('.py', '.so')]
    payload = (json.dumps(files, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    return dict(path=str(PIL_DIR), files=len(files), treeSHA256=hashlib.sha256(payload).hexdigest())


def request_stop(signum, frame):
    # Never throw between Popen and ownership registration. The next normal
    # transport gate raises inside the producer's try/finally instead.
    global STOP
    STOP = STOP or signum


def gate(deadline):
    need(STOP is None, 'Supervisor stop signal: ' + str(STOP))
    need(time.monotonic() < deadline, 'Capture wall-time limit reached')


class Budget:
    """Charge preparation files, JPEGs, logs and JSON to one 96 MiB total.

    Payloads are complete in RAM before this synchronized pre-write check.
    Ordinary writes stop below 80 MiB, preserving 16 MiB for failure/closure
    evidence. RLIMIT_FSIZE/-fs would only limit individual files, not this sum.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.used = self.actual()
        need(self.used < CAP - RESERVE, 'Preparation already reaches stop margin')

    def actual(self):
        return sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())

    def write(self, stream, payload, emergency=False):
        with self.lock:
            need(self.used + len(payload) < (CAP if emergency else CAP - RESERVE),
                 'Combined output budget reached')
            count = stream.write(payload)
            need(count == len(payload), 'Short evidence write')
            self.used += count

    def file(self, name, payload, emergency=False):
        with (OUT / name).open('xb') as stream:
            self.write(stream, payload, emergency)

    def json(self, name, value, emergency=False):
        self.file(name, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode(), emergency)


class Drain(threading.Thread):
    """Keep original stderr while the main thread consumes exact RGB blocks."""
    def __init__(self, pipe, log, budget):
        super().__init__(name='P29-original-stderr', daemon=False)
        self.pipe, self.log, self.budget = pipe, log, budget
        self.rows, self.timebase, self.error = [], None, None
        self.condition, self.finished, self.bytes = threading.Condition(), False, 0

    def run(self):
        try:
            while True:
                line = self.pipe.readline(65537)
                if not line:
                    break
                allowed = min(len(line), 65536, max(0, STDERR_CAP - self.bytes))
                self.budget.write(self.log, line[:allowed])
                self.bytes += allowed
                need(len(line) <= 65536 and allowed == len(line), 'Original stderr size limit reached; retained prefix only')
                text = line.decode('utf-8', errors='replace')
                tb = re.search(r'config in time_base:\s*([^,\s]+)', text)
                m = re.search(r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([^\s]+).*?\bs:(\d+)x(\d+)\b', text)
                with self.condition:
                    if tb:
                        need(self.timebase in (None, tb[1]), 'Original timebase changed')
                        self.timebase = tb[1]
                    if m and 'showinfo' in text:
                        n, pts, seconds, width, height = m.groups()
                        need(int(n) == len(self.rows) < MAX_FRAMES, 'Original showinfo order/count exceeds bound')
                        need((int(width), int(height)) == (WIDTH, HEIGHT), 'Original dimensions differ')
                        need(self.timebase is not None, 'Original showinfo has no timebase')
                        exact = int(pts) * Fraction(self.timebase)
                        need(START <= exact < END, 'Original integer PTS is outside 292<=PTS<301')
                        self.rows.append(dict(sourceDecodedIndex=int(n), pts=int(pts), ptsTime=seconds,
                                              exactPTSSeconds=str(exact), width=int(width), height=int(height)))
                    self.condition.notify_all()
        except BaseException as error:
            self.error = repr(error)
        finally:
            with self.condition:
                self.finished = True
                self.condition.notify_all()

    def row(self, number, deadline):
        with self.condition:
            while len(self.rows) <= number and not self.finished and not self.error:
                gate(deadline)
                self.condition.wait(.1)
            need(not self.error, 'Original stderr failed: ' + str(self.error))
            need(len(self.rows) > number, 'RGB block lacks original PTS row')
            return dict(self.rows[number])


def block(pipe, selector, drain, deadline):
    data = bytearray()
    while len(data) < BLOCK:
        gate(deadline)
        need(not drain.error, 'Original stderr failed: ' + str(drain.error))
        if not selector.select(.1):
            continue
        try:
            part = os.read(pipe.fileno(), min(65536, BLOCK - len(data)))
        except BlockingIOError:
            continue
        if not part:
            need(not data, 'Truncated raw RGB frame at EOF')
            return None
        data.extend(part)
    return bytes(data)


def group_members(group):
    result = []
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            try:
                if int((path / 'stat').read_text().rsplit(')', 1)[1].split()[2]) == group:
                    result.append(int(path.name))
            except (OSError, ValueError, IndexError):
                pass
    return sorted(result)


def close_owned(process, state):
    # Only the PID-named new session registered at Popen is eligible for stop.
    # Reap the producer, then independently inspect its PG; never kill by name.
    errors = []

    def attempt(label, action):
        try:
            return action()
        except BaseException as caught:
            errors.append(label + ': ' + repr(caught))

    if attempt('initial exit status', process.poll) is None:
        group = attempt('getpgid', lambda: os.getpgid(process.pid))
        if group != process.pid:
            errors.append('Owned PG changed/unproven; stop only the owned Popen child')
        attempt('TERM', lambda: os.killpg(process.pid, signal.SIGTERM) if group == process.pid else process.terminate())
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            state['termWaitTimedOut'] = True
        except BaseException as caught:
            errors.append('TERM wait: ' + repr(caught))
        if attempt('post-TERM exit status', process.poll) is None:
            actual_group = attempt('KILL getpgid', lambda: os.getpgid(process.pid))
            attempt('KILL', lambda: os.killpg(process.pid, signal.SIGKILL) if actual_group == process.pid else process.kill())
            attempt('KILL wait', lambda: process.wait(timeout=5))
    # A stop/wait failure cannot skip the remaining independent observations.
    state['exitCode'] = attempt('exit status', process.poll)
    state['pidAbsent'] = attempt('PID observation', lambda: not Path('/proc', str(process.pid)).exists())
    state['remainingGroupMembers'] = attempt('PG observation', lambda: group_members(process.pid))
    state['ownedStopErrors'] = errors
    state['closureProven'] = (state['exitCode'] is not None and state['pidAbsent'] is True and
                              state['remainingGroupMembers'] == [] and not errors)
    return errors + ([] if state['closureProven'] else ['Owned OS closure is unproven'])


def capture(budget, Image, state):
    # Preserve source PTS and every selected frame; there is no fps/scale/crop
    # filter. The producer's 300-frame limit is also a failure sentinel: reaching
    # it can never be reported as a naturally completed source window.
    argv = [str(FFMPEG), '-hide_banner', '-nostdin', '-loglevel', 'info', '-xerror',
            '-threads', '1', '-filter_threads', '1', '-filter_complex_threads', '1',
            '-copyts', '-ss', str(START), '-to', str(END), '-i', str(SOURCE),
            '-map', '0:v:0', '-an', '-sn', '-dn',
            '-vf', r'select=gte(t\,292)*lt(t\,301),showinfo', '-frames:v', str(MAX_FRAMES),
            '-pix_fmt', 'rgb24', '-c:v', 'rawvideo', '-threads:v', '1',
            '-fps_mode', 'passthrough', '-f', 'rawvideo', 'pipe:1']
    budget.json('decoder-command.json', dict(argv=argv, frameCapIsFailureSentinel=True,
                                            blockBytes=BLOCK, rawRGBWrittenToDisk=False))
    process, drain, error, rows = None, None, None, []
    state['producerStarted'] = False
    deadline = time.monotonic() + 120
    log = (OUT / 'ffmpeg.stderr.txt').open('xb')
    try:
        gate(deadline)
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=0, start_new_session=True)
        state.update(producerStarted=True, pid=process.pid, pgid=process.pid)
        drain = Drain(process.stderr, log, budget)
        drain.start()
        need(os.getpgid(process.pid) == process.pid, 'Producer did not create owned session')
        state.update(nice=os.getpriority(os.PRIO_PROCESS, process.pid),
                     cpuAffinity=sorted(os.sched_getaffinity(process.pid)))
        need(state['nice'] == 19 and state['cpuAffinity'] == [0, 1], 'Producer runtime limits differ')
        os.set_blocking(process.stdout.fileno(), False)
        with selectors.DefaultSelector() as selector, (OUT / 'frames.partial.jsonl').open('xb') as trace:
            selector.register(process.stdout, selectors.EVENT_READ)
            for number in range(1, MAX_FRAMES + 1):
                pixels = block(process.stdout, selector, drain, deadline)
                if pixels is None:
                    break
                item = drain.row(number - 1, deadline)
                image = Image.frombytes('RGB', (WIDTH, HEIGHT), pixels)
                encoded = BytesIO()
                try:
                    image.save(encoded, format='JPEG', quality=95, subsampling=0)
                finally:
                    image.close()
                payload = encoded.getvalue()
                name = f'frames/{number:06d}.jpg'
                budget.file(name, payload)
                row = dict(**item, frameNumber=number, file=name, bytes=len(payload),
                           sha256=hashlib.sha256(payload).hexdigest(), rawRGB24Bytes=BLOCK,
                           rawRGB24Sha256=hashlib.sha256(pixels).hexdigest())
                rows.append(row)
                budget.write(trace, (json.dumps(row, separators=(',', ':')) + '\n').encode())
                del pixels, payload
        need(0 < len(rows) < MAX_FRAMES, '300-frame cap reached or no frames; no truncated complete result')
        process.wait(timeout=max(.1, deadline - time.monotonic()))
        drain.join(timeout=5)
        need(not drain.is_alive() and drain.finished and not drain.error, 'Original stderr did not finish cleanly')
        need(process.returncode == 0 and len(rows) == len(drain.rows), 'Producer failed or PTS/RGB count differs')
        need(all(a['pts'] <= b['pts'] for a, b in zip(rows, rows[1:])), 'Original PTS decreased')
    except BaseException as caught:
        error = caught
        state['decodeError'] = traceback.format_exc()[-16384:]
    finally:
        cleanup = []
        if process is not None:
            try:
                cleanup.extend(close_owned(process, state))
            except BaseException as caught:
                cleanup.append(repr(caught))
            if drain is not None and drain.ident is not None:
                try:
                    drain.join(timeout=5)
                except BaseException as caught:
                    cleanup.append('stderr join: ' + repr(caught))
                try:
                    state['stderrReaderTerminal'] = not drain.is_alive()
                except BaseException as caught:
                    state['stderrReaderTerminal'] = False
                    cleanup.append('stderr terminal observation: ' + repr(caught))
                if not state['stderrReaderTerminal']:
                    cleanup.append('Original stderr thread remains alive')
            else:
                # If thread construction/start failed, no other consumer owns
                # stderr. The producer is terminal before this bounded drain;
                # preserve its startup diagnostics without a pipe deadlock.
                try:
                    need(process.poll() is not None, 'Producer remains alive; refusing a blocking startup drain')
                    left = STDERR_CAP
                    while left:
                        piece = process.stderr.read(min(65536, left))
                        if not piece:
                            break
                        budget.write(log, piece, emergency=True)
                        left -= len(piece)
                    state['stderrReaderTerminal'] = True
                except BaseException as caught:
                    state['stderrReaderTerminal'] = True  # No thread was started.
                    cleanup.append('Startup stderr drain failed: ' + repr(caught))
            for label, stream in [('stdout close', process.stdout), ('stderr close', process.stderr)]:
                if label == 'stderr close' and not state.get('stderrReaderTerminal', False):
                    continue
                try:
                    stream.close()
                except BaseException as caught:
                    cleanup.append(label + ': ' + repr(caught))
        else:
            state['stderrReaderTerminal'] = True
        # An active reader retains its log. Closing a file is not evidence that
        # its writer ended. Otherwise flush and close are attempted separately.
        if state.get('stderrReaderTerminal', False):
            for label, action in [('stderr flush', log.flush), ('stderr log close', log.close)]:
                try:
                    action()
                except BaseException as caught:
                    cleanup.append(label + ': ' + repr(caught))
        state.update(cleanupErrors=cleanup, framesWritten=len(rows),
                     originalTimebase=drain.timebase if drain is not None else None)
        try:
            budget.json('decoder-process.json', state, emergency=bool(error or cleanup))
        except BaseException as caught:
            cleanup.append('decoder process record: ' + repr(caught))
    if error is not None:
        if state['cleanupErrors']:
            error.add_note('Independent cleanup observations: ' + repr(state['cleanupErrors'])[:8192])
        raise error
    need(not state['cleanupErrors'], 'Owned cleanup failed: ' + repr(state['cleanupErrors']))
    return dict(timeBase=drain.timebase, frames=rows, originalPTSRetained=True,
                naturalEOFBelowFrameCap=True, jpegQuality=95, jpegSubsampling=0,
                rawRGBWrittenToDisk=False, imagesInterpreted=False)


def main():
    parser = argparse.ArgumentParser(description='One root-reviewed P29 node22 292<=originalPTS<301 capture')
    parser.add_argument('--script-sha256', required=True)
    args = parser.parse_args()
    need(digest(Path(__file__)) == args.script_sha256, 'Reviewed script SHA differs')
    need(sys.flags.isolated and sys.dont_write_bytecode, 'Use the original venv Python with -I -B')
    need(Path(sys.prefix).resolve() == VENV.resolve(), 'Original ARM virtualenv is required')
    need(os.getpriority(os.PRIO_PROCESS, 0) == 19 and sorted(os.sched_getaffinity(0)) == [0, 1], 'Use nice19 CPU0,1')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        need(os.environ.get(name) == '1', 'Set native thread limit: ' + name)
    resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    need(not OUT.exists(), 'Fresh run-1 only; no retry or overwrite')
    OUT.mkdir()
    (OUT / 'frames').mkdir()
    budget, state, failure, index, inputs, before = Budget(), {}, None, None, {}, None
    try:
        inputs['script'] = record(Path(__file__))
        inputs['freeBytesBefore'] = os.statvfs(HERE).f_bavail * os.statvfs(HERE).f_frsize
        need(inputs['freeBytesBefore'] >= CAP, 'Available disk space is below the96MiB capture budget')
        for name, path, expected in [('python', PYTHON, PYTHON_SHA), ('ffmpeg', FFMPEG, FFMPEG_SHA)]:
            inputs[name] = record(path)
            need(inputs[name]['sha256'] == expected, 'Pinned tool bytes differ: ' + name)
            with path.open('rb') as stream:
                elf = stream.read(20)
            need(elf[:4] == b'\x7fELF' and int.from_bytes(elf[18:20], 'little') == 183, 'Tool is not AArch64 ELF')
        need(Path(sys.executable).resolve() == PYTHON and Path('/proc/self/exe').resolve() == PYTHON, 'Actual Python selection differs')
        # Verify the installed Pillow package bytes before its first import.
        # Isolated Python excludes the script directory and PYTHONPATH lookup.
        inputs['pillow'] = pillow_record()
        need(inputs['pillow']['treeSHA256'] == PIL_TREE_SHA, 'Pinned Pillow package bytes differ')
        before = source_stat()
        inputs['sourceBefore'] = dict(**before, sha256=digest(SOURCE))
        need(inputs['sourceBefore']['sha256'] == SOURCE_SHA and source_stat() == before, 'Fresh whole source SHA/stat differs')
        budget.json('input-bindings-before.json', inputs)
        from PIL import Image
        need(Path(Image.__file__).resolve() == PIL_DIR / 'Image.py', 'Actual Pillow module selection differs')
        index = capture(budget, Image, state)
        budget.json('frames-index.json', index)
        need(budget.actual() < CAP, 'Actual combined folder exceeded96MiB')
    except BaseException:
        failure = traceback.format_exc()[-16384:]
    finally:
        # Every feasible after-observation is independent and runs on failure
        # as well as success. A source drift cannot hide tool/script drift,
        # and secondary observations must not replace the original failure.
        after_errors = []

        def observe(label, action, matches):
            try:
                inputs[label] = action()
                need(matches(inputs[label]), label + ' differs from the pinned input')
            except BaseException as caught:
                after_errors.append(dict(input=label, error=repr(caught)))

        observe('sourceAfter', lambda: dict(**source_stat(), sha256=digest(SOURCE)),
                lambda value: value['sha256'] == SOURCE_SHA and
                (before is None or all(value[key] == before[key] for key in before)) and
                (before is None or source_stat() == before))
        observe('scriptAfter', lambda: record(Path(__file__)), lambda value: value['sha256'] == args.script_sha256)
        observe('pythonAfter', lambda: record(PYTHON), lambda value: value['sha256'] == PYTHON_SHA)
        observe('ffmpegAfter', lambda: record(FFMPEG), lambda value: value['sha256'] == FFMPEG_SHA)
        observe('pillowAfter', pillow_record, lambda value: value['treeSHA256'] == PIL_TREE_SHA)
        if after_errors and failure is None:
            failure = 'Final input byte checks failed; see each independent after observation'
        receipt = dict(schema='stella.P29.node22.single-source-capture.v1',
                       status='failed-retained' if failure else 'complete-unreviewed', failure=failure,
                       requestedOriginalPTSSeconds=[START, END], frameLimit=MAX_FRAMES,
                       actualFrames=len(index['frames']) if index is not None else state.get('framesWritten', 0),
                       freshWholeSourceSHA256=inputs.get('sourceBefore', {}).get('sha256'),
                       sourceExpectedSHA256=SOURCE_SHA, inputs=inputs, afterCheckErrors=after_errors, ownedProducer=state,
                       combinedBytesBeforeReceipt=budget.actual(), hardCapBytes=CAP,
                       ordinaryWriteReserveBytes=RESERVE, stderrCapBytes=STDERR_CAP,
                       sourceOrIdentityAccepted=False, imagesInterpreted=False, rawRGBWrittenToDisk=False,
                       browserAPIProbeOrFormalWrites=False, automaticRetry=False)
        budget.json('receipt.json', receipt, emergency=bool(failure))
        # Keep console diagnostics bounded; full metadata/failure details have
        # already passed through the budgeted receipt writer.
        print(json.dumps(dict(status=receipt['status'], receipt=str(OUT / 'receipt.json'),
                              sha256=digest(OUT / 'receipt.json'), combinedBytes=budget.actual())), flush=True)
    return 1 if failure else 0


if __name__ == '__main__':
    raise SystemExit(main())
