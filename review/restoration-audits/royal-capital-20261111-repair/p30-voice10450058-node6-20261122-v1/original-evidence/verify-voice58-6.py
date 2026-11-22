"""Reuse the existing bounded PCM verifier for exactly one new recorded cue.

The pinned verifier only reads existing PCM and native metadata. Each literal
replacement is counted before execution so template drift cannot silently widen
the window, select another bank, or write outside this agent's artifact folder.
This is evidence collection only: no native/source/API/installer write occurs.
"""
from pathlib import Path
import hashlib

ROOT = Path('/home/rikka/Projects/stella')
REPAIR = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
HERE = Path(__file__).resolve().parent
template = REPAIR / 'p30-next-voice-preflight-20261113-v1/verify38.py'
assert hashlib.sha256(template.read_bytes()).hexdigest() == '4fb78b5d38bfc20a7db1b7609e2ca9a1fed8e651be9f6affd3e3b5201642a9bf'
source = template.read_text()
replacements = {
    'REPAIR = HERE.parent': "REPAIR = ROOT/'data/native_recovery/royal-capital-20261110/repair-20261111'",
    'WINDOW = (581, 588)': 'WINDOW = (811, 818)',
    "BANK, CUE = 'vo_adv_elsa', 'advg_elza_warai'": "BANK, CUE = 'vo_adv_julius', 'advk_julius_emilia'",
    "REFERENCES = [(BANK, CUE), (BANK, 'advk_elza_kougeki02'),\n              ('vo_adv_subaru', 'advg_subaru_douyou'),\n              ('vo_adv_subaru', 'advk_subaru_kirare')]": "REFERENCES = [(BANK, CUE), (BANK, 'advk_julius_anastasia'),\n              (BANK, 'advg_julius_subaru'), (BANK, 'advk_julius_koekake')]",
    "native_layout['rate'] == waveform['SamplingRate'] == 48000": "native_layout['rate'] == waveform['SamplingRate'] == 32000",
    "ROOT/'story_crowd_data/assets/catalog.json'": "ROOT/'artifacts/stella-script-continuation-20261121/data-checkout/assets/catalog.json'",
    "ROOT/f'story_crowd_data/assets/voices/{BANK}/{CUE}.wav'": "ROOT/f'artifacts/stella-script-continuation-20261121/data-checkout/assets/voices/{BANK}/{CUE}.wav'",
    "installedBindingVerified=False": "installedBindingVerified=installed_verified",
    "(HERE/'measurements38.json')": "(HERE/'voice58-6-measurements.json')",
    "result = dict(schema='stella.p30_next_voice_bounded_check.v1'": "assert published_cue['member'] == member\nassert published_cue['url'] == f'voices/{BANK}/{CUE}.wav'\ninstalled_verified = installed.read_bytes() == extracted.read_bytes()\nassert installed_verified\nresult = dict(schema='stella.p30_next_voice_bounded_check.v1'",
}
for old, new in replacements.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new)
exec(compile(source, str(template), 'exec'), {'__file__': str(__file__), '__name__': '__main__'})
