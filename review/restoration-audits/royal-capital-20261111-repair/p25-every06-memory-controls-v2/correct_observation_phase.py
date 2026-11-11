"""Preserve the unrun draft and emit a corrected passive observation stage.

The predecessor7 observer subscribes before8 starts its ramp. A synchronous
read in that earlier subscriber would observe the previous gain with the new
frame clock. Queueing a microtask leaves production listener order untouched
and reads only after the current shared-clock callback has finished all its
synchronous listeners. Both snapshots and generation identities are retained;
a mismatch is evidence, never a reason to replace the measured gain.
"""

import difflib
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'story_crowd_data/native/scenes/10170002.json').exists())


def receipt(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def main():
    path = OUT / 'capture-memory-loading.js'; old = path.read_text()
    text = once(old, 'const unsubscribe=m.clock.subscribe(()=>{', '''const unsubscribe=m.clock.subscribe(triggerSnapshot=>{
          const triggerAt=performance.now(),triggerGeneration=m.generation;
          // This subscriber existed before the real ramp subscriber. Do not
          // read a pre-ramp gain and label it with the current frame. The
          // microtask runs after this clock tick's synchronous listeners, with
          // no production listener reordered and no clock/gain/media write.
          queueMicrotask(()=>{
          if(a.closed)return;
          const observedSnapshot=m.clock.snapshot();
          const sameSharedFrame=triggerSnapshot.frame===observedSnapshot.frame;
          const sameGameSeconds=triggerSnapshot.gameSeconds===observedSnapshot.gameSeconds;
          if(!sameSharedFrame||!sameGameSeconds)a.notes.push({kind:'observation_frame_mismatch',triggerSnapshot,observedSnapshot});''')
    text = once(text, "a.samples.push({...snap(),generation:m.generation,", "a.samples.push({...snap(),observationStage:'microtask_after_shared_clock_synchronous_listeners',triggerSnapshot:{...triggerSnapshot},observedSnapshot,sameSharedFrame,sameGameSeconds,triggerAt,triggerGeneration,generationUnchanged:triggerGeneration===m.generation,generation:m.generation,")
    text = once(text, "cardOpacity:getComputedStyle(document.querySelector('#cardMotion')).opacity});\n        });", "cardOpacity:getComputedStyle(document.querySelector('#cardMotion')).opacity});\n          });\n        });")
    text = once(text, "const onTiming=event=>a.timing.push({...snap(),detail:{...event.detail}});", "const onTiming=event=>a.timing.push({...snap(),observationStage:'synchronous_player_timing_event',detail:{...event.detail}});")
    text = once(text, "a.remove=()=>{unsubscribe();document.removeEventListener('stella-player-timing',onTiming);};", "a.remove=()=>{a.closed=true;unsubscribe();document.removeEventListener('stella-player-timing',onTiming);};")
    corrected = OUT / 'capture-memory-loading-phase-corrected.js'
    with corrected.open('x') as stream:
        stream.write(text)
    with (OUT / 'probe-phase-correction.diff').open('x') as stream:
        stream.write(''.join(difflib.unified_diff(old.splitlines(True), text.splitlines(True),
            fromfile='unrun-v2/capture-memory-loading.js', tofile='capture-memory-loading-phase-corrected.js')))
    plan = json.loads((OUT / 'execution-plan.json').read_text())
    plan['supersedesUnrunPlan'] = receipt(OUT / 'execution-plan.json')
    plan['probe'] = receipt(corrected)
    plan['probeObservationPhase'] = {
        'oldUnrunIssue': 'Observer registered at7 precedes ramp registered at8; a synchronous sample would read pre-ramp gain with the new frame clock.',
        'phase': 'microtask_after_shared_clock_synchronous_listeners',
        'method': 'Subscription only queues a read-only microtask. Trigger/observed snapshots and generations are retained, and pending reads stop after teardown.',
        'requiredAudit': ['sameSharedFrame=true', 'sameGameSeconds=true', 'generationUnchanged=true for gain-formula comparisons',
            'observed gain is always the real MusicVoice volume; no value is fabricated or substituted'],
        'limit': 'This is after one shared-clock tick synchronous listener list, not after every asynchronous operation in the browser frame.'}
    plan['rootOnlyExecutionArgv'] = ['nice', '-n', '19', 'taskset', '-c', '22,23', 'playwright-cli',
        '-s=p25-every06-memory-v37', '--raw', 'run-code', '--filename=' + str(corrected)]
    target = OUT / 'execution-plan-phase-corrected.json'
    with target.open('x') as stream:
        stream.write(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'plan': receipt(target), 'probe': receipt(corrected), 'packetUnchanged': plan['fixture'], 'registryProposalUnchanged': plan['registryEntryProposal']}))


if __name__ == '__main__':
    main()
