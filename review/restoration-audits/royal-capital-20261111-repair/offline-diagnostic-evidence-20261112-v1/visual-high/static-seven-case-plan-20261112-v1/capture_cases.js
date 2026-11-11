async initialPage => {
  const config=__APPROVED_EXECUTION__;
  if(!config.scopeApproved||!config.singleBrowserOwnerAssigned||!config.freezeComplete||
     !config.cases.length||config.cases.length>7)throw Error('No separately approved execution');
  const context=initialPage.context(),summaries=[];
  if(context.pages().length!==1)throw Error('Expected one fresh owner page');
  let initialTimer;
  try{await Promise.race([initialPage.close(),new Promise((_,reject)=>{
    initialTimer=setTimeout(()=>reject(Error('Initial page close deadline')),10000);
  })]);}finally{clearTimeout(initialTimer);}
  let previous=null,stopped=false;
  const globalDeadline=Date.now()+540000;
  const digest=async bytes=>Buffer.from(await crypto.subtle.digest('SHA-256',bytes)).toString('hex');
  const save=async(page,name,payload)=>{
    const downloaded=page.waitForEvent('download',{timeout:30000});
    await page.evaluate(async({name,payload})=>{
      const blob=await new Response(new Blob([JSON.stringify(payload)],{type:'application/json'}).stream()
        .pipeThrough(new CompressionStream('gzip'))).blob();
      const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=name;link.click();
      setTimeout(()=>URL.revokeObjectURL(url),0);
    },{name,payload});
    await(await downloaded).saveAs(config.outputRoot+'/'+name);
  };
  for(const spec of config.cases){
    if(stopped)break;
    // Close the old Page before newPage, retaining one browser/profile. Context-
    // wide init scripts are deliberately forbidden: each Page gets one hook.
    let page=null,pagePending=null,caseFinished=false,cdp=null,streaming=false,failure=null,fixture=null,trace=null,compiled=null;
    const caseDeadline=Math.min(globalDeadline,Date.now()+75000);
    // All potentially hanging driver/body work shares an absolute wall deadline.
    // These are observer-control timers, never writes to the game's clock.
    const bounded=async(operation,label,cap=75000)=>{
      const remaining=Math.min(caseDeadline-Date.now(),cap);if(remaining<=0)throw Error('Case deadline: '+label);
      let timer;try{return await Promise.race([Promise.resolve(typeof operation==='function'?operation():operation),new Promise((_,reject)=>{
        timer=setTimeout(()=>reject(Error('Deadline: '+label)),remaining);
      })]);}finally{clearTimeout(timer);}
    };
    const consoleLog=[],errors=[],http=[],resources=[],pending=new Set(),windows=[],route=[];
    let activeWindow=null,resourceBytes=0,decodedResourceBytes=0;
    let expected=[];
    const counts=new Map();
    const onResponse=response=>{
      const url=response.url();if(response.status()>=400)http.push({url,status:response.status()});
      const match=expected.find(row=>row.url===url);if(!match)return;
      const operation=bounded(async()=>{
        // Only the four frozen identity resources may be read. Identity encoding
        // makes response.body() bytes comparable to the installed original file,
        // rather than comparing a decompressed payload with wire-length claims.
        counts.set(url,(counts.get(url)||0)+1);if(counts.get(url)!==1)throw Error('Duplicate identity response: '+url);
        const headers=await response.allHeaders(),requestHeaders=await response.request().allHeaders();
        const length=Number(headers['content-length']);
        if(response.status()!==200||!Number.isSafeInteger(length)||length!==match.local.bytes||length>8*1024*1024)
          throw Error('Identity status/length budget mismatch: '+url);
        if((headers['content-encoding']||'identity').trim().toLowerCase()!=='identity'||
           requestHeaders['accept-encoding']?.trim().toLowerCase()!=='identity')throw Error('Identity transport encoding mismatch: '+url);
        if(response.fromServiceWorker())throw Error('Unexpected service worker identity response');
        resourceBytes+=length;if(resourceBytes>16*1024*1024)throw Error('Identity total byte budget exceeded');
        const raw=await response.body();decodedResourceBytes+=raw.length;
        if(raw.length>8*1024*1024||decodedResourceBytes>16*1024*1024)throw Error('Decoded identity byte budget exceeded');
        const actualSha=await digest(raw);
        if(raw.length!==match.local.bytes||actualSha!==match.local.sha256)throw Error('Actual identity bytes differ: '+url);
        resources.push({role:match.role,url,status:response.status(),headers,requestAcceptEncoding:requestHeaders['accept-encoding'],
          actualBytes:raw.length,actualSha256:actualSha,expectedLocal:match.local});
      },'identity response '+url).catch(error=>errors.push(String(error)));
      pending.add(operation);operation.finally(()=>pending.delete(operation));
    };
    const child=()=>{const frames=page.frames().filter(frame=>new URL(frame.url()).pathname==='/player/player.html');
      if(frames.length!==1)throw Error('Expected one production iframe');return frames[0];};
    const waitReady=async node=>bounded(child().waitForFunction(id=>{
      if(document.body?.dataset.phase==='error'||window.__staticReference?.errors.length)throw Error('Player/instrument error');
      return document.body?.dataset.node===id&&document.body.dataset.phase==='ready';
    },spec.scene+':'+node,{timeout:45000}),'natural ready '+node);
    const observation=()=>bounded(child().evaluate(()=>{
      const qa=window.__staticReference;return {node:document.body.dataset.node,phase:document.body.dataset.phase,
        clock:qa.clock?.snapshot(),lastRender:qa.lastRender,errors:qa.errors,
        instances:qa.instances.map(r=>({instance:r.instance,sourceURL:r.sourceURL,destroyed:r.destroyed,attached:!!r.model.parent,
          visible:r.model.visible,lastApplied:r.lastApplied?.sequence||null}))};
    }),'route observation');
    const capture=async node=>{
      const group={node,frames:[],overflow:false,sameFramePixelMatchAccepted:false};windows.push(group);activeWindow=group;
      await bounded(()=>cdp.send('Page.startScreencast',{format:'jpeg',quality:90,maxWidth:1280,maxHeight:1000,everyNthFrame:1}),'start compositor');streaming=true;
      const index=await bounded(child().evaluate(node=>{const qa=window.__staticReference;
        if(qa.request)throw Error('Outstanding capture request');qa.request={node};return qa.captures.length;
      },spec.scene+':'+node),'arm actual capture');
      await bounded(child().waitForFunction(index=>{
        const qa=window.__staticReference;if(qa.errors.length)throw Error(JSON.stringify(qa.errors));return qa.captures.length>index;
      },index,{timeout:5000}),'actual render readback',5000);
      // A tiny bounded compositor window can miss the selected actual render.
      // Retain that honest gap; never pause, repeat the actor read or redraw.
      const deadline=Date.now()+1500;
      while(group.frames.length<8&&Date.now()<deadline)await bounded(()=>page.waitForTimeout(25),'short compositor window');
      if(streaming){await bounded(()=>cdp.send('Page.stopScreencast'),'stop compositor',5000);streaming=false;}
      activeWindow=null;
      group.actorCaptureIndex=index;
      group.rule='Offline readable rolling HUD exact render/frame/instance/applied equality only; asynchronous screenshot timestamp is insufficient.';
    };
    try{
      const identityRows=spec.kind==='background'?[{role:'background',route:spec.backgroundBinding.route,local:spec.backgroundBinding.local}]:spec.resourceBinding.responses;
      expected=identityRows.map(row=>({...row,url:new URL(row.route,config.baseURL).href}));
      if(previous&&!previous.isClosed())await bounded(()=>previous.close(),'close previous Page',5000);
      if(context.pages().length!==0)throw Error('Previous page remained open');
      if(Date.now()>=caseDeadline)throw Error('Case deadline before Page creation');
      pagePending=context.newPage();
      pagePending.then(latePage=>{try{if(caseFinished&&!latePage.isClosed())latePage.close().catch(()=>{});}catch(error){errors.push(String(error));}},()=>{});
      page=previous=await bounded(pagePending,'create fresh Page',10000);
      page.on('response',onResponse);
      page.on('requestfailed',request=>errors.push({url:request.url(),failure:request.failure()}));
      page.on('pageerror',error=>errors.push(String(error)));
      page.on('console',message=>{if(consoleLog.length<300)consoleLog.push({type:message.type(),text:message.text(),location:message.location()});});
      await bounded(()=>page.setViewportSize({width:1280,height:1000}),'parent viewport');
      await bounded(()=>page.setExtraHTTPHeaders({'Accept-Encoding':'identity'}),'identity headers');
      await bounded(()=>page.addInitScript({content:'('+config.instrumentationSource+')('+JSON.stringify({...spec,targetNode:spec.scene+':'+spec.target})+');'}),'single per-Page hook');
      const programResponse=page.waitForResponse(response=>new URL(response.url()).pathname==='/program');
      programResponse.catch(()=>{}); // Navigation may fail before the later await; retain no unhandled rejection.
      const query='?scene='+spec.scene+'&node='+spec.route[0]+(spec.kind==='character'?'&nativePreview='+encodeURIComponent(spec.id):'');
      await bounded(()=>page.goto(config.baseURL+'/'+query,{waitUntil:'domcontentloaded'}),'initial navigation');
      const response=await bounded(programResponse,'program response');
      const programHeaders=await bounded(()=>response.allHeaders(),'program headers');
      if(response.status()!==200||Number(programHeaders['content-length'])!==spec.programBytes||spec.programBytes>64*1024*1024||
         (programHeaders['content-encoding']||'identity').trim().toLowerCase()!=='identity')throw Error('Program transport budget/encoding mismatch');
      const raw=await bounded(()=>response.body(),'program body');
      if(raw.length!==spec.programBytes||await digest(raw)!==spec.programSha256)throw Error('Actual compiled program differs from frozen preflight');
      compiled=JSON.parse(raw.toString('utf8'));
      fixture=await bounded(page.evaluate(()=>{const iframe=document.querySelector('iframe');if(!iframe)throw Error('No fixture iframe');
        const before=iframe.getBoundingClientRect().toJSON();iframe.style.width='480px';iframe.style.height='856px';
        return {preset:{parent:[1280,1000],iframeOuter:[480,856]},before};}),'outer fixture preset');
      await waitReady(spec.route[0]);
      fixture.measured=await bounded(child().evaluate(async()=>{
        let old=null,stable=0;
        for(let n=0;n<120;n++){
          await new Promise(requestAnimationFrame);
          const rect=e=>e.getBoundingClientRect().toJSON();
          const row={frameRect:rect(window.frameElement),viewportRect:rect(document.querySelector('#viewport')),
            actorCanvas:{width:document.querySelector('#actor').width,height:document.querySelector('#actor').height,
              cssRect:rect(document.querySelector('#actor'))}};
          stable=JSON.stringify(row)===JSON.stringify(old)?stable+1:0;old=row;
          if(stable>=3){
            if(Math.abs(row.frameRect.width-480)>.1||Math.abs(row.frameRect.height-856)>.1||
               Math.abs(row.viewportRect.width/row.viewportRect.height-9/16)>.001)throw Error('Fixture/aspect mismatch');
            const qa=window.__staticReference;if(!qa?.installed||!qa.clock||qa.clock.snapshot().previewRate!==1)throw Error('Observer/normal clock unavailable');
            qa.fixtureReady=true;return row;
          }
        }throw Error('Fixture never stabilized');
      }),'measure stable actual geometry',10000);
      cdp=await bounded(()=>context.newCDPSession(page),'create compositor session',5000);
      cdp.on('Page.screencastFrame',event=>{
        cdp.send('Page.screencastFrameAck',{sessionId:event.sessionId}).catch(error=>errors.push(String(error)));
        if(!activeWindow)return;
        if(activeWindow.frames.length>=8){activeWindow.overflow=true;
          if(streaming){streaming=false;cdp.send('Page.stopScreencast').catch(error=>errors.push(String(error)));}return;}
        activeWindow.frames.push({index:activeWindow.frames.length,mimeType:'image/jpeg',data:event.data,metadata:event.metadata});
      });
      for(const node of spec.route){
        if(node!==spec.route[0]){await bounded(()=>page.locator('#advance').click(),'natural advance');await waitReady(node);}
        await bounded(child().waitForFunction(id=>window.__staticReference?.lastRender?.node===id&&
          window.__staticReference.lastRender.phase==='ready',spec.scene+':'+node,{timeout:5000}),'ready actual render',5000);
        if(spec.captureNodes.includes(node))await capture(node);
        const observed=await observation();route.push(observed);
        if(observed.node!==spec.scene+':'+node||observed.errors.length||errors.length)throw Error('Natural route/observer mismatch');
      }
      if(spec.kind==='character'){
        const lifetime=await bounded(child().evaluate(model=>window.__staticReference.lifecycle.filter(row=>
          row.event==='created'&&row.sourceURL.includes('/ac_'+model+'/')),spec.model),'target lifecycle');
        if(lifetime.length!==1||!lifetime[0].fixtureReady)throw Error('Target did not have one creation after the fixture preset');
      }
      await bounded(Promise.allSettled([...pending]),'identity body completion');
      if(spec.kind==='character'&&(resources.length!==4||expected.length!==4))throw Error('Four actual identity responses were not verified');
      if(spec.kind==='background'&&resources.length!==1)throw Error('Actual background response was not verified');
      if(errors.length||http.some(r=>new URL(r.url).pathname!=='/favicon.ico')||consoleLog.some(r=>r.text.startsWith('STORY_PLAYER_ERROR')))
        throw Error('Runtime/HTTP errors retained');
    }catch(error){failure={name:error.name,message:String(error.message),stack:String(error.stack).slice(0,2000)};stopped=true;}
    finally{
      caseFinished=true;
      const cleanupDeadline=Date.now()+20000;
      const cleanup=async(promise,label)=>{
        const remaining=Math.max(1,Math.min(cleanupDeadline-Date.now(),10000));let timer;
        try{return await Promise.race([Promise.resolve(promise),new Promise((_,reject)=>{
          timer=setTimeout(()=>reject(Error('Cleanup deadline: '+label)),remaining);
        })]);}finally{clearTimeout(timer);}
      };
      if(cdp){if(streaming)await cleanup(cdp.send('Page.stopScreencast'),'stop').catch(error=>errors.push(String(error)));
        await cleanup(cdp.detach(),'detach').catch(error=>errors.push(String(error)));}
      try{if(page)trace=await cleanup(child().evaluate(()=>{const qa=window.__staticReference;
        return qa?{id:qa.id,errors:qa.errors,originalFailures:qa.originalFailures,lifecycle:qa.lifecycle,timing:qa.timing,captures:qa.captures,actorReadbacks:qa.actorReadbacks,lastRender:qa.lastRender}:null;
      }),'partial trace');}catch(error){errors.push(String(error));failure??={message:String(error)};stopped=true;}
      const name=spec.id+'-raw.json.gz';
      let rawSaved=false;
      try{if(page){await cleanup(save(page,name,{id:spec.id,spec,fixture,route,trace,compositorWindows:windows,resourceResponses:resources,
        console:consoleLog,pageErrors:errors,http,failure,
        actualCompiledRoute:compiled?.nodes.filter(row=>spec.route.map(n=>spec.scene+':'+n).includes(row.id)),
        acceptance:{staticIdentity:false,motion:false,face:false,geometry:false,originalWrapper:false,originalCsv:false,fullChapter:false},
        sameFrameStageMatchPendingOffline:true,rawImagesDiskOnly:true}),'save partial disk evidence');rawSaved=true;}}
      catch(error){failure??={message:'Evidence save failed: '+String(error)};stopped=true;}
      summaries.push({id:spec.id,failure,partial:!!failure,rawFile:rawSaved?config.outputRoot+'/'+name:null,
        actorReadbacks:trace?.actorReadbacks||0,staticCaptures:trace?.captures.length||0,
        compositorFrames:windows.reduce((n,w)=>n+w.frames.length,0),sameFrameWholeStage:'pending_offline_HUD_match',visualAccepted:false});
      if(page){page.off('response',onResponse);await cleanup(page.close(),'close Page');}
      if(context.pages().length!==0)throw Error('Page failed to close; owner must close browser');
    }
  }
  return {cases:summaries,stoppedOnFirstFailure:stopped,unrunCaseIds:config.cases.slice(summaries.length).map(r=>r.id),
    browserPagesRemaining:context.pages().length,needsImmediateOwnerBrowserClose:true,visualAccepted:false};
}
