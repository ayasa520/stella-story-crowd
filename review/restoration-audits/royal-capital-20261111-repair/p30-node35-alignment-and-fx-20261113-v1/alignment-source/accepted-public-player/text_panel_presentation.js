// Node-scoped text presentation is an authored rendering policy. It does not
// recover a native CSV field or interpret dialogue contents as layout markup.
// Keeping selection here leaves node transport, text reveal and NativeFont's
// existing layout/draw implementation independent of restoration exceptions.
export function textPanelRows(node,group,rows,settings){
  if(settings?.version!==1||!settings.nodes||typeof settings.nodes!=='object'||Array.isArray(settings.nodes))
    throw new Error('文字面板呈现配置无效');
  if(!Object.hasOwn(settings.nodes,node.id))return rows;
  const profile=settings.nodes[node.id],target=profile?.row;
  if(!profile||typeof profile.id!=='string'||!profile.id||!target||
    typeof target.path!=='string'||!Number.isInteger(target.id)||
    !Number.isInteger(target.expected_alignment)||target.expected_alignment<0||target.expected_alignment>0xffff||
    ![1,2,4].includes(target.horizontal_alignment))
    throw new Error('文字面板呈现配置无效：'+node.id);

  // An exact node key is necessary but insufficient: fail closed if an edit
  // changes this node's kind, speaker, selected panel or exported TMP row.
  // Never apply the source-reviewed policy to every narration or to a magic
  // word. Both Japanese and translated text use this same guarded panel.
  if(node.kind!==profile.kind||node.speaker!==profile.speaker||group!==profile.group)
    throw new Error('文字面板呈现条件已变化：'+node.id);
  const matches=rows.filter(row=>row.path===target.path);
  if(matches.length!==1||matches[0].type!=='text'||matches[0].id!==target.id||
    matches[0].alignment!==target.expected_alignment)
    throw new Error('原版文字面板布局已变化：'+node.id);
  const selected=matches[0];

  // Exported manifest rows are shared across nodes and languages. Copy only
  // this panel's selected text row, replacing the horizontal low byte while
  // retaining its vertical bits, rect, font, sizes, spacing and every other
  // field. Layout and draw receive the same returned rows; the shared asset
  // and every later unprofiled node therefore retain the original metadata.
  return rows.map(row=>row===selected?
    {...row,alignment:(row.alignment&~0xff)|target.horizontal_alignment}:row);
}

export function reportTextPanelLayout({node,language,panel,nativeRows,textRowName,settings},reported){
  const profile=Object.hasOwn(settings.nodes,node.id)?settings.nodes[node.id].id:'native-default';
  for(const row of panel.rows){
    if(row.type!=='text'||!row.path.endsWith('/'+textRowName))continue;
    const nativeRow=nativeRows.find(value=>value.path===row.path&&value.id===row.id);
    const layout=panel.layouts.get(row.path);
    const detail={node:node.id,language,profile,group:panel.group,rowPath:row.path,rowId:row.id,
      nativeAlignment:nativeRow.alignment,effectiveAlignment:row.alignment,rect:{...row.rect},
      size:layout.size,lineCount:layout.lines.length,
      lineWidths:layout.lines.map(line=>line.reduce((width,glyph)=>width+glyph.advance,0))};

    // Report prepared metadata, not sampled pixels or a native runtime setter.
    // Reuse measured advances from layout: no additional glyph measurement,
    // drawing, frame callback, clock read or reveal-state change is introduced.
    // Preparation can run twice before the same line is drawn. Keep only the
    // last signature per node/language/profile/row; scene.clear drops this
    // diagnostic memory, and changed metadata produces a fresh record.
    const key=JSON.stringify([node.id,language,profile,row.path]),signature=JSON.stringify(detail);
    if(reported.get(key)===signature)continue;
    reported.set(key,signature);console.info('STORY_TEXT_PANEL_LAYOUT',signature);
  }
}
