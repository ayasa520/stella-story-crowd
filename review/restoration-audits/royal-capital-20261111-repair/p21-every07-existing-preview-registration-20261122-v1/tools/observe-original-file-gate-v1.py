"""Run one original file entry point and retain its original exception only.

The script path and fresh observation directory are observer arguments. The
remaining argv, interpreter, reads, parser and entry-point implementation stay
unchanged. This is not a retry mechanism or a replacement decoder/parser.
"""
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys
import traceback

SCRIPT = Path(sys.argv[1]).resolve(strict=True)
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir()
sys.argv = [str(SCRIPT), *sys.argv[3:]]
# Match normal direct-file execution, including any guarded sibling imports.
# run_path does not itself reproduce a direct script's sys.path[0].
sys.path[0] = str(SCRIPT.parent)
try:
    runpy.run_path(str(SCRIPT), run_name="__main__")
except BaseException as error:
    try:
        receipt = dict(errorType=type(error).__name__, message=str(error),
                       traceback=traceback.format_exc(), originalScript=str(SCRIPT),
                       originalFailureReRaised=True, parserReplaced=False,
                       readsIntercepted=False, automaticRetry=False)
        if isinstance(error, json.JSONDecodeError):
            # Preserve the actual failed string before encoding. A subsequent
            # successful disk read cannot replace this exception document.
            receipt.update(exceptionDocIdentity=id(error.doc), characters=len(error.doc),
                           NULCharacters=error.doc.count("\x00"), position=error.pos,
                           line=error.lineno, column=error.colno,
                           originalOrdinalsNearPosition=[ord(c) for c in error.doc[max(0,error.pos-32):error.pos+32]])
            raw = error.doc.encode("utf-8", errors="surrogatepass")
            (OUT / "original-exception-doc.txt.gz").write_bytes(gzip.compress(raw, mtime=0))
            receipt.update(exceptionDocBytes=len(raw), exceptionDocSHA256=hashlib.sha256(raw).hexdigest())
        (OUT / "failure.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    except BaseException as observation_error:
        # Evidence-writing failure must not replace the original exception.
        # Keep this fallback best-effort; the outer bare raise still reports
        # the original script's error and traceback even if stderr is closed.
        try:
            sys.stderr.write("ORIGINAL_EXCEPTION_OBSERVER_WRITE_FAILED "+repr(observation_error)+"\n")
        except BaseException:
            pass
    raise
