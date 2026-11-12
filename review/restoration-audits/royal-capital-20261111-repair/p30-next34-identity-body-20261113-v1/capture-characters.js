async page => {
  const targets=[{"sceneId": 10450056, "scenarioId": 37, "character": "live2d/AC_elsa_nomantle01"}, {"sceneId": 10450056, "scenarioId": 38, "character": "live2d/AC_elsa_nomantle01"}, {"sceneId": 10450056, "scenarioId": 41, "character": "live2d/AC_elsa_nomantle01"}, {"sceneId": 10450056, "scenarioId": 44, "character": "live2d/AC_julius01"}, {"sceneId": 10450056, "scenarioId": 45, "character": "live2d/AC_felt01"}, {"sceneId": 10450056, "scenarioId": 46, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450056, "scenarioId": 47, "character": "live2d/AC_emilia01"}, {"sceneId": 10450056, "scenarioId": 48, "character": "live2d/AC_felt01"}, {"sceneId": 10450056, "scenarioId": 49, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450056, "scenarioId": 50, "character": "live2d/AC_julius01"}, {"sceneId": 10450056, "scenarioId": 51, "character": "live2d/AC_julius01"}, {"sceneId": 10450056, "scenarioId": 52, "character": "live2d/AC_emilia01"}, {"sceneId": 10450056, "scenarioId": 53, "character": "live2d/AC_julius01"}, {"sceneId": 10450057, "scenarioId": 4, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 5, "character": "live2d/AC_felt01"}, {"sceneId": 10450057, "scenarioId": 6, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 7, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450057, "scenarioId": 8, "character": "live2d/AC_felt01"}, {"sceneId": 10450057, "scenarioId": 9, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 10, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450057, "scenarioId": 11, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 12, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450057, "scenarioId": 13, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 14, "character": "live2d/AC_subaru_tshirt01"}, {"sceneId": 10450057, "scenarioId": 15, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 16, "character": "live2d/AC_emilia01"}, {"sceneId": 10450057, "scenarioId": 17, "character": "live2d/AC_julius01"}, {"sceneId": 10450057, "scenarioId": 18, "character": "live2d/AC_julius01"}, {"sceneId": 10450058, "scenarioId": 4, "character": "live2d/AC_felt01"}, {"sceneId": 10450058, "scenarioId": 5, "character": "live2d/AC_emilia01"}, {"sceneId": 10450058, "scenarioId": 6, "character": "live2d/AC_julius01"}, {"sceneId": 10450058, "scenarioId": 7, "character": "live2d/AC_emilia01"}, {"sceneId": 10450058, "scenarioId": 8, "character": "live2d/AC_julius01"}];
  const output="/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-next34-native-runtime-20261113-v1/";

  const logs=[],errors=[],visits=[],images=[],programs=[];
  const onConsole=message=>{const text=message.text();if(text.startsWith('STORY_')||text.startsWith('MODEL_'))logs.push({wall:Date.now(),text});};
  const onError=error=>errors.push(String(error));page.on('console',onConsole);page.on('pageerror',onError);
  const player=()=>page.frames().find(frame=>frame.url().includes('/player/player.html'));
  const ready=async(scene,node)=>{
    await player().waitForFunction(id=>document.body.dataset.node===id&&['ready','choice'].includes(document.body.dataset.phase),scene+':'+node,{timeout:30000});
    const state=await player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,wall:Date.now()}));visits.push(state);return state;
  };
  try{
    for(const [scene,first,last] of [[10450056,36,53],[10450057,3,18],[10450058,3,8]]){
      const productionResponse=page.waitForResponse(response=>new URL(response.url()).pathname==='/program'&&response.status()===200);
      await page.goto('http://127.0.0.1:5192/?scene='+scene+'&node='+first);
      const program=await(await productionResponse).json();
      for(const target of targets.filter(target=>target.sceneId===scene)){
        const node=program.nodes.find(node=>node.id===scene+':'+target.scenarioId);
        const expected=target.character.replace('live2d/AC_','');
        if(!node||node.model!==expected)throw Error('Saved model mismatch '+scene+':'+target.scenarioId);
      }
      programs.push({scene,start:program.start,targetModelsVerified:targets.filter(target=>target.sceneId===scene).length});
      await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
      for(let node=first;node<=last;node++){
        const state=await ready(scene,node);const target=targets.find(target=>target.sceneId===scene&&target.scenarioId===node);
        if(target){
          const image=output+'saved-'+scene+'-'+node+'.jpg';
          await page.screenshot({path:image,type:'jpeg',quality:88});
          images.push({...target,path:image,phase:state.phase});
        }
        if(node===last)break;
        if(state.phase==='choice'){
          const expectedBranch=node===7?73:node===17?173:null;
          if(scene!==10450057||!expectedBranch)throw Error('Unexpected choice');
          const buttons=player().locator('#choices button:not([disabled])');
          if(await buttons.count()!==1)throw Error('Observed route must have exactly one restored choice');
          const edge=await buttons.getAttribute('data-edge');
          if(!edge.endsWith(':'+expectedBranch))throw Error('Wrong observed branch '+edge);
          // Select and confirm through the existing controls. Embedded mode
          // hides the textual controls but retains the native choice handler.
          await buttons.evaluate(button=>button.click());
          await player().locator('#advance').evaluate(button=>button.click());
        }else await player().locator('#viewport').click();
      }
    }
    if(images.length!==33||errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')))throw Error('Character playback missing target/error');
    return{status:'saved33_character_fields_completed',programs,visits,images,logs,errors,previewOverrides:false,formalWrites:false,actingAccepted:false,wholeEpisodeAccepted:false,segmentedPlayback:true};
  }catch(error){return{status:'saved_character_capture_failed',failure:String(error),programs,visits,images,logs,errors};}
  finally{page.off('console',onConsole);page.off('pageerror',onError);}
}
