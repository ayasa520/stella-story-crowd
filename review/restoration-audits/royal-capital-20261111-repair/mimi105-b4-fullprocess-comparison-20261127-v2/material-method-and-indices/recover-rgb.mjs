/** Root-authorized recovery from the MJPEG encoder's duplicate-PTS refusal.
 * The failed exit234 and155 partial JPEGs are retained separately. Original
 * video time is never rewritten: the RGB24 stream is encoded as independent
 * stills, and all original showinfo PTS must match the probe by frame ordinal.
 * No raw RGB movie, PNG, replacement video, frame interpolation or setpts is
 * produced. Geometry stays500x1000; RGB conversion and JPEG loss are explicit.
 */
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import os from 'node:os';import {spawn} from 'node:child_process';
const O=path.dirname(new URL(import.meta.url).pathname),ROOT='/home/rikka/Projects/stella';
const PY=path.join(ROOT,'.venv-video-ocr/bin/python'),WORKER=path.join(O,'encode-rgb-frames.py');
const FONT='/home/rikka/.local/share/fonts/Hack-Regular.ttf',MAX=256*1024*1024,STOP=240*1024*1024;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ref=p=>{const b=fs.readFileSync(p);return {path:p,bytes:b.length,sha256:sha(b)}};
const save=(p,d)=>fs.writeFileSync(p,JSON.stringify(d,null,2)+'\n',{flag:'wx'});
const need=(v,m)=>{if(!v)throw Error(m)};
const allocated=p=>fs.readdirSync(p,{withFileTypes:true}).reduce((n,e)=>{const f=path.join(p,e.name);return n+(e.isDirectory()?allocated(f):fs.statSync(f).blocks*512)},0);
const probes=JSON.parse(fs.readFileSync(path.join(O,'probe-index.json'),'utf8'));
const env={...process.env,OPENBLAS_NUM_THREADS:'1',OMP_NUM_THREADS:'1',MKL_NUM_THREADS:'1',NUMEXPR_NUM_THREADS:'1',PYTHONDONTWRITEBYTECODE:'1'};
need(os.getPriority(0)===19,'nice19 required');
const affinity=fs.readFileSync('/proc/self/status','utf8').match(/^Cpus_allowed_list:\s*(.+)$/m)?.[1]?.trim();
need(affinity==='0-1'||affinity==='0,1','CPUs0,1 required');
save(path.join(O,'recovery-run-start.json'),{orchestratorPID:process.pid,createdUTC:new Date().toISOString(),rootExplicitRecoveryAuthorized:true,originalFailuresPreserved:true});

async function contacts(C,framesDir,sheetsDir){
  const filter=`scale=200:400:flags=area,drawtext=fontfile=${FONT}:text='%{n}':x=4:y=4:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.65,tile=5x5:nb_frames=25:padding=3:margin=3:color=0x303030`;
  const argv=['-hide_banner','-nostdin','-v','warning','-threads','1','-start_number','0','-i',path.join(framesDir,'%04d.jpg'),'-an','-sn','-dn','-filter_threads','1','-filter_complex_threads','1','-vf',filter,'-fps_mode','passthrough','-q:v','4','-threads','1','-start_number','0',path.join(sheetsDir,'%03d.jpg')];
  save(path.join(C,'contacts.command.json'),{executable:'/usr/bin/ffmpeg',argv});
  const out=path.join(C,'contacts.stdout.log'),err=path.join(C,'contacts.stderr.log'),o=fs.openSync(out,'wx'),e=fs.openSync(err,'wx');
  const child=spawn('/usr/bin/ffmpeg',argv,{env,stdio:['ignore',o,e]});let error=null,stopped=false;child.on('error',x=>error=String(x));
  const timer=setInterval(()=>{if(allocated(O)>=STOP&&!stopped){stopped=true;child.kill('SIGINT')}},150);
  const terminal=await new Promise(r=>child.once('close',(exitCode,signal)=>r({exitCode,signal})));clearInterval(timer);fs.closeSync(o);fs.closeSync(e);
  const result={pid:child.pid,...terminal,error,budgetStop:stopped,stdout:ref(out),stderr:ref(err),retries:0,originalPIDAbsentAfterClose:!fs.existsSync('/proc/'+child.pid)};
  save(path.join(C,'contacts.exit.json'),result);need(terminal.exitCode===0&&terminal.signal===null&&!error&&!stopped,'Contact CLI failed');return result;
}

