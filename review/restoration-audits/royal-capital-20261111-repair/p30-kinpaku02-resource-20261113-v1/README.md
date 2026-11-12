# Native kinpaku02 resource restored to the music library

The recorded P30 music includes `bgm_adv_kinpaku02_cd2_18`, which was absent
from the18-track public resource catalog. The normal music exporter prepared
the original waveform as stereo Opus with its native ACB metadata. This change
adds that resource and its two member mappings, preserving all earlier music
rows and unrelated catalog values. It does not change a story field.

The native waveform has8,414,915samples at44,100Hz, or190.814399seconds.
Its loop is266,721→8,414,915samples, or6.048095→190.814399seconds.
The decoded preview length differs by less than one48kHz sample. The source
trim starts at the original waveform origin; it does not use a correlation
offset or retain the rendered extra loop. This cue's native track contains
noteOn2000 and end0, with no998 event. No gain, tempo, fade or wait is invented.

The package file index now includes the new Opus/metadata and the updated
catalog. It also reconciles only the two already accepted incremental assets:
`ADV_still_006.png` and the CG panel-entry transition profile. Those payloads
are unchanged here, and their accepted audit paths are linked in the index.
Other file records and baseline Studio project provenance are preserved.
No whole-library build, file inventory or source-audio decoding was performed.

The resource is identified from the recording and its native cue, and its
export/decode/metadata checks passed. Ordinary audible playback, the exact
story onset/phase, volume/fade parameters and the later waveform-clock
discrepancy remain unaccepted. The early narration2 source anchor is retained
as evidence, not an installed `bg_music` field or recovered command timestamp.
