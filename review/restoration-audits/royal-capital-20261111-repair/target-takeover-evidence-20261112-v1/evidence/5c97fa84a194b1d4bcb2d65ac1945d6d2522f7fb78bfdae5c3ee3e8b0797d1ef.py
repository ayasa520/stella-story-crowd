"""Independently compare two accepted P30 derivatives and fresh target guards.

Only rootConfirmed/status and the explicit rootIntegration object may change
from the delegated drafts. Historical whole-library hashes remain historical:
legitimate earlier identity publications do not invalidate untouched target
rows. Current ownership, target rows, complete model rows and resource bytes
are checked separately. This tool writes evidence only, never formal data.
"""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
DATA = ROOT / 'story_crowd_data'
OUT = Path(__file__).parent
BINDER = R / 'target_accept_p30_identity_v1.py'
BASE = 'b59da11b1ae34f1194b76c827bde42aba7abcbc8'
SIX = '698acdd0dcd242aebd481337a3feda0dd62942c8'
SPECS = [
    ('ord15to29','six-character-only-draft.json','8d6071b5c12c130c4e21f5a7849cb202a4f2691b2709bb51036a120368a8e2e4',
     {20:'rom01',21:'felt01',23:'felt01',31:'felt01',32:'rom01',33:'felt01'},range(15,30)),
    ('ord30to44','three-character-only-draft.json','aaf9eb2ebd819b15ca114ecdb76e9ea4194ff8d856ebf947e9271962c8cb8286',
     {41:'felt01',42:'rom01',43:'felt01'},range(30,45)),
]
checked, parsed, parse_errors, historical = {}, {}, [], []


def sha(path):
    path = Path(path).resolve()
    if str(path) not in checked:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                digest.update(chunk)
        checked[str(path)] = digest.hexdigest()
    return checked[str(path)]


def read(path):
    path = Path(path).resolve()
    if str(path) not in parsed:
        raw = path.read_bytes()
        try:
            parsed[str(path)] = json.loads(raw)
        except json.JSONDecodeError as error:
            parse_errors.append(dict(file=str(path),sha256=sha(path),message=str(error),
                position=error.pos,line=error.lineno,column=error.colno,
                codeUnit=ord(error.doc[error.pos]) if error.pos<len(error.doc) else None))
            raise
    return parsed[str(path)]


def record(path):
    path = Path(path).resolve()
    return dict(file=str(path),bytes=path.stat().st_size,sha256=sha(path))


def is_mutable_formal(path):
    path = Path(path).resolve()
    return path.is_relative_to(DATA) and not path.is_relative_to(DATA/'assets')


def references(value):
    if isinstance(value,dict):
        for field,digest in [('file','sha256'),('frame','frameSha256'),('video','videoSha256')]:
            if isinstance(value.get(field),str) and value.get(digest):
                path = Path(value[field])
                path = path if path.is_absolute() else ROOT/path
                actual = sha(path)
                if is_mutable_formal(path):
                    historical.append(dict(file=str(path),historicalSha256=value[digest],currentSha256=actual,
                        historicalEqualsCurrent=actual==value[digest],usedAsCurrentGuard=False))
                else:
                    assert actual == value[digest], str(path)
        for child in value.values():
            references(child)
    elif isinstance(value,list):
        for child in value:
            references(child)


def git(*args):
    return subprocess.check_output(['git','--no-optional-locks',*args],cwd=DATA,text=True).strip()


