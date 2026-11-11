import {performance} from 'node:perf_hooks';

// One absolute host clock owns the entire case, including Page creation and
// setup. Work stops ten seconds before the hard endpoint so cleanup/export do
// not consume the Page-close reserve. Promise races bound host waits; they do
// not pretend to cancel an underlying Playwright command or confirm OS exit.
export class CaseDeadline {
  constructor({totalMs = 45000, cleanupReserveMs = 10000} = {}) {
    this.started = performance.now();
    this.hardAt = this.started + totalMs;
    this.workAt = this.hardAt - cleanupReserveMs;
    this.closing = false;
    this.pending = new Map();
    this.next = 0;
    this.failures = [];
    this.fatal = new Promise((_, reject) => { this.rejectFatal = reject; });
    this.fatal.catch(() => {});
    this.abort = new AbortController();
    this.signal = this.abort.signal;
    this.hardTimer = setTimeout(() => this.abort.abort(Error('Absolute case deadline')), totalMs);
  }
  fail(error) {
    if (this.failures.length < 16) this.failures.push(String(error).slice(0, 700));
    this.rejectFatal(error);
  }
  beginCleanup() {
    this.closing = true;
    this.rejectFatal(Error('Case work ended; cleanup in progress'));
  }
  remaining({cleanup = false, reserveMs = 0} = {}) {
    return Math.max(0, Math.floor((cleanup ? this.hardAt - reserveMs : this.workAt) - performance.now()));
  }
  async within(label, operation, {cleanup = false, reserveMs = 0, maxMs = Infinity} = {}) {
    const absoluteAt = Math.min(cleanup ? this.hardAt - reserveMs : this.workAt, performance.now() + maxMs);
    if ((!cleanup && this.closing) || performance.now() >= absoluteAt) throw Error('Absolute deadline before ' + label);
    const token = ++this.next;
    const underlying = Promise.resolve().then(() => {
      if (performance.now() >= absoluteAt || (!cleanup && this.closing)) throw Error('Absolute deadline before starting ' + label);
      return operation();
    });
    this.pending.set(token, label);
    underlying.then(() => this.pending.delete(token), () => this.pending.delete(token));
    let timer;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => reject(Error('Absolute host deadline: ' + label)), Math.max(1, absoluteAt - performance.now()));
    });
    try {
      const result = await Promise.race(cleanup ? [underlying, timeout] : [underlying, timeout, this.fatal]);
      if (performance.now() > absoluteAt) throw Error('Absolute deadline at completion of ' + label);
      return result;
    } finally { clearTimeout(timer); }
  }
  work(label, operation) { return this.within(label, operation); }
  cleanup(label, operation, options = {}) { return this.within(label, operation, {...options, cleanup: true}); }
  snapshot() {
    return {startedHostMonotonicMs: this.started, workDeadlineMs: this.workAt,
      hardDeadlineMs: this.hardAt, nowHostMonotonicMs: performance.now(),
      closing: this.closing, underlyingCommandsStillPending: [...this.pending.values()],
      failures: [...this.failures]};
  }
  dispose() {
    if (!this.pending.size) clearTimeout(this.hardTimer);
    else this.hardTimer.unref?.();
  }
}
