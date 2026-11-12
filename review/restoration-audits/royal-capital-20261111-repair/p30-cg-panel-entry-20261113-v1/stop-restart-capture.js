async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-cg-panel-entry-followup-20261113-v3/';
  const logs=[],errors=[];
  const onConsole=message=>{const text=message.text();if(text.startsWith('STORY_'))logs.push({wall:Date.now(),text});};
  const onError=error=>errors.push(String(error));
  page.on('console',onConsole);page.on('pageerror',onError);
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  const ready=async id=>{
    await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
    await player().waitForFunction(id=>document.body.dataset.node===id&&document.body.dataset.phase==='ready',id,{timeout:30000});
  };
  const styles=()=>player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
    opacity:document.querySelector('#subtitles').style.opacity,translate:document.querySelector('#subtitles').style.translate}));
  try{
    // Queue the actual Stop control after the entering task, before its next
    // animation frame. This avoids an impossible synchronous reentrant Stop
    // inside enter(), and changes neither the script nor its animation clock.
    await page.addInitScript(()=>{
      let armed=true;
      document.addEventListener('stella-player-timing',event=>{
        if(!armed||event.detail.node!=='10450056:27'||event.detail.stage!=='text_begin')return;
        armed=false;queueMicrotask(()=>document.querySelector('#stop').click());
      });
    });
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=26');
    await ready('10450056:26');await player().locator('#viewport').click();
    await player().waitForFunction(()=>document.body.dataset.node==='10450056:27'&&document.body.dataset.phase==='stopped',null,{timeout:30000});
    await page.waitForTimeout(300);
    const stopped=await styles();
    if(stopped.opacity!==''||stopped.translate!==''||
       !logs.some(row=>row.text.startsWith('STORY_PANEL_IN_CANCELLED ')&&row.text.includes('10450056:27')))
      throw Error('Stop failed to release the entering panel');
    await player().locator('#restart').evaluate(button=>button.click());await ready('10450056:26');
    await player().locator('#viewport').click();await ready('10450056:27');await page.waitForTimeout(250);
    const restarted=await styles();
    if(restarted.opacity!==''||restarted.translate!=='')throw Error('Restart retained stale panel style');
    if(errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Baseline/Stop runtime error');
    return{status:'stop_restart_completed',stopped,restarted,logs,errors,
      previewOverrides:false,videoRecording:false,firstThreeScriptsChanged:false};
  }catch(error){return{status:'baseline_stop_failed',failure:String(error),logs,errors};}
  finally{page.off('console',onConsole);page.off('pageerror',onError);}
}

