(async function runPrivateP30FxObserver(page,options){
  'use strict';
  options=options||{};
  if(options.executionAuthorized!==true)throw Error('Root has not released this private diagnostic');
  const base=new URL(options.baseUrl);
  if(!['http:','https:'].includes(base.protocol)||!['127.0.0.1','localhost','[::1]'].includes(base.hostname))
    throw Error('An existing loopback adapter is required');
  for(const name of ['ownerInstallSource','observerFactorySource','candidateManifestSource'])
    if(typeof options[name]!=='string'||!options[name].trim())throw Error('Missing reviewed source: '+name);
  const installInFrame=(0,eval)(options.ownerInstallSource);
  if(typeof installInFrame!=='function')throw Error('Owner installer source is not a factory');
  const candidate=JSON.parse(options.candidateManifestSource);
  const resource='adv_ef_explosion01',texture='fx-texture-6509005618617200518.png';
  const candidateRoot='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-node27-fx-source-proposal-20261112-v1/candidate-player-v3/';
  const slot='__stellaP30FxFirstPaintObserverV2',command='PlayFX,"adv_ef_explosion01",0,0,0';
  const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const requireValue=(condition,message)=>{if(!condition)throw Error(message);};
  const describe=error=>{try{return String(error?.message||error);}catch{return 'Unreadable error';}};
  const candidateResource=candidate.resources?.[resource];
  requireValue(equal(Object.keys(candidate.resources||{}),[resource])&&candidateResource?.id===resource&&
    candidateResource.keep_time===3&&candidateResource.systems?.length===3&&
    candidateResource.systems.every(system=>system.material.texture===texture),'Unexpected reviewed candidate manifest');

  const logs=[],errors=[],routeErrors=[],events=[],overrides=[],routeAttempts=[],listenerAttempts=[];
  const requests={program:0,manifest:0,texture:0};
  const hostCleanup={routes:[],listeners:[],observerHandleDisposed:null};
  let frame=null,observerInstalled=false,uninstallAttempted=false,observerClosure=null;
  let installReceipt=null,installationFailure=null,result=null,observerHandle=null;
  const log=message=>{
    try{const text=message.text(),type=message.type();
      if(text.startsWith('STORY_')||['warning','error'].includes(type))logs.push({wall:Date.now(),type,text});}
    catch(error){errors.push('console observation: '+describe(error));}
  };
  const pageError=error=>errors.push('pageerror: '+describe(error));
  const routed=(kind,handler)=>async route=>{
    try{requests[kind]++;requireValue(requests[kind]===1,'Unexpected '+kind+' request multiplicity');await handler(route);}
    catch(error){routeErrors.push({kind,error:describe(error)});
      try{await route.abort();}catch(abortError){routeErrors.push({kind,error:'abort: '+describe(abortError)});}}
  };

  const textureHandler=routed('texture',route=>route.fulfill({path:candidateRoot+texture,contentType:'image/png'}));
  const manifestHandler=routed('manifest',async route=>{
    const response=await route.fetch();requireValue(response.status()===200,'Formal effect manifest did not load');
    const original=await response.json(),changed=JSON.parse(JSON.stringify(original));
    requireValue(Object.keys(original.resources).length===9&&!original.resources[resource]&&
      original.camera_name===candidate.camera_name&&equal(original.preview,candidate.preview),
      'Unexpected original nine-resource manifest/camera/preview');
    changed.resources[resource]=candidateResource;
    const restored=JSON.parse(JSON.stringify(changed));delete restored.resources[resource];
    requireValue(equal(restored,original),'Unrelated effect manifest mutation');
    overrides.push({type:'effect-manifest',addedResource:resource,oldResourcesPreserved:9,
      cameraAndPreviewUnchanged:true,restoredWholeManifestDeepEqual:true});
    await route.fulfill({response,json:changed});
  });
  const programHandler=routed('program',async route=>{
    const response=await route.fetch();requireValue(response.status()===200,'Canonical saved-data compiler failed');
    const original=await response.json(),changed=JSON.parse(JSON.stringify(original));
    const rows=[25,26,27,28].map(number=>changed.nodes.filter(node=>node.id==='10450056:'+number));
    requireValue(original.start==='10450056:25'&&rows.every(matches=>matches.length===1),'Unexpected normal route entry/identities');
    const [,predecessor,target]=rows.map(matches=>matches[0]);
    requireValue(predecessor.character_image==='ADV_still_006'&&target.character_image==='ADV_still_006'&&
      target.text==='――ああっ!?'&&target.translation==='——啊啊！？'&&
      target.command.length===3&&target.phases.length===3&&target.command[1]===''&&
      Array.isArray(target.phases[1])&&target.phases[1].length===0,'Target identity/empty phase guard changed');
    // Keep the exact complete CommandRow from the previously run candidate.
    // One raw authored slot has two necessary in-memory compiler projections;
    // neither this row nor its phase is written back to any repository.
    const row={command,line:0,name:'PlayFX',label:'显示卡片特效',values:[resource,0,0,0],
      error:'',kind:'fx',reason:'private candidate only; original provider/phase/offset unknown',
      terminates_block:false,resource,offset:[0,0,0],blocking:false};
    target.command[1]=command;target.phases[1]=[row];
    const restored=JSON.parse(JSON.stringify(changed));
    const restoredTarget=restored.nodes.find(node=>node.id==='10450056:27');
    restoredTarget.command[1]='';restoredTarget.phases[1]=[];
    requireValue(equal(restored,original),'Program mutation outside the two command projections');
    overrides.push({type:'program',node:target.id,authoredFieldCount:1,compiledFieldCount:2,
      fields:['command[1]','phases[1]'],command,offset:[0,0,0],
      restoredWholeProgramDeepEqual:true,sourcePhaseRecovered:false,sourceOffsetsRecovered:false});
    await route.fulfill({response,json:changed});
  });
  const routes=[
    {pattern:base.origin+'/player-assets/'+texture,handler:textureHandler},
    {pattern:base.origin+'/player-assets/effects.json',handler:manifestHandler},
    {pattern:base.origin+'/program?*',handler:programHandler},
  ];
  const state=()=>frame.evaluate(()=>({wall:Date.now(),now:performance.now(),
    node:document.body.dataset.node,phase:document.body.dataset.phase,
    pictureHidden:document.querySelector('#picture').hidden,
    fxInstances:Number(document.querySelector('#card').dataset.fxInstances||0),
    fxLayers:document.querySelectorAll('.story-fx-layer').length,
    background:JSON.parse(document.querySelector('#card').dataset.backgroundGeometry||'null')}));
  async function ready(number){
    await frame.waitForFunction(number=>document.body.dataset.node==='10450056:'+number&&
      document.body.dataset.phase==='ready',number,{timeout:30000});
    const value=await state();events.push(value);return value;
  }
  async function uninstall(reason){
    if(!observerInstalled||uninstallAttempted)return observerClosure;
    // Retain the verified observer through a read-only Playwright JSHandle.
    // A later same-named slot must never supply another owner's uninstall.
    // If transport loses this handle, root closes its frame rather than guessing.
    uninstallAttempted=true;
    requireValue(observerHandle,'Owned observer handle unavailable; root must close the frame');
    observerClosure=await observerHandle.evaluate((owned,reason)=>{
      if(owned.receipt?.status!=='observer_install_verified'&&owned.receipt?.validationCleanup)
        return owned.receipt.validationCleanup;
      if(!owned.handle||!owned.proof||typeof owned.uninstall!=='function')return {
        status:'no_identity_proven_observer_handle',active:false,snapshotError:null,
        cleanup:owned.receipt?.cleanup||{allRestored:false,conflicts:['No retained owned cleanup function']},
        requiresFrameClosure:true};
      if(owned.handle.ownerProof!==owned.proof)throw Error('Observer handle ownership changed');
      return Reflect.apply(owned.uninstall,owned.handle,[reason]);
    },reason);
    observerInstalled=false;return observerClosure;
  }
  function requireObserverCleanup(value){
    const expected=['VisualEffects.play','console.info','VisualEffects.tick','ParticleSystem.geometry',
      'ParticleRenderer.draw','OriginalScene.draw'];
    requireValue(value?.active===false&&!value.snapshotError&&!value.requiresFrameClosure&&
      value.cleanup?.allRestored===true&&equal(value.cleanup.conflicts,[])&&
      equal([...(value.cleanup.restored||[])].sort(),[...expected].sort())&&
      equal([...(value.cleanup.listeners||[])].sort(),['pagehide-removed','timing-removed'])&&
      value.cleanup.slotState==='removed','Observer descriptor/listener/slot restoration incomplete');
  }
  function requireCompleteObservation(value){
    requireObserverCleanup(value);
    requireValue(Array.isArray(value.observerErrors)&&value.observerErrors.length===0&&value.droppedRecords===0,
      'Observer errors or dropped/missing records');
    requireValue(value.targetInstances===1&&value.yellowNonemptyDrawBatchObserved===true&&
      equal([...(value.visibleThresholdsObserved||[])].sort(),[1,2,3]),'Missing instance/Yellow/prefix thresholds');
    const counts=value.originalCallCounts,labels=['VisualEffects.play','console.info','VisualEffects.tick',
      'ParticleSystem.geometry','ParticleRenderer.draw','OriginalScene.draw'];
    requireValue(value.allOriginalCallCountsEqual===true&&counts&&equal(Object.keys(counts).sort(),[...labels].sort())&&
      labels.every(label=>counts[label].entries>0&&counts[label].entries===counts[label].originalCalls&&counts[label].originalThrows===0)&&
      counts['VisualEffects.play'].entries===1,'Original-method forwarding evidence mismatch');
    const records=value.records||[],activation=records.filter(row=>row.kind==='fx_activation_existing_start_call');
    const yellow=records.filter(row=>row.kind==='yellow_nonempty_draw_batch_returned');
    requireValue(activation.length===1&&yellow.length===1&&
      !records.some(row=>row.kind==='fx_activation_attribution_gap'),'Ambiguous/missing activation or Yellow batch');
    requireValue(yellow[0].yellow.length===1&&yellow[0].yellow.every(row=>row.instance===activation[0].instance&&
      row.seed===activation[0].seed&&row.vertices>0&&row.maxVertexAlpha>0),'Yellow array attribution mismatch');
    const text=records.filter(row=>row.kind==='text_visible_thresholds_drawn');
    requireValue(text.length>0&&[1,2,3].every(count=>text.some(row=>row.reached.includes(count)))&&
      text.every(row=>row.group==='adv_tell_illiustration'&&['zh','ja'].includes(row.language)&&
        row.prefix===(row.language==='zh'?'——啊啊！？':'――ああっ!?').slice(0,row.visible)),
      'Prefix threshold text/group evidence mismatch');
    requireValue(value.exactTextBeganMs===null&&value.exactGlSubmissionTimestampAvailable===false&&
      value.gpuPresentationAccepted===false,'Observer boundaries were overstated');
  }
  try{
    // Attempts are recorded before registration so even a partially failed
    // setup enters independent removal paths in finally. No route outlives this
    // invocation by design; OS/browser/server closure remains root's ownership.
    for(const [event,handler] of [['console',log],['pageerror',pageError]]){
      listenerAttempts.push({event,handler});page.on(event,handler);
    }
    for(const route of routes){routeAttempts.push(route);await page.route(route.pattern,route.handler);}
    await page.goto(base.origin+'/?scene=10450056&node=25',{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>{
      const preview=document.querySelector('#storyPreview');
      try{return preview?.contentWindow?.location.pathname==='/player/player.html'&&Boolean(preview.contentDocument?.body);}
      catch{return false;}
    });
    frame=page.frames().find(candidate=>new URL(candidate.url()).pathname==='/player/player.html');
    requireValue(frame,'Original player iframe unavailable');
    const entry=await ready(25);requireValue(entry.fxInstances===0&&entry.fxLayers===0,'Existing FX prevents bounded attribution');
    const installation=await installInFrame(frame,options.observerFactorySource,{slot});
    installReceipt=installation.receipt;observerHandle=installation.observerHandle;
    observerInstalled=Boolean(observerHandle);
    requireValue(installReceipt.status==='observer_install_verified'&&installReceipt.ownedSlotVerified===true&&
      installReceipt.slot===slot&&installReceipt.methodCount===6&&observerInstalled,'FX observer installation not verified');
    await frame.locator('#viewport').click();await ready(26);await page.waitForTimeout(800);
    await frame.locator('#viewport').click();await ready(27);
    // Preserve the already reviewed observer dwell; this is neither a source
    // Wait nor an attempt to repair the rejected flash/prefix order.
    await page.waitForTimeout(3500);
    const cleaned=await state();requireValue(cleaned.fxInstances===0&&cleaned.fxLayers===0,'Candidate cleanup not complete');
    await uninstall('before-node28');requireCompleteObservation(observerClosure);
    await frame.locator('#viewport').click();const returned=await ready(28);await page.waitForTimeout(600);
    const tail=await state();
    requireValue([returned,tail].every(value=>value.pictureHidden&&value.background?.resource==='bg/bg046c_stealshop'&&
      value.fxInstances===0&&value.fxLayers===0),'Node28 background/FX residue mismatch');
    const starts=logs.filter(row=>row.text.startsWith('STORY_FX_START ')).map(row=>JSON.parse(row.text.slice('STORY_FX_START '.length)));
    const ends=logs.filter(row=>row.text.startsWith('STORY_FX_END '));
    const activation=observerClosure.records.find(row=>row.kind==='fx_activation_existing_start_call');
    requireValue(starts.length===1&&starts[0].resource===resource&&starts[0].seed===activation.seed&&equal(starts[0].offset,[0,0,0])&&
      ends.length===1&&ends[0].text.includes(resource)&&ends[0].text.endsWith('expired'),'Candidate lifecycle changed');
    requireValue(requests.program===1&&requests.manifest===1&&requests.texture===1&&overrides.length===2,
      'Missing or repeated private projection/resource route');
    requireValue(!routeErrors.length&&!errors.length&&!logs.some(row=>
      row.text.startsWith('STORY_PLAYER_ERROR ')||row.text.startsWith('STORY_FX_ERROR ')),'Runtime/route failure');
    result={status:'private_fx_observation_completed',cleaned,returned,tail,starts,ends};
  }catch(error){
    installationFailure=error?.observerInstallationReceipt||null;
    // A later host receipt read can fail after atomic installation succeeded.
    // Preserve that exact retained object for finally; never reacquire a slot.
    if(!observerHandle&&error?.observerHandle){observerHandle=error.observerHandle;observerInstalled=true;}
    result={status:'private_fx_observation_failed',failure:describe(error)};
  }finally{
    if(observerInstalled&&!uninstallAttempted){
      try{await uninstall('driver-finally');requireObserverCleanup(observerClosure);}
      catch(error){errors.push('observer cleanup: '+describe(error));}
    }
    if(observerHandle){
      try{await observerHandle.dispose();hostCleanup.observerHandleDisposed=true;}
      catch(error){hostCleanup.observerHandleDisposed=false;errors.push('observer handle dispose: '+describe(error));}
    }
    for(const route of [...routeAttempts].reverse()){
      try{await page.unroute(route.pattern,route.handler);hostCleanup.routes.push({pattern:route.pattern,removed:true});}
      catch(error){hostCleanup.routes.push({pattern:route.pattern,removed:false,error:describe(error)});errors.push('unroute: '+describe(error));}
    }
    for(const {event,handler} of [...listenerAttempts].reverse()){
      try{page.off(event,handler);hostCleanup.listeners.push({event,removed:true});}
      catch(error){hostCleanup.listeners.push({event,removed:false,error:describe(error)});errors.push('off '+event+': '+describe(error));}
    }
  }
  if(errors.length||routeErrors.length||hostCleanup.routes.some(row=>!row.removed)||
    hostCleanup.listeners.some(row=>!row.removed)||observerInstalled||!observerClosure?.cleanup?.allRestored)
    result={...result,status:'private_fx_observation_failed',cleanupOrEvidenceIncomplete:true};
  return {...result,installReceipt,installationFailure,observer:observerClosure,events,logs,errors,routeErrors,
    requests,overrides,hostCleanup,previewOverrides:true,formalWrites:false,persisted:false,
    authoredFieldCount:1,compiledFieldCount:2,sourceCommandPhaseAccepted:false,sourceOffsetsAccepted:false,
    actualFxIdentityAccepted:false,scriptWaitAdded:false,observerDwellMs:{26:800,27:3500,28:600},
    noScreenshotOrVideo:true,requiresFrameClosure:result.status!=='private_fx_observation_completed',
    rootOwnsBrowserClosure:true,rootReviewed:false,rootConfirmed:false};
})
