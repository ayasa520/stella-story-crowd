"""Future single-browser controlled P30 face-native supervisor with owned-group cleanup.

The one Firefox process opens one fresh document. A recorder
starts before each unchanged program load and stops only after its declared
natural boundary or failure. Failed cases retain their raw capture/logs and
abort all following cases; no retry, media seeking or player stop is used to
manufacture a passing boundary. Independent OS/port/image gates remain root work.
"""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import select
import selectors
import signal
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request
from common import HERE, ROOT, load, sha, write, checked_guards, limits, processes, group_members

stop_history = []
early_cleanup_errors = []

def stop(process, signum=signal.SIGTERM):
    """Bounded owned-PGID stop; retain every failure instead of aborting cleanup."""
    result = {'pid': process.pid, 'pgid': process.pid, 'requestedSignal': int(signum),
              'signals': [], 'errors': [], 'graceWaitTimedOut': False,
              'remainingGroupMembers': None, 'absenceProven': False}

    def failed(stage):
        result['errors'].append({'stage': stage, 'traceback': traceback.format_exc()})

    def members(stage):
        try:
            return group_members(process.pid)
        except BaseException:
            failed(stage)
            return None

    def send(signum, stage):
        try:
            os.killpg(process.pid, signum)
            result['signals'].append({'stage': stage, 'signal': int(signum), 'sent': True})
        except ProcessLookupError:
            result['signals'].append({'stage': stage, 'signal': int(signum), 'alreadyAbsent': True})
        except BaseException:
            failed(stage)

    initial = members('initial-os-membership')
    try:
        launcher_alive = process.poll() is None
    except BaseException:
        failed('launcher-poll')
        launcher_alive = True
    if initial is None or initial or launcher_alive:
        send(signum, 'grace-signal-owned-group')
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        result['graceWaitTimedOut'] = True
        send(signal.SIGKILL, 'escalation-owned-group')
        try:
            process.wait(timeout=5)
        except BaseException:
            failed('post-kill-launcher-wait')
    except BaseException:
        failed('grace-launcher-wait')
    remaining = members('after-launcher-wait-os-membership')
    if remaining is None or remaining:
        send(signal.SIGKILL, 'remaining-owned-group')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            remaining = members('bounded-post-kill-os-membership')
            if remaining is None or not remaining:
                break
            try:
                time.sleep(.1)
            except BaseException:
                failed('post-kill-membership-wait')
                break
    # Neither a successful wait nor a sent SIGKILL proves group absence.
    # This final OS query is mandatory, and unknown/nonempty stays unproven.
    result['remainingGroupMembers'] = members('final-stop-os-proof')
    result['absenceProven'] = result['remainingGroupMembers'] == []
    result['exitCode'] = process.returncode
    if not result['absenceProven']:
        result['errors'].append({'stage': 'owned-group-absence-unproven', 'remainingGroupMembers': result['remainingGroupMembers']})
    stop_history.append(result)
    return result

def early_stop(role, process, signum=signal.SIGTERM):
    try:
        return stop(process, signum)
    except BaseException:
        early_cleanup_errors.append({'role': role, 'pid': process.pid, 'stage': 'early-owned-stop',
                                     'traceback': traceback.format_exc()})
        return None

def cleanup_owned(owned):
    """Attempt every owned group, then make a new, separate OS absence proof."""
    outcomes, unexpected, observations = [], [], []
    for role, process in reversed(owned):
        try:
            outcomes.append({'role': role, **stop(process, signal.SIGINT if role.startswith('recorder:') else signal.SIGTERM)})
        except BaseException:
            # A broken wait/query must not skip the remaining owned groups.
            unexpected.append({'role': role, 'pid': process.pid, 'traceback': traceback.format_exc()})
    for role, process in owned:
        observed = {'role': role, 'pid': process.pid, 'pgid': process.pid,
                    'exitCode': process.returncode, 'observedMonotonicSeconds': time.monotonic(),
                    'observationSucceeded': False, 'remainingGroupMembers': None}
        try:
            observed['remainingGroupMembers'] = group_members(process.pid)
            observed['observationSucceeded'] = True
        except BaseException:
            unexpected.append({'role': role, 'pid': process.pid, 'stage': 'independent-final-os-query',
                               'traceback': traceback.format_exc()})
        observations.append(observed)
    cleanup_errors = [dict(error, pid=item['pid']) for item in stop_history for error in item['errors']] + unexpected + early_cleanup_errors
    return {'stopAttempts': outcomes, 'allStopHistory': stop_history, 'cleanupErrors': cleanup_errors,
            'finalOSMembership': observations,
            'allOwnedGroupsEmpty': all(item['observationSucceeded'] and item['remainingGroupMembers'] == [] for item in observations),
            'doesNotProveEscapedDescendantAbsence': True}

