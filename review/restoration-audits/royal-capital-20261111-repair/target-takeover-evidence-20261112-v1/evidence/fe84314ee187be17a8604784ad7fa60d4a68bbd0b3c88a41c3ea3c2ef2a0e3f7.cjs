// Parse only local evidence/current JSON with the installed ARM Node runtime.
// This does not import any transferred dependency, compiler or application.
// A parse error preserves raw identity and exact position/code-unit evidence;
// it does not imply that the file, caller or environment caused the error.
const fs = require('node:fs');
const crypto = require('node:crypto');
const records = process.argv.slice(2).map(file => {
  const raw = fs.readFileSync(file), text = raw.toString('utf8');
  const record = {file, bytes:raw.length,
    sha256:crypto.createHash('sha256').update(raw).digest('hex')};
  try {
    const value = JSON.parse(text);
    return {...record, success:true, jsonKind:Array.isArray(value)?'array':typeof value,
      topLevelKeys:value && typeof value==='object'?Object.keys(value):[],
      changes:Array.isArray(value?.changes)?value.changes.length:null};
  } catch (error) {
    const position = /position (\d+)/.exec(error.message);
    const index = position?Number(position[1]):null;
    return {...record, success:false, error:{name:error.name,message:error.message,
      position:index,codeUnit:index===null?null:text.charCodeAt(index)}};
  }
});
process.stdout.write(JSON.stringify({runtime:process.version,platform:process.platform,
  architecture:process.arch,records}));
process.exitCode = records.every(record=>record.success)?0:1;
