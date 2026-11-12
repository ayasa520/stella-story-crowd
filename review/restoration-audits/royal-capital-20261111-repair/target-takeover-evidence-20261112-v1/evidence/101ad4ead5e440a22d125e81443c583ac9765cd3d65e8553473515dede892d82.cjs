/** Independent ARM Node readback of the exact 45-character publication scope.
 *
 * Python import/audit receipts remain authoritative for their own operations.
 * This separate parser checks every native row against the takeover commit,
 * all ownership hashes and protected originals. It does not infer performances
 * from field counts or promote static identities into continuous-playback QA.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict');
const root = '/home/rikka/Projects/stella';
const r = __dirname;
const data = path.join(root, 'story_crowd_data');
const base = 'c33057d059da46e35fad96a7f31a9665c23b5fa0';
const studioSha = 'ebd974d90f89088fa3a504c1f419ae01c352a24e6bd80209c5ec651295d38522';
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const git = (...args) => execFileSync('git', ['--no-optional-locks', ...args], {cwd:data, maxBuffer:32*1024*1024});
const observed = [];
const parse = (raw, source) => {
  const entry = {source, bytes:raw.length, sha256:sha(raw)};
  observed.push(entry);
  try { const result=JSON.parse(raw.toString('utf8'));entry.status='passed';return result; }
  catch(error) {
    entry.status='failed';entry.error=String(error);
    // Capture the actual failed read, rather than assigning a cause from an
    // earlier successful hash or discarding a transient parser observation.
    const directory=path.join(r,'target-node-parser-failure-'+Date.now());fs.mkdirSync(directory);
    fs.writeFileSync(path.join(directory,'input.bin'),raw);
    fs.writeFileSync(path.join(directory,'observations.json'),JSON.stringify(observed,null,2)+'\n');
    throw error;
  }
};
const load = name => parse(fs.readFileSync(path.join(data,name)), name);
const previous = name => parse(git('show',base+':'+name), base+':'+name);
const packets = [3,4,5,6,7].map(n => `visual-high/accepted-p29-batch${n}-identities-20261112-v1.json`)
  .concat(['visual-high/accepted-p30-first15-identities-v1.json',
    'visual-high/accepted-p30-ord15to29-identities-target-20261112-v1.json',
    'visual-high/accepted-p30-ord30to44-identities-target-20261112-v1.json']);
assert.equal(process.arch,'arm64');
assert.equal(git('status','--porcelain').toString(),'');
const head=git('rev-parse','HEAD').toString().trim();
const targets=new Map();
for(const name of packets) {
  const packet=parse(fs.readFileSync(path.join(r,name)), name);
  for(const row of packet.changes) {
    assert.equal(row.rootConfirmed,true);
    assert.deepEqual(row.expected,{character:''});
    assert.deepEqual(Object.keys(row.fields),['character']);
    assert.equal(row.evidence.motionAndExpressionVerified,false);
    const key=row.sceneId+':'+row.scenarioId;assert.equal(targets.has(key),false);
    targets.set(key,row);
  }
}
assert.equal(targets.size,45);
const manifest=load('manifest.json'), state=load('review/native-restoration.json');
const fields={character:0,motion:0,bg_picture:0,bg_music:0,voice:0};
let ownedNodes=0,protectedFiles=0,libraryNodes=0;
const changed=[];
for(const entry of manifest.scenes) {
  const actual=load(entry.path), old=previous(entry.path);
  libraryNodes+=actual.scenario_list.length;
  assert.equal(actual.scenario_list.length,entry.nodeCount);
  assert.equal(actual.scenario_list.length,old.scenario_list.length);
  const expected=structuredClone(old);
  for(const row of expected.scenario_list) {
    const key=entry.id+':'+row.scenario_id, target=targets.get(key);
    if(target) {assert.equal(row.character,'');row.character=target.fields.character;changed.push(key);}
  }
  assert.deepEqual(actual,expected,entry.path);
  if(Object.hasOwn(state.scenes,String(entry.id))) {
    ownedNodes+=actual.scenario_list.length;
    for(const row of actual.scenario_list)for(const field of Object.keys(fields))fields[field]+=Number(Boolean(row[field]));
  } else {
    for(const name of [entry.path,entry.reviewPath]) {
      assert.deepEqual(fs.readFileSync(path.join(data,name)),git('show',base+':'+name),name);protectedFiles++;
    }
  }
}
assert.deepEqual(new Set(changed),new Set(targets.keys()));
for(const [name,expected] of Object.entries(state.files))assert.equal(sha(fs.readFileSync(path.join(data,name))),expected,name);
for(const name of ['assets/catalog.json','assets/package.json'])assert.deepEqual(fs.readFileSync(path.join(data,name)),git('show',base+':'+name),name);
assert.equal(sha(fs.readFileSync(path.join(root,'data/story_studio/project.json'))),studioSha);
assert.deepEqual([manifest.scenes.length,libraryNodes,Object.keys(state.scenes).length,ownedNodes,protectedFiles],[140,5599,121,4998,38]);
assert.deepEqual(fields,{character:1851,motion:5,bg_picture:146,bg_music:32,voice:12});
const catalog=load('assets/catalog.json');
assert.deepEqual([Object.keys(catalog.models).length,Object.keys(catalog.backgrounds).length,Object.keys(catalog.music).length],[43,45,18]);
const report={status:'passed_independent_arm_node_exact_45_character_delta',baseCommit:base,head,
  nodeVersion:process.version,architecture:process.arch,explicitFields:fields,changedNativeFields:changed,
  libraryScenes:140,libraryNodes,ownedScenes:121,ownedNodes,protectedFiles,ownershipFilesHashed:Object.keys(state.files).length,
  studioSha256:studioSha,resourcesUnchanged:true,sourceReads:observed,mainThreadViewedImages:false,
  newBrowser:false,newPlaybackVisits:0,historicalRestorationVisits:207,fullRestorationAccepted:false};
const output=path.join(r,'target-identity-cumulative-audit-20261112-v1.json');
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,head,changedFields:changed.length,explicitFields:fields,output}));
