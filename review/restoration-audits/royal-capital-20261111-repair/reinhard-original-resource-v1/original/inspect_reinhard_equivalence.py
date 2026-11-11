"""Bind one isolated Reinhard availability export to original Unity resources.

This is an offline evidence producer. It never installs a resource or assigns a
story character. Run with nice 19, CPU affinity 22/23 and cached UnityPy only.
Decoded texture bytes and controller trees are used for resource equivalence;
neither establishes that a source recording shows this costume. That separate
decision still needs an explicitly scheduled assembled-model capture.
"""

import hashlib
import importlib.metadata
import json
from collections import Counter
from pathlib import Path
import sys

import UnityPy
from PIL import Image


OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p / "story_studio/media.py").is_file())
R = ROOT / "data/native_recovery/royal-capital-20261110/repair-20261111"
STAGING = ROOT / "artifacts/repair-20261112-reinhard-reference-availability-v1"
ORIGINAL = ROOT / "data/extracted_archives/original/com.sega.stella/files/AssetBundle/assets"
LIME = ROOT / "data/extracted_archives/limeos/LIMEOS/assets/downloadassets/assetbundle/models/ac/ac_reinhard01/ac"
REVIEWER = "/root/felt_entry_offline_review"
sys.path.insert(0, str(ROOT))
from story_studio.actor_assets import controller_asset


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(file=str(path), sha256=sha(raw), bytes=len(raw))


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_new(name, value):
    path = OUT / name
    # Evidence is append-only: a failed run must not replace an earlier receipt.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return reference(path)


def one(rows):
    rows = list(rows)
    assert len(rows) == 1, len(rows)
    return rows[0]


