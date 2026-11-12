"""Run the unchanged read-only library audit with Python's pure JSON scanner.

Target logs preserve intermittent JSON exceptions on catalog/manifest reads,
including one pure-parser failure. Standard/pure comparisons per file agree
when parsing succeeds; the cause remains unknown. This explicit audit entrypoint
uses both py_scanstring and py_make_scanner, retaining strict JSON validation and
all original field/resource/protected-file checks. It changes no source payload,
importer, global Python configuration or installed environment.
"""

import json
import json.decoder
import json.scanner
import atexit
import hashlib
from pathlib import Path
import runpy
import sys
import time


def main():
    evidence = Path(__file__).parent / 'target-json-audit-observations-v1' / str(time.time_ns())
    evidence.mkdir(parents=True, exist_ok=False)
    observations = []
    original_loads = json.loads

    def observed_loads(value, *args, **kwargs):
        # Preserve the exact bytes passed to the parser on a failure. Earlier
        # file hashes alone cannot establish whether the failed read, decoding
        # or parsing observed the same content; no cause is asserted here.
        raw = value.encode('utf-8') if isinstance(value, str) else bytes(value)
        item = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                    nulBytes=raw.count(b'\0'), inputType=type(value).__name__)
        observations.append(item)
        try:
            result = original_loads(value, *args, **kwargs)
            item['status'] = 'passed'
            return result
        except json.JSONDecodeError as error:
            decoded = raw.decode('utf-8')
            item.update(status='failed', error=str(error), position=error.pos,
                        exceptionDocumentSha256=hashlib.sha256(error.doc.encode('utf-8')).hexdigest(),
                        decodedInputEqualsExceptionDocument=decoded == error.doc,
                        exceptionCharacter=ord(error.doc[error.pos]) if error.pos < len(error.doc) else None,
                        inputCharacter=ord(decoded[error.pos]) if error.pos < len(decoded) else None,
                        exceptionWindow=repr(error.doc[max(0, error.pos - 80):error.pos + 80]))
            (evidence / 'failed-input.bin').write_bytes(raw)
            (evidence / 'failed-exception-document.txt').write_text(error.doc)
            raise

    def save_observations():
        with (evidence / 'observations.json').open('x', encoding='utf-8') as stream:
            json.dump(dict(parser='py_scanstring_and_py_make_scanner',
                           cause='unknown', observations=observations), stream, indent=2)
            stream.write('\n')

    atexit.register(save_observations)
    json.loads = observed_loads
    decoder = json.JSONDecoder()
    decoder.parse_string = json.decoder.py_scanstring
    decoder.scan_once = json.scanner.py_make_scanner(decoder)
    # json.load()/loads() without custom options share this decoder. The audit
    # uses precisely that API, so subprocess/Git JSON and disk JSON receive the
    # same strict parser without weakening any schema or evidence assertion.
    json._default_decoder = decoder
    audit = Path(__file__).with_name('audit_v20_publication.py')
    sys.argv[0] = str(audit)
    runpy.run_path(str(audit), run_name='__main__')


if __name__ == '__main__':
    main()
