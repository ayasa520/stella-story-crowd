"""Decode disk-only evidence after verified browser closure; do not select a visual match.

PNG and framebuffer equality is a byte comparison after WebGL row reversal only.
Compositor images retain their exact JPEG bytes and real dimensions. A human
image reviewer must read the rolling HUD and bind its render/frame/instance/
applied tuple; arrival time or a matching host timestamp cannot sign that gate.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
from PIL import Image


def digest(raw):return hashlib.sha256(raw).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and sorted(os.sched_getaffinity(0))==[22,23]
    lifecycle=json.loads((args.output/"browser-lifecycle.json").read_bytes())
    assert lifecycle["taskCanaryAndCliOsZero"] and lifecycle["cliZero"],"Close before decoding pixels"
    destination=args.output/"pixels";destination.mkdir()
    index=dict(status="decoded_after_browser_close_visual_review_pending",cases=[],sameFrameStageMatchAccepted=False)
    for source in sorted(args.output.glob("*-raw.json.gz")):
        payload=json.loads(gzip.decompress(source.read_bytes()));folder=destination/payload["id"];folder.mkdir()
        case=dict(id=payload["id"],raw=dict(path=str(source),bytes=source.stat().st_size,sha256=digest(source.read_bytes())),captures=[],compositorWindows=[])
        for number,capture in enumerate((payload.get("trace") or {}).get("captures",[])):
            metadata={k:v for k,v in capture.items() if k not in ["actorPng","rawRgbaBase64"]}
            if "actorPng" in capture:
                raw=base64.b64decode(capture["actorPng"].split(",",1)[1],validate=True)
                rgba=base64.b64decode(capture["rawRgbaBase64"],validate=True)
                png=folder/f"capture-{number:02}-actor.png";binary=folder/f"capture-{number:02}-actual-bottom-up.rgba"
                png.write_bytes(raw);binary.write_bytes(rgba)
                image=Image.open(io.BytesIO(raw));image.load();width,height=image.size
                assert (width,height)==(capture["width"],capture["height"]) and len(rgba)==width*height*4
                stride=width*4;top_down=b"".join(rgba[start:start+stride] for start in range((height-1)*stride,-1,-stride))
                decoded=image.convert("RGBA").tobytes();equal=decoded==top_down
                metadata["actorPng"]=dict(path=str(png),bytes=len(raw),sha256=digest(raw),width=width,height=height)
                metadata["actualRgba"]=dict(path=str(binary),bytes=len(rgba),sha256=digest(rgba),rowOrder="bottom-up")
                metadata["pngEqualsActualRgbaAfterRowReversalOnly"]=equal
                metadata["pixelEqualityMismatchBytes"]=sum(a!=b for a,b in zip(decoded,top_down)) if not equal else 0
                metadata["identityAccepted"]=False
            case["captures"].append(metadata)
        for window_number,window in enumerate(payload.get("compositorWindows",[])):
            record={k:v for k,v in window.items() if k!="frames"};record["frames"]=[]
            for frame in window["frames"]:
                raw=base64.b64decode(frame["data"],validate=True);path=folder/f"window-{window_number:02}-frame-{frame['index']:02}.jpg";path.write_bytes(raw)
                image=Image.open(io.BytesIO(raw));width,height=image.size
                record["frames"].append(dict(index=frame["index"],path=str(path),bytes=len(raw),sha256=digest(raw),
                    width=width,height=height,metadata=frame["metadata"],hudReadAndExactFrameMatchPending=True))
            case["compositorWindows"].append(record)
        index["cases"].append(case)
    path=args.output/"pixel-index.json"
    with path.open("x") as stream:json.dump(index,stream,ensure_ascii=False,indent=2);stream.write("\n")
    print(json.dumps(dict(index=str(path),sha256=digest(path.read_bytes()),cases=len(index["cases"]),visualAccepted=False)))


if __name__=="__main__":main()
