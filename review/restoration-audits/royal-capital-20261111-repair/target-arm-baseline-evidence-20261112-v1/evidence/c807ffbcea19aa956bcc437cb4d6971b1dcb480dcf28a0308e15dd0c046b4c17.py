"""Audit captured ARM production compilation without starting its application.

The 45 character changes are derived from actual committed native bytes since
the migrated baseline, not from a count assertion. Match their current native
identities/text/commands and outgoing branch transitions to the captured normal
program using the canonical compiler's explicit source semantics. This is data
compilation/readback evidence, never body/face, browser or continuous playback.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import json.decoder
import json.scanner
from pathlib import Path
import subprocess
import os

ROOT=Path('/home/rikka/Projects/stella')
R=ROOT/'data/native_recovery/royal-capital-20261110/repair-20261111'
OUT=Path(__file__).parent
BASELINE=R/'target-arm-baseline-20261112-v1'
ADAPTER=R/'target-arm-adapter-20261112-v2'
DATA=ROOT/'story_crowd_data'
SITE=ROOT/'artifacts/stella-site-repair-source/.sites-checkout'
DATA_HEAD='aefa1f4aa9bd353a4f39f41d051b3a84d2850a44'
SITE_HEAD='37232806a8180375a4b7a178e27157bb16d12201'
MIGRATED='c33057d059da46e35fad96a7f31a9665c23b5fa0'
PROGRAM_SHA='2dc7724b27cdeebfd7421d47403e72cae0281328631ecf5b9a49900f1b7257a2'
decoder=json.JSONDecoder();decoder.parse_string=json.decoder.py_scanstring
decoder.scan_once=json.scanner.py_make_scanner(decoder)


def require(condition,message):
    if not condition:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return decoder.decode(Path(path).read_bytes().decode('utf-8'))
def ref(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def git(repository,*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(repository),*args])
def write(name,value):
    path=OUT/name
    with path.open('x')as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return ref(path)
def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


require(os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[0,1],'Audit CPU limits differ')
require(git(DATA,'rev-parse','HEAD').decode().strip()==DATA_HEAD and not git(DATA,'status','--porcelain').strip(),'Formal data HEAD/status differs')
require(git(SITE,'rev-parse','HEAD').decode().strip()==SITE_HEAD and not git(SITE,'status','--porcelain').strip(),'Canonical Site HEAD/status differs')
release=read(BASELINE/'root-release.json');preparation=read(BASELINE/'preparation.json')
require(ref(BASELINE/'root-release.json')==preparation['release'],'Baseline release bytes differ')
require(release['dataHead']==DATA_HEAD and release['canonicalHead']==SITE_HEAD and release['rootConfirmed'] and
        release['adapterLaunchAuthorized'] and release['compilerExecutionAuthorized'] and
        not release['browserExecutionAuthorized'] and not release['formalWritesAllowed'],'Release scope differs')
require(release['allowedRequests']==[dict(sceneId=10450054,scenarioId=4,nativePreview='')],'Baseline request scope differs')
guards=release['guardFiles'];require(len(guards)==836 and len({record['path']for record in guards})==836,'Guard allocation differs')
for record in guards:
    path=Path(record['path'])
    require(path.stat().st_size==record['bytes'] and file_sha(path)==record['sha256'],'Guard changed: '+str(path))
guard_report=write('guard-after-readback.json',dict(status='all_frozen_before_records_equal_current_after_bytes',
    release=ref(BASELINE/'root-release.json'),files=836,guardPaths=[record['path']for record in guards],
    beforeEvidence='Root release records; guarded adapter source verifies before and after successful compilation.',
    afterEvidence='Independent current byte/length/SHA256 reread after owned server termination.',
    browserStarted=False,formalWrites=False))
tracked=git(SITE,'ls-files','-z').split(b'\0');tracked=[item.decode()for item in tracked if item]
require(len(tracked)==289,'Canonical tracked file count differs')
for name in tracked:
    require((SITE/name).read_bytes()==git(SITE,'show',SITE_HEAD+':'+name),'Canonical tracked Git blob differs: '+name)

health_raw=(BASELINE/'health.bin').read_bytes();health=decoder.decode(health_raw.decode('utf-8'))
require(health==read(BASELINE/'health.json') and health['pid']==2379 and health['siteRoot']==str(SITE) and
        health['nice']==19 and health['affinity']==[0,1] and health['readOnly'] and not health['browserStartedByAdapter'],'Actual health differs')
registry=Path(health['registryPath']);registry_raw=registry.read_bytes()
require(registry_raw==b'[]\n' and sha(registry_raw)==health['registrySha256']==release['registryBinding']['sha256'],'Fresh empty registry differs')
require(health['registryScopeCount']==0 and release['registryScopeCount']==0 and release['noPrivateOverrides'],'Private scope unexpectedly enabled')
for path_key,sha_key in [('nodeExecutable','nodeExecutableSha256'),('compilerLoader','compilerLoaderSha256'),
                         ('compilerPath','compilerSha256'),('adapterEntry','adapterEntrySha256')]:
    require(file_sha(health[path_key])==health[sha_key],'Actual health program identity differs: '+path_key)
require(health['releaseSha256']==ref(BASELINE/'root-release.json')['sha256'] and
        health['toolchainReceiptSha256']==release['toolchainReceiptBinding']['sha256'],'Actual release/toolchain binding differs')

runs=list((ADAPTER/'compiler-runs').glob('*/receipt.json'));require(len(runs)==1,'Baseline compiler run allocation differs')
run_path=runs[0];run=read(run_path);stdout_path=run_path.parent/'stdout.bin';stderr_path=run_path.parent/'stderr.bin'
program_raw=(BASELINE/'program.bin').read_bytes()
require(program_raw==stdout_path.read_bytes() and len(program_raw)==7439170 and sha(program_raw)==PROGRAM_SHA==run['stdoutSha256'],'Actual compiler stdout/HTTP body differs')
require(stderr_path.read_bytes()==b'' and run['stderrSha256']==sha(b'') and run['exitCode']==0 and not run['timedOut'] and run['interruptedBy'] is None,'Actual compile did not finish cleanly')
require(run['pid']==3049 and run['processGroup']==3049 and run['affinity']==[0,1] and run['nice']==19 and not run['formalWrites'] and not run['browserStarted'],'Compiler lifecycle limits differ')
require(run['cwd']==str(SITE) and run['command']==[
    '/usr/bin/node','--import',health['compilerLoader'],health['compilerPath'],str(ROOT),'10450054','4','',
    str(SITE),str(registry),sha(registry_raw)],'Actual command is not the canonical normal baseline')
request=read(BASELINE/'program-request.json')
require(request['status']==200 and request['url']=='http://127.0.0.1:5190/program?scene=10450054&node=4' and
        request['bytes']==len(program_raw) and request['sha256']==PROGRAM_SHA and
        request['headers']['content-length']==str(len(program_raw)) and request['headers']['cache-control']=='no-store' and
        request['headers']['content-type']=='application/json' and 'content-encoding'not in request['headers'],'HTTP evidence differs')
program=decoder.decode(program_raw.decode('utf-8'));nodes={node['id']:node for node in program['nodes']}
require(program['start']=='10450054:4' and len(nodes)==5599 and len(program['edges'])==5845 and
        'review_only_overrides'not in program,'Actual normal program scope differs')
require(program['before']['model']==program['before']['body']==program['before']['face']=='','Direct preview state unexpectedly reconstructed incoming acting')

manifest=read(DATA/'manifest.json');entries={entry['id']:entry for entry in manifest['scenes']}
documents={entry['id']:read(DATA/entry['path'])for entry in manifest['scenes']}
changed_paths=git(DATA,'diff','--name-only',MIGRATED,DATA_HEAD,'--','native/scenes').decode().splitlines()
require(set(changed_paths)=={'native/scenes/10040052.json','native/scenes/10040053.json','native/scenes/10450054.json'},'Changed native scene scope differs')
targets=[];edge_checks=[];counts=Counter()
for name in changed_paths:
    old=decoder.decode(git(DATA,'show',MIGRATED+':'+name).decode('utf-8'));current=read(DATA/name)
    scene=int(Path(name).stem);review=read(DATA/entries[scene]['reviewPath'])
    require(len(old['scenario_list'])==len(current['scenario_list']),'Native rows added or removed')
    require({key:value for key,value in old.items()if key!='scenario_list'}=={key:value for key,value in current.items()if key!='scenario_list'},'Non-row native data changed')
    for before,row in zip(old['scenario_list'],current['scenario_list']):
        if before==row:continue
        require(before['character']=='' and row['character'] and
                {key:value for key,value in before.items()if key!='character'}=={key:value for key,value in row.items()if key!='character'},'Change exceeds a sparse character field')
        number=row['scenario_id'];identifier=f'{scene}:{number}';actual=nodes[identifier];r=review['scenarios'][str(number)]
        expected_model=row['character'].removeprefix('live2d/AC_')
        display=lambda text:''if text=='未設定'else text
        require(actual['model']==expected_model and actual['scenario_id']==number and actual['scene_id']==f'scene:{scene}' and
                actual['speaker']==display(row['msg_character']) and actual['text']==display(r.get('sourceText')or row['msg_text']) and
                actual['translation']==display(row['msg_text']) and actual['command']==row['command'],'Actual compiled node identity/source/command differs: '+identifier)
        for field in ['bg_picture','bg_music','character_image']:
            require(actual[field]==row[field],'Raw sparse field differs: '+identifier+':'+field)
        counts[expected_model]+=1
        targets.append(dict(id=identifier,sceneId=scene,scenarioId=number,stableKey=r['stableKey'],expectedModel=expected_model,actualModel=actual['model'],sourceTextAndChineseAndCommandsEqual=True))
        actual_edges=[edge for edge in program['edges']if edge['source']==identifier]
        require(len(actual_edges)==len(row['branch_list']),'Compiled outgoing branch count differs')
        for branch in row['branch_list']:
            matches=[edge for edge in actual_edges if edge['id']==f'{identifier}:{branch["branch_id"]}'];require(len(matches)==1,'Native branch edge not unique')
            edge=matches[0];transition=branch['transition_list'][0]if len(branch['transition_list'])==1 else None
            finish=bool(transition and transition.get('next_scenario_label')=='FINISH')
            destination_scene=(transition.get('next_scene_id')or 0)if finish else scene
            destination=documents.get(destination_scene);destination_id=transition.get('next_scenario_id')if transition else None
            if destination_id==0:
                destination_id=next((item['scenario_id']for item in destination['scenario_list']if item['is_root']==1),None)if destination else None
            target=f'{destination_scene}:{destination_id}'if destination_id is not None else ''
            flow=('scene'if transition.get('next_section_id')==entries[scene]['sectionId']else'section')if finish else'continue'
            available=bool(transition and(flow=='section'or target in nodes))
            require(edge['native_transition']==transition and edge['target']==target and edge['flow_action']==flow and
                    edge['available']==available and edge['kind']==('choice'if branch['type']in[2,3]else'next')and
                    edge['side']==('left'if branch['type']==2 else'right'if branch['type']==3 else''),'Actual native connection semantics differ: '+edge['id'])
            edge_checks.append(dict(id=edge['id'],target=target,available=available,nativeTransitionEqual=True,flowAction=flow))
require(len(targets)==45 and counts==Counter(rom01=23,felt01=22),'Known installed character delta count differs')
target_ref=write('affected-native-bindings.json',dict(targets=targets,outgoingEdges=edge_checks))
target_list=OUT/'node-targets.json';target_list.write_text(json.dumps(targets,ensure_ascii=False)+'\n')
node_output=OUT/'node-readback.json'
node_process=subprocess.run(['/usr/bin/node',str(OUT/'node_readback.mjs'),str(BASELINE/'program.bin'),str(stdout_path),str(target_list),str(node_output)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
require(node_process.returncode==0,'Captured JSON Node audit failed: '+node_process.stderr.decode(errors='replace'))
node=read(node_output);require(node['programSha256']==PROGRAM_SHA and len(node['checkedCharacterBindings'])==45 and len(node['p30CharacterBindings'])==16,'Independent ARM Node parsed result differs')

log=(BASELINE/'server.log').read_text();require('ARM_COMPILER_STARTED'in log and 'ARM_COMPILER_FINISHED'in log and 'ARM_ADAPTER_SIGNAL'in log,'Actual lifecycle logs missing')
stop=read(BASELINE/'stop-request.json');require(stop['pid']==2379 and stop['signal']=='SIGTERM'and stop['ownedCommandVerified'],'Owned stop request differs')
processes=dict(adapterPid2379Present=Path('/proc/2379').exists(),compilerPid3049Present=Path('/proc/3049').exists())
require(not any(processes.values()),'Owned historical process PID still present; inspect instead of inferring closure')
require(git(DATA,'rev-parse','HEAD').decode().strip()==DATA_HEAD and not git(DATA,'status','--porcelain').strip(),'Formal data changed during readback')
receipt=write('receipt.json',dict(schema='stella.actual_ARM_baseline_independent_readback.v1',
    status='passed_captured_actual_compilation_and_current_guard_readback',reviewer='/root/p30_packet_preflight',
    createdUtc=datetime.now(timezone.utc).isoformat(),dataHead=DATA_HEAD,canonicalHead=SITE_HEAD,
    program=ref(BASELINE/'program.bin'),actualCompileReceipt=ref(run_path),actualStdout=ref(stdout_path),actualStderr=ref(stderr_path),
    actualHTTPHeaders=ref(BASELINE/'program-request.json'),actualHealth=ref(BASELINE/'health.bin'),
    actualCompilerExitCode=0,actualCompilerElapsedSeconds=run['elapsedSeconds'],actualCompilerChildPid=3049,adapterPid=2379,
    actualCompilerStdoutEqualsHTTPBody=True,emptyFreshRegistry=ref(registry),privateOverridePresent=False,
    originalFrozenGuardFiles=836,independentAfterGuardCheck=guard_report,canonicalTrackedGitBlobsRechecked=289,
    knownSparseCharacterChanges=45,changedByModel=dict(counts),affectedNativeBindings=target_ref,
    outgoingNativeEdgesChecked=len(edge_checks),compiledP30CharacterBindings=16,
    independentARMNodeReadback=ref(node_output),nodeReadbackExitCode=node_process.returncode,
    canonicalCompilerSource=ref(SITE/'lib/preview.ts'),actualWrapperSource=ref(ADAPTER/'compile.mjs'),
    guardLifecycleSource=ref(ADAPTER/'adapter_config.py'),adapterRequestSource=ref(ADAPTER/'serve.py'),
    stopRequest=ref(BASELINE/'stop-request.json'),actualSignalLog=ref(BASELINE/'server.log'),ownedProcessAfterCheck=processes,
    directPreviewWarning=program['warnings'],beforeStateMeaning='Explicit-node preview starts with empty route state; previous music/body/commands are not reconstructed.',
    newApplicationOrCompilerExecutionsByReviewer=0,newNetworkRequestsByReviewer=0,browserStarted=False,
    formalDataSourceOrGitWrites=False,newRestorationVisits=0,continuousPlaybackAccepted=False,
    motionFaceGeometryTimingOrChapterAccepted=False,fullRestorationAccepted=False,nice=19,cpuAffinity=[0,1]))
print(json.dumps(dict(receipt=receipt,guards=836,canonicalBlobs=289,knownNativeCharacterChanges=45,outgoingEdgesChecked=len(edge_checks),p30ModelBindings=16,additionalApplicationExecutions=0)))
