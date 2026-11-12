async page => {
  const root='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-ord90to104-runtime-20261113-v1/';
  const expected={29:'rom01',30:'julius01',31:'julius01',32:'julius01',33:'felt01',34:'julius01',35:'felt01',36:'julius01',39:'julius01',40:'subaru_tshirt01',42:'julius01',43:'subaru_tshirt01'};
  const logs=[],errors=[],responses=[],visits=[],captures=[];
  page.on('console',message=>{
    const text=message.text();
    if(text.startsWith('STORY_')||text.startsWith('MODEL_')||['warning','error'].includes(message.type()))
      logs.push({wall:Date.now(),type:message.type(),text});
  });
  page.on('pageerror',error=>errors.push(String(error)));
  page.on('response',response=>{
    if(response.url().includes('.model3.json')||response.url().includes('/api/model/'))
      responses.push({url:response.url(),status:response.status()});
  });
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  try{
    await page.goto('http://127.0.0.1:5192/?scene=10450056&node=28');
    await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
    // Every observed edge28→44 is installed and linear. Advancing the saved
    // program checks actual resource/display lifecycles without authoring a
    // phase, motion or missing nomantle identity in a private preview.
    for(let node=28;node<=44;node++){
      await player().waitForFunction(node=>document.body.dataset.node==='10450056:'+node&&
        document.body.dataset.phase==='ready',node,{timeout:30000});
      const state=await player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
        actorHidden:document.querySelector('#actor').hidden,pictureHidden:document.querySelector('#picture').hidden,
        background:JSON.parse(document.querySelector('#card').dataset.backgroundGeometry||'null')}));
      visits.push(state);
      if(expected[node]){
        const id='10450056:'+node,model=expected[node];
        if(state.actorHidden||!state.pictureHidden||!logs.some(row=>row.text==='STORY_DISPLAY_COMMIT '+id+' actor '+model))
          throw Error('Saved-data actor/display mismatch at'+node);
        const file=root+'node-'+String(node).padStart(4,'0')+'.png';
        await page.screenshot({path:file});
        captures.push({node:id,model,path:file,phase:'ready',privateOverride:false});
      }
      if(node<44)await player().locator('#viewport').click();
    }
    for(const model of new Set(Object.values(expected)))
      if(!logs.some(row=>row.text.startsWith('MODEL_READY '+model+' ')))throw Error('No actual assembled model ready: '+model);
    if(captures.length!==12||errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))
      throw Error('Incomplete capture or runtime failure');
    if(responses.some(row=>row.status!==200))throw Error('Model resource response failure');
    return{status:'ordinary28_to44_twelve_character_fields_completed',visits,captures,logs,responses,errors,
      previewOverrides:false,videoRecording:false,scriptWaitAdded:false,actingAccepted:false,
      pendingNomantleNodes:[37,38,41],formalCharacterDelta:12};
  }catch(error){return{status:'ordinary_character_capture_failed',failure:String(error),visits,captures,logs,responses,errors,previewOverrides:false};}
}
