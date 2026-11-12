async page => {
  const frame=page.frames().find(value=>value.url().includes('/player/player.html'));
  if(!frame)throw Error('Normal player frame missing before transport Stop');
  await frame.locator('#stop').evaluate(button=>button.click());
  await frame.waitForFunction(()=>document.body.dataset.phase==='stopped');
  return {status:'normal_transport_stopped_after_recording',
    state:await frame.evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase}))};
}
