"""Independently inspect the finalized ARM adapter without importing it.

Syntax checks parse source only. Complete author/provenance inventories, the
unchanged guarded override body and prepared host payload identities are read
as immutable evidence. This audit does not execute the compiler, adapter,
verified UTF-8 helper, browser, installer or registry workflow.
"""

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT=Path('/home/rikka/Projects/stella')
R=ROOT/'data/native_recovery/royal-capital-20261110/repair-20261111'
KIT=R/'target-arm-adapter-20261112-v2'
OLD=R/'target-arm-adapter-20261112-v1'
TOOLS=R/'target-arm-tools-20261112-v1'
SITE=ROOT/'artifacts/stella-site-repair-source/.sites-checkout'
OUT=Path(__file__).parent
checked={}


def sha(path):
    path=Path(path).resolve()
    if str(path) not in checked:
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                digest.update(chunk)
        checked[str(path)]=digest.hexdigest()
    return checked[str(path)]


def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8',errors='strict'))


def record(path):
    path=Path(path).resolve()
    return dict(file=str(path),bytes=path.stat().st_size,sha256=sha(path))


def verify(spec):
    path=Path(spec['file'])
    assert sha(path)==spec['sha256'] and ('bytes' not in spec or path.stat().st_size==spec['bytes']), str(path)


def fragment(path):
    text=path.read_text()
    start=text.index('  const scope=scopes.find')
    return text[start:text.index('\n}',start)].encode()


def literal(tree,name):
    return next(ast.literal_eval(node.value) for node in tree.body
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id==name for target in node.targets))


