# P09 costume and model-family recheck — 2026-11-12

Direct inspection of the two stored original P09 full frames and the matching
historical candidate full screenshots supports the same three non-prison
costume families. No substantive normal/prison variant mismatch was found.
This is an appearance and file-binding result; it does not accept the rejected
vertical composition, poses, original CSV or original evaluated MOC state.

No P28 source image was used to infer P09's clothing. The three already
assembled normal-model reference images were used only as original-resource
costume references, independently of the P28 scene where they were indexed.

| Actor | Features directly visible in both P09 source frames and both candidate frames | Comparison with the independently viewed reference/atlas |
|---|---|---|
| Kan, left | Brown bowl-cut hair; salmon/pink high collar and shoulder cape; round crossed-stitch clasp; purple clothing below | The assembled normal reference and current texture contain this cape/clasp/purple costume. The alternate prison texture has a wide black/white striped torso and sleeves instead. Source lower-body details are obscured by the bottom crop/UI and are not accepted. |
| Chin, center | Blue-grey hair with pink accent; plain ragged short-sleeve grey shirt; red neck band with hanging dark chain; dark/red wrist bands | These match the assembled normal reference and current texture. The alternate prison texture has a wide black/white striped torso and sleeves. Faint light bands on the normal model's grey trousers are not the discriminant; the visible shirt is. |
| Ton, right | White head wrap and purple braids; open green vest; beige sleeveless shirt with crossed chest lacing; red diamond pendant; ochre waist sash | The current normal reference/texture carries these features. The alternate prison torso/sleeves are wide black/white stripes and do not supply the green-vest/beige-shirt combination. Head wrap/hair alone would not distinguish the variants. |

Directly inspected source frames:

- `visual-low/p09-all/cast-172.8500.png`, original node `10020002:5`, 172.85 s;
  SHA-256 `f433cd5980b73356952894e1ced0d1b2bd7a9c1fc02f90def31cdd4f9995b640`.
- `visual-low/p09-all/cast-299.8500.png`, original node `10020002:15`, 299.85 s;
  SHA-256 `154ac18152e064bca8f172358f89663644950913df8993142fef1fa75ab41c07`.

Directly inspected original candidate full screenshots in
`../visual-review/`:

- `three-original-models-prefab-order-node5.png`;
  SHA-256 `f4bc4cdf890e5cc37f2db33d078139dc5f12fbbd51d939ce2e1636e84656d3fd`.
- `three-original-models-prefab-order-node15.png`;
  SHA-256 `cac92e419c39d1eb122993d40cf8f846b4f34ab845657edf489709866bf99295`.

The two existing 480×856 normalized full active-canvas versions were also
directly inspected. These are the earlier common viewport crop/resize, not
per-actor fitting. `receipt.json` records the exact path, actual byte digest,
header dimensions and usage for every image inspected in this task: the six
source/candidate views, three assembled references, three current normal
atlases and three original prison atlases. No image was regenerated or edited.

## Current file binding

For each of Kan/Chin/Ton, the current catalog resolves `/api/model/<id>` to
its own `models/<id>/detail.json`; that detail's member resolves through
`asset_members` to its own model JSON. The actual JSON's `FileReferences.Moc`
is `ac.moc3` and its only texture is `textures/texture_00.png`, resolved inside
that same model's `ac/` directory. No prison path or cross-family redirection
appears in these bindings.

All nine current normal model JSON/MOC/texture files are byte-identical to
their corresponding original extracted files. The current normal MOC hashes
remain Kan `a5c38be019a07c255ecbec74cee3c04513d38625c39f6b086e68fc695b8243bf`,
Chin `7adb0e76e46414404f2917cd6316d27bec87914813f2d58c3eef2a6700b78de1`,
Ton `d83c0a3ba3652fc279229e59530958216c3237eb67d5b0bebb547d47f27a1f72`.
Each differs from its prison alternate's actual MOC and texture digest.
The full normal/alternate model JSON, MOC and texture hashes and resolved
catalog paths are in `receipt.json`; no equivalence is inferred from names.

The historical `../visual-review/browser-network-all.txt` independently
records 200 responses for those normal JSON/MOC/texture paths in all four
candidate runs. It records no prison-family request. Those URL/status records
do not include response-body hashes or GPU texture/MOC instance digests.
Consequently this recheck proves the current on-disk binding and supports
the visible historical costume family, while the exact historical delivered
bytes and original P09 runtime MOC identity remain unmeasured.

The adapter's current mapping is at `../../playback/serve.py:37`, `:94–107`;
the viewer resolves each model JSON relative URL at
`story_crowd/public/pairing/viewer.js:65–74`. Both source hashes and bounded
network rows are retained in the receipt. Historical source mutability is
not used to assign a failure or cause.

## Result and boundary

The specific proposed prerequisite is now supported by direct P09 clothing
inspection plus current file bindings: the inspected candidate uses the
same visible non-prison costume families as the inspected P09 original
frames. No variant substitution or geometry correction is proposed.

The next draw logger should still record model JSON/MOC/texture digests and
actual instance identities once per load, as already requested in
`../offline-geometry-recheck-20261112-v1/DIAGNOSTIC_PROPOSAL.md`. This preserves
the distinction between a checked model-family prerequisite and actual
per-frame evaluated geometry. Complete entry motion/expression remains
unreviewed by this costume-only check.

Only new report/receipt files were written in this directory. No Chrome,
CLI browser session, new extraction, large decode, source/data/registry edit,
Git mutation or publication was performed.
