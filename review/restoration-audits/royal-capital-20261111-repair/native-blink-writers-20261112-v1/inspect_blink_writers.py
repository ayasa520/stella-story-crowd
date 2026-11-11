"""Inspect bounded original blink writer/update methods, never run a game.

Reuse the assembly-aware entry/BGM inspector and its original method tables.
The output labels real direct branches and retains indirect dispatch sites;
static callable code is not reported as observed execution in Felt15. Missing
serialized AutoEyeBlinkInput/UpdateController instances do not exclude runtime
creation or other writers. No website, native scene or prior receipt is edited.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
from lost_in_memories.tools.metadata import Metadata


def import_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def rec(path):
    raw=path.read_bytes();return {'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    parent=HERE.parent
    helper=import_file('blink_bounded_inspector',parent/'native-bgm-entry-20261112/inspect_native_bgm.py')
    inherited=parent/'native-motion-entry-20261111/entry-order-evidence.json'
    modules=json.loads(inherited.read_text())['modules']
    paths=[ROOT/'data/libil2cpp-offline.so',ROOT/'logs/metadata-decrypted.dat',
           ROOT/'lost_in_memories/config/metadata_layout.json',ROOT/'logs/metadata-types.json']
    old_path=parent/'visual-low/p11-felt15-blink-local-review-v1/original-blink-inventory.json'
    old=json.loads(old_path.read_text());old_sources={row['path']:row['sha256'] for row in old['sources']}
    before=[rec(path) for path in paths]
    assert all(row['sha256']==old_sources[row['path']] for row in before)
    native=helper.load_image_reader(parent/'visual-low/inspect_native_actor_grammar.py')(paths[0])
    metadata=Metadata(paths[1].read_bytes(),json.loads(paths[2].read_text()),json.loads(paths[3].read_text()))
    names={};methods=[]
    for module in modules:
        if module['name'] not in ['Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll']:continue
        indexed,records=helper.index_methods(metadata,native,module)
        for address,labels in indexed.items():names.setdefault(address,[]).extend(labels)
        methods.extend(records)
    targets=[
      'Live2D.Cubism.Framework.CubismEyeBlinkController.Refresh',
      'Live2D.Cubism.Framework.CubismEyeBlinkController.OnLateUpdate',
      'Live2D.Cubism.Framework.CubismEyeBlinkController.LateUpdate',
      'Live2D.Cubism.Framework.CubismAutoEyeBlinkInput.Start',
      'Live2D.Cubism.Framework.CubismAutoEyeBlinkInput.Reset',
      'Live2D.Cubism.Framework.CubismAutoEyeBlinkInput.LateUpdate',
      'Live2D.Cubism.Framework.CubismParameterExtensionMethods.AddToValue',
      'Live2D.Cubism.Framework.CubismParameterExtensionMethods.MultiplyValueBy',
      'Live2D.Cubism.Framework.CubismParameterExtensionMethods.BlendToValue',
      'Live2D.Cubism.Framework.CubismUpdateController.Refresh',
      'Live2D.Cubism.Framework.CubismUpdateController.LateUpdate',
      'Live2D.Cubism.Framework.CubismParameterStore.SaveParameters',
      'Live2D.Cubism.Framework.CubismParameterStore.RestoreParameters',
      'Live2D.Cubism.Core.CubismModel.Update',
      'Live2D.Cubism.Core.CubismModel.OnRenderObject',
      'Live2D.Cubism.Core.CubismModel.ForceUpdateNow',
    ]
    selected,calls,text=helper.disassemble_targets(native,names,methods,targets)
    trace=HERE/'blink-writer-update-capstone.txt'
    with trace.open('x') as stream:stream.write(text)
    owners={method['owner'] for method in selected}|{'Live2D.Cubism.Core.CubismParameter','Live2D.Cubism.Framework.CubismParameterBlendMode'}
    declarations=[metadata.declaration(i,True) for i in range(metadata.layout['type_count']) if metadata.definition_name(i) in owners]
    result={'status':'bounded_original_static_sites_not_runtime_observation','browserOpened':False,'imagesOpened':False,
        'nativeGameRun':False,'sources':before,'inheritedAssemblyTables':rec(inherited),'bindingModules':modules,
        'priorSerializedInventory':rec(old_path),'selectedMethods':selected,'calls':calls,'declarations':declarations,
        'disassembly':rec(trace),'externalKnownCalls':[row for row in methods if row['address'] in {c.get('target') for c in calls}
           and row['owner'].startswith(('UnityEngine.Time','UnityEngine.Animator','UnityEngine.Behaviour'))],
        'limits':['These are actual static writer/call sites, not a trace of the recorded Felt15 instance.',
          'Absent serialized components do not rule out dynamic AddComponent or other field writers.',
          'Method ends are bounded by the next indexed method address, not recovered size symbols.',
          'Indirect delegates/generic helpers remain explicit until their bindings are resolved.',
          'No blink cause, face/body instruction, time offset or website correction is proposed.'],
        'compute':{'nice':os.getpriority(os.PRIO_PROCESS,0),'affinity':sorted(os.sched_getaffinity(0))}}
    assert before==[rec(path) for path in paths]
    output=HERE/'blink-writer-update-evidence.json'
    with output.open('x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'evidence':rec(output),'trace':rec(trace),'methods':len(selected),'calls':len(calls)},ensure_ascii=False))


if __name__=='__main__':main()
