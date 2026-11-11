"""Accept a bounded image review delegated by the user, without viewing images.

Visual decisions remain attributed to the named subagent. Root accepts only
the packet digest, node identities, source text, field preconditions and file
witnesses. This adapter deliberately cannot select a candidate, change another
performance field outside its explicit scope, install data or declare a whole
chapter complete. The default scope remains character identity; a background
packet must explicitly select bg_picture at the command line. A command packet
requires recording sequences and explicit authored-phase provenance.
Motion acceptance additionally requires independently reviewed complete entry
sequences, stable served sources and the exact compiled node being installed.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "story_studio/recovery/native_repair.py").is_file())
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_reference(reference, label):
    path = Path(reference["file"])
    path = path if path.is_absolute() else ROOT / path
    require(fingerprint(path) == reference["sha256"], f"{label} changed")
    return path


def accept_temporal_motion(row, evidence, reviewer):
    """Check a delegated temporal decision without interpreting any image.

    A held pose cannot authorize a motion CSV. Bind this separate gate to the
    actual original/player frame sequences, the reviewer's bounded decision,
    and the served code and compiled node used for that decision. This gate
    verifies evidence integrity and scope; visual judgments remain delegated.
    """
    temporal = evidence["temporalReview"]
    components = set(row["verifiedMotionComponents"])
    require(bool(components) and components <= {"body", "face", "extra"}, "Invalid motion components")
    require(components == set(temporal["verifiedMotionComponents"]), "Temporal component scope differs")
    require(temporal["fullVisibleEntryPassed"] is True and
            temporal["independentFromFormalPredecessor"] is True,
            "Conditional or held-only motion cannot be installed")
    require(temporal["originalCsvRecovered"] is False and temporal["exactTimingValidated"] is False,
            "This gate accepts explicit visible reproductions, not recovered original clocks or CSV")
    require(bool(row["expected"].get("character")) and row["expected"].get("motion") == "",
            "New motion needs an explicit model and empty-field guard")
    receipt_path = checked_reference(temporal["reviewReceipt"], "Motion review receipt")
    receipt = json.loads(receipt_path.read_text())
    require(receipt["reviewer"] == reviewer and receipt["directImageReview"] is True,
            "Temporal visual reviewer differs")
    decision = next((item for item in receipt["decisions"]
                     if item["scenarioId"] == row["scenarioId"]), None)
    require(decision and decision["installableSubset"] is True and
            decision["fullVisibleEntryPassed"] is True and decision["independentFromFormalPredecessor"] is True,
            "Motion review does not approve this independent entry")
    require(decision["stableKey"] == row["stableKey"] and decision["sourceText"] == row["sourceText"] and
            decision["fields"] == row["fields"] and set(decision["verifiedMotionComponents"]) == components,
            "Approved motion fields or identities differ")

    source = json.loads(checked_reference(temporal["sourceEntryIndex"], "Original entry index").read_text())
    actual = json.loads(checked_reference(temporal["actualEntryIndex"], "Player entry index").read_text())
    source_frames = source["sequences"][temporal["sourceEntryIndex"]["sequenceId"]]["frames"]
    run = actual["runs"][temporal["actualEntryIndex"]["run"]]
    node_id = f'{row["sceneId"]}:{row["scenarioId"]}'
    require(temporal["actualEntryIndex"]["nodeId"] == node_id and
            run["overrides"]["exampleId"] == temporal["actualEntryIndex"]["exampleId"] and
            run["overrides"]["persisted"] is False and not run["failures"],
            "Reviewed player entry or bounded override differs")
    frames = run["actorPixelSequences"][node_id]["frames"]
    require(len(source_frames) == temporal["sourceEntryIndex"]["frames"] and len(source_frames) > 1 and
            len(frames) == temporal["actualEntryIndex"]["frames"] and len(frames) > 1,
            "Complete-entry frame inventory differs")
    for sample in [*source_frames, *frames]:
        path = Path(sample["path"])
        require(fingerprint(path if path.is_absolute() else ROOT / path) == sample["sha256"],
                "Reviewed temporal frame changed")
    require(any(0 < sample["opacity"] < .05 for sample in frames) and
            any(sample["opacity"] >= .999 for sample in frames),
            "Player sequence does not retain both low-alpha entry and full visibility")
    require(all(a["elapsedGame"] <= b["elapsedGame"] for a, b in zip(frames, frames[1:])),
            "Player entry game-time order differs")
    require(all(not run["clockAudit"][key] for key in
                ("sameClockAndIncrementErrors", "sharedFrameDomainErrors", "sameFrameDuplicateIntegrationErrors")),
            "Player entry has unresolved shared-clock errors")
    compiled = next(item for item in run["nodes"] if item["id"] == node_id)
    command = ",".join(token for token in
                       [compiled["body"], compiled["face"], *compiled["extra_motions"]] if token)
    require(command == row["fields"]["motion"] and compiled["text"] == row["sourceText"] and
            row["expected"]["character"] == 'live2d/AC_' + compiled["model"],
            "Reviewed compiled node does not express the proposed model/motion/text")

    # Recheck code archives and the still-installed predecessor snapshot. A
    # source update or intervening edit invalidates old runtime observations;
    # it must not silently inherit acceptance from an earlier implementation.
    binding = evidence["sourceBinding"]
    before_path = checked_reference(binding["servedBefore"], "Served source before")
    after_path = checked_reference(binding["servedAfter"], "Served source after")
    before, after = json.loads(before_path.read_text()), json.loads(after_path.read_text())
    before_sources = {item["url"]: item for item in before["sources"]}
    after_sources = {item["url"]: item for item in after["sources"]}
    require(set(before_sources) == set(after_sources), "Served source inventory differs")
    for url, item in before_sources.items():
        later = after_sources[url]
        require(item["sha256"] == later["sha256"] == fingerprint(ROOT / item["local"]) and
                fingerprint(before_path.parent / item["archive"]) == item["sha256"] and
                fingerprint(after_path.parent / later["archive"]) == later["sha256"],
                "Served or current player source changed")
    require(before["canonicalCommit"] == after["canonicalCommit"] == binding["canonicalCommit"] and
            before["nativeSceneSha256"] == after["nativeSceneSha256"] ==
            fingerprint(ROOT / f'story_crowd_data/native/scenes/{row["sceneId"]}.json') and
            before["protectedStudioSha256"] == after["protectedStudioSha256"] ==
            fingerprint(ROOT / 'data/story_studio/project.json'), "Motion predecessor/source snapshot changed")
    for key in ("originalController", "originalClipBindings", "originalClipCurves", "integrity",
                "compiledNodeSnapshots", "actualPayload"):
        checked_reference(evidence[key], key)
    return dict(originalEntryFrames=len(source_frames), playerEntryFrames=len(frames),
                servedSourceFiles=len(before_sources), verifiedMotionComponents=sorted(components),
                fullVisibleEntryPassed=True, originalCsvRecovered=False, exactTimingValidated=False)


def accept_digital_voice(row, evidence, reviewer):
    """Bind an original-cue reproduction to its payload and visible card.

    Unsupported audio input cannot become a fictional listening claim. This
    gate instead retains the named reviewer's independent full-cue/held-out
    signal analysis, bounded alternative audit, ACB provenance and directly
    reviewed card sequence. It does not infer a delay, phase, gain or pitch.
    """
    reference = evidence["verdict"]
    case = json.loads(checked_reference(dict(file=reference["path"], sha256=reference["sha256"]),
                                        "Voice review verdict").read_text())
    require(case["reviewer"] == reviewer and case["verdict"]["digitalIdentity"] ==
            "supported-for-the-exact-catalog-payload" and case["verdict"]["cardAssignment"] ==
            "supported-by-direct-original-full-interface-sequence-review",
            "Voice identity and original-card review are not both approved")
    guard = case["guard"]
    require(all(guard[key] == row[key] for key in ("sceneId", "scenarioId", "stableKey", "sourceText", "sourceSpeaker")) and
            all(guard[key] == value for key, value in row["expected"].items()) and
            row["expected"].get("voice") == "" and bool(row["expected"].get("character")),
            "Voice card/model/empty-field guards differ")
    require(case["proposedVoice"] == row["fields"]["voice"] and
            row["originalCsvRecovered"] is False and row["originalCommandPhaseRecovered"] is False and
            row["exactTimingValidated"] is False and evidence["originalVoiceDelayRecovered"] is False,
            "Voice proposal exceeds its cue-only reconstruction scope")
    require(case["directFrameReview"]["performed"] is True and
            case["directFrameReview"]["reviewer"] == reviewer and
            case["sourceClipProvenance"]["freshPCMIdenticalToExistingClip"] is True,
            "Original card sequence or fresh source decode was not verified")
    alternatives = case["ambiguityAudit"]
    require(alternatives["excludedCues"] == 0 and alternatives["signedCorrelationGap"] > 0 and
            len(alternatives["samePCM"]) == 1 and len(alternatives["sameWaveformAliases"]) == 1,
            "Voice evidence still contains an unresolved duplicate or stronger alternative")

    # These are integrity checks on already performed signal experiments, not
    # a new classifier or a score-only acceptance threshold. Hash every nested
    # file receipt once per case and recheck file stats before returning, so an
    # intervening source replacement cannot mix two evidence versions.
    checked = {}
    def check_tree(value):
        if isinstance(value, dict):
            if {"path", "sha256", "bytes"} <= set(value):
                path = Path(value["path"])
                path = path if path.is_absolute() else ROOT / path
                if path not in checked:
                    stat = path.stat()
                    require(stat.st_size == value["bytes"] and fingerprint(path) == value["sha256"],
                            "Voice evidence file changed")
                    checked[path] = (value["sha256"], stat.st_size, stat.st_mtime_ns)
                else:
                    require(checked[path][:2] == (value["sha256"], value["bytes"]),
                            "One voice evidence path has conflicting receipts")
            for item in value.values():
                check_tree(item)
        elif isinstance(value, list):
            for item in value:
                check_tree(item)
    check_tree(case)
    payload = case["actualCatalogPayload"]
    bank, cue = row["fields"]["voice"].split(",")
    require(payload["entry"]["cue"] == cue and payload["byteIdenticalToMatchedLimeosCue"] is True and
            Path(payload["catalog"]["path"]).parent.name == bank and
            (ROOT / payload["payload"]["path"]).resolve() ==
            (ROOT / 'story_crowd_data/assets' / payload["entry"]["url"]).resolve(),
            "Voice CSV does not resolve to the reviewed catalog payload")
    for path, (_, size, modified) in checked.items():
        stat = path.stat()
        require((stat.st_size, stat.st_mtime_ns) == (size, modified), "Voice evidence changed during acceptance")
    sample = evidence["selectedWitness"]
    witness = dict(frame=str(ROOT / sample["image"]["path"]), frameSha256=sample["image"]["sha256"],
                   video=str(ROOT / evidence["originalVideo"]["path"]), videoSha256=evidence["originalVideo"]["sha256"])
    return witness, dict(nestedFileReceiptsChecked=len(checked),
                         comparedCues=alternatives["allComparedCues"],
                         fullCueCorrelation=case["recordedSourceToCatalog"]["signedFullCorrelation"],
                         alternativeCorrelationGap=alternatives["signedCorrelationGap"],
                         subjectivelyListened=False, originalVoiceDelayRecovered=False,
                         originalCommandPhaseRecovered=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--field", choices=("character", "bg_picture", "command", "motion", "voice"), default="character")
    args = parser.parse_args()
    require(not args.output.exists(), "Use a fresh accepted-packet path")
    require(fingerprint(args.source) == args.sha256, "Reviewed packet changed")
    packet = json.loads(args.source.read_text())
    require(packet["reviewer"] == args.reviewer, "Unexpected visual reviewer")
    snapshot = InstalledSnapshot(ROOT, ROOT / "story_crowd_data")
    accepted, seen = deepcopy(packet), set()
    for row in accepted["changes"]:
        identity = (row["sceneId"], row["scenarioId"])
        require(identity not in seen, "Duplicate node in delegated packet")
        seen.add(identity)
        node, review = snapshot.node(*identity, row["stableKey"])
        require(review["sourceText"] == row["sourceText"], "Japanese source changed")
        require(set(row["fields"]) == {args.field}, "Packet exceeds the selected field scope")
        require(all(node[key] == value for key, value in row["expected"].items()),
                "Installed field changed before acceptance")
        evidence = row["evidence"]
        require(evidence["reviewer"] == args.reviewer, "Node reviewer mismatch")
        require(evidence.get("directImageReview") is True or
                evidence.get("directImageInspection") is True,
                "A numerical match is not a delegated image review")
        witness = evidence.get("selectedWitness", evidence.get("sourceWitness", evidence))
        temporal_checks = accept_temporal_motion(row, evidence, args.reviewer) if args.field == "motion" else None
        voice_checks = None
        if args.field == "voice":
            require(review["sourceSpeaker"] == row["sourceSpeaker"], "Voice source speaker changed")
            witness, voice_checks = accept_digital_voice(row, evidence, args.reviewer)
        if args.field == "command":
            require(evidence.get("originalCommandPhaseRecovered") is False and
                    evidence.get("reconstructedCommandPhase") == 2,
                    "This acceptance path only handles explicitly authored after-text commands")
            require(row["fields"]["command"][:2] == row["expected"]["command"][:2],
                    "An after-text reconstruction cannot change earlier phases")
            # Verify every retained recording sample and the original texture,
            # not just the contact sheet shown to the visual reviewer. Preserve
            # each sequence's own video SHA; alternate quality encodings must
            # never be relabelled as the original file's byte identity.
            for key in ("sourceSequence", "refinedSourceSequence"):
                require(fingerprint(evidence[key]) == evidence[key + "Sha256"],
                        "Reviewed recording sequence changed")
                sequence = json.loads(Path(evidence[key]).read_text())
                for sample in sequence["frames"]:
                    require(fingerprint(sample["file"]) == sample["sha256"],
                            "Reviewed recording sample changed")
            require(fingerprint(evidence["originalPhoneTexture"]) == evidence["originalPhoneTextureSha256"],
                    "Original overlay texture changed")
            first = sequence["frames"][0]
            witness = dict(first, video=sequence["video"], videoSha256=sequence["videoSha256"])
        # Identity reviews use frame/frameSha256; focused boundary reviews
        # use file/sha256. Both name one explicit recording frame, rather than
        # a numerical match result or an unbounded search-result collection.
        frame = witness.get("frame", witness.get("file"))
        frame_sha256 = witness.get("frameSha256", witness.get("sha256"))
        require(bool(frame) and bool(frame_sha256), "Missing recording frame identity")
        require(fingerprint(frame) == frame_sha256,
                "Reviewed frame changed")
        require(bool(witness.get("videoSha256")) and bool(witness.get("video")),
                "Missing original recording provenance")
        if args.field == "bg_picture":
            plate = evidence["originalPlate"]
            require(plate["id"] == row["fields"][args.field], "Background plate identity differs")
            require(fingerprint(plate["file"]) == plate["sha256"], "Original background plate changed")
        # Keep the existing importer's rootConfirmed gate, but record exactly
        # what root accepted. The user's current instruction forbids images
        # in the main conversation; this is no claim of direct root viewing.
        row["rootConfirmed"] = True
        evidence["rootIntegration"] = dict(
            reviewer="/root", visualReviewer=args.reviewer,
            mainThreadViewedImages=False,
            authorization="User explicitly delegated all image inspection to subagents",
            checks=["packet SHA-256", "unique owned node and stable key",
                    "Japanese source", "field preconditions", "image witness SHA-256"],
            sourcePacket=str(args.source.resolve()), sourcePacketSha256=args.sha256,
            acceptedScope=[args.field],
        )
        if temporal_checks is not None:
            evidence["rootIntegration"]["temporalChecks"] = temporal_checks
        if voice_checks is not None:
            evidence["rootIntegration"]["digitalVoiceChecks"] = voice_checks
    require(bool(seen), "Empty delegated packet")
    snapshot.unchanged_on_disk()
    accepted["status"] = "delegated_image_review_accepted_for_guarded_install"
    if "rootConfirmed" in accepted:
        accepted["rootConfirmed"] = True
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(accepted, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(accepted=len(seen), reviewer=args.reviewer,
                         sha256=fingerprint(args.output), output=str(args.output))))


if __name__ == "__main__":
    main()
