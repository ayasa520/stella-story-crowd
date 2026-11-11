"""Prepare or integrate an additive native-asset package with guarded metadata.

Preparation reuses the existing crowd asset exporters but never invokes their
whole-project build/player methods: those intentionally filter model sets for a
bounded pilot. This incremental workflow instead preserves every existing row,
adds only missing resources, and merges selected model controller records into
the current shared player manifests. Integration is a separate explicit mode.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import logging
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "story_studio/crowd_assets.py").is_file())
sys.path.insert(0, str(ROOT))

from story_studio.crowd_assets import AssetWriter, PilotAssetPackage, PilotReferences, read_json, sha256
from story_studio.paths import DEFAULT_STUDIO_CONFIG, load_studio_configuration


METADATA_FILES = {"catalog.json", "package.json", "player/manifest.json", "player/animation.json",
                  "player/motion_states.json", "player/effects.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def guarded_merge(existing, additions, label):
    """Only append keys; an existing logical identity cannot silently change."""
    result = deepcopy(existing)
    for key, value in additions.items():
        require(key not in result or result[key] == value, f"Conflicting {label} identity: {key}")
        result[key] = deepcopy(value)
    return result


def checked_path(directory, relative):
    result = (directory / relative).resolve()
    require(result.is_relative_to(directory.resolve()) and result != directory.resolve(),
            f"Unsafe asset relative path: {relative}")
    return result


class AssetIncrement:
    """Export resources, merge immutable baseline metadata, and record a plan."""

    def __init__(self, output, packets, models, banks, music, effects, movies, backgrounds=None):
        self.root, self.config = load_studio_configuration(DEFAULT_STUDIO_CONFIG)
        self.baseline = self.root / "story_crowd_data/assets"
        self.output = output.resolve()
        require(not self.output.exists(), "Use a fresh output directory to retain prior build evidence")
        self.catalog = read_json(self.baseline / "catalog.json")
        self.index = read_json(self.baseline / "package.json")
        self.source_locks = {name: sha256(self.baseline / name) for name in METADATA_FILES}
        self.project_path = self.root / "data/story_studio/project.json"
        self.project_sha256 = sha256(self.project_path)
        self.project = read_json(self.project_path)
        self.packet_locks, self.packet_scenes = [], set()
        # Availability can precede a story-field approval. Accept explicit
        # resource selections without manufacturing a root-confirmed node patch
        # merely to export its background. Signed packets remain an independent
        # source of resource references and retain their existing guards.
        backgrounds = set(backgrounds or ())
        for path in packets:
            packet = read_json(path)
            self.packet_locks.append(dict(path=str(path.resolve().relative_to(self.root)), sha256=sha256(path)))
            for row in packet["changes"]:
                require(row.get("rootConfirmed") is True, f"Unsigned resource patch in {path}")
                fields = row["fields"]
                self.packet_scenes.add(row["sceneId"])
                if fields.get("bg_picture"):
                    backgrounds.add(fields["bg_picture"])
                if fields.get("character"):
                    require(fields["character"].startswith("live2d/AC_"), "Unsupported native model identity")
                    models.add(fields["character"].removeprefix("live2d/AC_"))
                if fields.get("bg_music"):
                    # STOP is a native sparse music control value, never an
                    # audio resource. Preserve the authored event in the signed
                    # packet while exporting only actual original cue names.
                    resource = fields["bg_music"].split(",", 1)[0]
                    if resource != "STOP":
                        music.add(resource)
                if fields.get("voice"):
                    banks.add(fields["voice"].split(",", 1)[0])
                if fields.get("video"):
                    movies.add(fields["video"])
                effects.update(PilotReferences.command_resources(fields.get("command", []), ("PlayFX", "FX")))
        self.requested = dict(models=sorted(models), backgrounds=sorted(backgrounds),
                              banks=sorted(banks), music=sorted(music), effects=sorted(effects), movies=sorted(movies))
        existing_effects = read_json(self.baseline / "player/effects.json")["resources"]
        self.refs = SimpleNamespace(models={model for model in models if "live2d/AC_" + model not in self.catalog["models"]},
            backgrounds=backgrounds - self.catalog["backgrounds"].keys(),
            banks=banks - self.catalog["voices"].keys(), music=music - self.catalog["music"].keys(),
            effects=effects - existing_effects.keys(), movies=movies - self.catalog["movies"].keys())
        self.writer = AssetWriter(self.output, self.root)
        self.package = PilotAssetPackage(self.root, self.config, self.project, self.writer, self.refs, "128k")

    def validate_baseline(self):
        # Validate the existing index against actual files before merging it.
        # Merely carrying forward an old digest would hide a pre-existing
        # package/index disagreement and make the preservation claim meaningless.
        for name, row in self.index["files"].items():
            path = checked_path(self.baseline, name)
            require(path.is_file() and path.stat().st_size == row["bytes"] and sha256(path) == row["sha256"],
                    "Existing asset package/index mismatch: " + name)

    def merge_player_model_records(self):
        source = self.root / self.config["player_assets"]
        mappings = (("manifest.json", "actors", source / "manifest.json"),
                    ("animation.json", "models", source / "animation.json"),
                    ("motion_states.json", "models", self.root / self.package.catalog.config["motion_index"]))
        counts = {}
        for name, field, original_path in mappings:
            current = read_json(self.baseline / "player" / name)
            original = read_json(original_path)
            additions = {model: original[field][model] for model in sorted(self.refs.models)}
            merged = deepcopy(current)
            merged[field] = guarded_merge(current[field], additions, "player " + name)
            require(all(merged[field][key] == value for key, value in current[field].items()),
                    "An existing player model record changed: " + name)
            if additions:
                self.writer.json("player/" + name, merged, original_path)
            counts[name] = dict(before=len(current[field]), after=len(merged[field]), added=sorted(additions))
        return counts

    def validate_merged_references(self, catalog, index):
        def resolve(name):
            staged = checked_path(self.output, name)
            return staged if staged.is_file() else checked_path(self.baseline, name)

        def walk(document):
            if isinstance(document, dict):
                for key, value in document.items():
                    if isinstance(value, str) and (key == "url" or key.endswith("_url")):
                        require(value in index["files"] and resolve(value).is_file(), "Missing catalog reference: " + value)
                    walk(value)
            elif isinstance(document, list):
                for row in document:
                    walk(row)

        walk(catalog)
        for model in catalog["models"].values():
            model_path = resolve(model["model_url"])
            model_document = read_json(model_path)

            def model_reference(value):
                if isinstance(value, dict):
                    for item in value.values():
                        model_reference(item)
                elif isinstance(value, list):
                    for item in value:
                        model_reference(item)
                elif isinstance(value, str):
                    require((model_path.parent / value).resolve().is_file(), "Missing Live2D dependency: " + value)

            model_reference(model_document["FileReferences"])
        require(all(url in index["files"] for url in catalog["members"].values()),
                "Merged member map contains an unindexed file")

    def merge_effects(self):
        """Append original cutin programs without filtering existing effects.

        The player's extracted geometry, animation clips and events remain
        verbatim. Only the logical desktop texture endpoint is projected to
        the catalog-owned browser file, matching PilotAssetPackage.player.
        Supporting a new effect type requires an explicit exporter; it must
        never be made playable by silently dropping its dependencies.
        """
        current = read_json(self.baseline / "player/effects.json")
        if not self.refs.effects:
            return current["resources"]
        source = self.root / self.config["player_assets"] / "effects.json"
        original = read_json(source)
        additions = {}
        for identity in sorted(self.refs.effects):
            row = deepcopy(original["resources"][identity])
            texture = row.get("texture", "")
            require(row.get("type") == "cutin" and texture.startswith("/cutin/"),
                    "Incremental effect needs a dedicated exporter: " + identity)
            cutin = self.package.media.cutins[texture.removeprefix("/cutin/")]
            member = cutin if isinstance(cutin, str) else cutin["member"]
            url = self.package.copied_member(member, "cutins/" + Path(member).name)
            row["texture"] = "/resource/" + url
            additions[identity] = row
        current["resources"] = guarded_merge(current["resources"], additions, "effect")
        current["sources"] = guarded_merge(current.get("sources", {}), original.get("sources", {}), "effect provenance")
        self.writer.json("player/effects.json", current, source)
        return current["resources"]

    def build(self):
        try:
            self.validate_baseline()
            additions = dict(models=self.package.models(),
                backgrounds=self.package.media_rows(self.refs.backgrounds, self.package.media.backgrounds, "backgrounds"),
                # Preserve complete original movie bytes and dimensions. Movie
                # presentation is owned by the native renderer; packaging must
                # not crop, retime, transcode or replace them with sampled frames.
                movies=self.package.media_rows(self.refs.movies, self.package.media.movies, "movies"),
                voices=self.package.voices(), music=self.package.music())
            effect_resources = self.merge_effects()
            merged = deepcopy(self.catalog)
            # Compilation and rendering must consult the same asset revision.
            # Expose only the execution contract here; the full native clips,
            # geometry and textures remain in player/effects.json.
            merged["visual_effects"] = {key: dict(blocking=value["blocking"])
                                        for key, value in effect_resources.items()}
            for field, values in additions.items():
                merged[field] = guarded_merge(self.catalog[field], values, "catalog " + field)
            merged["members"] = guarded_merge(self.catalog["members"], self.writer.members, "archive member")
            merged["asset_members"] = guarded_merge(self.catalog["asset_members"], self.writer.members, "asset member")
            player_counts = self.merge_player_model_records()
            self.writer.json("catalog.json", merged)
            files = deepcopy(self.index["files"])
            for name, record in self.writer.files.items():
                require(name not in files or name in METADATA_FILES or files[name] == record,
                        "Generated resource would replace existing asset: " + name)
                files[name] = deepcopy(record)
            index = deepcopy(self.index)
            index.update(files=dict(sorted(files.items())), bytes=sum(row["bytes"] for row in files.values()))
            self.validate_merged_references(merged, index)
            self.writer.json("package.json", index)
            require(sha256(self.project_path) == self.project_sha256, "Studio changed during preparation")
            require(all(sha256(self.baseline / name) == value for name, value in self.source_locks.items()),
                    "Asset metadata changed during preparation")
            changed_records = [name for name, row in self.index["files"].items() if files[name] != row]
            require(set(changed_records) <= METADATA_FILES, "Existing binary resource metadata changed")
            changes = []
            for name, row in sorted(self.writer.files.items()):
                old = self.baseline / name
                changes.append(dict(path=name, source=str(self.output / name), bytes=row["bytes"], sha256=row["sha256"],
                                    expectedSha256=sha256(old) if old.is_file() else None))
            plan = dict(version=1, mode="staged-additive-assets", target=str(self.baseline),
                        sourceMetadataLocks=self.source_locks, packetLocks=self.packet_locks,
                        sourceProjectSha256=self.project_sha256, changes=changes)
            audit = dict(version=1, status="prepared-not-integrated", requestedReferences=self.requested,
                additions={key:sorted(value) for key, value in vars(self.refs).items()},
                catalogCounts={key:dict(before=len(self.catalog[key]), after=len(merged[key])) for key in additions},
                playerModelCounts=player_counts, baselineFileCount=len(self.index["files"]),
                mergedFileCount=len(files), stagedFileCount=len(changes),
                baselineBytes=self.index["bytes"], mergedBytes=index["bytes"],
                existingChangedIndexRecords=changed_records,
                existingBinaryFilesPreserved=True, existingCatalogRowsPreserved=True,
                sourceProjectRevision=self.project["revision"], sourceProjectUnchanged=True,
                signedPacketSceneCount=len(self.packet_scenes), packetLocks=self.packet_locks,
                limitations=["Resource availability is not evidence that a cue, motion or BGM belongs at a particular node."])
            for name, document in (("integration-plan.json", plan), ("audit.json", audit)):
                (self.output / name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({key:audit[key] for key in ("catalogCounts", "playerModelCounts", "baselineFileCount",
                                                       "mergedFileCount", "stagedFileCount", "sourceProjectRevision")}, ensure_ascii=False))
        finally:
            self.package.catalog.close()


def integrate(plan_path, apply):
    """Preflight all changes before the root explicitly chooses integration.

    The existing file digest, generated digest, and every baseline metadata
    lock are checked before any mutation. Only files named by the reviewed
    plan are copied; native/review documents and Studio are outside its scope.
    """
    plan = read_json(plan_path)
    require(plan.get("version") == 1 and plan.get("mode") == "staged-additive-assets", "Unsupported asset integration plan")
    target = Path(plan["target"])
    require(target.resolve() == (ROOT / "story_crowd_data/assets").resolve(), "Unexpected asset target")
    for name, fingerprint in plan["sourceMetadataLocks"].items():
        require(sha256(checked_path(target, name)) == fingerprint, "Target asset metadata changed: " + name)
    for change in plan["changes"]:
        source, destination = Path(change["source"]), checked_path(target, change["path"])
        require(source.is_file() and source.stat().st_size == change["bytes"] and sha256(source) == change["sha256"],
                "Staged asset changed: " + change["path"])
        expected = change["expectedSha256"]
        require((not destination.exists()) if expected is None else (destination.is_file() and sha256(destination) == expected),
                "Target resource changed: " + change["path"])
    if apply:
        # Metadata follows payload files so a live reader never sees a new
        # catalog entry before its resource exists. package.json is written last.
        ordered = sorted(plan["changes"], key=lambda row:(row["path"] in METADATA_FILES,
                                                          row["path"] == "package.json", row["path"]))
        for change in ordered:
            destination = checked_path(target, change["path"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".asset-repair-tmp")
            require(not temporary.exists(), "Unexpected pending asset temporary file")
            shutil.copyfile(change["source"], temporary)
            temporary.replace(destination)
        require(all(sha256(checked_path(target, row["path"])) == row["sha256"] for row in plan["changes"]),
                "Integrated asset verification failed")
    print(json.dumps(dict(status="integrated" if apply else "preflight-only", files=len(plan["changes"]))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--packet", type=Path, action="append", default=[])
    parser.add_argument("--model", action="append", default=["rom01"])
    parser.add_argument("--background", action="append", default=[])
    parser.add_argument("--bank", action="append", default=["vo_adv_rom"])
    parser.add_argument("--music", action="append", default=["bgm_adv_comical02_cd2_09"])
    parser.add_argument("--effect", action="append", default=[])
    parser.add_argument("--movie", action="append", default=[])
    parser.add_argument("--integration-plan", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.integration_plan:
        integrate(args.integration_plan, args.apply)
    else:
        require(args.output is not None and not args.apply, "Preparation requires --output; --apply requires an integration plan")
        AssetIncrement(args.output, args.packet, set(args.model), set(args.bank), set(args.music),
                       set(args.effect), set(args.movie), backgrounds=set(args.background)).build()


if __name__ == "__main__":
    main()
