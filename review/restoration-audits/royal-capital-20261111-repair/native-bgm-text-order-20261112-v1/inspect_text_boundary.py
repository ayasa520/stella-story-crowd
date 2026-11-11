"""Inspect bounded original text/background/bridge edges without running it.

Reuse the archived BGM inspector's assembly-correct indexing/disassembler.
Inputs and inherited evidence are hashed before/after. Inventory is restricted
to relevant owners; dumps are explicitly named methods with inherited hard
bounds. Indirect calls and callback timing remain unresolved unless separately
bound. Never write into the old evidence directory or a formal source tree.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'data/libil2cpp-offline.so').exists())
R = OUT.parent
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', action='append', default=[])
    parser.add_argument('--prefix', default='text-boundary-pass1')
    parser.add_argument('--slot', action='append', default=[])
    args = parser.parse_args()
    assert Path(args.prefix).name == args.prefix
    inherited_path = R / 'native-motion-entry-20261111/entry-order-evidence.json'
    helper_path = R / 'visual-low/inspect_native_actor_grammar.py'
    bgm_path = R / 'native-bgm-entry-20261112/inspect_native_bgm.py'
    paths = [ROOT / 'data/libil2cpp-offline.so', ROOT / 'logs/metadata-decrypted.dat',
             ROOT / 'lost_in_memories/config/metadata_layout.json', ROOT / 'logs/metadata-types.json',
             ROOT / 'logs/adv.html', inherited_path, helper_path, bgm_path, Path(__file__)]
    before = [receipt(path) for path in paths]
    inherited = json.loads(inherited_path.read_text())
    bgm = import_file('inherited_bgm_inspector', bgm_path)
    image = bgm.load_image_reader(helper_path)(paths[0])
    metadata = Metadata(paths[1].read_bytes(), json.loads(paths[2].read_text()), json.loads(paths[3].read_text()))
    names, methods, modules = {}, [], []
    for name in ['Assembly-CSharp.dll', 'UnityEngine.CoreModule.dll']:
        module = next(row for row in inherited['modules'] if row['name'] == name)
        modules.append(module)
        found_names, found_methods = bgm.index_methods(metadata, image, module)
        for address, labels in found_names.items():
            names.setdefault(address, []).extend(labels)
        methods.extend(found_methods)
    inventory = [row for row in methods if row['owner'].startswith('Stella.ScriptSystem.') or
        row['owner'].startswith('Stella.Scenes.ADV2.UIController') or
        row['owner'].startswith('Stella.Scenes.ADV2.TextPanel') or
        row['owner'].startswith('Stella.Scenes.ADV2.ADVPlayer') or
        row['owner'].startswith('Stella.Scenes.ADV2.Director')]
    selected, calls, text = bgm.disassemble_targets(image, names, methods, args.target)
    disassembly_path = OUT / (args.prefix + '-capstone.txt')
    with disassembly_path.open('x') as stream:
        stream.write(text)
    # Bind delegate/literal slots by exact metadata usage pairs. Do not infer a
    # closure from a nearby method name or a same-number token in another DLL.
    usage_base, usage_count = 0x2B94018, 47169
    usages = {image.qword(usage_base + n * 8): n for n in range(usage_count)}
    pair_offset = struct.unpack_from('<I', metadata.data, 20)[0]
    pair_bytes = struct.unpack_from('<I', metadata.data, 112)[0]
    slots = []
    for slot_text in args.slot:
        slot = int(slot_text, 0); destination = usages[image.qword(slot)]
        encodings = {encoded for pos in range(pair_offset, pair_offset + pair_bytes, 8)
                     for target, encoded in [struct.unpack_from('<II', metadata.data, pos)] if target == destination}
        assert len(encodings) == 1, (slot_text, encodings)
        encoded = encodings.pop(); kind, index = encoded >> 29, encoded & 0x1FFFFFFF
        row = {'slot': hex(slot), 'destination': destination, 'encoded': hex(encoded), 'kind': kind, 'index': index}
        if kind == 3:
            offset = metadata.layout['methods_offset'] + index * 32
            row.update(method=metadata.definition_name(metadata.integer(offset + 4)) + '.' + metadata.string(metadata.integer(offset)),
                       token=hex(metadata.integer(offset + 20)))
        elif kind == 5:
            literal_table = struct.unpack_from('<I', metadata.data, 176)[0]
            literal_data = struct.unpack_from('<I', metadata.data, 116)[0]
            length, offset = struct.unpack_from('<II', metadata.data, literal_table + index * 8)
            row['literal'] = metadata.data[literal_data + offset:literal_data + offset + length].decode()
        slots.append(row)
    assert before == [receipt(path) for path in paths]
    result = {'status': 'bounded_static_text_background_bridge_inspection_no_runtime', 'inputs': before,
        'modules': modules, 'inventory': inventory, 'selectedMethods': selected, 'calls': calls,
        'usageSlots': slots, 'disassembly': receipt(disassembly_path),
        'limits': ['No native/browser process or image review.', 'Method ends are next-indexed-method upper bounds.',
                   'A submission/callback construction does not prove its latency or the order of independent completions.']}
    target = OUT / (args.prefix + '-evidence.json')
    with target.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'evidence': receipt(target), 'methods': len(selected), 'inventory': len(inventory), 'disassembly': receipt(disassembly_path)}))


if __name__ == '__main__':
    main()
