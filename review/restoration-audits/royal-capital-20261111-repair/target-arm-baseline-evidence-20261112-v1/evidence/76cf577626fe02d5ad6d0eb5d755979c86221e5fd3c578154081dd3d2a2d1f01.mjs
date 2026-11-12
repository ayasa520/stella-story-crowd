// Compile only the canonical website source with explicit fresh registry bytes.
// This file is a new ARM authoring artifact, not an execution release. Node/tsx
// must be selected by the reviewed absolute host toolchain; no sibling registry,
// legacy Site path, PATH-selected executable or desktop loader is a fallback.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
import {pathToFileURL} from 'node:url';

const args=process.argv.slice(2);
if(args.length!==7)throw new Error('Explicit ROOT SCENE SCENARIO PREVIEW CANONICAL_SITE REGISTRY REGISTRY_SHA256 required');
const [root,scene,scenario,nativePreview,siteRoot,registryPath,registrySha256]=args;
const expectedRoot='/home/rikka/Projects/stella';
const canonical=path.join(expectedRoot,'artifacts/stella-site-repair-source/.sites-checkout');
const armParent=path.join(expectedRoot,'artifacts/stella-arm-runtime');
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const inside=(parent,candidate)=>candidate.startsWith(parent+path.sep);
if(root!==expectedRoot||fs.realpathSync(root)!==expectedRoot||siteRoot!==canonical||fs.realpathSync(siteRoot)!==canonical)
  throw new Error('Only the explicit workspace and canonical Site are permitted');
if(process.execPath!=='/usr/bin/node'||process.platform!=='linux'||process.arch!=='arm64'||os.getPriority()!==19)
  throw new Error('Compiler requires absolute /usr/bin/node on nice19 Linux ARM64');
const cpuLine=fs.readFileSync('/proc/self/status','utf8').split('\n').find(line=>line.startsWith('Cpus_allowed_list:'));
if(!cpuLine||!['0-1','0,1'].includes(cpuLine.split(':')[1].trim()))throw new Error('Compiler must inherit CPUs0,1');
if(!/^\d+$/.test(scene)||!Number.isSafeInteger(Number(scene))||Number(scene)<=0||
    (scenario&&(!/^\d+$/.test(scenario)||!Number.isSafeInteger(Number(scenario))||Number(scenario)<=0)))
  throw new Error('Invalid explicit scene or scenario');
if(!path.isAbsolute(registryPath)||!inside(armParent,fs.realpathSync(registryPath))||!/^[a-f0-9]{64}$/.test(registrySha256))
  throw new Error('A fresh ARM registry path and exact SHA256 are required');

