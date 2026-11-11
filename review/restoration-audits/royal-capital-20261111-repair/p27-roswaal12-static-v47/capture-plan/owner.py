"""Own one separately approved browser, close it, then index saved pixels.

This is an offline-prepared owner, not an approval. Execution requires an
explicit root release, exact frozen-input hash and --execute-approved-once.
Preflight completes before open. One CLI call owns the ordered case prefix;
the capture stops on failure and never retries. This wrapper never registers
previews, starts/restarts an adapter, changes native data or edits a website.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
from urllib.request import urlopen

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
ROOT = R.parents[3]
DATA = ROOT / 'story_crowd_data'
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'


def read(path): return json.loads(Path(path).read_text())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def rec(path):
    path = Path(path); raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': sha(raw)}
def write(path, value):
    with path.open('x') as stream: json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
def git(*args): return subprocess.check_output(['git', '-C', str(SITE), *args], text=True).strip()


def processes():
    result = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            executable = str((path / 'exe').readlink())
            command = (path / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            chrome = '/chrome-canary/' in executable
            cli = 'node' in Path(executable).name and 'playwright' in command and 'run-server' in command
            if chrome or cli:
                pid = int(path.name)
                parent = int((path/'stat').read_text().rsplit(')',1)[1].split()[1])
                result.append({'pid': pid, 'ppid':parent, 'exe': executable, 'argv': command, 'kind': 'chrome' if chrome else 'cli',
                    'nice': os.getpriority(os.PRIO_PROCESS, pid), 'cpus': sorted(os.sched_getaffinity(pid))})
        except (OSError, ProcessLookupError): pass
    return result


def verify_guards(records):
    for row in records:
        path = (ROOT / row['path']).resolve()
        assert path.is_relative_to(ROOT) and rec(path) == row, ('Guard changed', row['path'])


def fetch(base, route):
    with urlopen(base + route, timeout=40) as response:
        assert response.status == 200, route
        raw = response.read()
    return raw


def resource_checks(base):
    catalog = read(DATA / 'assets/catalog.json'); records = []
    assert len(catalog['models']) == 41
    for model in ['roswaal01', 'subaru_butler01']:
        row = catalog['models']['live2d/AC_' + model]
        members = [(row['member'], 'model-json')]
        document = read(DATA / 'assets' / row['model_url'])
        parent = Path(row['member']).parent
        refs = document['FileReferences']
        members += [(str(parent / refs['Moc']), 'MOC')]
        members += [(str(parent / name), 'texture') for name in refs['Textures']]
        for member, role in members:
            local = DATA / 'assets' / catalog['asset_members'][member]
            route = '/asset/' + quote(member, safe='/')
            raw = fetch(base, route)
            assert raw == local.read_bytes(), ('Served original model payload changed', route)
            records.append({'model': model, 'role': role, 'url': base + route, 'local': rec(local),
                'servedBytes': len(raw), 'servedSha256': sha(raw)})
        route = '/api/model/' + model; local = DATA / 'assets' / row['detail_url']; raw = fetch(base, route)
        assert raw == local.read_bytes()
        records.append({'model': model, 'role': 'detail', 'url': base + route, 'local': rec(local),
            'servedBytes': len(raw), 'servedSha256': sha(raw)})
    return records


def compiled_cases(base, cases, scopes):
    baselines = {}; result = []
    for spec in cases:
        scene, start = spec['scene'], spec['route'][0]
        route = '/program?scene=' + str(scene) + '&node=' + str(start)
        if scene not in baselines: baselines[scene] = json.loads(fetch(base, route))
        baseline = baselines[scene]
        raw = fetch(base, route + '&nativePreview=' + quote(spec['id']))
        candidate = json.loads(raw)
        assert candidate['edges'] == baseline['edges']
        assert {k:v for k,v in candidate.items() if k not in ['nodes','review_only_overrides']} == {
            k:v for k,v in baseline.items() if k not in ['nodes','review_only_overrides']}
        assert len(candidate['nodes']) == len(baseline['nodes'])
        target = str(scene) + ':' + str(spec['target']); differences = []
        for current, old in zip(candidate['nodes'], baseline['nodes']):
            assert current['id'] == old['id']
            if current != old:
                assert current['id'] == target
                changed = {key for key in set(current)|set(old) if current.get(key) != old.get(key)}
                allowed = {'model'} if len(spec['fields']) == 1 else {'model','body','face'}
                assert changed <= allowed, ('Unexpected compiled consequence', sorted(changed))
                differences.append({'node': target, 'changedKeys': sorted(changed)})
        assert len(differences) == 1
        actual = next(row for row in candidate['nodes'] if row['id'] == target)
        assert actual['model'] == spec['model']
        if 'motion' in spec['fields']:
            body, face = spec['fields']['motion'].split(','); assert actual['body'] == body and actual['face'] == face
        scope = next(row for row in scopes if spec['id'] in row['exampleIds'])
        override = candidate['review_only_overrides']
        assert override['exampleId'] == spec['id'] and override['packetSha256'] == scope['sha256'] and override['persisted'] is False
        result.append({**spec, 'programSha256': sha(raw), 'packetSha256': scope['sha256'],
            'compiledScope': [row for row in candidate['nodes'] if row['id'] in [str(scene)+':'+str(n) for n in spec['route']]],
            'compiledNodeCount': len(candidate['nodes']), 'compiledEdgeCount': len(candidate['edges']), 'differences': differences})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--execute-approved-once', action='store_true')
    args = parser.parse_args()
    assert args.execute_approved_once, 'No browser authorization: an explicit execution flag is required'
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19 and sorted(os.sched_getaffinity(0)) == [22,23]
    assert args.release.resolve().is_relative_to(ROOT), 'Keep the explicit release inside this workspace'
    release = read(args.release)
    assert release['scopeApprovedByRoot'] is True and release['singleBrowserOwnerAssignedByRoot'] is True
    assert release['browserOwner'] == '/root/p24_background_final_qa'
    frozen = (ROOT / release['frozenExecutionInput']['path']).resolve()
    assert frozen.is_relative_to(HERE) and rec(frozen) == release['frozenExecutionInput']
    inputs = read(frozen); assert inputs['freezeComplete'] and inputs['maxCases'] == 3
    ids = release['selectedCaseIds']; assert 1 <= len(ids) <= 3
    assert ids == [row['id'] for row in inputs['cases'][:len(ids)]], 'Only the ordered approved prefix is allowed'
    cases = inputs['cases'][:len(ids)]
    base = release['baseURL']; assert re.fullmatch(r'http://127\.0\.0\.1:\d+', base)
    session = release['session']; assert re.fullmatch(r'assembled-three-[a-z0-9-]+', session)
    output = (HERE / release['freshOutputDirectory']).resolve()
    assert output.is_relative_to(HERE) and not output.exists(); output.mkdir()
    lifecycle = {'session': session, 'ownerPid':os.getpid(), 'browserOpened': False, 'commands': [], 'failure': None,
        'before': processes(), 'release': rec(args.release.resolve()), 'frozenInput': rec(frozen)}
    opened = False; before_registry = None; guard_after = False
    def call(arguments, label, timeout):
        command = ['playwright-cli', '-s='+session, *arguments]
        try:
            result = subprocess.run(command, cwd=SITE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=timeout)
            raw = result.stdout.encode(); code = result.returncode
        except subprocess.TimeoutExpired as error:
            raw = (error.stdout or b''); raw = raw.encode() if isinstance(raw,str) else raw; code = None
        path = output / (label+'.txt')
        with path.open('xb') as stream: stream.write(raw)
        record = {'argv': command, 'exitCode': code, 'log': rec(path)}
        lifecycle['commands'].append(record)
        print(json.dumps({'step': label, 'exitCode': code, 'log': str(path)}), flush=True)
        assert code == 0, ('CLI command failed or timed out', label, code)
        return raw.decode(errors='replace')
    try:
        assert not lifecycle['before'], 'Another browser or CLI daemon is already owned elsewhere'
        verify_guards(inputs['guardReceipts'])
        assert git('rev-parse','HEAD') == inputs['sourceCommit']
        subprocess.run(['git','-C',str(SITE),'diff','--quiet','HEAD','--'],check=True)
        helper_spec = importlib.util.spec_from_file_location('assembled_deep_guards', HERE/'prepare_guards.py')
        helper = importlib.util.module_from_spec(helper_spec); helper_spec.loader.exec_module(helper)
        for row in read(HERE/'target-deep-guards.json'): helper.verify_rows(row)
        registry = R/'playback/approved-memory-previews.json'; before_registry = rec(registry)
        actual_scopes = read(registry)
        for scope in inputs['requiredScopes']: assert scope in actual_scopes, 'Root has not registered these exact frozen packet bytes'
        health = json.loads(fetch(base,'/health'))
        assert health['kind']=='stella-readonly-production-adapter' and health['root']==str(ROOT) and health['siteRoot']==str(SITE)
        assert health['pid'] == release['adapterPid']
        server = Path('/proc')/str(health['pid']); command=(server/'cmdline').read_bytes().replace(b'\0',b' ').decode()
        assert str(R/'playback/serve.py') in command and str(SITE) in command
        assert os.getpriority(os.PRIO_PROCESS,health['pid'])==19 and set(os.sched_getaffinity(health['pid'])) <= {22,23}
        served = resource_checks(base)
        actual_cases = compiled_cases(base,cases,inputs['requiredScopes'])
        verify_guards(inputs['guardReceipts'])
        write(output/'preflight.json',{'status':'complete_before_browser_open','health':health,'serverCommand':command,
            'guardedFiles':inputs['guardReceipts'],'registry':before_registry,'cases':actual_cases,'servedOriginalResources':served,
            'fixture':{'parent':[1280,1000],'iframeOuter':[480,856],'viewport':'measured actual CSS9:16; not asserted856px'}})
        config = {'scopeApproved':True,'singleBrowserOwnerAssigned':True,'freezeComplete':True,'baseURL':base,
            'outputRoot':str(output),'cases':actual_cases,'servedResources':served,'instrumentationSource':(HERE/'instrument.js').read_text()}
        runner_text = (HERE/'capture_cases.js').read_text()
        assert runner_text.count('__APPROVED_EXECUTION__')==1
        runner = output/'approved-runner.js'
        with runner.open('x') as stream: stream.write(runner_text.replace('__APPROVED_EXECUTION__',json.dumps(config,ensure_ascii=False)))
        subprocess.run(['node','--check',str(runner)],check=True)
        lifecycle['beforeCliZero']='(no browsers)' in call(['list'],'cli-before',30)
        assert lifecycle['beforeCliZero']
        lifecycle['immediatelyBeforeOpen']=processes()
        assert not lifecycle['immediatelyBeforeOpen'], 'Another browser/daemon appeared during preflight'
        opened=True
        call(['open','about:blank','--config='+str(R/'playback/canary.json')],'open',60)
        lifecycle['browserOpened']=True; lifecycle['live']=processes()
        assert any(row['kind']=='chrome' for row in lifecycle['live'])
        assert all(row['nice']==19 and set(row['cpus'])<={22,23} for row in lifecycle['live'])
        summary=json.loads(call(['--raw','run-code','--filename='+str(runner)],'capture',270))
        write(output/'capture-summary.json',summary)
        if summary['stoppedOnFirstFailure'] or any(row['failure'] for row in summary['cases']):
            raise RuntimeError('Capture stopped with preserved partial evidence; no remaining case or retry is authorized')
    except Exception as error:
        lifecycle['failure']={'type':type(error).__name__,'message':str(error)}
    finally:
        if opened:
            try: call(['close'],'close',60)
            except Exception as error: lifecycle['closeFailure']=str(error)
        lifecycle['after']=processes()
        lifecycle['osZero']=not lifecycle['after']
        if opened:
            try: lifecycle['cliZero']='(no browsers)' in call(['list'],'cli-after',30)
            except Exception as error: lifecycle['cliZero']=False;lifecycle['listFailure']=str(error)
        else: lifecycle['cliZero']=lifecycle.get('beforeCliZero')
        # Browser closure is the first post-capture action. Only now hash files
        # again or decode stored base64 images; neither image review nor slow
        # evidence work may leave the browser idling in the background.
        try:
            verify_guards(inputs['guardReceipts'])
            if before_registry: assert rec(R/'playback/approved-memory-previews.json')==before_registry
            assert rec(args.release.resolve())==lifecycle['release']
            assert git('rev-parse','HEAD')==inputs['sourceCommit']
            subprocess.run(['git','-C',str(SITE),'diff','--quiet','HEAD','--'],check=True)
            guard_after=True
        except Exception as error: lifecycle['afterGuardFailure']=str(error)
        lifecycle['guardedBytesUnchangedAfter']=guard_after
        write(output/'browser-lifecycle.json',lifecycle)
    if opened and lifecycle['osZero'] and lifecycle['cliZero']:
        subprocess.run([sys.executable,str(HERE/'index_pixels.py'),'--output',str(output)],check=True)
    print(json.dumps({'lifecycle':rec(output/'browser-lifecycle.json'),'failure':lifecycle['failure'],
        'osZero':lifecycle['osZero'],'cliZero':lifecycle['cliZero'],'guardedBytesUnchangedAfter':guard_after,
        'visualAccepted':False,'automaticRetry':False}),flush=True)
    if lifecycle['failure'] or not guard_after or not lifecycle['osZero'] or not lifecycle['cliZero']: sys.exit(1)


if __name__=='__main__': main()
