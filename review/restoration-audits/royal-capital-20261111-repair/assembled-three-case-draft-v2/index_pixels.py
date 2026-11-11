"""Extract exact saved image bytes only after CLI/OS-zero is established.

This creates an offline index, not a visual verdict. It neither edits images
nor re-renders a model, fits geometry, maps frames by host time, or reads any
image in root's context. JPEGs remain exact compositor bytes; the raw WebGL
RGBA buffer remains in its original bottom-up convention. Direct HUD/image
review is a separate, later task for the delegated image reviewer.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent


def record(path):
    raw=path.read_bytes()
    return {'file':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def image_size(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        width,height=struct.unpack_from('>II',raw,16);return {'width':width,'height':height,'format':'PNG'}
    if raw.startswith(b'\xff\xd8'):
        at=2
        while at<len(raw):
            assert raw[at]==255;at+=1
            while raw[at]==255:at+=1
            marker=raw[at];at+=1
            if marker in [0xD8,0xD9] or 0xD0<=marker<=0xD7:continue
            length=int.from_bytes(raw[at:at+2],'big')
            if marker in [0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF]:
                height,width=struct.unpack_from('>HH',raw,at+3);return {'width':width,'height':height,'format':'JPEG'}
            assert marker!=0xDA, 'JPEG reached scan before size header'
            at+=length
    raise ValueError('Unsupported or incomplete saved image header')


def save(path, raw):
    with path.open('xb') as stream:stream.write(raw)
    return record(path)


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve();assert output.is_relative_to(HERE)
    lifecycle=json.loads((output/'browser-lifecycle.json').read_text())
    assert lifecycle['osZero'] and lifecycle['cliZero'], 'Never process image payloads while the browser is alive'
    destination=output/'pixels';destination.mkdir()
    cases=[]
    for path in sorted(output.glob('*-raw.json.gz')):
        payload=json.loads(gzip.decompress(path.read_bytes()));identity=payload['id']
        assert '/' not in identity and '\\' not in identity
        target=destination/identity;target.mkdir();frames=[]
        assert len(payload['pixelFrames'])<=300
        for row in payload['pixelFrames']:
            raw=base64.b64decode(row['data'],validate=True);image=target/f"compositor-{row['index']:03d}.jpg"
            frames.append({**save(image,raw),**image_size(raw),'index':row['index'],'cdpMetadata':row['metadata'],
                'exactRenderBinding':'pending_direct_read_of_pixel_HUD_then_match_trace_renders_and_applied',
                'hostTimeBindingUsed':False})
        static=(payload.get('trace') or {}).get('staticCapture');static_index=None
        if static:
            prefix='data:image/png;base64,';assert static['actorPng'].startswith(prefix)
            raw=base64.b64decode(static['actorPng'][len(prefix):],validate=True);size=image_size(raw)
            assert size['width']==static['width'] and size['height']==static['height']
            static_index={**save(target/'actual-actor.png',raw),**size,
                'render':static['render'],'hudKey':static['hudKey'],'instance':static['instance'],
                'lastApplied':static['lastApplied'],'gameFrame':static['gameFrame'],
                'capturePoint':static['capturePoint'],'stageFitOrTransformChanges':False}
            if 'rawRgbaBase64' in static:
                rgba=base64.b64decode(static['rawRgbaBase64'],validate=True)
                assert len(rgba)==static['width']*static['height']*4
                static_index['rawRGBA']={**save(target/'actual-actor-bottom-up.rgba',rgba),
                    'width':static['width'],'height':static['height'],'channels':4,
                    'convention':static['rawRgbaConvention'],'convertedOrUnpremultiplied':False}
        shots=[]
        for shot in payload['screenshots']:
            source=Path(shot['file']).resolve();assert source.is_relative_to(output)
            raw=source.read_bytes();shots.append({**record(source),**image_size(raw),'requestInterval':{
                'before':shot['before'],'after':shot['after']},'exactAppliedFrameClaim':False})
        renders=(payload.get('trace') or {}).get('renders',[])
        positive=[row for row in renders if row['node']==str(payload['spec']['scene'])+':'+str(payload['spec']['target']) and 0<row['cardOpacity']<1]
        cases.append({'id':identity,'raw':record(path),'failure':payload['failure'],'compositorFrames':frames,
            'overflow':payload['overflow'],'droppedFrameEventsObserved':payload['droppedFrames'],
            'traceOverflow':(payload.get('trace') or {}).get('traceOverflow'),
            'numericEarliestPositiveRender':positive[0] if positive else None,
            'numericAlphaIsPixelEvidence':False,'staticActor':static_index,'stageScreenshots':shots,
            'fixture':payload['fixture'],'visualAccepted':False,
            'remainingReview':payload['pending'],'geometryRule':'Use actual image/crop bounds and logged frame/viewport/canvas/renderer rects; no unknown-camera fitting.'})
    index={'status':'offline_exact_byte_image_index_visual_review_pending','lifecycle':record(output/'browser-lifecycle.json'),
        'browserAndCliZeroBeforeImageExtraction':True,'cases':cases,'automaticRetry':False,'rootViewedImages':False}
    path=output/'pixel-index.json'
    with path.open('x') as stream:json.dump(index,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'index':record(path),'cases':len(cases),'visualAccepted':False}))


if __name__=='__main__':main()
