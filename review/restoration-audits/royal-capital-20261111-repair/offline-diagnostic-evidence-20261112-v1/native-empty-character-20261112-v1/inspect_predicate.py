"""Resolve the original ADV2 actor-presence predicate from exact offline bytes.

Only evidence files next to this script are written. No game, browser, managed
method, Studio source, native scenario or production player is executed/changed.
The result is one conditional native path, not proof of the recording producer.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

BASE = Path(__file__).parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT))
from lost_in_memories.tools.metadata import Metadata

spec = importlib.util.spec_from_file_location(
    'original_actor_grammar', BASE.parent / 'visual-low/inspect_native_actor_grammar.py')
grammar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grammar)
paths = [ROOT / 'data/libil2cpp-offline.so', ROOT / 'logs/metadata-decrypted.dat',
         ROOT / 'lost_in_memories/config/metadata_layout.json', ROOT / 'logs/metadata-types.json']
native = grammar.NativeImage(paths[0])
metadata = Metadata(paths[1].read_bytes(), json.loads(paths[2].read_text()),
                    json.loads(paths[3].read_text()))

# Resolve each token through its own inspected IL2CPP module record. A token
# number reused in mscorlib must never be indexed in the CSharp method table.
modules = {'Assembly-CSharp.dll': dict(record=0x2BF0788, table=0x2EB00D8, count=34806),
           'mscorlib.dll': dict(record=0x2C8F328, table=0x2F17338, count=10567)}
for name, row in modules.items():
    assert native.qword(row['record'] + 8) == row['count']
    assert native.qword(row['record'] + 16) == row['table']
    offset = native.offset(native.qword(row['record']))
    assert native.raw[offset:native.raw.index(b'\0', offset)].decode() == name
owners = {'Stella.Scenes.ADV2.ScenarioUtil': 'Assembly-CSharp.dll',
          'System.String': 'mscorlib.dll'}
bindings, addresses = [], {}
for index in range(metadata.layout['type_count']):
    owner = metadata.definition_name(index)
    if owner not in owners:
        continue
    row = modules[owners[owner]]
    for method in metadata.declaration(index, True)['methods']:
        token = int(method['token'], 16) & 0xFFFFFF
        assert 0 < token <= row['count']
        address = native.qword(row['table'] + (token - 1) * 8)
        if not address:
            continue
        addresses.setdefault(address, []).append(owner + '.' + method['name'])
        if method['name'] in ('HasLive2DChara', 'IsNullOrEmpty'):
            bindings.append(dict(owner=owner, module=owners[owner], address=address, **method))
selected = [row for row in bindings if row['owner'] == 'Stella.Scenes.ADV2.ScenarioUtil' and
            row['name'] == 'HasLive2DChara']
assert len(selected) == 1 and selected[0]['address'] == 0x17179F4
start = selected[0]['address']
end = min(address for address in addresses if address > start)
assert 0 < end - start <= 512
raw = native.raw[native.offset(start):native.offset(start) + end - start]
lines = []
for instruction in Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN).disasm(raw, start):
    labels = []
    if instruction.mnemonic in ('b', 'bl') and instruction.op_str.startswith('#'):
        labels = addresses.get(int(instruction.op_str[1:], 0), [])
    lines.append(f'{instruction.address:#x}: {instruction.mnemonic} {instruction.op_str}' +
                 (' // ' + ', '.join(labels) if labels else '') + '\n')
text = BASE / 'HasLive2DChara-capstone.txt'
assert not text.exists()
text.write_text(''.join(lines))
sources = [dict(file=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
receipt = dict(status='exact_original_predicate_static_bytes_only', sources=sources,
               bindings=bindings, start=hex(start), end=hex(end),
               rawCodeSha256=hashlib.sha256(raw).hexdigest(),
               disassembly=dict(file=str(text), sha256=hashlib.sha256(text.read_bytes()).hexdigest()),
               mainThreadViewedImages=False, browserOpened=False, productionWrites=0,
               recordingProducerProven=False, universalActorInheritanceClaim=False)
output = BASE / 'receipt.json'
assert not output.exists()
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(output=str(output), bytes=len(raw), start=hex(start), end=hex(end))))
