// Inspect the already captured JSON only. This audit imports no application,
// compiler, loader or browser code and performs no network request or launch.
import fs from 'node:fs';
import crypto from 'node:crypto';
import os from 'node:os';
const [programPath,stdoutPath,targetsPath,outputPath]=process.argv.slice(2);
if(process.execPath!=='/usr/bin/node'||process.arch!=='arm64'||os.getPriority()!==19)
  throw Error('Readback requires the installed ARM Node at nice19');
const allowed=fs.readFileSync('/proc/self/status','utf8').split('\n').find(line=>line.startsWith('Cpus_allowed_list:'));
if(!allowed||!['0-1','0,1'].includes(allowed.split(':')[1].trim()))throw Error('Readback affinity differs');
const raw=fs.readFileSync(programPath),stdout=fs.readFileSync(stdoutPath);
if(!raw.equals(stdout))throw Error('HTTP body and actual compiler stdout differ');
const program=JSON.parse(raw.toString('utf8')),targets=JSON.parse(fs.readFileSync(targetsPath,'utf8'));
if(program.start!=='10450054:4'||program.nodes.length!==5599||program.edges.length!==5845||
   Object.hasOwn(program,'review_only_overrides'))throw Error('Actual normal program scope differs');
const nodes=new Map(program.nodes.map(node=>[node.id,node]));
if(nodes.size!==5599)throw Error('Compiled node IDs are not unique');
const checked=targets.map(target=>{
  const node=nodes.get(target.id);
  if(!node||node.model!==target.expectedModel)throw Error('Actual Node parsed model differs: '+target.id);
  return {id:node.id,model:node.model};
});
const p30=program.nodes.filter(node=>node.scene_id==='scene:10450054'&&node.model).map(node=>({id:node.id,model:node.model}));
if(checked.length!==45||p30.length!==16)throw Error('Actual affected binding counts differ');
fs.writeFileSync(outputPath,JSON.stringify({status:'captured_JSON_readback_only',nodeExecutable:process.execPath,
  nodeVersion:process.version,architecture:process.arch,nice:os.getPriority(),cpuAffinity:[0,1],
  programSha256:crypto.createHash('sha256').update(raw).digest('hex'),programBytes:raw.length,
  actualCompilerStdoutEqualsHTTPBody:true,start:program.start,nodeCount:program.nodes.length,
  edgeCount:program.edges.length,privateOverridePresent:false,checkedCharacterBindings:checked,
  p30CharacterBindings:p30,warnings:program.warnings,applicationOrCompilerExecuted:false,
  browserStarted:false,newRestorationVisits:0},null,2)+'\n',{flag:'wx'});
