"""Bounded owned-role attribution for the existing summed-RSS budget only.

Importing this module performs no sampling. It launches no browser, changes no
limit, and makes no program/actor/clock/acceptance decision. A future separately
reviewed supervisor calls sample() at its existing budget boundary.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


class OwnedMemoryDiagnostic:
    MAX_ROWS = 128
    MAX_STATE_BYTES = 32768
    MAX_CROSSING_BYTES = 32768
    MAX_FALLBACK_BYTES = 73728
    WINDOW_SAMPLES = 4
    MAX_ROLLUP_PIDS = 8

    def __init__(self, output, *, rollup_on_first=True):
        self.output = Path(output)
        self.rollup_on_first = rollup_on_first
        self.sequence = 0
        self.first = None
        self.peak = None
        self.window = []
        self.crossing_written = False
        self.role_peaks = {}
        self.write_failure_reported = False
        self.crossing_failure_reported = False

    @staticmethod
    def _encode(value):
        return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()

    @staticmethod
    def _proof(raw):
        return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def _rollups(self, rows):
        # PSS is explicitly a second, later observation, never the RSS gate.
        # Only the largest eight observed owned contributors are read; missing
        # or inaccessible files are unknown, not zero or a complete PSS total.
        selected = sorted((row for row in rows if row['rssBytes'] is not None),
                          key=lambda row: (-row['rssBytes'], row['pid']))[:self.MAX_ROLLUP_PIDS]
        result = []
        for row in selected:
            item = {'pid': row['pid'], 'pgid': row['pgid'], 'role': row['role'],
                    'readStartedMonotonicNs': time.monotonic_ns()}
            try:
                raw = Path('/proc/' + str(row['pid']) + '/smaps_rollup').read_bytes()
                item['firstRead'] = self._proof(raw)
                values = {}
                for line in raw.decode('ascii').splitlines():
                    fields = line.split()
                    if fields and fields[0] in ('Rss:', 'Pss:'):
                        assert len(fields) == 3 and fields[2] == 'kB'
                        values[fields[0][:-1] + 'Bytes'] = int(fields[1]) * 1024
                assert set(values) == {'RssBytes', 'PssBytes'}
                item.update(values)
            except Exception as error:
                item.update(error=str(error), errorType=type(error).__name__)
            item['readEndedMonotonicNs'] = time.monotonic_ns()
            result.append(item)
        return {'selection': 'largest observed RSS, at most eight owned PIDs',
                'observedOwnedPids': len(rows), 'selectedPids': len(selected),
                'completeOwnedPssTotalClaimed': False, 'rows': result}

    def _persist(self, sample, rss_limit):
        bounded = sample
        if len(sample['rows']) > self.MAX_ROWS:
            # Keep the original RSS sum over ALL owned processes. A diagnostic
            # representation limit cannot remove a contributor from the gate.
            # Do not label an over-scope attribution packet as complete.
            bounded = {key: value for key, value in sample.items() if key != 'rows'}
            bounded.update(rows=[], attributionComplete=False,
                           diagnosticError='owned row cap exceeded',
                           completeRowsProof=self._proof(self._encode(sample['rows'])))
        self.first = self.first or bounded
        if self.peak is None or sample['summedOwnedProcessRssBytes'] >= self.peak['summedOwnedProcessRssBytes']:
            self.peak = bounded
        self.window.append(bounded)
        self.window = self.window[-self.WINDOW_SAMPLES:]
        for role, value in sample['roleRssBytes'].items():
            self.role_peaks[role] = max(value, self.role_peaks.get(role, 0))
        while True:
            samples = {item['sequence']: item for item in [self.first, self.peak, *self.window]}
            state = {'schema': 'stella.owned-memory-bounded-attribution.v1',
                     'rssGateBytesUnchanged': rss_limit, 'samplesObserved': self.sequence,
                     'firstSequence': self.first['sequence'], 'peakSequence': self.peak['sequence'],
                     'retainedSequences': sorted(samples),
                     'nonretainedSampleCount': self.sequence - len(samples),
                     'completeHistoryClaimed': False, 'perRolePeakSummedRssBytes': self.role_peaks,
                     'samples': [samples[key] for key in sorted(samples)]}
            raw = self._encode(state)
            if len(raw) <= self.MAX_STATE_BYTES or not self.window:
                break
            self.window.pop(0)
        if len(raw) > self.MAX_STATE_BYTES:
            # Metadata-only fallback is bounded and explicitly incomplete.
            state = {'schema': state['schema'], 'samplesObserved': self.sequence,
                     'rssGateBytesUnchanged': rss_limit, 'attributionComplete': False,
                     'diagnosticError': 'state byte cap exceeded',
                     'completeStateProof': self._proof(raw),
                     'currentSummedOwnedProcessRssBytes': sample['summedOwnedProcessRssBytes']}
            raw = self._encode(state)
        temporary = self.output / 'memory-role-samples.json.tmp'
        final = self.output / 'memory-role-samples.json'
        try:
            # One bounded rolling file is replaced after every budget sample.
            # Prior windows are explicitly superseded, not a full raw history.
            with temporary.open('wb') as stream:
                stream.write(raw)
            os.replace(temporary, final)
            if sample['summedOwnedProcessRssBytes'] > rss_limit and not self.crossing_written:
                crossing = self._encode(bounded)
                if len(crossing) > self.MAX_CROSSING_BYTES:
                    crossing = self._encode({'sequence': sample['sequence'], 'attributionComplete': False,
                        'diagnosticError': 'crossing byte cap exceeded',
                        'completeCrossingProof': self._proof(crossing),
                        'summedOwnedProcessRssBytes': sample['summedOwnedProcessRssBytes']})
                with (self.output / 'memory-role-first-crossing.json').open('xb') as stream:
                    stream.write(crossing)
                self.crossing_written = True
        except Exception as error:
            # Telemetry I/O does not replace or relax the pre-existing RSS
            # decision. At most one ordinary fallback and one first-crossing
            # fallback are emitted; a broken disk cannot create an unbounded
            # stderr history on every subsequent budget poll.
            crossing_now = sample['summedOwnedProcessRssBytes'] > rss_limit
            report = (crossing_now and not self.crossing_failure_reported) or not self.write_failure_reported
            self.write_failure_reported = True
            self.crossing_failure_reported |= crossing_now
            if report:
                try:
                    fallback = self._encode({
                        'error': str(error)[:1024], 'traceback': traceback.format_exc()[-4096:],
                        'boundedState': state})
                    if len(fallback) > self.MAX_FALLBACK_BYTES:
                        fallback = self._encode({'diagnosticError': 'stderr fallback byte cap exceeded',
                            'attributionComplete': False, 'completeFallbackProof': self._proof(fallback),
                            'summedOwnedProcessRssBytes': sample['summedOwnedProcessRssBytes']})
                    sys.stderr.buffer.write(b'OWNED_MEMORY_DIAGNOSTIC_WRITE_FAILED ' + fallback)
                    sys.stderr.buffer.flush()
                except Exception:
                    # Both diagnostic sinks can fail. This establishes no
                    # attribution proof, but must still reach the RSS assert.
                    pass

    def sample(self, owned, *, rss_limit):
        self.sequence += 1
        started = time.monotonic_ns()
        groups = {process.pid: role for role, process in owned}
        # Hold exactly ONE identity snapshot. No full command arguments or
        # unowned rows are persisted, and a later ps result is not used to label
        # RSS values after the fact. Each selected statm file is read once.
        raw = subprocess.check_output(['/usr/bin/ps', '-eo', 'pid=,ppid=,pgid=,comm='])
        page_size = os.sysconf('SC_PAGE_SIZE')
        rows, vanished, role_totals = [], [], {}
        rss, statm_failure = 0, None
        for line in raw.decode('utf-8').splitlines():
            fields = line.strip().split(None, 3)
            if len(fields) < 4:
                continue
            pid, ppid, pgid = map(int, fields[:3])
            if pgid not in groups:
                continue
            row = {'pid': pid, 'ppid': ppid, 'pgid': pgid,
                   'role': groups[pgid], 'comm': fields[3], 'rssBytes': None}
            try:
                held_statm = Path('/proc/' + str(pid) + '/statm').read_bytes()
                pages = int(held_statm.split()[1])
                row.update(residentPages=pages, rssBytes=pages * page_size,
                           statmFirstRead=self._proof(held_statm))
                rss += row['rssBytes']
                role_totals[row['role']] = role_totals.get(row['role'], 0) + row['rssBytes']
            except FileNotFoundError:
                row['vanishedDuringStatmRead'] = True
                vanished.append(pid)
            except Exception as error:
                # Preserve the original failing read/parse exception, after
                # writing the known partial attribution. An unknown PID is
                # never silently treated as a zero-RSS complete observation.
                row.update(readError=str(error), readErrorType=type(error).__name__)
                statm_failure = (error, error.__traceback__)
            rows.append(row)
            if statm_failure is not None:
                break
        sample = {'sequence': self.sequence, 'startedMonotonicNs': started,
                  'identitySnapshotProof': self._proof(raw), 'pageSizeBytes': page_size,
                  'identitySource': 'one held ps(pid,ppid,pgid,comm), without args',
                  'rssSource': 'one held statm resident-pages read per selected PID',
                  'crossPidAtomicSnapshotClaimed': False, 'sharedPagesCountedPerProcess': True,
                  'summedOwnedProcessRssBytes': rss, 'roleRssBytes': role_totals,
                  'rows': sorted(rows, key=lambda row: row['pid']),
                  'vanishedDuringRead': vanished,
                  'rssSumComplete': statm_failure is None and not vanished,
                  'attributionComplete': statm_failure is None and not vanished}
        crossing = rss > rss_limit
        if (self.sequence == 1 and self.rollup_on_first) or (crossing and not self.crossing_written):
            sample['smapsRollup'] = self._rollups(rows)
        sample['endedMonotonicNs'] = time.monotonic_ns()
        self._persist(sample, rss_limit)  # Persist BEFORE the caller's original assertion.
        if statm_failure is not None:
            error, original_traceback = statm_failure
            raise error.with_traceback(original_traceback)
        return sample
