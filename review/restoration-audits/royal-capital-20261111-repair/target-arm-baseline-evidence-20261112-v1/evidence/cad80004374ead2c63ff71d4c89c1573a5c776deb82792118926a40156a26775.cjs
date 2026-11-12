/** Prepare one explicit root release for a normal P30 program on the ARM host.
 *
 * The independently reviewed adapter/compiler is reused without private story
 * overrides. This step creates a fresh EMPTY registry and binds the complete
 * native/review read set, canonical checkout and installed ARM payloads. It
 * authorizes only this read-only adapter/compiler run; Chrome stays unreleased.
 * Actual compilation/HTTP behavior must produce their own runtime receipts.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root='/home/rikka/Projects/stella';
const r=path.join(root,'data/native_recovery/royal-capital-20261110/repair-20261111');
const data=path.join(root,'story_crowd_data');
const site=path.join(root,'artifacts/stella-site-repair-source/.sites-checkout');
const adapter=path.join(r,'target-arm-adapter-20261112-v2');
const tools=path.join(r,'target-arm-tools-20261112-v1');
const work=path.join(r,'target-arm-baseline-20261112-v1');
const peerFile=path.join(r,'target-arm-adapter-peer-20261112-v2/receipt.json');
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const load=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const identity=file=>{file=fs.realpathSync(file);const raw=fs.readFileSync(file);return {path:file,sha256:sha(raw),bytes:raw.length};};
const git=(cwd,...args)=>execFileSync('git',['--no-optional-locks',...args],{cwd,maxBuffer:8*1024*1024}).toString().trim();
const write=(file,value)=>fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
assert.equal(process.arch,'arm64');
assert.equal(require('node:os').getPriority(),19);
assert.match(fs.readFileSync('/proc/self/status','utf8'),/Cpus_allowed_list:\s+(?:0-1|0,1)\s/);
assert.equal(git(data,'status','--porcelain'),'');assert.equal(git(site,'status','--porcelain'),'');
assert.equal(fs.existsSync(work),false);
const peer=load(peerFile);
assert.equal(peer.status,'static_pass_no_execution_release');assert.deepEqual(peer.blockingFindings,[]);
const prepared=peer.preparationReceipt;
assert.equal(identity(prepared.file).sha256,prepared.sha256);
for(const entry of peer.reviewedFiles)assert.equal(identity(entry.file).sha256,entry.sha256,entry.file);
const toolReceipt=path.join(tools,'toolchain-receipt.json');
assert.equal(identity(toolReceipt).sha256,'1348b6ee3de36beac729002e6dc5812f5fc544b93e767e946352e3c283e08753');
const tool=load(toolReceipt),inventoryFile=tool.installedFileManifest.file;
assert.equal(identity(inventoryFile).sha256,tool.installedFileManifest.sha256);
const inventory=load(inventoryFile),guards=new Map();
const add=file=>{const entry=identity(file);assert(entry.path.startsWith(root+'/'));guards.set(entry.path,entry);};
for(const entry of inventory.files)if(entry.sha256){
  const file=path.join(tools,entry.relativePath);assert.equal(identity(file).sha256,entry.sha256,file);add(file);
}
for(const file of [toolReceipt,inventoryFile,path.join(tools,'package-lock.json'),path.join(tools,'package.json')])add(file);
for(const name of ['serve.py','adapter_config.py','compile.mjs','index.html','target_verified_utf8_v1.py'])add(path.join(adapter,name));
const tracked=execFileSync('git',['ls-files','-z'],{cwd:site}).toString().split('\0').filter(Boolean);
for(const name of tracked)add(path.join(site,name));
for(const name of ['manifest.json','assets/catalog.json','assets/package.json','review/native-restoration.json'])add(path.join(data,name));
const manifest=load(path.join(data,'manifest.json'));
for(const scene of manifest.scenes)for(const key of ['path','reviewPath'])add(path.join(data,scene[key]));
add(path.join(root,'data/story_studio/project.json'));
assert.equal(identity(path.join(root,'data/story_studio/project.json')).sha256,'ebd974d90f89088fa3a504c1f419ae01c352a24e6bd80209c5ec651295d38522');
fs.mkdirSync(work);
const runtime=path.join(adapter,'runtime-baseline-20261112-v1');assert.equal(fs.existsSync(runtime),false);fs.mkdirSync(runtime);
const registry=path.join(runtime,'registry.json');write(registry,[]);
const registryBinding=identity(registry);
const release={schema:'stella.target_arm_adapter_release.v1',status:'root_deliberate_normal_program_baseline_release',
  rootConfirmed:true,adapterLaunchAuthorized:true,compilerExecutionAuthorized:true,browserExecutionAuthorized:false,
  registryApproved:true,formalWritesAllowed:false,canonicalSiteRoot:site,adapterRoot:adapter,toolRoot:tools,
  registryBinding:{path:registry,sha256:registryBinding.sha256},toolchainReceiptBinding:{path:toolReceipt,sha256:identity(toolReceipt).sha256},
  independentPeer:identity(peerFile),preparationReceipt:identity(prepared.file),dataHead:git(data,'rev-parse','HEAD'),
  canonicalHead:git(site,'rev-parse','HEAD'),guardFiles:[...guards.values()].sort((a,b)=>a.path.localeCompare(b.path)),
  allowedRequests:[{sceneId:10450054,scenarioId:4,nativePreview:''}],registryScopeCount:0,
  noPrivateOverrides:true,maximumCompilerRequestSeconds:45,rootExecutionOwner:'/root',
  heavyNice:19,cpuAffinity:[0,1],fullRestorationAccepted:false};
const releaseFile=path.join(work,'root-release.json');write(releaseFile,release);
const launch=['python3',path.join(adapter,'serve.py'),'--port','5190','--site-root',site,
  '--registry',registry,'--registry-sha256',registryBinding.sha256,'--toolchain-receipt',toolReceipt,
  '--toolchain-sha256',identity(toolReceipt).sha256,'--release',releaseFile,'--release-sha256',identity(releaseFile).sha256];
write(path.join(work,'preparation.json'),{status:'prepared_for_one_deliberately_released_readonly_baseline',
  release:identity(releaseFile),registry:registryBinding,guardFiles:guards.size,canonicalTrackedFiles:tracked.length,
  dataHead:release.dataHead,canonicalHead:release.canonicalHead,launchCommand:launch,
  requestURL:'http://127.0.0.1:5190/program?scene=10450054&node=4',browserExecutionAuthorized:false,
  compilerExecuted:false,adapterStarted:false,formalWrites:0,fullRestorationAccepted:false});
console.log(JSON.stringify({work,guards:guards.size,releaseSha256:identity(releaseFile).sha256,launchCommand:launch}));
