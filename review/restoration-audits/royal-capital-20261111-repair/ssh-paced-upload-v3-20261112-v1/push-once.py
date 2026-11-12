"""Observe one Git ref transaction over the reviewed coarse-pacing candidate."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = Path('/home/rikka/Projects/stella')
ssh = shlex.join(['/usr/bin/python3', str(HERE.parent / 'github_ssh_paced_v3.py'),
                  '-vvv', '-E', str(HERE / 'ssh-debug.log')])
arguments = ['git', '-c', 'pack.threads=1', '-c', 'core.sshCommand=' + ssh,
             'push', '--progress', 'origin', 'main']
started = time.monotonic()
with (HERE / 'push.log').open('w') as output:
    process = subprocess.Popen(arguments, cwd=ROOT / 'story_crowd_data',
                               stdin=subprocess.DEVNULL, stdout=output, stderr=output)
    with (HERE / 'owned-ssh-sockets.jsonl').open('w') as samples:
        while process.poll() is None:
            # Collect only this Git transaction's SSH descendants. System or
            # unrelated application sockets are neither persisted nor changed.
            descendants = {process.pid}
            rows = [line.split(None, 2) for line in subprocess.check_output(
                ['ps', '-eo', 'pid=,ppid=,comm='], text=True).splitlines()]
            changed = True
            while changed:
                changed = False
                for pid, parent, _ in rows:
                    if int(parent) in descendants and int(pid) not in descendants:
                        descendants.add(int(pid))
                        changed = True
            pids = {int(pid) for pid, _, name in rows if name == 'ssh' and int(pid) in descendants}
            lines = subprocess.check_output(['ss', '-tinp'], text=True).splitlines()
            blocks = [lines[i:i+2] for i, line in enumerate(lines)
                      if any('pid=' + str(pid) + ',' in line for pid in pids)]
            samples.write(json.dumps(dict(elapsedSeconds=time.monotonic()-started,
                gitPid=process.pid, sshPids=sorted(pids), ownedSocketBlocks=blocks)) + '\n')
            samples.flush()
            time.sleep(2)
result = dict(exitCode=process.returncode, elapsedSeconds=time.monotonic()-started,
              nice=os.getpriority(os.PRIO_PROCESS, 0), cpus=sorted(os.sched_getaffinity(0)),
              gitTransactionCount=1, stdinReplayed=False, repositoryConfigChanged=False)
(HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
raise SystemExit(process.returncode)
