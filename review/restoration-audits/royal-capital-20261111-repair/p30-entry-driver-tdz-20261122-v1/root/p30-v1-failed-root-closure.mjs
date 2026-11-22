// Close the original failed attempt without converting its diagnostics into
// a playback pass. No recorder started and no native program was loaded.
// Unreadable process environments remain explicit inspection limitations.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import net from 'node:net';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const a=path.dirname(fileURLToPath(import.meta.url));
const kit=path.join(a,'p30-node4-ordinary-entry-owner-kit-rootfalse-v1'),run=path.join(kit,'attempt-1');
const releasePath=path.join(a,'ordinary-QA-root-preparation-6a6093e8-v1/p30-runtime-release.root-approved-v1.json');
const out=path.join(a,'p30-node4-ordinary-entry-v1-failed-root-closure.json');
const read=p=>fs.readFileSync(p),load=p=>JSON.parse(read(p));
function sha(p){const h=crypto.createHash('sha256'),fd=fs.openSync(p,'r'),b=Buffer.alloc(1048576);
  try{for(;;){const n=fs.readSync(fd,b);if(!n)break;h.update(b.subarray(0,n));}}finally{fs.closeSync(fd);}return h.digest('hex');}
const ref=p=>({path:p,bytes:fs.statSync(p).size,sha256:sha(p)});
const write=(p,j)=>fs.writeFileSync(p,JSON.stringify(j,null,2)+'\n',{flag:'wx'});
try{
  assert.equal(sha(releasePath),'ce770aaccb43287658aa0cd9d5ff365acaac28e931cadddeb7a29cc58b68385f');
  const release=load(releasePath),binding=load(path.join(kit,'frozen/binding.json'));
  assert.equal(sha(path.join(kit,'frozen/binding.json')),release.bindingSha256);
  const beforePath=path.join(run,'inputs-before.json'),afterPath=path.join(run,'inputs-after.json');
  assert.deepEqual(read(beforePath),read(afterPath));
  const before=load(beforePath);
  assert.deepEqual(before,release.runtimeBindings);
  for(const[p,h]of Object.entries(release.runtimeBindings))assert.equal(sha(p),h,p);
  const handles=load(path.join(run,'handles.json')),exit=load(path.join(run,'process-exit.json'));
  assert.equal(handles.state,'closed');assert.equal(exit.driverExitCode,1);assert.equal(exit.supervisorStatus,1);
  assert.equal(exit.allOwnedGroupsEmpty,true);assert.equal(exit.inputsUnchanged,true);assert.deepEqual(exit.cleanupErrors,[]);
  const pids=[handles.supervisorPid,...handles.owned.map(x=>x.pid)],groups=handles.owned.map(x=>x.pgid);
  for(const pid of pids)assert.equal(fs.existsSync('/proc/'+pid),false,'OwnedPID '+pid);
  const rows=execFileSync('ps',['-eo','pid,ppid,pgid,comm,args'],{encoding:'utf8'}).split('\n').slice(1).filter(Boolean).map(line=>{
    const m=line.trim().match(/^(\d+)\s+(\d+)\s+(\d+)\s+(\S+)(?:\s+(.*))?$/);assert.ok(m,line);
    return {pid:+m[1],ppid:+m[2],pgid:+m[3],comm:m[4],args:m[5]||''};});
  assert.deepEqual(rows.filter(r=>groups.includes(r.pgid)),[]);
  assert.deepEqual(rows.filter(r=>/^(firefox|firefox-bin|chrome|chromium|chromium-browse|Xvfb|ffmpeg|ffprobe)$/.test(r.comm)),[]);
  const escapedArgs=rows.filter(r=>r.pid!==process.pid&&r.args.includes(kit));assert.deepEqual(escapedArgs,[]);
  const environmentDenied=[],environmentRaced=[],escapedEnvironment=[];
  for(const pid of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x)&&+x!==process.pid)){
    try{const vars=read('/proc/'+pid+'/environ').toString().split('\0');
      if(vars.some(v=>v.includes(kit)||v==='STELLA_RUNTIME_RELEASE_PATH='+releasePath||v==='STELLA_PRIVATE_OUTPUT='+run))escapedEnvironment.push(+pid);
    }catch(e){if(['ENOENT','ESRCH'].includes(e.code))environmentRaced.push(+pid);
      else if(['EACCES','EPERM'].includes(e.code))environmentDenied.push({pid:+pid,code:e.code});else throw e;}}
  assert.deepEqual(escapedEnvironment,[]);
  const paths=[...['root','profile','authority'].map(k=>handles.temporaryState[k]),'/tmp/.X11-unix/X'+handles.display.slice(1),'/tmp/.X'+handles.display.slice(1)+'-lock'];
  for(const p of paths)assert.equal(fs.existsSync(p),false,p);
  const ports=[];
  for(const port of [5198,+new URL(handles.address).port]){
    const state=await new Promise(resolve=>{const s=net.createConnection({host:'127.0.0.1',port});
      s.once('connect',()=>{s.destroy();resolve('connected');});s.once('error',e=>resolve(e.code));
      s.setTimeout(1000,()=>{s.destroy();resolve('timeout');});});assert.equal(state,'ECONNREFUSED');ports.push({port,state});}
  const capture=load(path.join(run,'capture-index.json'));assert.deepEqual(capture.captures,[]);assert.equal(capture.driverExitCode,1);
  assert.equal(handles.owned.some(x=>x.role.startsWith('recorder')),false);
  const terminal=load(path.join(run,'terminal-failure.json'));
  assert.equal(terminal.firstFailure.stage,'p30-node4-unchanged-ordinary:fresh-document');
  assert.equal(terminal.firstFailure.error,"ReferenceError: Cannot access 'target' before initialization");
  const driver=read(path.join(kit,'driver.mjs')).toString(),lines=driver.split('\n');
  assert.ok(lines[293].includes('context:target.context'));
  assert.ok(driver.includes('const target=active.holds.find(h=>h.scenario===4)'));
  const refs=fs.readdirSync(run).filter(n=>fs.statSync(path.join(run,n)).isFile()).map(n=>ref(path.join(run,n)));
  const receipt={schema:'stella.p30.ordinary-entry.failed-root-closure.v1',createdAt:new Date().toISOString(),session:57682,exitCode:1,
    release:ref(releasePath),dataHead:binding.finalDataHead,sourceHead:binding.finalSourceHead,
    allRuntimeBindingsFreshExact:true,runtimeGuardCount:Object.keys(release.runtimeBindings).length,inputBefore:ref(beforePath),inputAfter:ref(afterPath),
    knownAbsentPIDs:pids,knownEmptyPGIDs:groups,escapedArgs,escapedEnvironment,environmentDenied,environmentRaced,
    environmentScanLimit:'Permission-denied environments were not inspected; explicit PID/PGID, command inventory, ports and temporary-path facts are independent.',
    allMediaAndTestBrowserProcessesAbsent:true,ports,temporaryAndDisplayPathsAbsent:paths,
    existingUserFloorp:rows.filter(r=>r.pid===9671).map(({pid,pgid,comm})=>({pid,pgid,comm})),foreignProcessesSignalled:false,
    firstFailure:terminal.firstFailure,cause:'The case try block declares a later const target hold record, shadowing the outer browser context target throughout that block. The first navigate access occurs in its temporal dead zone.',
    productFailureClaimed:false,programLoaded:false,recorderStarted:false,captureCount:0,playbackAccepted:false,rootViewedImages:false,
    originalAttemptExhausted:true,additionalExecutionAuthorized:false,wholeEpisodeAccepted:false,references:refs};
  write(out,receipt);console.log(JSON.stringify({closure:ref(out),runtimeGuardCount:receipt.runtimeGuardCount,ports,knownAbsentPIDs:pids,playbackAccepted:false,allClosed:true}));
}catch(error){write(out+'.failed.json',{createdAt:new Date().toISOString(),error:String(error),stack:error.stack});throw error;}