def immutable(commit, name):
    """Retain exact committed bytes instead of racing the sole root writer."""
    raw = subprocess.check_output(['git','--no-optional-locks','show',f'{commit}:{name}'],cwd=DATA)
    destination = OUT/'git-inputs'/commit[:8]/name
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
    return destination


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and set(os.sched_getaffinity(0))=={0,1}
    head = git('rev-parse','HEAD')
    status_before = git('status','--porcelain')
    ledger_path,manifest_path = immutable(BASE,'review/native-restoration.json'),immutable(BASE,'manifest.json')
    catalog_path = DATA/'assets/catalog.json'
    ledger,manifest,catalog = read(ledger_path),read(manifest_path),read(catalog_path)
    native_path,review_path = immutable(BASE,'native/scenes/10450054.json'),immutable(BASE,'review/scenes/10450054.json')
    assert sha(native_path)==ledger['files']['native/scenes/10450054.json']
    assert sha(review_path)==ledger['files']['review/scenes/10450054.json']
    entry = next(entry for entry in manifest['scenes'] if entry['id']==10450054)
    encoded_entry = (json.dumps(entry,ensure_ascii=False,indent=2)+'\n').encode()
    assert hashlib.sha256(encoded_entry).hexdigest()==ledger['scenes']['10450054']
    native,review = read(native_path),read(review_path)
    nodes = {row['scenario_id']:row for row in native['scenario_list']}
    prior_path = R/'target-p30-first15-preflight-20261112-v1/receipt.json'
    prior = read(prior_path)
    assert prior['status'].startswith('passed_') and sha(catalog_path)==prior['currentCatalogSha256']
    first = read(R/'visual-high/accepted-p30-first15-identities-v1.json')
    first_keys = {(change['sceneId'],change['scenarioId']) for change in first['changes']}
    seen,packets,models = set(),[],Counter()
    for label,draft_name,draft_digest,expected,ordinals in SPECS:
        folder = R/'visual-high'/f'target-reviewed-p30-{label}-20261112-v1'
        draft_path = folder/draft_name
        accepted_path = R/'visual-high'/f'accepted-p30-{label}-identities-target-20261112-v1.json'
        binding_path = R/f'target-p30-{label}-root-binding-20261112-v1/receipt.json'
        draft,accepted,binding = read(draft_path),read(accepted_path),read(binding_path)
        assert sha(draft_path)==draft_digest and draft['rootConfirmed'] is False
        assert len(draft['changes'])==len(expected) and len(accepted['changes'])==len(expected)
        assert {row['scenarioId']:row['fields']['character'] for row in draft['changes']}=={number:'live2d/AC_'+model for number,model in expected.items()}
        normalized = deepcopy(draft)
        normalized.update(status='delegated_image_review_accepted_for_guarded_install',rootConfirmed=True)
        for row,actual in zip(normalized['changes'],accepted['changes']):
            row['rootConfirmed']=True
            row['evidence']['rootIntegration']=deepcopy(actual['evidence']['rootIntegration'])
        assert normalized==accepted, 'Accepted derivative changes delegated content beyond the authorized metadata'
        references(accepted)
        direct_path = Path(draft['reviewReceipt']['file'])
        direct = read(direct_path)
        references(direct)
        assert sha(direct_path)==draft['reviewReceipt']['sha256']
        assert sorted(direct['directlyViewedOrdinals'])==list(ordinals)
        assert direct['directlyViewedOriginalFullFrames']==15 and len(direct['observations'])==15
        assert all(direct[key] is False for key in ['actingAccepted','geometryAccepted','fullPartReviewed','fullPartIdentityAccepted','historicalFailedTrialAccepted','mainThreadViewedImages'])
        assert len(direct['observations'])==len({row['ordinal'] for row in direct['observations']})
        for observation in direct['observations']:
            assert observation['directImageReview'] and observation['fullFrameReview']
            assert observation['motionAndExpressionVerified'] is False
        revalidation = read(draft['referenceRevalidation']['file'])
        references(revalidation)
        for model in ['rom01','felt01']:
            model_spec = revalidation['models'][model]
            assert read(model_spec['currentFullCatalogRow']['file'])==catalog['models']['live2d/AC_'+model]
            canonical = json.dumps(catalog['models']['live2d/AC_'+model],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
            assert hashlib.sha256(canonical).hexdigest()==model_spec['currentFullCatalogRowCanonicalSha256']
        targets = []
        for change in accepted['changes']:
            number = change['scenarioId'];key=(change['sceneId'],number)
            assert key not in seen and key not in first_keys
            seen.add(key)
            assert key[0]==10450054 and change['expected']=={'character':''}
            assert set(change['fields'])=={'character'} and change['fields']['character']=='live2d/AC_'+expected[number]
            assert nodes[number]['character']==''
            current_review = review['scenarios'][str(number)]
            assert (current_review['stableKey'],current_review['sourceText'])==(change['stableKey'],change['sourceText'])
            evidence = change['evidence'];integration=evidence['rootIntegration']
            assert evidence['directImageReview'] and evidence['fullFrameReview'] and evidence['motionAndExpressionVerified'] is False
            assert integration['sourceDraft']==dict(file=str(draft_path),sha256=draft_digest)
            assert integration['independentReview']==draft['reviewReceipt']
            assert integration['binder']==dict(file=str(BINDER),sha256=sha(BINDER))
            assert integration['currentResourcePreflight']==dict(file=str(prior_path),sha256=sha(prior_path))
            assert integration['reviewer']=='/root' and integration['mainThreadViewedImages'] is False
            assert integration['acceptance']=='character_and_costume_only' and integration['motionAndExpressionAccepted'] is False
            observation = next(row for row in direct['observations'] if (row['sceneId'],row['scenarioId'])==key)
            assert observation['classification']=='confirmed_identity_new_field'
            assert observation['candidateModel']==expected[number]
            assert (observation['stableKey'],observation['sourceText'])==(change['stableKey'],change['sourceText'])
            assert observation['sourceWitness']==evidence['sourceWitness']
            models[change['fields']['character']]+=1
            targets.append(dict(sceneId=10450054,scenarioId=number,stableKey=change['stableKey'],expected={'character':''},
                fields=change['fields'],currentNativeRowSha256=hashlib.sha256(json.dumps(nodes[number],ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
        assert binding['status']=='passed_root_rebinding_of_independent_identity_review'
        assert binding['packet']['sha256']==sha(accepted_path) and binding['originalDraft']==dict(file=str(draft_path),sha256=draft_digest)
        assert binding['independentReview']==draft['reviewReceipt']
        assert binding['currentCatalogSha256']==sha(catalog_path) and not binding['actingAccepted']
        packets.append(dict(label=label,accepted=record(accepted_path),draft=record(draft_path),rootBinding=record(binding_path),
            directReview=record(direct_path),directlyViewedOrdinals=list(ordinals),targets=targets,
            exactDerivativeCheck='Only top status/rootConfirmed, change rootConfirmed and evidence.rootIntegration differ'))
    # Prove the complete immutable six-row publication delta, including every
    # untouched native property and row, independently of later root writes.
    six_path = immutable(SIX,'native/scenes/10450054.json')
    six = read(six_path)
    six_expected = {number:'live2d/AC_'+model for number,model in SPECS[0][3].items()}
    assert {key:value for key,value in native.items() if key!='scenario_list'} == {
        key:value for key,value in six.items() if key!='scenario_list'}
    assert len(native['scenario_list'])==len(six['scenario_list'])
    delta = []
    for before,after in zip(native['scenario_list'],six['scenario_list']):
        number = before['scenario_id']
        if number in six_expected:
            assert before['character']=='' and after==dict(before,character=six_expected[number])
            delta.append(dict(sceneId=10450054,scenarioId=number,before='',after=after['character']))
        else:
            assert before==after
    assert len(delta)==6
    # Current-file parses are observations only; immutable Git snapshots carry
    # the proof while root may legitimately apply the final three identities.
    parse_paths = sorted(set(parsed)|{str(DATA/'native/scenes/10450054.json'),
        str(DATA/'review/scenes/10450054.json'),str(DATA/'review/native-restoration.json'),str(DATA/'manifest.json')})
    node_result = subprocess.run(['/usr/bin/node',str(OUT/'node-parse.cjs'),*parse_paths],capture_output=True)
    with (OUT/'node-json-parse.json').open('x') as stream:
        stream.write(node_result.stdout.decode()+'\n')
    assert node_result.returncode==0,node_result.stderr.decode()
    node_parse = json.loads(node_result.stdout)
    assert node_parse['architecture']=='arm64' and all(row['success'] for row in node_parse['records'])
    assert all(row['sha256']==sha(row['file']) for row in node_parse['records'] if not is_mutable_formal(row['file']))
    for path in [ledger_path,manifest_path,native_path,review_path,catalog_path]:
        assert hashlib.sha256(path.read_bytes()).hexdigest()==checked[str(path.resolve())], 'Fresh current guard changed'
    result = dict(schema='stella.p30_extra9_independent_preflight.v1',status='passed_exact_derivatives_current_targets_and_resource_guards',
        reviewer='/root/p29_packet_preflight',createdUtc=datetime.now(timezone.utc).isoformat(),
        observedCurrentHeadBefore=head,observedCurrentHeadAfter=git('rev-parse','HEAD'),
        observedCurrentStatusBefore=status_before,observedCurrentStatusAfter=git('status','--porcelain'),
        immutableBlankTargetBase=BASE,immutableSixInstalledHead=SIX,immutableSixNativeDelta=delta,
        currentCatalogSha256=sha(catalog_path),currentOwnershipSha256=sha(ledger_path),binder=record(BINDER),
        independentMetadataOnly=True,imagesViewed=False,mainThreadViewedImages=False,acceptedChanges=9,
        acceptedByModel=dict(models),packets=packets,first7TargetKeys=sorted(first_keys),extra9DistinctFromFirst7=True,
        checkedFiles=[dict(file=file,sha256=digest) for file,digest in sorted(checked.items())],
        historicalMutableFormalReferences=historical,historicalWholeOwnershipRequiredUnchanged=False,
        pythonJsonParseExceptions=parse_errors,nodeJsonParse=record(OUT/'node-json-parse.json'),
        formalWrites=0,sourceWrites=0,gitMutations=0,browserStarted=False,newPlaybackVisits=0,
        actingAccepted=False,geometryAccepted=False,fullPartIdentityAccepted=False,fullRestorationAccepted=False)
    with (OUT/'receipt.json').open('x') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(receipt=record(OUT/'receipt.json'),acceptedChanges=9,byModel=dict(models),
        parsedJsonFiles=len(parsed),referenceFiles=len(checked),dataHead=head),ensure_ascii=False))


if __name__=='__main__':
    main()