def authority(path):
    # Built-in open supports opener; keep exclusive creation and mode 0600.
    with open(path, 'xb', opener=lambda name, flags: os.open(name, flags, 0o600)) as stream:
        stream.write(struct.pack('>H', 65535))
        for piece in [b'', b'', b'MIT-MAGIC-COOKIE-1', os.urandom(16)]:
            stream.write(struct.pack('>H', len(piece)))
            stream.write(piece)

parser = argparse.ArgumentParser()
parser.add_argument('--release', required=True)
parser.add_argument('--release-sha256', required=True)
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
assert re.fullmatch(r'attempt-[1-9][0-9]*', args.attempt)
release_path = Path(args.release).resolve()
assert sha(release_path) == args.release_sha256
release = load(release_path)
for flag in ['rootConfirmed', 'executionAuthorized', 'browserLaunchAuthorized',
             'diagnosticInstrumentationAuthorized', 'continuousRecorderAuthorized', 'controlledNativeCandidateAuthorized']:
    assert release.get(flag) is True, flag
assert release['attempt'] == args.attempt
assert os.environ.get('STELLA_BROWSER_OWNER') == release['browserOwner']
binding = load(HERE / 'frozen/binding.json')
assert [p['id'] for p in binding['plans']] == ['p30-node4-face-bikkuri-only']
assert binding['nativeOnlyOverlay'] is True and binding['controlledNativeCandidate'] is True
assert binding['noProgramMutation'] is True
for plan in binding['plans']:
    assert [step['scenario'] for step in plan['steps']] == [3, 4, 5]
    assert plan['stop']['scenario'] == 5 and plan['stop']['phase'] == 'ready'
    assert plan['stop']['forbiddenNext'] == 6 and plan['stop']['forbiddenEdge'].endswith(':51')
    assert plan['ordinaryBaseline'] is False and plan['controlledNativeCandidate'] is True
    assert plan['aliasIsGitCommit'] is False and re.fullmatch('[a-f0-9]{40}', plan['alias'])
    assert plan['alias'] != binding['finalDataHead']
    assert plan['expectedSemanticDiff'] == [{'path': '/scenario_list/3/motion', 'before': '', 'after': ',face_bikkuri'}]
    assert plan['overlay']['path'] == str(HERE / 'frozen' / 'p30-node4-face-bikkuri-only' / '10450054.json')
    assert plan['overlay']['sha256'] == sha(plan['overlay']['path'])
    assert binding['fileGuards'][plan['overlay']['path']] == plan['overlay']['sha256']
    target = next(step for step in plan['steps'] if step['target'])
    assert target['scenario'] == 4 and target['native']['character'] == 'live2d/AC_subaru_tshirt01'
    assert target['native']['motion'] == ''
    assert target['candidateMotion'] == ',face_bikkuri'
    assert target['parsedMotion'] == {'body': '', 'face': 'face_bikkuri', 'extras': []}
assert release['bindingSha256'] == sha(HERE / 'frozen/binding.json')
assert release['normalPreparationIndexSha256'] == sha(HERE / 'prepared/index.json')
assert load(HERE / 'prepared/index.json')['allSucceeded'] is True
for key in ['finalDataHead', 'finalSourceHead', 'browserOwner']:
    assert release[key] == binding[key]
guards = release['runtimeBindings']
for path, expected in binding['fileGuards'].items():
    assert guards.get(path) == expected, path
for name in ['common.py', 'freeze.py', 'prepare.mjs', 'transport.mjs', 'server.mjs', 'workers-private.mjs', 'node-guards.mjs', 'owner-events.mjs',
             'curve-audit.mjs', 'driver.mjs', 'run.py', 'README.md', 'plan.rootfalse.json', 'static-report.rootfalse.json',
             'frozen/binding.json', 'frozen/plan.json', 'prepared/index.json',
             'prepared/p30-node4-face-bikkuri-only.request.json',
             'prepared/p30-node4-face-bikkuri-only.http.json',
             'prepared/p30-node4-face-bikkuri-only.receipt.json',
             'prepared/p30-node4-face-bikkuri-only.raw.json.gz',
             'prepared/p30-node4-face-bikkuri-only.complete-program-diff.json',
             'prepared/baseline.request.json', 'prepared/baseline.http.json',
             'prepared/baseline.receipt.json', 'prepared/baseline.raw.json.gz',
             'frozen/provider-events.jsonl']:
    assert guards.get(str(HERE / name)) == sha(HERE / name), name
