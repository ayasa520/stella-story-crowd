"""Root-gated K5 single-capture RGB extraction; static preparation only.

Reuse the executed K4 RGB/PTS/strict-EOF mechanism for the independently
closed 54-talk0-only capture: exactly 453 frames, bound by its actual recorder
artifacts and root closure. Each native frame remains 500*1000*3 RGB bytes,
with original PTS and duplicates retained independently of Pillow JPEGs.
Earlier F1/F2/F3 and completed K4 output remain read-only; this new directory
alone has a 128 MiB hard cap and 32 MiB ordinary-write margin. No original
source recording or live canonical/data snapshot is an execution dependency.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import threading
import time
import traceback

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
HERE = Path(__file__).resolve().parent
OLD_F1 = A / 'episode5-six-private-kitv3-complete-actual-frames-v1'
OLD_F2 = A / 'episode5-six-private-kitv3-complete-actual-frames-v2'
OLD_F3 = A / 'episode5-six-private-kitv3-complete-actual-frames-v3'
OLD_K4_OUTPUT = A / 'episode5-silent54-nativeflag-complete-actual-frames-v2/run-1'
# P30 scope adapter: only INPUT, CAPTURE_CLOSURE and CASES differ from the
# executed K5 configuration. All extraction/contact/EOF/cleanup code remains
# unchanged. The recorder's 453 samples are an expectation, never a decoded
# result: real showinfo/RGB counts, one-byte EOF, exit0 and a terminal reader
# must independently prove completeness. Historical K5 schema/message labels
# below identify the reused mechanism; actual caseId/input/closure bind P30.
# Native JPEGs stay 500x1000. Contact tiles alone are reduced for inspection.
# Face-only scope: the new recorder reports 484 samples; decoded frame count
# and original PTS are still unobserved until actual transport and strict EOF.
# The six allowed literal edits are three scope inputs, CAP/MARGIN and two
# main count gates. Every other function byte remains the executed base.
# CAP/MARGIN below are authoritative: 96/24 MiB gives a 72 MiB ordinary disk
# ceiling, not a RAM limit. Older 453/128/32/K5 prose is historical provenance.
# This budget never changes native 500x1000 JPEG95, original PTS or sampling.
INPUT = A / 'p30-node4-face-bikkuri-owner-kit-rootfalse-v1/attempt-1'
CAPTURE_CLOSURE = A / 'p30-face-bikkuri-root-preparation-e77938f6-v1/runtime.root-closure.json'
CASES = [('p30-node4-face-bikkuri-only', 484)]
WIDTH, HEIGHT, BLOCK_BYTES = 500, 1000, 500*1000*3
CAP, MARGIN = 96*1024*1024, 24*1024*1024
FFMPEG = '/usr/bin/ffmpeg'
FONT = Path('/usr/share/fonts/noto/NotoSans-Regular.ttf')
STDERR_CAP = 8*1024*1024
STOP_SIGNAL = None


def request_stop(signum,frame):
    """Record cancellation without throwing across subprocess ownership.

    Python can deliver a signal between Popen returning and its assignment or
    registration. A flag-only handler allows that indivisible ownership setup
    to finish; cooperative gates then raise inside the owned try/finally.
    No signal mask, preexec callback or inherited child mask is introduced.
    """
    global STOP_SIGNAL
    if STOP_SIGNAL is None:
        STOP_SIGNAL = signum


def check_stop():
    if STOP_SIGNAL is not None:
        raise InterruptedError('Deferred supervisor signal '+str(STOP_SIGNAL))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def record(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def tree_manifest(directory):
    return {str(path.relative_to(directory)): dict(bytes=path.stat().st_size, sha256=sha(path))
            for path in sorted(directory.rglob('*')) if path.is_file()}


def group_members(group):
    members = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group:
                members.append(int(path.name))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(members)


class OutputBudget:
    """Account every byte of the new K5 extraction directory before writing.

    JPEG/contact images are encoded to memory first. Bounded diagnostics use
    the same synchronized writer, so the stderr thread cannot race a pixel
    writer past the shared cap. The 32 MiB margin remains unused on success.
    No raw RGB stream is ever written to disk.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.accounted = sum(path.stat().st_size for path in HERE.rglob('*') if path.is_file())
        require(self.accounted < CAP-MARGIN, 'Existing K5 output already reaches stop margin')

    def write(self, stream, payload, emergency=False):
        with self.lock:
            ceiling = CAP if emergency else CAP-MARGIN
            require(self.accounted+len(payload) < ceiling, 'K5 output stop margin reached')
            written = stream.write(payload)
            require(written == len(payload), 'Short evidence write')
            self.accounted += written

    def bytes_file(self, path, payload, emergency=False):
        with Path(path).open('xb') as stream:
            self.write(stream,payload,emergency=emergency)

    def json_file(self, path, value, emergency=False):
        self.bytes_file(path,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode(),emergency=emergency)

    def checkpoint(self):
        actual = sum(path.stat().st_size for path in HERE.rglob('*') if path.is_file())
        require(actual < CAP, 'Actual K5 output reached hard cap')
        return actual


