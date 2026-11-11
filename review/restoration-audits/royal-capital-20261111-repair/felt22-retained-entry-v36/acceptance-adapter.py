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


def compiled_motion(node):
    return ",".join(token for token in
                    [node["body"], node["face"], *node["extra_motions"]] if token)


def accept_new_actor_entry(row, temporal, decision, run, frames, snapshot):
    """Preserve the original independent, newly visible actor requirement."""
    require(temporal["independentFromFormalPredecessor"] is True and
            decision["independentFromFormalPredecessor"] is True,
            "Conditional new-actor motion cannot be installed")
    require(any(0 < sample["opacity"] < .05 for sample in frames) and
            any(sample["opacity"] >= .999 for sample in frames),
            "New-actor sequence needs low-alpha entry and full visibility")
    return dict(entryContext="new_actor", independentFromFormalPredecessor=True)


def accept_retained_actor_entry(row, temporal, decision, run, frames, snapshot):
    """Authorize a retained actor only from an already accepted formal pose.

    A same-model card has no new actor fade. Requiring a low-alpha screenshot
    would force fabricated evidence, while treating its predecessor as unknown
    would incorrectly transfer pending poses into formal data. This separate
    strategy therefore binds an explicit independently reviewed predecessor,
    its current fields, its single native edge, and the real compiled/rAF
    continuity. It never accepts a dependency on a pending memory override.
    """
    require(temporal["independentFromFormalPredecessor"] is False and
            decision["independentFromFormalPredecessor"] is False and
            temporal["independentFromPendingPredecessors"] is True and
            decision["independentFromPendingPredecessors"] is True,
            "Retained entry must disclose its accepted formal dependency")
    override = run["overrides"]
    preview = json.loads(checked_reference(dict(file=override["evidence"],
                         sha256=override["packetSha256"]), "Retained preview packet").read_text())
    example = next(item for item in preview["examples"] if item["id"] == override["exampleId"])
    require(preview["sceneId"] == row["sceneId"] and preview["persisted"] is False and
            preview["formalDataWrites"] == 0 and len(example["changes"]) == 1 and
            example["changes"][0]["scenarioId"] == row["scenarioId"] and
            example["changes"][0]["fields"] == row["fields"],
            "Retained preview must override this motion alone")
    prior = row["requiredPredecessor"]
    require(prior == temporal["requiredPredecessor"] == decision["requiredPredecessor"] and
            prior["sceneId"] == row["sceneId"] and prior["scenarioId"] != row["scenarioId"] and
            prior["alreadyIndependentlyReviewed"] is True and
            set(prior["expected"]) == {"character", "motion"} and
            all(prior["expected"].values()), "Retained predecessor scope differs")
    native, review = snapshot.node(prior["sceneId"], prior["scenarioId"], prior["stableKey"])
    require(review["sourceText"] == prior["sourceText"] and
            all(native[key] == value for key, value in prior["expected"].items()) and
            native["character"] == row["expected"]["character"],
            "Retained predecessor is not the guarded installed same-model pose")
    receipt = json.loads(checked_reference(prior["reviewReceipt"], "Predecessor visual receipt").read_text())
    approval = next((item for item in receipt["decisions"]
                     if item["scenarioId"] == prior["scenarioId"]), None)
    require(receipt["directImageReview"] is True and bool(receipt["reviewer"]) and
            approval and approval["installableSubset"] is True and
            approval["fullVisibleEntryPassed"] is True and
            approval["independentFromFormalPredecessor"] is True and
            approval["stableKey"] == prior["stableKey"] and
            approval["sourceText"] == prior["sourceText"] and
            approval["fields"] == {"motion": native["motion"]} and
            {"body", "face"} <= set(approval["verifiedMotionComponents"]),
            "Retained predecessor lacks independent complete body/face approval")
    branches = native["branch_list"]
    require(len(branches) == 1 and branches[0]["type"] == 1 and
            len(branches[0]["transition_list"]) == 1 and
            branches[0]["transition_list"][0]["next_scenario_id"] == row["scenarioId"],
            "Retained predecessor no longer leads directly to this card")
    prior_id = f'{prior["sceneId"]}:{prior["scenarioId"]}'
    compiled = next(item for item in run["nodes"] if item["id"] == prior_id)
    require(compiled_motion(compiled) == native["motion"] and
            compiled["text"] == prior["sourceText"] and
            'live2d/AC_' + compiled["model"] == native["character"],
            "Captured predecessor differs from the installed approved pose")
    prior_frames = run["actorPixelSequences"][prior_id]["frames"]
    require(bool(prior_frames), "Missing captured predecessor pixels")
    for sample in prior_frames:
        path = Path(sample["path"])
        require(fingerprint(path if path.is_absolute() else ROOT / path) == sample["sha256"],
                "Captured predecessor pixels changed")
    instance = prior_frames[-1]["instance"]
    require(all(sample["instance"] == instance and sample["opacity"] >= .999 and
                sample["preUpdateLink"]["paired"] is True and
                sample["preUpdateLink"]["sameSharedFrame"] is True and
                sample["preUpdateLink"]["sameNode"] is True and
                sample["preUpdateLink"]["appliedStageSupported"] is True for sample in frames),
            "Retained pixels lack stable visible same-instance applied-frame links")
    def layer_tokens(sample):
        return {layer["layer"]: layer["token"] for layer in sample["actor"]["layers"]}
    pre_roll = [sample for sample in frames if sample["elapsedGame"] < 0]
    require(bool(pre_roll) and all(layer_tokens(sample).get("motion") in
                                  {compiled["body"], compiled["body"] + "_w"} and
                                  layer_tokens(sample).get("face") in
                                  {compiled["face"], compiled["face"] + "_w"}
                                  for sample in pre_roll),
            "Retained entry does not show the approved prior pose before motion")
    target = next(item for item in run["nodes"]
                  if item["id"] == f'{row["sceneId"]}:{row["scenarioId"]}')
    require(any(layer_tokens(sample).get("motion") == target["body"] for sample in frames) and
            layer_tokens(frames[-1]).get("motion") == target["body"] + "_w" and
            frames[-1]["elapsedGame"] >= 3.5,
            "Retained sequence does not cover active motion through settled hold")
    audit = run["parameterReadbackAudit"]
    node_id = target["id"]
    require(not run["httpErrors"] and not any(item.get("type") == "error" for item in run["console"]) and
            not any(item["node"] == node_id for item in
            run["transitionClockSnapshots"]) and not any(item.get("node") == node_id for item in
            audit["orderOrBindingFailures"]) and not any(item.get("detail", {}).get("node") == node_id
            for item in audit["samplingIssues"]),
            "Retained target has a fade, runtime error or unresolved observer warning")
    # Preserve global capture warnings rather than rewriting success:false.
    # Other model changes may invalidate old observers; only their explicitly
    # scoped target-free records can coexist with this bounded acceptance.
    return dict(entryContext="retained_actor", independentFromFormalPredecessor=False,
                independentFromPendingPredecessors=True, requiredPredecessor=prior,
                retainedAlphaMinimum=min(sample["opacity"] for sample in frames),
                indexedOrderOrBindingFailuresPreserved=len(audit["orderOrBindingFailures"]))


