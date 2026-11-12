async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/target-native-title-entry-runtime-20261112-v1';
  const logs=[],errors=[],responses=[],audio=[],cases=[];
  page.on('console',m=>{const text=m.text();if(text.startsWith('STORY_')||m.type()==='warning'||m.type()==='error')logs.push({wall:Date.now(),type:m.type(),text});});
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('response',r=>{if(/\/(movie|music)\/|title-assets/.test(r.url()))responses.push({wall:Date.now(),url:r.url(),status:r.status()});});
  const cdp=await page.context().newCDPSession(page);
  for(const event of ['contextCreated','contextChanged','contextWillBeDestroyed'])cdp.on('WebAudio.'+event,data=>audio.push({wall:Date.now(),event,data}));
  await cdp.send('WebAudio.enable');
  const player=()=>page.frames().find(f=>f.url().includes('/player/player.html'));
  const waitPhase=async phase=>{
    await page.waitForFunction(()=>window.messageHistory?.some(m=>m.type==='stella-player-state'));
    await player().waitForFunction(p=>document.body.dataset.phase===p,phase,{timeout:25000});
  };
  const language=async value=>page.evaluate(value=>document.querySelector('iframe').contentWindow.postMessage({type:'stella-player-action',action:'language',value},location.origin),value);
  const titleImage=async name=>{
    await waitPhase('title');
    await player().waitForFunction(()=>{
      const e=document.querySelector('.native-title-content');
      return e&&e.isConnected&&+e.style.opacity>.999&&[...e.querySelectorAll('canvas')].every(c=>+c.style.opacity>.999);
    },null,{timeout:12000});
    await player().locator('#viewport').screenshot({path:output+'/'+name+'.png'});
  };
  const ordinary=async({name,scene,node,mode,end=false,lang='zh'})=>{
    const start=Date.now(),from=logs.length;
    await page.goto(`http://127.0.0.1:5192/?scene=${scene}&node=${node}`);
    if(!end){await waitPhase('chart');await language(lang);await page.locator('#advance').click();}
    await titleImage(name);await waitPhase(end?'complete':'ready');
    const local=logs.slice(from),entry=local.filter(r=>r.text.startsWith('STORY_NATIVE_TITLE_ENTRY ')).map(r=>JSON.parse(r.text.slice('STORY_NATIVE_TITLE_ENTRY '.length)));
    if(entry.length!==2||entry[0].stage!=='started'||entry[1].stage!=='completed'||entry[1].mode!==mode||entry[1].gameElapsedMilliseconds<2500)throw Error('Native title lifecycle failed: '+name);
    cases.push({name,start,end:Date.now(),scene,node,mode,entry,viewport:await player().locator('#viewport').boundingBox()});
  };
  try{
    await ordinary({name:'normal-ja',scene:10040053,node:1,mode:'normal',lang:'ja'});
    await ordinary({name:'if-zh',scene:10030005,node:1,mode:'if'});
    await ordinary({name:'baseline-clear',scene:10010001,node:32,mode:'normal',end:true});
    const start=Date.now(),from=logs.length;
    await page.goto('http://127.0.0.1:5192/?scene=10040053&node=49');
    await waitPhase('ready');
    await player().locator('#viewport').screenshot({path:output+'/p29-final-line.png'});
    await player().locator('#viewport').click();
    await titleImage('p29-clear');await waitPhase('complete');
    await player().locator('#viewport').screenshot({path:output+'/p29-completed-chart.png'});
    const local=logs.slice(from),enters=local.filter(r=>r.text.startsWith('STORY_PLAYER_ENTER ')).map(r=>r.text.split(' ')[1]);
    if(JSON.stringify(enters)!==JSON.stringify(['10040053:49','10040053:50','10040053:51']))throw Error('Unexpected P29 suffix route: '+JSON.stringify(enters));
    if(!local.some(r=>r.text.startsWith('STORY_PLAYER_SECTION_COMPLETE section:1004 ')))throw Error('P29 section did not complete');
    const terminal=local.find(r=>r.text.startsWith('STORY_PLAYER_TRANSITION ')&&r.text.includes('"action":"complete"'));
    if(!terminal||!terminal.text.includes('"target":""'))throw Error('P29 terminal completion changed');
    const video=await player().locator('#movie').evaluate(v=>({duration:v.duration,currentTime:v.currentTime,ended:v.ended}));
    if(!video.ended||video.currentTime<video.duration-.05)throw Error('Door movie did not finish');
    cases.push({name:'p29-ending',start,end:Date.now(),enters,video,terminal,viewport:await player().locator('#viewport').boundingBox()});
    if(errors.length||logs.some(r=>r.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Player runtime error');
    return {status:'ordinary_title_entries_and_p29_ending_completed',captureEndWall:Date.now(),cases,logs,errors,responses,audio,previewOverrides:false,audioAuditionPerformed:false};
  }finally{await cdp.detach();}
}
