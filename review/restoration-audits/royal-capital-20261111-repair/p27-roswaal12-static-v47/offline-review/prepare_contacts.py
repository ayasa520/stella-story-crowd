"""Create bounded offline inspection derivatives from saved original bytes.

No source image is changed. Actual compositor crops use logged parent-space
game bounds, rounded outward to complete pixel cells. Contact thumbnails are
navigation aids, not geometry measurements or exact applied-frame bindings;
the full images and raw HUD remain the authoritative evidence. No camera,
model, renderer, animation or source recording is run here.
"""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
R=RUN.parents[2]


def rec(path):
    raw=path.read_bytes();return {'file':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def sheets(name, rows, crop=None):
    result=[]
    for start in range(0,len(rows),36):
        sheet=Image.new('RGB',(960,1848),'#252525');draw=ImageDraw.Draw(sheet)
        for offset,row in enumerate(rows[start:start+36]):
            source=Path(row['file']);image=Image.open(source).convert('RGB')
            if crop:image=image.crop(crop)
            image.thumbnail((160,285),Image.Resampling.LANCZOS)
            x=(offset%6)*160;y=(offset//6)*308
            sheet.paste(image,(x,y));draw.text((x+2,y+287),row['label'],fill='white')
        target=HERE/f'{name}-{start//36+1:02d}.jpg';sheet.save(target,quality=88)
        result.append({**rec(target),'sourceRange':[start,min(start+35,len(rows)-1)],'thumbnailOnly':True})
    return result


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    index=json.loads((RUN/'pixel-index.json').read_text());contacts=[];facts=[]
    for case in index['cases']:
        payload=json.loads(gzip.decompress(Path(case['raw']['file']).read_bytes()));trace=payload['trace']
        identity=case['id'];target=payload['spec']['model'];node=str(payload['spec']['scene'])+':'+str(payload['spec']['target'])
        target_renders=[row for row in trace['renders'] if any('/ac_'+target+'/' in model['sourceURL'] for model in row['models'])]
        positive=[row for row in target_renders if row['node']==node and row['cardOpacity']>0]
        entry=[row for row in positive if row['cardOpacity']<1]
        native={row['sequence']:row for row in trace['applied']}
        paired=[]
        for row in entry[:12]:
            model=next(model for model in row['models'] if '/ac_'+target+'/' in model['sourceURL'])
            applied=native.get(model['lastApplied'])
            paired.append({'render':row['render'],'hudKey':row['hudKey'],'alpha':row['cardOpacity'],
                'wall':row['wall'],'game':row['clock'],'model':model,
                'appliedSequence':model['lastApplied'],'sameGameFrame':model['sameGameFrame'],
                'appliedPresent':applied is not None})
        static=trace['staticCapture'];sample=native[static['lastApplied']]
        values=dict(zip(sample['parameterIds'],sample['values']))
        facts.append({'id':identity,'raw':rec(Path(case['raw']['file'])),'firstTargetPositiveNumeric':paired[0] if paired else None,
            'targetEntryNumericSamples':paired,'staticRender':static['render'],'staticHudKey':static['hudKey'],
            'staticApplied':{key:value for key,value in values.items() if key.startswith(('ParamAngle','ParamBody','ParamArm','ParamForeArm','ParamEye','ParamBrow','ParamMouth'))},
            'staticModel':next(model for row in trace['renders'] if row['render']==static['render'] for model in row['models'] if model['instance']==static['instance']),
            'geometry':next(row for row in trace['renders'] if row['render']==static['render']),
            'numericValuesAreNotPixelAcceptance':True})
        if identity.startswith('n9-'):
            box=trace['renders'][0]['parentLayout']['game'];crop=(math.floor(box['left']),math.floor(box['top']),math.ceil(box['right']),math.ceil(box['bottom']))
            rows=[{'file':row['file'],'label':f'pixel {row["index"]:03d}'} for row in case['compositorFrames']]
            contacts.append({'id':identity,'cropOutwardParentPixels':crop,'sheets':sheets('normal02' if 'normal02' in identity else 'normal',rows,crop)})
    source=R/'visual-high/butler-projection-three-frame-v1/memory-proposals-v1/source-entry-s10150004-n9-v1/source-frame-index.json'
    source_index=json.loads(source.read_text());assert len(source_index['frames'])==120
    source_rows=[{'file':row['file'],'label':f'src {row["frameIndex"]:03d} {row["decodedPTSSeconds"]:.3f}'} for row in source_index['frames']]
    contacts.append({'id':'original-source120','sourceIndex':rec(source),'sheets':sheets('source',source_rows)})
    output=HERE/'inspection-index.json'
    with output.open('x') as stream:json.dump({'contacts':contacts,'numericFacts':facts},stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'index':rec(output),'contactSheets':sum(len(row['sheets']) for row in contacts),
        'cases':[{'id':row['id'],'firstNumeric':row['firstTargetPositiveNumeric']['hudKey'] if row['firstTargetPositiveNumeric'] else None} for row in facts]}))


if __name__=='__main__':main()
