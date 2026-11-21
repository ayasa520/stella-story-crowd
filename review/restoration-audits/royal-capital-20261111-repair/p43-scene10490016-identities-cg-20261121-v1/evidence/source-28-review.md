# P43 rolling model, picture and background review

This extends the22-character first-scene packet in
`episode11-13-audit-20261121-v1`. Every model decision uses visible clothing and
body identity in an original full frame inside its saved dialogue interval,
not a speaker-name lookup.

| Packet | Character fields | Preserved exceptions |
|---|---:|---|
| s10490016-character.packet.json | 28 | Nodes9/27/29 need dark/white-effect process review; node17 is a picture. |
| s10490017-character.packet.json | 23 | Node8 needs white-flash process review; nodes9/13 are pictures. |
| s10490018-character.packet.json | 27 | Nodes30/31/33 visibly have no actor during internal monologue; empty character fields are preserved. |
| s10490019-character.packet.json | 33 | Node17 lacked a cached full frame in its short interval. |
| s10490019-node17-character.packet.json | 1 | Fresh sourcePTS774.421s confirms standard Reinhard. This resolves the frame gap separately without changing the earlier33 packet. |

Including the first scene,134character identities have direct original frame
evidence. This accepts no motion, expression, extra layer, geometry, timing or
whole part. Root flags remain false pending approval. Sparkles/rings on several
cards remain separate effects even when the underlying identity is clear.
`character_decisions.json` is the explicit per-node ledger; `make_packet.py`
binds it to empty-field guards and actual model texture/file hashes.

## Three original illustrations

Targeted geometric search over550original picture/still assets found candidates.
The reviewer then directly inspected each complete original image and its
matching composition in the recording:

| Scene/node | Confirmed resource | Composition |
|---|---|---|
| 10490016:17 | ADV_pic_103006 | Overhead Reinhard crouching beside a straight sword on blue floorboards. |
| 10490017:9 | ADV_pic_103008 | Reinhard from behind in the ruined shop, with Subaru in the right foreground. |
| 10490017:13 | ADV_pic_103009 | Gloved hand holding a crumbling sword against blue. |

Inlier counts112/28/44 supported retrieval; direct image inspection supplied the
verdict. These are character_image identities, not Live2D actors. Original
10101–10114 video keyframes were also inspected; numbering was not used to
choose identity.

`p43-three-pictures.packet.json` supplies picture-only scalar changes. All three
WebP payloads are already published under assets/preview/pictures, but absent
from the installed catalog picture map. The resource-additions JSON proposes
metadata referencing those existing WebP files, preserving original PNG member
and hash evidence. Root owns canonical resource integration before install.
CG command phases, entry/exit effects and timing remain unrecovered.

## Ruin background provider

`p43-ruin-background.packet.json` changes one sparse field at10490017:10 to
bg/bg046c_stealshop. The original card's leafless tree silhouettes, destroyed
upper wall and leaning broken beams, debris and blue night colors directly
match the complete original texture. The installed first provider is node2's
intact interior, which otherwise continues after the ruin illustration.

This source-backed change goes on the first following Live2D card. It is an
authored reconstruction of the visible change, not a recovered original provider
row or array order. It does not fill every later blank. Destruction/flash
commands and precise transition timing remain separate gaps.

The complete P43 ending/body-entry review and terminal suffix draft are in
`episode13-p43-ending-full-20261121-v1/REPORT.md`. This reviewer made no formal
data/source branch edit and launched no browser.
