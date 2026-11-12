"""Require exact UTF-8 roundtrip before admitting target JSON text.

Captured evidence proves a one-character mismatch between valid input bytes and
an exception document. A later explicit decode also failed byte roundtrip. The
underlying runtime cause is unknown. This boundary therefore checks the result,
retains every rejected result, and permits at most three attempts on the SAME
immutable input bytes. It never rereads, rewrites, normalizes or retries an
import/write operation. Exhaustion stops before JSON parsing or data mutation.
"""
import hashlib
import json
from pathlib import Path
import time


def decode_verified(raw, context):
    assert isinstance(raw, bytes)
    encoding = json.detect_encoding(raw)
    assert encoding in ('utf-8', 'utf-8-sig'), 'Only repository UTF-8 JSON is admitted'
    expected = hashlib.sha256(raw).hexdigest()
    for attempt in range(1, 4):
        text = raw.decode(encoding, errors='strict')
        encoded = text.encode(encoding, errors='strict')
        if encoded == raw:
            return text
        directory = Path(__file__).parent / 'target-utf8-roundtrip-observations-v1' / str(time.time_ns())
        directory.mkdir(parents=True, exist_ok=False)
        (directory / 'input.bin').write_bytes(raw)
        (directory / 'rejected-text-encoded.bin').write_bytes(encoded)
        metadata = dict(status='rejected_before_json_parse', context=context,
            attempt=attempt, maximumAttempts=3, inputBytes=len(raw), inputSha256=expected,
            rejectedBytes=len(encoded), rejectedSha256=hashlib.sha256(encoded).hexdigest(),
            inputNulBytes=raw.count(b'\0'), rejectedNulBytes=encoded.count(b'\0'),
            firstDifferentByte=next((i for i, (a, b) in enumerate(zip(raw, encoded)) if a != b), None),
            sameImmutableInputOnEveryAttempt=True, dataRewritten=False, cause='unknown')
        with (directory / 'receipt.json').open('x') as stream:
            json.dump(metadata, stream, indent=2)
            stream.write('\n')
    raise RuntimeError('Three UTF-8 roundtrip checks failed; inspect target-utf8-roundtrip-observations-v1')
