async page => {
  // Root creates this fresh directory and supplies the sole browser/session.
  // This script is a normal saved-data consumer: no route handler, program
  // mutation, registry write, alternate player, retry or screenshot overwrite.
  const baseUrl='http://127.0.0.1:5192';
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-ending-normal-runtime-20261113-v1/';
  const owner='p30-ending-normal-v1',key='__stellaP30EndingNormalV1',scene=10450058;
  const expectedModels={9:'emilia01',10:'subaru_tshirt01',11:'julius01',12:'subaru_tshirt01',
    13:'julius01',14:'subaru_tshirt01',15:'julius01',16:'julius01',17:'subaru_tshirt01',
    18:'julius01',19:'subaru_tshirt01',20:'subaru_tshirt01',21:'emilia01',22:'emilia01',
    23:'subaru_tshirt01',24:'subaru_tshirt01',25:'emilia01',26:'subaru_tshirt01',
    27:'emilia01',28:'emilia01',29:'subaru_tshirt01',30:'emilia01',31:'emilia01',
    32:'subaru_tshirt01',33:'subaru_tshirt01',34:'subaru_tshirt01'};
  const selectedBranches={21:212,26:263};
  const logs=[],errors=[],visits=[],images=[],programs=[],programRequests=[],choices=[],cleanupErrors=[];
  let frame=null,handoffCommitted=false,result;
  const onConsole=message=>{const text=message.text();
    if(text.startsWith('STORY_')||text.startsWith('MODEL_'))logs.push({wall:Date.now(),text});};
  const onError=error=>errors.push(String(error));
  const onRequest=request=>{if(new URL(request.url()).pathname==='/program')
    programRequests.push({url:request.url(),method:request.method()});};
  const state=()=>frame.evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
    language:document.getElementById('language').value,now:performance.now(),
    timeOrigin:performance.timeOrigin,status:document.getElementById('status').textContent,
    error:document.getElementById('status').classList.contains('error')}));
  const ready=async number=>{
    await frame.waitForFunction(id=>document.body.dataset.node===id&&
      ['ready','choice'].includes(document.body.dataset.phase),scene+':'+number,{timeout:30000});
    const value=await state();visits.push(value);if(value.error)throw Error(value.status);return value;
  };
  const requireCondition=(condition,message)=>{if(!condition)throw Error(message);};
  try{
    page.on('console',onConsole);page.on('pageerror',onError);page.on('request',onRequest);
    const responsePromise=page.waitForResponse(response=>new URL(response.url()).pathname==='/program'&&response.status()===200,{timeout:30000});
    // If navigation itself fails, the independently pending response deadline
    // must not create an unhandled rejection after the failure result returns.
    responsePromise.catch(()=>{});
    // Only this first driver navigates. The ending driver has no goto/reload.
    await page.goto(baseUrl+'/?scene='+scene+'&node=8');
    const response=await responsePromise,program=await response.json();
    frame=page.frames().find(item=>item.url().includes('/player/player.html'));
    requireCondition(frame,'Normal player iframe missing');
    const nodes=new Map(program.nodes.map(node=>[node.id,node]));
    // Retain what was actually received before the first assertion, so a
    // mismatch cannot erase the program evidence while leaving only a label.
    const programProof={url:response.url(),start:program.start,nodeCount:program.nodes.length,
      edgeCount:program.edges.length,actualTargetModels:Object.keys(expectedModels).map(number=>({
        id:scene+':'+number,model:nodes.get(scene+':'+number)?.model??null})),
      suffixNodes:[35,36,37].map(number=>nodes.get(scene+':'+number)||null),
      receivedPathEdges:program.edges.filter(edge=>{
        const number=Number(edge.source.split(':')[1]);return edge.source.startsWith(scene+':')&&number>=8&&number<=37;
      })};
    programs.push(programProof);
    requireCondition(program.start===scene+':8','Wrong normal program start');
    for(const [number,model] of Object.entries(expectedModels))
      requireCondition(nodes.get(scene+':'+number)?.model===model,'Saved model mismatch '+number);
    // Verify the same normal program's full intended path before driving it.
    // Missing alternatives remain unavailable; the driver never repairs them.
    const edgeProof=[];
    for(let number=8;number<=36;number++){
      const edges=program.edges.filter(edge=>edge.source===scene+':'+number);
      const selected=selectedBranches[number];
      if(selected){
        const edge=edges.find(item=>item.id===scene+':'+number+':'+selected);
        requireCondition(edges.length===2&&edge?.kind==='choice'&&edge.available&&
          edge.target===scene+':'+(number+1),'Observed choice changed '+number);
        requireCondition(edges.filter(item=>item.available).length===1,'Unexpected restored alternative '+number);
        edgeProof.push({source:edge.source,id:edge.id,target:edge.target,
          unavailable:edges.filter(item=>!item.available).map(item=>item.id)});
      }else{
        requireCondition(edges.length===1&&edges[0].kind==='next'&&edges[0].available&&
          edges[0].target===scene+':'+(number+1),'Normal continuation changed '+number);
        edgeProof.push({source:edges[0].source,id:edges[0].id,target:edges[0].target});
      }
    }
    const narration=nodes.get(scene+':35'),movie=nodes.get(scene+':36'),clear=nodes.get(scene+':37');
    requireCondition(narration?.kind==='text'&&narration.model===''&&narration.text==='―完―','Narration35 changed');
    requireCondition(movie?.kind==='movie'&&movie.movie_resource==='adv_dive01_out'&&
      JSON.stringify(movie.command)===JSON.stringify(['StopBGM','','CardOut']),'Saved door changed');
    requireCondition(clear?.kind==='title'&&clear.title_mode==='end'&&clear.text==='CLEAR'&&
      clear.music.action==='play'&&clear.music.resource==='bgm_btl_adv_win01'&&
      clear.music.fade===1&&clear.music.restart===false&&
      JSON.stringify(clear.command)===JSON.stringify(['','','']),'Saved CLEAR changed');
    const endings=program.edges.filter(edge=>edge.source===scene+':37');
    const terminal=endings[0],native=terminal?.native_transition;
    requireCondition(endings.length===1&&terminal.available&&terminal.flow_action==='complete'&&
      terminal.target===''&&native?.next_scenario_label==='FINISH'&&native.next_scenario_id===0&&
      !Object.hasOwn(native,'next_section_id')&&!Object.hasOwn(native,'next_scene_id'),'Terminal FINISH changed');
    Object.assign(programProof,{targetModelsVerified:26,
      expectedModels,edgeProof,narration:{id:narration.id,kind:narration.kind,text:narration.text},
      movie:{id:movie.id,resource:movie.movie_resource,command:movie.command},
      clear:{id:clear.id,kind:clear.kind,title_mode:clear.title_mode,music:clear.music},
      terminal:{id:terminal.id,target:terminal.target,flow_action:terminal.flow_action,native}});
    await page.waitForFunction(()=>window.messageHistory?.some(message=>message.type==='stella-player-state'));
    for(let number=8;number<=34;number++){
      const current=await ready(number);
      if(number>=9){
        const path=output+'saved-'+scene+'-'+number+'.jpg';
        await page.screenshot({path,type:'jpeg',quality:88});
        images.push({sceneId:scene,scenarioId:number,character:'live2d/AC_'+expectedModels[number],
          path,phase:current.phase});
      }
      if(number===34)break;
      if(selectedBranches[number]){
        requireCondition(current.phase==='choice','Expected ordinary choice missing '+number);
        const buttons=frame.locator('#choices button:not([disabled])');
        requireCondition(await buttons.count()===1,'Observed route must have one available choice');
        const edge=await buttons.getAttribute('data-edge'),expected=scene+':'+number+':'+selectedBranches[number];
        requireCondition(edge===expected,'Wrong enabled branch '+edge);
        // Existing controls own selection and confirmation, as in the preceding
        // successful driver. No edge or choice handler is replaced or invoked twice.
        await buttons.evaluate(button=>button.click());
        await frame.locator('#advance').evaluate(button=>button.click());
        choices.push({node:number,edge});
      }else{
        requireCondition(current.phase==='ready','Unexpected choice '+number);
        await frame.locator('#viewport').click();
      }
    }
    await page.evaluate(()=>document.querySelector('#storyPreview').contentWindow.postMessage(
      {type:'stella-player-action',action:'language',value:'ja'},location.origin));
    await frame.waitForFunction(()=>document.getElementById('language').value==='ja'&&
      document.body.dataset.node==='10450058:34'&&document.body.dataset.phase==='ready');
    const final=await state();
    requireCondition(images.length===26&&programRequests.length===1&&errors.length===0&&
      !logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')),'Capture/program/error count mismatch');
    // This inert metadata handoff deliberately survives the first driver. It
    // owns no listener/timer and changes no production program. Keeping the
    // actual Document reference lets the ending driver refuse a reconstructed
    // iframe. That driver deletes it in finally; first-driver failure deletes
    // it here. Closing the tab also disposes the data if video-start fails.
    await frame.evaluate(({key,owner,summary})=>{
      if(Object.hasOwn(window,key))throw Error('Owned handoff already exists; do not retry this case');
      Object.defineProperty(window,key,{configurable:true,value:{owner,document,
        timeOrigin:performance.timeOrigin,url:location.href,summary,claimed:false}});
    },{key,owner,summary:programs[0]});
    handoffCommitted=true;
    result={status:'saved26_characters_completed_at34_ja',programs,programRequests,visits,images,choices,
      final,logs,errors,previewOverrides:false,formalWrites:false,actingAccepted:false,
      originalPhaseOrTimingAccepted:false,wholeEpisodeAccepted:false,
      sameDocumentHandoff:{key,owner,timeOrigin:final.timeOrigin,activeListenersOrTimers:0}};
  }catch(error){
    result={status:'saved_character_capture_failed',failure:String(error),programs,programRequests,
      visits,images,choices,logs,errors,previewOverrides:false,formalWrites:false};
  }finally{
    for(const [event,listener] of [['console',onConsole],['pageerror',onError],['request',onRequest]]){
      try{page.off(event,listener);}catch(error){cleanupErrors.push(String(error));}
    }
    if(frame&&!handoffCommitted){try{await frame.evaluate(({key,owner})=>{
      if(window[key]?.owner===owner)delete window[key];
    },{key,owner});}catch(error){cleanupErrors.push('Handoff cleanup: '+String(error));}}
  }
  return{...result,cleanupErrors,cleanupPassed:cleanupErrors.length===0};
}