# Bind the actual interpreter and both Node launches to the declared tools.
# Checking another executable on PATH would not establish what ran this kit.
assert Path(sys.executable).resolve() == Path(binding['tools']['python']['binaryPath']).resolve()
assert sha(sys.executable) == binding['tools']['python']['sha256']
limits()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
budgets = binding['budgets']
out = HERE / args.attempt
out.mkdir()  # An existing attempt, including a failed one, must never be reused.
write(out / 'release-binding.json', {'path': str(release_path), 'sha256': sha(release_path),
                                    'rootConfirmed': True, 'runtimeBindings': guards})
owned, logs, captures = [], [], []
handles = {'supervisorPid': os.getpid(), 'nice': 19, 'affinity': [0, 1], 'state': 'guarding', 'owned': []}
status, recording = 1, None
private_temp = None

def announce():
    # This mutable handle file is diagnostic only; the static release and all
    # artifact input files are kept separate and are never rewritten here.
    (out / 'handles.json').write_text(json.dumps(handles, indent=2) + '\n')
    print('HANDLES ' + json.dumps(handles), flush=True)

def spawn(role, argv, env, log_path, **kwargs):
    log = log_path.open('xb')
    logs.append(log)
    process = subprocess.Popen(argv, env=env, stderr=subprocess.STDOUT,
                               stdout=log, start_new_session=True, **kwargs)
    owned.append((role, process))
    handles['owned'].append({'role': role, 'pid': process.pid, 'pgid': process.pid})
    announce()
    return process

def verify():
    assert sha(release_path) == args.release_sha256
    return checked_guards(guards)

def stop_recorder(case_id):
    global recording
    assert recording and recording['caseId'] == case_id
    item = recording
    ended_early = item['process'].poll() is not None
    stop_outcome = stop(item['process'], signal.SIGINT)
    progress = {}
    path = item['folder'] / 'recorder-progress.txt'
    if path.exists():
        for line in path.read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                progress[key.strip()] = value.strip()
    movie = item['folder'] / 'actual.mkv'
    receipt = {'caseId': case_id, 'pid': item['process'].pid, 'pgid': item['process'].pid,
               'exitCode': item['process'].returncode, 'endedBeforeRequestedStop': ended_early,
               'ownedGroupStop': stop_outcome, 'groupAbsenceProven': stop_outcome['absenceProven'],
               'recordStart': item['started'], 'recordEndWallEpochMilliseconds': time.time_ns() / 1e6,
               'frames': int(progress.get('frame', '0')), 'progress': progress,
               'bytes': movie.stat().st_size if movie.exists() else 0,
               'sha256': sha(movie) if movie.exists() and stop_outcome['absenceProven'] else None,
               'xSurfaceSamplesAreNotUniqueGLFrames': True, 'audioCaptured': False,
               'containerDecodeVerified': False, 'motionAccepted': False}
    write(item['folder'] / 'capture-receipt.json', receipt)
    captures.append(receipt)
    recording = None
    assert stop_outcome['absenceProven'] and not stop_outcome['errors'], 'Recorder cleanup failed/unproven; preserve private state'
    assert not ended_early, 'Recorder hit a bound/exited before the requested natural boundary'
    assert receipt['exitCode'] in [0, 255], receipt
    assert 0 < receipt['frames'] <= budgets['videoFramesPerCase'], receipt
    assert 0 < receipt['bytes'] <= budgets['videoBytesPerCase'], receipt
    verify()  # Each case has its own after-guard gate before another case begins.
    return receipt

