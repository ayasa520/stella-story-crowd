import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile, mkdir, readdir, lstat, realpath, stat } from 'node:fs/promises';
import { getPriority } from 'node:os';
import { dirname, resolve, relative, sep, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const ROOT = '/home/rikka/Projects/stella';
const A = resolve(ROOT, 'artifacts/stella-script-continuation-20261121');
const DATA = resolve(A, 'data-checkout');
const SOURCE = resolve(ROOT, 'artifacts/stella-site-repair-source/.sites-checkout');
const P30_KIT = resolve(A, 'p30-node4-ordinary-entry-owner-kit-rootfalse-v2');
const SELF = fileURLToPath(import.meta.url);
const need = (ok, message) => { if (!ok) throw Error(message); };
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const sorted = values => [...values].sort();
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const within = (path, base) => path.startsWith(base + sep);
// Only the already reviewed formal publication families may differ from Qv3.
// The three bare-BGM repairs add six native/review paths; the pending P29
// identity remains in its existing pair. This allowlist grants no acceptance
// to a particular delta: root must still review the exact committed changes.
const controlled = new Set(['native/scenes/10090015.json',
  'native/scenes/10040052.json', 'review/scenes/10040052.json',
  'native/scenes/10030006.json', 'review/scenes/10030006.json',
  'native/scenes/10020001.json', 'review/scenes/10020001.json',
  'native/scenes/10020011.json', 'review/scenes/10020011.json',
  'native/scenes/10020048.json', 'review/scenes/10020048.json',
  'manifest.json', 'review/native-restoration.json']);
const auditAddition = name => name.startsWith('review/restoration-audits/') ||
  /^review\/restoration-batches\/[^/]+\.json$/.test(name);
let output, outputCreated = false, jsonFailureNumber = 0;
const boundInputs = new Map();

/** Retain the actual bytes and original decoded text if a metadata parser
 * fails. A later read is never relabelled as that lost parser input, and this
 * collector has no retry, business-module import or parser-replacement path.
 */
async function parseBytes(path, bytes, expectedSHA256) {
  const text = bytes.toString('utf8');
  try {
    need(!expectedSHA256 || hash(bytes) === expectedSHA256, `Actual metadata bytes differ from captured SHA: ${path}`);
    return JSON.parse(text);
  }
  catch (error) {
    if (outputCreated) {
      const stem = `json-read-failure-${++jsonFailureNumber}`;
      await writeFile(resolve(output, stem + '.raw.gz'), gzipSync(bytes), { flag: 'wx' });
      await writeFile(resolve(output, stem + '.decoded.utf8.gz'), gzipSync(Buffer.from(text)), { flag: 'wx' });
      await writeFile(resolve(output, stem + '.json'), JSON.stringify({ path, bytes: bytes.length,
        sha256: hash(bytes), expectedSHA256: expectedSHA256 || null, decodedLength: text.length, error: String(error.stack || error),
        cause: 'unknown', noRetry: true }, null, 2) + '\n', { flag: 'wx' });
    }
    throw error;
  }
}
async function boundJSON(binding) {
  need(binding && isAbsolute(binding.path) && /^[a-f0-9]{64}$/.test(binding.sha256 || ''), 'Missing JSON byte binding');
  const bytes = await readFile(binding.path);
  const value = await parseBytes(binding.path, bytes, binding.sha256);
  need(!boundInputs.has(binding.path) || boundInputs.get(binding.path) === binding.sha256, 'Conflicting metadata reference');
  boundInputs.set(binding.path, binding.sha256);
  return value;
}
async function walk(base) {
  const result = [];
  for (const entry of await readdir(base, { withFileTypes: true })) {
    const path = resolve(base, entry.name);
    if (entry.isDirectory()) result.push(...await walk(path));
    else { need(entry.isFile(), `Nonregular inventory member requires explicit review: ${path}`); result.push(path); }
  }
  return result.sort();
}
async function maybeWalk(base) {
  try { return await walk(base); } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

/** Only this pinned Git executable is launched. Its environment cannot inherit
 * alternate repositories, object directories, pagers or fsmonitor commands.
 * No Git write, network, build, freezer, Worker or browser is invoked.
 */
function git(cwd, ...args) {
  return execFileSync('/usr/bin/git', ['--no-pager', '--no-optional-locks', '-c', 'core.fsmonitor=false',
    '-c', 'core.untrackedCache=false', '-C', cwd, ...args], { maxBuffer: 128 * 1024 * 1024,
    env: { PATH: '/usr/bin:/bin', LANG: 'C.UTF-8', LC_ALL: 'C.UTF-8', GIT_OPTIONAL_LOCKS: '0',
      GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null' } });
}
const gitText = (cwd, ...args) => git(cwd, ...args).toString('utf8').trim();
function tree(cwd, revision) {
  const result = new Map();
  for (const row of git(cwd, 'ls-tree', '-rz', revision).toString('utf8').split('\0').filter(Boolean)) {
    const tab = row.indexOf('\t'), [mode, kind, oid] = row.slice(0, tab).split(' ');
    need(tab > 0 && kind === 'blob', 'Unexpected HEAD tree record');
    result.set(row.slice(tab + 1), { mode, oid });
  }
  return result;
}
function committedChanges(base, revision) {
  const fields = git(DATA, 'diff', '--name-status', '-z', '--no-renames', base, revision, '--').toString('utf8').split('\0').filter(Boolean);
  need(fields.length % 2 === 0, 'Unexpected commit delta format');
  const result = [];
  for (let i = 0; i < fields.length; i += 2) {
    const status = fields[i], path = fields[i + 1];
    need((status === 'M' && controlled.has(path)) || (status === 'A' && auditAddition(path)),
      `Unapproved committed change since Qv3: ${status} ${path}`);
    result.push({ status, path });
  }
  return result;
}

async function main() {
  const args = process.argv.slice(2), options = {};
  need(args.length === 6, 'Use --request PATH --request-sha256 SHA --script-sha256 SHA');
  for (let i = 0; i < args.length; i += 2) {
    need(['--request', '--request-sha256', '--script-sha256'].includes(args[i]) && !options[args[i]], 'Unknown/duplicate argument');
    options[args[i]] = args[i + 1];
  }
  need(hash(await readFile(SELF)) === options['--script-sha256'], 'Collector source guard failed');
  boundInputs.set(SELF, options['--script-sha256']);
  need(process.execArgv.length === 0 && !process.env.NODE_OPTIONS && !process.env.NODE_PATH, 'No Node preload/module-selection overrides');
  need(getPriority() >= 19 && /^Cpus_allowed_list:\s*(?:0-1|0,1)\s*$/m.test(await readFile('/proc/self/status', 'utf8')), 'Use nice19/CPU0,1');
  const request = await boundJSON({ path: resolve(options['--request']), sha256: options['--request-sha256'] });
  need(request.rootConfirmed === true && request.inventoryCollectionAuthorized === true, 'No root authorization for metadata collection');
  need(request.browserLaunchAuthorized === false && /^[a-f0-9]{40}$/.test(request.finalDataHead || '') &&
    /^[a-f0-9]{40}$/.test(request.expectedSourceHead || ''), 'Final exact heads are required; browser stays false');
  output = resolve(request.outDirectory || '');
  need(dirname(output) === A && output.split(sep).at(-1).startsWith('ordinary-QA-root-bindings-'), 'Use a fresh direct A-owned output directory');
  await mkdir(output); // Existing output is a failure; never overwrite/retry.
  outputCreated = true;
  const seed = await boundJSON(request.seedInventory), selection = await boundJSON(request.toolSelection);
  need(equal(Object.keys(request.kits || {}), ['p30']) && request.kits.p30.directory === P30_KIT &&
    request.p30Template.path === resolve(P30_KIT, 'root-inputs.draft.json') &&
    request.p30Plan.path === resolve(P30_KIT, 'plan.rootfalse.json'), 'This adapter only binds the sealed P30 v2 kit');
  const p30 = await boundJSON(request.p30Template);
  need(seed.dataRoot === DATA && seed.sourceRoot === SOURCE && seed.observedSourceHead === request.expectedSourceHead,
    'The approved Qv3 source epoch cannot drift');
  need(Object.keys(seed.sourceFiles).length === 312 && Object.keys(seed.distFiles).length === 234 &&
    Object.keys(seed.protectedFirstThree).length === 22, 'Unexpected Qv3 baseline membership');
  need(hash(await readFile('/usr/bin/git')) === seed.toolFiles['/usr/bin/git'] &&
    hash(await readFile('/proc/self/exe')) === seed.toolFiles['/usr/bin/node'], 'Actual Git/Node bytes differ from Qv3');
  need(gitText(DATA, 'rev-parse', 'HEAD') === request.finalDataHead && gitText(DATA, 'status', '--short') === '', 'Final data HEAD must be committed and clean');
  const sourceStatus = gitText(SOURCE, 'status', '--short');
  need(gitText(SOURCE, 'rev-parse', 'HEAD') === request.expectedSourceHead && sourceStatus === seed.sourceStatus &&
    gitText(SOURCE, 'diff', '--name-only', 'HEAD') === '', 'Source/status differs from Qv3');
  need(gitText(DATA, 'rev-parse', '--show-object-format') === 'sha1' &&
    gitText(SOURCE, 'rev-parse', '--show-object-format') === 'sha1', 'Unreviewed Git object format');
  const dataTree = tree(DATA, request.finalDataHead), sourceTree = tree(SOURCE, request.expectedSourceHead);
  const delta = committedChanges(seed.observedDataHead, request.finalDataHead);
  const cache = new Map(), old = new Map();
  const declareOld = (path, sha256) => {
    path = resolve(path); need(!old.has(path) || old.get(path) === sha256, `Conflicting old path provenance: ${path}`); old.set(path, sha256);
  };
  for (const [name, value] of Object.entries(seed.dataInputs)) declareOld(resolve(DATA, name), value);
  for (const group of ['globalGuards', 'sharedClosure', 'evidenceGuards', 'toolFiles'])
    for (const [path, value] of Object.entries(seed[group])) declareOld(path, value);
  for (const [name, value] of Object.entries(seed.sourceFiles)) declareOld(resolve(SOURCE, name), value);
  for (const [name, value] of Object.entries(seed.distFiles)) declareOld(resolve(SOURCE, 'dist', name), value);
  need(old.size === 5536, 'Retain the complete approved Qv3 old-path baseline');
  const changedOldPaths = [];
  async function capture(path) {
    path = resolve(path);
    if (cache.has(path)) return cache.get(path);
    const before = await stat(path), bytes = await readFile(path), after = await stat(path), sha256 = hash(bytes);
    need(before.ino === after.ino && before.size === after.size && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs,
      `Input changed during read: ${path}`);
    // Git hashes are hashes of the actual object header and working bytes.
    // Matching ls-tree's blob OID proves HEAD equality without thousands of
    // cat-file subprocesses or collecting an enormous in-memory blob stream.
    const base = within(path, DATA) ? DATA : within(path, SOURCE) && !within(path, resolve(SOURCE, 'dist')) ? SOURCE : null;
    if (base) {
      const member = (base === DATA ? dataTree : sourceTree).get(relative(base, path));
      need(member && ['100644', '100755'].includes(member.mode), `Input is not an approved regular HEAD blob: ${path}`);
      const oid = createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
      need(oid === member.oid, `Working bytes differ from final HEAD blob: ${path}`);
    }
    if (old.has(path) && old.get(path) !== sha256) {
      need(within(path, DATA) && controlled.has(relative(DATA, path)), `Old approved input drifted: ${path}`);
      changedOldPaths.push({ path, oldSHA256: old.get(path), sha256, verifiedFinalHEADBlob: true });
    }
    const record = { sha256, bytes: bytes.length }; cache.set(path, record); return record;
  }
  const json = async path => {
    const captured = await capture(path), bytes = await readFile(path);
    return parseBytes(path, bytes, captured.sha256);
  };
  // Retain every old path before expanding membership. New observations never
  // replace a missing historical member or silently excuse source/resource drift.
  for (const path of old.keys()) await capture(path);
  const sourceNames = git(SOURCE, 'ls-files', '-z').toString('utf8').split('\0').filter(Boolean);
  const distPaths = await walk(resolve(SOURCE, 'dist'));
  need(equal(sorted(sourceNames), sorted(Object.keys(seed.sourceFiles))) &&
    equal(distPaths.map(path => relative(resolve(SOURCE, 'dist'), path)), sorted(Object.keys(seed.distFiles))), 'Source/dist membership drift');
  const sourceFiles = {}, distFiles = {};
  for (const name of sourceNames) sourceFiles[name] = (await capture(resolve(SOURCE, name))).sha256;
  for (const path of distPaths) distFiles[relative(resolve(SOURCE, 'dist'), path)] = (await capture(path)).sha256;
  const manifest = await json(resolve(DATA, 'manifest.json'));
  need(manifest.scenes.length === 140 && new Set(manifest.scenes.map(row => row.id)).size === 140, 'Expected the existing 140-scene catalog');
  const documents = new Map();
  for (const entry of manifest.scenes) documents.set(entry.id, await json(resolve(DATA, entry.path)));
  const counts = { libraryScenes: manifest.scenes.length,
    libraryNodes: [...documents.values()].reduce((n, doc) => n + doc.scenario_list.length, 0),
    libraryEdges: [...documents.values()].reduce((n, doc) => n + doc.scenario_list.reduce((m, row) => m + row.branch_list.length, 0), 0) };
  const protectedIds = manifest.chapters.find(row => row.id === 1).sections.slice(0, 3).flatMap(row => row.sceneIds);
  const protectedNames = protectedIds.flatMap(id => { const entry = manifest.scenes.find(row => row.id === id); return [entry.path, entry.reviewPath]; });
  need(equal(sorted(protectedNames), sorted(Object.keys(seed.protectedFirstThree))), 'Protected22 membership differs');
  const protectedFirstThree = {};
  for (const name of protectedNames) { const sha256 = (await capture(resolve(DATA, name))).sha256;
    need(sha256 === seed.protectedFirstThree[name], `Protected original baseline changed: ${name}`); protectedFirstThree[name] = sha256; }

  /** Retain the previously successful metadata resource union without removal.
   * The section1003 resources remain historical closure, while this adapter
   * only prepares P30 v2. No P22 template, freezer, API or browser is invoked.
   */
  const catalog = await json(resolve(DATA, 'assets/catalog.json'));
  const dataNames = new Set([...Object.keys(seed.dataInputs), 'manifest.json', 'review/native-restoration.json',
    'assets/catalog.json', 'assets/package.json', 'assets/preview/catalog.json']);
  for (const entry of manifest.scenes) { dataNames.add(entry.path); dataNames.add(entry.reviewPath); }
  const addTree = async name => { for (const path of await maybeWalk(resolve(DATA, name))) dataNames.add(relative(DATA, path)); };
  const models = new Set(['subaru01']), movies = new Set(['adv_dive01_out']);
  for (const entry of manifest.scenes.filter(row => [1003, 1045].includes(row.sectionId))) {
    dataNames.add('assets/' + catalog.thumbnails.scene[String(entry.id)]);
    for (const row of documents.get(entry.id).scenario_list) {
      if (row.character) {
        need(/^live2d\/AC_[A-Za-z0-9_]+$/.test(row.character), 'Actor metadata needs the same separately reviewed freezer mapping');
        models.add(row.character.slice('live2d/AC_'.length));
      }
      if (entry.sectionId === 1003 && row.video) movies.add(row.video);
    }
  }
  for (const name of ['player', 'backgrounds', 'music', 'voices', 'sounds', 'cutins', 'pictures', 'thumbnails'])
    for (const prefix of ['assets/', 'assets/preview/']) await addTree(prefix + name);
  for (const model of models) for (const prefix of ['assets/', 'assets/preview/']) {
    await addTree(prefix + 'models/' + model);
    for (const path of await maybeWalk(resolve(DATA, prefix + 'portraits')))
      if (path.split(sep).at(-1).startsWith(model + '.')) dataNames.add(relative(DATA, path));
  }
  for (const prefix of ['assets/', 'assets/preview/'])
    for (const path of await maybeWalk(resolve(DATA, prefix + 'movies')))
      if ([...movies].some(movie => path.split(sep).at(-1).startsWith(movie + '.'))) dataNames.add(relative(DATA, path));
  const nativeReview = [...await walk(resolve(DATA, 'native')), ...await walk(resolve(DATA, 'review'))];
  for (const path of nativeReview) if (within(path, resolve(DATA, 'review/restoration-batches'))) dataNames.add(relative(DATA, path));
  const globalGuards = Object.fromEntries([...old.keys()].map(path => [path, cache.get(path).sha256])), dataInputs = {};
  for (const path of nativeReview) globalGuards[path] = (await capture(path)).sha256;
  for (const name of sorted(dataNames)) { const path = resolve(DATA, name), sha256 = (await capture(path)).sha256;
    dataInputs[name] = sha256; globalGuards[path] = sha256; }
  for (const path of Object.keys(globalGuards)) globalGuards[path] = (await capture(path)).sha256;

  const tools = {}, toolFiles = { ...seed.toolFiles };
  need(equal(sorted(Object.keys(selection.tools)), ['ffmpeg', 'firefox', 'node', 'python', 'xvfb']), 'Exactly five tool selections required');
  for (const [name, item] of Object.entries(selection.tools)) {
    const binary = await readFile(item.binaryPath), launch = await readFile(item.launchPath);
    need(hash(binary) === item.sha256 && hash(launch) === item.launchSha256 && binary.subarray(0, 4).equals(Buffer.from([127, 69, 76, 70])) &&
      binary[4] === 2 && binary[5] === 1 && binary.readUInt16LE(18) === 183, `Actual ARM tool/launcher differs: ${name}`);
    if (name === 'firefox') need(launch.toString() === '#!/bin/sh\nexec /usr/lib/firefox/firefox "$@"\n', 'Firefox wrapper selection changed');
    else need(await realpath(item.launchPath) === await realpath(item.binaryPath), `Launcher targets another executable: ${name}`);
    tools[name] = { ...item, elfMachine: 183, arm64ByteEvidence: true };
    for (const [path, sha256] of [[item.binaryPath, item.sha256], [item.launchPath, item.launchSha256]]) {
      need((await capture(path)).sha256 === sha256, `Tool changed during binding: ${path}`);
      toolFiles[path] = sha256; globalGuards[path] = sha256;
    }
  }
  const evidenceGuards = { ...seed.evidenceGuards }, sharedClosure = { ...seed.sharedClosure };
  const p30Plan = await boundJSON(request.p30Plan);
  const evidenceToBind = {};
  for (const group of [request.publicationGuards, request.additionalEvidence, p30Plan.evidenceReferences]) for (const [path, sha256] of Object.entries(group)) {
    need(!Object.hasOwn(evidenceToBind, path) || evidenceToBind[path] === sha256, `Conflicting evidence references: ${path}`);
    evidenceToBind[path] = sha256;
  }
  for (const [path, sha256] of Object.entries(evidenceToBind)) {
    need((await capture(path)).sha256 === sha256, `Fresh evidence differs: ${path}`); evidenceGuards[path] = sha256; globalGuards[path] = sha256;
  }
  need(Object.keys(request.publicationGuards).length > 0, 'Bind final publication/ACK/source status receipts');
  const kitMaps = {};
  for (const name of ['p30']) {
    const item = request.kits[name], receipt = await boundJSON(item.receipt), map = {};
    for (const [file, expected] of Object.entries(receipt.payloads)) {
      const path = resolve(item.directory, file); need((await capture(path)).sha256 === expected.sha256, `Sealed kit payload differs: ${path}`); map[path] = expected.sha256;
    }
    map[item.receipt.path] = item.receipt.sha256;
    for (const [path, sha256] of Object.entries(sharedClosure)) map[path] = sha256;
    kitMaps[name] = map;
  }
  const tap = resolve(A, 'episode5-actor-private-read-tap-v2-20261121-v1/proposed-read-tap.v2.mjs');
  need((await capture(tap)).sha256 === 'cc191d0433def9fbcbb5b9b4e556ff7e92e6c46f366ab9151d4aef860fdbc8c1', 'Original read tap changed');
  kitMaps.p30[tap] = (await capture(tap)).sha256;
  for (const [path, sha256] of boundInputs) globalGuards[path] = sha256;
  const inventory = { ...seed, schema: 'stella.ordinary-qa.p30-v2-fresh-guard-inventory-candidate.v1',
    rootConfirmed: false, isExecutionBinding: false, preparationAuthorized: false, executionAuthorized: false, browserLaunchAuthorized: false,
    observedAt: new Date().toISOString(), observedDataHead: request.finalDataHead, observedSourceHead: request.expectedSourceHead,
    publishedHead: request.finalDataHead, dataStatus: '', sourceStatus, atomicFreeze: false, collectionWindowStable: true,
    controlledDifferenceAcceptance: 'PENDING_ROOT_REVIEW_OF_THIS_FRESH_METADATA', dataInputs, globalGuards, sourceFiles, distFiles,
    protectedFirstThree, sharedClosure, evidenceGuards, toolFiles, routeSource: request.p30Plan,
    inheritedRouteSource: seed.routeSource, resourceDerivation: { models: sorted(models), sections: [1003, 1045],
      basis: 'Retained successful historical resource union plus current P30 metadata, preserving Qv3 inputs; no P22 execution, API or before-state synthesis' },
    counts: { ...counts, dataInputs: Object.keys(dataInputs).length, globalGuards: Object.keys(globalGuards).length,
      globalNativeReview: nativeReview.length, sourceFiles: sourceNames.length, distFiles: distPaths.length,
      protectedFirstThree: Object.keys(protectedFirstThree).length, sharedClosure: Object.keys(sharedClosure).length,
      evidenceGuards: Object.keys(evidenceGuards).length, toolFiles: Object.keys(toolFiles).length },
    inheritedMembershipDerivation: seed.membershipDerivation,
    membershipDerivation: { collector: { path: SELF, sha256: options['--script-sha256'] },
      p30Freezer: { path: resolve(request.kits.p30.directory, 'freeze.py'), sha256: kitMaps.p30[resolve(request.kits.p30.directory, 'freeze.py')] } },
    metadataDifferenceClassification: { knownControlledScopeOnly: true, unexpectedDifferenceCount: 0,
      rootIndependentReviewStillRequired: true, changedOldPathCount: changedOldPaths.length,
      committedAddedAuditOrBatchCount: delta.filter(row => row.status === 'A').length },
    provenance: { seedInventory: request.seedInventory, oldPathsRetained: old.size, changedOldPaths, committedChanges: delta,
      everyDataInputVerifiedAgainstFinalHEADBlob: true, noRemoteACKClaimFromGitReads: true },
    limits: ['False metadata candidate only; root approves separate external freezer inputs.', 'Actual API-before dependencies remain fail-closed.'] };
  const inventoryPath = resolve(output, 'inventory.rootfalse.json');
  const inventoryBytes = Buffer.from(JSON.stringify(inventory, null, 2) + '\n'), inventoryRef = { path: inventoryPath, sha256: hash(inventoryBytes) };
  Object.assign(p30, { finalDataHead: request.finalDataHead, finalSourceHead: request.expectedSourceHead, browserOwner: request.browserOwner,
    globalGuardsFile: inventoryRef, publicationGuards: request.publicationGuards, protectedFirstThree, kitGuards: kitMaps.p30, tools });
  // No approval bit is promoted by collecting hashes. Root must inspect the
  // candidate and separately authorize the original P30 freezer/API step.
  need(p30.rootConfirmed === false && p30.freezeAuthorized === false && p30.apiPreparationAuthorized === false &&
    p30.fullGlobalInventoryApproved === false && p30.browserLaunchAuthorized === false,
    'Supply the original false templates');
  for (const [path, record] of cache) need(hash(await readFile(path)) === record.sha256, `Final byte drift: ${path}`);
  for (const [path, sha256] of boundInputs) need(hash(await readFile(path)) === sha256, `Final metadata drift: ${path}`);
  need(equal(await walk(resolve(SOURCE, 'dist')), distPaths) &&
    equal([...await walk(resolve(DATA, 'native')), ...await walk(resolve(DATA, 'review'))], nativeReview), 'Final inventory membership drift');
  need(gitText(DATA, 'rev-parse', 'HEAD') === request.finalDataHead && gitText(DATA, 'status', '--short') === '' &&
    gitText(SOURCE, 'rev-parse', 'HEAD') === request.expectedSourceHead && gitText(SOURCE, 'status', '--short') === sourceStatus, 'Final HEAD/status drift');
  await writeFile(inventoryPath, inventoryBytes, { flag: 'wx' });
  for (const [name, value] of [['p30-inputs.filled.rootfalse.json', p30], ['tools.fresh.json', tools]])
    await writeFile(resolve(output, name), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  await writeFile(resolve(output, 'collection-receipt.rootfalse.json'), JSON.stringify({ rootConfirmed: false, executionAuthorized: false,
    finalDataHead: request.finalDataHead, sourceHead: request.expectedSourceHead, inventory: inventoryRef, counts,
    sourceFiles: sourceNames.length, distFiles: distPaths.length, protected22: 22, requestSHA256: options['--request-sha256'],
    collectorSHA256: options['--script-sha256'], metadataOnlyNoFreezeAPIOrBrowser: true, noD_C_orGitWrites: true }, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ status: 'metadata-only-rootfalse', output, inventory: inventoryRef, counts }) + '\n');
}
main().catch(async error => {
  if (outputCreated) try { await writeFile(resolve(output, 'collection-failure.json'), JSON.stringify({ error: String(error.stack || error),
    originalFailureRetained: true, noRetry: true }, null, 2) + '\n', { flag: 'wx' }); } catch {}
  process.stderr.write(String(error.stack || error) + '\n'); process.exitCode = 1;
});
