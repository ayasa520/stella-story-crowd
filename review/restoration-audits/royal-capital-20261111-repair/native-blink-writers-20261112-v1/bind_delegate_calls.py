"""Bind the few System calls in UpdateController using original mscorlib.

Use the assembly's own validated code-generation record. A shared numeric
method token in Assembly-CSharp would identify a different method and must
never be used to label these targets. Only selected declarations are read;
this does not enumerate or execute runtime delegates.
"""

import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [22, 23]
    spec = importlib.util.spec_from_file_location(
        'blink_delegate_helper', HERE.parent / 'native-bgm-entry-20261112/inspect_native_bgm.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.load_image_reader(HERE.parent / 'visual-low/inspect_native_actor_grammar.py')(
        ROOT / 'data/libil2cpp-offline.so')
    metadata = Metadata((ROOT / 'logs/metadata-decrypted.dat').read_bytes(),
                        json.loads((ROOT / 'lost_in_memories/config/metadata_layout.json').read_text()),
                        json.loads((ROOT / 'logs/metadata-types.json').read_text()))
    module = {'name': 'mscorlib.dll', 'record': 0x2C8F328,
              'count': 10567, 'table': 0x2F17338}
    name_offset = image.offset(image.qword(module['record']))
    assert image.raw[name_offset:image.raw.index(b'\0', name_offset)].decode() == module['name']
    assert image.qword(module['record'] + 8) == module['count']
    assert image.qword(module['record'] + 16) == module['table']
    selected = {'System.Action': {'.ctor', 'Invoke'},
                'System.Delegate': {'Combine', 'RemoveAll'},
                'System.Object': {'GetType'},
                'System.Type': {'GetTypeFromHandle', 'op_Equality'}}
    bindings, interface = [], None
    for index in range(metadata.layout['type_count']):
        owner = metadata.definition_name(index)
        if owner == 'Live2D.Cubism.Framework.ICubismUpdatable':
            interface = metadata.declaration(index, True)
        if owner not in selected:
            continue
        for method in metadata.declaration(index, True)['methods']:
            if method['name'] not in selected[owner]:
                continue
            ordinal = int(method['token'], 16) & 0xFFFFFF
            assert 0 < ordinal <= module['count']
            bindings.append({'owner': owner, **method, 'module': module['name'],
                             'address': hex(image.qword(module['table'] + (ordinal - 1) * 8))})
    result = {'status': 'original_mscorlib_token_table_bindings_not_runtime_observation',
              'module': {key: hex(value) if key in ['record', 'table'] else value
                         for key, value in module.items()},
              'bindings': bindings, 'interfaceDeclaration': interface}
    output = HERE / 'delegate-call-bindings.json'
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
