import {createHash} from 'node:crypto';

// This is an exact identity-HTTP-body ledger, not a browser/GPU RAM limiter.
// Reservations precede Response.body, equal the frozen decoded length, and
// survive a timed-out host await until the underlying body Promise settles.
export class DecodedBodyBudget {
  constructor(maxTotalBytes = 32 * 1024 * 1024) {
    this.maximum = maxTotalBytes;
    this.reserved = 0; this.actualDecoded = 0; this.next = 0;
    this.tickets = new Map(); this.failures = [];
  }
  reserve(bytes, label) {
    if (!Number.isSafeInteger(bytes) || bytes <= 0 || this.actualDecoded + this.reserved + bytes > this.maximum)
      throw Error('Frozen decoded-byte budget exceeded before body read: ' + label);
    const ticket = {id: ++this.next, bytes, label, settled: false, error: null};
    this.tickets.set(ticket.id, ticket); this.reserved += bytes;
    return ticket;
  }
  complete(ticket, actualBytes) {
    if (ticket.settled) return;
    ticket.settled = true; this.reserved -= ticket.bytes;
    if (!Number.isSafeInteger(actualBytes) || actualBytes < 0) {
      ticket.error = 'Unavailable actual decoded-byte count';
      this.failures.push(ticket.error); return;
    }
    this.actualDecoded += actualBytes;
    if (actualBytes !== ticket.bytes || this.actualDecoded > this.maximum) {
      ticket.error = 'Identity response violated its frozen length/decoded budget: ' + ticket.label;
      this.failures.push(ticket.error);
    }
  }
  reject(ticket) {
    if (!ticket.settled) { ticket.settled = true; this.reserved -= ticket.bytes; }
  }
  snapshot() {
    return {maximumDecodedBytes: this.maximum, actualDecodedBytes: this.actualDecoded,
      reservedForUnsettledBodies: this.reserved,
      unsettledBodies: [...this.tickets.values()].filter(row => !row.settled).map(row => ({label: row.label, bytes: row.bytes})),
      failures: [...this.failures]};
  }
}

export async function readFrozenIdentityBody(response, {expected, deadline, budget, label, maxBodyBytes}) {
  // Unknown resources never reach body(). The frozen size, identity encoding,
  // one Content-Length and absence of transfer framing are mandatory before
  // Playwright is asked to return a complete buffer. This deliberately refuses
  // gzip/br/chunked/SW/unknown-length delivery instead of decoding it first.
  if (!expected || !Number.isSafeInteger(expected.bytes) || expected.bytes <= 0 || expected.bytes > maxBodyBytes ||
      !/^[a-f0-9]{64}$/.test(expected.sha256 || '')) throw Error('No bounded frozen body identity: ' + label);
  const headers = await deadline.work(label + ':headers', () => response.allHeaders());
  const length = headers['content-length'], encoding = headers['content-encoding'];
  if (response.status() !== 200 || response.request().method() !== 'GET' ||
      response.url() !== expected.url || typeof response.fromServiceWorker !== 'function' || response.fromServiceWorker())
    throw Error('Unexpected response status/URL/method/SW provenance: ' + label);
  if ((encoding !== undefined && encoding.trim().toLowerCase() !== 'identity') ||
      headers['transfer-encoding'] !== undefined || headers['content-range'] !== undefined ||
      !/^[1-9]\d*$/.test(length || '') || Number(length) !== expected.bytes)
    throw Error('Response is not exact frozen identity Content-Length delivery: ' + label);
  const ticket = budget.reserve(expected.bytes, label);
  let started = false;
  try {
    const body = await deadline.work(label + ':body', () => {
      const originalBodyPromise = response.body();
      started = true;
      // The side settlement handlers never throw. If a deadline abandons the
      // await, keep its exact-size reservation until the body actually settles
      // or Page close cancels it; do not reuse that reservation for new reads.
      originalBodyPromise.then(value => {
        try { budget.complete(ticket, value.byteLength); }
        catch { ticket.error = 'Decoded budget accounting failure'; }
      }, () => { try { budget.reject(ticket); } catch {} });
      return originalBodyPromise;
    });
    if (!ticket.settled || ticket.error || body.byteLength !== expected.bytes) throw Error(ticket.error || 'Missing exact decoded settlement');
    const sha256 = await deadline.work(label + ':hash', () => createHash('sha256').update(body).digest('hex'));
    if (sha256 !== expected.sha256) throw Error('Actual response SHA differs from frozen identity: ' + label);
    return {body, bytes: body.byteLength, sha256, headers: {
      contentLength: length, contentEncoding: encoding ?? null, transferEncoding: null},
      hashStage: 'actual_existing_exact_identity_response_body_no_second_request'};
  } finally {
    if (!started) budget.reject(ticket);
  }
}
