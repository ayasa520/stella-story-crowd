# P31 / P33 final dialogue actor candidates

Two **unapproved character-only** candidates are ready. No formal or canonical
data was changed; no browser/server, video decode, install, commit or push was
performed. Existing original images and model payloads are referenced by path
and SHA, without copying them into this package.

| Target | Stable key | Exact proposed scalar |
| --- | --- | --- |
| P31 / scene10040043 / node108 / uniq1004004300108 | `s10040043-p31-at0814` | `character=live2d/AC_ricardo01` |
| P33 / scene10040036 / node28 / uniq1004003600028 | `s10040036-p33-at0565` | `character=live2d/AC_ferris_dress01` |

The Japanese rows remain exactly:

P31: `大体、誰でもそうなんねん。` / `だーれもミミには勝てんのやから。` /
`はあ、ワイの奢りとはなあ……` (the three original newline-separated lines).

P33: `まあ、当然の反応だよネ`.

## Existing independent evidence reused

The publication queue already has these two independently accepted identities:

* Queue132, `132-s10040043-p31-source-review-accepted-character-bindings.packet.json`,
  from `/root/p31_source_review`, contains108→Ricardo. Its report covers the full
  entrance/hold/exit and direct original atlas inspection.
* Queue128, `128-s10040036-episode9-10-audit-p33-tail-character-bindings.packet.json`,
  from `/root/p31_route_evidence`, contains28→Ferris dress. Its report covers the
  full entrance/hold/exit, both original dress texture pages and a costume control.

Both old queue rows have no target-validation failures and their exact proposed
models have registered, passing resource checks. Their generic
`sourceFrameHashVerified` flag is false and their generic evidence-check arrays
are empty. This packet does not silently promote that flag: it adds fresh SHA
bindings for the actual full-size witnesses and records the prior limitation.

The existing ending audits were rehashed: **347 P31 frames plus324 P33 frames**,
and every bound contact sheet. Those audits and their source MP4 SHA bindings
are reused; the MP4 files were not decoded again. This identity packet does not
newly accept the door, CLEAR, terminal data, BGM or ending command phases.

## Fresh direct image review

The delegated reviewer directly opened the full-size P31 final dialogue frame
`source31/frames/0371.jpg` (819.587s), P33's full final dialogue frame
`source33/frames/0430.jpg` (565.756s), and its last actor frame0467 (566.990s).
The actual Japanese panels match the two current sidecar rows.

The full actor process was also personally rechecked using existing ordered
sheets: P31 frames0211–0420, and P33 frames0384–0486: **313 consecutive source
frames**, including prior-actor disappearance, the new actor entrance, current
dialogue, hold, exit and black. No sheet was generated or video re-decoded.

**P31 Ricardo:** the large wolf-like head, pointed upright crest/ears, two
braided locks with red ties, bare muscular torso with V-shaped chest fur,
diagonal black strap and red/black shoulder plate agree with the entire original
`ricardo01` atlas. The prior Subaru has fully disappeared before this actor
enters; the same actor remains through the final multiline dialogue and exits.

**P33 Ferris dress:** cat ears, short brown hair, pale bows with blue/gold ribbon
ends at both ears, thin shoulder straps, a striped scalloped bodice, detached
pale sleeves and a choker with circular pendant/ribbon ends match
`ferris_dress01`. The source costume structure was compared directly against
the complete originals of **all four available Ferris variants**:

| Variant | Directly observed costume distinction |
| --- | --- |
| `ferris01` | Closed military tunic, cape, long sleeves; does not match the bare-shouldered striped bodice. |
| `ferris_after20y01` | Dark pinstriped suit/tie; does not match the dress. |
| `ferris_dress01` | Matching scalloped striped bodice, thin straps, bows and detached sleeves; both texture pages inspected. |
| `ferris_kimono01` | Pink floral wrapped garment with obi; does not match the dress. |

The actual source colors appear turquoise while the original texture is blue.
Exact lighting/color reproduction is outside this identity decision. Speaker
names were not used to choose a Ferris variant.

All **six complete original atlas images** (Ricardo1, Ferris regular1,
after20y1, dress2, kimono1) were directly opened. Each installed model descriptor,
MOC and complete texture payload is byte-identical to the corresponding extracted
original. `model-payloads-and-controls.json` retains every path/SHA pair. Neither
selected model requires a new resource.

## Standard checks and final writer boundary

Both candidates pass standard `InstalledSnapshot`, `validate_document` and
`validate_resources`. Disposable in-memory copies differ only at the requested
one `character` field each. The normal `ReviewedRepair.node_fields` gate rejects
the unapproved packets as expected:

* `Unreviewed performance patch: 10040043:108`
* `Unreviewed performance patch: 10040036:28`

Each packet guards the current unique ID, stable key, exact Japanese sidecar,
all native string/command preconditions and the SHA of the complete row body
excluding `branch_list`. The preparation data HEAD was
`db23843217c80693e893279c1f60760105997510`.

The normal ending work is separate and may replace the old empty continuation
and append its movie/CLEAR nodes. **Root must fresh-rebind after that write**:
read the current snapshot and ownership, verify the stable ID/Japanese and
unchanged non-branch row body, preserve the new edge and appended suffix, then
rebind whole-file/global guards. This packet writes no branch or ending field.

**Acceptance is only two model identities/costumes.** Motion, face, pose, extra
layers, geometry, lighting fidelity, audio, original command phases, timing,
ending reconstruction, saved playback and whole-scene restoration remain
unaccepted. Root approval, normal staging/install and saved identity readback
remain the formal writer's work.

The package contains only small JSON/Markdown/Python evidence, well below5 MB.
No original image, model, video or large source JSON was copied.
