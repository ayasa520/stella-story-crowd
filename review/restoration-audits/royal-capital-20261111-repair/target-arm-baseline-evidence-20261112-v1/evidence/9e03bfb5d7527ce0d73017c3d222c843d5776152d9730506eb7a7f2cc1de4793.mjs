// Compile installed native documents with the production website compiler.
// This read-only evidence adapter does not recreate script semantics or fill
// sparse fields; every route and inherited value comes from compilePreview.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
import {pathToFileURL} from 'node:url';
const [root,scene,scenario,nativePreview,siteRoot]=process.argv.slice(2);
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'story_crowd_data',name),'utf8'));
const manifest=read('manifest.json'),assets=read('assets/catalog.json');
const sources=manifest.scenes.map(entry=>({entry,document:read(entry.path),review:read(entry.reviewPath)}));
let override=null;
if(nativePreview){
  // Both the HTTP adapter and this compiler use one explicit review registry.
  // A named proposal is bound to its exact bytes, start, target rows and fields;
  // neither an arbitrary file nor a later edited proposal gains approval merely
  // by reusing an example ID. Changes exist only in these private source objects.
  const scopes=JSON.parse(fs.readFileSync(new URL('./approved-memory-previews.json',import.meta.url),'utf8'));
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
// A release checkout may intentionally omit unpublished workspace prototypes.
// Compile that exact selected Site source while keeping installed data and
// bounded in-memory evidence under the same independent restoration root.
const {compilePreview}=await import(pathToFileURL(path.join(siteRoot||path.join(root,'story_crowd'),'lib/preview.ts')).href);
const program=compilePreview(Number(scene),sources,manifest,assets,scenario?Number(scenario):undefined);
if(override)program.review_only_overrides=override;
process.stdout.write(JSON.stringify(program));
