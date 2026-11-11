"""Find direct references to exactly three command-boundary methods.

This is one bounded pass over executable ELF load segments, not disassembly of
the game corpus. Only BL/B destinations for the three declared targets are
retained. Enclosing indexed methods are candidates/upper bounds, and indirect
registrations remain an explicit limitation. No game or browser is started.
"""

import bisect
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'data/libil2cpp-offline.so').exists())
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def ref(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    start = time.monotonic()
    inherited = OUT.parent / 'native-motion-entry-20261111/entry-order-evidence.json'
    inspector = OUT.parent / 'native-bgm-entry-20261112/inspect_native_bgm.py'
    spec = importlib.util.spec_from_file_location('command_xref_inherited', inspector)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    source = ROOT / 'data/libil2cpp-offline.so'; before = ref(source)
    image = helper.load_image_reader(OUT.parent / 'visual-low/inspect_native_actor_grammar.py')(source)
    metadata = Metadata((ROOT / 'logs/metadata-decrypted.dat').read_bytes(),
        json.loads((ROOT / 'lost_in_memories/config/metadata_layout.json').read_text()),
        json.loads((ROOT / 'logs/metadata-types.json').read_text()))
    module = next(row for row in json.loads(inherited.read_text())['modules'] if row['name'] == 'Assembly-CSharp.dll')
    names, methods = helper.index_methods(metadata, image, module); addresses = sorted(names)
    targets = {0x159E518: 'Stella.ScriptSystem.ScriptManager.SetFuncTbl',
               0x1250558: 'Stella.Scenes.ADV2.ADVPlayer.SetTextPanel',
               0x124D4C4: 'Stella.Scenes.ADV2.ADVPlayer.SendScenarioID'}
    hits, bounds = [], []
    for segment in image.segments:
        if segment[0] != 1 or not segment[1] & 1:
            continue
        file_offset, va, byte_count = segment[2], segment[3], segment[5]
        assert byte_count % 4 == 0
        bounds.append({'fileOffset': hex(file_offset), 'virtualAddress': hex(va), 'bytes': byte_count})
        for ordinal, (word,) in enumerate(struct.iter_unpack('<I', image.raw[file_offset:file_offset + byte_count])):
            opcode = word & 0xFC000000
            if opcode not in (0x94000000, 0x14000000):
                continue
            imm = word & 0x3FFFFFF
            if imm & 0x2000000:
                imm -= 0x4000000
            at = va + ordinal * 4; target = at + imm * 4
            if target not in targets:
                continue
            pos = bisect.bisect_right(addresses, at) - 1
            enclosing = addresses[pos] if pos >= 0 else None
            end = addresses[pos + 1] if pos + 1 < len(addresses) else None
            hits.append({'at': hex(at), 'opcode': 'bl' if opcode == 0x94000000 else 'b',
                'target': hex(target), 'targetName': targets[target],
                'enclosingIndexedCandidateStart': hex(enclosing) if enclosing else None,
                'nextIndexedUpperBound': hex(end) if end else None,
                'candidateNames': names.get(enclosing, [])})
    assert before == ref(source)
    result = {'status': 'targeted_direct_branch_xrefs_only', 'source': before, 'inspector': ref(inspector),
        'module': module, 'targets': {hex(key): value for key, value in targets.items()},
        'scannedExecutableBounds': bounds, 'hits': hits, 'elapsedSeconds': time.monotonic() - start,
        'limits': ['Direct B/BL only; indirect or inlined references are not covered.',
                   'Nearest indexed method labels are candidates within an upper bound, not recovered function-size symbols.']}
    target = OUT / 'targeted-command-registration-xrefs.json'
    with target.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'receipt': ref(target), 'hits': len(hits), 'elapsedSeconds': result['elapsedSeconds'],
        'advCandidates': [row for row in hits if any('ADV' in name for name in row['candidateNames'])]}))


if __name__ == '__main__':
    main()
