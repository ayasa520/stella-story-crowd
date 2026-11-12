"""Archive one actual ARM program baseline and its source/byte/closure proofs.

The normal production compiler ran once with an empty registry. This evidence
commit changes neither story fields nor runtime sources, and never upgrades a
source-only capture-kit pass to a browser, acting or complete chapter pass.
"""
import json
from pathlib import Path
import subprocess

from target_identity_publication_v1 import archive_files, read, write_new

ROOT = Path('/home/rikka/Projects/stella')
R = Path(__file__).parent
DATA = ROOT / 'story_crowd_data'
NAME = 'target-arm-baseline-evidence-20261112-v1'


def selected_files(folder):
    return {p for p in folder.rglob('*') if p.is_file() and p.suffix in
            ('.json', '.py', '.mjs', '.html', '.md', '.log', '.txt', '.bin', '.diff')
            and '__pycache__' not in p.parts}


def main():
    def git(*args):
        return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=DATA)
    assert not git('status', '--porcelain')
    head = git('rev-parse', 'HEAD').decode().strip()
    baseline = R / 'target-arm-baseline-20261112-v1'
    runtime = read(baseline / 'runtime-result.json')
    closed = read(baseline / 'closure.json')
    peer = read(R / 'target-arm-baseline-peer-20261112-v1/FINAL.json')
    assert runtime['status'] == 'passed_actual_arm_canonical_compilation'
    assert peer['status'] == 'bounded_actual_compilation_readback_passed'
    assert closed['status'] == 'owned_adapter_and_compiler_closed_all_baseline_guards_unchanged'
    assert closed['relevantLiveProcesses'] == [] and closed['guardsRechecked'] == 836
    assert read(baseline / 'root-release.json')['dataHead'] == head
    assert runtime['nodeCount'] == 5599 and runtime['edgeCount'] == 5845
    paths = selected_files(baseline)
    paths.update(selected_files(R / 'target-arm-baseline-peer-20261112-v1'))
    paths.update(selected_files(R / 'target-arm-adapter-peer-20261112-v2'))
    # Keep both completed author revisions and their historical semantic diff.
    # Generated compiler stdout is exact evidence; repeated byte-identical .bin
    # inputs are deduplicated by the archive's content-addressed storage.
    for version in (1, 2):
        paths.update(selected_files(R / f'target-arm-adapter-20261112-v{version}'))
    paths.update({Path(__file__), R / 'target_prepare_arm_baseline_v1.cjs',
                  R / 'target_identity_publish_git_v1.py', R / 'PROGRESS.md',
                  R / 'playback/serve.py', R / 'playback/compile.mjs', R / 'playback/index.html'})
    destination = DATA / 'review/restoration-audits/royal-capital-20261111-repair' / NAME
    work = R / NAME
    assert not work.exists() and not destination.exists()
    work.mkdir()
    copied, local = archive_files(destination, paths)
    report = dict(status='actual_arm_baseline_evidence_verified', baseCommit=head,
        nativeFieldsChangedByThisCheckpoint=0, actualCompileRequests=1,
        programSha256=runtime['programSha256'], programBytes=runtime['programBytes'],
        nodeCount=5599, edgeCount=5845, knownCharacterFieldsMapped=45,
        frozenGuardsRechecked=836, canonicalTrackedBlobsChecked=289,
        adapterAndCompilerClosed=True, browserStarted=False, newPlaybackVisits=0,
        actualRestorationVisits=207, motionFaceGeometryOrContinuousPlaybackAccepted=False,
        fullRestorationAccepted=False)
    write_new(destination / 'MANIFEST.json', dict(schema='stella.exact_evidence_archive.v1',
        **report, copiedFiles=copied, localOnlyEvidence=local))
    files = [str(p.relative_to(DATA)) for p in sorted(destination.rglob('*')) if p.is_file()]
    assert not git('diff', '--name-only')
    assert set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == set(files)
    write_new(work / 'owned-files.json', dict(baseCommit=head, files=files, report=report))
    print(json.dumps(dict(work=str(work), copiedSources=len(copied), localOnly=len(local),
                         gitFiles=len(files), baseCommit=head)))


if __name__ == '__main__':
    main()
