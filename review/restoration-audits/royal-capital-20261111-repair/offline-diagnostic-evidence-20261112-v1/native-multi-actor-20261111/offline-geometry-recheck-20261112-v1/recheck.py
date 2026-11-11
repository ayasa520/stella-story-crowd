"""Recheck bounded existing geometry receipts; never render or author data.

This evidence tool deliberately separates the direct-canvas equivalent origin
from Unity's actual world space. It validates the existing neutral examples,
not the unknown original P09 script or the evaluated pose of any screenshot.
Run offline with nice 19 and CPU affinity 22,23 as required by AGENTS.md.
"""

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import zipfile

import UnityPy


ROOT = Path('/home/rikka/Projects/stella')
BASE = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111/native-multi-actor-20261111'
HERE = Path(__file__).resolve().parent
CANONICAL = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'


def read(relative):
    return json.loads((ROOT / relative).read_text())


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def receipt(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': digest(path)}


def transform(point, position, angle, scale):
    radians = math.radians(angle['z'])
    x, y = point['x'] * scale['x'], point['y'] * scale['y']
    return {'x': position['x'] + math.cos(radians) * x - math.sin(radians) * y,
            'y': position['y'] + math.sin(radians) * x + math.cos(radians) * y,
            'z': position['z'] + point['z'] * scale['z']}


def main():
    layout = json.loads((BASE / 'original-layout.json').read_text())
    detached = json.loads((BASE / 'canvas-geometry-detached-result.json').read_text())
    projected = json.loads((BASE / 'visual-review/projection-logs.json').read_text())
    config = read('story_studio/config/player_assets.json')

    # Decode only the small, already identified scene member. This supplies an
    # independent original-camera receipt without another broad asset scan.
    with zipfile.ZipFile(ROOT / config['apk']) as archive:
        raw = archive.read(layout['space']['source'])
    environment = UnityPy.load(raw)
    camera = next(obj.read_typetree() for obj in environment.objects if obj.type.name == 'Camera')
    camera_transform = next(row['transform'] for row in layout['space']['transforms'] if row['name'] == 'Camera')
    camera_origin = camera_transform['m_LocalPosition']
    bases = {row['model']: next(component['value'] for component in row['components']
             if component['name'] == 'CH_top') for row in layout['actors']}
    clips = {row['name']: row for row in layout['clips']}

    sources = [layout['source']] + [{'path': row['source'], 'sha256': row['sha256']} for row in layout['actors']]
    sources += json.loads((BASE / 'model-origin-evidence.json').read_text())['sources']
    source_checks = [{**row, 'actualSha256': digest(ROOT / row['path'])} for row in sources]
    for row in source_checks:
        row['matches'] = row['actualSha256'] == row['sha256']

    calculations = []
    for index, row in enumerate(projected['entries']):
        event = row['event']
        base, script, slot = bases[event['model']], event['script'], event['layout']['slot']
        original_slot = clips[event['layout']['clip']]['slots'][slot['name']]
        slot_matches = all(slot[key] == dict(zip(('x', 'y', 'z'), original_slot[original_key]))
                           for key, original_key in [('position', 'position'), ('angle', 'euler'), ('scale', 'scale')])
        origin = transform(base['m_LocalPosition'], script['position'], script['angle'], script['scale'])
        origin = transform(origin, slot['position'], slot['angle'], slot['scale'])
        pixels = event['viewport'][1] / (2 * (origin['z'] - camera_origin['z']) * math.tan(math.radians(camera['field of view'] / 2)))
        residual = {axis: origin[axis] - event['world'][axis] for axis in ('x', 'y', 'z')}
        calculations.append({'index': index, 'caseId': row['caseId'], 'model': event['model'],
            'sourceEntryIndex': event['source']['entry_index'], 'slotIndex': event['layout']['slot_index'],
            'slotMatchesOriginalClip': slot_matches, 'at': event['at'], 'equivalentCardSpaceOrigin': origin,
            'originResidualVsLoggedWorld': residual, 'recomputedPixelsPerUnityUnit': pixels,
            'pixelsResidual': pixels - event['pixels']})

    canvas_checks = []
    for event in detached['models']:
        width, height = event['canvas']['width'], event['canvas']['height']
        origin, ppu = event['world'], event['ppu']
        predicted_position = {'x': event['viewport'][0] / 2 + (origin['x'] - camera_origin['x']) * event['pixels'],
                              'y': event['viewport'][1] / 2 - (origin['y'] - camera_origin['y']) * event['pixels']}
        base, script, slot = bases[event['model']], event['script'], event['layout']['slot']
        predicted_scale = {axis: base['m_LocalScale'][axis] * script['scale'][axis] * slot['scale'][axis]
                           * event['pixels'] / ppu / event['internalTransform'][matrix_axis]
                           for axis, matrix_axis in [('x', 'a'), ('y', 'd')]}
        canvas_checks.append({'model': event['model'], 'canvasOriginMinusCenter': {
            'x': event['canvas']['originX'] - width / 2, 'y': event['canvas']['originY'] - height / 2},
            'internalTransform': event['internalTransform'], 'anchor': event['anchor'],
            'positionResidual': {axis: predicted_position[axis] - event['projectedPosition'][axis] for axis in ('x', 'y')},
            'scaleResidual': {axis: predicted_scale[axis] - event['modelScale'][axis] for axis in ('x', 'y')}})

    groups = defaultdict(list)
    for row in calculations:
        groups[row['caseId']].append(row)
    groups = [{'caseId': case, 'fitInvocationModelOrder': [row['model'] for row in rows],
               'fitInvocationTimes': [row['at'] for row in rows],
               'actualDrawOrderMeasured': False} for case, rows in groups.items()]

    # Preserve short, exact code excerpts and hashes. Vendor byte offsets are
    # stable only for the recorded blob; they are never generalized to a build.
    ranges = {
        'story_crowd/lib/native-actors.ts': [(126, 164)],
        'story_crowd/public/studio/actor_placement.js': [(110, 164)],
        'story_crowd/public/studio/actor_stage.js': [(47, 79)],
        'story_crowd/public/pairing/viewer.js': [(100, 115)],
        'story_crowd/public/studio/player_scene.js': [(33, 39)],
        'story_crowd/public/studio/actor_animation.js': [(230, 240)],
        str((BASE / 'geometry-native-capstone.txt').relative_to(ROOT)): [(492, 550), (550, 599), (663, 710)],
        str((BASE / 'model-origin-native-capstone.txt').relative_to(ROOT)): [(1282, 1293)],
    }
    snippets = []
    for relative, spans in ranges.items():
        path = ROOT / relative
        lines = path.read_text().splitlines()
        snippets.append({**receipt(path), 'ranges': [{'firstLine': first, 'lastLine': last,
            'text': '\n'.join(lines[first - 1:last])} for first, last in spans]})
    vendor_path = ROOT / 'story_crowd/public/pairing/vendor/cubism4.min.js'
    vendor = vendor_path.read_bytes()
    needles = [b'_render(t){', b'this.emit("beforeModelUpdate"),o.update(),o.loadParameters()',
               b'draw(t){const e=this.drawingMatrix', b'this.renderer.drawModel()']
    vendor_snippets = [{**receipt(vendor_path), 'line': 1, 'byteOffset': vendor.index(needle),
        'needle': needle.decode(), 'text': vendor[vendor.index(needle):vendor.index(needle) + length].decode()}
        for needle, length in zip(needles, [1200, 100, 265, 50])]

    input_paths = ['REPORT.md', 'NATIVE_GEOMETRY_LOG_PLAN.md', 'original-layout.json', 'original-scaling.json',
        'model-origin-evidence.json', 'geometry-channel-review.json', 'geometry-channel-evidence.json',
        'visual-review/projection-logs.json', 'visual-review/visual-review-result.json', 'canvas-geometry-detached-result.json']
    result = {'status': 'static_receipt_recheck_passed_cause_unproven', 'createdUtc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Offline audit only. No image inspection, browser, model update, fitting, source/data/Git write.',
        'process': {'nice': os.getpriority(os.PRIO_PROCESS, 0), 'affinity': sorted(os.sched_getaffinity(0))},
        'canonical': {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CANONICAL, text=True).strip(),
            'status': subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=CANONICAL, text=True)},
        'originalInputChecks': source_checks,
        'originalCamera': {'sourceMember': layout['space']['source'], 'sourceBytes': len(raw),
            'sourceSha256': hashlib.sha256(raw).hexdigest(), 'matchesPreviousSourceHash': hashlib.sha256(raw).hexdigest() == layout['space']['sha256'],
            'camera': camera, 'localTransform': camera_transform},
        'projectionRecomputations': calculations, 'canvasChecks': canvas_checks,
        'fitInvocationGroups': groups, 'inputReceipts': [receipt(BASE / path) for path in input_paths],
        'codeReceipts': snippets, 'vendorReceipts': vendor_snippets,
        'limits': ['Logged world is equivalent reduced card-space origin, not Unity localToWorld.',
            'Fit logs are not joined to screenshot draw submissions, parameter generations or evaluated drawable vertices.',
            'Original active P09 CSV, camera/runtime UI state and pose remain unknown.',
            'No camera, offset, scale, native field, model variant or motion value is proposed.']}
    result['checks'] = {'sourceHashesMatch': all(row['matches'] for row in source_checks),
        'originalCameraMemberMatches': result['originalCamera']['matchesPreviousSourceHash'],
        'all12SlotsMatchOriginal': len(calculations) == 12 and all(row['slotMatchesOriginalClip'] for row in calculations),
        'all12SlotIndicesPreserved': all(row['sourceEntryIndex'] == row['slotIndex'] for row in calculations),
        'all12OriginsAndPixelsMatch': all(max(abs(value) for value in row['originResidualVsLoggedWorld'].values()) < 1e-9
            and abs(row['pixelsResidual']) < 1e-9 for row in calculations),
        'threeCanvasCentersAndPlacementMatch': len(canvas_checks) == 3 and all(
            max(abs(value) for key in ['canvasOriginMinusCenter', 'positionResidual', 'scaleResidual'] for value in row[key].values()) < 1e-9
            for row in canvas_checks)}
    (HERE / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'checks': result['checks'], 'process': result['process'],
        'canonical': result['canonical'], 'receipt': str(HERE / 'receipt.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
