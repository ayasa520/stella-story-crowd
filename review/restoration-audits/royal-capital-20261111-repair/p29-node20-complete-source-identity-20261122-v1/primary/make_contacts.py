"""Create only complete, ordered contacts from the already closed P29 JPEGs.

This is image composition, not video decoding. Every original frame appears
once; source JPEGs and capture receipts are never modified. All contact images
are encoded in RAM and charged before writing to the shared16MiB review cap.
"""
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path('/home/rikka/Projects/stella')
A = ROOT / 'artifacts/stella-script-continuation-20261121'
HERE = Path(__file__).resolve().parent
INDEX = HERE / 'merged-frames-index.json'
CLOSURE = A / 'p29-node20-source-root-closure-v1.json'
OLD_SOURCE = A / 'p29-node18-source-capture-preparation-rootfalse-v1/run-1'
NEW_SOURCE = A / 'p29-node20-source-capture-preparation-rootfalse-v1/run-1'
PIL_DIR = ROOT / '.venv-video-ocr/lib/python3.11/site-packages/PIL'
CAP, RESERVE = 16 * 1024**2, 1024**2


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def record(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def main():
    need(sys.flags.isolated and sys.dont_write_bytecode, 'Use original venv -I -B')
    need(os.getpriority(os.PRIO_PROCESS, 0) == 19 and sorted(os.sched_getaffinity(0)) == [0, 1], 'Use nice19 CPU0,1')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        need(os.environ.get(name) == '1', 'Native threads must be1')
    need(sha(CLOSURE) == '214fc82e9d94dca811fcee164e4d67d87724c70843387cbba48e8a9fb3ed0d70', 'Root closure differs')
    need(sha(INDEX) == 'e9cf1d6142f2bd9f397050d61e43968402b6bfc8898c6b9a3d562854d6b2f8c7', 'Merged reference index differs')
    closure = json.loads(CLOSURE.read_text())
    need(closure['ownedProducerAndGroupGone'] and closure['scriptCLIAbsent'] and closure['noOtherMediaOrTestBrowserProcessObserved'], 'Root OS closure is missing')
    index = json.loads(INDEX.read_text())
    rows = index['frames']
    need(len(rows) == 270 and [x['mergedFrameNumber'] for x in rows] == list(range(1, 271)), 'Full270-frame order required')
    # The join references existing JPEGs only. The producer never copies, rewrites,
    # renumbers original files or synthesizes PTS across the capture boundary.
    for binding in index['sourceFrameIndexes'] + index['sourceClosures'] + index['sourceCaptureReceipts']:
        p = Path(binding['path'])
        need(p.stat().st_size == binding['bytes'] and sha(p) == binding['sha256'], 'Source binding changed')
    for n, row in enumerate(rows):
        p = Path(row['path'])
        base = OLD_SOURCE if n < 30 else NEW_SOURCE
        expected_number = 241 + n if n < 30 else n - 29
        need(row['sourceFrameNumber'] == expected_number, 'Original source frame order differs')
        need(p == base / 'frames' / f"{expected_number:06d}.jpg", 'Unexpected original frame path')
        need(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Original JPEG changed before composition')
    pil = [dict(path=p.relative_to(PIL_DIR).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
           for p in sorted(PIL_DIR.rglob('*')) if p.is_file() and p.suffix in ('.py', '.so')]
    tree = hashlib.sha256((json.dumps(pil, ensure_ascii=False, separators=(',', ':')) + '\n').encode()).hexdigest()
    need(tree == '4c32f6181e53b8aa29c77529bb75c225f23526dae31965b1d700a02e27fc4d5e', 'Known Pillow bytes differ')
    from PIL import Image, ImageDraw, ImageFont
    font_path = Path('/usr/share/fonts/noto/NotoSans-Regular.ttf')
    font = ImageFont.truetype(str(font_path), 12)
    output = HERE / 'contacts'
    need(not output.exists(), 'Fresh contacts only; no overwrite or retry')
    output.mkdir()
    used = sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())
    sheets = []

    def write(path, payload):
        nonlocal used
        need(used + len(payload) < CAP - RESERVE, '16MiB contact/review budget stop margin reached')
        with path.open('xb') as stream:
            need(stream.write(payload) == len(payload), 'Short contact write')
        used += len(payload)

    for offset in range(0, len(rows), 12):
        batch = rows[offset:offset + 12]
        canvas = Image.new('RGB', (720, 1844), '#20242a')
        draw = ImageDraw.Draw(canvas)
        draw.text((6, 5), f"P29 node20 ORIGINAL | M{batch[0]['mergedFrameNumber']:03d}-M{batch[-1]['mergedFrameNumber']:03d} | complete row-major", font=font, fill='white')
        for slot, row in enumerate(batch):
            x, y = (slot % 3) * 240, 28 + (slot // 3) * 454
            with Image.open(Path(row['path'])) as image:
                need(image.size == (480, 856), 'Native JPEG dimensions differ')
                tile = image.convert('RGB').resize((240, 428), Image.Resampling.LANCZOS)
                canvas.paste(tile, (x, y + 26))
                tile.close()
            draw.text((x + 3, y + 5), f"M{row['mergedFrameNumber']:03d}  {row['ptsTime']}s  p{row['pts']}", font=font, fill='white')
        encoded = BytesIO()
        canvas.save(encoded, 'JPEG', quality=84, subsampling=0)
        canvas.close()
        p = output / f"sheet-{offset // 12 + 1:02d}.jpg"
        write(p, encoded.getvalue())
        sheets.append(dict(**record(p), frames=[row['mergedFrameNumber'] for row in batch],
                           firstOriginalPTS=batch[0]['ptsTime'], lastOriginalPTS=batch[-1]['ptsTime']))
    need([n for sheet in sheets for n in sheet['frames']] == list(range(1, 271)), 'Contact coverage is not exact')
    for row in rows:
        need(sha(Path(row['path'])) == row['sha256'], 'Original JPEG changed during composition')
    result = dict(schema='stella.P29.node20.merged270-original-frame-contacts.v1', rootConfirmed=False,
                  imageInterpretationAccepted=False, generator=record(Path(__file__)), rootClosure=record(CLOSURE),
                  mergedOriginalIndex=record(INDEX), sourceFrameIndexes=index['sourceFrameIndexes'],
                  sourceCaptureReceipts=index['sourceCaptureReceipts'], sourceClosures=index['sourceClosures'],
                  originalFrameCount=270, allOriginalJPEGHashesBeforeAndAfterExact=True,
                  eachOriginalFrameCoveredExactlyOnceInOrder=True, frameSampling=False,
                  sourceCropped=False, contactThumbnailSize=[240, 428], contactSheetSize=[720, 1844],
                  contactQuality=84, contactSubsampling=0, pillowTreeSHA256=tree, font=record(font_path),
                  sheets=sheets, hardCapBytes=CAP, reservedForReviewMetadataBytes=RESERVE,
                  contactBytes=sum(sheet['bytes'] for sheet in sheets),
                  noNewVideoDecodeProbeBrowserAPI=True, originalFilesWritten=False,
                  nice=19, cpuAffinity=[0, 1], imagesViewedDuringCLI=False)
    write(HERE / 'contacts-index.json', (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    need(sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file()) < CAP, 'Actual review directory exceeds16MiB')
    print(json.dumps(dict(status='contacts-ready-unreviewed', sheets=len(sheets), frames=270,
                          contactBytes=result['contactBytes'], folderBytes=used)), flush=True)


if __name__ == '__main__':
    main()
