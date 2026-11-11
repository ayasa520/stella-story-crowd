async initialPage => {
  // The owner replaces this single marker with an explicitly approved frozen
  // configuration and writes a new local runner. This draft does not authorize
  // navigation or registry changes. Never return pixel/base64 payloads to CLI.
  const config = __APPROVED_EXECUTION__;
  if (!config.scopeApproved || !config.singleBrowserOwnerAssigned || !config.freezeComplete ||
      !config.outputRoot || !/^http:\/\/127\.0\.0\.1:\d+$/.test(config.baseURL) ||
      config.cases.length<1 || config.cases.length>3) throw Error('Missing root-approved frozen execution');
  const context = initialPage.context(), summaries = [];
  if (context.pages().length !== 1) throw Error('Expected only the new owner initial page');
  await initialPage.close();
  let casePage = null, stopped = false;
  const savePayload = async (page, name, payload) => {
    const download = page.waitForEvent('download',{timeout:30000});
    await page.evaluate(async ({name,payload}) => {
      const blob = await new Response(new Blob([JSON.stringify(payload)],{type:'application/json'})
        .stream().pipeThrough(new CompressionStream('gzip'))).blob();
      const url = URL.createObjectURL(blob), link = document.createElement('a');
      link.href=url; link.download=name; link.click();
      setTimeout(()=>URL.revokeObjectURL(url),0);
    },{name,payload});
    await (await download).saveAs(config.outputRoot+'/'+name);
  };
  for (const spec of config.cases) {
    if (stopped) break;
    // Close before creating: one Page at a time, one init hook per fresh Page,
    // one shared Chrome. Old observers cannot survive into the next candidate.
    if (casePage && !casePage.isClosed()) await casePage.close();
    if (context.pages().length !== 0) throw Error('Previous case left another Page');
    casePage = await context.newPage();
    const page = casePage, started = Date.now(), logs=[],errors=[],http=[],network=[],pixelFrames=[],shots=[];
    let cdp=null,streamActive=false,overflow=false,droppedFrames=0,failure=null,trace=null,fixture=null,compiled=null;
    const onConsole = message => {
      if (logs.length<2000) logs.push({type:message.type(),text:message.text(),location:message.location(),hostWall:Date.now()});
    };
    const onError = error => errors.push(String(error));
    const onRequestFailed = request => errors.push({url:request.url(),failure:request.failure()});
    const onResponse = response => {
      const url=response.url(),status=response.status();
      if (status>=400) http.push({url,status});
      if (/\/api\/model\/|\/asset\/.*\/models\/|\/resource\/models\//.test(url))
        network.push({url,status,hostWall:Date.now(),headers:response.headers()});
    };
    page.on('console',onConsole);page.on('pageerror',onError);page.on('requestfailed',onRequestFailed);page.on('response',onResponse);
    const child = () => {
      const frames=page.frames().filter(frame=>new URL(frame.url()).pathname==='/player/player.html');
      if(frames.length!==1)throw Error('Expected one actual production player iframe');
      return frames[0];
    };
    const waitReady = async number => {
      await child().waitForFunction(id => {
        if (document.body?.dataset.phase==='error') throw Error('Player error phase');
        return document.body?.dataset.node===id && document.body.dataset.phase==='ready';
      },spec.scene+':'+number,{timeout:40000});
    };
    const screenshot = async label => {
      const file=config.outputRoot+'/'+spec.id+'-'+label+'.png';
      const before=await child().evaluate(()=>({wall:performance.now(),render:window.__assembledReview?.renderCount}));
      await page.frameLocator('iframe').locator('#viewport').screenshot({path:file,animations:'allow'});
      const after=await child().evaluate(()=>({wall:performance.now(),render:window.__assembledReview?.renderCount,
        rect:(()=>{const b=document.querySelector('#viewport').getBoundingClientRect();return {width:b.width,height:b.height};})()}));
      shots.push({label,file,before,after,binding:'Locator screenshot has a request interval, not an exact applied-render assertion'});
    };
    try {
      await page.setViewportSize({width:1280,height:1000});
      await page.addInitScript({content:'('+config.instrumentationSource+')('+JSON.stringify({...spec,
        targetNode:spec.scene+':'+spec.target,maxTraceFrames:2400})+');'});
      const programResponse=page.waitForResponse(response=>new URL(response.url()).pathname==='/program',{timeout:30000});
      // Preserve the original rejection for the awaited branch without an
      // unhandled-rejection race if navigation itself fails first.
      programResponse.catch(()=>{});
      await page.goto(config.baseURL+'/?scene='+spec.scene+'&node='+spec.route[0]+'&nativePreview='+encodeURIComponent(spec.id),
        {waitUntil:'domcontentloaded',timeout:30000});
      // Explicit root-approved QA fixture, not a hidden template assumption or
      // result-driven camera fit. Only the parent iframe outer box is assigned.
      fixture=await page.evaluate(()=>{
        const iframe=document.querySelector('iframe');if(!iframe)throw Error('Missing fixture iframe');
        const before={width:iframe.getBoundingClientRect().width,height:iframe.getBoundingClientRect().height};
        iframe.style.width='480px';iframe.style.height='856px';
        return {preset:{parent:[1280,1000],iframe:[480,856]},before,wall:performance.now()};
      });
      const response=await programResponse;
      if(response.status()!==200)throw Error('Program HTTP '+response.status());
      const programText=await response.text();compiled=JSON.parse(programText);
      const actualSha=Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(programText))).toString('hex');
      if(actualSha!==spec.programSha256 || compiled.review_only_overrides?.packetSha256!==spec.packetSha256)
        throw Error('Actual program differs from frozen preflight compilation');
      await waitReady(spec.route[0]);
      fixture.measured = await child().evaluate(async ()=>{
        const rect = element=>{const b=element.getBoundingClientRect();return {left:b.left,top:b.top,width:b.width,height:b.height};};
        let prior=null,stable=0;
        for(let n=0;n<120;n++){
          await new Promise(requestAnimationFrame);
          const now={frame:rect(window.frameElement),viewport:rect(document.querySelector('#viewport')),
            actor:{width:document.querySelector('#actor').width,height:document.querySelector('#actor').height,
              css:rect(document.querySelector('#actor'))}};
          if(JSON.stringify(now)===JSON.stringify(prior))stable++;else stable=0;
          if(stable>=3){
            if(Math.abs(now.frame.width-480)>.1||Math.abs(now.frame.height-856)>.1)throw Error('Outer iframe fixture mismatch');
            if(Math.abs(now.viewport.width/now.viewport.height-9/16)>.001)throw Error('Actual stage aspect mismatch');
            const qa=window.__assembledReview;if(!qa?.installed||!qa.clock)throw Error('Missing read-only model/clock observer');
            qa.fixtureReady=true;return {...now,wall:performance.now(),clock:qa.clock.snapshot(),stableConsecutiveFrames:stable};
          }
          prior=now;
        }
        throw Error('QA fixture did not stabilize');
      });
      await child().waitForFunction(()=>{
        const qa=window.__assembledReview;return qa.renders.length>=3&&qa.hud&&qa.clock.snapshot().previewRate===1;
      },null,{timeout:10000});
      const setup=await child().evaluate(()=>({errors:window.__assembledReview.errors,
        count:window.__assembledReview.instances.length,staticCaptured:!!window.__assembledReview.staticCapture}));
      if(setup.errors.length||setup.count!==1)throw Error('Predecessor observer/setup mismatch: '+JSON.stringify(setup));
      await screenshot('before');
      cdp=await context.newCDPSession(page);
      cdp.on('Page.screencastFrame',event=>{
        cdp.send('Page.screencastFrameAck',{sessionId:event.sessionId}).catch(error=>errors.push(String(error)));
        if(pixelFrames.length>=300){
          droppedFrames++;overflow=true;
          if(streamActive){streamActive=false;cdp.send('Page.stopScreencast').catch(error=>errors.push(String(error)));}
          return;
        }
        pixelFrames.push({index:pixelFrames.length,mimeType:'image/jpeg',data:event.data,metadata:event.metadata,
          binding:'Offline read parent pixel HUD; bind exact render/applied IDs. Host receipt time is not a frame match.'});
      });
      await cdp.send('Page.startScreencast',{format:'jpeg',quality:80,maxWidth:1280,maxHeight:1000,everyNthFrame:2});streamActive=true;
      await page.locator('#advance').click();await waitReady(spec.target);
      // Observe natural body entry and at least one second of the2s entry's
      // hold without seeking, changing speed, adding script Wait or forcing a
      // model parameter. The real elapsed game clock is preserved independently.
      await child().waitForFunction(target=>{
        const qa=window.__assembledReview;
        const start=qa.timing.find(row=>row.node===target&&row.stage==='motion_ready');
        return !!start?.clock&&qa.clock.now()-start.clock.gameSeconds>=3;
      },spec.scene+':'+spec.target,{timeout:15000});
      await child().evaluate(()=>{window.__assembledReview.staticCaptureRequested=true;});
      await child().waitForFunction(()=>!!window.__assembledReview.staticCapture,null,{timeout:5000});
      await screenshot('held');
      await page.locator('#advance').click();await waitReady(spec.route[2]);
      if(streamActive){await cdp.send('Page.stopScreencast');streamActive=false;}
      await screenshot('successor');
      const verdict=await child().evaluate(({model,target})=>{
        const qa=window.__assembledReview;
        return {errors:qa.errors,targetCreatedAfterPreset:qa.lifecycle.filter(row=>row.event==='created'&&row.sourceURL.includes('/ac_'+model+'/')).every(row=>row.fixtureReady),
          targetCreatedCount:qa.lifecycle.filter(row=>row.event==='created'&&row.sourceURL.includes('/ac_'+model+'/')).length,
          targetStillAttached:qa.instances.filter(row=>row.sourceURL.includes('/ac_'+model+'/')&&!row.destroyed&&row.model.parent).length,
          traceOverflow:qa.traceOverflow,phase2End:qa.timing.filter(row=>row.stage==='phase_2_end').map(row=>row.node)};
      },{model:spec.model,target:spec.target});
      if(verdict.errors.length||!verdict.targetCreatedAfterPreset||verdict.targetCreatedCount!==1||verdict.targetStillAttached!==0)
        throw Error('Same-instance/lifecycle/geometry audit needs review: '+JSON.stringify(verdict));
      if(http.some(row=>new URL(row.url).pathname!=='/favicon.ico')||errors.length||logs.some(row=>row.text.startsWith('STORY_PLAYER_ERROR')))
        throw Error('Actual player/request errors retained');
    } catch(error) { failure={name:error.name,message:String(error.message),stack:String(error.stack).slice(0,2500)};stopped=true; }
    finally {
      if(cdp){if(streamActive)await cdp.send('Page.stopScreencast').catch(()=>{});await cdp.detach().catch(()=>{});}
      try {
        trace=await child().evaluate(()=>{
          const qa=window.__assembledReview;if(!qa)return null;
          return {id:qa.id,documentId:qa.documentId,errors:qa.errors,installed:qa.installed,
            applied:qa.applied,renders:qa.renders,timing:qa.timing,lifecycle:qa.lifecycle,traceOverflow:qa.traceOverflow,
            observerSkips:qa.observerSkips,
            staticCapture:qa.staticCapture,instances:qa.instances.map(row=>({instance:row.instance,sourceURL:row.sourceURL,
              destroyed:row.destroyed,attached:!!row.model.parent,visible:row.model.visible,lastApplied:row.lastApplied?.sequence||null}))};
        });
      }catch(error){errors.push('Trace retrieval: '+String(error));failure??={message:String(error)};stopped=true;}
      const name=spec.id+'-raw.json.gz';
      const payload={id:spec.id,url:config.baseURL+'/?scene='+spec.scene+'&node='+spec.route[0]+'&nativePreview='+spec.id,
        spec,startedHostWall:started,finishedHostWall:Date.now(),failure,fixture,trace,pixelFrames,overflow,droppedFrames,
        screenshots:shots,logs,pageErrors:errors,http,resourceResponses:network,
        actualCompiledNodes:compiled?.nodes.filter(row=>spec.route.map(n=>spec.scene+':'+n).includes(row.id)),
        expectedResourceIdentity:config.servedResources.filter(row=>row.model===spec.model),
        imageDataDestination:'disk-only gzip; never returned to CLI',
        pending:['Offline exact pixel HUD-to-applied binding','Earliest positive-alpha PNG/JPEG evidence; numbers alone do not pass',
          'Full active/held/successor pixels and same-instance comparison','Geometry measured from each actual crop boundary; no camera fitting',
          ...(overflow?['Compositor cap reached; missing later pixels remain pending']:[])]};
      try { await savePayload(page,name,payload); }
      catch(error){failure??={message:'Raw evidence save failed: '+String(error)};stopped=true;}
      summaries.push({id:spec.id,failure,rawFile:config.outputRoot+'/'+name,pixelFrames:pixelFrames.length,
        overflow,droppedFrames,traceFrames:trace?.renders.length||0,staticActorImageSavedInRaw:!!trace?.staticCapture,
        visualAccepted:false,partial:!!failure});
      page.off('console',onConsole);page.off('pageerror',onError);page.off('requestfailed',onRequestFailed);page.off('response',onResponse);
      if(!page.isClosed())await page.close();
      if(context.pages().length!==0)throw Error('Case Page did not close');
    }
  }
  return {cases:summaries,stoppedOnFirstFailure:stopped,unrunCaseIds:config.cases.slice(summaries.length).map(row=>row.id),
    browserPagesRemaining:context.pages().length,visualAccepted:false,needsImmediateOwnerBrowserClose:true};
}
