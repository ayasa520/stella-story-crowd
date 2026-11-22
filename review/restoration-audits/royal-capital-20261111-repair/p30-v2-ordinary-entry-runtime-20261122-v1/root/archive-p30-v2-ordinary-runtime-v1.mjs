// Archive closed evidence only. The byte-preservation and gzip readback
// mechanism follows the successfully executed P22 ordinary-QA archiver.
// A plan digest, the independently closed runtime, the exact data HEAD and
// a clean checkout are all checked before any new directory is created.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gzipSync,gunzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const A=path.dirname(fileURLToPath(import.meta.url));
const workspace=path.resolve(A,'../..'),D=path.join(A,'data-checkout');
const targetRelative='review/restoration-audits/royal-capital-20261111-repair/p30-v2-ordinary-entry-runtime-20261122-v1';
const base='edd4afedf2dd2720da1c0f873ed1ad6caeac2e50';
const read=p=>fs.readFileSync(p),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ref=p=>{const b=read(p);return {path:p,bytes:b.length,sha256:sha(b)};};
const git=(...args)=>execFileSync('git',['-C',D,...args],{encoding:'utf8',maxBuffer:8*1024*1024}).trim();
const [planPath,expectedPlanSha]=process.argv.slice(2);
assert.ok(planPath&&/^[a-f0-9]{64}$/.test(expectedPlanSha||''));
const planBytes=read(planPath);assert.equal(sha(planBytes),expectedPlanSha);
const plan=JSON.parse(planBytes);
assert.equal(plan.targetRelativeDirectory,targetRelative);
assert.equal(plan.targetCheckout,D);
assert.equal(git('rev-parse','HEAD'),base);assert.equal(git('status','--short'),'');
const closurePath=path.join(A,'ordinary-QA-root-preparation-edd4afed-p30v2-v1/p30-runtime.root-closure.json');
assert.equal(ref(closurePath).sha256,'c6db91bd357c2935a2452ee5864ce736af388ff103e77c181230ebdf5b8dbc86');
const closure=JSON.parse(read(closurePath));
assert.equal(closure.runtimeSession,87926);assert.equal(closure.runtimeExitCode,0);
assert.equal(closure.allOwnedPidAndGroupsAbsent,true);assert.equal(closure.freshGuardCount,14099);
assert.equal(closure.sourceMotionPhaseTimingMatchOrWholeSceneAccepted,false);
const destination=path.join(D,targetRelative);assert.equal(fs.existsSync(destination),false);
const space=fs.statfsSync(D);assert.ok(space.bavail*space.bsize>80*1024*1024);
assert.ok(Array.isArray(plan.archiveEntries)&&plan.archiveEntries.length>0);

// Resolve only named local evidence under this continuation directory. No
// SQLite content is needed for this public runtime audit; it stays local.
const originalPath=name=>{
  const absolute=path.resolve(path.isAbsolute(name)?name:path.join(workspace,name));
  assert.ok(absolute.startsWith(A+path.sep));
  assert.ok(!/\.sqlite(?:-|$)/.test(absolute));
  return absolute;
};
const originals=new Map(),targets=new Set();
for(const entry of plan.archiveEntries){
  assert.ok(!path.isAbsolute(entry.archivePath)&&!entry.archivePath.split('/').includes('..'));
  assert.ok(!targets.has(entry.archivePath));targets.add(entry.archivePath);
  assert.ok(['copy-original-verbatim','new-gzip-of-exact-original-bytes'].includes(entry.encoding));
  assert.ok(entry.originalSources.length>0);
  for(const original of entry.originalSources){
    const p=originalPath(original.path),bytes=read(p);
    assert.equal(bytes.length,original.bytes,p);assert.equal(sha(bytes),original.sha256,p);
    assert.equal(bytes.length,entry.originalBytes);assert.equal(sha(bytes),entry.originalSHA256);
    const value={bytes:bytes.length,sha256:sha(bytes)};
    if(originals.has(p))assert.deepEqual(originals.get(p),value);
    originals.set(p,value);
  }
}

