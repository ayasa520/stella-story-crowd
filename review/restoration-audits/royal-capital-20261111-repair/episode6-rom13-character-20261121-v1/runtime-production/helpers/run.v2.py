"""One future root-released saved Worker/ARM Firefox session.

This v2 supervisor binds its own v2 file and the natural-text v2 driver. The
original prepared program and original helpers remain immutable evidence.

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
            'sourceHead': git(source, 'rev-parse', 'HEAD'), 'sourceStatus': git(source, 'status', '--short'),
            'sourceFiles': {p: sha(source / p) for p in binding['source']['sourceFiles']},
            'distFiles': {p: sha(source / 'dist' / p) for p in binding['source']['distFiles']}}

def check_inputs(actual, binding):
    for key in ['dataHead', 'dataStatus', 'dataInputs', 'protectedFirstThree', 'resourceAndSourceGuards']:
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
    if members(process.pid):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
    # Firefox descendants may outlive the launcher. Treat its entire owned
    # group as live until the OS inventory proves that the group is empty.
    if members(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        end = time.monotonic() + 5
        while members(process.pid) and time.monotonic() < end:
            time.sleep(.1)

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
assert release['publishedRomHead'] == binding['dataHead'] == binding['revision']
assert release['sourceHead'] == binding['source']['head']
assert release['inputBindingSha256'] == sha(HERE / 'input-binding.json')
assert release['planSha256'] == sha(HERE / 'capture-plan.json')
assert release['normalProgramSha256'] == load(HERE / 'normal-prepare-receipt.json')['programSha256']
bindings = release['runtimeBindings']
required = [HERE / name for name in ['run.v2.py', 'play.v2.mjs', 'worktree-upstream.mjs', 'input-binding.json',
             'capture-plan.json', 'normal-prepare-body.json.gz', 'normal-prepare-receipt.json', 'normal-prepare-route-check.json']]
required += [ROOT / name for name in ['artifacts/stella-local-deployment-3394828/serve-local.mjs',
  'artifacts/stella-local-deployment-3394828/workers-local.mjs', 'artifacts/stella-local-deployment-3394828/d1-local.mjs',
  'artifacts/stella-p30-firefox-20261120/bidi.mjs', 'artifacts/stella-p30-firefox-20261120/render-probe.mjs']]
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
    with tempfile.TemporaryDirectory(prefix='stella-episode6-rom13-') as folder:
        profile = Path(folder)
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
        try:
            while time.monotonic() < end and browser.poll() is None:
                found = re.search(r'WebDriver BiDi listening on (ws://127.0.0.1:\d+)', (out / 'firefox.log').read_text())
                if found:
                    address = found[1]
                    break
                time.sleep(.1)
            if not address:
                raise RuntimeError('Firefox did not announce BiDi; inspect actual firefox.log')
            driver_log = (out / 'driver.log').open('wb')
            driver = subprocess.Popen(['node', str(HERE / 'play.v2.mjs'), address], env=env,
              stdout=driver_log, stderr=subprocess.STDOUT, start_new_session=True)
            owned.append(('driver', driver, driver_log))
            handles['driver'] = {'pid': driver.pid, 'pgid': driver.pid, 'bidi': address}
            handles['state'] = 'capturing'
            write(out / 'handles.json', handles)
            print('HANDLES ' + json.dumps(handles), flush=True)
            try:
                status = driver.wait(timeout=420)
            finally:
                stop(driver)
        finally:
            stop(browser)  # Always before TemporaryDirectory removes the profile.
finally:
    if sys.exc_info()[1]:
        write(out / 'supervisor-failure.json', {'error': str(sys.exc_info()[1]), 'traceback': traceback.format_exc()})
    for name, process, log in reversed(owned):
        stop(process)
        log.close()
    same = False
    try:
        after = inputs(binding)
        write(out / 'inputs-after.json', after)
        check_inputs(after, binding)
        same = before == after
        assert same
    except Exception as error:
        write(out / 'input-guard-failure.json', {'error': str(error), 'traceback': traceback.format_exc()})
        status = 1
    closure = {'owned': [{'kind': name, 'pid': process.pid, 'pgid': process.pid, 'exitCode': process.returncode,
               'remainingGroupMembers': members(process.pid)} for name, process, _ in owned],
               'allOwnedGroupsEmpty': all(not members(p.pid) for _, p, _ in owned),
               'inputsUnchanged': same, 'driverExitCode': status, 'recorderStarted': False, 'xvfbStarted': False,
               'imageReviewStarted': False, 'requiresIndependentClosureAfterSupervisorExit': True, 'supervisorPid': os.getpid()}
    if not closure['allOwnedGroupsEmpty']:
        status = 1
    (out / 'processes-after.txt').write_text(processes())
    write(out / 'process-exit.json', closure)
    handles['state'] = 'closed'
    write(out / 'handles.json', handles)
    print('CLOSURE ' + json.dumps(closure), flush=True)
sys.exit(status)
