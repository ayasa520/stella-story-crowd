"""Check four existing cue PCMs in one seven-second source window.

Only existing PCM and original metadata are read. No decoder, separation,
audio playback, whole-bank correlation, media export or installer is invoked.
Waveform coordinates identify a cue; they are not authored trigger offsets.
"""
import ast
import json
import os
from pathlib import Path
import resource
import struct
import wave

# Bound this process and any accidental child before loading numerical code.
# RLIMIT_NICE=1 permits nice19 only; affinity and thread limits come from launch.
resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
if os.getpriority(os.PRIO_PROCESS, 0) != 19 or sorted(os.sched_getaffinity(0)) != [0, 1]:
    raise RuntimeError("Run with nice19 and CPU0,1")
import numpy as np
from story_studio.recovery.audio_correlation import WaveformCorrelation

ROOT = Path('/home/rikka/Projects/stella')
HERE = Path(__file__).resolve().parent
REPAIR = HERE.parent
RATE = 4000
WINDOW = (581, 588)
BANK, CUE = 'vo_adv_elsa', 'advg_elza_warai'
REFERENCES = [(BANK, CUE), (BANK, 'advk_elza_kougeki02'),
              ('vo_adv_subaru', 'advg_subaru_douyou'),
              ('vo_adv_subaru', 'advk_subaru_kirare')]

def read_pcm(path, start=0, end=None):
    with wave.open(str(path)) as stream:
        layout = dict(channels=stream.getnchannels(), sampleBytes=stream.getsampwidth(),
                      rate=stream.getframerate(), frames=stream.getnframes())
        assert layout['channels'] == 1 and layout['sampleBytes'] == 2
        left = round(start * layout['rate'])
        right = layout['frames'] if end is None else round(end * layout['rate'])
        stream.setpos(left)
        pcm = np.frombuffer(stream.readframes(right-left), '<i2').astype(np.float64)/32768
        assert len(pcm) == right-left
    return pcm, layout

