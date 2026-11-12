"""Observe exact JSON inputs while running an unmodified restoration module.

The captured bytes and the exception's document differ by one space/NUL despite
the ownership hash matching. This launcher explicitly decodes the known UTF-8
inputs and verifies byte roundtrip before calling the unchanged normal decoder.
It records failures and never retries or rewrites data. The lower-level cause
remains unknown; schema, resource and transaction checks stay unchanged.
"""
import atexit
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
from target_verified_utf8_v1 import decode_verified


def main():
    module, *arguments = sys.argv[1:]
    assert module in ('story_studio.recovery.native_repair', 'story_studio.recovery.native_install')
    output = Path(__file__).parent / 'target-json-module-observations-v1' / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    original = json.loads
    observations = []

    def observed(value, *args, **kwargs):
        raw = value.encode('utf-8') if isinstance(value, str) else bytes(value)
        item = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), nulBytes=raw.count(b'\0'))
        observations.append(item)
        encoding = json.detect_encoding(raw)
        assert encoding in ('utf-8', 'utf-8-sig'), 'Only verified repository UTF-8 inputs are admitted'
        text = value if isinstance(value, str) else decode_verified(raw, module)
        assert text.encode(encoding) == raw, 'Decoded input differs from its exact original bytes'
        item.update(encoding=encoding, strictByteRoundtrip=True, parserInputType='str')
        try:
            result = original(text, *args, **kwargs)
            item['status'] = 'passed'
            return result
        except json.JSONDecodeError as error:
            decoded = raw.decode('utf-8')
            item.update(status='failed', error=str(error), position=error.pos,
                exceptionDocumentSha256=hashlib.sha256(error.doc.encode('utf-8')).hexdigest(),
                decodedInputEqualsExceptionDocument=decoded == error.doc,
                inputCharacter=ord(decoded[error.pos]) if error.pos < len(decoded) else None,
                exceptionCharacter=ord(error.doc[error.pos]) if error.pos < len(error.doc) else None,
                exceptionWindow=repr(error.doc[max(0, error.pos - 80):error.pos + 80]))
            (output / 'failed-input.bin').write_bytes(raw)
            (output / 'failed-exception-document.txt').write_text(error.doc)
            raise

    def save():
        with (output / 'observations.json').open('x') as stream:
            json.dump(dict(module=module, arguments=arguments, cause='unknown',
                           decoder='unchanged_standard_with_verified_utf8_text_ingress', observations=observations), stream, indent=2)
            stream.write('\n')

    atexit.register(save)
    json.loads = observed
    sys.argv = [module, *arguments]
    runpy.run_module(module, run_name='__main__', alter_sys=True)


if __name__ == '__main__':
    main()
