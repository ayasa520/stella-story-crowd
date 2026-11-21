"""Bind the actually saved silent54 suffix without starting any service.

The normal editor owns saved state and IDs. This reader verifies its exact
result and never constructs initial_state/before, modifies sparse fields or
converts source intervals into commands. Execution approval stays rootfalse.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=HERE.parent/'data-checkout'
SOURCE=ROOT/'artifacts/stella-site-repair-source/.sites-checkout'

def load(p): return json.loads(Path(p).read_text())
def git(p,*args): return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def write(name,value): (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

receipt=HERE.parent/'episode5-silent54-root-saved-verification-v1.json'
assert sha(receipt)=='b96257f60167816f565b9eca09fccb40724cb0e1ee7a678da9036a8ea4de83d5'
saved=load(receipt)
assert all(sha(DATA/p)==h for p,h in saved['files'].items())
assert git(DATA,'rev-parse','HEAD')==saved['dataHead']
native=load(DATA/'native/scenes/10090015.json');review=load(DATA/'review/scenes/10090015.json')
old=json.loads(git(DATA,'show','HEAD:native/scenes/10090015.json'))
old_review=json.loads(git(DATA,'show','HEAD:review/scenes/10090015.json'))
packet=load(HERE.parent/'episode5-silent-card-db238432-preflight-v1/silent-card.insertions.rootfalse.json')
proposal=packet['changes'][0]['nodes'][0]
row54=next(r for r in native['scenario_list'] if r['scenario_id']==54)
assert row54==proposal['native']
assert len(old['scenario_list'])==52 and len(native['scenario_list'])==53
expected=copy.deepcopy(old);index=next(i for i,r in enumerate(expected['scenario_list']) if r['scenario_id']==45)
expected['scenario_list'][index]['branch_list'][0]['transition_list'][0]['next_scenario_id']=54
expected['scenario_list'].insert(index+1,row54)
assert expected==native
assert all(review['scenarios'][sid]==value for sid,value in old_review['scenarios'].items())
assert review['scenarios']['54']['sourceText']=='――。\n――――。\n――――――――。'
assert review['scenarios']['54']['translation']==row54['msg_text']=='——。\n————。\n————————。'
assert sum(r.get('status')=='draft' for r in review['scenarios'].values())==53
ownership=git(DATA,'show','HEAD:review/native-restoration.json').encode()
assert json.loads(ownership)==load(DATA/'review/native-restoration.json')
assert subprocess.check_output(['git','-C',str(DATA),'show','HEAD:review/native-restoration.json'])==(DATA/'review/native-restoration.json').read_bytes()
manifest=load(DATA/'manifest.json');entry=next(s for s in manifest['scenes'] if s['id']==10090015)
assert entry['nodeCount']==53 and entry['reviewCounts']['draft']==53
assert sum(len(load(DATA/s['path'])['scenario_list']) for s in manifest['scenes'])==5620
steps=[]
for sid in [45,54,46,49,47]:
    row=next(r for r in native['scenario_list'] if r['scenario_id']==sid)
    stable=review['scenarios'][str(sid)].get('studioNodeId') or row['uniq_id']
    steps.append({'scenario':sid,'id':f'node:10090015:{stable}','native':row,
                  'expectedModel':row['character'].removeprefix('live2d/AC_')})
assert steps[0]['id']=='node:10090015:node_dae6816ae851'
assert steps[1]['id']=='node:10090015:node_869b7bc19352'
for a,b in zip(steps,steps[1:]): assert a['native']['branch_list'][0]['transition_list'][0]['next_scenario_id']==b['scenario']
assert steps[-1]['native']['bg_music']=='bgm_btl_adv_win01'
langs=[{'name':'silent54-zh','language':'zh','expectedText':row54['msg_text'],'bar':'—'},
       {'name':'silent54-ja','language':'ja','expectedText':review['scenarios']['54']['sourceText'],'bar':'―'}]
plan={'schema':'stella.silent54.saved-plan.v1','rootConfirmed':False,'status':'saved-await-root-runtime-release',
      'sceneId':10090015,'start':steps[0]['id'],'steps':steps,'languages':langs,
      'allLibraryNodes':5620,'targetSceneRows':53,'targetDraftRows':53,'expectedBgm':'bgm_btl_adv_win01',
      'perLanguageEntered':5,'perLanguageTransitionsIncludingSection':5,'stopAfterSection1009Complete':True,
      'forbiddenEnterPrefix':'node:10020001:','captureLimit':10,'maximumCaptureBytes':3000000,
      'scope':'New independent silent54 panel in both languages, saved45→54→46, full natural49 and win01/CLEAR/sectioncomplete. No original timing, acting, face, phase, subjective audio or whole-episode acceptance.'}
write('capture-plan.json',plan)
base=load(HERE.parent/'p42-six-visual-saved-runtime-v1/input-binding.json')
source={p:sha(SOURCE/p) for p in sorted(git(SOURCE,'ls-files').splitlines()) if (SOURCE/p).is_file()}
dist={str(p.relative_to(SOURCE/'dist')):sha(p) for p in sorted((SOURCE/'dist').rglob('*')) if p.is_file()}
assert source==base['source']['sourceFiles'] and dist==base['source']['distFiles']
assert sha(SOURCE/'public/player/native-title.json')=='ac2eee6d1db23fd8ec636d870672110ca570f1d326cd3364073e086d36bc4447'
paths={s[k] for s in manifest['scenes'] for k in ['path','reviewPath']}
paths|={'manifest.json','review/native-restoration.json','assets/catalog.json','assets/package.json','assets/preview/catalog.json'}
extra=['assets/music/bgm_adv_fuon02_cd2_14.json','assets/music/bgm_btl_adv_win01.json',
       'assets/backgrounds/ADV_bg001_black.png']
for member in extra:
    raw=subprocess.check_output(['git','-C',str(DATA),'show',saved['dataHead']+':'+member])
    assert hashlib.sha256(raw).hexdigest()==sha(DATA/member)
    paths.add(member)
for model in ['kadomon01','subaru01']:
    for group in ['assets/models','assets/preview/models']:
        paths|={str(p.relative_to(DATA)) for p in (DATA/group/model).rglob('*') if p.is_file()}
paths|={str(p.relative_to(DATA)) for p in (DATA/'assets/player').rglob('*') if p.is_file()}
catalog=load(DATA/'assets/catalog.json')
for scene in [10090013,10090014,10090015]:
    for row in load(DATA/f'native/scenes/{scene}.json')['scenario_list']:
        for field,group in [('bg_picture','backgrounds'),('bg_music','music'),('video','movies')]:
            value=row[field].split(',')[0]
            if not value: continue
            asset=catalog[group][value];url=asset['url'];path=DATA/'assets'/url
            if path.is_file(): paths.add(str(path.relative_to(DATA)))
            stem=Path(url).stem
            for found in (DATA/'assets/preview'/group).glob(stem+'.*'):
                if found.is_file(): paths.add(str(found.relative_to(DATA)))
first=base['protectedFirstThree'];assert {p:sha(DATA/p) for p in first}==first
evidence=ROOT/'data/native_recovery/royal-capital-20261110/repair-20261111/episode5-fuon01-provider-investigation-20261121-v1'
guards={str(evidence/n):sha(evidence/n) for n in ['silent-card-source-review.json','native-phase-contract.json']}
assert guards[str(evidence/'silent-card-source-review.json')]=='6428b08ce6e47a05593038b775904b56bac79121420903bc3b226774fd54ff9d'
binding={'schema':'stella.silent54.saved-inputs.v1','rootConfirmed':False,'dataRoot':str(DATA),'sourceRoot':str(SOURCE),
  'dataHead':git(DATA,'rev-parse','HEAD'),'dataStatus':git(DATA,'status','--short'),
  'dataInputs':{p:sha(DATA/p) for p in sorted(paths)},'protectedFirstThree':first,
  'allSceneFiles':{s[k]:sha(DATA/s[k]) for s in manifest['scenes'] for k in ['path','reviewPath']},
  'source':{'head':git(SOURCE,'rev-parse','HEAD'),'status':git(SOURCE,'status','--short'),
            'sourceFiles':source,'distFiles':dist,'sourceTreeSha256':digest(source)},
  'resourceAndSourceGuards':guards,'savedReceipt':{'path':str(receipt),'sha256':sha(receipt)},
  'captureReadiness':load(HERE.parent/'p31-p33-ending-runtime-final-v3/input-binding.json')['captureReadiness'],
  'planSha256':sha(HERE/'capture-plan.json')}
binding['snapshotIdentitySha256']=digest({'dataHead':binding['dataHead'],'dataInputs':binding['dataInputs'],
                                        'sourceTree':binding['source']['sourceTreeSha256']})
binding['revision']=binding['snapshotIdentitySha256'][:40]
binding['revisionMeaning']='Content-derived saved worktree alias, not a Git ref'
binding['addedActualProviderMembers']=extra
previous_events=HERE.parent/'episode5-silent54-saved-runtime-v1/attempt-1/provider-events.jsonl'
previous_rows=[json.loads(line) for line in previous_events.read_text().splitlines() if line]
assert all(binding['dataInputs'].get(row['relative'])==row['sha256'] for row in previous_rows)
binding['previousCaptureActualProviderReadsAllCovered']=len(previous_rows)
write('input-binding.json',binding)
print(json.dumps({'rootConfirmed':False,'data':len(paths),'source':len(source),'dist':len(dist),'rows':53,'library':5620,'revision':binding['revision']}))
