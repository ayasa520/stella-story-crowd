"""Guard a source-backed final scene without replacing existing authored rows.

Identity evidence comes from delegated full-frame review. The ending adds only
the independently observed door and CLEAR, using the already supported native
no-successor representation. Original script identities/phases stay unknown.
This step writes review packets and before snapshots, never formal data.
"""

from copy import deepcopy
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
R = HERE.parent
ROOT = R.parents[3]
DATA = ROOT / "story_crowd_data"
SCENE = 10450058


def read(path):
    return json.loads(path.read_text())


def write(name, document):
    (HERE / name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")


def main():
    assert not (HERE / "accepted-node-fields.json").exists(), "Do not overwrite an accepted packet"
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=DATA, check=True,
                          capture_output=True, text=True).stdout.strip()
    native_path = DATA / f"native/scenes/{SCENE}.json"
    review_path = DATA / f"review/scenes/{SCENE}.json"
    native, review = read(native_path), read(review_path)
    nodes = {node["scenario_id"]: node for node in native["scenario_list"]}
    catalog = read(DATA / "assets/catalog.json")
    sources = [
        R / "p30-next15-character-preflight-20261113-v1/fifteen-character-only-current-binding-draft.json",
        R / "visual-high/target-reviewed-p30-ord150toend-20261113-v1/ten-character-only-draft.json",
        R / "p30-choice26-and-ending-source-review-20261113-v1/node26-character-only-draft.json",
    ]
    changes, seen, provenance = [], set(), []
    for path in sources:
        packet = read(path)
        provenance.append(dict(path=str(path), sourceBoundDataHead=packet.get("sourceBoundDataHead"),
                               priorBindingHead=packet.get("boundDataHead"), changes=len(packet["changes"])))
        for upstream in packet["changes"]:
            change = deepcopy(upstream)
            number = change["scenarioId"]
            assert change["sceneId"] == SCENE and number not in seen
            seen.add(number)
            node, sidecar = nodes[number], review["scenarios"][str(number)]
            uid = change.get("uniqId", change.get("boundNativeIdentity", {}).get("uniq_id"))
            assert uid == node["uniq_id"]
            assert sidecar["stableKey"] == change["stableKey"] and sidecar["sourceText"] == change["sourceText"]
            assert change["expected"] == {"character": ""} and node["character"] == ""
            assert set(change["fields"]) == {"character"} and change["fields"]["character"] in catalog["models"]
            change["upstreamCurrentNativeBinding"] = deepcopy(change.get("currentNativeBinding"))
            change["currentNativeBinding"] = dict(dataHead=head, scenario_id=number,
                                                   uniq_id=uid, character="", committedBase=True)
            change["rootConfirmed"] = change["rootReviewed"] = True
            change["rootAcceptanceScope"] = "character identity/costume only"
            change["evidence"]["rootIntegrator"] = "/root"
            change["evidence"]["mainThreadViewedImages"] = False
            change["evidence"]["actualSavedFormalPlaybackAccepted"] = False
            changes.append(change)
    assert len(changes) == 26 and seen == set(range(9, 35))
    accepted = dict(schema="native_repair.node_fields", status="root_accepted_26_character_fields_pending_saved_playback",
                    rootReviewed=True, rootConfirmed=True, sourceBoundDataHead=head,
                    fieldGroups=["character"], sourcePackets=provenance, changes=changes)

    ending = read(R / "p30-ending-sequence-proposal-20261113-v1/ending-sequence-v2.draft.json")
    after, sidecar = nodes[35], review["scenarios"]["35"]
    branch = next(row for row in after["branch_list"] if row["branch_id"] == 351)
    assert native["scenario_list"][-1] is after and max(nodes) == 35
    assert after["uniq_id"] == 1045005800035 and after["scenario_type"] == 1
    assert after["msg_text"] == "——完——" and after["msg_character"] == "" and after["character"] == ""
    assert after["command"] == ["", "", ""] and branch["uniq_id"] == 1045005810351
    assert branch["transition_list"] == [] and sidecar["stableKey"] == "s10450058-p30-at0992"
    assert sidecar["sourceText"] == "―完―"
    assert ending["sceneId"] == SCENE and ending["afterScenarioId"] == 35 and ending["branchId"] == 351
    assert "finish" not in ending and len(ending["nodes"]) == 2
    assert ending["nodes"][0]["fields"] == dict(scenario_type=3, video="adv_dive01_out", command=["StopBGM", "", "CardOut"])
    assert ending["nodes"][1]["fields"] == dict(scenario_type=0, bg_music="bgm_btl_adv_win01", command=["", "", ""])
    assert "adv_dive01_out" in catalog["movies"] and "bgm_btl_adv_win01" in catalog["music"]
    for record in [ending, ending["terminal"], *ending["nodes"]]:
        record["rootConfirmed"] = record["rootReviewed"] = True
    ending.update(status="root_accepted_source_backed_authored_suffix_pending_saved_playback",
                  installable=True, executionAuthorized=True, sourceBoundDataHead=head)
    ending["authorship"]["rootAuthorizedConvention"] = (
        "Root reviewed the concrete packet: retain type1 narration35, then append complete door "
        "with phase0 bare StopBGM/default1s nonblocking ramp and phase2 CardOut; separate CLEAR "
        "with plain win01/default fade; omitted-destination FINISH. These are authored choices, "
        "not recovered original P30 CSV phases or parameters.")
    for evidence in ending["evidence"]:
        if evidence.get("kind") == "root-authorized-authored-convention":
            evidence["concretePacketApprovalPending"] = False
    ending["rootReview"] = dict(integrator="/root", mainThreadViewedImages=False,
                               narration35TypeAlreadyCorrect=True, exactOriginalPayloadRecovered=False,
                               sourceAndAudioReportsRead=True, actualSavedPlaybackAccepted=False,
                               doesNotAddWaitRewardSuccessorOrMapEdge=True)

    (HERE / "native.before.json").write_bytes(native_path.read_bytes())
    (HERE / "review.before.json").write_bytes(review_path.read_bytes())
    write("accepted-node-fields.json", accepted)
    write("accepted-ending-sequence.json", ending)
    write("root-preflight.json", dict(status="passed", currentDataHead=head, characterFields=26,
                                      characterScenarioIds=sorted(seen), originalNarrationTypePreserved=1,
                                      existingLastNode=35, expectedSuffixCount=2,
                                      nativeDataWritten=False, originalScriptRecovered=False))
    print("Accepted26identity fields and source-backed two-row ending; formal data unchanged.")


if __name__ == "__main__":
    main()
