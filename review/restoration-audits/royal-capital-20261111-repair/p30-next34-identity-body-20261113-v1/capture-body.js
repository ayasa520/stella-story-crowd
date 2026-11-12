async page => {
  const logs=[],errors=[],visits=[],overrides=[];
  const consoleListener=message=>{const text=message.text();if(text.startsWith('STORY_')||text.startsWith('MODEL_'))logs.push({wall:Date.now(),text});};
  const errorListener=error=>errors.push(String(error));
  page.on('console',consoleListener);page.on('pageerror',errorListener);
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  const ready=async node=>{
    await player().waitForFunction(node=>document.body.dataset.node==='10450056:'+node&&
      document.body.dataset.phase==='ready',node,{timeout:30000});
    visits.push(await player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
      now:performance.now(),wall:Date.now()})));
  };
  try{
    const productionResponse=page.waitForResponse(response=>new URL(response.url()).pathname==='/program'&&response.status()===200);
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=32');
    const program=await(await productionResponse).json();
    const saved=program.nodes.find(node=>node.id==='10450056:33');
    if(program.start!=='10450056:32'||saved.model!=='felt01'||saved.body!=='act_punpun'||saved.face!==''||saved.extra_motions.length)throw Error('Saved Felt33 program mismatch');
    await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
    await ready(32);await page.waitForTimeout(400);
    await player().locator('#viewport').click();await ready(33);
    // Hold only the observer to include the native one-shot→hold transition.
    // The script queue, source motion, face and extra layers are not retimed.
    await page.waitForTimeout(2200);
    await player().locator('#viewport').click();await ready(34);await page.waitForTimeout(500);
    if(!logs.some(row=>row.text.startsWith('STORY_MOTION_BINDING felt01 act_punpun '))||
       !logs.some(row=>row.text==='STORY_ANIMATOR_TRANSITION felt01 motion act_punpun_w'))
      throw Error('Native Felt body binding/automatic hold missing');
    if(errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Body trial runtime error');
    return{status:'saved32_33punpun_34_completed',visits,logs,errors,overrides:[],programRequests:1,
      previewOverrides:false,formalWrites:false,scriptWaitAdded:false,observerHold33Ms:2200,
      inRecordingScreenshots:false,bodyAccepted:false,faceAccepted:false};
  }catch(error){return{status:'felt_body_capture_failed',failure:String(error),visits,logs,errors,overrides:[]};}
  finally{page.off('console',consoleListener);page.off('pageerror',errorListener);}
}
