"""Encode independent JPEG stills from a bounded original-order RGB stream.

Rawvideo has no timestamp container. The caller independently retains and
matches every original decoder showinfo PTS to the sealed probe by ordinal;
this worker never drops, inserts, resamples or assigns a temporal value.
"""
import hashlib
import os
from pathlib import Path
import sys
from PIL import Image

assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert os.sched_getaffinity(0) == {0, 1}
destination = Path(sys.argv[1])
width, height, expected = map(int, sys.argv[2:])
size = width * height * 3
ordinal = 0
with (destination.parent / 'raw-frame-digests.tsv').open('x') as index:
    index.write('ordinal\trgb24_sha256\tjpeg_bytes\tjpeg_sha256\n')
    while True:
        raw = sys.stdin.buffer.read(size)
        if not raw:
            break
        assert len(raw) == size, (ordinal, len(raw), size)
        assert ordinal < expected, 'Unexpected extra decoded frame'
        target = destination / f'{ordinal:04d}.jpg'
        with target.open('xb') as output:
            Image.frombytes('RGB', (width, height), raw).save(
                output, format='JPEG', quality=90, subsampling=0, optimize=False)
        jpeg = target.read_bytes()
        index.write(f'{ordinal}\t{hashlib.sha256(raw).hexdigest()}\t{len(jpeg)}\t{hashlib.sha256(jpeg).hexdigest()}\n')
        ordinal += 1
assert ordinal == expected, (ordinal, expected)
print(f'complete_frames={ordinal}; rgb24_bytes={ordinal * size}')
