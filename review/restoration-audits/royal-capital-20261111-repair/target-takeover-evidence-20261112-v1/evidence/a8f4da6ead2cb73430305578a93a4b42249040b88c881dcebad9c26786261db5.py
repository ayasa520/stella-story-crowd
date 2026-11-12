"""Verify one saved JSON mismatch without rerunning any application module.

The source input, saved exception document and immutable Git manifest are
independent byte inputs. One strict UTF-8 parse and one ARM Node parse per saved
document establish their behavior. These observations do not identify a decoder,
runtime, operating-system or hardware cause and do not modify the standard JSON
decoder, formal story data, environment or application source.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/home/rikka/Projects/stella')
R=ROOT/'data/native_recovery/royal-capital-20261110/repair-20261111'
SOURCE=R/'target-json-module-observations-v1/1794463311690541315'
OUT=Path(__file__).parent
COMMIT='698acdd0dcd242aebd481337a3feda0dd62942c8'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def record(path):
    raw=path.read_bytes()
    return dict(file=str(path),bytes=len(raw),sha256=sha(raw))


def parse_once(raw,label):
    text=raw.decode('utf-8',errors='strict')
    result=dict(strictUtf8DecodePassed=True,utf8RoundtripEqualsRaw=text.encode('utf-8')==raw,
        unicodeCharacters=len(text),nulCharacters=text.count('\0'),
        beforeTextUtf8Sha256=sha(text.encode('utf-8')))
    try:
        value=json.loads(text)
        result.update(parsePassed=True,topLevelKeys=list(value) if isinstance(value,dict) else None)
    except json.JSONDecodeError as error:
        result.update(parsePassed=False,error=dict(name=type(error).__name__,message=str(error),
            position=error.pos,line=error.lineno,column=error.colno,
            characterCode=ord(error.doc[error.pos]) if error.pos<len(error.doc) else None,
            inputTextEqualsExceptionDocument=text==error.doc,
            exceptionDocumentUtf8Sha256=sha(error.doc.encode('utf-8'))))
        with (OUT/(label+'-independent-exception-document.txt')).open('xb') as stream:
            stream.write(error.doc.encode('utf-8'))
    result.update(afterTextUtf8Sha256=sha(text.encode('utf-8')),
        afterTextNulCharacters=text.count('\0'))
    return text,result


def main():
    assert os.getpriority(os.PRIO_PROCESS,0)==19 and set(os.sched_getaffinity(0))=={0,1}
    original_path=SOURCE/'failed-input.bin'
    exception_path=SOURCE/'failed-exception-document.txt'
    original,exception=original_path.read_bytes(),exception_path.read_bytes()
    committed=subprocess.check_output(['git','--no-optional-locks','show',f'{COMMIT}:manifest.json'],cwd=ROOT/'story_crowd_data')
    assert original==committed
    assert sha(original)=='ddcc3942dd154a5c6f32ccc83600a999cd8da191e8a4c22abbfbc2ba7b775755'
    assert sha(exception)=='81dc58a5faa79985f8d57f3aee374f965e17b8e694eafb631864375e407e37da'
    observations=json.loads((SOURCE/'observations.json').read_bytes())
    failure=next(row for row in observations['observations'] if row['status']=='failed')
    original_text,original_parse=parse_once(original,'original-'+str(time.time_ns()))
    exception_text,exception_parse=parse_once(exception,'saved-exception-'+str(time.time_ns()))
    with (OUT/('python-observation-'+str(time.time_ns())+'.json')).open('x') as stream:
        json.dump(dict(original=original_parse,savedException=exception_parse),stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    position=failure['position']
    assert original_text!=exception_text and ord(original_text[position])==32 and ord(exception_text[position])==0
    assert exception_parse['parsePassed'] is False
    byte_differences=[dict(offset=index,original=left,exception=right)
        for index,(left,right) in enumerate(zip(original,exception)) if left!=right]
    text_differences=[dict(position=index,originalCode=ord(left),exceptionCode=ord(right))
        for index,(left,right) in enumerate(zip(original_text,exception_text)) if left!=right]
    node_script=R/'target-p30-extra9-independent-preflight-20261112-v1/node-parse.cjs'
    saved_node=OUT/'node-observation.raw.json'
    if saved_node.exists():
        # Reuse the already captured adaptive Node observation. Modern Node may
        # report a token/context without a numeric position; absence is not a
        # second parser discrepancy and must not be replaced with an invented
        # error offset. The full independent text comparison supplies its own
        # exact difference position below.
        node_result=json.loads(saved_node.read_bytes())
        node_code,node_stderr=1,''
    else:
        node=subprocess.run(['/usr/bin/node',str(node_script),str(original_path),str(exception_path)],capture_output=True)
        node_result=json.loads(node.stdout)
        node_code,node_stderr=node.returncode,node.stderr.decode()
    # The observer exits1 because one intentionally supplied saved document is
    # invalid. Preserve that expected failure as evidence, not a broken tool.
    assert node_code==1 and node_result['architecture']=='arm64'
    assert node_result['records'][0]['success'] is True and node_result['records'][1]['success'] is False
    assert node_result['records'][1]['error']['position'] in [None,position]
    with (OUT/'node-observation.json').open('x') as stream:
        json.dump(dict(exitCode=node_code,stderr=node_stderr,**node_result),stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    result=dict(schema='stella.json_decode_mismatch_independent_review.v1',status='saved_input_and_exception_document_difference_independently_verified',
        reviewer='/root/p29_packet_preflight',createdUtc=datetime.now(timezone.utc).isoformat(),
        sourceObservation=record(SOURCE/'observations.json'),original=record(original_path),exceptionDocument=record(exception_path),
        immutableGit=dict(commit=COMMIT,path='manifest.json',bytes=len(committed),sha256=sha(committed),exactlyEqualsSavedInput=True),
        originalRawNulBytes=original.count(b'\0'),exceptionRawNulBytes=exception.count(b'\0'),
        equalRawByteLength=len(original)==len(exception),equalUnicodeLength=len(original_text)==len(exception_text),
        byteDifferenceCount=len(byte_differences),byteDifferences=byte_differences,
        textDifferenceCount=len(text_differences),textDifferences=text_differences,
        pythonOriginalExplicitStrictUtf8Parse=original_parse,pythonSavedExceptionStrictUtf8Parse=exception_parse,
        nodeObservation=record(OUT/'node-observation.json'),nodeObserverSource=record(node_script),
        cause='unknown',applicationModuleRerun=False,standardDecoderChanged=False,globalEnvironmentChanged=False,
        formalDataChanged=False,applicationSourceChanged=False,browserStarted=False,
        limits=['The saved exception document differs from the saved byte input; this does not locate the cause in decoding, parsing, observation or another layer.',
            'Explicit strict UTF-8 decoding and parsing passed once for this exact valid input. This is bounded evidence, not a guarantee for every future invocation.',
            'No pure-parser workaround, file corruption, operating-system or hardware cause is asserted.'])
    with (OUT/'receipt.json').open('x') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(receipt=record(OUT/'receipt.json'),originalEqualsGit=True,
        originalParsePassed=original_parse['parsePassed'],savedExceptionParseRejected=True,byteDifferenceCount=len(byte_differences),
        textDifferenceCount=len(text_differences),position=position,cause='unknown'),ensure_ascii=False))


if __name__=='__main__':
    main()
