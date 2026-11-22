"""Check native resource references against the installed player package.

Structural validation cannot detect an exported model that was omitted from
the package. Keep this check separate from reconstruction and rendering: it
does not choose resources, populate inherited values, or claim visual fidelity.
"""

import re
from pathlib import Path

from .native_rough import require


def validate_resources(document: dict, catalog: dict, assets: Path, scene: int) -> None:
    """Reject a repair whose explicit resources would produce missing loads.

    Model entries may contain native parameters and multiple LF-separated
    actors. Only their unambiguous resource prefix is inspected here; parameter
    interpretation belongs to the native actor parser. Movie identifiers are
    case-insensitive in the existing compiler, including the preserved original
    prologue's uppercase ADV name. Other resource identities remain exact.
    """
    movies = {key.lower(): key for key in catalog["movies"]}
    for row in document["scenario_list"]:
        references = []
        for entry in row["character"].splitlines():
            match = re.match(r"live2d/AC_[A-Za-z0-9_]+", entry.strip())
            require(match is not None, f"Unrecognized model reference: {scene}:{row['scenario_id']}")
            references.append(("models", match.group(0), "detail_url"))
        for section, field, path in (("backgrounds", "bg_picture", "url"),
                                     ("pictures", "character_image", "url"),
                                     ("music", "bg_music", "metadata_url"),
                                     ("voices", "voice", "detail_url"),
                                     ("movies", "video", "url")):
            resource = row[field].split(",", 1)[0]
            if not resource or (section == "music" and resource == "STOP"):
                continue
            if section == "movies":
                resource = movies.get(resource.lower(), resource)
            references.append((section, resource, path))
        for section, resource, field in references:
            prefix = f"{scene}:{row['scenario_id']} {section}/{resource}"
            require(resource in catalog[section], "Resource is absent from player catalog: " + prefix)
            metadata = catalog[section][resource]
            path = (assets / metadata[field]).resolve()
            require(path.is_relative_to(assets.resolve()) and path.is_file(),
                    "Resource payload is absent from player package: " + prefix)
