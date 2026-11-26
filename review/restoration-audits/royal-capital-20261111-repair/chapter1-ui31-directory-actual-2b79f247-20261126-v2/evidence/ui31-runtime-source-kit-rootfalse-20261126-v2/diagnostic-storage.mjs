// Storage for complete UI-sweep diagnostic packets only. This policy is
// deliberately separate from the original raw-size policy: a future reviewed
// plan must opt in explicitly, while the supervisor's 16 MiB output gate stays
// unchanged. No collector row, error, payload, or fallback attachment is edited.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {gzipSync} from 'node:zlib';
const sha = value => createHash('sha256').update(value).digest('hex');
export const diagnosticStoragePolicy = 'complete-json-gzip-v1';

export function prepareDiagnosticArchive(value, name, plan) {
  assert.equal(plan.diagnosticStorage?.policy, diagnosticStoragePolicy,
    'A separately reviewed diagnostic storage policy is required');
  assert.equal(plan.budgets.diagnosticBytes, 2097152, 'Stored diagnostic cap remains 2 MiB');
  assert.equal(plan.diagnosticStorage.decodedBytes, 16777216, 'Explicit decoded diagnostic cap is 16 MiB');
  assert.match(name, /^[a-z0-9.-]+\.json\.gz$/);
  // Serialize the entire original packet once, with its terminal newline.
  // Level 1 bounds compression work on the browser-owner event loop; compression
  // efficiency is never evidence acceptance. Even a complete crossing packet
  // is retained before reporting its failed bound in writeDiagnosticArchive.
  const raw = Buffer.from(JSON.stringify(value) + '\n', 'utf8');
  const compressed = gzipSync(raw, {level: 1});
  const index = {schema: 'stella.ui-sweep.complete-diagnostic-archive.v1', policy: diagnosticStoragePolicy,
    file: name, encoding: 'gzip', decodedEncoding: 'utf8-json-newline',
    rawBytes: raw.length, rawSha256: sha(raw), bytes: compressed.length, sha256: sha(compressed),
    completeJsonRetained: true, originalRowsDropped: 0};
  const indexRaw = JSON.stringify(index) + '\n';
  return {compressed, index, indexRaw, indexBytes: Buffer.byteLength(indexRaw),
    decodedLimit: plan.diagnosticStorage.decodedBytes, storedLimit: plan.budgets.diagnosticBytes};
}

export function assertDiagnosticArchiveBudget(archive) {
  // These are acceptance/input bounds, not permission to truncate a crossing
  // BiDi event. The original arrays and complete structured failure attachment
  // remain available to the existing first-error and independent fallback paths.
  assert.ok(archive.index.rawBytes <= archive.decodedLimit,
    'Complete decoded diagnostic budget exceeded; crossing rows retained');
  assert.ok(archive.indexBytes <= 4096, 'Diagnostic index exceeds 4 KiB');
  assert.ok(archive.index.bytes + archive.indexBytes <= archive.storedLimit,
    'Complete gzip and diagnostic index exceed 2 MiB; crossing rows retained');
}

export async function writeDiagnosticArchive(output, name, value, plan) {
  const archive = prepareDiagnosticArchive(value, name, plan);
  const indexFile = name + '.index.json';
  await writeFile(resolve(output, name), archive.compressed, {flag: 'wx'});
  await writeFile(resolve(output, indexFile), archive.indexRaw, {flag: 'wx'});
  const retained = {...archive.index, indexFile, indexBytes: archive.indexBytes,
    storedBytesIncludingIndex: archive.index.bytes + archive.indexBytes};
  try { assertDiagnosticArchiveBudget(archive); }
  catch (error) {
    // This marker exists only after BOTH exclusive writes succeeded. It lets
    // the owner cite the complete retained archive on a budget crossing while
    // keeping its independent full-object log fallback for actual write errors.
    error.retainedDiagnosticArchive = retained;
    throw error;
  }
  return retained;
}
