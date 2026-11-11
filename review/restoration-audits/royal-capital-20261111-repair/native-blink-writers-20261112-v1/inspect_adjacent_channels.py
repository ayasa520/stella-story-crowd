"""Read a small set of original adjacent parameter writers and L2D_Eye calls.

The prefab's L2D_Eye name is not evidence of a blink writer. Bind its actual
direct calls through the same original assembly tables and keep unlabelled
generic/indirect calls explicit. Expression and model-transfer methods show
where parameter values can combine, without claiming an observed Animator
state or a global Unity callback order for a recorded character instance.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    assert os.getpriority(os.PRIO_PROCESS, 0) == 19
    assert sorted(os.sched_getaffinity(0)) == [22, 23]
    spec = importlib.util.spec_from_file_location(
        'blink_adjacent_helper', HERE.parent / 'native-bgm-entry-20261112/inspect_native_bgm.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    original = json.loads((HERE / 'blink-writer-update-evidence.json').read_text())
    for row in original['sources']:
        assert receipt(ROOT / row['path']) == row
    image = helper.load_image_reader(HERE.parent / 'visual-low/inspect_native_actor_grammar.py')(
        ROOT / 'data/libil2cpp-offline.so')
    metadata = Metadata((ROOT / 'logs/metadata-decrypted.dat').read_bytes(),
                        json.loads((ROOT / 'lost_in_memories/config/metadata_layout.json').read_text()),
                        json.loads((ROOT / 'logs/metadata-types.json').read_text()))
    names, methods = {}, []
    for module in original['bindingModules']:
        if module['name'] not in ['Assembly-CSharp.dll', 'UnityEngine.CoreModule.dll',
                                  'UnityEngine.AnimationModule.dll']:
            continue
        indexed, rows = helper.index_methods(metadata, image, module)
        for address, labels in indexed.items():
            names.setdefault(address, []).extend(labels)
        methods.extend(rows)
    targets = [
        'L2D_Eye.Init', 'L2D_Eye.SetTargetActive', 'L2D_Eye.<Awake>b__2_1',
        'Live2D.Cubism.Framework.Expression.CubismExpressionController.OnLateUpdate',
        'Live2D.Cubism.Framework.CubismEyeBlinkController..ctor',
        'Live2D.Cubism.Framework.CubismAutoEyeBlinkInput..ctor',
        'Live2D.Cubism.Core.CubismTaskableModel.TryWriteParametersAndParts',
    ]
    selected, calls, text = helper.disassemble_targets(image, names, methods, targets)
    trace = HERE / 'adjacent-channel-capstone.txt'
    with trace.open('x') as stream:
        stream.write(text)
    owners = {row['owner'] for row in selected}
    evidence = {
        'status': 'bounded_static_adjacent_channels_not_runtime_trace',
        'sources': original['sources'], 'selectedMethods': selected, 'calls': calls,
        'declarations': [metadata.declaration(i, True)
                         for i in range(metadata.layout['type_count'])
                         if metadata.definition_name(i) in owners],
        'disassembly': receipt(trace),
        'limits': ['No recorded instance execution or generic runtime creation was observed.',
                   'Method extent is a next-indexed-method upper bound, not a size symbol.',
                   'No global Unity/Animator execution order is inferred from direct-call names.'],
    }
    for row in original['sources']:
        assert receipt(ROOT / row['path']) == row
    output = HERE / 'adjacent-channel-evidence.json'
    with output.open('x') as stream:
        json.dump(evidence, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'evidence': receipt(output), 'trace': receipt(trace),
                      'methods': len(selected), 'calls': len(calls)}))


if __name__ == '__main__':
    main()
