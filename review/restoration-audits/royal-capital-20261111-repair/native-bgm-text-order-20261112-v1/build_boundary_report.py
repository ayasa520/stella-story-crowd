"""Collect the bounded supplement as conditional facts, not a player patch.

The original HTML producer, native request dispatcher and native Director
continuation strategy are separate evidence paths. The report preserves that
distinction and the invalid-slot attempt, and never promotes a loading timing
observation into a recovered command phase, Wait or unconditional completion
order. All existing inputs remain immutable; only fresh adjacent files appear.
"""

import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parent
ROOT = next(parent for parent in OUT.parents if (parent / 'data/libil2cpp-offline.so').exists())
R = OUT.parent


def ref(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def write(name, value):
    path = OUT / name
    with path.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return ref(path)


def main():
    bgm = load_module('bounded_report_native', R / 'native-bgm-entry-20261112/inspect_native_bgm.py')
    image = bgm.load_image_reader(R / 'visual-low/inspect_native_actor_grammar.py')(ROOT / 'data/libil2cpp-offline.so')
    inherited = json.loads((R / 'native-motion-entry-20261111/entry-order-evidence.json').read_text())
    from lost_in_memories.tools.metadata import Metadata
    metadata = Metadata((ROOT / 'logs/metadata-decrypted.dat').read_bytes(),
        json.loads((ROOT / 'lost_in_memories/config/metadata_layout.json').read_text()),
        json.loads((ROOT / 'logs/metadata-types.json').read_text()))
    module = next(row for row in inherited['modules'] if row['name'] == 'Assembly-CSharp.dll')
    _, methods = bgm.index_methods(metadata, image, module)
    context_signatures = [row for row in methods if row['qualified'] == 'Stella.Context.WaitFrame']
    declarations = []
    for n in range(metadata.layout['type_count']):
        name = metadata.definition_name(n)
        if name in ['Stella.ScriptSystem.ScriptManager', 'Stella.Scenes.ADV2.Director', 'Stella.Scenes.ADV2.Director+Phase']:
            declarations.append(metadata.declaration(n, True))
    actions = {0x17122D0: 'Optional image: GetImageAssetName then CardSetImage/NextStep',
               0x171238C: 'CardIn then Wait(NextStep)', 0x1712328: 'ExecCommand(1, NextStep)',
               0x1712368: 'SetTextPanel(null) then Wait(NextStep)', 0x17122F4: 'ExecCommand(2, NextStep)',
               0x17123A0: 'StartUserOperation(NextStep)', 0x17123DC: 'ChangePhase(3)'}
    tables = []
    for name, address, count in [('Director.Main_Init scenario-type branch', 0x22DC750, 6),
                                 ('Director.Card_Init step branch', 0x22DC77C, 7),
                                 ('Director.NextStep phase-minus2 branch', 0x22DC798, 5)]:
        rows = []
        for n in range(count):
            offset = struct.unpack_from('<i', image.raw, image.offset(address) + n * 4)[0]
            target = address + offset
            rows.append({'index': n, 'relativeInt32': offset, 'target': hex(target), 'boundedAction': actions.get(target)})
        tables.append({'name': name, 'tableVA': hex(address), 'entries': rows})
    card = tables[1]['entries']
    assert [row['target'] for row in card] == ['0x17122d0', '0x171238c', '0x1712328', '0x1712368', '0x17122f4', '0x17123a0', '0x17123dc']
    html_path = ROOT / 'logs/adv.html'; html = html_path.read_text().splitlines()
    excerpts = []
    for a, b, purpose in [(1295, 1327, 'Per-call next resolver storage'), (1378, 1393, 'Native-facing window.next callback'),
        (1573, 1583, 'Phase0 Exec1st awaits Exec(command0)'), (2179, 2193, 'HTML SetBG is conditional on card state'),
        (2233, 2250, 'TextPanel request is awaited by PanelSequence'), (2563, 2574, 'SendScenarioID returns app.turn Promise'),
        (2597, 2613, 'CardIn request is awaited'), (2727, 2738, 'CardSetBG request producer'),
        (6031, 6048, 'App.turn delegates to Toroste'), (6681, 6729, 'Independent callId/wait per Toroste.turn'),
        (6747, 6753, 'Unity.call producer'), (7000, 7035, 'PlayScenario does not yield SendScenarioID, then awaits phase0/card procedure'),
        (7216, 7255, 'HTML ordinary CardProc await chain')]:
        excerpts.append({'firstLine': a, 'lastLine': b, 'purpose': purpose, 'text': '\n'.join(html[a-1:b])})
    html_receipt = write('original-html-await-and-request-excerpts.json', {'source': ref(html_path), 'excerpts': excerpts,
        'limit': 'Original script contents prove producer/await structure. The exact deployment/Unity.call receiving route for the reference recording is not dynamically established.'})
    inputs = [ROOT / 'data/libil2cpp-offline.so', ROOT / 'logs/metadata-decrypted.dat',
        ROOT / 'logs/metadata-types.json', ROOT / 'lost_in_memories/config/metadata_layout.json', html_path,
        R / 'native-bgm-entry-20261112/REPORT.md', R / 'native-motion-entry-20261111/entry-order-native-capstone.txt']
    sources = [ref(path) for path in inputs]
    passes = sorted(OUT.glob('text-boundary-*-evidence.json'))
    witnesses = [ref(path) for path in passes] + [ref(path) for path in sorted(OUT.glob('*-capstone.txt'))]
    numeric = R / 'audio/p25-p26-bgm-evidence-v1/p25-every06-envelope-v1/executable-memory-v2/actual-loading-text-original-entry-limits.json'
    facts = [
        {'id': 'html-producers', 'basis': 'logs/adv.html7006,7011,7216–7237; original-html-await-and-request-excerpts.json',
         'proved': 'The HTML submits SendScenarioID without yielding its returned Promise. It does yield phase0, then ordinary CardProc yields conditional SetBG/SetImage, CardIn, phase1, TextPanel completion, phase2.',
         'condition': 'This original HTML implementation is the executing producer path; SetBG is requested only for cardState Out or Stay.'},
        {'id': 'native-dispatch-not-a-resource-barrier', 'basis': 'pass2 ScriptManager.Update0x159e9e8..0x159ebf8; pass1 ReturnSuccess; pass6 ResetReturnSuccess/SetReturnCallback',
         'proved': 'The native request-drain loop has no branch on the ReturnSuccess flag+0x70. A separate later block checks isWait+0x80 and isReturn+0x70 before scheduling Context.WaitFrame with the registered callback.',
         'condition': 'Only native dispatch-loop behavior is stated. It does not determine which later requests JS has produced or awaited.'},
        {'id': 'native-director-explicit-gate', 'basis': 'pass5 Main_Init0x1711c30,0x1711c6c; Wait0x1711db0; pass6 SetReturnCallback; slot0x2cfb8a8=Director.NextStep',
         'proved': 'Director.Main_Init step0 directly calls SendScenarioID and installs Wait(NextStep). NextStep resets the completion flag and step1 calls ExecCommand(0). This native continuation path has an explicit completion gate despite the separate HTML non-yield call.',
         'condition': 'The native Director route is executing. The shared isReturn latch is not a per-request correlation proof; unrelated pending completions were not measured.'},
        {'id': 'background-init-bgm-submission', 'basis': 'Inherited SendScenarioID0x124d588→SetBG; slot0x2cad600 bound callback; inherited callback0x1251328→InitScenario; pass1/2 BG coroutine; archived BGM loader audit',
         'proved': 'The bound SendScenarioID background callback calls InitScenario in its own invocation. Within InitScenario ordinary setup submits BGM before SetLive2D and then returns; the background callback subsequently calls ReturnSuccess. Texture SetBG coroutine waits load-count/busy conditions before invoking its supplied callback.',
         'condition': 'The matched SendScenarioID background completion supplies the continuation signal. Empty-background paths may invoke completion inline; actual latency and the prefab branch timing remain conditional.'},
        {'id': 'native-card-text-step-order', 'basis': 'pass5 Director.Card_Init plus exact jump table0x22dc77c',
         'proved': 'Decoded Card steps are optional image→CardIn+Wait→Exec1→SetTextPanel(null)+Wait→Exec2→user operation→phase change. It does not call a BGM-load wait in the inspected step chain.',
         'condition': 'Ordinary native Director.Card phase after the preceding native Main steps.'},
        {'id': 'native-text-start-and-completion', 'basis': 'pass1 SetTextPanel0x1250638→UI.ShowTextPanel; pass2 View.ShowTextPanel0x1688e88→TextPanel.Open; pass3 Open/PlayText; pass4 StartTextAnim/Update; bound completion slots0x2cf0690/0x2c98a68',
         'proved': 'UI.ShowTextPanel requests ordinary/full voice, then View.ShowTextPanel→TextPanel.Open. Open selects immediate SetText or PlayText; PlayText selects SetAllText or StartTextAnim according to speed/options. Normal text update is gated by CanPlay and advances using Unity deltaTime. Its completion closure reaches UI completion, then SetTextPanel closure→ReturnSuccess.',
         'condition': 'HasText and skip/speed/option branches determine the specific visible-text path. A method call is not an exact first-glyph timestamp.'},
        {'id': 'music-completion-not-in-shown-text-gate', 'basis': 'Archived native-bgm-entry SetupBGM→PlayBGM→Loader.Download→success CrossFade and new native Director/text chain',
         'proved': 'No shown Director Main/Card or TextPanel gate waits for the BGM loader success/CrossFade callback. The setup submission and actual music-play completion therefore remain distinct events.',
         'condition': 'This is a bounded static-chain statement, not proof that every independent resource always completes in a particular order.'}]
    limits = [
        'No original game/browser or device instrumentation was run; the reference recording route selection between native Director and the archived HTML producer is not dynamically established.',
        'The exact binding from the archived HTML Unity.call to a native API function-table entry for TextPanel/CardSetBG was not established. The separately proved native Director direct-call path must not be silently relabelled as that JS bridge.',
        'Native queue dispatch does not by itself prove JS continuation. The HTML awaits and native Director completion waits are documented separately.',
        'Director uses a global completion latch. The shown matched callback chain is its intended signal, but complete concurrency/request-correlation and stale-callback cancellation semantics were not audited.',
        'BGM success, model asset creation, background texture/prefab load, CardIn and text-layout completion are not a universally ordered set. Inline/cache-ready callbacks and delayed callbacks are both possible; their actual timing was not measured here.',
        'Unlabelled generic MethodRef usage kinds remain numeric, including the worklist helper at slot0x2d09c88. No guessed generic/assembly binding is substituted.',
        'This evidence does not authorize removing every await, starting text before all prerequisites, adding a phase/Wait/PlayBGM command, or writing a native BGM CSV/fade/reset flag.',
        'The old BGM REPORT website paragraph describes an earlier implementation. Current372 already uses shared game-clock gain, as the separately bound actual two-variant capture demonstrates; old evidence is preserved unchanged.']
    result = {'version': 1, 'status': 'bounded_original_text_and_card_start_edges_audited_no_runtime_or_field_change',
        'reviewer': '/root/p15_p16_voice_evidence', 'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sources': sources, 'htmlRequestExcerpts': html_receipt, 'newNativeWitnesses': witnesses,
        'targetedRegistrationXrefs': ref(OUT / 'targeted-command-registration-xrefs.json'),
        'assemblyBindings': [module], 'nativeDeclarations': declarations, 'contextWaitFrameSignatures': context_signatures,
        'decodedJumpTables': tables, 'facts': facts, 'limits': limits,
        'retainedProbeFailure': {'failureLog': ref(OUT / 'pass3-invalid-slot-probe.log'),
            'partialDump': ref(OUT / 'text-boundary-pass3-capstone.txt'), 'reason': 'Supplied VA0x2d090c88 was outside ELF load segments; intended adrp+offset is0x2d09c88.',
            'correctedEvidence': ref(OUT / 'text-boundary-pass3-corrected-evidence.json'), 'originalPartialOutputOverwritten': False},
        'relatedCurrentMemoryObservation': ref(numeric),
        'outcome': {'independentBgmLoaderCompletionNotAnInspectedTextPrerequisite': True,
            'nativeDirectorBackgroundInitCompletionGateExists': True, 'htmlNonYieldIsNotUniversalNoWaitProof': True,
            'universalNativeResourceCompletionOrderProven': False, 'runtimeImplementationChangeApproved': False,
            'newNativeFieldsApproved': False, 'browserOpened': False, 'originalProcessStarted': False}}
    evidence = write('boundary-supplement-evidence.json', result)
    rollback = write('revert native BGM text boundary supplement.json', {'status': 'new_directory_only_old_evidence_untouched',
        'createdEvidence': evidence, 'preservedFailedProbe': result['retainedProbeFailure'],
        'oldReportBeforeSha256': ref(R / 'native-bgm-entry-20261112/REPORT.md'),
        'originalHtml': ref(html_path), 'originalSo': sources[0],
        'revertInstruction': 'If explicitly asked to revert this audit, exclude only this new native-bgm-text-order-20261112 directory. No original script/binary/metadata, old receipt, website, registry or native scene was modified.'})
    print(json.dumps({'evidence': evidence, 'rollback': rollback, 'facts': len(facts),
        'nativeCardSteps': [row['boundedAction'] for row in card], 'runtimeChangeApproved': False}))


if __name__ == '__main__':
    main()
