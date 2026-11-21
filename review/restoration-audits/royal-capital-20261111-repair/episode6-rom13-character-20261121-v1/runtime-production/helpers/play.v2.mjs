// Ordinary saved-player input only. The complete program is returned by the
// real API and passed unchanged to its existing load protocol. Passive probes
// observe display ownership and GL submissions; they supply no actor, route,
// initial state, background, animation clock or replacement renderer.
import assert from 'node:assert/strict';
import {readFile,writeFile,appendFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {connect} from '../../stella-p30-firefox-20261120/bidi.mjs';
import {installRenderProbe} from '../../stella-p30-firefox-20261120/render-probe.mjs';
const here=new URL('./',import.meta.url),origin='http://127.0.0.1:5198';
const output=process.env.STELLA_REVIEW_OUTPUT;assert.ok(output);
const load=async name=>JSON.parse(await readFile(new URL(name,here),'utf8'));
const plan=await load('capture-plan.json'),binding=await load('input-binding.json');
const offlinePrepare=await load('normal-prepare-receipt.json'),route=await load('normal-prepare-route-check.json');
assert.equal(offlinePrepare.status,200);
const driver=await connect(process.argv[2]);
const traces=[],records=[],errors=[],http=[],played=[],captures=[],actions=[],eventWrites=[];
let target,stage='connect',capabilities,prepared,panelConfig,totalCaptureBytes=0;
const save=async(name,value)=>writeFile(resolve(output,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
async function evaluate(fn,arg){
  const reply=await driver.call('script.evaluate',{target,awaitPromise:true,
    expression:`(async()=>JSON.stringify(await (${fn})(${JSON.stringify(arg)})))()`});
  if(reply.type!=='success')throw Error(reply.exceptionDetails?.text||'Firefox evaluation failed');
  return reply.result.type==='undefined'?null:JSON.parse(reply.result.value);
}
async function snapshot(){return evaluate(()=>{
  const geometry=id=>{const e=document.getElementById(id);return e.dataset.backgroundGeometry?JSON.parse(e.dataset.backgroundGeometry):null;};
  const panel=document.getElementById('subtitles'),actor=document.getElementById('actor'),quote=document.getElementById('choiceCanvas');
  return {epochMilliseconds:Date.now(),performanceMilliseconds:performance.now(),body:{...document.body.dataset},
    status:document.getElementById('status').textContent,accessibleText:document.getElementById('accessibleText').textContent,
    background:geometry('card'),backdrop:geometry('backdrop'),
    choiceGeometry:document.getElementById('viewport').dataset.choiceGeometry||null,
    actor:{visible:actor.checkVisibility({opacityProperty:true,visibilityProperty:true}),width:actor.width,height:actor.height},
    pictureHidden:document.getElementById('picture').hidden,
    card:{opacity:getComputedStyle(document.getElementById('cardMotion')).opacity},
    panel:{hidden:panel.hidden,opacity:getComputedStyle(panel).opacity,translate:getComputedStyle(panel).translate},
    choiceSurface:{hidden:quote.hidden,visible:quote.checkVisibility({opacityProperty:true,visibilityProperty:true}),
      opacity:getComputedStyle(quote).opacity,width:quote.width,height:quote.height},
    choices:[...document.querySelectorAll('#choices button')].map(e=>({edge:e.dataset.edge,text:e.textContent,
      disabled:e.disabled,selected:e.getAttribute('aria-pressed')})),advanceDisabled:document.getElementById('advance').disabled,
    render:window.reviewRenderProbe.snapshot()};
});}
async function click(selector){
  const point=await evaluate(selector=>{
    const e=document.querySelector(selector);if(!e||e.disabled||!e.checkVisibility())return null;
    e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
    return {x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)};
  },selector);assert.ok(point,'Visible enabled ordinary control '+selector);
  actions.push({selector,before:await snapshot()});
  await driver.call('input.performActions',{context:target.context,actions:[{type:'pointer',id:'mouse',parameters:{pointerType:'mouse'},
    actions:[{type:'pointerMove',origin:'viewport',...point,duration:0},{type:'pointerDown',button:0},{type:'pointerUp',button:0}]}]});
  actions.at(-1).afterEpochMilliseconds=Date.now();
}
async function waitFor(fn,arg,timeout=45000){
  const end=Date.now()+timeout;
  while(Date.now()<end){
    if(errors.length)throw Error(errors.at(-1));
    const value=await evaluate(fn,arg);if(value)return value;
    const voice=await evaluate(()=>{const e=document.getElementById('voiceContinue');return e&&!e.hidden&&!e.disabled&&e.checkVisibility();});
    if(voice)await click('#voiceContinue');
    await delay(70);
  }
  throw Error('Ordinary player condition timed out at '+stage);
}
function parsed(prefix){return traces.filter(line=>line.startsWith(prefix)).map(line=>JSON.parse(line.slice(prefix.length)));}
async function waitTrace(test,timeout=15000){
  const end=Date.now()+timeout;
  while(Date.now()<end){if(errors.length)throw Error(errors.at(-1));const value=test();if(value)return value;await delay(50);}
  throw Error('Actual player event timed out at '+stage);
}
async function panelReady(step,node){
  const group=!node.speaker?panelConfig.player.panels.narration:node.character_image?panelConfig.player.panels.picture:panelConfig.player.panels.dialogue;
  const profile=panelConfig.transitions.panel_entries?.[group];
  if(!profile){assert.equal(parsed('STORY_PANEL_IN_START ').filter(e=>e.node===step.id).length,0);return {group,profile:null};}
  // Match the owning node/group/token rather than treating ENTER, ready phase
  // or an arbitrary elapsed delay as evidence that its panel became visible.
  const owner=await waitTrace(()=>parsed('STORY_PANEL_IN_START ').filter(e=>e.node===step.id).at(-1));
  assert.equal(owner.group,group);
  const complete=await waitTrace(()=>{
    assert.ok(!parsed('STORY_PANEL_IN_CANCELLED ').some(e=>e.group===group&&e.token===owner.token),'Owned panel cancelled');
    return parsed('STORY_PANEL_IN_COMPLETE ').find(e=>e.node===step.id&&e.group===group&&e.token===owner.token);
  });
  return {group,profile,owner,complete};
}
async function actorReady(step){
  assert.equal(traces.filter(e=>e.startsWith('STORY_DISPLAY_COMMIT '+step.id+' ')).at(-1),
    'STORY_DISPLAY_COMMIT '+step.id+' actor '+step.expectedModel);
  const before=await evaluate(()=>window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor'));
  assert.ok(before?.attached&&!before.lost);
  // Positive new draw submissions belong to the attached actor canvas. A
  // stale Subaru screenshot, an ENTER event or a scratch GL context cannot
  // satisfy Rom's gate. Actual pixels are reviewed independently after exit.
  return waitFor(draws=>{
    const e=window.reviewRenderProbe.snapshot().contexts.find(e=>e.canvas==='actor');
    return e?.attached&&!e.lost&&e.draws>draws+3&&document.getElementById('actor')
      .checkVisibility({opacityProperty:true,visibilityProperty:true})&&e;
  },before.draws,10000);
}
async function capture(step){
  assert.ok(captures.length<4,'At most four original JPEGs');
  const before=await snapshot();
  const shot=await driver.call('browsingContext.captureScreenshot',{context:target.context,origin:'viewport',
    format:{type:'image/jpeg',quality:plan.captureFormat.quality}});
  const bytes=Buffer.from(shot.data,'base64'),file='episode6-rom13-'+step.scenario+'.jpg';
  totalCaptureBytes+=bytes.length;assert.ok(totalCaptureBytes<=plan.captureFormat.maximumCaptureBytes);
  await writeFile(resolve(output,file),bytes,{flag:'wx'});
  const after=await snapshot();assert.equal(before.body.node,step.id);assert.equal(after.body.node,step.id);
  captures.push({scenario:step.scenario,file,bytes:bytes.length,
    sha256:createHash('sha256').update(bytes).digest('hex'),model:step.expectedModel,before,after});
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
        records.push(row);eventWrites.push(appendFile(resolve(output,'events.jsonl'),JSON.stringify(row)+'\n')
          .catch(error=>errors.push(String(error))));
      }
    }
    if(event==='network.responseCompleted'){
      const url=new URL(value.response.url);
      if(url.origin===origin){const row={url:url.href,status:value.response.status,mimeType:value.response.mimeType,
        observedEpochMilliseconds:Date.now()};http.push(row);
        if(row.status>=400&&url.pathname!=='/favicon.ico')errors.push('HTTP '+row.status+' '+row.url);}
    }
  });
  await driver.call('session.subscribe',{events:['log.entryAdded','network.responseCompleted'],contexts:[target.context]});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:installRenderProbe.toString()});
  await driver.call('script.addPreloadScript',{contexts:[target.context],functionDeclaration:(()=>{
    window.reviewTrustedInputs=[];
    window.addEventListener('message',event=>{
      if(event.source===window&&event.origin===location.origin&&event.data?.type==='stella-player-ready')window.reviewReady=true;
    });
    document.addEventListener('click',event=>{const e=event.target.closest('button');if(e)window.reviewTrustedInputs.push({
      button:e.id,edge:e.dataset.edge,trusted:event.isTrusted,node:document.body.dataset.node,phase:document.body.dataset.phase,
      epochMilliseconds:Date.now(),performanceMilliseconds:performance.now()});},true);
  }).toString()});
  await driver.call('browsingContext.setViewport',{context:target.context,viewport:plan.captureFormat.viewport,devicePixelRatio:1});
  stage='normal-setup';
  await driver.call('browsingContext.navigate',{context:target.context,url:origin+'/player/player.html?assetRevision='+binding.revision,wait:'interactive'});
  await waitFor(()=>window.reviewReady===true);
  assert.equal(await evaluate(()=>document.getElementById('language').value),'zh');
  panelConfig=await evaluate(async()=>({player:await(await fetch('/player/player_config.json')).json(),
    transitions:await(await fetch('/player-assets/transitions.json')).json()}));
  stage='ordinary-saved-prepare';
  const actual=await evaluate(async({id,revision,expectedProgramSha256})=>{
    const response=await fetch('/api/player/prepare',{method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({id,baseSha:revision,choices:{}})});
    const raw=await response.text();
    if(!response.ok)return {status:response.status,raw};
    const program=JSON.parse(raw),digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(program)));
    const programSha256=[...new Uint8Array(digest)].map(e=>e.toString(16).padStart(2,'0')).join('');
    if(programSha256!==expectedProgramSha256)return {status:response.status,raw,programSha256,loaded:false};
    // Existing player protocol receives the complete, unmodified API object.
    window.postMessage({type:'stella-player-load',program},location.origin);
    return {status:response.status,raw,programSha256,loaded:true};
  },{id:plan.start,revision:binding.revision,expectedProgramSha256:offlinePrepare.programSha256});
  await writeFile(resolve(output,'normal-http-prepare.json.gz'),gzipSync(actual.raw),{flag:'wx'});
  assert.equal(actual.status,200);assert.equal(actual.loaded,true);assert.equal(actual.programSha256,offlinePrepare.programSha256);
  prepared=JSON.parse(actual.raw);assert.equal(prepared.start,plan.start);assert.equal(prepared.headSha,binding.revision);
  assert.equal(prepared.nodes.length,plan.allLibraryNodes);
  for(const [index,step]of plan.steps.entries()){
    stage='node-'+step.scenario;
    await waitTrace(()=>traces.find(line=>line.startsWith('STORY_PLAYER_ENTER '+step.id+' ')),45000);
    const node=prepared.nodes.find(e=>e.id===step.id);assert.equal(node.model,step.expectedModel);
    // Let the ordinary typewriter complete naturally. Sampling phase=text and
    // later clicking across asynchronous point/snapshot/BiDi calls could race
    // natural ready and accidentally dispatch the node's outgoing transition.
    // No Advance input is used to finish text, including the terminal14 card.
    const wanted=step.scenario===13?'choice':'ready';
    await waitFor(({id,wanted})=>document.body.dataset.node===id&&document.body.dataset.phase===wanted,{id:step.id,wanted});
    const panel=await panelReady(step,node);
    const visible=await waitFor(id=>{
      const card=document.getElementById('cardMotion'),panel=document.getElementById('subtitles'),a=getComputedStyle(card),p=getComputedStyle(panel);
      return document.body.dataset.node===id&&Number(a.opacity)>=.99&&Number(p.opacity)>=.99&&p.translate==='none'&&
        card.checkVisibility({opacityProperty:true,visibilityProperty:true})&&panel.checkVisibility({opacityProperty:true,visibilityProperty:true})&&
        {cardAlpha:a.opacity,panelAlpha:p.opacity,panelTranslate:p.translate,epochMilliseconds:Date.now()};
    },step.id);
    let render=await actorReady(step);
    const scriptBackground=await waitTrace(()=>parsed('STORY_SCRIPT_BACKGROUND ').filter(e=>e.node===step.id).at(-1));
    const expectedBG=route.nodes.find(e=>e.node.id===step.id).expectedEffectiveBackground;
    assert.equal(scriptBackground.effective,expectedBG);
    let state=await snapshot();assert.equal(state.background?.resource,expectedBG);assert.equal(state.backdrop?.resource,expectedBG);
    assert.equal(state.pictureHidden,true);assert.equal(state.actor.visible,true);
    assert.ok(state.accessibleText.includes(step.native.msg_text));
    assert.equal(state.render.losses.filter(e=>e.canvas==='actor'||e.attached).length,0);
    let selected=null;
    if(step.scenario===13){
      const unknown=state.choices.find(e=>e.edge===route.unknown.id);assert.ok(unknown?.text.includes('未恢复'));
      assert.equal(state.advanceDisabled,true,'No default choice confirmation');
      selected=route.edges[index];assert.equal(selected.label_translation,'零食？');assert.equal(selected.available,true);
      await click('#choices button[data-edge='+JSON.stringify(selected.id)+']');
      await waitFor(edge=>document.body.dataset.phase==='choice'&&!document.getElementById('advance').disabled&&
        [...document.querySelectorAll('#choices button')].some(e=>e.dataset.edge===edge&&e.getAttribute('aria-pressed')==='true'),selected.id);
      const quote=await waitTrace(()=>parsed('STORY_CHOICE_QUOTE ').filter(e=>e.edge===selected.id).at(-1));
      assert.equal(quote.language,'zh');
      // Read the normal CardTouch endpoint rather than sleeping for a guessed
      // duration. The choice crop/portrait/balloon can still animate after the
      // click and quote log; their settled capture needs the actual touch=1.
      const choiceGeometry=await waitFor(()=>{
        const raw=document.getElementById('viewport').dataset.choiceGeometry;
        const value=raw&&JSON.parse(raw);
        return value?.pressed&&value.touch===1&&value;
      });
      render=await actorReady(step);state=await snapshot();
      assert.equal(state.body.node,step.id);assert.equal(state.body.phase,'choice');
      assert.ok(state.accessibleText.includes(step.native.branch_list.find(e=>e.branch_id===132).msg_quote));
      assert.equal(state.choiceSurface.visible,true);
      // The quote canvas may contain Subaru's presentation portrait while the
      // separately committed, drawing large-stage actor remains Rom.
      selected={edge:selected,quote,choiceGeometry,state};
    }
    await capture(step);
    played.push({scenario:step.scenario,id:step.id,model:step.expectedModel,panel,visible,render,scriptBackground,state,selected});
    console.error('PLAYED '+played.length+'/4');
    // Terminal14 is observation-only. Its ready phase must never be passed to
    // the asynchronous click path:141 would enter the explicitly excluded15.
    if(step.scenario===14){assert.equal(index,3);break;}
    // Only a captured11/12/13 card may dispatch its saved outgoing transition.
    assert.ok([11,12,13].includes(step.scenario));
    assert.equal(captures.at(-1)?.scenario,step.scenario);
    await click('#advance');
  }
  const enters=traces.filter(line=>line.startsWith('STORY_PLAYER_ENTER ')).map(line=>line.split(' ')[1]);
  assert.deepEqual(enters,plan.steps.map(e=>e.id));
  const transitions=parsed('STORY_PLAYER_TRANSITION ');assert.equal(transitions.length,3);
  for(const [index,event]of transitions.entries()){
    assert.equal(event.edge,route.edges[index].id);assert.equal(event.target,plan.steps[index+1].id);
    assert.deepEqual(event.native,plan.steps[index].expectedTransition);
  }
  assert.equal(played.length,4);assert.equal(captures.length,4);assert.deepEqual(errors,[]);
  const trustedInputs=await evaluate(()=>window.reviewTrustedInputs);assert.ok(trustedInputs.every(e=>e.trusted));
  const chosen=trustedInputs.filter(e=>e.edge);assert.deepEqual(chosen.map(e=>e.edge),[route.edges[2].id]);
  const finalState=await snapshot();assert.equal(finalState.body.node,plan.steps[3].id);assert.equal(finalState.body.phase,'ready');
  const providerEvents=(await readFile(resolve(output,'provider-events.jsonl'),'utf8')).trim().split('\n').map(e=>JSON.parse(e));
  const modelDelivery={};
  for(const model of ['rom01','subaru01']){
    const members=providerEvents.filter(e=>new RegExp('^assets/(?:preview/)?models/'+model+'/').test(e.relative));
    const definition=members.find(e=>e.relative.endsWith('/ac.model3.json'));
    const moc=members.find(e=>e.relative.endsWith('.moc3'));
    const texture=members.find(e=>e.relative.includes('/textures/'));
    assert.ok(definition&&moc&&texture,'Actual saved definition/MOC/texture delivery '+model);
    modelDelivery[model]={definition,moc,texture,members};
  }
  await save('provider-proof.json',{modelDelivery,controller:providerEvents.filter(e=>e.relative==='assets/player/animation.json')});
  await save('image-manifest.json',{format:'original-browser-viewport-jpeg',captures:captures.map(({scenario,file,bytes,sha256,model})=>
    ({scenario,file,bytes,sha256,model})),count:4,totalCaptureBytes,requiresIndependentClosureBeforeReview:true});
  await save('result.json',{browser:capabilities.browserName,version:capabilities.browserVersion,
    prepared:{start:prepared.start,headSha:prepared.headSha,programSha256:actual.programSha256,before:prepared.before},
    played,captures,totalCaptureBytes,enters,transitions,finalState,actions,trustedInputs,panelConfig,traces,records,errors,http,modelDelivery,
    terminal:{edge:route.edges[3],executed:false,destinationEntered:false},scope:plan.acceptanceScope,revision:binding.revision});
  console.log(JSON.stringify({entered:4,internalTransitions:3,captures:4,totalCaptureBytes,stop14Ready:true,errors}));
}catch(error){
  let state;try{state=await snapshot();}catch(e){state={observationFailure:String(e)};}
  await save('failure.json',{stage,error:String(error),stack:error.stack,played,captures,totalCaptureBytes,state,traces,records,errors,http,actions});
  console.error(JSON.stringify({stage,error:String(error),played:played.length,captures:captures.length}));process.exitCode=1;
}finally{
  await Promise.all(eventWrites);await driver.call('session.end').catch(error=>console.error('SESSION_END '+String(error)));driver.close();
}
