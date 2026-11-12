(function compileMusic(value,fadeDefault){
  if(!value.trim())return {action:"inherit",resource:"",fade:fadeDefault,restart:false};
  // BGM accepts the resource name with optional CSV quoting, unlike command
  // lines. Pilot resource IDs contain no commas, and empty option slots remain
  // defaults; invalid booleans are rejected rather than coerced to truthy text.
  const parts=value.split(",").map(part=>part.trim().replace(/^"(.*)"$/,"$1"));
  if(parts.length>3||!parts[0])throw new Error("BGM 格式应为：曲目,渐变秒数,是否重播");
  const fade=parts[1]?Number(parts[1]):fadeDefault,restart=parts[2]?JSON.parse(parts[2]):false;
  if(!Number.isFinite(fade)||fade<0||typeof restart!=="boolean")throw new Error("BGM 渐变时间需为非负数，重播需为 true 或 false");
  return {action:parts[0]==="STOP"?"stop":"play",resource:parts[0]==="STOP"?"":parts[0],fade,restart};
})
