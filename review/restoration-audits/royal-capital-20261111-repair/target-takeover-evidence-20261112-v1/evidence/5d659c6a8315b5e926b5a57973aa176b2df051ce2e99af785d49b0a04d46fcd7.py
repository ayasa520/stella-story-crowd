"""Archive a bounded independent P30 identity review without editing story data.

Allocation uses the actual current native type-2 rows and explicit P30 review
recordings across the five mapped scenes. It is metadata coverage only: no image
outside ordinals 15--29 is opened or claimed reviewed by this work. Images for
those fifteen witnesses were opened directly by /root/p30_packet_preflight.
Names, dialogue, static poses, portrait panels and resource availability cannot
choose an unresolved costume variant. Acting always needs the full original
entry/action/hold/next-boundary sequence and independently mapped native commands.
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/rikka/Projects/stella')
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
DATA = ROOT / 'story_crowd_data'
OUT = Path(__file__).parent
REVIEWER = '/root/p30_packet_preflight'
P = R / 'visual-high/agent-reviewed-p30-first15-identity-v1'
checked = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    path = Path(path)
    if path not in checked:
        value = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                value.update(block)
        checked[path] = dict(file=str(path), sha256=value.hexdigest(), bytes=path.stat().st_size)
    return checked[path]


def write(name, value):
    path = OUT / name
    require(not path.exists(), f'Use a fresh output, refusing overwrite: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return ref(path)


def git(*args):
    return subprocess.check_output(['git', '-C', str(DATA), *args], text=True).strip()


head = git('rev-parse', 'HEAD')
manifest_raw = (DATA / 'manifest.json').read_bytes()
ownership_raw = (DATA / 'review/native-restoration.json').read_bytes()
ownership = json.loads(ownership_raw)
mapping_path = P / 'p30-actual-scene-recording-mapping.json'
mapping = json.loads(mapping_path.read_text())
source_index_path = Path(mapping['originalSourceIndex']['file'])
require(ref(source_index_path)['sha256'] == mapping['originalSourceIndex']['sha256'], 'Index changed')
index = json.loads(source_index_path.read_text())
events = {event['id']: event for event in index['events']}
video = mapping['sourceVideo']
require(ref(video['file']) == video, 'Original video differs')
rows, sources, native_by_scene, review_by_scene = [], [], {}, {}
for part_scene in mapping['currentSceneSegments']:
    scene = part_scene['sceneId']
    for kind, storage in [('native', native_by_scene), ('review', review_by_scene)]:
        path = DATA / f'{kind}/scenes/{scene}.json'
        raw = path.read_bytes()
        require(digest(raw) == ownership['files'][f'{kind}/scenes/{scene}.json'], 'Owned file guard differs')
        storage[scene] = json.loads(raw)
        target = OUT / f'source-snapshots/{kind}-scene-{scene}.json'
        require(not target.exists(), 'Snapshot already exists')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        sources.append(dict(sourceFile=str(path), rawSnapshot=ref(target),
                            sourceAtHead=head, sourceSha256=digest(raw)))
    review = review_by_scene[scene]
    require(part_scene['currentSceneSegment'] in review['sceneSegments'], 'Current scene mapping differs')
    for row in native_by_scene[scene]['scenario_list']:
        number = row['scenario_id']
        node = review['scenarios'][str(number)]
        recordings = [item for item in node.get('recordings', [])
                      if item.get('recordingId') == 'bili-capital-30']
        if row['scenario_type'] == 2 and recordings:
            require(len(recordings) == 1, 'P30 node source recording is not unique')
            rows.append(dict(ordinal=len(rows), sceneId=scene, scenarioId=number,
                             stableKey=node['stableKey'], sourceText=node['sourceText'],
                             sourceSpeakerInformationalOnly=node.get('sourceSpeaker'),
                             recording=recordings[0], currentCharacter=row['character']))
require(len(rows) == 161, 'Whole metadata observation count differs')
allocation_ref = write('allocation.json', dict(schema='stella.target_recording_allocation.v1',
    recordingPart=30, recordingId='bili-capital-30', dataHead=head,
    sourceMapping=ref(mapping_path), metadataOnly=True, observations=rows,
    rows={row['stableKey']: dict(sceneId=row['sceneId'], scenarioId=row['scenarioId']) for row in rows},
    totalObservations=161, boundedImageReviewOrdinals=list(range(15, 30))))
provenance_ref = write('source-snapshot-provenance.json', dict(schema='stella.raw_source_snapshot_provenance.v1',
    reviewer=REVIEWER, gitCommitObservedBefore=head, files=sources,
    sourceOwnershipSha256=digest(ownership_raw), sourceManifestSha256=digest(manifest_raw),
    scope='All five P30 native/review files are metadata snapshots; image review is restricted to ordinals15–29.',
    formalWrites=False))

observations = []
for row in rows[15:30]:
    recording = row['recording']
    event = events[recording['ocrEventId']]
    require(recording['start'] <= event['time'] <= recording['end'], 'Event outside current node interval')
    require(event['source_sha256'] == video['sha256'], 'Event source video differs')
    frame = ref(event['frame'])
    observations.append(dict(ordinal=row['ordinal'], sceneId=row['sceneId'], scenarioId=row['scenarioId'],
        stableKey=row['stableKey'], sourceText=row['sourceText'],
        sourceSpeakerInformationalOnly=row['sourceSpeakerInformationalOnly'], recordingPart=30,
        recordingId='bili-capital-30', time=event['time'], sourceFrameTime=event['source_frame_time'],
        sourceFrameIndex=event['frame_index'], sourceIndex=ref(source_index_path),
        sourceEventId=event['id'], frame=frame['file'], frameSha256=frame['sha256'],
        video=video['file'], videoSha256=video['sha256'], fullFrame=True, crop=None,
        originalEvidence=recording, expectedCharacterAtSnapshot=row['currentCharacter'],
        directImageReview=True, reviewer=REVIEWER,
        timeBasis='Existing original source-index event inside the exact current node recording interval'))
observations_ref = write('observation-evidence.json', observations)

catalog_path = DATA / 'assets/catalog.json'
catalog_raw = catalog_path.read_bytes()
catalog = json.loads(catalog_raw)
model_refs = {}
for model in ['felt01', 'rom01']:
    token = 'live2d/AC_' + model
    binding_path = R / f'visual-high/agent-reviewed-p29-identity-v1/{model}-assembled-original-binding.json'
    binding = json.loads(binding_path.read_text())
    current = catalog['models'][token]
    current_canonical = digest(json.dumps(current, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    require(current_canonical == binding['catalogModelEntryCanonicalSha256'], 'Current model row differs')
    anchor = binding['anchor']
    require(ref(anchor['file']) == anchor, 'Exact model anchor changed')
    for item in binding['originalFiles'] + binding['installedModelFiles']:
        require(ref(item['file'])['sha256'] == item['sha256'], 'Original/model binding changed')
    model_refs[model] = dict(nativeToken=token, assembledReferenceBinding=ref(binding_path),
        directlyViewedReference=anchor, currentFullCatalogRow=write(f'{model}-current-complete-catalog-row.json', current),
        currentFullCatalogRowCanonicalSha256=current_canonical,
        actualAttribution=binding['actualAttribution'], historicalTrialAccepted=False,
        scope='Exact costume identity only; no acting, geometry, lighting, CSV, timing or playback acceptance.')
references_ref = write('current-positive-reference-revalidation.json', dict(
    reviewer=REVIEWER, currentCatalogSha256=digest(catalog_raw), models=model_refs,
    sourceReferenceReview='Both exact raw canvas anchors were directly viewed by this reviewer earlier in the same active P30 target preflight.',
    originalReferenceReviewReceipt=ref(R/'target-p30-first15-preflight-20261112-v1/receipt.json'),
    browserOpened=False, formalWrites=False))

FELT = 'The full stage body has blonde braided crown and large dark bow, red scarf/gold tabs, sleeveless brown buttoned vest with white fur hem, dark bandeau, bare midriff and red gloves/fur cuffs matching the exact felt01 raw canvas.'
ROM = 'The full stage body has bald head/red spiral, white brows/side locks, bead earrings, broad marked bare torso with tiered white chest hair, ragged cape with blue-green trim and diagonal chain matching the exact rom01 raw canvas.'
JULIUS = 'Lavender-haired stage body wears a high closed dark tracksuit collar, pale zip-front chest panels, dark sleeves, orange stripe and N emblem. Exact assembled julius_jersey01 reference remains pending; a name or expression does not replace it.'
TEE = 'Black-haired stage body wears a plain dark crew-neck short-sleeve tee with exposed arms. Exact tshirt01/02 model-wrapper and assembled-reference comparison remains unresolved.'
ELSA = 'Long brown side braid, purple flower, purple feather collar and brown mantle with round gold clasp over a purple-striped low-cut outfit are directly visible. Candidate elsa01 is retained, but no equivalent current exact assembled-original binding with capture identity attribution has been revalidated by this bounded packet.'
decisions = {
  15: ('assembled_reference_pending', 'julius_jersey01', JULIUS),
  16: ('confirmed_identity_new_field', 'rom01', ROM),
  17: ('confirmed_identity_new_field', 'felt01', FELT),
  18: ('choice_overlay_and_tshirt_variant_pending', None, TEE + ' Choice HUD and two portrait panels cover part of the stage body; those UI portraits are not extra stage actors.'),
  19: ('confirmed_identity_new_field', 'felt01', FELT),
  20: ('assembled_reference_pending', 'julius_jersey01', JULIUS),
  21: ('assembled_reference_pending', 'julius_jersey01', JULIUS),
  22: ('tshirt_model_variant_and_assembled_reference_pending', None, TEE),
  23: ('assembled_original_binding_revalidation_pending', 'elsa01', ELSA),
  24: ('tshirt_model_variant_and_assembled_reference_pending', None, TEE),
  25: ('assembled_reference_pending', 'julius_jersey01', JULIUS),
  26: ('assembled_original_binding_revalidation_pending', 'elsa01', ELSA),
  27: ('confirmed_identity_new_field', 'felt01', FELT),
  28: ('confirmed_identity_new_field', 'rom01', ROM),
  29: ('confirmed_identity_new_field', 'felt01', FELT),
}
review_rows, changes, pending = [], [], []
for witness in observations:
    ordinal = witness['ordinal']
    classification, model, reason = decisions[ordinal]
    accepted = classification == 'confirmed_identity_new_field'
    require(witness['expectedCharacterAtSnapshot'] == '', 'Bounded node no longer empty')
    evidence = dict(reviewer=REVIEWER, directImageReview=True, directImageInspection=True,
        fullFrameReview=True, recordingPart=30, recordingId='bili-capital-30',
        sourceWitness=witness, selectedWitness=witness, sourceLedger=observations_ref,
        allocation=allocation_ref, sceneRecordingMapping=ref(mapping_path),
        sourceSnapshotProvenance=provenance_ref, decision=classification, reason=reason,
        motionAndExpressionVerified=False, originalScriptCSVRecovered=False,
        actingEvidenceRequired='Review the complete original prior boundary, entry/action, hold and next boundary; compare against mapped native motion/face/layer sequence before accepting any acting field.')
    if accepted:
        evidence.update(selectedModel=model, directlyViewedReferences=[model_refs[model]['directlyViewedReference']],
                        assembledReferenceBinding=model_refs[model]['assembledReferenceBinding'],
                        currentReferenceRevalidation=references_ref)
        changes.append(dict(sceneId=witness['sceneId'], scenarioId=witness['scenarioId'],
            stableKey=witness['stableKey'], sourceText=witness['sourceText'], rootConfirmed=False,
            directImageReview=True, expected={'character': ''},
            fields={'character': 'live2d/AC_' + model}, evidence=evidence))
    record = dict(ordinal=ordinal, sceneId=witness['sceneId'], scenarioId=witness['scenarioId'],
        stableKey=witness['stableKey'], sourceText=witness['sourceText'], classification=classification,
        candidateModel=model, reason=reason, sourceWitness=witness, evidence=evidence,
        identityAccepted=accepted, characterAtSourceSnapshot='', directImageReview=True,
        fullFrameReview=True, motionAndExpressionVerified=False, originalScriptCSVRecovered=False)
    review_rows.append(record)
    if not accepted:
        pending.append(record)

require(len(changes) == 6 and len(pending) == 9, 'Bounded counts differ')
require(git('rev-parse', 'HEAD') == head, 'Data HEAD changed while preparing; retain evidence and rebind')
require((DATA/'review/native-restoration.json').read_bytes() == ownership_raw and
        (DATA/'manifest.json').read_bytes() == manifest_raw, 'Ownership changed while preparing; rebind')
require((DATA/'assets/catalog.json').read_bytes() == catalog_raw, 'Catalog changed while preparing')
receipt_ref = write('direct-character-review-receipt.json', dict(
    schema='stella.bounded_independent_character_review.v1', reviewer=REVIEWER,
    createdUtc=datetime.now(timezone.utc).isoformat(), dataHeadObservedBefore=head, dataHeadObservedAfter=head,
    recordingPart=30, sourceVideo=video, observations=review_rows,
    directlyViewedOriginalFullFrames=15, directlyViewedOrdinals=list(range(15, 30)),
    candidateCharacterChanges=6, pendingIdentityObservations=9,
    confirmedByModel=dict(Counter(x['fields']['character'] for x in changes)),
    totalP30MetadataObservations=161, cumulativeReviewedThroughOrdinal=29,
    remainingUnreviewedObservations=131, first15PendingRemainOutsideThisPacket=8,
    fullPartReviewed=False, fullPartIdentityAccepted=False, actingAccepted=False,
    geometryAccepted=False, historicalFailedTrialAccepted=False, browserOpened=False,
    formalWrites=0, gitMutations=0, mainThreadViewedImages=False,
    sourceAllocation=allocation_ref, sourceLedger=observations_ref,
    sourceSnapshotProvenance=provenance_ref, positiveReferenceRevalidation=references_ref,
    additionalPendingReferenceRequests=[
      dict(models=['julius_jersey01','subaru_tshirt01','subaru_tshirt02'],
           existingRequest=ref(P/'minimal-pending-exact-model-reference-request-reuse.json'),
           action='Reuse existing exact-model assembled-reference requests; no browser run authorized by this receipt.'),
      dict(model='elsa01', historicalAcceptedPacket=ref(R/'visual/root-reviewed-cast-p11-049-096.json'),
           historicalReference=ref(R/'visual/elsa01-cast.json.gz'),
           action='Revalidate historical exact assembled anchor and current original/model binding with attributable capture provenance before promoting ord23/26. Historical matcher score is not identity acceptance.')],
    checkedFiles=list(checked.values())))
packet_ref = write('six-character-only-draft.json', dict(schema='native_repair.node_fields',
    status='delegated_direct_image_review_complete_root_integration_required', reviewer=REVIEWER,
    recordingPart=30, rootConfirmed=False, fieldGroups=['character'], changes=changes,
    pending=pending, reviewReceipt=receipt_ref, referenceRevalidation=references_ref,
    fullPartReviewed=False, fullPartIdentityAccepted=False))
write('delivery-receipt.json', dict(status='delivered_for_root_current_guard_integration',
    reviewer=REVIEWER, packet=packet_ref, reviewReceipt=receipt_ref,
    newCharacterCandidates=6, pendingIdentityObservations=9,
    newCandidates=[dict(sceneId=x['sceneId'], scenarioId=x['scenarioId'], fields=x['fields']) for x in changes],
    remainingUnreviewedObservations=131, fullRestorationAccepted=False, formalWrites=0,
    browserStarted=False, dataHeadAtReview=head))
print(json.dumps(dict(packet=packet_ref, reviewReceipt=receipt_ref, newCharacterCandidates=6,
    pendingIdentityObservations=9, dataHead=head), ensure_ascii=False))