class StderrReader(threading.Thread):
    """One independent original-stderr drain, with no model/pixel sampling.

    Draining continuously prevents FFmpeg from deadlocking on a full stderr
    pipe while the main thread reads exact pixel blocks. Every raw line is
    retained before parsing; exceptions are communicated to the main reader.
    Neither reader silently drops diagnostics or accepts missing showinfo.
    """
    def __init__(self, pipe, log, budget, expected):
        super().__init__(name='original-ffmpeg-stderr-reader',daemon=False)
        self.pipe,self.log,self.budget,self.expected = pipe,log,budget,expected
        self.condition = threading.Condition()
        self.rows,self.time_base,self.error,self.finished = [],None,None,False
        self.byte_count,self.line_number,self.header_lines = 0,0,[]

    def run(self):
        try:
            while True:
                line = self.pipe.readline(65537)
                if not line:
                    break
                require(len(line)<=65536, 'Unexpected oversized stderr line')
                self.line_number += 1
                self.byte_count += len(line)
                require(self.byte_count<=STDERR_CAP, 'Original stderr budget exceeded')
                self.budget.write(self.log,line)
                text = line.decode('utf-8',errors='replace')
                if ('Input #' in text or 'Output #' in text or
                        ('Stream #' in text and 'Video:' in text)):
                    self.header_lines.append(dict(line=self.line_number,text=text.rstrip('\r\n')))
                timebase = re.search(r'config in time_base:\s*([^,\s]+)',text)
                frame = re.search(r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([^\s]+).*?\bs:(\d+)x(\d+)\b',text)
                with self.condition:
                    if timebase:
                        require(self.time_base in (None,timebase[1]), 'Unexpected original timebase change')
                        self.time_base = timebase[1]
                    if 'showinfo' in text and frame:
                        n,pts,pts_time,width,height = frame.groups()
                        require(int(n)==len(self.rows), 'Missing/reordered original showinfo index')
                        require((int(width),int(height))==(WIDTH,HEIGHT), 'Native dimensions changed')
                        require(len(self.rows)<self.expected, 'Extra decoded frame beyond exact capture receipt')
                        self.rows.append(dict(sourceDecodedIndex=int(n),pts=int(pts),ptsTime=pts_time,
                                              width=int(width),height=int(height)))
                    self.condition.notify_all()
        except BaseException as error:
            with self.condition:
                self.error = repr(error)
                self.condition.notify_all()
        finally:
            with self.condition:
                self.finished = True
                self.condition.notify_all()

    def row(self,index,deadline):
        with self.condition:
            check_stop()
            while len(self.rows)<=index and not self.error and not self.finished:
                check_stop()
                require(time.monotonic()<deadline, 'Original showinfo wait exceeded wall budget')
                self.condition.wait(.1)
            require(not self.error, 'Original stderr reader failed: '+str(self.error))
            require(len(self.rows)>index, 'Pixel block has no corresponding original showinfo frame')
            return dict(self.rows[index])


def raw_command(source):
    return [FFMPEG,'-hide_banner','-nostdin','-loglevel','info','-xerror',
            '-threads','1','-filter_threads','1','-filter_complex_threads','1','-copyts',
            '-i',str(source),'-map','0:v:0','-an','-sn','-dn','-vf','showinfo',
            '-pix_fmt','rgb24','-c:v','rawvideo','-threads:v','1',
            '-fps_mode','passthrough','-f','rawvideo','pipe:1']


def read_exact_or_eof(pipe,selector,reader,deadline,size):
    """Return one exact block, clean EOF, or fail on a truncated block.

    The selector gives wall/error gates an opportunity even when FFmpeg has
    stalled. A clean EOF is valid only between whole blocks. After the exact
    expected count, a separate one-byte read proves true EOF; extra data is
    rejected rather than hidden with -frames or a truncated consumer.
    """
    result = bytearray()
    while len(result)<size:
        check_stop()
        require(time.monotonic()<deadline, 'Raw transport wall budget exceeded')
        require(not reader.error, 'Original stderr reader failed: '+str(reader.error))
        if not selector.select(.1):
            continue
        try:
            piece = os.read(pipe.fileno(),min(65536,size-len(result)))
        except BlockingIOError:
            continue
        if not piece:
            require(not result, 'EOF in the middle of a raw RGB frame')
            return None
        result.extend(piece)
    return bytes(result)


def stop_owned(process,log):
    errors = []
    if process.poll() is None:
        try:
            os.killpg(process.pid,signal.SIGTERM)
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL)
            process.wait(timeout=5)
        except BaseException as error:
            errors.append(repr(error))
    remaining = group_members(process.pid)
    log.update(exitCode=process.poll(),remainingGroupMembers=remaining,
               pidAbsent=not Path('/proc',str(process.pid)).exists(),cleanupErrors=errors)
    require(not remaining and log['pidAbsent'] and not errors, 'Owned decoder closure is unproven')