// Compression is transport only: never parse, normalize, or reserialize an
// original JSON/log before archiving it. Identical originals may share one
// payload, but every original path and digest remains in the manifest.
fs.mkdirSync(destination);
const archived=[];
for(const entry of plan.archiveEntries){
  const original=read(originalPath(entry.originalSources[0].path));
  const compressed=entry.encoding==='new-gzip-of-exact-original-bytes';
  if(compressed)assert.ok(/\.(?:jsonl?|txt|log|mjs|md)$/.test(entry.originalSources[0].path));
  const output=compressed?gzipSync(original,{level:6}):original;
  const p=path.join(destination,entry.archivePath);fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p,output,{flag:'wx'});const actual=read(p);
  assert.deepEqual(compressed?gunzipSync(actual):actual,original,p);
  archived.push({...entry,archivedBytes:actual.length,archivedSHA256:sha(actual)});
}
fs.writeFileSync(path.join(destination,'archive-plan.rootfalse.json'),planBytes,{flag:'wx'});
const readme=`# P30 node4: closed ordinary entry observation\n\nPublished data EDD4 and canonical player 6630 completed the unchanged ordinary route 3→4→5 natural ready in session87926, exit0. The fresh runtime used the reviewed transport and its entire program SHA and genuine before matched the retained ordinary response before recording ACK and load. Original edges31/41 were used;51/6 were not. The original surface capture has453 samples,1439679 bytes; no screenshots or audio were recorded. All14099 released inputs were independently rehashed after owned browser/media/process groups, ports, display and private state closed.\n\nThis accepts bounded execution and evidence closure only. Container decode, complete source/actual image comparison, acting, timing, motion/provider/phase and whole-scene/episode acceptance remain pending. Three Normal hitches, original diagnostics and observer timing costs remain intact.\n\nThe earlier successful preparation omitted the reviewed transport preload. Its original outputs and missing provider trace are retained. Independent full140-scene/5624-node/5870-edge comparisons supported limited reuse as an immutable program/before reference; the actually loaded fresh local response had to match in full. Runtime provider evidence does not retroactively fill the earlier missing trace.\n\nEvery original is mapped to an exact transport below. Large text transports decompress byte-for-byte; existing gzip/video remain verbatim. Byte-identical streams share a payload with all source mappings retained. The28 already published kit blobs are referenced without copying. SQLite remains in the local original directory. Earlier v1 failure and future image/motion acceptance remain separate records.\n`;
fs.writeFileSync(path.join(destination,'README.md'),readme,{flag:'wx'});
for(const[p,expected]of originals){assert.equal(read(p).length,expected.bytes);assert.equal(sha(read(p)),expected.sha256,p);}
const payloadBytes=archived.reduce((n,e)=>n+e.archivedBytes,0);
const manifest={schema:'stella.p30.v2.ordinary-runtime.audit-archive.v1',rootConfirmed:true,
  createdAt:new Date().toISOString(),dataHeadAtExecution:base,sourceHead:'6630ac70f17332efa031d021af00532d42307568',
  sourcePlan:ref(planPath),rootClosure:ref(closurePath),originalSourceMembers:originals.size,
  payloadFiles:archived.length,payloadBytes,allOriginalsFreshUnchanged:true,allArchivesReadBackByteExact:true,
  sourceMotionPhaseTimingMatchOrWholeSceneAccepted:false,archiveEntries:archived};
fs.writeFileSync(path.join(destination,'archive-manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
const total=payloadBytes+planBytes.length+Buffer.byteLength(readme)+fs.statSync(path.join(destination,'archive-manifest.json')).size;
assert.ok(total<64*1024*1024);assert.equal(git('diff','--name-only'),'');
const files=git('ls-files','--others','--exclude-standard').split('\n');
assert.ok(files.every(p=>p.startsWith(targetRelative+'/')));assert.equal(files.length,archived.length+3);
const receipt={schema:'stella.p30.v2.ordinary-runtime.archive-execution.v1',createdAt:new Date().toISOString(),
  baseHead:base,targetDirectory:destination,files:files.length,originalSourceMembers:originals.size,
  payloadBytes,totalBytes:total,newGzipFiles:archived.filter(e=>e.encoding==='new-gzip-of-exact-original-bytes').length,
  allOriginalsFreshUnchanged:true,allArchivesReadBackByteExact:true,formalDataChanged:false,
  archiveManifest:ref(path.join(destination,'archive-manifest.json')),committed:false,pushed:false};
const receiptPath=path.join(A,'p30-v2-ordinary-runtime-archive-execution-v1.json');
fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({receipt:ref(receiptPath),files:files.length,totalBytes:total,allExact:true}));
