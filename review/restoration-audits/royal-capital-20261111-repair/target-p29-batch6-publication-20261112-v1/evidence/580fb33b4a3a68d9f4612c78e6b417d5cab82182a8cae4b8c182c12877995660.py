"""Run the unchanged read-only library audit with Python's pure JSON scanner.

Target logs preserve intermittent accelerated-parser exceptions on unchanged
catalog/manifest bytes. Three standard/pure comparisons per affected file agree
when parsing succeeds; the cause remains unknown. This explicit audit entrypoint
uses both py_scanstring and py_make_scanner, retaining strict JSON validation and
all original field/resource/protected-file checks. It changes no source payload,
importer, global Python configuration or installed environment.
"""

import json
import json.decoder
import json.scanner
from pathlib import Path
import runpy
import sys


def main():
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
