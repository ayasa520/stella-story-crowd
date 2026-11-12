"""Prepare a normal alignment case and a separately scoped private FX probe.

Retain the existing adapter guard set. Refresh only the two edited player
files and add the two reviewed presentation files; do not rebuild an asset
inventory or change formal data. Root must apply and review the source first.
"""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
OLD = R / 'p30-ending-normal-runtime-20261113-v1'
release = json.loads((OLD / 'service-release.json').read_text())
updated = ['public/player/player_scene.js', 'public/player/player_config.json']
added = ['public/player/text_panel_presentation.js', 'public/player/text-panel-presentation.json']
for relative in updated + added:
    path = SITE / relative
    content = path.read_bytes()
    matches = [record for record in release['guardFiles'] if record['path'] == str(path)]
    if relative in updated:
        assert len(matches) == 1, relative
        record = matches[0]
    else:
        assert not matches, relative
        record = dict(path=str(path))
        release['guardFiles'].append(record)
    record.update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
release.update(status='root_reviewed_scoped_narration_alignment_and_private_fx_observer',
               dataHead='60df9eb51a7849134a296e95a187fa6bc21e0006', dataWorktreeBatch=None,
               purpose='Normal35 JA/ZH and default narration; separate private FXv2',
               canonicalWorktree='817a45f6 plus reviewed four-file alignment patch',
               allowedRequests=[dict(sceneId=scene, scenarioId=node, nativePreview='')
                                for scene,node in [(10450058,34),(10450056,2),(10450056,25)]])
(HERE / 'service-release.json').write_text(json.dumps(release, indent=2) + '\n')
(HERE / 'release-delta.json').write_text(json.dumps(dict(
    source=str(OLD / 'service-release.json'), refreshedKnownSourceFiles=updated,
    newReviewedSourceFiles=added, formalDataChanged=False, newInventory=False), indent=2) + '\n')
shutil.copyfile(OLD / 'run-service.py', HERE / 'run-service.py')

proposal = R / 'p30-fx-observer-driver-proposal-20261113-v2'
options = dict(baseUrl='http://127.0.0.1:5192', executionAuthorized=True,
               ownerInstallSource=(proposal / 'owner-install-handle.js').read_text(),
               observerFactorySource=(R / 'p30-fx-first-paint-observer-proposal-20261113-v2/observer-factory.js').read_text(),
               candidateManifestSource=(R / 'p30-node27-fx-source-proposal-20261112-v1/candidate-player-v3/effects-candidate.json').read_text())
(HERE / 'capture-private-fx.js').write_text('async page => {\nconst run=' +
    (proposal / 'driver-factory.js').read_text().strip() +
    ';\nreturn await run(page,' + json.dumps(options) + ');\n}\n')
print(json.dumps(dict(prepared=True, updatedSourceFiles=2, newSourceFiles=2,
                     formalDataChanged=False)), flush=True)
