// The saved API and normal controls own all player state. Passive observers
// retain event/Normal/generation provenance; they never supply a seed or time.
import assert from 'node:assert/strict';
import {readFile,writeFile,appendFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';
import {connect} from '../../stella-p30-firefox-20261120/bidi.mjs';
import {installRenderProbe} from '../../stella-p30-firefox-20261120/render-probe.mjs';
import {installEndingObserver} from './ending-observer.mjs';
import {installCaptureReadiness} from './capture-readiness.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const binding=JSON.parse(await readFile(new URL('input-binding.json',here),'utf8'));
const plan=JSON.parse(await readFile(new URL('capture-plan.json',here),'utf8'));
const preflight=JSON.parse(await readFile(new URL('normal-prepare-receipt.json',here),'utf8'));
const musicMetadata=JSON.parse(await readFile(new URL('win01-metadata.json',here),'utf8'));
const output=process.env.STELLA_REVIEW_OUTPUT;assert.ok(output);
const driver=await connect(process.argv[2]);
const traces=[],records=[],errors=[],http=[],actions=[],cases=[],captures=[],writes=[],languageControlActions=[];
let target,capabilities,stage='connect',caseName='setup',configuration,totalImageBytes=0;
const sha=value=>createHash('sha256').update(value).digest('hex');
const save=async(name,value)=>writeFile(resolve(output,name),JSON.stringify(value,null,2)+'\n');
async function evaluate(fn,arg){
 const response=await driver.call('script.evaluate',{target,awaitPromise:true,
  expression:`(async()=>JSON.stringify(await (${fn})(${JSON.stringify(arg)})))()`});
 if(response.type!=='success')throw Error(response.exceptionDetails?.text||'Firefox evaluation failed');
 if(response.result.type==='undefined')return null;
 return JSON.parse(response.result.value);
}
const parsed=(prefix,start=0)=>traces.slice(start).filter(s=>s.startsWith(prefix)).map(s=>JSON.parse(s.slice(prefix.length)));
async function snapshot(){return evaluate(()=>({
 ...window.reviewEndingObserver.snapshot(),render:window.reviewRenderProbe.snapshot(),
 text:document.getElementById('accessibleText').textContent,
 language:document.getElementById('language').value,
 panel:{hidden:document.getElementById('subtitles').hidden,
  alpha:getComputedStyle(document.getElementById('subtitles')).opacity,
  translate:getComputedStyle(document.getElementById('subtitles')).translate},
 history:[...document.querySelectorAll('#history li')].map(n=>n.textContent)}));}
async function click(selector){
 const point=await evaluate(selector=>{
  const n=document.querySelector(selector);if(!n||n.disabled||!n.checkVisibility())return null;
  n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)};
 },selector);assert.ok(point,'Visible normal control '+selector);
 actions.push({caseName,selector,before:await snapshot()});
 await driver.call('input.performActions',{context:target.context,actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},
  actions:[{type:'pointerMove',origin:'viewport',...point,duration:0},{type:'pointerDown',button:0},{type:'pointerUp',button:0}]}]});
 actions.at(-1).afterEpochMilliseconds=Date.now();
}
async function waitFor(fn,arg,timeout=45000){
 const end=Date.now()+timeout;
 while(Date.now()<end){
  if(errors.length)throw Error(errors.at(-1));
  const found=await evaluate(fn,arg);if(found)return found;
  for(const selector of ['#movieContinue','#voiceContinue']){
   if(await evaluate(s=>{const n=document.querySelector(s);return n&&!n.hidden&&!n.disabled&&n.checkVisibility();},selector))await click(selector);
  }
  await delay(50);
 }
 throw Error('Normal condition timed out '+caseName+'/'+stage);
}
async function waitTrace(test,timeout=15000){
 const end=Date.now()+timeout;while(Date.now()<end){if(errors.length)throw Error(errors.at(-1));const found=test();if(found)return found;await delay(40);}
 throw Error('Expected original event timed out '+caseName+'/'+stage);
}
async function languageInventory(){return evaluate(()=>{
 const n=document.getElementById('language');
 const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
 const ancestors=[];
 for(let e=n;e instanceof Element;e=e.parentElement){const s=getComputedStyle(e);
  ancestors.push({tag:e.tagName,id:e.id,display:s.display,visibility:s.visibility,opacity:s.opacity,rect:rect(e)});}
 return {found:!!n,disabled:n?.disabled??null,value:n?.value??null,
  checkVisibility:!!n?.checkVisibility({opacityProperty:true,visibilityProperty:true}),
  rect:n?rect(n):null,ancestors,innerWidth:innerWidth,innerHeight:innerHeight,
  node:document.body.dataset.node,phase:document.body.dataset.phase,epochMilliseconds:Date.now()};
});}
async function setLanguage(language){
 const entry={caseName,expectedLanguage:language,before:await languageInventory()};languageControlActions.push(entry);
 if(entry.before.value===language){entry.action='already-selected';return;}
 assert.equal(language,'ja');let failure;
 try{
  // The production responsive stylesheet hides aside labels at <=650px.
  // Expose its original select through a real temporary browser resize, then
  // restore the captured440px viewport before loading any new saved program.
  // No CSS, DOM value, synthetic change event or game clock is altered.
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:{width:1000,height:900},devicePixelRatio:1});
  entry.expanded=await languageInventory();
  assert.equal(entry.expanded.innerWidth,1000);assert.ok(entry.expanded.found&&!entry.expanded.disabled&&entry.expanded.checkVisibility,'Original language control visible at desktop width');
  await click('#language');
  await driver.call('input.performActions',{context:target.context,actions:[{type:'key',id:'language-keyboard',actions:[
   {type:'keyDown',value:'\uE013'},{type:'keyUp',value:'\uE013'},
   {type:'keyDown',value:'\uE007'},{type:'keyUp',value:'\uE007'}]}]});
  await waitFor(value=>document.getElementById('language').value===value,language,10000);
  entry.changed=await languageInventory();entry.changeEvents=await evaluate(()=>window.reviewLanguageEvents);
  assert.ok(entry.changeEvents.some(e=>e.value===language&&e.trusted),'Actual trusted select change');
 }catch(error){entry.error=String(error);failure=error;}
 try{
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:{width:440,height:900},devicePixelRatio:1});
  entry.restored=await languageInventory();assert.equal(entry.restored.innerWidth,440);assert.equal(entry.restored.innerHeight,900);
  if(!failure)assert.equal(entry.restored.value,language);
 }catch(error){entry.restoreError=String(error);if(!failure)failure=error;}
 if(failure)throw failure;
}
function readiness(node,test){
 const group=!node.speaker?configuration.player.panels.narration:node.character_image?configuration.player.panels.picture:configuration.player.panels.dialogue;
 return {method:'dialogue',args:{node:node.id,caseName:test.name,group,
  hasEntryProfile:!!configuration.transitions.panel_entries?.[group],referenceWidth:binding.captureReadiness.referenceWidth,
  expectedText:test.language==='ja'?node.text:node.translation}};
}
async function capture(suffix,gate=null){
 const before=gate?await waitFor(({method,args})=>{const r=window.reviewCaptureReadiness[method](args);return r.ready?r:null;},gate,20000):null;
 const stateBefore=await snapshot(),requestEpochMilliseconds=Date.now();
 const shot=await driver.call('browsingContext.captureScreenshot',{context:target.context,origin:'viewport',format:{type:'image/jpeg',quality:.9}});
 const bytes=Buffer.from(shot.data,'base64'),file=caseName+'-'+suffix+'.jpg';totalImageBytes+=bytes.length;
 await writeFile(resolve(output,file),bytes);
 const after=gate?await evaluate(({method,args})=>window.reviewCaptureReadiness[method](args),gate):null;
 const observed=await snapshot();
 captures.push({caseName,file,bytes:bytes.length,sha256:sha(bytes),requestEpochMilliseconds,
  beforeReadiness:before,afterReadiness:after,before:stateBefore,observed});
 if(gate){
  assert.ok(after.ready,'Capture remains within real visible readiness');assert.equal(after.node,before.node);
  if(before.hasEntryProfile)assert.equal(before.complete.token,after.complete.token);
  if(gate.method==='title'){assert.equal(before.generation,after.generation);assert.equal(before.startSequence,after.startSequence);}
 }
 assert.ok(totalImageBytes<=plan.maximumCaptureBytes,'Compact image byte budget');
}
async function actor(step,start){
 const display='STORY_DISPLAY_COMMIT '+step.id+' actor '+step.expectedModel;
 await waitTrace(()=>traces.slice(start).includes(display));
 const owner=await waitTrace(()=>parsed('STORY_PANEL_IN_START ',start).filter(r=>r.node===step.id).at(-1));
 const complete=await waitTrace(()=>{
  assert.ok(!parsed('STORY_PANEL_IN_CANCELLED ',start).some(r=>r.group===owner.group&&r.token===owner.token));
  return parsed('STORY_PANEL_IN_COMPLETE ',start).find(r=>r.node===step.id&&r.group===owner.group&&r.token===owner.token);
 });
 const before=await evaluate(()=>window.reviewRenderProbe.snapshot().contexts.find(r=>r.canvas==='actor'));
 assert.ok(before?.attached&&!before.lost);
 const after=await waitFor(({id,draws})=>{
  const r=window.reviewRenderProbe.snapshot().contexts.find(r=>r.canvas==='actor');
  return document.body.dataset.node===id&&r?.attached&&!r.lost&&r.draws>draws+3&&
   document.getElementById('actor').checkVisibility({opacityProperty:true,visibilityProperty:true})&&r;
 },{id:step.id,draws:before.draws});
 const losses=await evaluate(()=>window.reviewRenderProbe.snapshot().losses);
 assert.equal(losses.filter(x=>x.canvas==='actor'||x.attached).length,0);
 return {display,owner,complete,before,after,drawDelta:after.draws-before.draws,rawLosses:losses};
}
async function prepare(test){
 caseName=test.name;stage='normal-saved-HTTP';const startTrace=traces.length;
 await evaluate(({name,test})=>{window.reviewRunName=name;return window.reviewEndingObserver.beginCase(name,test);},{name:caseName,test});
 const response=await evaluate(async({id,revision})=>{
  const reply=await fetch('/api/player/prepare',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({id,baseSha:revision,choices:{}})});
  const raw=await reply.text();
  if(reply.ok){const program=JSON.parse(raw);window.postMessage({type:'stella-player-load',program},location.origin);}
  return {status:reply.status,raw};
 },{id:plan.start,revision:binding.revision});
 const raw=Buffer.from(response.raw),rawSha256=sha(raw),file='normal-http-'+rawSha256+'.json.gz';
 try{await writeFile(resolve(output,file),gzipSync(raw),{flag:'wx'});}
 catch(error){if(error.code!=='EEXIST')throw error;assert.deepEqual(gunzipSync(await readFile(resolve(output,file))),raw);}
 assert.equal(response.status,200,response.raw.slice(0,1200));const program=JSON.parse(response.raw);
 assert.equal(sha(JSON.stringify(program)),preflight.programSha256);assert.equal(program.headSha,binding.revision);
 assert.equal(program.nodes.length,5620);assert.equal(program.nodes.filter(n=>n.scene_id==='scene:10090015').length,53);
 const nodes=plan.steps.map(s=>program.nodes.find(n=>n.id===s.id));assert.ok(nodes.every(Boolean));
 assert.equal(nodes[1].text,plan.languages[1].expectedText);assert.equal(nodes[1].translation,plan.languages[0].expectedText);
 const edges=plan.steps.map(s=>program.edges.find(e=>e.source===s.id&&e.native_transition?.uniq_id===s.native.branch_list[0].transition_list[0].uniq_id));
 for(const[index,edge]of edges.entries()){assert.ok(edge.available);assert.deepEqual(edge.native_transition,plan.steps[index].native.branch_list[0].transition_list[0]);}
 assert.equal(edges.at(-1).flow_action,'section');
 return {name:test.name,language:test.language,startTrace,prepared:{status:200,start:program.start,headSha:program.headSha,
  programSha256:sha(JSON.stringify(program)),rawSha256,gzipFile:file,allNodes:5620,sceneRows:53,before:program.before,nodes,edges},cards:[]};
}
try{
 ({capabilities}=await driver.call('session.new',{capabilities:{}}));const tree=await driver.call('browsingContext.getTree');target={context:tree.contexts[0].context};
 driver.events((event,value)=>{
  if(event==='log.entryAdded'){
   const line=value.text||'';if(value.type==='javascript'||line.startsWith('STORY_PLAYER_ERROR'))errors.push(line);
   if(/^(?:STORY_|STELLA_|MODEL_|PREVIEW_|VOICE_)/.test(line)){
    traces.push(line);const record={sequence:traces.length-1,eventEpochMilliseconds:value.timestamp,observedEpochMilliseconds:Date.now(),line};records.push(record);
    writes.push(appendFile(resolve(output,'events.jsonl'),JSON.stringify(record)+'\n').catch(error=>errors.push(String(error))));
   }
  }
  if(event==='network.responseCompleted'){
   const u=new URL(value.response.url);if(u.origin!==origin)return;
   const record={url:u.href,status:value.response.status,epochMilliseconds:Date.now()};http.push(record);
   if(record.status>=400&&u.pathname!=='/favicon.ico')errors.push('HTTP '+record.status+' '+record.url);
  }
 });
 await driver.call('session.subscribe',{events:['log.entryAdded','network.responseCompleted'],contexts:[target.context]});
 for(const fn of [installEndingObserver,installRenderProbe,installCaptureReadiness])await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:fn.toString()});
 await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:(()=>{
  window.reviewMediaEvents=[];window.reviewLanguageEvents=[];window.reviewRunName='setup';
  document.addEventListener('change',event=>{if(event.target.id==='language')window.reviewLanguageEvents.push({value:event.target.value,trusted:event.isTrusted,epochMilliseconds:Date.now()});},true);
  document.addEventListener('DOMContentLoaded',()=>{
   const video=document.getElementById('movie');
   for(const name of ['loadstart','loadedmetadata','loadeddata','canplay','play','playing','pause','waiting','stalled','ended','seeking','seeked','ratechange','volumechange','timeupdate','error'])
    video.addEventListener(name,()=>window.reviewMediaEvents.push({event:name,caseName:window.reviewRunName,node:document.body.dataset.node,
     epochMilliseconds:Date.now(),performanceMilliseconds:performance.now(),resource:video.currentSrc,
     currentTime:video.currentTime,duration:Number.isFinite(video.duration)?video.duration:null,playbackRate:video.playbackRate,
     seeking:video.seeking,ended:video.ended,paused:video.paused,muted:video.muted,volume:video.volume,
     mozHasAudio:typeof video.mozHasAudio==='boolean'?video.mozHasAudio:null,
     played:Array.from({length:video.played.length},(_,i)=>[video.played.start(i),video.played.end(i)])}));
  },{once:true});
 }).toString()});
 await driver.call('browsingContext.setViewport',{context:target.context,viewport:{width:440,height:900},devicePixelRatio:1});
 await driver.call('browsingContext.navigate',{context:target.context,url:origin+'/player/player.html?assetRevision='+binding.revision,wait:'interactive'});
 await waitFor(()=>window.reviewReady===true);await evaluate(()=>window.reviewEndingObserver.attachClock());
 configuration=await evaluate(async()=>({player:await(await fetch('/player/player_config.json')).json(),transitions:await(await fetch('/player-assets/transitions.json')).json()}));
 assert.equal(await evaluate(()=>document.getElementById('language').value),'zh');assert.equal(await evaluate(()=>document.getElementById('auto').getAttribute('aria-pressed')),'false');
 for(const test of plan.languages){
  caseName=test.name;stage='language-switch-'+test.language+'-before-normal-prepare';
  await setLanguage(test.language);const row=await prepare(test);cases.push(row);
  for(const[index,step]of plan.steps.slice(0,3).entries()){
   stage='card-'+step.scenario;const phase=await waitFor(id=>document.body.dataset.node===id&&['text','ready'].includes(document.body.dataset.phase)&&document.body.dataset.phase,step.id);
   if(phase==='text')await click('#advance');await waitFor(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready',step.id);
   const rendered=await actor(step,row.startTrace);await capture('node-'+step.scenario,readiness(row.prepared.nodes[index],test));
   const state=await snapshot(),layout=parsed('STORY_TEXT_PANEL_LAYOUT ',row.startTrace).filter(x=>x.node===step.id).at(-1);
   assert.equal(state.language,test.language);assert.equal(state.normalClock.previewRate,1);
   if(step.scenario===54){
    const text=test.language==='ja'?row.prepared.nodes[index].text:row.prepared.nodes[index].translation;
    assert.equal(text,test.expectedText);assert.ok(state.text.endsWith(test.expectedText));
    const lines=text.split('\n');assert.deepEqual(lines.map(x=>[...x].filter(c=>c===test.bar).length),[2,4,8]);assert.equal(lines.length,3);assert.ok(lines.every(x=>x.endsWith('。')));
    assert.equal(layout.lineCount,3);assert.equal(rendered.display,'STORY_DISPLAY_COMMIT '+step.id+' actor subaru01');
   }
   row.cards.push({scenario:step.scenario,id:step.id,rendered,layout,state});await click('#advance');
  }
  assert.equal(new Set(row.cards.map(c=>c.rendered.owner.token)).size,3,'Three separate current owned panels');
  stage='natural-door49';const movie=plan.steps[3],title=plan.steps[4];
  const ended=await waitFor(({name,node})=>window.reviewMediaEvents.findLast(e=>e.caseName===name&&e.node===node&&e.event==='ended'),{name:test.name,node:movie.id},30000);
  assert.equal(ended.playbackRate,1);assert.equal(ended.seeking,false);assert.equal(ended.muted,false);assert.equal(ended.volume,1);
  assert.ok(Math.abs(ended.currentTime-ended.duration)<.001);assert.deepEqual(ended.played.length,1);assert.equal(ended.played[0][0],0);assert.ok(Math.abs(ended.played[0][1]-ended.duration)<.001);
  row.movieEnded=ended;await waitFor(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready',movie.id);row.beforeMovieContinue=await snapshot();await click('#advance');
  stage='visible-CLEAR';await capture('CLEAR',{method:'title',args:{node:title.id,caseName:test.name,...{
   referenceWidth:binding.captureReadiness.referenceWidth,stableStart:binding.captureReadiness.titleStableStart,stableEnd:binding.captureReadiness.titleStableEnd}}});
  await waitFor(()=>document.body.dataset.phase==='complete',null,20000);await capture('section-complete');
  row.metadata=await evaluate(async id=>{const r=await fetch('/api/music/'+id);if(!r.ok)throw Error('Music metadata '+r.status);return r.json();},plan.expectedBgm);assert.deepEqual(row.metadata,musicMetadata);
  const decision=await waitTrace(()=>parsed('STORY_NATIVE_INTERVAL_DECISION ',row.startTrace).findLast(x=>x.node===title.id));
  const command=await waitTrace(()=>parsed('STORY_BGM_COMMAND ',row.startTrace).findLast(x=>x.resource===plan.expectedBgm&&x.key===title.id+':'+decision.generation));
  const play=await waitTrace(()=>parsed('STORY_BGM_PLAY ',row.startTrace).findLast(x=>x.resource===plan.expectedBgm));
  const playIndex=traces.findLastIndex((line,index)=>index>=row.startTrace&&line.startsWith('STORY_BGM_PLAY ')&&JSON.parse(line.slice('STORY_BGM_PLAY '.length)).resource===plan.expectedBgm);
  const fadeBegin=await waitTrace(()=>traces.slice(playIndex).filter(x=>x.startsWith('STORY_BGM_FADE_BEGIN ')).map(x=>JSON.parse(x.slice('STORY_BGM_FADE_BEGIN '.length)))[0]);
  const fadeComplete=await waitTrace(()=>parsed('STORY_BGM_FADE_COMPLETE ',row.startTrace).find(x=>x.generation===fadeBegin.generation));
  assert.equal(command.fade,1);assert.equal(command.restart,false);assert.equal(play.samples,musicMetadata.samples);assert.equal(play.sampleRate,musicMetadata.sample_rate);assert.equal(play.start,musicMetadata.loop_start);assert.equal(play.end,musicMetadata.loop_end);assert.equal(play.loop,musicMetadata.loop);assert.ok(fadeComplete.gameElapsedSeconds>=1&&fadeComplete.audioTime>0);
  row.BGM={command,play,fadeBegin,fadeComplete};
  const observed=await evaluate(()=>window.reviewEndingObserver.data()),owned=observed.rows.filter(x=>x.state.caseName===test.name);
  row.actualEnters=owned.filter(x=>x.kind==='product-console'&&x.value.name==='STORY_PLAYER_ENTER').map(x=>x.value.args[0]);assert.deepEqual(row.actualEnters,plan.steps.map(s=>s.id));
  row.transitions=parsed('STORY_PLAYER_TRANSITION ',row.startTrace);assert.equal(row.transitions.length,5);
  for(const[index,t]of row.transitions.entries()){assert.deepEqual(t.native,plan.steps[index].native.branch_list[0].transition_list[0]);if(index<4)assert.equal(t.target,plan.steps[index+1].id);}
  assert.equal(row.transitions.at(-1).action,'section');assert.equal(traces.slice(row.startTrace).filter(x=>x.startsWith('STORY_PLAYER_SECTION_COMPLETE section:1009 ')).length,1);assert.ok(!row.actualEnters.some(x=>x.startsWith(plan.forbiddenEnterPrefix)));
  row.mediaEvents=await evaluate(name=>window.reviewMediaEvents.filter(e=>e.caseName===name),test.name);
  assert.ok(row.mediaEvents.filter(e=>e.node===movie.id).every(e=>e.playbackRate===1&&!e.seeking&&!['seeking','seeked','error'].includes(e.event)));
  row.silentTo46PassiveSamples=owned.filter(x=>[plan.steps[1].id,plan.steps[2].id].includes(x.state.node));
  row.sourceContinuityAcceptance='Pending independent process comparison; event/mutation samples are not full-frame video and stable JPEGs do not prove continuous actor visibility.';
  row.final=await snapshot();assert.equal(observed.droppedRecords,0);assert.deepEqual(observed.observerErrors,[]);assert.deepEqual(errors,[]);console.error('CASE_COMPLETE '+test.name);
 }
 const observer=await evaluate(()=>window.reviewEndingObserver.finish());await Promise.all(writes);
 assert.equal(observer.droppedRecords,0);assert.deepEqual(observer.observerErrors,[]);assert.deepEqual(errors,[]);assert.equal(captures.length,10);
 await save('observer.json',observer);await save('result.json',{browser:capabilities,cases,captures,totalImageBytes,actions,languageControlActions,traces,records,errors,http,languageEvents:await evaluate(()=>window.reviewLanguageEvents),sourceTreeSha256:binding.source.sourceTreeSha256,revision:binding.revision,scope:plan.scope});
 console.log(JSON.stringify({cases:2,captures:10,totalImageBytes,errors}));
}catch(error){
 let state;try{state=await snapshot();}catch(observationError){state={error:String(observationError)};}
 let observer;try{observer=await evaluate(()=>window.reviewEndingObserver.finish());}catch(observationError){observer={error:String(observationError)};}
 await save('failure.json',{stage,caseName,error:String(error),stack:error.stack,state,observer,cases,captures,actions,languageControlActions,traces,records,errors,http});console.error(String(error));process.exitCode=1;
}finally{await Promise.all(writes);await driver.call('session.end').catch(error=>console.error('SESSION_END '+String(error)));driver.close();}
