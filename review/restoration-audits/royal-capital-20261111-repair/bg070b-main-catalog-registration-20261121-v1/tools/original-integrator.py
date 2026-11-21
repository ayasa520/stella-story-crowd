"""Install a reviewed additive asset stage after validating every input byte."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from story_studio.recovery.native_install import atomic_write


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def integrate(plan_path, receipt_path):
    plan = json.loads(plan_path.read_bytes())
    target = Path(plan["target"]).resolve()
    head = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
    assert head == plan["expectedBaseHead"], "Asset review base changed; rebind before installing"
    assert target.name == "assets" and target.parent.name == "data-checkout"
    snapshots, writes = {}, {}
    # Asset stages are independent of the scene importer. Validate the entire
    # additive transaction before copying its first binary, including reused
    # compressed media. This prevents a partial catalog from exposing payloads
    # that were never checked against the independently reviewed original.
    for name, expected in plan["sourceMetadataLocks"].items():
        raw = (target / name).read_bytes()
        assert sha(raw) == expected, f"Metadata changed: {name}"
        snapshots[name] = raw
    for name, expected in plan["reusedPayloadLocks"].items():
        assert sha((target / name).read_bytes()) == expected, f"Reused asset changed: {name}"
    for change in plan["changes"]:
        name = change["path"]
        destination = (target / name).resolve()
        assert destination.is_relative_to(target), name
        raw = Path(change["source"]).read_bytes()
        assert len(raw) == change["bytes"] and sha(raw) == change["sha256"], name
        expected = change["expectedSha256"]
        assert (sha(destination.read_bytes()) if destination.exists() else None) == expected, name
        snapshots[name] = destination.read_bytes() if destination.exists() else None
        writes[name] = raw
    before_catalog = json.loads(snapshots["catalog.json"])
    after_catalog = json.loads(writes["catalog.json"])
    for section, entries in before_catalog.items():
        if isinstance(entries, dict):
            assert all(after_catalog[section].get(key) == value for key, value in entries.items()), section
        else:
            assert after_catalog[section] == entries, section
    # Recheck just before the ordered writes. Payloads precede catalog/package
    # metadata so a committed stage never names an absent original resource.
    for name, raw in snapshots.items():
        destination = target / name
        assert (destination.read_bytes() if destination.exists() else None) == raw, name
    for name in sorted(writes, key=lambda name: name in {"catalog.json", "package.json"}):
        atomic_write(target / name, writes[name])
    verified = {name: sha((target / name).read_bytes()) for name in writes}
    assert verified == {name: sha(raw) for name, raw in writes.items()}
    receipt = {"status": "installed-and-read-back", "baseHead": head, "plan": str(plan_path),
               "planSha256": sha(plan_path.read_bytes()), "files": verified,
               "sceneFieldsChanged": False, "runtimePlaybackAccepted": False}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "files": list(verified)}))


if __name__ == "__main__":
    integrate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
