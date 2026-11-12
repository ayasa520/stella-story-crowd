# P30 CG white radial entry/exit — bounded native control-chain finding

The inspected **default picture load / CardIn chain does not supply the observed white radial opening or closing**. It supplies image loading over black, normal card masks/UVs, position changes and opacity. Native Wipe is a separate named-resource control path. This distinguishes the owners; it does **not** recover the actual P30 Wipe/FX name, color argument, phase, normalized start or timer. Do not append a guessed command, attach a radial effect automatically to every character_image, or change a Wait based on this finding. The26/27 yellow blast and smoke remain separate unknowns.

No original or runtime image was viewed, no source video was decoded, and no browser, application, native method, compiler or installer was run. Only original metadata/ELF, two AnimationClip objects, the directly referenced card prefab/materials and existing transition metadata were read. Processing used nice19/CPU0,1 and bounded threads. Source/formal data/Git/environment were not modified.

## Exact default-image control chain

| Original method / site | Bounded finding |
| --- | --- |
| ADVPlayer.InitScenario0x124d7b0; callsites0x124d90c/0x124d920 | IsAnimeAsset is passed to UI.SetAnimeView. Its character_image case selects card-category mask geometry, not a named Wipe. The previous investigation retains the predicate, mask and UV disassembly. |
| UIController.SetCardImageMode0x1689b6c → View.SetCardImageMode0x1689b84 | The inspected body toggles the normal/movie image GameObjects at View fields0x60/0x68. It does not select a Wipe prefab or radial parameter. See `ui-card-image-mode.asm.txt`. |
| ADVPlayer.CardSetImage0x124edb4 → UI.SetBG at0x124ef3c → UI.SetCardImage0x168bb60 | The original image loader installs `adv_bg001_black`, loads the named texture and creates the card image. Its full loading/instantiation evidence remains in `../target-p30-still006-native-proposal-20261112-v1/`. No Wipe selection is present in those inspected direct bodies. |
| ADVPlayer.CardIn0x124f454 → UIController.CardIn0x16894ac → CardBehaviour.In0x1255404 | The ordinary entry owner plays Card_wait, then Card_in through its existing state machine. It is not the Wipe command owner. See `player-card-in-out.asm.txt`, `behaviour-card-in.asm.txt`, and the prior native state-machine evidence in `logs/cg-timing-fix-20261006.txt`. |
| CardBehaviour.SetAnimeView0x1255b78 / CalcWidth0x1255c10 and CardUVSetter0x1705108 | These affect square card-mask sizing and rendered-card UVs. Their existence does not establish a white radial cover or a new transition duration. |

The original HTML corroborates the separation: CardProc (`logs/adv.html:7216–7259`) awaits SetBG/SetImage, CardIn, phase1, panel, phase2 and normal drop. It separately executes explicit WipeIn/WipeOut command handlers at1598/1618. The HTML is corroboration rather than replacement of the native disassembly.

## Original card clips and the exact affected fields

`original-card-clips.json` is a fresh bounded metadata read of APK members:

- `assets/bin/Data/ceed43112b0d205458494e89adb43d2e`: Card_in,0.5 seconds,8 streamed channels,0 dense curves,9 constant scalars.
- `assets/bin/Data/3ae92e8847c93ff45aae515b5deb25fc`: Card_wait,0.0166666675 seconds,3 streamed channels,0 dense curves,11 constant scalars.

All retained streamed coefficients and constants are finite. The nonfinite stream sentinel times are not animation keys. Binding hashes were resolved against the original scene transform hierarchy, not guessed from the visual shape; see `card-prefab-links-v2.json`.

| Card_in channel | Bound field / values |
| --- | --- |
| 0/1 | `CardTop/move/Card_Frame` RectTransform size x/y960→1980 during the first1/60 second, then constant. This is Card_Frame geometry, not a slowly opening radial mask. |
| 2 | An inactive GameObject binding whose path is absent from the inspected CardPos hierarchy; zero throughout the retained keys. No target or effect is invented for it. |
| 3 | Card_Frame GameObject inactive. |
| 4 | `CardTop/move/mask` GameObject becomes active by1/60 second. |
| 5 | `CardTop/move` anchored Y-40→0 during the first1/60 second, then constant. |
| 6/7 | `CardTop/move/mask/RawImage` and Card_Frame `m_Color.a`:0 at the opening boundary, rising to1 by0.5 seconds. |

