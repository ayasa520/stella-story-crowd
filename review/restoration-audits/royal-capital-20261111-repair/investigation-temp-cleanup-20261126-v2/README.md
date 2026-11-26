# Investigation temporary-file cleanup, 2026-11-26 v2

Deleted 287 closed browser-generated console logs, DOM snapshots and reproducible renderer diagnostic packages containing temporary PNG samples. No original source frames, videos, OCR, scripts, assets or ARM environments were removed. The latest UI31 run remains intact.

Replaced 91 uncompressed FFmpeg/source-quality logs with complete gzip archives. Every archive was decompressed and verified against its original SHA-256 before unlinking the old path. `retained-log-mapping.json.gz` maps each old path to its preserved archive and records termination uncertainty; compression does not turn failed or unknown runs into successes.

`deleted-file-metadata.jsonl.gz` records exact deleted file paths, hashes and original allocated sizes. Only this compact audit and retained log archives are added to the configured data repository.
