async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-node27-prefix-runtime-20261113-v2/';
  const logs=[],errors=[],visits=[];
  const consoleListener=message=>{const text=message.text();if(text.startsWith('STORY_'))logs.push({wall:Date.now(),text});};
  const errorListener=error=>errors.push(String(error));
  page.on('console',consoleListener);page.on('pageerror',errorListener);
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  const ready=async node=>{
    await player().waitForFunction(node=>document.body.dataset.node==='10450056:'+node&&
      document.body.dataset.phase==='ready',node,{timeout:30000});
    visits.push(node);
  };
  try{
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=26');
    await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
    await ready(26);await player().locator('#viewport').click();await ready(27);
    if(await player().locator('#language').inputValue()!=='zh')throw Error('Default Chinese preview changed');
    const chinese=await player().locator('#accessibleText').textContent();
    if(!chinese.includes('——啊啊！？'))throw Error('Saved Chinese two-dash text missing');
    const chineseImage=output+'node27-two-dashes-zh.png';
    await page.screenshot({path:chineseImage});
    // Embedded mode hides aside controls; select the existing language control
    // explicitly without changing its DOM/style or the application's handler.
    await player().locator('#language').selectOption('ja',{force:true});
    const japanese=await player().locator('#accessibleText').textContent();
    if(!japanese.includes('――ああっ!?'))throw Error('Corrected normalized Japanese text missing');
    const japaneseImage=output+'node27-two-dashes-ja.png';
    await page.screenshot({path:japaneseImage});
    await player().locator('#language').selectOption('zh',{force:true});
    await player().locator('#viewport').click();await ready(28);
    if(errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Prefix runtime error');
    return{status:'ordinary26_27_28_corrected_prefix_completed',visits,chinese,japanese,chineseImage,japaneseImage,
      logs,errors,previewOverrides:false,videoRecording:false,fxOrPanelTimingAccepted:false};
  }catch(error){return{status:'prefix_capture_failed',failure:String(error),visits,logs,errors};}
  finally{page.off('console',consoleListener);page.off('pageerror',errorListener);}
}