const summaries=[];
try{
  // Seal the incomplete failed output before creating a separate recovery.
  const failed=probes.cases.find(x=>x.case==='mimi105-B2F0'),F=path.join(O,failed.case),oldFrames=path.join(F,'frames');
  const rawProbe=JSON.parse(fs.readFileSync(failed.probeOutput.path,'utf8')).frames;
  const partial=fs.readdirSync(oldFrames).sort().map((n,i)=>({frameOrdinalZeroBased:i,...ref(path.join(oldFrames,n)),originalPTS:rawProbe[i].best_effort_timestamp??rawProbe[i].pts,timeBase:failed.timeBase}));
  need(partial.length===155,'Original failed partial count differs');
  save(path.join(F,'failed-mjpeg-partial-index.json'),{originalExit:ref(path.join(F,'decode.exit.json')),frames:partial,incomplete:true,excludedFromActualCaseReview:true,originalFailureRetained:true});
  for(const item of probes.cases.filter(x=>x.case.startsWith('mimi105-B2'))){
    const C=path.join(O,item.case,'rgb-recovery-v1'),framesDir=path.join(C,'frames'),sheetsDir=path.join(C,'sheets');fs.mkdirSync(C);fs.mkdirSync(framesDir);fs.mkdirSync(sheetsDir);
    need(ref(item.media.path).sha256===item.media.sha256,'Original MKV changed');
    const decodeArgs=['-hide_banner','-nostdin','-nostats','-v','info','-threads','1','-i',item.media.path,'-map','0:v:0','-an','-sn','-dn','-filter_threads','1','-filter_complex_threads','1','-vf','format=rgb24,showinfo','-fps_mode','passthrough','-c:v','rawvideo','-pix_fmt','rgb24','-threads','1','-f','rawvideo','pipe:1'];
    const encodeArgs=['-B',WORKER,framesDir,String(item.width),String(item.height),String(item.frameCount)];
    save(path.join(C,'commands.json'),{ffmpeg:{executable:'/usr/bin/ffmpeg',argv:decodeArgs},independentJPEG:{executable:PY,argv:encodeArgs},rawvideoStreamSavedToDisk:false,frameBytes:item.width*item.height*3});
    const ffErr=path.join(C,'decode.stderr.log'),pyErr=path.join(C,'encode.stderr.log'),pyOut=path.join(C,'encode.stdout.log');
    const ffd=fs.openSync(ffErr,'wx'),ped=fs.openSync(pyErr,'wx'),pod=fs.openSync(pyOut,'wx');
    const consumer=spawn(PY,encodeArgs,{env,stdio:['pipe',pod,ped]}),producer=spawn('/usr/bin/ffmpeg',decodeArgs,{env,stdio:['ignore','pipe',ffd]});
    let rawBytes=0,budgetStop=false,producerError=null,consumerError=null,pipeError=null;const rawHash=crypto.createHash('sha256');
    producer.on('error',e=>producerError=String(e));consumer.on('error',e=>consumerError=String(e));
    producer.stdout.on('data',b=>{rawBytes+=b.length;rawHash.update(b)});
    producer.stdout.on('error',e=>pipeError=String(e));consumer.stdin.on('error',e=>{pipeError=String(e);producer.kill('SIGINT')});
    producer.stdout.pipe(consumer.stdin);
    const timer=setInterval(()=>{if(allocated(O)>=STOP&&!budgetStop){budgetStop=true;producer.kill('SIGINT');consumer.kill('SIGINT')}},150);
    const a=new Promise(r=>producer.once('close',(exitCode,signal)=>r({exitCode,signal}))),b=new Promise(r=>consumer.once('close',(exitCode,signal)=>r({exitCode,signal})));
    const [decodeExit,encodeExit]=await Promise.all([a,b]);clearInterval(timer);for(const fd of [ffd,ped,pod])fs.closeSync(fd);
    const terminal={case:item.case,decoder:{pid:producer.pid,...decodeExit,error:producerError,stderr:ref(ffErr)},JPEGEncoder:{pid:consumer.pid,...encodeExit,error:consumerError,stdout:ref(pyOut),stderr:ref(pyErr)},pipeError,budgetStop,rawStreamBytes:rawBytes,rawStreamSHA256:rawHash.digest('hex'),rawStreamNotMaterializedOnDisk:true,retries:0,originalPIDAbsence:[producer.pid,consumer.pid].map(pid=>({pid,absent:!fs.existsSync('/proc/'+pid)}))};
    save(path.join(C,'decode-encode.exit.json'),terminal);
    need(decodeExit.exitCode===0&&decodeExit.signal===null&&encodeExit.exitCode===0&&encodeExit.signal===null&&!producerError&&!consumerError&&!pipeError&&!budgetStop,'Original RGB decode/encode CLI failed');
    const original=JSON.parse(fs.readFileSync(item.probeOutput.path,'utf8')).frames;
    const log=fs.readFileSync(ffErr,'utf8'),matches=[...log.matchAll(/\[Parsed_showinfo_\d+ @ [^\]]+\] n:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([-\d.]+)/g)];
    need(matches.length===item.frameCount,'showinfo count differs from complete probe');
    const config=[...log.matchAll(/config in time_base:\s*(\d+)\/(\d+)/g)];need(config.length>=1&&`${config[0][1]}/${config[0][2]}`===item.timeBase,'showinfo time_base differs');
    matches.forEach((m,i)=>need(Number(m[1])===i&&Number(m[2])===(original[i].best_effort_timestamp??original[i].pts),'Original showinfo ordinal/PTS differs at '+i));
    need(rawBytes===item.width*item.height*3*item.frameCount,'Raw RGB stream was truncated or contained extra data');
    const digestLines=fs.readFileSync(path.join(C,'raw-frame-digests.tsv'),'utf8').trim().split('\n').slice(1);need(digestLines.length===item.frameCount,'Independent JPEG digest count differs');
    const names=fs.readdirSync(framesDir).sort();need(names.length===item.frameCount,'JPEG count differs');
    const frames=names.map((n,i)=>{need(n===String(i).padStart(4,'0')+'.jpg','Frame sequence incomplete');const [ord,rgbHash,bytes,jpegHash]=digestLines[i].split('\t'),r=ref(path.join(framesDir,n));need(Number(ord)===i&&Number(bytes)===r.bytes&&jpegHash===r.sha256,'Independent JPEG bytes differ');return {frameOrdinalZeroBased:i,...r,rawRGB24SHA256:rgbHash,originalPTS:original[i].pts??null,originalBestEffortPTS:original[i].best_effort_timestamp??null,originalBestEffortSeconds:original[i].best_effort_timestamp_time??null,matchedShowinfoPTS:Number(matches[i][2]),timeBase:item.timeBase}});
    const contactExit=await contacts(C,framesDir,sheetsDir),pages=fs.readdirSync(sheetsDir).sort();need(pages.length===Math.ceil(frames.length/25),'Contact coverage incomplete');
    const sheets=pages.map((n,i)=>({sheet:i,...ref(path.join(sheetsDir,n)),firstFrameOrdinal:i*25,lastFrameOrdinal:Math.min(frames.length-1,i*25+24),actualFrameCells:Math.min(25,frames.length-i*25),columns:5,rows:5,thumbnail:[200,400],labels:'zero-based decoded ordinal, no synthetic original PTS'}));
    const index=path.join(C,'index.json');save(index,{schema:'stella.mimi105.b4.actual-case-material.rgb.v1',case:item.case,media:item.media,frameCount:frames.length,dimensions:[item.width,item.height],timeBase:item.timeBase,originalPTSAnomalies:item.duplicates,originalProbe:item.probeOutput,probeExit:item.probeExit,RGBDecodeEncodeExit:ref(path.join(C,'decode-encode.exit.json')),contactsExit:ref(path.join(C,'contacts.exit.json')),showinfoAllOrdinalsAndOriginalPTSMatched:true,completeOriginalEOF:true,rawRGBByteCountExact:true,noFrameSelectionDroppingInterpolationOrRetiming:true,passthroughDecode:true,colorAndCompressionBoundary:'FFmpeg decoded YUV is converted to native-size RGB24; ARM Pillow creates independent quality90/subsampling0 lossy JPEG stills. No pixels are posed, cropped or temporally transformed. Original MKV remains authoritative.',priorFailedMJPEG:item.case==='mimi105-B2F0'?ref(path.join(O,item.case,'decode.exit.json')):null,frames,contactSheets:sheets});
    need(ref(item.media.path).sha256===item.media.sha256,'Original MKV changed after recovery');need(allocated(O)<=MAX,'256MiB cap exceeded');
    const summary={case:item.case,index:ref(index),frames:frames.length,sheets:sheets.length,decodeExitCode:decodeExit.exitCode,JPEGEncoderExitCode:encodeExit.exitCode,contactsExitCode:contactExit.exitCode,allocatedMaterialBytes:allocated(O),allOriginalFramePTSAndOrdinalsMatched:true};summaries.push(summary);console.log(JSON.stringify(summary));
  }
  save(path.join(O,'recovery-stage-complete.json'),{orchestratorPID:process.pid,orchestratorStillRunningUntilCLIExit:true,cases:summaries,originalFailure234Preserved:true,maximumMaterialBytes:MAX,allocatedMaterialBytes:allocated(O),imagesViewed:false});
}catch(error){save(path.join(O,'recovery-failure.json'),{error:String(error),stack:error.stack,completed:summaries,allocatedMaterialBytes:allocated(O),imagesViewed:false});throw error;}
