async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/target-native-title-runtime-20261112-v1';
  const logs=[],errors=[],responses=[],cases=[];
  page.on('console',message=>{const text=message.text();if(/^(STORY_NATIVE_TITLE_LAYOUT|STORY_PLAYER_TITLE|STORY_PLAYER_ERROR|STORY_PLAYER_SECTION_COMPLETE) /.test(text))logs.push(text);});
  page.on('pageerror',error=>errors.push(String(error)));
  page.on('response',response=>{if(response.url().includes('/title-assets/')||response.url().endsWith('/native-title.json'))responses.push({url:response.url(),status:response.status()});});
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  const waitPhase=async phase=>{
    await page.waitForFunction(()=>Boolean(document.querySelector('iframe')));
    await page.waitForFunction(()=>window.messageHistory?.some(m=>m.type==='stella-player-state'));
    await player().waitForFunction(phase=>document.body.dataset.phase===phase,phase,{timeout:25000});
  };
  const capture=async({name,scene,node,language,mode,end=false})=>{
    await page.goto(`http://127.0.0.1:5192/?scene=${scene}&node=${node}`);
    if(!end){
      await waitPhase('chart');
      await player().locator('#language').selectOption(language);
      await page.locator('#advance').click();
    }
    await waitPhase('title');
    const frame=player();
    await frame.locator('#viewport').screenshot({path:output+'/'+name+'.png'});
    const layout=logs.filter(text=>text.startsWith('STORY_NATIVE_TITLE_LAYOUT ')).map(text=>JSON.parse(text.slice('STORY_NATIVE_TITLE_LAYOUT '.length))).at(-1);
    if(layout.mode!==mode||layout.nativeAnimationPlayed!==false)throw Error('Wrong native title mode or unsupported animation claim: '+name);
    cases.push({name,scene,node,language,layout,previewOverrides:false});
    if(end){
      await waitPhase('complete');
    }else{
      await waitPhase('ready');
      if(name==='normal-zh')await frame.locator('#viewport').screenshot({path:output+'/normal-next-dialogue.png'});
    }
  };
  await capture({name:'normal-zh',scene:10040053,node:1,language:'zh',mode:'normal'});
  await capture({name:'normal-ja',scene:10040053,node:1,language:'ja',mode:'normal'});
  await capture({name:'if-zh',scene:10030005,node:1,language:'zh',mode:'if'});
  await capture({name:'clear-zh',scene:10010001,node:32,language:'zh',mode:'normal',end:true});
  if(errors.length||logs.some(text=>text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Title/player runtime error: '+JSON.stringify({errors,logs}));
  if(!responses.some(r=>r.status===200&&r.url.includes('adv_start_bg_normal_01.png'))||!responses.some(r=>r.status===200&&r.url.includes('adv_start_bg_if_01.png')))throw Error('Both actual original title image responses are required');
  return {status:'ordinary_native_title_four_cases_passed',cases,errors,responses,logs,nativeAnimationAccepted:false};
}