try:
    before = verify()
    write(out / 'inputs-before.json', before)
    inventory = processes()
    (out / 'processes-before.txt').write_text(inventory)
    assert not [line for line in inventory.splitlines()[1:]
                if re.search(r'\b(?:firefox|chrome|chromium|Xvfb)(?:\s|$)', line.split(None, 3)[-1])], 'Another browser/display is live'
    with socket.socket() as test:
        test.bind(('127.0.0.1', 5198))
    binary_evidence = {}
    for name, tool in binding['tools'].items():
        assert sha(tool['binaryPath']) == tool['sha256']
        output = subprocess.check_output(['file', tool['binaryPath']], text=True)
        assert 'ARM aarch64' in output, output
        binary_evidence[name] = {**tool, 'actualFileOutput': output}
    write(out / 'binary-platform.json', {'tools': binary_evidence, 'nice': 19, 'affinity': [0, 1],
          'recorderDecoderThreads': 1, 'recorderEncoderThreads': 1, 'filterThreads': 1,
          'GALLIUM_DRIVER': 'llvmpipe', 'LIBGL_ALWAYS_SOFTWARE': '1', 'LP_NUM_THREADS': '1', 'MESA_GLTHREAD': 'false'})
    # mkdtemp has no automatic finalizer. Profile/authority deletion belongs
    # exclusively to the explicit owned-group OS cleanup gate below.
    private_temp = Path(tempfile.mkdtemp(prefix='stella-six-private-owner-'))
    temp = private_temp
    auth = temp / 'authority'
    authority(auth)
    channel, announcement = os.pipe()
    try:
        xvfb = spawn('xvfb', [binding['tools']['xvfb']['launchPath'], '-displayfd', str(announcement),
            '-screen', '0', '500x1000x24', '-auth', str(auth), '-nolisten', 'tcp', '-noreset'],
            os.environ.copy(), out / 'xvfb.log', pass_fds=(announcement,))
    finally:
        os.close(announcement)
    assert select.select([channel], [], [], 10)[0], 'Owned Xvfb did not announce a display'
    with os.fdopen(channel, 'rb') as stream:
        display = ':' + stream.readline(32).decode().strip()
    assert display[1:].isdigit()
    env = os.environ.copy()
    env.pop('STELLA_HOSTING', None)
    env.update(DISPLAY=display, XAUTHORITY=str(auth), GDK_BACKEND='x11', MOZ_ENABLE_WAYLAND='0',
               GALLIUM_DRIVER='llvmpipe', LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='1', MESA_GLTHREAD='false',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', STELLA_PRIVATE_OUTPUT=str(out),
               STELLA_PRIVATE_ATTEMPT=args.attempt, STELLA_RUNTIME_RELEASE_PATH=str(release_path),
               STELLA_RUNTIME_RELEASE_SHA256=args.release_sha256)
    server = spawn('server', [binding['tools']['node']['launchPath'], '--import', str(HERE / 'transport.mjs'), str(HERE / 'server.mjs')], env, out / 'server.log')
    end = time.monotonic() + 20
    while True:
        assert server.poll() is None, 'Owned Worker host exited; inspect original server.log'
        try:
            with urllib.request.urlopen('http://127.0.0.1:5198/player/player.html', timeout=2) as reply:
                assert reply.status == 200
            break
        except OSError:
            if time.monotonic() >= end:
                raise
            time.sleep(.1)
    profile = temp / 'firefox-profile'
    profile.mkdir()
    (profile / 'user.js').write_text('''user_pref("browser.shell.checkDefaultBrowser",false);
user_pref("network.proxy.type",1);
user_pref("network.proxy.http","127.0.0.1");user_pref("network.proxy.http_port",9);
user_pref("network.proxy.ssl","127.0.0.1");user_pref("network.proxy.ssl_port",9);
user_pref("network.proxy.no_proxies_on","127.0.0.1,localhost");
''')
    browser = spawn('browser', [binding['tools']['firefox']['launchPath'], '--kiosk', '--window-size', '500,1000',
        '--no-remote', '--profile', str(profile), '--remote-debugging-port', '0', 'about:blank'], env, out / 'firefox.log')
    try:
        end, address = time.monotonic() + 30, None
        while time.monotonic() < end and browser.poll() is None:
            found = re.search(r'WebDriver BiDi listening on (ws://127.0.0.1:\d+)', (out / 'firefox.log').read_text())
            if found:
                address = found[1]
                break
            time.sleep(.1)
        assert address, 'Firefox did not announce BiDi; retain actual firefox.log'
        driver_log = (out / 'driver.log').open('x')
        logs.append(driver_log)
        driver = subprocess.Popen([binding['tools']['node']['launchPath'], str(HERE / 'driver.mjs'), address], env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True, bufsize=1, start_new_session=True)
        owned.append(('driver', driver))
        handles.update(state='capturing', address=address, display=display)
        handles['owned'].append({'role': 'driver', 'pid': driver.pid, 'pgid': driver.pid})
        announce()
        selector = selectors.DefaultSelector()
        selector.register(driver.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + budgets['totalWallSeconds']
        while True:
            assert time.monotonic() < deadline, 'Total private-run wall budget reached'
            if recording:
                assert recording['process'].poll() is None, 'Recorder ended before its natural boundary request'
            events = selector.select(.2)
            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    selector.unregister(key.fileobj)
                    continue
                driver_log.write(line)
                driver_log.flush()
                if not line.startswith('OWNER_IPC '):
                    continue
                message = json.loads(line[len('OWNER_IPC '):])
                case_id = message['caseId']
                assert case_id in [p['id'] for p in binding['plans']]
                if message['type'] == 'capture-start':
                    assert recording is None
                    assert case_id == binding['plans'][len(captures)]['id'], 'Cases must remain sequential and non-retried'
                    folder = out / case_id
                    assert folder.is_dir()
                    cap = budgets['videoBytesPerCase']
                    def recorder_limit():
                        resource.setrlimit(resource.RLIMIT_FSIZE, (cap, cap))
                    argv = [binding['tools']['ffmpeg']['launchPath'], '-nostdin', '-n', '-hide_banner',
                      '-filter_threads', '1', '-filter_complex_threads', '1', '-threads', '1', '-f', 'x11grab',
                      '-draw_mouse', '0', '-video_size', '500x1000', '-framerate', '30', '-i', display,
                      '-an', '-c:v', 'libx264', '-threads', '1', '-preset', 'ultrafast', '-crf', '23',
                      '-maxrate', '1200k', '-bufsize', '2400k', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough',
                      '-frames:v', str(budgets['videoFramesPerCase']), '-fs', str(cap),
                      '-progress', str(folder / 'recorder-progress.txt'), '-nostats', str(folder / 'actual.mkv')]
                    started = {'wallEpochMilliseconds': time.time_ns() / 1e6, 'monotonicSeconds': time.monotonic()}
                    recorder = spawn('recorder:' + case_id, argv, env, folder / 'capture.log', preexec_fn=recorder_limit)
                    recording = {'caseId': case_id, 'folder': folder, 'process': recorder, 'started': started}
                    write(folder / 'recorder-command.json', {'argv': argv, 'start': started, 'threadBounds': 1})
                    # A live PID alone does not prove that X11 capture has
                    # started. Require its first real surface sample before
                    # allowing the driver to load the predecessor program.
                    first_frame = None
                    ready_deadline = time.monotonic() + 10
                    while time.monotonic() < ready_deadline and recorder.poll() is None:
                        progress_path = folder / 'recorder-progress.txt'
                        if progress_path.exists():
                            frames = re.findall(r'^frame=(\d+)\s*$', progress_path.read_text(), re.MULTILINE)
                            if frames and int(frames[-1]) > 0:
                                first_frame = {'frames': int(frames[-1]), 'observedWallEpochMilliseconds': time.time_ns() / 1e6}
                                break
                        time.sleep(.05)
                    assert first_frame, 'Recorder did not prove its first surface frame; inspect original capture.log'
                    write(folder / 'recorder-first-frame.json', first_frame)
                    reply = {'replyTo': message['id'], 'ok': True, 'recorderPid': recorder.pid, 'recordStart': started}
                elif message['type'] == 'capture-end':
                    reply = {'replyTo': message['id'], 'ok': True, 'capture': stop_recorder(case_id)}
                else:
                    raise ValueError('Unexpected driver IPC type')
                driver.stdin.write(json.dumps(reply) + '\n')
                driver.stdin.flush()
            if driver.poll() is not None and not selector.get_map():
                status = driver.returncode
                break
        if status == 0:
            assert len(captures) == 1 and recording is None
            # An earlier result file may predate a late original fatal event.
            # Driver exit0 also requires its post-session terminal decision;
            # this remains distinct from the supervisor/root OS exit proof.
            terminal = load(out / 'terminal-acceptance.json')
            assert terminal['accepted'] is True and terminal['sessionRetired'] is True
        write(out / 'capture-index.json', {'captures': captures, 'driverExitCode': status,
              'oneBrowserSession': True, 'motionAccepted': False, 'containerDecodeVerified': False})
    finally:
        if 'driver' in locals():
            early_stop('driver', driver)
        if recording:
            try:
                stop_recorder(recording['caseId'])
            except BaseException:
                early_cleanup_errors.append({'role': 'recorder', 'stage': 'early-recorder-cleanup',
                                             'traceback': traceback.format_exc()})
        early_stop('browser', browser)
finally:
    failure = sys.exc_info()[1]
    failure_trace = traceback.format_exc() if failure else None
    cleanup = cleanup_owned(owned)
    for stream in logs:
        try:
            stream.close()
        except BaseException:
            cleanup['cleanupErrors'].append({'stage': 'log-close', 'traceback': traceback.format_exc()})
    if 'selector' in locals():
        try:
            selector.close()
        except BaseException:
            cleanup['cleanupErrors'].append({'stage': 'selector-close', 'traceback': traceback.format_exc()})
    if failure or cleanup['cleanupErrors'] or not cleanup['allOwnedGroupsEmpty']:
        status = 1

    def persist_final(name, value):
        try:
            write(out / name, value)
            return True
        except BaseException:
            # Group cleanup has already been attempted for every owner. If a
            # diagnostic file cannot be saved, keep temporary state for root.
            print('FINAL_RECORD_WRITE_FAILED ' + json.dumps({'file': name, 'traceback': traceback.format_exc()}),
                  file=sys.stderr, flush=True)
            return False

    temporary_state = {'root': str(private_temp) if private_temp else None,
                       'profile': str(private_temp / 'firefox-profile') if private_temp else None,
                       'authority': str(private_temp / 'authority') if private_temp else None,
                       'deletionAttempted': False, 'deleted': False, 'preservedForRoot': private_temp is not None,
                       'deletionError': None}
    gate_recorded = persist_final('owned-cleanup-gate.json', {**cleanup, 'temporaryPaths': temporary_state})
    # Deletion is a separate action after all owned stop attempts and a new
    # successful OS absence proof. Any cleanup/query/log failure keeps paths.
    deletion_allowed = cleanup['allOwnedGroupsEmpty'] and not cleanup['cleanupErrors'] and gate_recorded
    temporary_state['cleanupGateRecorded'] = gate_recorded
    temporary_state['deletionAllowedByOwnedProof'] = deletion_allowed
    if private_temp is not None and deletion_allowed:
        temporary_state['deletionAttempted'] = True
        try:
            shutil.rmtree(private_temp)
            temporary_state['deleted'] = True
            temporary_state['preservedForRoot'] = False
        except BaseException:
            temporary_state['deletionError'] = traceback.format_exc()
            status = 1
    elif private_temp is not None:
        status = 1
        print('TEMPORARY_STATE_PRESERVED ' + json.dumps(temporary_state), flush=True)
    if not gate_recorded or not persist_final('temporary-state-cleanup.json', temporary_state):
        status = 1
    if failure or cleanup['cleanupErrors'] or temporary_state['deletionError']:
        if not persist_final('supervisor-failure.json', {'error': str(failure), 'traceback': failure_trace,
                'cleanupErrors': cleanup['cleanupErrors'], 'temporaryState': temporary_state}):
            status = 1
    same = False
    try:
        after = verify()
        write(out / 'inputs-after.json', after)
        same = before == after
        assert same
    except BaseException:
        persist_final('input-guard-failure.json', {'traceback': traceback.format_exc()})
        status = 1
    closure = {'owned': cleanup['finalOSMembership'],
               'allOwnedGroupsEmpty': cleanup['allOwnedGroupsEmpty'], 'inputsUnchanged': same,
               'cleanupErrors': cleanup['cleanupErrors'], 'temporaryState': temporary_state,
               'driverExitCode': driver.returncode if 'driver' in locals() else None,
               'supervisorStatus': status, 'supervisorPid': os.getpid(), 'imageReviewStarted': False,
               'requiresIndependentOSPortsGuardsAfterSupervisorExit': True,
               'ownedGroupProofDoesNotExcludeEscapedDescendants': True}
    try:
        with (out / 'processes-after.txt').open('x') as process_file:
            process_file.write(processes())
    except BaseException:
        status = 1
        persist_final('process-inventory-failure.json', {'traceback': traceback.format_exc()})
    if not persist_final('process-exit.json', closure):
        status = 1
    handles['state'] = 'closed' if cleanup['allOwnedGroupsEmpty'] else 'cleanup-unproven'
    handles['temporaryState'] = temporary_state
    try:
        announce()
    except BaseException:
        status = 1
        print('HANDLE_RECORD_FAILURE ' + traceback.format_exc(), file=sys.stderr, flush=True)
    print('CLOSURE ' + json.dumps(closure), flush=True)
sys.exit(status)
