"""One future root-released saved Worker/ARM Firefox session.

This P22 supervisor binds one new one-case4-node driver and its exact ordinary API program.
Profile retirement is conditional on fresh OS evidence after every role has
received an independent best-effort stop attempt; errors never imply closure.
Historical choice92/Rom13/full46 helpers remain immutable reuse provenance.

The supervisor owns only the process groups it creates. A failure retains the
actual logs, never retries and closes its browser before removing its profile.
Independent image review starts only after the supervisor itself has exited and
a separate process inventory confirms complete closure.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def load(path):
    return json.loads(Path(path).read_text())

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def inputs(binding):
    data, source = Path(binding['dataRoot']), Path(binding['sourceRoot'])
    return {'dataHead': git(data, 'rev-parse', 'HEAD'), 'dataStatus': git(data, 'status', '--short'),
            'dataInputs': {p: sha(data / p) for p in binding['dataInputs']},
            'protectedFirstThree': {p: sha(data / p) for p in binding['protectedFirstThree']},
            'resourceAndSourceGuards': {p: sha(ROOT / p) for p in binding['resourceAndSourceGuards']},
            'globalGuards': {p: sha(ROOT / p) for p in binding['globalGuards']},
            'toolFiles': {p: sha(p) for p in binding['toolFiles']},
            'kitGuards': {p: sha(p) for p in binding['kitGuards']},
            'sourceHead': git(source, 'rev-parse', 'HEAD'), 'sourceStatus': git(source, 'status', '--short'),
            'sourceFiles': {p: sha(source / p) for p in binding['source']['sourceFiles']},
            'distFiles': {p: sha(source / 'dist' / p) for p in binding['source']['distFiles']}}

def check_inputs(actual, binding):
    for key in ['dataHead', 'dataStatus', 'dataInputs', 'protectedFirstThree', 'resourceAndSourceGuards', 'globalGuards', 'toolFiles', 'kitGuards']:
        assert actual[key] == binding[key], key
    for key in ['sourceFiles', 'distFiles']:
        assert actual[key] == binding['source'][key], key
    assert actual['sourceHead'] == binding['source']['head']
    assert actual['sourceStatus'] == binding['source']['status']

def processes():
    return subprocess.check_output(['ps', '-eo', 'pid,ppid,pgid,comm,args'], text=True)

def members(group):
    result = []
    for line in processes().splitlines()[1:]:
        fields = line.strip().split(None, 4)
        if len(fields) >= 4 and int(fields[2]) == group:
            result.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                           'comm': fields[3], 'args': fields[4] if len(fields) > 4 else ''})
    return result

def stop(process):
    """Attempt only this Popen's newly created PGID, retaining every failure.

    A completed wait only reaps the launcher; it does not prove descendants
    exited. Conversely, SIGKILL is a request, not an exit receipt. The caller
    obtains a separate final PID/PGID inventory before retiring any profile.
    """
    result = {'pid': process.pid, 'pgid': process.pid, 'signals': [], 'errors': [],
              'lastGroupObservation': None}

    def signal_group(sig):
        try:
            os.killpg(process.pid, sig)
            result['signals'].append({'signal': int(sig), 'outcome': 'sent'})
        except ProcessLookupError:
            result['signals'].append({'signal': int(sig), 'outcome': 'group-not-found'})
        except Exception as error:
            result['errors'].append({'operation': 'killpg', 'signal': int(sig),
                                     'error': str(error), 'traceback': traceback.format_exc()})

    def observe_group():
        try:
            remaining = members(process.pid)
            result['lastGroupObservation'] = remaining
            return remaining
        except Exception as error:
            result['errors'].append({'operation': 'group-inventory', 'error': str(error),
                                     'traceback': traceback.format_exc()})
            result['lastGroupObservation'] = None
            return None

    # These are exclusively the process groups created with start_new_session.
    # Do not signal a discovered external browser or an escaped foreign group.
    signal_group(signal.SIGTERM)
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        signal_group(signal.SIGKILL)
        try:
            process.wait(timeout=5)
        except Exception as error:
            result['errors'].append({'operation': 'wait-after-kill', 'error': str(error),
                                     'traceback': traceback.format_exc()})
    except Exception as error:
        result['errors'].append({'operation': 'wait-after-term', 'error': str(error),
                                 'traceback': traceback.format_exc()})

    remaining = observe_group()
    if remaining is None or remaining:
        signal_group(signal.SIGKILL)
        end = time.monotonic() + 5
        while time.monotonic() < end:
            remaining = observe_group()
            if remaining == [] or remaining is None:
                break
            time.sleep(.1)
    # Never translate an unknown inventory into an empty group. Even if this
    # function returns with survivors, final cleanup must preserve the profile.
    return result


def owned_inventory(owned):
    """Read one actual OS inventory for owned PIDs and their original PGIDs."""
    raw = processes()
    entries = []
    for line in raw.splitlines()[1:]:
        fields = line.strip().split(None, 4)
        if len(fields) >= 4:
            entries.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                            'comm': fields[3], 'args': fields[4] if len(fields) > 4 else ''})
    rows = []
    for name, process, _ in owned:
        rows.append({'kind': name, 'pid': process.pid, 'pgid': process.pid,
                     'exitCode': process.returncode,
                     'remainingOwnedPid': [row for row in entries if row['pid'] == process.pid],
                     'remainingGroupMembers': [row for row in entries if row['pgid'] == process.pid]})
    return raw, rows

parser = argparse.ArgumentParser()
parser.add_argument('--release', required=True)
parser.add_argument('--release-sha256', required=True)
parser.add_argument('--attempt', default='attempt-1')
args = parser.parse_args()
assert re.fullmatch(r'attempt-[1-9][0-9]*', args.attempt)
release_path = Path(args.release).resolve()
assert sha(release_path) == args.release_sha256
release = load(release_path)
assert all(release.get(k) is True for k in ['rootConfirmed', 'executionAuthorized', 'browserLaunchAuthorized'])
assert release['attempt'] == args.attempt
assert os.environ.get('STELLA_BROWSER_OWNER') == release['browserOwner']
binding = load(HERE / 'input-binding.json')
assert release['browserOwner'] == binding['browserOwner']
assert release['publishedHead'] == binding['dataHead'] == binding['revision']
assert release['sourceHead'] == binding['source']['head']
assert release['inputBindingSha256'] == sha(HERE / 'input-binding.json')
assert release['planSha256'] == sha(HERE / 'capture-plan.json')
prepared_receipt = load(HERE / 'normal-prepare-receipt.json')
assert prepared_receipt['allStatus200'] is True
assert release['normalProgramSha256ByCase'] == {
    key: value['programSha256'] for key, value in prepared_receipt['programs'].items()}
assert set(prepared_receipt['programs']) == {'p22-ending23-to26'}
bindings = release['runtimeBindings']
required = [HERE / name for name in ['run.py', 'play.mjs', 'guards.mjs', 'prepare-normal.mjs',
             'freeze-inputs.py', 'worktree-upstream.mjs', 'input-binding.json', 'capture-plan.json',
             'normal-prepare-receipt.json', 'static-report.rootfalse.json']]
for case_id in prepared_receipt['programs']:
    for suffix in ['request.json', 'response.json.gz', 'http.json', 'receipt.json', 'route.json']:
        required.append(HERE / ('prepared/' + case_id + '.' + suffix))
required += [ROOT / name for name in ['artifacts/stella-local-deployment-3394828/serve-local.mjs',
  'artifacts/stella-local-deployment-3394828/workers-local.mjs', 'artifacts/stella-local-deployment-3394828/d1-local.mjs',
  'artifacts/stella-p30-firefox-20261120/bidi.mjs', 'artifacts/stella-p30-firefox-20261120/render-probe.mjs',
  'artifacts/stella-script-continuation-20261121/episode5-silent54-saved-runtime-v2/ending-observer.mjs',
  'artifacts/stella-script-continuation-20261121/episode5-silent54-saved-runtime-v2/capture-readiness.mjs']]
for path in required:
    assert bindings.get(str(path.relative_to(ROOT))) == sha(path), str(path)
for path, expected in bindings.items():
    assert sha(ROOT / path) == expected, path
assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert sorted(os.sched_getaffinity(0)) == [0, 1]
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
out = HERE / args.attempt
out.mkdir()  # Existing attempts are immutable evidence and are never reused.
write(out / 'release-binding.json', {'path': str(release_path), 'sha256': sha(release_path), 'runtimeBindings': bindings})
owned = []
profile = None
before = None
handles = {'supervisorPid': os.getpid(), 'nice': 19, 'affinity': [0, 1],
           'server': None, 'browser': None, 'driver': None, 'state': 'fresh-guards'}
status = 1
try:
    before = inputs(binding)
    write(out / 'inputs-before.json', before)
    check_inputs(before, binding)
    inventory = processes()
    (out / 'processes-before.txt').write_text(inventory)
    assert not [line for line in inventory.splitlines()[1:]
                if re.search(r'\b(?:firefox|chrome|chromium|Xvfb)(?:\s|$)', line.split(None, 3)[-1])], 'Another test browser is live'
    with socket.socket() as test_socket:
        test_socket.bind(('127.0.0.1', 5198))
    elf = subprocess.check_output(['file', '/usr/lib/firefox/firefox'], text=True)
    assert 'ARM aarch64' in elf, elf
    write(out / 'browser-platform.json', {'path': str(Path('/usr/bin/firefox').resolve()), 'fileOutput': elf,
          'binarySha256': sha('/usr/lib/firefox/firefox'), 'GALLIUM_DRIVER': 'llvmpipe',
          'LIBGL_ALWAYS_SOFTWARE': '1', 'LP_NUM_THREADS': '1', 'MESA_GLTHREAD': 'false'})
    env = os.environ.copy()
    env.pop('STELLA_HOSTING', None)
    env.update(STELLA_REVIEW_DIST=str(Path(binding['sourceRoot']) / 'dist'), STELLA_REVIEW_REVISION=binding['revision'],
               STELLA_REVIEW_OUTPUT=str(out), GALLIUM_DRIVER='llvmpipe', LIBGL_ALWAYS_SOFTWARE='1',
               LP_NUM_THREADS='1', MESA_GLTHREAD='false', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    server_log = (out / 'server.log').open('wb')
    server = subprocess.Popen(['node', '--import', str(HERE / 'worktree-upstream.mjs'),
       str(ROOT / 'artifacts/stella-local-deployment-3394828/serve-local.mjs'), '5198'],
       env=env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
    owned.append(('server', server, server_log))
    handles['server'] = {'pid': server.pid, 'pgid': server.pid, 'origin': 'http://127.0.0.1:5198'}
    write(out / 'handles.json', handles)
    print('HANDLES ' + json.dumps(handles), flush=True)
    end = time.monotonic() + 20
    while True:
        if server.poll() is not None:
            raise RuntimeError('Saved Worker exited; inspect actual server.log')
        try:
            with urllib.request.urlopen('http://127.0.0.1:5198/player/player.html', timeout=2) as response:
                assert response.status == 200
            break
        except OSError:
            if time.monotonic() >= end:
                raise
            time.sleep(.1)
    # No auto-cleaning context manager: a surviving browser must retain its
    # actual profile and logs. Only the final OS-proven cleanup may remove it.
    profile = Path(tempfile.mkdtemp(prefix='stella-p22-ending-normal-qa-'))
    (profile / 'user.js').write_text('''user_pref("browser.shell.checkDefaultBrowser",false);
user_pref("network.proxy.type",1);
user_pref("network.proxy.http","127.0.0.1");
user_pref("network.proxy.http_port",9);
user_pref("network.proxy.ssl","127.0.0.1");
user_pref("network.proxy.ssl_port",9);
user_pref("network.proxy.no_proxies_on","127.0.0.1,localhost");
''')
    browser_log = (out / 'firefox.log').open('wb')
    browser = subprocess.Popen(['/usr/bin/firefox', '--headless', '--no-remote', '--profile', str(profile),
      '--remote-debugging-port', '0', 'about:blank'], env=env, stdout=browser_log,
      stderr=subprocess.STDOUT, start_new_session=True)
    owned.append(('browser', browser, browser_log))
    handles['browser'] = {'pid': browser.pid, 'pgid': browser.pid, 'profile': str(profile)}
    write(out / 'handles.json', handles)
    print('HANDLES ' + json.dumps(handles), flush=True)
    end, address = time.monotonic() + 25, None
    while time.monotonic() < end and browser.poll() is None:
        found = re.search(r'WebDriver BiDi listening on (ws://127.0.0.1:\d+)', (out / 'firefox.log').read_text())
        if found:
            address = found[1]
            break
        time.sleep(.1)
    if not address:
        raise RuntimeError('Firefox did not announce BiDi; inspect actual firefox.log')
    driver_log = (out / 'driver.log').open('wb')
    driver = subprocess.Popen(['node', str(HERE / 'play.mjs'), address], env=env,
      stdout=driver_log, stderr=subprocess.STDOUT, start_new_session=True)
    owned.append(('driver', driver, driver_log))
    handles['driver'] = {'pid': driver.pid, 'pgid': driver.pid, 'bidi': address}
    handles['state'] = 'capturing'
    write(out / 'handles.json', handles)
    print('HANDLES ' + json.dumps(handles), flush=True)
    maximum_seconds = release.get('maximumDriverSeconds', 900)
    assert type(maximum_seconds) is int and 1 <= maximum_seconds <= 900
    status = driver.wait(timeout=maximum_seconds)
    if status == 0:
        # A result payload may predate a late original product/log failure.
        # Admit a successful driver only with its separate post-session,
        # post-flush terminal receipt; process exit remains authoritative.
        terminal = load(out / 'terminal-acceptance.json')
        assert terminal['accepted'] is True and terminal['sessionRetired'] is True
        assert terminal['diagnosticWritesFlushed'] is True
finally:
    cleanup_errors, stop_results = [], []

    def report_error(operation, error):
        cleanup_errors.append({'operation': operation, 'error': str(error),
                               'traceback': traceback.format_exc()})

    def retain_json(name, value):
        # A failed diagnostic write must not skip another role or suppress the
        # final closure attempt. Original failures remain in the emitted receipt.
        try:
            write(out / name, value)
        except BaseException as error:
            report_error('write-' + name, error)

    active_error = sys.exc_info()[1]
    if active_error is not None:
        status = 1
        retain_json('supervisor-failure.json',
                    {'error': str(active_error), 'traceback': traceback.format_exc()})

    # Cleanup is centralized. Every owned role gets an independent attempt,
    # even if another wait/signal/inventory or log-close operation raises.
    for name, process, log in reversed(owned):
        try:
            result = stop(process)
            stop_results.append({'kind': name, **result})
            if result['errors']:
                cleanup_errors.extend({'kind': name, **item} for item in result['errors'])
        except BaseException as error:
            report_error('stop-' + name, error)
        finally:
            try:
                log.close()
            except BaseException as error:
                report_error('close-log-' + name, error)

    same = False
    try:
        after = inputs(binding)
        retain_json('inputs-after.json', after)
        check_inputs(after, binding)
        same = before is not None and before == after
        assert same
    except BaseException as error:
        report_error('input-guard-after', error)
        retain_json('input-guard-failure.json',
                    {'error': str(error), 'traceback': traceback.format_exc()})

    # Obtain the exit evidence after all stop attempts and resource hashing,
    # immediately before deciding the profile's fate. Missing OS evidence is
    # unknown, never an empty list; preserve the profile and fail in that case.
    inventory_raw, owned_rows, inventory_known = None, [], False
    try:
        inventory_raw, owned_rows = owned_inventory(owned)
        inventory_known = True
    except BaseException as error:
        report_error('final-owned-pid-pgid-inventory', error)
        owned_rows = [{'kind': name, 'pid': process.pid, 'pgid': process.pid,
                       'exitCode': process.returncode, 'remainingOwnedPid': None,
                       'remainingGroupMembers': None} for name, process, _ in owned]
    all_groups_empty = inventory_known and all(row['remainingGroupMembers'] == [] for row in owned_rows)
    all_pids_groups_empty = all_groups_empty and all(row['remainingOwnedPid'] == [] for row in owned_rows)

    profile_cleanup = {'path': str(profile) if profile is not None else None,
                       'removed': False, 'retained': profile is not None,
                       'ownedPidPgidExitProven': all_pids_groups_empty,
                       'escapedProcessReview': 'Root independent review is still required; no foreign group is signalled.'}
    if profile is None:
        profile_cleanup['reason'] = 'profile-not-created'
    elif all_pids_groups_empty:
        try:
            # This is the only profile deletion site. Successful SIGKILL/wait
            # alone cannot reach it; an actual empty owned-PID/PGID snapshot can.
            shutil.rmtree(profile)
            profile_cleanup.update(removed=True, retained=False, reason='removed-after-os-exit-proof')
        except BaseException as error:
            report_error('remove-proven-exited-profile', error)
            profile_cleanup['reason'] = 'removal-failed-after-os-exit-proof'
    else:
        profile_cleanup['reason'] = 'retained-owned-process-live-or-exit-unproven'

    if inventory_raw is not None:
        try:
            (out / 'processes-after.txt').write_text(inventory_raw)
        except BaseException as error:
            report_error('write-processes-after', error)
    if not same or not all_pids_groups_empty or cleanup_errors:
        status = 1
    closure = {'owned': owned_rows, 'stopAttempts': stop_results,
               'osInventoryKnown': inventory_known, 'allOwnedGroupsEmpty': all_groups_empty,
               'allOwnedPidsAndGroupsEmpty': all_pids_groups_empty,
               'inputsUnchanged': same,
               'driverExitCode': next((process.returncode for name, process, _ in owned if name == 'driver'), None),
               'supervisorExitCode': status, 'cleanupErrors': cleanup_errors,
               'profileCleanup': profile_cleanup,
               'recorderStarted': False, 'xvfbStarted': False, 'imageReviewStarted': False,
               'requiresIndependentClosureAfterSupervisorExit': True, 'supervisorPid': os.getpid()}
    # Try both final receipts independently. If either write fails the other
    # and stdout still carry the real cleanup errors; no role is skipped.
    handles['state'] = 'closed' if all_pids_groups_empty else 'cleanup-incomplete'
    handles['profileCleanup'] = profile_cleanup
    retain_json('handles.json', handles)
    if cleanup_errors:
        status = 1
        closure['supervisorExitCode'] = status
    retain_json('process-exit.json', closure)
    if cleanup_errors:
        status = 1
        closure['supervisorExitCode'] = status
    try:
        print('CLOSURE ' + json.dumps(closure), flush=True)
    except BaseException as error:
        status = 1
sys.exit(status)
