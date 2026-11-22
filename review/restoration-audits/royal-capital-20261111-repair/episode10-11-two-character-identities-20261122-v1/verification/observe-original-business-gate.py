"""Observe one original repair/install invocation without replacing any read.

The first two observer arguments identify the original module and a new log
directory. All remaining CLI arguments are forwarded unchanged. Original JSON
failure strings are retained before encoding; no retry or parser shim exists.
"""
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys
import traceback

MODULE = sys.argv[1]
if MODULE not in {"story_studio.recovery.native_repair", "story_studio.recovery.native_install"}:
    raise ValueError("Only the two unchanged normal business gates are supported")
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir()
sys.argv = [MODULE, *sys.argv[3:]]
try:
    runpy.run_module(MODULE, run_name="__main__")
except BaseException as error:
    receipt = dict(errorType=type(error).__name__, message=str(error),
                   traceback=traceback.format_exc(), originalModule=MODULE,
                   parserReplaced=False, originalFailureReRaised=True,
                   automaticRetry=False)
    if isinstance(error, json.JSONDecodeError):
        receipt.update(exceptionDocIdentity=id(error.doc), characters=len(error.doc),
                       NULCharacters=error.doc.count("\x00"), position=error.pos,
                       line=error.lineno, column=error.colno,
                       originalOrdinalsNearPosition=[ord(c) for c in error.doc[max(0,error.pos-32):error.pos+32]])
        raw = error.doc.encode("utf-8", errors="surrogatepass")
        (OUT / "original-exception-doc.txt.gz").write_bytes(gzip.compress(raw, mtime=0))
        receipt.update(exceptionDocBytes=len(raw), exceptionDocSHA256=hashlib.sha256(raw).hexdigest())
    (OUT / "failure.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    raise
