"""Enforce the observed Chrome thread priorities for this sole owned session.

Launching the CLI at nice19 did not preserve that value in the observed Chrome
processes. Retain the actual before/after values and correct only this user's
installed Chrome/crashpad executable threads while the owned session exists.
There is no second browser or systemwide scheduler configuration change.
"""
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
executables = {'/opt/google/chrome/chrome', '/opt/google/chrome/chrome_crashpad_handler'}
changes = []
seen = False
empty = 0
while empty < 4:
    active = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            if entry.stat().st_uid != os.getuid() or os.readlink(entry / 'exe') not in executables:
                continue
            active.append(int(entry.name))
            for thread in (entry / 'task').iterdir():
                tid = int(thread.name)
                before = os.getpriority(os.PRIO_PROCESS, tid)
                if before != 19:
                    os.setpriority(os.PRIO_PROCESS, tid, 19)
                    changes.append(dict(pid=int(entry.name), tid=tid, before=before,
                                        after=os.getpriority(os.PRIO_PROCESS, tid), wall=time.time()))
        except ProcessLookupError:
            pass
        except OSError as error:
            # A disappearing /proc entry is expected during normal Chrome
            # shutdown. An extant entry's error is retained for root review.
            if entry.exists():
                changes.append(dict(pid=int(entry.name), error=str(error)))
    seen = seen or bool(active)
    empty = empty + 1 if seen and not active else 0
    (HERE / 'owned-browser-priority-enforcement.json').write_text(json.dumps(dict(
        rootOwner='/root', observedOriginalPriorities='runtime-process-scheduling.json',
        activePids=active, changes=changes, ended=empty >= 4), indent=2) + '\n')
    time.sleep(.5)
print(json.dumps(dict(ended=True, corrections=len(changes))))
