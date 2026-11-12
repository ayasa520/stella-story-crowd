async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-cg-panel-entry-runtime-20261113-v1/';
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
  await page.addInitScript(()=>{
    window.__entryTextBegins=[];
    document.addEventListener('stella-player-timing',event=>{
      if(event.detail.stage!=='text_begin')return;
      const canvas=document.querySelector('#subtitles');
      window.__entryTextBegins.push({node:event.detail.node,now:performance.now(),
        opacity:canvas.style.opacity,translate:canvas.style.translate});
    });
  });
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
    const starts=logs.filter(row=>row.text.startsWith('STORY_PANEL_IN_START ')).map(row=>JSON.parse(row.text.slice('STORY_PANEL_IN_START '.length)));
    const completes=logs.filter(row=>row.text.startsWith('STORY_PANEL_IN_COMPLETE ')).map(row=>JSON.parse(row.text.slice('STORY_PANEL_IN_COMPLETE '.length)));
    const textBegins=await player().evaluate(()=>window.__entryTextBegins);
    for(const node of ['10450056:26','10450056:27']){
      if(starts.filter(row=>row.node===node&&row.group==='adv_tell_illiustration'&&Math.abs(row.duration-0.1666666716337204)<1e-9).length!==1||
         completes.filter(row=>row.node===node).length!==1||!textBegins.some(row=>row.node===node&&row.opacity==='0'))
        throw Error('Independent parallel CG entry missing at'+node);
    }
    if(starts.some(row=>row.node==='10450056:28'))throw Error('Ordinary actor received an unbound entry profile');
    return{status:'ordinary26_27_28_cg_entry_completed',starts,completes,textBegins,visits,chinese,japanese,chineseImage,japaneseImage,
      logs,errors,previewOverrides:false,videoRecording:false,fxOrPanelTimingAccepted:false};
  }catch(error){return{status:'prefix_capture_failed',failure:String(error),visits,logs,errors};}
  finally{page.off('console',consoleListener);page.off('pageerror',errorListener);}
}


