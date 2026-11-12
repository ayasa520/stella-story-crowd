async page => {
  const output='/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/p30-ruined-shop-background-20261112-v1';
  const events=[],logs=[],responses=[];
  page.on('console',m=>{const t=m.text();if(/^(STORY_SCRIPT_BACKGROUND|STORY_ACTOR_LIGHTING|STORY_BACKGROUND_PROJECTION) /.test(t))logs.push(t);});
  page.on('response',r=>{if(r.url().includes('/background/'))responses.push({url:r.url(),status:r.status()});});
  const player=()=>page.frames().find(f=>f.url().includes('/player/player.html'));
  const ready=async n=>{await player().waitForFunction(n=>document.body.dataset.node==='10450056:'+n&&document.body.dataset.phase==='ready',n,{timeout:20000});events.push(await player().evaluate(()=>({node:document.body.dataset.node,phase:document.body.dataset.phase,wall:performance.now()})));};
  await ready(27);await page.locator('#advance').click();await ready(28);
  await page.screenshot({path:output+'/node28-ruined-shop.png'});
  await page.locator('#advance').click();await ready(29);
  await page.screenshot({path:output+'/node29-inherited-ruined-shop.png'});
  const backgrounds=logs.filter(t=>t.startsWith('STORY_SCRIPT_BACKGROUND ')).map(t=>JSON.parse(t.slice('STORY_SCRIPT_BACKGROUND '.length)));
  for(const n of[28,29])if(!backgrounds.some(b=>b.node==='10450056:'+n&&b.effective==='bg/bg046c_stealshop'))throw Error('Background not applied/inherited at'+n);
  if(!responses.some(r=>r.status===200&&decodeURIComponent(r.url()).includes('bg/bg046c_stealshop')))throw Error('Actual background image response missing');
  return {status:'ordinary_ruined_shop_27_28_29_passed',events,backgrounds,responses,logs,previewOverrides:false,actingAccepted:false};
}
