async page => {
  const logs=[],errors=[],responses=[],events=[];
  page.on('console',m=>{const text=m.text();if(text.startsWith('STORY_')||m.type()==='warning'||m.type()==='error')logs.push({wall:Date.now(),type:m.type(),text});});
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('response',r=>{if(/\/picture\/|\/background\//.test(r.url()))responses.push({url:r.url(),status:r.status()});});
  const player=()=>page.frames().find(f=>f.url().includes('/player/player.html'));
  const ready=async node=>{
    await page.waitForFunction(()=>window.messageHistory?.some(m=>m.type==='stella-player-state'));
    await player().waitForFunction(node=>document.body.dataset.node==='10450056:'+node&&document.body.dataset.phase==='ready',node,{timeout:25000});
    events.push(await player().evaluate(()=>({wall:Date.now(),node:document.body.dataset.node,phase:document.body.dataset.phase,
      picture:{hidden:document.querySelector('#picture').hidden,fit:document.querySelector('#picture').style.objectFit,position:document.querySelector('#picture').style.objectPosition},
      viewport:(()=>{const{x,y,width,height}=document.querySelector('#viewport').getBoundingClientRect();return{x,y,width,height};})()})));
  };
  try{
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=25');await ready(25);
    await player().locator('#viewport').click();await ready(26);await page.waitForTimeout(800);
    await player().locator('#viewport').click();await ready(27);await page.waitForTimeout(800);
    await player().locator('#viewport').click();await ready(28);await page.waitForTimeout(500);
    const layouts=logs.filter(r=>r.text.startsWith('STORY_PICTURE_LAYOUT ')).map(r=>JSON.parse(r.text.slice('STORY_PICTURE_LAYOUT '.length)));
    for(const n of[26,27]){
      const row=layouts.find(r=>r.node==='10450056:'+n);
      if(!row||row.resource!=='ADV_still_006'||row.fit!=='cover'||JSON.stringify(row.naturalSize)!=='[1536,2048]'||row.displayBackground!=='bg/bg001_black')throw Error('Still layout/resource/black plate mismatch at'+n);
    }
    const state=await player().evaluate(()=>({node:document.body.dataset.node,pictureHidden:document.querySelector('#picture').hidden,card:JSON.parse(document.querySelector('#card').dataset.backgroundGeometry||'null')}));
    if(!state.pictureHidden||state.card?.resource!=='bg/bg046c_stealshop')throw Error('CG did not leave for ruined shop');
    if(!responses.some(r=>r.status===200&&r.url.includes('/picture/ADV_still_006')))throw Error('Original still response missing');
    if(errors.length||logs.some(r=>r.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Player runtime error');
    return {status:'ordinary25_26_27_28_still006_completed',events,layouts,state,logs,responses,errors,previewOverrides:false,inRecordingScreenshots:false,userDwellMs:{26:800,27:800,28:500},scriptWaitAdded:false,fxAccepted:false,actingAccepted:false};
  }catch(error){return{status:'capture_failed',failure:String(error),events,logs,responses,errors};}
}
