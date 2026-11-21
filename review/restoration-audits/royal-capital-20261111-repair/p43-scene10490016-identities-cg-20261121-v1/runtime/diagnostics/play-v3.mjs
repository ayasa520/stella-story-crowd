// Drive only the normal saved player controls. Read-only probes count existing
// GL submissions and retain native event ownership; they never supply scene
// state, resource substitutions, clock changes or a replacement program.
import assert from 'node:assert/strict';
import {readFile,writeFile,appendFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import {connect} from '../../stella-p30-firefox-20261120/bidi.mjs';
import {installRenderProbe} from '../../stella-p30-firefox-20261120/render-probe.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const output=process.env.STELLA_REVIEW_OUTPUT;assert.ok(output);
const plan=JSON.parse(await readFile(new URL('capture-plan-v2.json',here),'utf8'));
const binding=JSON.parse(await readFile(new URL('input-binding-v2.json',here),'utf8'));
const offlinePrepare=JSON.parse(await readFile(new URL('normal-prepare-receipt.json',here),'utf8'));
const driver=await connect(process.argv[2]);
const traces=[],records=[],errors=[],http=[],played=[],captures=[],actions=[],eventWrites=[];
let target,stage='connect',capabilities,prepared,panelConfig,totalCaptureBytes=0;
async function save(name,value){await writeFile(resolve(output,name),JSON.stringify(value,null,2)+'\n');}
async function evaluate(fn,arg){
  const result=await driver.call('script.evaluate',{target,awaitPromise:true,
    expression:`(async()=>JSON.stringify(await (${fn})(${JSON.stringify(arg)})))()`});
  if(result.type!=='success')throw Error(result.exceptionDetails?.text||'Firefox evaluation failed');
  return JSON.parse(result.result.value);
}
async function snapshot(){return evaluate(()=>{
  const geometry=id=>{const n=document.getElementById(id);return n.dataset.backgroundGeometry?JSON.parse(n.dataset.backgroundGeometry):null;};
  const picture=document.getElementById('picture'),subtitles=document.getElementById('subtitles');
  return {epochMilliseconds:Date.now(),performanceMilliseconds:performance.now(),body:{...document.body.dataset},
    status:document.getElementById('status').textContent,accessibleText:document.getElementById('accessibleText').textContent,
    cardOpacity:document.getElementById('cardMotion').style.opacity,background:geometry('card'),backdrop:geometry('backdrop'),
    actorVisible:document.getElementById('actor').checkVisibility({opacityProperty:true,visibilityProperty:true}),
    picture:{hidden:picture.hidden,src:picture.currentSrc,naturalWidth:picture.naturalWidth,naturalHeight:picture.naturalHeight,
      presentation:picture.dataset.picturePresentation,objectFit:getComputedStyle(picture).objectFit},
    panel:{opacity:getComputedStyle(subtitles).opacity,translate:getComputedStyle(subtitles).translate,hidden:subtitles.hidden},
    choices:[...document.querySelectorAll('#choices button')].map(n=>({edge:n.dataset.edge,text:n.textContent,
      disabled:n.disabled,selected:n.getAttribute('aria-pressed')})),advanceDisabled:document.getElementById('advance').disabled,
    render:window.reviewRenderProbe.snapshot()};
  });}
async function click(selector){
  const point=await evaluate(selector=>{
    const n=document.querySelector(selector);if(!n||n.disabled||!n.checkVisibility())return null;
    n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();
    return {x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)};
  },selector);assert.ok(point,'Visible enabled normal control '+selector);
  actions.push({selector,before:await snapshot()});
  await driver.call('input.performActions',{context:target.context,actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},
    actions:[{type:'pointerMove',origin:'viewport',...point,duration:0},{type:'pointerDown',button:0},{type:'pointerUp',button:0}]}]});
  actions.at(-1).afterEpochMilliseconds=Date.now();
}
async function waitFor(fn,arg,timeout=45000){
  const end=Date.now()+timeout;
  while(Date.now()<end){
    if(errors.length)throw Error(errors.at(-1));
    const found=await evaluate(fn,arg);if(found)return found;
    const voice=await evaluate(()=>{const n=document.getElementById('voiceContinue');return n&&!n.hidden&&!n.disabled&&n.checkVisibility();});
    if(voice)await click('#voiceContinue');
    await delay(70);
  }
  throw Error('Expected normal player condition timed out: '+stage);
}
function parsed(prefix){return traces.filter(x=>x.startsWith(prefix)).map(x=>JSON.parse(x.slice(prefix.length)));}
async function waitTrace(test,timeout=15000){
  const end=Date.now()+timeout;while(Date.now()<end){if(errors.length)throw Error(errors.at(-1));const found=test();if(found)return found;await delay(50);}
  throw Error('Expected actual event timed out: '+stage);
}
async function stablePanel(step,node){
  const group=!node.speaker?panelConfig.player.panels.narration:node.character_image?panelConfig.player.panels.picture:panelConfig.player.panels.dialogue;
  const profile=panelConfig.transitions.panel_entries?.[group];
  // A panel without an installed entry profile has no animation token. For
  // profiled panels, correlate the exact node/group/token instead of using
  // a nearby ENTER or wall-clock delay as proof of entry completion.
  if(!profile){assert.equal(parsed('STORY_PANEL_IN_START ').filter(x=>x.node===step.id).length,0);return {group,profile:null};}
  const owner=await waitTrace(()=>parsed('STORY_PANEL_IN_START ').filter(x=>x.node===step.id).at(-1));
  assert.equal(owner.group,group);
  const complete=await waitTrace(()=>{
    const cancelled=parsed('STORY_PANEL_IN_CANCELLED ').find(x=>x.group===group&&x.token===owner.token);
    if(cancelled)throw Error('Owned panel cancelled before stable capture '+JSON.stringify({node:step.id,owner,cancelled}));
    return parsed('STORY_PANEL_IN_COMPLETE ').find(x=>x.node===step.id&&x.group===group&&x.token===owner.token);
  });
  return {group,profile,owner,complete};
}
async function capture(step){
  const shot=await driver.call('browsingContext.captureScreenshot',{context:target.context,origin:'viewport',
    format:{type:'image/jpeg',quality:plan.captureFormat.quality}});
  const bytes=Buffer.from(shot.data,'base64'),file='scene16-'+String(step.scenario).padStart(2,'0')+'.jpg';
  totalCaptureBytes+=bytes.length;
  await writeFile(resolve(output,file),bytes);
  captures.push({scenario:step.scenario,file,bytes:bytes.length,model:step.expectedModel,picture:step.expectedPicture,
    source:step.source,observed:await snapshot()});
  assert.ok(totalCaptureBytes<=plan.captureFormat.maximumCaptureBytes,'Compact capture byte budget exceeded');
}
try{
  ({capabilities}=await driver.call('session.new',{capabilities:{}}));
  const {contexts}=await driver.call('browsingContext.getTree');target={context:contexts[0].context};
  driver.events((event,value)=>{
    if(event==='log.entryAdded'){
      const line=value.text||'';
      if(value.type==='javascript'||line.startsWith('STORY_PLAYER_ERROR'))errors.push(line);
      if(/^(?:STORY_|STELLA_|MODEL_|PREVIEW_|VOICE_)/.test(line)){
        traces.push(line);const row={sequence:traces.length-1,eventEpochMilliseconds:value.timestamp,observedEpochMilliseconds:Date.now(),line};
        records.push(row);
        eventWrites.push(appendFile(resolve(output,'events.jsonl'),JSON.stringify(row)+'\n').catch(error=>errors.push(String(error))));
      }
    }
    if(event==='network.responseCompleted'){
      const u=new URL(value.response.url);
      if(u.origin===origin){const row={url:u.href,status:value.response.status,mimeType:value.response.mimeType,observedEpochMilliseconds:Date.now()};
        http.push(row);if(row.status>=400&&u.pathname!=='/favicon.ico')errors.push('HTTP '+row.status+' '+row.url);}
    }
  });
  await driver.call('session.subscribe',{events:['log.entryAdded','network.responseCompleted'],contexts:[target.context]});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:installRenderProbe.toString()});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:(()=>{
    window.reviewTrustedInputs=[];
    window.addEventListener('message',event=>{
      if(event.source===window&&event.origin===location.origin&&event.data?.type==='stella-player-ready')window.reviewReady=true;
    });
    document.addEventListener('click',event=>{
      const n=event.target.closest('button');if(n)window.reviewTrustedInputs.push({button:n.id,edge:n.dataset.edge,
        trusted:event.isTrusted,node:document.body.dataset.node,phase:document.body.dataset.phase,
        epochMilliseconds:Date.now(),performanceMilliseconds:performance.now()});
    },true);
  }).toString()});
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:plan.captureFormat.viewport,devicePixelRatio:1});
  stage='normal-setup';
  await driver.call('browsingContext.navigate',{context:target.context,url:origin+'/player/player.html?assetRevision='+binding.revision,wait:'interactive'});
  await waitFor(()=>window.reviewReady===true);
  assert.equal(await evaluate(()=>document.getElementById('language').value),'zh');
  panelConfig=await evaluate(async()=>({player:await(await fetch('/player/player_config.json')).json(),
    transitions:await(await fetch('/player-assets/transitions.json')).json()}));
  stage='normal-saved-prepare';
  prepared=await evaluate(async({id,revision})=>{
    const response=await fetch('/api/player/prepare',{method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({id,baseSha:revision,choices:{}})});
    if(!response.ok)throw Error('Normal prepare '+response.status+' '+await response.text());
    const program=await response.json();
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(program)));
    const programSha256=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
    const result={status:response.status,start:program.start,headSha:program.headSha,programSha256,
      semantics:{illustration_background:program.semantics.illustration_background},
      nodes:program.nodes.filter(n=>n.id.startsWith('node:10490016:')),
      edges:program.edges.filter(e=>e.source.startsWith('node:10490016:'))};
    window.postMessage({type:'stella-player-load',program},location.origin);
    return result;
  },{id:plan.start,revision:binding.revision});
  assert.equal(prepared.programSha256,offlinePrepare.programSha256);
  assert.equal(prepared.start,plan.start);assert.equal(prepared.headSha,binding.revision);
  assert.equal(prepared.nodes.length,36);
  for(const step of plan.steps){
    const node=prepared.nodes.find(n=>n.id===step.id);assert.ok(node);
    assert.equal(node.model,step.expectedModel);assert.equal(node.character_image,step.expectedPicture);
    const edge=prepared.edges.find(e=>e.source===step.id&&e.native_transition?.uniq_id===step.expectedTransition.uniq_id);
    assert.ok(edge);assert.deepEqual(edge.native_transition,step.expectedTransition);assert.equal(edge.available,true);
  }
  const terminal=prepared.edges.find(e=>e.source===plan.steps.at(-1).id);assert.equal(terminal.target,'node:10490017:1049001700001');
  for(const [index,step] of plan.steps.entries()){
    stage='node-'+step.scenario;
    await waitTrace(()=>traces.find(x=>x.startsWith('STORY_PLAYER_ENTER '+step.id+' ')),45000);
    const node=prepared.nodes.find(n=>n.id===step.id);
    if(node.kind==='title'){
      const decision=await waitTrace(()=>parsed('STORY_NATIVE_INTERVAL_DECISION ').find(x=>x.node===step.id));
      if(decision.show){await waitFor(id=>document.body.dataset.node===id&&document.body.dataset.phase==='chart',step.id);await click('#advance');}
      played.push({scenario:step.scenario,id:step.id,titleDecision:decision,observed:await snapshot()});
      continue;
    }
    const phase=await waitFor(id=>document.body.dataset.node===id&&['text','ready','choice'].includes(document.body.dataset.phase)&&document.body.dataset.phase,step.id);
    if(phase==='text')await click('#advance');
    const choice=plan.recordedChoices.find(c=>c.scenarioId===step.scenario);
    const wanted=choice?'choice':'ready';
    await waitFor(({id,wanted})=>document.body.dataset.node===id&&document.body.dataset.phase===wanted,{id:step.id,wanted});
    const panel=await stablePanel(step,node);
    let render=null,pictureLayout=null;
    if(step.expectedModel){
      const display=traces.filter(x=>x.startsWith('STORY_DISPLAY_COMMIT '+step.id+' ')).at(-1);
      assert.equal(display,'STORY_DISPLAY_COMMIT '+step.id+' actor '+step.expectedModel);
      const before=await evaluate(()=>window.reviewRenderProbe.snapshot().contexts.find(x=>x.canvas==='actor'));
      assert.ok(before?.attached&&!before.lost);
      render=await waitFor(before=>{
        const r=window.reviewRenderProbe.snapshot().contexts.find(x=>x.canvas==='actor');
        return r?.attached&&!r.lost&&r.draws>before+3&&document.getElementById('actor').checkVisibility({opacityProperty:true,visibilityProperty:true})&&r;
      },before.draws,10000);
    }
    if(step.expectedPicture){
      assert.ok(traces.some(x=>x.startsWith('STORY_DISPLAY_COMMIT '+step.id+' picture ')));
      pictureLayout=await waitTrace(()=>parsed('STORY_PICTURE_LAYOUT ').find(x=>x.node===step.id));
      assert.equal(pictureLayout.resource,'ADV_pic_103006');assert.deepEqual(pictureLayout.naturalSize,[1080,1080]);
      assert.equal(pictureLayout.displayBackground,prepared.semantics.illustration_background);
      assert.equal(pictureLayout.fit,'contain');assert.equal(node.speaker,'ラインハルト');
    }
    const state=await snapshot();
    assert.equal(state.body.node,step.id);
    // Keep every raw loss, including unnamed, unattached setup contexts from
    // Pixi's support test. Any actor loss fails even after detachment; any
    // other context lost while attached also fails. Actor draw/liveness gates
    // above remain unchanged and cannot be satisfied by a scratch context.
    assert.equal(state.render.losses.filter(x=>x.canvas==='actor'||x.attached).length,0);
    if(step.scenario===17){
      assert.equal(state.picture.hidden,false);assert.equal(state.picture.naturalWidth,1080);assert.equal(state.picture.naturalHeight,1080);
      assert.equal(state.background.resource,'bg/bg001_black');assert.equal(state.backdrop.resource,'bg/bg001_black');
      assert.ok(state.accessibleText.includes(step.native.msg_text));assert.equal(state.panel.hidden,false);
    }
    if(step.scenario===18){assert.equal(state.picture.hidden,true);assert.equal(state.background.resource,'bg/bg031c_stealshop');}
    const choices=prepared.edges.filter(e=>e.source===step.id&&e.kind==='choice');
    if(choice){
      const locked=plan.lockedUnrecordedBranches.find(c=>c.scenarioId===step.scenario);
      const unknown=choices.find(e=>e.id.endsWith(':'+locked.branchId));
      assert.equal(unknown.available,false);assert.equal(unknown.state,'missing');assert.equal(unknown.target,'');
      assert.ok(state.choices.find(c=>c.edge===unknown.id)?.text.includes('未恢复'));
      assert.equal(state.advanceDisabled,true,'No default choice confirmation');
    }
    if(step.capture)await capture(step);
    played.push({scenario:step.scenario,id:step.id,model:step.expectedModel,picture:step.expectedPicture,
      panel,render,pictureLayout,choices,state});
    if(index===plan.steps.length-1)break; // Deliberately never execute 36/361.
    if(choice){const edge=choices.find(e=>e.id.endsWith(':'+choice.branchId));assert.ok(edge?.available);
      await click('#choices button[data-edge='+JSON.stringify(edge.id)+']');
      await waitFor(()=>document.body.dataset.phase==='choice'&&!document.getElementById('advance').disabled);
    }
    await click('#advance');
    if(played.length%5===0)console.error('PLAYED '+played.length+'/36');
  }
  const enters=traces.filter(x=>x.startsWith('STORY_PLAYER_ENTER ')).map(x=>x.split(' ')[1]);
  assert.deepEqual(enters,plan.steps.map(s=>s.id));
  const transitions=parsed('STORY_PLAYER_TRANSITION ');
  assert.equal(transitions.length,35);assert.ok(!transitions.some(e=>e.edge===terminal.id));
  assert.equal(played.length,36);assert.equal(captures.length,32);assert.deepEqual(errors,[]);
  assert.equal(captures.filter(c=>c.model).length,31);
  const trustedInputs=await evaluate(()=>window.reviewTrustedInputs);assert.ok(trustedInputs.every(i=>i.trusted));
  const finalState=await snapshot();assert.equal(finalState.body.node,plan.steps.at(-1).id);assert.equal(finalState.body.phase,'ready');
  await save('result.json',{browser:capabilities.browserName,version:capabilities.browserVersion,prepared,played,captures,
    totalCaptureBytes,enters,transitions,terminal:{edge:terminal,executed:false,destinationEntered:false},
    finalState,actions,trustedInputs,panelConfig,traces,records,errors,http,
    scope:plan.acceptanceScope,sourceTreeSha256:binding.source.sourceTreeSha256,revision:binding.revision});
  console.log(JSON.stringify({entered:36,internalTransitions:35,actors:31,pictures:1,captures:32,totalCaptureBytes,
    terminalExecuted:false,destinationEntered:false,errors}));
}catch(error){
  let state;try{state=await snapshot();}catch(e){state={observationFailure:String(e)};}
  await save('failure.json',{stage,error:String(error),stack:error.stack,prepared,played,captures,totalCaptureBytes,state,traces,records,errors,http,actions});
  console.error(JSON.stringify({stage,error:String(error),played:played.length,captures:captures.length}));process.exitCode=1;
}finally{
  await Promise.all(eventWrites);
  await driver.call('session.end').catch(error=>console.error('SESSION_END '+String(error)));driver.close();
}