There is no streamed radius, named Wipe selection or material Range curve in these bindings. Two additional constant MonoBehaviour attribute hashes are left unnamed in the raw receipt; they are not relabeled as radial controls. The default shader/material checks below are therefore relevant, rather than treating an incomplete property-name mapping as a blanket proof about every possible effect.

## Referenced mask, materials and shaders

The exact scene is APK member `assets/bin/Data/c4f7312e113260a4e8803880a0069bca`.

- `CardTop/move/mask` is GameObject228 / RectTransform949, with Image1367 and Mask1357. Its Image has no sprite and uses no custom material. Mask1357's serialized `m_ShowMaskGraphic` byte at32 is0 (`card-mask-fields.json`), so the white Image color is not itself a visible white cover. Its ordinary stencil mask must not be reinterpreted as the observed white wipe.
- `CardTop/move/mask/RawImage` is GameObject241 / RawImage1356, referencing material file `dca607ceb9776c14da4d21e2065ebff0`, object1, named CardRawImage. Its shader is `Stella/UI/Image-RGB`; the exported original GLES text is `raw-image-native.shader.txt`. The inspected fragment samples texture RGB and multiplies by vertex/tint color; it has no radial-mask or Range input in this material path.
- The instantiated illustration prefab is `assets/bin/Data/54f1215e512b2f145b888053158aa105`, ADVPanel/Quad. Its material file `16f53b7422be48f42825d6cf8eaa1d51`, object1, is CardImage. Its shader is `Stella/BattleBG_Transparent` (`panel-native.shader.txt`), with normal texture/tint/scale and a noise variant. Neither shown variant is a white radial aperture. Generic `_Scale`/`_Weight` properties were inspected, not assumed to mean a radial effect.

These shader exports are diagnostic text, not valid shader source proposed for publication. No textures were exported or inspected visually.

## Separate Wipe owner and the unresolved P30 binding

Native `CommandUtil` declares CMD_WIPE_IN, CMD_WIPE_OUT, a stored `wipe_prefab` and `wipe_asset`. Its Wipe method0x17070a8 reads command arguments, remembers/reuses that explicit state, resolves named transition assets and calls `BX.Sys.WipeMediator.Play`0x1e6c544 at0x17075f8. The bounded bodies are `command-wipe.asm.txt` and `command-wipe-tail.asm.txt`. This is a separate control path from the image loader/normal CardIn.

The native defaults/path fragments were resolved through metadata usage pointers in `extra-chain-and-wipe-literals.json`: `fade_color_black.png`, `wipe_adv_effect`, and `Prefabs/Transition/`. Thus the presence of a white source cover cannot be attributed to an automatic white default merely because a PNG is a still. HTML Wipe.In can inherit a preceding Out's resource/image (`logs/adv.html:5864–5899`), so a later blank WipeIn argument would not prove that no explicit earlier selection existed.

The project already has extracted Wipe prefab/material/finite-curve metadata in `data/story_player/extracted/transitions.json`, sourced from the explicitly configured original prefab list in `story_studio/config/player_assets.json`. That library includes multiple independent patterns and both Fade/FadeAnim mechanisms. **No particular entry in it is bound to this P30 transition by the available original CSV or native invocation data.** Choosing one from a radial-looking silhouette would exceed the evidence. Its generic default duration likewise is not P30's recovered timer.

## Stop boundary and the smallest next observation

The default character_image/CardIn chain has been classified sufficiently for this task; further broad prefab enumeration would not identify P30's missing command. The unknown is the source-specific invocation, not the existence of a usable Wipe renderer.

The smallest decisive new native evidence is the actual P30 command/provider record around10450056:25–28, or an already authorized original-game command-stream observation containing node/phase, WipeIn/Out direction, prefab name, image/color name, normalized start and WipeMediator.Play call. A matching Fade/FadeAnim component and its exact material/finite clip can then be followed from that named asset. This report does not request a new browser or game session and does not propose a guessed phase.

Root's already necessary ordinary25→26→27→28 comparison can separately record the current picture fit and visible absence/difference of this radial cover using existing frame/transition logs. That restored-player observation cannot recover an absent original command or justify adding a Wait. Keep the accepted still identity/cover candidate distinct from the unaccepted radial transition, blast and smoke.