def git(path,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(path),*args],text=True).strip()


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and set(os.sched_getaffinity(0))=={0,1}
    preparation_path=KIT/'preparation-receipt.json'
    assert sha(preparation_path)=='fe537af8151f2260a5497db84dcce8ee62733fcaa879ad57ec6c967585c63127'
    preparation=read(preparation_path)
    for key in ['inventory','authorReport','sourceProvenance','syntaxOnlyAudit','releasePrerequisitesTemplate',
                'toolchainProvenance','previousAuthorKitReceipt','previousAuthorKitInventory']:
        verify(preparation[key])
    inventory=read(KIT/'inventory.json')
    assert len(inventory['files'])==18
    for spec in inventory['files']:
        verify(spec)
    inventoried={Path(spec['file']).name for spec in inventory['files']}
    assert {path.name for path in KIT.iterdir() if path.is_file()}==inventoried|{'inventory.json','preparation-receipt.json'}
    old_inventory=read(OLD/'inventory.json')
    for spec in old_inventory['files']:
        verify(spec)
    for spec in preparation['historicalInputsUnchanged']:
        verify(spec)
    source=read(KIT/'source-provenance.json')
    for copy in source['files']:
        if copy.get('exactByteCopy'):
            assert Path(copy['source']).read_bytes()==Path(copy['destination']).read_bytes()
    for copy in source['revisionBaseCopies']:
        assert sha(copy['source'])==copy['sourceSha256']
        assert Path(copy['source']).stat().st_size==copy['sourceBytes']
    original_fragment=fragment(R/'playback/compile.mjs')
    assert original_fragment==fragment(OLD/'compile.mjs')==fragment(KIT/'compile.mjs')
    fragment_sha=hashlib.sha256(original_fragment).hexdigest()
    assert len(original_fragment)==3260 and fragment_sha=='643f97a3828200c60a383430346c99f5e21fbb407813fd6725190d7329950a20'
    assert (KIT/'index.html').read_bytes()==(R/'playback/index.html').read_bytes()
    assert (KIT/'target_verified_utf8_v1.py').read_bytes()==(R/'target_verified_utf8_v1.py').read_bytes()
    checks=[]
    trees={}
    for path in sorted(KIT.glob('*.py')):
        trees[path.name]=ast.parse(path.read_text(),filename=str(path))
        checks.append(dict(kind='python_AST_only',source=record(path),passed=True,moduleImported=False))
    node=subprocess.run(['/usr/bin/node','--check',str(KIT/'compile.mjs')],capture_output=True)
    assert node.returncode==0
    checks.append(dict(kind='node_syntax_only',source=record(KIT/'compile.mjs'),exitCode=node.returncode,
        stdout=node.stdout.decode(),stderr=node.stderr.decode(),compilerImported=False))
    closure=literal(trees['adapter_config.py'],'SOURCE_CLOSURE')
    assert len(closure)==13
    closure_records=[record(SITE/name) for name in closure]
    adapter_names=literal(trees['adapter_config.py'],'ADAPTER_FILES')
    assert set(adapter_names)=={'serve.py','adapter_config.py','compile.mjs','index.html','target_verified_utf8_v1.py'}
    template=read(KIT/'release-prerequisites.template.json')
    assert all(template[key] is False for key in ['rootConfirmed','adapterLaunchAuthorized','compilerExecutionAuthorized',
        'browserExecutionAuthorized','registryApproved','formalWritesAllowed'])
    assert template['guardFiles']==[]
    tools_path=TOOLS/'toolchain-receipt.json'
    assert sha(tools_path)=='1348b6ee3de36beac729002e6dc5812f5fc544b93e767e946352e3c283e08753'
    tools=read(tools_path)
    assert tools['toolRoot']==str(TOOLS) and tools['architecture']=='aarch64'
    assert not any(tools[key] for key in ['executionAuthorized','browserExecutionAuthorized','adapterExecutionAuthorized','productionCompileAuthorized'])
    for key in ['localLock','sourceLockPins','lockResolutionAudit','installedPayloadVerification','installedFileManifest']:
        verify(tools[key])
    payloads=read(tools['installedFileManifest']['file'])
    assert payloads['root']==str(TOOLS)
    regular=symlinks=0
    for spec in payloads['files']:
        path=TOOLS/spec['relativePath']
        if 'sha256' in spec:
            assert path.resolve().is_relative_to(TOOLS) and sha(path)==spec['sha256']
            if 'bytes' in spec:
                assert path.stat().st_size==spec['bytes']
            regular+=1
        else:
            assert path.is_symlink() and os.readlink(path)==spec['symlink']
            assert str(path.resolve())==spec['resolvedTarget'] and path.resolve().is_relative_to(TOOLS)
            symlinks+=1
    # The payload receipt counts252 package files checked against tarballs.
    # The complete installed inventory additionally binds npm's generated
    # node_modules/.package-lock.json; its five .bin entries are symlinks.
    assert regular==253 and symlinks==5
    assert any(spec['relativePath']=='node_modules/.package-lock.json' and 'sha256' in spec for spec in payloads['files'])
    binary_records=[]
    for spec in [tools['tools']['node']['executable'],tools['tools']['esbuild']['armExecutable']]:
        verify(spec)
        with Path(spec['file']).open('rb') as stream:
            header=stream.read(64)
        assert header[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',header,18)[0]==183
        binary_records.append(dict(**record(spec['file']),elfMachine=183))
    canonical_lock,local_lock=read(SITE/'package-lock.json'),read(TOOLS/'package-lock.json')
    selected=[]
    for name in ['tsx','esbuild','@esbuild/linux-arm64']:
        before=canonical_lock['packages']['node_modules/'+name]
        after=local_lock['packages']['node_modules/'+name]
        fields=['version','resolved','integrity']
        assert {key:before[key] for key in fields}=={key:after[key] for key in fields}
        selected.append(dict(package=name,**{key:after[key] for key in fields}))
    result=dict(schema='stella.target_arm_adapter_independent_peer.v2',status='static_pass_no_execution_release',
        reviewer='/root/p29_packet_preflight',createdUtc=datetime.now(timezone.utc).isoformat(),
        preparationReceipt=record(preparation_path),authorInventoriedFiles=18,allAuthorFiles=20,
        v1Inventory=record(OLD/'inventory.json'),v1InventoriedFilesUnchanged=len(old_inventory['files']),
        historicalOverrideGuard=dict(bytes=len(original_fragment),sha256=fragment_sha,exactByteEquality=True),
        historicalIndexAndUtf8VerifierExactCopies=True,staticChecks=checks,
        canonicalProductionClosure=closure_records,requiredAdapterFiles=list(adapter_names),
        toolchainReceipt=record(tools_path),installedRegularPayloadsRehashed=regular,toolSymlinksVerified=symlinks,
        armBinaries=binary_records,canonicalLock=record(SITE/'package-lock.json'),actualIsolatedLock=record(TOOLS/'package-lock.json'),
        selectedCompilerLockRows=selected,wholeLockEqualityRequired=False,
        scope='Read-only canonical production compiler adapter, with explicit released registry/guards and no data-write/browser API.',
        blockingFindings=[],releaseTemplateAllAuthorityFalse=True,registryCreated=False,
        observedDataHead=git(ROOT/'story_crowd_data','rev-parse','HEAD'),
        observedDataStatus=git(ROOT/'story_crowd_data','status','--porcelain'),
        observedCanonicalHead=git(SITE,'rev-parse','HEAD'),observedCanonicalStatus=git(SITE,'status','--porcelain'),
        reviewedFiles=[dict(file=path,sha256=digest) for path,digest in sorted(checked.items())],
        runtimeLimits=['Actual canonical TypeScript compilation, loader alias resolution and program/served-byte comparison remain unrun.',
            'Actual request behavior, browser compatibility, UTF8 rejection and interrupted process-group cleanup remain unrun.',
            'Per-request compiler timeout bounds communicate wait; post-kill reap is synchronous and has not been observed.',
            'Packet/source guard body intentionally retains historical JSON.parse behavior; the new strict roundtrip boundary covers formal source JSON and explicit registry.',
            'Static-file identity and renderer acceptance additionally require the later owner freeze/byte/closure/image gates.'],
        compilerExecuted=False,adapterImportedOrStarted=False,browserStarted=False,freezeOrRegistry=False,
        dependencyInstall=False,formalDataSourceGitWrites=False,imagesViewed=False,newRestorationVisits=0,
        actingOrGeometryAccepted=False,wholeRestorationAccepted=False)
    with (OUT/'receipt.json').open('x') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(receipt=record(OUT/'receipt.json'),status=result['status'],authorFiles=20,
        installedPayloads=regular,syntaxChecks=len(checks),blockingFindings=[]),ensure_ascii=False))


if __name__=='__main__':
    main()
