"""Read back a bounded installed packet against its previous Git commit.

This verifies exact native changes independently of the publisher. It neither
repeats visual review nor grants playback acceptance. The publication-wide
resource, ownership, baseline and Studio audit remains a separate responsibility.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/rikka/Projects/stella')
DATA = ROOT / 'story_crowd_data'
sys.path.insert(0, str(ROOT))
from story_studio.recovery.native_repair import InstalledSnapshot


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), 'Use a fresh output path')
    packet = json.loads(args.packet.read_text())
    snapshot = InstalledSnapshot(ROOT, DATA)
    grouped, identities, counts = defaultdict(dict), set(), Counter()
    for row in packet['changes']:
        identity = (row['sceneId'], row['scenarioId'])
        require(identity not in identities and row['rootConfirmed'] is True,
                'Duplicate or unaccepted node')
        identities.add(identity)
        native, review = snapshot.node(*identity, row['stableKey'])
        require(review['sourceText'] == row['sourceText'], 'Japanese source changed')
        require(all(native[key] == value for key, value in row['fields'].items()),
                'Installed fields differ from the accepted packet')
        grouped[row['sceneId']][row['scenarioId']] = row
    files = []
    for scene, rows in grouped.items():
        relative = f'native/scenes/{scene}.json'
        old = json.loads(subprocess.check_output(['git', 'show', f'{args.base}:{relative}'], cwd=DATA))
        current_raw = (DATA / relative).read_bytes()
        current = json.loads(current_raw)
        require({key: value for key, value in old.items() if key != 'scenario_list'} ==
                {key: value for key, value in current.items() if key != 'scenario_list'},
                'Scene-level native metadata changed')
        require(len(old['scenario_list']) == len(current['scenario_list']), 'Native row count changed')
        observed = set()
        for before, after in zip(old['scenario_list'], current['scenario_list']):
            require(before['scenario_id'] == after['scenario_id'], 'Native row order changed')
            if before == after:
                continue
            scenario = after['scenario_id']
            require(scenario in rows, 'Unapproved native node changed')
            row = rows[scenario]
            require(all(before[key] == value for key, value in row['expected'].items()),
                    'Previous node did not satisfy the accepted precondition')
            expected = dict(before, **row['fields'])
            require(after == expected, 'Native properties outside the packet changed')
            observed.add(scenario)
            counts.update(row['fields'].keys())
        require(observed == set(rows), 'Accepted native changes are missing')
        files.append(dict(path=relative, sha256=hashlib.sha256(current_raw).hexdigest(),
                          scenarioIds=sorted(observed)))
    snapshot.unchanged_on_disk()
    require(all(isinstance(value, int) and value > 0 for value in counts.values()),
            'Changed field counts must be positive integers')
    result = dict(status='passed_exact_installed_packet_readback', baseCommit=args.base,
                  packetSha256=hashlib.sha256(args.packet.read_bytes()).hexdigest(),
                  nodes=len(identities), changedFieldCounts=dict(counts), nativeFiles=files,
                  mainThreadViewedImages=False, formalWrites=0, browserOpened=False)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
