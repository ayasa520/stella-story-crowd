/** Extract every original decoded frame for the root-released B4 review.
 * Frame ordinal and original ffprobe PTS remain separate identities. Equal
 * source PTS are preserved, never repaired, dropped, interpolated or retimed.
 * Contact sheets are spatial review aids; their JPEG-sequence input clock is
 * not used as evidence of original video, actor or native command timing.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import {spawn} from 'node:child_process';

const O=path.dirname(new URL(import.meta.url).pathname);
const MAX=256*1024*1024, STOP=240*1024*1024;
const FONT='/home/rikka/.local/share/fonts/Hack-Regular.ttf';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ref=p=>{const b=fs.readFileSync(p);return {path:p,bytes:b.length,sha256:sha(b)};};
const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const demand=(v,s)=>{if(!v)throw Error(s);};
const allocated=p=>fs.readdirSync(p,{withFileTypes:true}).reduce((n,e)=>{
  const f=path.join(p,e.name);return n+(e.isDirectory()?allocated(f):fs.statSync(f).blocks*512);
},0);
const probeIndex=JSON.parse(fs.readFileSync(path.join(O,'probe-index.json'),'utf8'));
const exits=[];
demand(os.getPriority(0)===19,'nice19 required');
const affinity=fs.readFileSync('/proc/self/status','utf8').match(/^Cpus_allowed_list:\s*(.+)$/m)?.[1]?.trim();
demand(affinity==='0-1'||affinity==='0,1','CPUs0,1 required');

async function run(C,stem,argv){
  save(path.join(C,stem+'.command.json'),{executable:'/usr/bin/ffmpeg',argv,nice:19,cpuAffinity:affinity,allThreads:1});
  const stdout=path.join(C,stem+'.stdout.log'),stderr=path.join(C,stem+'.stderr.log');
  const outFD=fs.openSync(stdout,'wx'),errFD=fs.openSync(stderr,'wx');
  const child=spawn('/usr/bin/ffmpeg',argv,{stdio:['ignore',outFD,errFD]});
  let error=null,budgetStop=false,peak=allocated(O);
  child.once('error',e=>{error={name:e.name,message:e.message,code:e.code};});
  const watch=setInterval(()=>{
    peak=Math.max(peak,allocated(O));
    if(peak>=STOP&&!budgetStop){budgetStop=true;child.kill('SIGINT');}
  },150);
  const terminal=await new Promise(resolve=>child.once('close',(exitCode,signal)=>resolve({exitCode,signal})));
  clearInterval(watch);fs.closeSync(outFD);fs.closeSync(errFD);
  peak=Math.max(peak,allocated(O));
  const record={stem,pid:child.pid,...terminal,error,budgetStop,allocatedPeakBytes:peak,
    stdout:ref(stdout),stderr:ref(stderr),originalExitPreserved:true,retries:0,
    originalPIDAbsentAfterClose:!child.pid||!fs.existsSync('/proc/'+child.pid)};
  save(path.join(C,stem+'.exit.json'),record);exits.push(record);
  demand(!error&&terminal.exitCode===0&&terminal.signal===null&&!budgetStop,stem+' failed; original evidence retained');
  demand(peak<=MAX,'256MiB material cap exceeded');
  return record;
}

try{
  const cases=[];
  for(const item of probeIndex.cases){
    const C=path.join(O,item.case),framesDir=path.join(C,'frames'),sheetsDir=path.join(C,'sheets');
    demand(ref(item.media.path).sha256===item.media.sha256,'Original MKV changed');
    fs.mkdirSync(framesDir);fs.mkdirSync(sheetsDir);
    const decode=await run(C,'decode',['-hide_banner','-nostdin','-v','warning','-threads','1','-i',item.media.path,
      '-map','0:v:0','-an','-sn','-dn','-filter_threads','1','-filter_complex_threads','1',
      '-fps_mode','passthrough','-q:v','4','-threads','1','-start_number','0',path.join(framesDir,'%04d.jpg')]);
    const names=fs.readdirSync(framesDir).sort();
    demand(names.length===item.frameCount,'Decoded frame count differs from complete original ffprobe');
    const expected=Array.from({length:item.frameCount},(_,i)=>String(i).padStart(4,'0')+'.jpg');
    demand(names.every((n,i)=>n===expected[i]),'Decoded frame ordinals are incomplete');
    const original=JSON.parse(fs.readFileSync(item.probeOutput.path,'utf8')).frames;
    const frames=names.map((n,i)=>({frameOrdinalZeroBased:i,...ref(path.join(framesDir,n)),
      originalPTS:original[i].pts??null,originalPTSSeconds:original[i].pts_time??null,
      originalBestEffortPTS:original[i].best_effort_timestamp??null,
      originalBestEffortSeconds:original[i].best_effort_timestamp_time??null,timeBase:item.timeBase}));
    // All frames feed the tile filter in their decoded ordinal order. The
    // visible label is that zero-based ordinal, not a synthetic source time.
    const filter=`scale=200:400:flags=area,drawtext=fontfile=${FONT}:text='%{n}':x=4:y=4:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.65,tile=5x5:nb_frames=25:padding=3:margin=3:color=0x303030`;
    const contact=await run(C,'contacts',['-hide_banner','-nostdin','-v','warning','-threads','1',
      '-start_number','0','-i',path.join(framesDir,'%04d.jpg'),'-an','-sn','-dn',
      '-filter_threads','1','-filter_complex_threads','1','-vf',filter,'-fps_mode','passthrough',
      '-q:v','4','-threads','1','-start_number','0',path.join(sheetsDir,'%03d.jpg')]);
    const sheets=fs.readdirSync(sheetsDir).sort();
    demand(sheets.length===Math.ceil(frames.length/25),'Contact sheets omit a final partial page');
    const contacts=sheets.map((n,i)=>({sheet:i,...ref(path.join(sheetsDir,n)),
      firstFrameOrdinal:i*25,lastFrameOrdinal:Math.min(frames.length-1,i*25+24),
      actualFrameCells:Math.min(25,frames.length-i*25),columns:5,rows:5,thumbnail:[200,400],
      labels:'zero-based decoded frame ordinal; see frames for original PTS'}));
    const value={schema:'stella.mimi105.b4.actual-case-material.v1',case:item.case,media:item.media,
      frameCount:frames.length,dimensions:[item.width,item.height],timeBase:item.timeBase,
      originalPTSAnomalies:item.duplicates,originalProbe:item.probeOutput,originalProbeExit:item.probeExit,
      decodeExit:ref(path.join(C,'decode.exit.json')),contactsExit:ref(path.join(C,'contacts.exit.json')),
      noFrameSelectionDroppingInterpolationOrRetiming:true,passthroughDecode:true,
      JPEGQualityScale:4,contactSheetsAreSpatialReviewAidsOnly:true,frames,contactSheets:contacts};
    const index=path.join(C,'index.json');save(index,value);
    demand(ref(item.media.path).sha256===item.media.sha256,'Original MKV changed after extraction');
    const summary={case:item.case,index:ref(index),frameCount:frames.length,contactSheets:contacts.length,
      decodeExitCode:decode.exitCode,contactsExitCode:contact.exitCode,allocatedMaterialBytes:allocated(O),
      originalPTSAnomalyCount:item.duplicates.length};
    cases.push(summary);console.log(JSON.stringify(summary));
  }
  const index=path.join(O,'material-index.json');
  save(index,{schema:'stella.mimi105.b4.actual-shared-material.v1',createdUTC:new Date().toISOString(),
    rootConfirmed:false,source:'Four root-released original B4 MKVs; shared by both independent image reviewers.',
    probeIndex:ref(path.join(O,'probe-index.json')),initialStrictPTSAssertion:'failed_preserved',
    initialPTSFailure:ref(path.join(O,'probe-initial-check-failure.json')),cases,
    totalFrames:cases.reduce((n,c)=>n+c.frameCount,0),allOriginalDecoderAndContactExitCodesZero:true,
    allFrameOrdinalsCovered:true,knownEqualPTS:'B2F0 three pairs, B2F1 one pair; original values retained with frame ordinal.',
    noPNGOrCopiedOriginalVideo:true,actualCaseResultJSONRead:false,imagesViewed:false,
    allocatedMaterialBytesAtIndex:allocated(O),maximumMaterialBytes:MAX,
    execution:{nice:19,cpuAffinity:affinity,ffmpegDecoderFilterEncoderThreads:1},
    noDOrCOrBrowserAPIOrGitOperation:true});
  save(path.join(O,'extraction-stage-complete.json'),{orchestratorPID:process.pid,orchestratorStillRunningUntilCLIExit:true,
    childExits:exits,materialIndex:ref(index),allChildOriginalExitCodesZero:true,
    finalCLIClosureRequiredBeforeImages:true,allocatedMaterialBytes:allocated(O),maximumMaterialBytes:MAX});
}catch(error){
  save(path.join(O,'extraction-failure.json'),{error:String(error),stack:error.stack,childExits:exits,
    allocatedMaterialBytes:allocated(O),retries:0,imagesViewed:false});throw error;
}
