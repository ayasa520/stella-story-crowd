(async function captureNormalP30EndMarkerAlignment(page,options){
  'use strict';
  // SOURCE ONLY. Root supplies the existing sole Playwright page and a fresh
  // output directory, owns the server/session and closes them independently.
  // This helper installs no route, prototype hook, player, renderer or clock.
  if(options?.executionAuthorized!==true)throw Error('Root has not released this normal capture');
  const bindings=JSON.parse(options.expectedBindingsSource);
  const expected=new Map(bindings.rows.map(row=>[row.id,row]));
  const requireValue=(condition,message)=>{if(!condition)throw Error(message);};
  requireValue(expected.size===6&&['10450058:34','10450058:35','10450058:36','10450058:37','10450056:2','10450056:3']
    .every(id=>expected.has(id)),'Expected source bindings changed');
  const base='http://127.0.0.1:5192';
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-node35-alignment-and-fx-runtime-20261113-v1/';
  const markerProfile='p30-ending-marker-source-centered-v1',group='adv_tell_system';
  const rowPath='/adv_tell_system/anim_root/txt_tell',rowId=739;
  const logs=[],errors=[],layoutLogs=[],visits=[],images=[],programs=[],programRequests=[],resourceResponses=[],cleanupErrors=[];
  const listenerAttempts=[],hostCleanup={listeners:[]};let frame=null,result=null,caseName=null;
  const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const describe=error=>String(error?.message||error);
  const onConsole=message=>{
    try{
      const text=message.text();
      if(text.startsWith('STORY_')||text.startsWith('MODEL_'))logs.push({case:caseName,hostUnixMs:Date.now(),text});
      if(text.startsWith('STORY_TEXT_PANEL_LAYOUT '))layoutLogs.push({case:caseName,
        detail:JSON.parse(text.slice('STORY_TEXT_PANEL_LAYOUT '.length))});
    }catch(error){errors.push('Console observation: '+describe(error));}
  };
  const onError=error=>errors.push(describe(error));
  const onRequest=request=>{
    const url=new URL(request.url());
    if(url.origin===base&&url.pathname==='/program')programRequests.push({case:caseName,url:request.url(),method:request.method()});
  };
  const onResponse=response=>{
    const url=new URL(response.url());
    if(url.origin===base&&['/movie/adv_dive01_out','/player/text-panel-presentation.json'].includes(url.pathname))
      resourceResponses.push({case:caseName,url:response.url(),status:response.status()});
  };
  const state=()=>frame.evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,
    language:document.getElementById('language').value,performanceMs:performance.now(),timeOrigin:performance.timeOrigin,
    status:document.getElementById('status').textContent,error:document.getElementById('status').classList.contains('error'),
    panelStyle:{opacity:document.getElementById('subtitles').style.opacity,translate:document.getElementById('subtitles').style.translate}}));
  async function at(id,phase='ready'){
    await frame.waitForFunction(({id,phase})=>document.body.dataset.node===id&&document.body.dataset.phase===phase,
      {id,phase},{timeout:phase==='complete'?90000:30000});
    const value=await state();visits.push({case:caseName,...value});
    requireValue(!value.error,value.status);return value;
  }
  function requireNext(program,source,target){
    const edges=program.edges.filter(edge=>edge.source===source);
    requireValue(edges.length===1&&edges[0].kind==='next'&&edges[0].available&&edges[0].target===target,
      'Saved continuation changed: '+source);return edges[0];
  }
  async function load(scene,start,ids,name){
    caseName=name;frame=null;
    // Read the normal response; never intercept, fulfill, mutate or refetch it.
    // Arm before navigation, and consume its rejection if navigation fails.
    const pending=page.waitForResponse(response=>{
      const url=new URL(response.url());return url.origin===base&&url.pathname==='/program'&&
        url.searchParams.get('scene')===String(scene)&&url.searchParams.get('node')===String(start)&&response.status()===200;
    },{timeout:30000});pending.catch(()=>{});
    await page.goto(base+'/?scene='+scene+'&node='+start,{waitUntil:'domcontentloaded'});
    const response=await pending,program=await response.json();
    requireValue(program.start===scene+':'+start,'Unexpected saved program start');
    const rows=ids.map(id=>{
      const matches=program.nodes.filter(row=>row.id===id),bound=expected.get(id);
      requireValue(matches.length===1&&bound,'Missing saved target '+id);const row=matches[0];
      for(const field of ['kind','speaker','text','translation','model','character_image','movie_resource','command'])
        requireValue(equal(row[field],bound[field]),'Saved field guard changed '+id+'.'+field);
      return row;
    });
    // Keep the exact guarded rows/edges from this actual received program.
    // Expected values were serialized beforehand from native/review files.
    programs.push({case:caseName,url:response.url(),httpStatus:response.status(),start:program.start,
      rows,edges:program.edges.filter(edge=>ids.includes(edge.source)),normalResponseReadOnly:true});
    await page.waitForFunction(()=>{
      const preview=document.querySelector('#storyPreview');
      try{return preview?.contentWindow?.location.pathname==='/player/player.html'&&Boolean(preview.contentDocument?.body);}
      catch{return false;}
    });
    frame=page.frames().find(value=>new URL(value.url()).pathname==='/player/player.html');
    requireValue(frame,'Actual normal player iframe unavailable');return program;
  }
  function layoutEvidence(id,language){
    // These are production prepareText results. A repeated language may reuse
    // its earlier deduplicated log; the current DOM language/ready state below
    // still proves which text is actually being captured. No layout/draw call
    // or temporary prototype wrapper is added merely to force another report.
    const rows=layoutLogs.filter(row=>row.case===caseName&&row.detail.node===id&&row.detail.language===language&&row.detail.rowPath===rowPath);
    requireValue(rows.length>0,'Production layout log missing '+id+'/'+language);
    const detail=rows.at(-1).detail,marker=id==='10450058:35';
    requireValue(detail.profile===(marker?markerProfile:'native-default')&&detail.group===group&&detail.rowId===rowId&&
      detail.nativeAlignment===513&&detail.effectiveAlignment===(marker?514:513),'Panel profile/shared/effective alignment mismatch');
    const rect=detail.rect;
    requireValue(rect&&['x','y','width','height','scale_x','scale_y'].every(key=>Number.isFinite(rect[key]))&&
      rect.width>0&&rect.height>0&&Number.isFinite(detail.size)&&detail.size>0&&
      Number.isInteger(detail.lineCount)&&detail.lineCount>0&&Array.isArray(detail.lineWidths)&&
      detail.lineWidths.length===detail.lineCount&&detail.lineWidths.every(width=>Number.isFinite(width)&&width>=0),
      'Incomplete prepared rect/font/layout evidence');
    if(marker)requireValue(detail.lineCount===1,'Ending marker unexpectedly wraps');
    return detail;
  }
  async function capture(id,language){
    await at(id);
    // This is the existing parent→player language control, handled by the
    // production select/change path. It neither advances nor edits a node.
    await page.evaluate(language=>document.querySelector('#storyPreview').contentWindow.postMessage(
      {type:'stella-player-action',action:'language',value:language},location.origin),language);
    await frame.waitForFunction(({id,language})=>document.body.dataset.node===id&&document.body.dataset.phase==='ready'&&
      document.getElementById('language').value===language,{id,language},{timeout:5000});
    const before=await state();requireValue(!before.error,before.status);
    const path=output+'alignment-'+id.replace(':','-')+'-'+language+'.png';
    await frame.locator('#viewport').screenshot({path,type:'png'});
    // Retain a successfully written image path before later evidence checks.
    // A missing layout log must not erase or undercount an existing capture.
    const image={node:id,language,path,before,after:null,layout:null};images.push(image);
    const after=await state();image.after=after;
    requireValue(after.node===id&&after.phase==='ready'&&after.language===language&&!after.error,
      'Node/language moved during screenshot');
    image.layout=layoutEvidence(id,language);
  }
  async function normalStop(reason){
    if(!frame||frame.isDetached())return;
    await frame.locator('#stop').evaluate(button=>button.click());
    await frame.waitForFunction(()=>document.body.dataset.phase==='stopped',null,{timeout:3000});
    visits.push({case:caseName,label:reason,...await state()});
  }
  try{
    for(const [event,handler] of [['console',onConsole],['pageerror',onError],['request',onRequest],['response',onResponse]]){
      listenerAttempts.push({event,handler});page.on(event,handler);
    }
    const ending=await load(10450058,34,['10450058:34','10450058:35','10450058:36','10450058:37'],'ending-marker');
    requireNext(ending,'10450058:34','10450058:35');requireNext(ending,'10450058:35','10450058:36');
    requireNext(ending,'10450058:36','10450058:37');
    const terminal=ending.edges.filter(edge=>edge.source==='10450058:37'),native=terminal[0]?.native_transition;
    requireValue(terminal.length===1&&terminal[0].available&&terminal[0].flow_action==='complete'&&terminal[0].target===''&&
      native?.next_scenario_label==='FINISH'&&native.next_scenario_id===0&&
      !Object.hasOwn(native,'next_section_id')&&!Object.hasOwn(native,'next_scene_id'),'Saved no-successor FINISH changed');
    await at('10450058:34');await frame.locator('#viewport').click();await at('10450058:35');
    await capture('10450058:35','ja');await capture('10450058:35','zh');
    await frame.locator('#viewport').click();await at('10450058:37','complete');
    const enters=logs.filter(row=>row.case==='ending-marker'&&row.text.startsWith('STORY_PLAYER_ENTER '))
      .map(row=>row.text.split(' ')[1]);
    requireValue(equal(enters,['10450058:34','10450058:35','10450058:36','10450058:37'])&&
      logs.some(row=>row.case==='ending-marker'&&row.text==='STORY_PLAYER_TITLE 10450058:37 end'),
      'Normal door→CLEAR continuation evidence missing');
    await normalStop('stop-after-ending-before-regression');
    const regression=await load(10450056,2,['10450056:2','10450056:3'],'ordinary-narration');
    requireNext(regression,'10450056:2','10450056:3');
    await at('10450056:2');await capture('10450056:2','ja');await capture('10450056:2','zh');
    await frame.locator('#viewport').click();await at('10450056:3');
    await capture('10450056:3','ja');await capture('10450056:3','zh');
    requireValue(images.length===6&&equal(programRequests.map(row=>row.case),['ending-marker','ordinary-narration'])&&
      programRequests.every(row=>row.method==='GET'),'Unexpected screenshot/program count');
    requireValue(images.every(image=>equal(image.layout.rect,images[0].layout.rect)),'Shared narration rect changed between captures');
    requireValue(!errors.length&&!logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR ')),'Player/observation error');
    result={status:'normal_end_marker_alignment_and_default_narration_captured',alignmentMetadataChecksPassed:true};
  }catch(error){result={status:'normal_alignment_capture_failed',failure:describe(error)};}
  finally{
    // Stop through the existing handler even if a capture/assertion failed.
    // Listener removals do not depend on Stop, screenshot or log success.
    try{await normalStop('driver-finally-stop');}catch(error){cleanupErrors.push('normal Stop: '+describe(error));}
    for(const {event,handler} of [...listenerAttempts].reverse()){
      try{page.off(event,handler);hostCleanup.listeners.push({event,removed:true});}
      catch(error){hostCleanup.listeners.push({event,removed:false});cleanupErrors.push('remove '+event+': '+describe(error));}
    }
  }
  if(cleanupErrors.length||errors.length)result={...result,status:'normal_alignment_capture_failed'};
  return {...result,sourceBoundDataHead:bindings.parentReportedDataHead,programs,programRequests,layoutLogs,images,visits,logs,errors,
    resourceResponses,cleanupErrors,hostCleanup,previewOverrides:false,formalWrites:false,persisted:false,
    prototypeHooksInstalled:0,newPlayerOrContext:false,videoRecording:false,screenshotsTaken:images.length,
    actingOrWholeEpisodeAccepted:false,originalNativeAlignmentMechanismRecovered:false,
    rootOwnsServerSessionFilesAndClosure:true,rootReviewed:false,rootConfirmed:false};
})
