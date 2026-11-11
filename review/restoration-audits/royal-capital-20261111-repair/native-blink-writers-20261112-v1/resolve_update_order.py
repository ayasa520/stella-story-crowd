"""Resolve only the literal type slots used by the bounded blink trace.

The IL2CPP usage pair's TypeInfo/Il2CppType index is a runtime type index,
not a type-definition index. Keep generic MethodRef entries numeric: a
convenient-looking component name must never substitute for a recovered
generic binding. This tool reads original files and writes only its own new
evidence file; it neither loads Unity nor inspects a running process.
"""

import importlib.util
import json
import os
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [22, 23]
    helper_path = HERE.parent / 'native-bgm-entry-20261112/inspect_native_bgm.py'
    spec = importlib.util.spec_from_file_location('blink_slot_helper', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.load_image_reader(HERE.parent / 'visual-low/inspect_native_actor_grammar.py')(
        ROOT / 'data/libil2cpp-offline.so')
    metadata = Metadata((ROOT / 'logs/metadata-decrypted.dat').read_bytes(),
                        json.loads((ROOT / 'lost_in_memories/config/metadata_layout.json').read_text()),
                        json.loads((ROOT / 'logs/metadata-types.json').read_text()))
    usage_base, usage_count = 0x2B94018, 47169
    usage_indices = {image.qword(usage_base + index * 8): index
                     for index in range(usage_count)}
    # All addresses below are retained verbatim from the bounded disassembly.
    # Stack locations and combine sites identify the actual construction order
    # instead of assuming an order from SDK names or a modern implementation.
    slots = [
        ('component_x24', 0x2D11E80), ('component_sp38', 0x2C97F10),
        ('component_sp30', 0x2CD1D48), ('component_sp28', 0x2C97C38),
        ('component_sp20', 0x2C99D48), ('component_sp18', 0x2CA2FE8),
        ('component_sp08', 0x2CFB958), ('component_sp00', 0x2CC93E0),
        ('component_sp10', 0x2CFDAF0), ('update_interface', 0x2CFE7D8),
        ('auto_start_component_generic', 0x2D27F90),
        ('blink_refresh_component_generic', 0x2D188B8),
    ]
    pair_start = struct.unpack_from('<I', metadata.data, 20)[0]
    pair_bytes = struct.unpack_from('<I', metadata.data, 112)[0]
    assert (pair_start, pair_bytes) == (8196832, 1245240)
    by_destination = {}
    for at in range(pair_start, pair_start + pair_bytes, 8):
        destination, encoded = struct.unpack_from('<II', metadata.data, at)
        by_destination.setdefault(destination, set()).add(encoded)
    rows = []
    for label, slot in slots:
        destination = usage_indices[image.qword(slot)]
        values = by_destination[destination]
        assert len(values) == 1, (label, len(values))
        encoded = next(iter(values))
        kind, index = encoded >> 29, encoded & 0x1FFFFFFF
        row = {'label': label, 'slot': hex(slot), 'destination': destination,
               'encoded': hex(encoded), 'kind': kind, 'index': index}
        if kind in (1, 2):
            row['type'] = metadata.type_name(index)
        elif kind == 3:
            offset = metadata.layout['methods_offset'] + index * 32
            row['method'] = (metadata.definition_name(metadata.integer(offset + 4)) + '.' +
                             metadata.string(metadata.integer(offset)))
        else:
            row['bindingStatus'] = 'encoded_reference_preserved_not_resolved'
        rows.append(row)
    labels = {row['label']: row for row in rows}
    append_order = [
        ('component_sp30', '0x1676414'), ('component_sp28', '0x16764dc'),
        ('component_sp20', '0x1676594'), ('component_sp18', '0x1676648'),
        ('component_sp08', '0x16766fc'), ('component_sp00', '0x16767b4'),
        ('component_sp10', '0x1676868'), ('component_x24', '0x167691c'),
        ('component_sp38', '0x16769d4'),
    ]
    result = {
        'status': 'original_static_conditional_delegate_construction_order',
        'slots': rows,
        'conditionalAppendOrder': [
            {'ordinal': i + 1, 'local': label, 'type': labels[label]['type'],
             'delegateCombineSite': site}
            for i, (label, site) in enumerate(append_order)],
        'limits': [
            'This is construction order when each discovered component exists; it does not prove an instance was present.',
            'No original runtime execution or Animator/global Unity callback order was observed.',
            'Generic component MethodRef slots remain numeric until their generic bindings are recovered.',
        ],
    }
    output = HERE / 'update-controller-type-usage-slots.json'
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(output), 'slots': len(rows),
                      'order': result['conditionalAppendOrder']}))


if __name__ == '__main__':
    main()
