"""Prepare read-only file locks and bounded source receipts, without a browser.

This script writes only new evidence beside itself. Its lock describes the
current canonical372 source; it is not a claim that P09 multi-actor execution
exists there, nor does it authorize enabling the unaccepted prototype.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
HERE = Path(__file__).resolve().parent
SITE = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
DATA = ROOT / 'story_crowd_data'


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(path, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=path, text=True).strip()


def write_new(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    if git(SITE, 'rev-parse', 'HEAD') != '37232806a8180375a4b7a178e27157bb16d12201' or git(SITE, 'status', '--porcelain=v1'):
        raise ValueError('The inspected canonical source is not clean37232806')
    catalog = json.loads((DATA / 'assets/catalog.json').read_text())
    resources, models = [], []
    for model in ['kan01', 'chin01', 'ton01']:
        entry = catalog['models']['live2d/AC_' + model]
        detail = json.loads((DATA / 'assets' / entry['detail_url']).read_text())
        member = detail['member']
        model_path = DATA / 'assets' / catalog['asset_members'][member]
        document = json.loads(model_path.read_text())
        references = document['FileReferences']
        base_member = member.rsplit('/', 1)[0] + '/'
        members = [('modelJSON', member), ('MOC', base_member + references['Moc'])]
        members += [('texture', base_member + value) for value in references['Textures']]
        for kind, source_member in members:
            path = DATA / 'assets' / catalog['asset_members'][source_member]
            resources.append({**receipt(path), 'kind': kind, 'model': model, 'pathname': '/asset/' + source_member})
        models.append({'model': model, 'modelJSONPath': '/asset/' + member})
    # These are the actual /player/ module graph and its shared Animator/clock,
    # not an assumption that the /studio/ placement copy is the loaded owner.
    required_sources = ['pairing/vendor/cubism4.min.js', 'pairing/vendor/live2dcubismcore.min.js',
        'pairing/vendor/pixi.min.js', 'pairing/viewer.js', 'pairing/model_resources.js',
        'player/player.js', 'player/player_scene.js', 'player/actor_placement.js',
        'player/actor_animation.js', 'player/actor_stage.js', 'studio/actor_animation.js',
        'studio/visual_frame_clock.js', 'studio/native_time_config.js']
    resources += [{**receipt(SITE / 'public' / relative), 'kind': 'source', 'pathname': '/' + relative}
                  for relative in required_sources]
    lock = {'status': 'prepared_unexecuted_not_acceptance', 'canonicalSource': git(SITE, 'rev-parse', 'HEAD'),
        'dataHead': git(DATA, 'rev-parse', 'HEAD'), 'models': models, 'resources': resources,
        'resourceHashStageRequired': 'actual_response_body_no_second_fetch',
        'currentCanonicalHasNativeParentBranch': 'native_parent' in (SITE / 'public/player/actor_placement.js').read_text(),
        'currentCanonicalHasNativeActorParser': (SITE / 'lib/native-actors.ts').exists()}
    write_new('resource-lock.json', lock)

    snippets = []
    needles = {'pairing/vendor/cubism4.min.js': [
        ('actual_core_wrapper', 'class D{update(){', 150),
        ('SDK_input_restore_order', 'this.emit("beforeModelUpdate"),o.update(),o.loadParameters()', 70),
        ('actual_model_render_update_draw', '_render(t){', 1210),
        ('internal_projection_and_drawModel', 'draw(t){const e=this.drawingMatrix', 270),
        ('native_array_accessors', 'getDrawableVertexIndices(t){', 260),
        ('render_order_sort_and_color_submission', 'doDrawModel(){', 1000),
        ('actual_drawMesh_upload', 'drawMesh(t,e,i,s,r,a,o,n,l){', 1250),
        ('mask_setup_drawMesh', 'drawMesh(t.getDrawableTextureIndices(r)', 500),
        ('mask_context_accessor', 'getClippingContextBufferForMask(){', 230),
        ('renderer_core_identity', 'this.renderer.initialize(this.coreModel)', 100)],
        'pairing/vendor/live2dcubismcore.min.js': [('draw_order_array', 'this.drawOrders=', 180),
            ('stable_vertex_views', 'this.vertexPositions=new Array', 550),
            ('stable_index_views', 'this.indices=new Array', 450)]}
    for relative, items in needles.items():
        path = SITE / 'public' / relative
        raw = path.read_bytes()
        for role, needle, length in items:
            offset = raw.index(needle.encode())
            snippets.append({**receipt(path), 'role': role, 'line': 1, 'byteOffset': offset,
                'needle': needle, 'text': raw[offset:offset + length].decode()})
    qa = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111/visual-high/assembled-three-case-plan-20261112-v1/instrument.js'
    audit = {'status': 'offline_source_audit_only_unexecuted', 'createdUtc': datetime.now(timezone.utc).isoformat(),
        'canonicalSource': lock['canonicalSource'], 'dataHead': lock['dataHead'],
        'borrowedQAInstrument': receipt(qa), 'borrowedBoundaries': {'Core.update': [33, 62], 'Renderer.render': [157, 174]},
        'sourceSnippets': snippets, 'scopeLimits': [
            'No actual runtime result, delivered byte hash, or geometry packet was collected.',
            'Current canonical372 lacks the native_parent projection branch and native actor parser.',
            'The lock must not be silently applied to the unaccepted story_crowd prototype.']}
    write_new('source-audit.json', audit)
    print(json.dumps({'status': audit['status'], 'resources': len(resources), 'canonicalSource': lock['canonicalSource'],
        'nativeParentAvailable': lock['currentCanonicalHasNativeParentBranch'],
        'nativeActorParserAvailable': lock['currentCanonicalHasNativeActorParser']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
