async page => {
  const logs=[],errors=[],cases=[];
  page.on('console',m=>{const text=m.text();if(text.startsWith('STORY_')||m.type()==='warning'||m.type()==='error')logs.push({wall:Date.now(),type:m.type(),text});});
  page.on('pageerror',e=>errors.push(String(e)));
  const player=()=>page.frames().find(f=>f.url().includes('/player/player.html'));
  const waitPhase=async phase=>{
    await page.waitForFunction(()=>window.messageHistory?.some(m=>m.type==='stella-player-state'));
    await player().waitForFunction(p=>document.body.dataset.phase===p,phase,{timeout:25000});
  };
  const action=async(action,value)=>page.evaluate(({action,value})=>document.querySelector('iframe').contentWindow.postMessage({type:'stella-player-action',action,value},location.origin),{action,value});
  const describe=()=>player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
    cardOpacity:getComputedStyle(document.querySelector('#cardMotion')).opacity,
    backdrop:JSON.parse(document.querySelector('#backdrop').dataset.backgroundGeometry||'null'),
    titleRootPresent:Boolean(document.querySelector('.native-title-content'))}));
  const ordinary=async({name,scene,node,mode,end=false,lang='zh'})=>{
    const start=Date.now(),from=logs.length;
    await page.goto(`http://127.0.0.1:5192/?scene=${scene}&node=${node}`);
    if(!end){await waitPhase('chart');await action('language',lang);await page.locator('#advance').click();}
    await waitPhase('title');const titleStart=await describe();
    await waitPhase(end?'complete':'ready');const final=await describe();
    const local=logs.slice(from),entry=local.filter(r=>r.text.startsWith('STORY_NATIVE_TITLE_ENTRY ')).map(r=>JSON.parse(r.text.slice('STORY_NATIVE_TITLE_ENTRY '.length)));
    if(entry.length!==2||entry[0].stage!=='started'||entry[1].stage!=='completed'||entry[1].mode!==mode||entry[1].gameElapsedMilliseconds<2500)throw Error('Native title lifecycle failed: '+name);
    if(!end&&titleStart.backdrop&&titleStart.backdrop.blur!==0)throw Error('Ordinary title backdrop is blurred');
    if(name==='normal-ja'&&titleStart.backdrop.resource!=='bg/bg031a_stealshop')throw Error('P29 Title1 backing missing');
    if(final.titleRootPresent)throw Error('Title was not removed after completion');
    cases.push({name,start,end:Date.now(),scene,node,mode,entry,titleStart,final,viewport:await player().locator('#viewport').boundingBox()});
  };
  try{
  await ordinary({name:'baseline-clear',scene:10010001,node:32,mode:'normal',end:true});
  const start=Date.now(),from=logs.length;
  await page.goto('http://127.0.0.1:5192/?scene=10040053&node=1');await waitPhase('chart');await page.locator('#advance').click();
  await waitPhase('title');await action('stop');await waitPhase('stopped');
  await page.waitForTimeout(2800);const stopped=await describe();
  const local=logs.slice(from),entry=local.filter(r=>r.text.startsWith('STORY_NATIVE_TITLE_ENTRY ')).map(r=>JSON.parse(r.text.slice('STORY_NATIVE_TITLE_ENTRY '.length)));
  if(stopped.phase!=='stopped'||stopped.titleRootPresent||stopped.backdrop?.blur<=0||entry.filter(e=>e.stage==='cancelled').length!==1||entry.some(e=>e.stage==='completed')||local.some(r=>r.text.startsWith('STORY_PLAYER_ENTER 10040053:2 ')))throw Error('Stop did not release title/backdrop ownership');
  cases.push({name:'stop-during-title',start,end:Date.now(),entry,stopped,viewport:await player().locator('#viewport').boundingBox()});
  if(errors.length||logs.some(r=>r.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Player runtime error');
  return {status:'native_title_baseline_and_stop_completed',cases,logs,errors,previewOverrides:false,inRecordingScreenshots:false};
  }catch(error){return {status:'capture_failed',failure:String(error),cases,logs,errors};}
}