// Reject undecodable or altered text before JSON parsing, without replacement
// characters, normalization or a second read of a potentially changing file.
// Python uses the separately copied, evidence-backed UTF8 roundtrip reader.
const parseBytes=(raw,context)=>{
  const text=raw.toString('utf8');
  if(!Buffer.from(text,'utf8').equals(raw))throw new Error('UTF8 byte roundtrip rejected: '+context);
  return JSON.parse(text);
};
const registryRaw=fs.readFileSync(registryPath);
if(hash(registryRaw)!==registrySha256)throw new Error('Fresh registry bytes changed');
const scopes=parseBytes(registryRaw,registryPath);
if(!Array.isArray(scopes))throw new Error('Fresh registry must retain the list schema');
for(const scope of scopes){
  if(!Number.isSafeInteger(scope.sceneId)||!['allowedStarts','allowedTargets','allowedFields','exampleIds'].every(key=>Array.isArray(scope[key]))||
      typeof scope.packet!=='string'||path.isAbsolute(scope.packet)||!/^[a-f0-9]{64}$/.test(scope.sha256))
    throw new Error('Malformed bounded registry entry');
  const packetRoot=path.join(root,'data/native_recovery/royal-capital-20261110/repair-20261111');
  if(!inside(packetRoot,fs.realpathSync(path.resolve(packetRoot,scope.packet))))throw new Error('Registry packet escapes repair evidence');
}
const read=name=>parseBytes(fs.readFileSync(path.join(root,'story_crowd_data',name)),name);
const manifest=read('manifest.json'),assets=read('assets/catalog.json');
const sources=manifest.scenes.map(entry=>({entry,document:read(entry.path),review:read(entry.reviewPath)}));
let override=null;
if(nativePreview){
  // The original guarded override body is retained verbatim below. Only the
  // registry source changed: it is now an explicit hash-bound input loaded
  // above, never an implicit historical sibling with eight desktop scopes.
  const scope=scopes.find(row=>row.sceneId===Number(scene)&&row.allowedStarts.includes(Number(scenario))&&row.exampleIds.includes(nativePreview));
  if(!scope)throw new Error('Memory preview target is outside the bounded review scope');
  const evidence=path.join(root,'data/native_recovery/royal-capital-20261110/repair-20261111',scope.packet);
  const evidenceRaw=fs.readFileSync(evidence);
  if(createHash('sha256').update(evidenceRaw).digest('hex')!==scope.sha256)throw new Error('Approved memory proposal bytes changed');
  const packet=JSON.parse(evidenceRaw);
  // Visible-reproduction proposals can depend on an unchanged whole scene,
  // its neighbouring rows, the native projection inventory and the selected
  // renderer. Bind those exact bytes before applying any private override.
  // This is a read-only evidence gate, never an extension of install scope.
  const guardReceipts=[...(packet.guardReceipts||[]),...(packet.sourceProposal?[packet.sourceProposal]:[])];
  for(const receipt of guardReceipts){
    const guardedPath=path.resolve(root,receipt.path);
    if(!guardedPath.startsWith(path.resolve(root)+path.sep))throw new Error('Memory review receipt escapes the workspace');
    const raw=fs.readFileSync(guardedPath);
    if(createHash('sha256').update(raw).digest('hex')!==receipt.sha256)throw new Error('Memory review source receipt changed: '+receipt.path);
  }
  const example=packet.examples.find(row=>row.id===nativePreview);
  if(!example)throw new Error('Unknown original-layout review example');
  const source=sources.find(row=>row.entry.id===Number(scene));
  if(example.changes){
    // Conditional facial-layer evidence needs the real predecessor as well
    // as the target. Apply both immutable, guarded rows in this subprocess's
    // private source objects so normal production compilation owns inheritance.
    for(const change of example.changes){
      if(!scope.allowedTargets.includes(change.scenarioId))throw new Error('Memory proposal target exceeds its approved scope');
      const row=source.document.scenario_list.find(row=>row.scenario_id===change.scenarioId);
      if(!row)throw new Error('Memory proposal target no longer exists');
      // Raw commands are three ordered JSON phases. Compare arrays/objects
      // structurally as well as scalar fields; reference equality would reject
      // an unchanged parsed array and weaken the proposal's explicit guards.
      for(const [key,value]of Object.entries(change.expected))if(!isDeepStrictEqual(row[key],value))throw new Error('Memory preview precondition changed');
      for(const [key,value]of Object.entries(change.fields)){
        if(!scope.allowedFields.includes(key))throw new Error('Unsupported memory preview field');
        row[key]=value;
      }
    }
  }else{
    if(!scope.allowedTargets.includes(Number(scenario))||!['character','motion'].every(key=>scope.allowedFields.includes(key)))throw new Error('Legacy memory proposal exceeds its approved scope');
    const row=source.document.scenario_list.find(row=>row.scenario_id===Number(scenario));
    row.character=example.character;row.motion=example.motion;
  }
  override={exampleId:example.id,evidence,packetSha256:scope.sha256,persisted:false,originalScriptRecovered:false};
}

// Production owns sparse fields, inherited values and route compilation. No
// local replacement compiler or geometry/motion policy is introduced here.
const {compilePreview}=await import(pathToFileURL(path.join(siteRoot,'lib/preview.ts')).href);
const program=compilePreview(Number(scene),sources,manifest,assets,scenario?Number(scenario):undefined);
if(override)program.review_only_overrides=override;
process.stdout.write(JSON.stringify(program));