def make_contacts(folder,rows,budget):
    directory = folder/'contacts'
    directory.mkdir()
    font = ImageFont.truetype(str(FONT),14)
    sheets = []
    for start in range(0,len(rows),20):
        check_stop()
        subset = rows[start:start+20]
        sheet = Image.new('RGB',(1250,2104),'#101010')
        draw = ImageDraw.Draw(sheet)
        for offset,row in enumerate(subset):
            check_stop()
            x,y = (offset%5)*250,(offset//5)*526
            with Image.open(folder/row['file']) as image:
                require(image.size==(WIDTH,HEIGHT),'JPEG dimensions changed')
                tile = image.convert('RGB').resize((250,500),Image.Resampling.LANCZOS)
                sheet.paste(tile,(x,y))
                tile.close()
            draw.text((x+4,y+503),f"f{row['frameNumber']:06d}  PTS {row['ptsTime']}",font=font,fill='white')
        output = BytesIO()
        sheet.save(output,format='JPEG',quality=82,subsampling=0)
        check_stop()
        path = directory/f'{start//20:03d}-f{subset[0]["frameNumber"]:06d}-f{subset[-1]["frameNumber"]:06d}.jpg'
        budget.bytes_file(path,output.getvalue())
        sheets.append(dict(**record(path),frames=[row['frameNumber'] for row in subset]))
        sheet.close()
    require([n for sheet in sheets for n in sheet['frames']]==list(range(1,len(rows)+1)),
            'Contact sheets must cover every frame exactly once in sequence')
    return sheets


def decode_case(case,expected,source,output,budget,handles,announce):
    folder = output/case
    folder.mkdir()
    (folder/'frames').mkdir()
    argv = raw_command(source)
    budget.json_file(folder/'decoder-command.json',dict(argv=argv,nice=19,cpuAffinity=[0,1],
        decoderFilterEncoderThreadsEach=1,frameBlockBytes=BLOCK_BYTES,pillowQuality=95,pillowSubsampling=0))
    rows,process,reader = [],None,None
    failure = None
    deadline = time.monotonic()+180
    child = dict(caseId=case,role='ffmpeg-raw-RGB24',exitCode=None,pgidVerified=False)
    stderr_log = (folder/'ffmpeg.stderr').open('xb')
    try:
        # This stream deliberately outlives the producer/reader cleanup.
        # Closing a with-block first on an exception could discard the last
        # original diagnostic while the independent drain was still active.
        check_stop()
        process = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                   bufsize=0,start_new_session=True)
        # start_new_session establishes a PID-named owned group. Register that
        # minimal identity before any enrichment or announcement can fail.
        # The deferred signal handler cannot raise in this ownership interval.
        child.update(pid=process.pid,pgid=process.pid)
        handles.append(child)
        # Start the sole stderr drain before the first cooperative stop gate,
        # so even a cancellation immediately after spawn preserves diagnostics.
        reader = StderrReader(process.stderr,stderr_log,budget,expected)
        reader.start()
        check_stop()
        require(os.getpgid(process.pid)==child['pgid'],'Actual owned group differs')
        child.update(pgidVerified=True,startedUTC=datetime.now(timezone.utc).isoformat(),
                     nice=os.getpriority(os.PRIO_PROCESS,process.pid),cpuAffinity=sorted(os.sched_getaffinity(process.pid)))
        require(child['nice']==19 and child['cpuAffinity']==[0,1], 'Actual decoder limits differ')
        check_stop()
        announce('running',child)
        os.set_blocking(process.stdout.fileno(),False)
        with selectors.DefaultSelector() as selector, (folder/'frames.partial.jsonl').open('xb') as frame_trace:
            selector.register(process.stdout,selectors.EVENT_READ)
            for number in range(1,expected+1):
                check_stop()
                pixels = read_exact_or_eof(process.stdout,selector,reader,deadline,BLOCK_BYTES)
                require(pixels is not None, 'Early EOF before exact capture frame count')
                item = reader.row(number-1,deadline)
                raw_sha = hashlib.sha256(pixels).hexdigest()
                image = Image.frombytes('RGB',(WIDTH,HEIGHT),pixels)
                jpeg = BytesIO()
                image.save(jpeg,format='JPEG',quality=95,subsampling=0)
                image.close()
                check_stop()
                path = folder/'frames'/f'{number:06d}.jpg'
                budget.bytes_file(path,jpeg.getvalue())
                row = dict(**item,frameNumber=number,file='frames/'+path.name,bytes=path.stat().st_size,
                           sha256=sha(path),rawRGB24Bytes=BLOCK_BYTES,rawRGB24Sha256=raw_sha)
                rows.append(row)
                budget.write(frame_trace,(json.dumps(row,separators=(',',':'))+'\n').encode())
                del pixels
            require(read_exact_or_eof(process.stdout,selector,reader,deadline,1) is None,
                    'Extra raw bytes after exact capture frame count; no truncated success')
        process.wait(timeout=max(.1,deadline-time.monotonic()))
        reader.join(timeout=5)
        require(not reader.is_alive() and reader.finished and not reader.error, 'Original stderr did not close cleanly')
        require(process.returncode==0, 'FFmpeg failed; retain original stderr without retry')
        require(len(reader.rows)==len(rows)==expected and reader.time_base, 'Original PTS count/timebase mismatch')
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        if process is not None:
            cleanup_failure = None
            try:
                stop_owned(process,child)
                if reader is not None and reader.ident is not None:
                    reader.join(timeout=5)
                    require(not reader.is_alive(), 'Original stderr reader remains alive')
                else:
                    # If reader construction/start failed, no thread can own
                    # this pipe. The producer is now proven terminal, so drain
                    # already-produced bytes once without a deadlock or retry.
                    while True:
                        line = process.stderr.readline(65537)
                        if not line:
                            break
                        require(len(line)<=65536,'Oversized retained startup diagnostic')
                        budget.write(stderr_log,line,emergency=True)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
            except BaseException as error:
                cleanup_failure = repr(error)
            child.update(endedUTC=datetime.now(timezone.utc).isoformat(),failure=failure,cleanupFailure=cleanup_failure,
                         stderrReaderTerminal=reader is None or not reader.is_alive())
            stderr_log.flush()
            stderr_log.close()
            budget.json_file(folder/'decoder-process.json',child,emergency=bool(failure or cleanup_failure))
            announce('terminal',child)
            require(cleanup_failure is None,'Decoder cleanup failed: '+str(cleanup_failure))
        else:
            stderr_log.close()
    duplicate_pairs = [dict(previousFrame=a['frameNumber'],currentFrame=b['frameNumber'],pts=a['pts'],ptsTime=a['ptsTime'])
                       for a,b in zip(rows,rows[1:]) if a['pts']==b['pts']]
    decreasing = [dict(previousFrame=a['frameNumber'],currentFrame=b['frameNumber'],previousPTS=a['pts'],currentPTS=b['pts'])
                  for a,b in zip(rows,rows[1:]) if b['pts']<a['pts']]
    check_stop()
    budget.json_file(folder/'frames-index.json',dict(schema='stella.silent54-talk0-only.original-PTS-raw-RGB-every-frame.v1',caseId=case,
        input=record(source),timeBase=reader.time_base,frames=rows,duplicateOriginalPTSPairs=duplicate_pairs,
        decreasingOriginalPTSPairs=decreasing,allOriginalPTSRetained=True,allFramesSequential=True,
        exactCountAndStrictEOF=True,rawRGBStreamSaved=False,jpegQuality=95,jpegSubsampling=0,
        freshMetadataSource='actual K5 talk0-only capture FFmpeg header/showinfo and exact RGB count/EOF; no fresh ffprobe',
        actualHeaderLines=reader.header_lines,freshFfprobeExecuted=False,
        completeOriginalHeaderAndDiagnostics=record(folder/'ffmpeg.stderr')))
    check_stop()
    sheets = make_contacts(folder,rows,budget)
    check_stop()
    budget.json_file(folder/'contact-index.json',dict(sheets=sheets,everyFrameCoveredOnceInOrder=True,
                                                    imagesInterpreted=False))
    check_stop()
    return dict(caseId=case,frames=expected,sheets=len(sheets),decoder=child,
                frameIndex=record(folder/'frames-index.json'),contactIndex=record(folder/'contact-index.json'),
                duplicatePTSPairs=duplicate_pairs,decreasingPTSPairs=decreasing,strictEOF=True,
                rawStreamBytesConsumed=expected*BLOCK_BYTES)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release',required=True)
    parser.add_argument('--release-sha256',required=True)
    args = parser.parse_args()
    require(os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[0,1], 'Use nice19 CPU0,1')
    release_path = Path(args.release).resolve()
    require(sha(release_path)==args.release_sha256,'Root release hash differs')
    release = json.loads(release_path.read_text())
    require(release['rootConfirmed'] is True and release['changedRawRGBDecoderAuthorized'] is True,
            'Separate root approval for this changed conversion mechanism is required')
    require(release['cases']==[case for case,_ in CASES] and release['expectedFrames']==[484], 'Exact one K5 case only')
    require(release['newOutputCapBytes']==CAP and release['stopMarginBytes']==MARGIN, 'Exact K5 output budget required')
    require(release['codeSha256']==sha(Path(__file__)),'Reviewed code differs')
    capture_closure = release['captureRootClosure']
    require(capture_closure['path']==str(CAPTURE_CLOSURE) and
            isinstance(capture_closure['bytes'],int) and capture_closure['bytes']>0 and
            isinstance(capture_closure['sha256'],str) and len(capture_closure['sha256'])==64,
            'A complete independent K5 root closure binding is required')
    require(record(CAPTURE_CLOSURE)==capture_closure,'Fresh independent K5 root closure differs')
    proof = release['mechanismProof']
    require(record(proof['path'])==proof,'Reviewed mechanism proof differs')
    require(record(release['legacyF1Inventory']['path'])==release['legacyF1Inventory'],'Legacy F1 inventory differs')
    expected_f1 = json.loads(Path(release['legacyF1Inventory']['path']).read_text())
    require(tree_manifest(OLD_F1)==expected_f1['files'],'Preserved legacy F1 tree changed')
    require(record(release['legacyF2Inventory']['path'])==release['legacyF2Inventory'],'Legacy F2 inventory differs')
    expected_f2 = json.loads(Path(release['legacyF2Inventory']['path']).read_text())
    require(tree_manifest(OLD_F2)==expected_f2['files'],'Preserved legacy F2 tree changed')
    require(record(release['legacyF3Inventory']['path'])==release['legacyF3Inventory'],'Legacy F3 inventory differs')
    expected_f3 = json.loads(Path(release['legacyF3Inventory']['path']).read_text())
    require(tree_manifest(OLD_F3)==expected_f3['files'],'Preserved completed legacy F3 tree changed')
    # Root supplies the completed K4 output subtree, not a live renderer/data
    # snapshot. Preserve those pixels without re-running historical guards.
    require(record(release['legacyK4Inventory']['path'])==release['legacyK4Inventory'],'Completed K4 inventory differs')
    expected_k4 = json.loads(Path(release['legacyK4Inventory']['path']).read_text())
    require(expected_k4['root']==str(OLD_K4_OUTPUT),'Completed K4 inventory root differs')
    # This root-issued inventory uses rows, while the inherited tree guard
    # uses a relative-path map. Normalize without altering the source receipt.
    expected_k4_files = {item['path']:dict(bytes=item['bytes'],sha256=item['sha256'])
                         for item in expected_k4['files']}
    require(len(expected_k4_files)==len(expected_k4['files']),'Duplicate completed K4 inventory path')
    require(tree_manifest(OLD_K4_OUTPUT)==expected_k4_files,'Preserved completed K4 output tree changed')
    expected_tools = dict(ffmpeg=FFMPEG,python=sys.executable,font=str(FONT),
        pillow_init=sys.modules['PIL'].__file__,pillow_image=Image.__file__,
        pillow_imaging=Image.core.__file__,pillow_font=ImageFont.__file__)
    require(set(release['toolBindings'])==set(expected_tools),'All exact installed tool/Pillow inputs must be bound')
    for key,item in release['toolBindings'].items():
        require(item['path']==expected_tools[key],'Unexpected actual tool path: '+key)
        require(record(item['path'])==item,'Actual approved tool/Pillow/font file differs')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        require(os.environ.get(key)=='1','Bound native library threads: '+key)
    require(pillow_version==release['pillowVersion'],'Pillow version differs')
    required_inputs = {str(INPUT/case/name) for case,_ in CASES
                       for name in ('actual.mkv','capture-receipt.json','recorder-command.json')}
    required_inputs.update([str(INPUT/'capture-index.json'),str(CAPTURE_CLOSURE)])
    require(len(release['inputBindings'])==len(required_inputs) and
            {item['path'] for item in release['inputBindings']}==required_inputs,
            'Bind the K5 capture, receipt, recorder command, capture index and independent root closure')
    for item in release['inputBindings']:
        require(record(item['path'])==item,'Original input changed before conversion')
    output = HERE/'run-1'
    require(not output.exists(),'Fresh run directory only; no automatic retry')
    output.mkdir()
    budget = OutputBudget()
    # Defer stops until cooperative gates. In particular, no asynchronous
    # exception can split Popen from assignment and owned-group registration.
    signal.signal(signal.SIGTERM,request_stop)
    signal.signal(signal.SIGINT,request_stop)
    children,results = [],[]
    def announce(state,active=None):
        value = dict(supervisorPid=os.getpid(),supervisorPgid=os.getpgrp(),state=state,active=active,children=children,
                     nice=19,cpuAffinity=[0,1])
        text = (json.dumps(value,indent=2)+'\n').encode()
        # Diagnostics use unique records so repeated handle writes cannot
        # subtract/undercount bytes in the shared immutable-output budget.
        path = output/f'handles-{len(list(output.glob("handles-*.json"))):03d}.json'
        budget.bytes_file(path,text,emergency=state.startswith('failed') or bool(active and active.get('failure')))
        print(json.dumps(dict(event='RAW_DECODE_HANDLES',supervisorPid=os.getpid(),state=state,active=active)),flush=True)
    before = dict(code=record(Path(__file__)),release=record(release_path),inputBindings=release['inputBindings'],
                  legacyF1Inventory=release['legacyF1Inventory'],legacyF2Inventory=release['legacyF2Inventory'],
                  legacyF3Inventory=release['legacyF3Inventory'],legacyK4Inventory=release['legacyK4Inventory'],
                  captureRootClosure=capture_closure)
    budget.json_file(output/'input-bindings-before.json',before)
    failure = None
    try:
        announce('ready-before-first-decoder')
        for case,expected in CASES:
            check_stop()
            source = INPUT/case/'actual.mkv'
            require(any(item['path']==str(source) for item in release['inputBindings']),'Exact source is unbound')
            # There is no metadata subprocess. The single K5 actual capture,
            # its original recorder artifacts and independent root closure
            # bind this scope. Fresh metadata comes from that capture's own
            # budgeted FFmpeg header/showinfo, RGB count and genuine EOF.
            # No source-recording decode or fresh ffprobe result is claimed.
            results.append(decode_case(case,expected,source,output,budget,children,announce))
        require(sum(item['frames'] for item in results)==484, 'Exact complete K5 count required')
        announce('all-decoder-children-terminal')
    except BaseException as error:
        failure = dict(error=repr(error),traceback=traceback.format_exc())
        # All started child groups were stopped in their own finally blocks.
        # A failed attempt remains wholly retained and aborts later cases.
        announce('failed-retained-no-retry')
        raise
    finally:
        # Before/after evidence is required even after an early transport or
        # encoder failure. Never omit it just because a later case did not
        # start, and never report the expected hashes as fresh observations.
        after_errors = []
        observed_inputs = []
        for item in release['inputBindings']:
            try:
                actual = record(item['path'])
                observed_inputs.append(actual)
                require(actual==item,'Original input changed: '+item['path'])
            except BaseException as error:
                after_errors.append(repr(error))
        observed_code = record(Path(__file__))
        if observed_code['sha256'] != release['codeSha256']:
            after_errors.append('Conversion source changed')
        f1_unchanged = tree_manifest(OLD_F1)==expected_f1['files']
        if not f1_unchanged:
            after_errors.append('Preserved legacy F1 tree changed')
        f2_unchanged = tree_manifest(OLD_F2)==expected_f2['files']
        if not f2_unchanged:
            after_errors.append('Preserved legacy F2 tree changed')
        f3_unchanged = tree_manifest(OLD_F3)==expected_f3['files']
        if not f3_unchanged:
            after_errors.append('Preserved completed legacy F3 tree changed')
        k4_unchanged = tree_manifest(OLD_K4_OUTPUT)==expected_k4_files
        if not k4_unchanged:
            after_errors.append('Preserved completed K4 output tree changed')
        if after_errors and failure is None:
            failure = dict(error='Input preservation gate failed',details=after_errors)
        budget.json_file(output/'input-bindings-after.json',dict(inputBindings=observed_inputs,
            code=observed_code,allInputHashesUnchanged=not after_errors,
            legacyF1TreeExactlyUnchanged=f1_unchanged,legacyF2TreeExactlyUnchanged=f2_unchanged,
            legacyF3TreeExactlyUnchanged=f3_unchanged,legacyK4TreeExactlyUnchanged=k4_unchanged,errors=after_errors),emergency=bool(failure))
        # Derive the aggregate from observed comparisons even on failure.
        # A rejected preservation gate must never claim that all trees survived.
        receipt=dict(schema='stella.silent54-talk0-only.raw-RGB-to-native-JPEG.v1',status='failed-retained' if failure else 'single-complete',
            failure=failure,cases=results,children=children,sourceInputsBefore=before,
            newK5OutputBytes=budget.checkpoint(),newOutputCapBytes=CAP,unusedStopMarginBytes=MARGIN,
            priorExtractionTreesReferencedOnly=True,
            legacyF1F2F3K4Preserved=f1_unchanged and f2_unchanged and f3_unchanged and k4_unchanged,noAutomaticRetry=True,
            noOriginalVideoDecode=True,noTimestampAlteration=True,noFrameSampling=True,
            imagesInterpreted=False,performanceAccepted=False,browserStarted=False,apiCalled=False,
            freshFfprobeExecuted=False,freshMetadata='actual K5 talk0-only capture budgeted FFmpeg headers/showinfo; no fresh probe',
            sourceDataOrKitWritten=False,nice=19,cpuAffinity=[0,1])
        budget.json_file(output/'receipt.json',receipt,emergency=bool(failure))
        require(not after_errors,'Fresh after-input preservation checks failed; inspect retained receipt')


if __name__ == '__main__':
    main()
