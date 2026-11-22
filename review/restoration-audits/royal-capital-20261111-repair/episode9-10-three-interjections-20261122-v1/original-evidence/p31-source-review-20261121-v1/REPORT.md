# P31 final four cards: independent source identity review

Reviewer: `/root/p31_source_review`. This is delegated image review only;
formal data installation and saved playback remain the root writer's work.

Accepted identity fields in scene **10040043**:

| Node | Stable key | Exact character value |
|---|---|---|
| 105 | `s10040043-p31-at0804p5` | `live2d/AC_mimi01` |
| 106 | `s10040043-p31-at0808` | `live2d/AC_felt01` |
| 107 | `s10040043-p31-at0812` | `live2d/AC_subaru01` |
| 108 | `s10040043-p31-at0814` | `live2d/AC_ricardo01` |

All four identities were compared directly with the actual existing model
texture atlases. The distinguishing costume, hair, ornaments and torso
details are recorded per row in `accepted-character-bindings.json`; this
does not rely on speaker names. Native/source IDs are preserved as authored
restoration IDs; no claim is made that these are recovered original IDs.

## Source coverage

Source: `/home/rikka/Videos/re0/真夜黑兔_Official_王都一日游篇/31 9本篇「结束与开始」Ver蜜蜜.mp4`.
SHA-256 `7f5bf8a6e10ad2afd02e53a039c60dfcdc378eec3b3062e1f75446437db7497f`.
The source is 480×856, nominal 30 fps with source timestamps preserved.

Directly reviewed all 126 consecutive reused prefix frames from
803.321–807.487s and all 449 newly decoded consecutive frames from
806.021–820.954s. The overlapping intervals cover predecessor 104, Mimi's
complete entry/arm raise/eye change/hold/exit, Felt's complete entry/hold/exit,
Subaru's complete entry/eye and head change/hold/exit, Ricardo's complete
entry/hold/exit and the beginning of the source ending transition. Review
used ordered sheets with every frame present and full-size original stills.

Original earlier prefix frames were copied from
`/tmp/stella-p31-ending-source.vQHxSs45/prefix` to `reused/prefix/` before
review. The earlier 258-frame location evidence was also preserved under
`reused/location/`, but its background interpretation is a separate packet.
All copied prefix/location frames are bound by source PTS and SHA-256 in
`input-evidence-hashes.json`. Model JSON and texture hashes are included.

The fresh bounded decode used nice 19, CPU 0/1, decoder/filter/encoder each
one thread, no temporal resampling. `decode.log`, `frame-index.json` and all
449 frames are preserved. FFmpeg's filter logged two tail lookahead frames
that were not encoded at the duration cut; the sheet helper validates and
excludes that unencoded tail explicitly. Every encoded frame is indexed.

## Acceptance boundary

Only the four **character identity** scalars are accepted. Motion, face,
additional layers, geometry, lip behavior, phase commands, sound, background,
timing and ending are not signed by this packet. In particular, Subaru enters
with eyes open, then lowers his head and closes his eyes; selecting a motion
only from his closed-eye still would lose the original process.

No browser was launched by this reviewer, no formal data was changed and no
commit was made. Normal saved playback must still show the four bound models
across 104→105→106→107→108, and resulting captured images need delegated
review after the root-designated browser session is closed.

Inspected local native scene SHA-256:
`dfbd52c3818f2fd6f89dc6f8bf065ac972d16d43e433ca1d8991c0d4253a0c5b`.
Inspected review scene SHA-256:
`1424843e65225f88257e82d232afff2f84ee94832e09c2d264d08932ea321b27`.
Root requested rebinding against fetched main
`260b660e2fef6e2c14eb697e8123cfc077e1424f`; the packet records that reference
and deliberately leaves `rootConfirmed` false.

Auxiliary audio alignment check: at source seek 291.30s, Ricardo is fully
visible under a `リカード` panel containing `うおい！`, with no selection or
previous card remaining. `node9-at291p30.jpg` supports the card attribution,
but does not measure the cue's precise start time.
