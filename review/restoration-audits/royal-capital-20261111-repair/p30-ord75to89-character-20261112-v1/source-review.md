All15 original full frames were directly inspected. **One new character-only
proposal:** scene10450056/node18, ordinal79, `live2d/AC_felt01`.
The other14 observations remain pending. All15 current character fields are
empty; current stable keys and Japanese text match the existing allocation.

| Ordinal | Scene10450056 node | Original frame time | Direct visual decision |
| --- | --- | --- | --- |
| 75 | 14 | 454.999s | Dark short-sleeved tee; tshirt01/tshirt02 unresolved |
| 76 | 15 | 460.999s | Cloaked Elsa candidate; exact assembled binding pending |
| 77 | 16 | 462.999s | Julius knight costume; exact assembled reference pending |
| 78 | 17 | 468.999s | Julius knight costume; exact assembled reference pending |
| **79** | **18** | **474.999s** | **Felt01 identity/costume supported** |
| 80 | 19 | 478.999s | Dark short-sleeved tee; tshirt01/tshirt02 unresolved |
| 81 | 20 | 482.999s | Julius knight costume; exact assembled reference pending |
| 82 | 21 | 487.999s | Dark short-sleeved tee; tshirt01/tshirt02 unresolved |
| 83 | 22 | 504.999s | Knight costume partly covered by choice/response UI; same reference gap |
| 84 | 23 | 513.999s | Julius knight costume; exact assembled reference pending |
| 85 | 24 | 515.499s | Julius knight costume; held pose/scale not accepted |
| 86 | 25 | 520.499s | Braid, flower, feathers and mantle/gold clasp visible; Elsa exact binding pending |
| 87 | 26 | 529.999s | Illustrated spell frame with two figures and multicolour rays; no ordinary Live2D fill |
| 88 | 27 | 534.999s | White radial impact with a small illustration fragment; no Live2D costume inference |
| 89 | 28 | 545.999s | Dark tee against blue-lit background; tshirt01/tshirt02 unresolved |

For ordinal79, I directly compared the full source frame
`ocr/30/root-review/frames/d7d29c63dc09-014250.jpg` with the exact assembled
[Felt01 anchor](../../visual-low/p11-felt21-production-review-v1/fresh-felt22-v31/felt22-ikaru-from-formal21-v31-actor-frame-148.png).
The braided blonde crown, dark bow, red scarf, brown sleeveless vest, black
bandeau, bare midriff and fur cuffs match. The anchor's model/instance/Core
attribution is retained in
`agent-reviewed-p29-identity-v1/felt01-assembled-original-binding.json`.
Current catalog key`live2d/AC_felt01` identifies model`felt01` and
`models/felt01/ac/ac.model3.json`. The historical trial remains failed; this
reference supports identity/costume only.

The existing Julius01 binding explicitly has
`assembledReferenceAvailable:false`. The Elsa resource revalidation still
lacks the required selected assembled PNG attribution. Existing tshirt01/02
bindings likewise provide no accepted assembled variant reference. Visible
names, expressions and dialogue do not settle those gaps. No capture was run.
For87/88, the exact illustration/CG/movie/FX asset and its full sequence need
a separate source review; these stills do not establish an asset type or
ordinary character field.

`decisions.json` contains each exact stable key, JP text, original full-frame
path, event, interval, decision and existing reference path. It points to the
existing evidence instead of copying nested source/model packets.
`one-character-only-draft.json` has one guarded empty-character proposal and
`rootConfirmed:false` for parent integration. No formal data/source/Git
changes, extraction, browser or compiler execution. No acting, expression,
geometry, timing, audio, FX, route or whole-part acceptance.
