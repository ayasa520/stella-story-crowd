# Closed investigation log and screenshot cleanup

The user requested deletion of accumulated investigation logs and screenshots.
This bounded cleanup removed 4,589 files and released 547,213,312 allocated bytes
from fully unlinked inodes. Earlier cleanup is excluded from these totals.

The deleted files were four historical browser trace JSON outputs, 166 old test
logs and temporary dumps, and 4,419 derived playback frames and contact sheets
from completed local tests. They were not original-game recording frames.

Original videos, original recording frames, local test MKV/WebM recordings,
OCR, audio, native implementation evidence, review reports and indices, current
v3 capture inputs, ARM environments and tablet configuration remain. Hashes of
212 retained recordings, reports and current input files were checked before
and after deletion. Data scripts, canonical website source and unrelated dirty
work were unchanged. No browser or decoder was started.

The compressed deletion manifest contains paths, hashes and file metadata only;
there is no replacement backup of the removed logs or images. Historical
references to the deleted investigation outputs are intentionally retired.
Accessible process descriptors had no open reference to a selected file;
foreign process descriptor permission limits are recorded in the manifest.

This publication adds only cleanup metadata and does not claim further scene or
performance restoration acceptance.