MOTION_ENTRY_ACCEPTORS = {"new_actor": accept_new_actor_entry,
                          "retained_actor": accept_retained_actor_entry}


def accept_temporal_motion(row, evidence, reviewer, snapshot):
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
    require(temporal["fullVisibleEntryPassed"] is True, "Held-only motion cannot be installed")
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
    # Review receipts use either an installable-subset flag or the explicit
    # authored-reproduction verdict. An explicit rejection always wins; the
    # alternate spelling does not replace any identity, component or entry gate.
    require(decision and decision.get("installableSubset", decision.get("authoredReproductionAccepted")) is True and
            decision["fullVisibleEntryPassed"] is True,
            "Motion review does not approve this complete entry")
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
    context = temporal.get("entryContext", "new_actor")
    require(context in MOTION_ENTRY_ACCEPTORS and decision.get("entryContext", "new_actor") == context,
            "Unknown or inconsistent motion entry context")
    if context == "retained_actor":
        require(decision["sourceFullEntry"] == temporal["sourceEntryIndex"] and
                decision["actualFullEntry"] == temporal["actualEntryIndex"],
                "Retained visual approval refers to a different frame inventory")
    context_checks = MOTION_ENTRY_ACCEPTORS[context](row, temporal, decision, run, frames, snapshot)
    require(all(a["elapsedGame"] <= b["elapsedGame"] for a, b in zip(frames, frames[1:])),
            "Player entry game-time order differs")
    require(all(not run["clockAudit"][key] for key in
                ("sameClockAndIncrementErrors", "sharedFrameDomainErrors", "sameFrameDuplicateIntegrationErrors")),
            "Player entry has unresolved shared-clock errors")
    compiled = next(item for item in run["nodes"] if item["id"] == node_id)
    command = compiled_motion(compiled)
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
    # SDK/model lifecycle helpers participate in the evidence binding when
    # present. A fresh retained-actor review must include those files and the
    # Japanese review snapshot as well as the eight original player sources.
    if context == "retained_actor":
        require(bool(before.get("supplementalSources")) and bool(after.get("supplementalSources")) and
                before["reviewSceneSha256"] == after["reviewSceneSha256"] ==
                fingerprint(ROOT / f'story_crowd_data/review/scenes/{row["sceneId"]}.json'),
                "Retained entry lacks stable SDK/review source binding")
    before_sources = {item["url"]: item for item in
                      [*before["sources"], *before.get("supplementalSources", [])]}
    after_sources = {item["url"]: item for item in
                     [*after["sources"], *after.get("supplementalSources", [])]}
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
    return dict(**context_checks, originalEntryFrames=len(source_frames), playerEntryFrames=len(frames),
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
        temporal_checks = accept_temporal_motion(row, evidence, args.reviewer, snapshot) if args.field == "motion" else None
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