def main():
    request_path = R / "visual-high/agent-reviewed-p28-identity-v1/reinhard01-resource-assembled-reference-request.json"
    request = read_json(request_path)
    source = ORIGINAL / "ac_reinhard01.prefab"
    base = ORIGINAL / "ac_base_reinhard01.prefab"
    environment = UnityPy.load(str(source))
    objects = {o.path_id: o for o in environment.objects}
    trees = {k: o.read_typetree() for k, o in objects.items()
             if o.type.name in {"MonoBehaviour", "Animator", "AnimatorController", "GameObject", "AssetBundle"}}
    moc_id, moc = one((k, t) for k, t in trees.items() if "_bytes" in t)
    model_id, model = one((k, t) for k, t in trees.items() if "_moc" in t)
    animator_id, animator = one((k, t) for k, t in trees.items() if objects[k].type.name == "Animator")
    controller_id, controller = one((k, t) for k, t in trees.items() if objects[k].type.name == "AnimatorController")
    assert model["_moc"] == dict(m_FileID=0, m_PathID=moc_id)
    assert model["m_GameObject"] == animator["m_GameObject"]
    assert animator["m_Controller"] == dict(m_FileID=0, m_PathID=controller_id)
    assert controller["m_Name"] == "AC_reinhard01_ver2"
    bundle = one(t for k, t in trees.items() if objects[k].type.name == "AssetBundle")
    root_pointer = one(bundle["m_Container"])[1]["asset"]
    assert root_pointer == animator["m_GameObject"]

    embedded_moc = bytes(moc["_bytes"])
    assert embedded_moc == (LIME / "ac.moc3").read_bytes()
    assert embedded_moc == (STAGING / "models/reinhard01/ac/ac.moc3").read_bytes()
    texture_object = one(o for o in objects.values() if o.type.name == "Texture2D")
    decoded = texture_object.read().image.convert("RGBA")
    lime_texture = Image.open(LIME / "textures/texture_00.png").convert("RGBA")
    staged_texture = Image.open(STAGING / "models/reinhard01/ac/textures/texture_00.png").convert("RGBA")
    assert decoded.size == lime_texture.size == staged_texture.size
    assert decoded.tobytes() == lime_texture.tobytes() == staged_texture.tobytes()
    renderers = [(k, t) for k, t in trees.items() if "_mainTexture" in t]
    assert len(renderers) == 64
    assert all(t["_mainTexture"] == dict(m_FileID=0, m_PathID=texture_object.path_id) for _, t in renderers)

    model_json = LIME / "ac.model3.json"
    definition = read_json(model_json)
    files = definition["FileReferences"]
    relatives = [files["Moc"], *files["Textures"]]
    motion_files = [row["File"] for group in files["Motions"].values() for row in group]
    relatives += motion_files
    assert len(relatives) == len(set(relatives)) == 40
    file_equivalence = []
    for relative in ["ac.model3.json", *relatives]:
        original_file = LIME / relative
        staged_file = STAGING / "models/reinhard01/ac" / relative
        assert original_file.read_bytes() == staged_file.read_bytes(), relative
        file_equivalence.append(dict(relative=relative, original=reference(original_file),
                                     staged=reference(staged_file), exactBytesEqual=True))

    # Resolve each controller clip by BOTH its actual PathID and external CAB
    # identity. A matching filename/token alone is not a Unity pointer binding.
    # Only the 38 explicitly referenced model motions are loaded; no archive scan
    # or animation conversion is performed by this audit.
    clip_pointers = controller["m_AnimationClips"]
    assert len(clip_pointers) == len(motion_files) == 38
    controller_object = objects[controller_id]
    clips = []
    seen_slots = set()
    for relative in motion_files:
        clip_name = Path(relative).name.removesuffix(".motion3.json")
        source_clip = ORIGINAL / (clip_name.lower() + ".anim")
        clip_object = one(o for o in UnityPy.load(str(source_clip)).objects if o.type.name == "AnimationClip")
        clip_tree = clip_object.read_typetree()
        assert clip_tree["m_Name"] == clip_name
        slot, pointer = one((i, p) for i, p in enumerate(clip_pointers) if p["m_PathID"] == clip_object.path_id)
        assert slot not in seen_slots
        seen_slots.add(slot)
        external = controller_object.assets_file.externals[pointer["m_FileID"] - 1].path
        assert Path(external).name.lower() == clip_object.assets_file.name.lower()
        clips.append(dict(controllerSlot=slot, controllerPointer=pointer,
                          externalSerializedFile=external, loadedSerializedFile=clip_object.assets_file.name,
                          exactPointerAndCabMatch=True, originalClip=reference(source_clip),
                          originalClipName=clip_tree["m_Name"], originalClipPathId=clip_object.path_id,
                          limeosMotion=reference(LIME / relative),
                          stagedMotion=reference(STAGING / "models/reinhard01/ac" / relative)))
    assert seen_slots == set(range(38))

    controller_ref = write_new("reinhard01-original-controller.json", controller)
    model_binding_ref = write_new("reinhard01-model-component-bindings.json", dict(
        source=reference(source), rootGameObjectPathId=root_pointer["m_PathID"],
        modelComponentPathId=model_id, modelComponent=model,
        animatorPathId=animator_id, animator=animator,
        rendererTexturePointers=[dict(componentPathId=k, texture=t["_mainTexture"]) for k, t in renderers]))
    base_env = UnityPy.load(str(base))
    base_trees = [dict(pathId=o.path_id, type=o.type.name, value=o.read_typetree()) for o in base_env.objects
                  if o.type.name != "MonoScript"]
    base_ref = write_new("reinhard01-original-base-prefab.json", dict(source=reference(base), objects=base_trees))
    base_names = {row["pathId"]: row["value"]["m_Name"] for row in base_trees if row["type"] == "GameObject"}
    ch_top = one(row for row in base_trees if row["type"] == "Transform"
                 and base_names[row["value"]["m_GameObject"]["m_PathID"]] == "CH_top")
    manifest_path = ROOT / "data/story_player/extracted/manifest.json"
    animation_path = ROOT / "data/story_player/extracted/animation.json"
    actor = read_json(manifest_path)["actors"]["reinhard01"]
    assert actor["position"] == ch_top["value"]["m_LocalPosition"]
    assert actor["scale"] == ch_top["value"]["m_LocalScale"]
    assert actor["source"] == str(base.relative_to(ROOT / "data/extracted_archives/original"))
    freshly_parsed = controller_asset(source)
    extracted_animation = read_json(animation_path)["models"]["reinhard01"]
    assert {k: extracted_animation[k] for k in freshly_parsed} == freshly_parsed
    staged_actor = read_json(STAGING / "player/manifest.json")["actors"]["reinhard01"]
    staged_animation = read_json(STAGING / "player/animation.json")["models"]["reinhard01"]
    assert actor == staged_actor and extracted_animation == staged_animation
    assert freshly_parsed["sha256"] == reference(source)["sha256"]

    # Existing full-frame observations are rebound by SHA only here. There is
    # no newly assembled visual witness, so this routine must never turn these
    # resource checks into a character-field proposal or a costume verdict.
    native_path = ROOT / "story_crowd_data/native/scenes/10040004.json"
    review_path = ROOT / "story_crowd_data/review/scenes/10040004.json"
    native_rows = {n["scenario_id"]: n for n in read_json(native_path)["scenario_list"]}
    review_rows = read_json(review_path)["scenarios"]
    pending = []
    for row in request["pendingNodes"]:
        node = row["scenarioId"]
        assert native_rows[node]["character"] == ""
        assert review_rows[str(node)]["stableKey"] == row["stableKey"]
        assert review_rows[str(node)]["sourceText"] == row["sourceText"]
        assert reference(row["originalFullFrame"]["file"])["sha256"] == row["originalFullFrame"]["sha256"]
        pending.append(dict(**row, decision="assembled_reference_pending_no_character_assignment",
                            expected={"character": ""}, rootConfirmed=False))

    alternatives = []
    for family in ["reinhard_formal01", "reinhard_idle01", *request["otherFamilyCandidatesNotVisuallyRejected"]]:
        family_root = LIME.parents[1] / ("ac_" + family) / "ac"
        paths = [family_root / "ac.model3.json", family_root / "ac.moc3", family_root / "textures/texture_00.png"]
        alternatives.append(dict(model=family, originalFiles=[reference(p) for p in paths if p.is_file()],
            originalFilesMissing=[str(p) for p in paths if not p.is_file()],
            nativeUnityEquivalenceChecked=False, assembledReferenceChecked=False,
            storyIdentityAccepted=False,
            priorCandidateStatus="texture-only visually different garment construction" if family in {"reinhard_formal01", "reinhard_idle01"} else "not visually excluded"))

    preflight = R / "reinhard-staging-root-preflight-v1.json"
    audit = dict(schema="stella.original_model_resource_equivalence.v1", reviewer=REVIEWER,
        status="resource_equivalence_pass_story_identity_pending", model="reinhard01",
        proposedToken="live2d/AC_reinhard01", rootConfirmed=False,
        originalRequest=reference(request_path), tool=reference(Path(__file__)),
        runtimeVersions=dict(UnityPy=importlib.metadata.version("UnityPy"), Pillow=importlib.metadata.version("Pillow")),
        originalPrefab=reference(source), originalBasePrefab=reference(base),
        sourceObjectCounts=dict(Counter(o.type.name for o in environment.objects)),
        modelBindings=model_binding_ref, originalController=controller_ref, originalBaseDecoded=base_ref,
        moc=dict(objectPathId=moc_id, name=moc["m_Name"], byteCount=len(embedded_moc),
                 embeddedSha256=sha(embedded_moc), limeos=reference(LIME / "ac.moc3"),
                 staged=reference(STAGING / "models/reinhard01/ac/ac.moc3"),
                 originalEmbeddedEqualsLimeosEqualsStaged=True),
        texture=dict(objectPathId=texture_object.path_id, dimensions=list(decoded.size),
                     originalDecodedRgbaSha256=sha(decoded.tobytes()),
                     limeosDecodedRgbaSha256=sha(lime_texture.tobytes()),
                     stagedDecodedRgbaSha256=sha(staged_texture.tobytes()),
                     originalDecodedEqualsLimeosEqualsStaged=True,
                     rendererComponentCount=len(renderers), allRendererTexturePointersMatch=True,
                     limeos=reference(LIME / "textures/texture_00.png"),
                     staged=reference(STAGING / "models/reinhard01/ac/textures/texture_00.png")),
        limeosModel=reference(model_json), referencedFileCount=40,
        modelJsonAndAllReferencedFilesByteEquivalent=True, fileEquivalence=file_equivalence,
        controller=dict(pathId=controller_id, name=controller["m_Name"], animationClipSlotCount=38,
                        everyClipPointerAndExternalCabResolved=True, clips=sorted(clips, key=lambda x:x["controllerSlot"]),
                        freshlyParsedEqualsExtractedAnimation=True, stagedAnimationEqualsExtracted=True,
                        parser=reference(ROOT / "story_studio/actor_assets.py"),
                        originalAnimation=reference(animation_path), stagedAnimation=reference(STAGING / "player/animation.json")),
        basePlacement=dict(CH_top=ch_top, actorEntry=actor, transformMatchesOriginalManifest=True,
                           stagedActorEqualsOriginalManifest=True, originalManifest=reference(manifest_path),
                           stagedManifest=reference(STAGING / "player/manifest.json")),
        staging=dict(integrationPlan=reference(STAGING / "integration-plan.json"),
                     audit=reference(STAGING / "audit.json"), catalog=reference(STAGING / "catalog.json"),
                     package=reference(STAGING / "package.json"),
                     rootPreflight=reference(preflight) if preflight.is_file() else None,
                     integratedByThisReviewer=False),
        pendingStoryObservations=pending, familyCandidates=alternatives,
        unknown=dict(exactAssembledCostumeMatch=True, sourceStoryCharacterFields=True,
                     sourceMotionExpression=True, sourceCommandOnsetPhaseTiming=True,
                     convertedMotionCurveEquivalence=True, visualGeometryAcceptance=True),
        acceptance=dict(resourceIdentityEquivalence=True, storyIdentity=False, motion=False,
                        expression=False, position=False, fullPart=False, newActualPlayback=False),
        requiredNextStep="Explicitly schedule a new unique-browser exact-model assembled reference with JSON/MOC/texture/controller/actor bindings, then directly review all five original full frames against that capture. Keep the five character fields empty until that independent step passes.",
        browserOpened=False, formalDataWrites=False, gitWrites=False)
    audit_ref = write_new("reinhard01-original-unity-equivalence-audit.json", audit)
    delivery = write_new("reinhard01-equivalence-delivery.json", dict(
        schema="stella.offline_resource_review_delivery.v1", reviewer=REVIEWER,
        audit=audit_ref, originalController=controller_ref, modelBindings=model_binding_ref,
        originalBaseDecoded=base_ref, tool=reference(Path(__file__)),
        status="resource_equivalence_pass_5_story_identities_pending", newCharacterFields=0,
        browserOpened=False, formalDataWrites=False, gitWrites=False))
    print(json.dumps(dict(status="pass", audit=audit_ref, delivery=delivery,
                          mocSha256=sha(embedded_moc), rgbaSha256=sha(decoded.tobytes()),
                          referencedFiles=40, clips=38, pendingStoryIdentities=5)))


if __name__ == "__main__":
    main()