def to_4k(pcm, original_rate):
    assert original_rate in (32000, 48000) and original_rate % RATE == 0
    # Match the earlier independent Julius check: symmetric compensated
    # low-pass filtering followed by exact integer decimation preserves cue0.
    positions = np.arange(-64, 65)
    kernel = (2*1800/original_rate * np.sinc(2*1800/original_rate*positions)
              * np.hamming(129))
    kernel /= kernel.sum()
    return np.convolve(pcm, kernel, mode='same')[::original_rate//RATE]

# Evaluate only the existing pure @UTF parser definition, avoiding decoder or
# media-export module initialization. The complete resolved chain is retained.
parser = ROOT/'story_studio/recovery/cri_audio.py'
definition = next(n for n in ast.parse(parser.read_text()).body
                  if isinstance(n, ast.FunctionDef) and n.name == 'utf_table')
scope = {'struct': struct}
exec(compile(ast.Module(body=[definition], type_ignores=[]), str(parser), 'exec'), scope)
utf = scope['utf_table']
original = ROOT/'data/extracted_archives/original/com.sega.stella/files/AssetBundle/assets'
acb_path, awb_path = original/(BANK+'.acb'), original/(BANK+'.awb')
header = utf(acb_path.read_bytes())[0]
table = lambda key: utf(header[key])
name = next(row for row in table('CueNameTable') if row['CueName'] == CUE)
cue = table('CueTable')[name['CueIndex']]
assert cue['ReferenceType'] == 3
sequence = table('SequenceTable')[cue['ReferenceIndex']]
assert sequence['Type'] == 0 and sequence['NumTracks'] == 1 and len(sequence['TrackIndex']) == 2
track_index = int.from_bytes(sequence['TrackIndex'], 'big')
track = table('TrackTable')[track_index]
event = table('TrackEventTable')[track['EventIndex']]['Command']
assert len(event) == 10 and event[:5] == bytes.fromhex('07d0040002') and event[7:] == b'\0\0\0'
synth_index = int.from_bytes(event[5:7], 'big')
synth = table('SynthTable')[synth_index]
assert synth['Type'] == 0 and len(synth['ReferenceItems']) == 4 and synth['ReferenceItems'][:2] == b'\0\1'
wave_index = int.from_bytes(synth['ReferenceItems'][2:], 'big')
waveform = table('WaveformTable')[wave_index]
assert waveform['Streaming'] == 1
with awb_path.open('rb') as stream:
    prefix = stream.read(16)
    assert prefix[:4] == b'AFS2'
    offset_width, id_width = prefix[5:7]
    count, alignment = struct.unpack_from('<IH', prefix, 8)
    ids_raw, offsets_raw = stream.read(count*id_width), stream.read((count+1)*offset_width)
    ids = [int.from_bytes(ids_raw[i*id_width:(i+1)*id_width], 'little') for i in range(count)]
    offsets = [int.from_bytes(offsets_raw[i*offset_width:(i+1)*offset_width], 'little') for i in range(count+1)]
    selected_entry = ids.index(waveform['StreamAwbId'])
    selected_begin = (offsets[selected_entry]+alignment-1)//alignment*alignment
    selected_end = offsets[selected_entry+1]
    stream.seek(selected_begin)
    selected_prefix = stream.read(8)  # Header prefix only; no compressed-audio decode.

member = f'LIMEOS/audio/{BANK}/{CUE}.wav'
extracted = ROOT/'data/extracted_archives/limeos'/member
old_copy = REPAIR/'audio/waveform-graphs/p30-d7d29c63dc09/audible-review/native'/BANK/(CUE+'.wav')
assert old_copy.read_bytes() == extracted.read_bytes()
native_pcm, native_layout = read_pcm(extracted)
assert native_layout['rate'] == waveform['SamplingRate'] == 48000
assert native_layout['frames'] == waveform['NumSamples']
assert native_layout['channels'] == waveform['NumChannels'] == 1
catalog = json.loads((ROOT/'story_crowd_data/assets/catalog.json').read_text())
published_bank = catalog['voices'].get(BANK)
published_cue = next((row for row in (published_bank or {}).get('cues', []) if row['cue'] == CUE), None)
installed = ROOT/f'story_crowd_data/assets/voices/{BANK}/{CUE}.wav'

source_path = REPAIR/'p30-bgm-identification-20261113-v1/p30-original-source.wav'
source, source_layout = read_pcm(source_path, *WINDOW)
assert source_layout['rate'] == RATE
source -= source.mean()
comparisons = []
settings = dict(backend='cpu', query_fft_cache_bytes=8388608,
                memory_limit_bytes=67108864, fft_plan_cache_bytes=0)
with WaveformCorrelation(settings) as compute:
    signal = compute.signal(source, 1 << (len(source)+8000-2).bit_length())
    def measure(label, template, cue_offset=0):
        template = template.copy()
        template -= template.mean()
        query = compute.query(template, float(np.dot(template, template)))
        scores = compute.scores(signal, query)
        values = []
        for at, score in compute.peaks(scores.copy(), 5, 0, round(.4*RATE)):
            block = source[at:at+len(template)]
            centered = block-block.mean()
            signed = float(np.dot(centered, template)/np.sqrt(np.dot(centered, centered)*query.energy))
            values.append(dict(cueZeroPcmSeconds=WINDOW[0]+at/RATE-cue_offset,
                               templateStartPcmSeconds=WINDOW[0]+at/RATE,
                               absoluteNcc=score, signedNcc=signed))
        item = dict(label=label, templateStartInCueSeconds=cue_offset,
                    templateDuration=len(template)/RATE, peaks=values)
        comparisons.append(item)
        return item
    active_reference = None
    for bank, cue_name in REFERENCES:
        pcm, layout = read_pcm(ROOT/f'data/extracted_archives/limeos/LIMEOS/audio/{bank}/{cue_name}.wav')
        converted = to_4k(pcm, layout['rate'])
        active = np.flatnonzero(np.abs(converted) >= np.max(np.abs(converted))*.02)
        left = max(0, int(active[0])-round(RATE*.025))
        right = min(len(converted), int(active[-1])+round(RATE*.025)+1)
        measure(bank+'/'+cue_name+'-active', converted[left:right], left/RATE)
        if bank == BANK and cue_name == CUE:
            measure(bank+'/'+cue_name+'-whole-existing-cue', converted)
            active_reference = converted[left:right], left
    active, left = active_reference
    # Three disjoint pieces check equivalent cue0 independently; retain their
    # off-time peaks as well, rather than reporting only the winning match.
    borders = [0, len(active)//3, len(active)*2//3, len(active)]
    for i in range(3):
        a, b = borders[i:i+2]
        measure(CUE+f'-piece{i+1}', active[a:b], (left+a)/RATE)

result = dict(schema='stella.p30_next_voice_bounded_check.v1',bank=BANK,cue=CUE,
    sourcePcm=str(source_path),sourceLayout=source_layout,sourceWindowPcmSeconds=WINDOW,
    referencePcm=str(extracted),referenceLayout=native_layout,oldNativeCopy=str(old_copy),oldCopyByteEqual=True,
    referenceResampling='129-tap symmetric Hamming sinc cutoff1800Hz, compensated same convolution, exact decimation48k/12 or32k/8 to4kHz',
    nativeBinding=dict(acb=str(acb_path),cueName=name,cue=cue,sequenceIndex=cue['ReferenceIndex'],sequence=sequence,
        trackIndex=track_index,track=track,eventHex=event.hex(),synthIndex=synth_index,synth=synth,
        waveformIndex=wave_index,waveform=waveform,awb=str(awb_path),streamId=waveform['StreamAwbId'],
        awbSelectedEntry=selected_entry,awbSelectedBegin=selected_begin,awbSelectedEnd=selected_end,
        selectedPrefixHex=selected_prefix.hex()),
    catalogBankPresent=published_bank is not None,catalogCue=published_cue,
    intendedInstalledPath=str(installed),installedPathPresent=installed.exists(),
    installedBindingVerified=False,comparisons=comparisons,
    computation=dict(nice=os.getpriority(os.PRIO_PROCESS,0),affinity=sorted(os.sched_getaffinity(0)),
        rlimitNice=resource.getrlimit(resource.RLIMIT_NICE),numpy=np.__version__,backend='cpu'),
    sourceVideoDecoded=False,bankWideSearch=False,listeningPerformed=False,
    originalCsvRecovered=False,nativeStartPhaseOffsetGainRecovered=False,rootConfirmed=False)
with (HERE/'measurements38.json').open('x') as output:
    json.dump(result,output,ensure_ascii=False,indent=2,allow_nan=False,
              default=lambda value:value.hex() if isinstance(value,bytes) else str(value))
    output.write('\n')
print(json.dumps([dict(label=r['label'],duration=r['templateDuration'],peaks=r['peaks'][:2]) for r in comparisons],indent=2))
