# P30 still006: native ID and bounded integration proposal

**Resource naming is sufficiently established for a reviewed integration using bare `ADV_still_006`. The current `#picture` contain presentation is not the source-framing target for this still. A resource-specific centered cover profile is the smallest concrete candidate for actual comparison; complete native projection equivalence remains unproved.** No image was viewed in this task, and no browser, application, compiler, installation, formal data/source or Git mutation occurred.

## Native ID and loading chain

The original APK1.19.7 ELF and decrypted metadata were inspected offline. The Assembly-CSharp module pointer table was admitted only after CardSetImage and SetAnimeView both matched their established native addresses; metadata method tokens were resolved within that module, not treated as addresses. `native-methods.json`, bounded `.asm.txt` files and `literal-bindings.json` retain the relevant evidence. The companion source reviewer independently resolved the same callees in `../visual-high/target-p30-spell26to28-source-review-20261112-v1/native-image-binding-v2.json`.

1. `ScenarioUtil.GetImageAssetName` at0x1712440 reads `ScenarioData.character_image` at offset0x60. For a **bare ID with no slash**, it returns its `ToLower()` result directly (0x17124a4–0x17124d4). Thus `ADV_still_006` deterministically resolves to `adv_still_006`.
2. For a slash-containing value, this native function uses `String.IndexOf("/")`, takes the original string's suffix after that **first** slash, then checks for `adv_` and may prepend it (0x17124d8–0x1712528). This is not a universal last-directory/extension sanitizer. The HTML version at `logs/adv.html:2198–2221` instead strips through the last slash and conditionally adds `adv_`; its arbitrary-path behavior must not be substituted for the native implementation. The proposal avoids this difference entirely by using a bare ID.
3. `ADVPlayer.CardSetImage` calls that helper at0x124edfc. It sets the display background to exact literal `adv_bg001_black` through UI.SetBG at0x124ef3c, then appends exact literal `.png` at0x124ef60 and calls UI.SetCardImage at0x124efdc. Do not include `.png` in the native field: it would be appended again.
4. `UIController.SetCardImage` at0x168bb60 calls `AssetBundleLoader.LoadAsset` with that texture name, and its callback0x168efa4 delegates the texture to `View.SetCardImage` at0x168f118. `ADVAssetsLoader.LoadImage` at0x1246780 similarly appends `.png` before loading. No new `still/` or `images/adv_still/` native-field prefix is required by this chain. The physical extracted member path is provenance, not the script ID.

The literal associations were resolved through actual metadata usage kind5 entries and the ELF's metadata-usage pointer table: `adv_` literal8308, slash1748, `.png`11 and `adv_bg001_black`81. They were not chosen from nearby string matches. `SetScriptParamater`'s relevant array-scan assignments write sparse script background/BGM (0x1718344/0x171835c); image asset-name construction belongs to the dedicated helper above. The displayed black background is separate from that script-background state.

The preserved first-episode source has bare `ADV_pic_101001` and `ADV_pic_101008` character_image values, and all seven current catalog picture keys retain that uppercase filename-stem convention. Bare `ADV_still_006` follows the same existing repository convention while the original native loader resolves its lowercase name. This does **not** recover P30's original CSV spelling or path.

## Smallest resource addition

Root's independent visual reviewer has identified the exact full source texture:

`data/extracted_archives/limeos/LIMEOS/assets/downloadassets/assetbundle/images/adv_still/ADV_still_006.png` —1536×2048.

The proposed resource key is `ADV_still_006`, with the full original PNG copied to `story_crowd_data/assets/pictures/ADV_still_006.png`, plus a single `assets/catalog.json.pictures` entry:

```json
{
  "ADV_still_006": {
    "label": "ADV_still_006",
    "url": "pictures/ADV_still_006.png",
    "member": "LIMEOS/assets/downloadassets/assetbundle/images/adv_still/ADV_still_006.png",
    "thumbnail_url": "pictures/ADV_still_006.png"
  }
}
```

Pointing thumbnail_url to the same full payload matches the existing seven entries; it does not authorize copying a small thumbnail as the payload. Preserve PNG dimensions, alpha and content. The existing guarded asset publication path must also account for its member mapping and file/member provenance. No existing picture entry needs replacement. `app/picture/[id]/route.ts` and `lib/resources.ts:72` already resolve an exact catalog picture key to its URL; a new image-serving route or guessed compatibility alias is unnecessary.

`StoryMediaCatalog` currently scans only `settings.picture_prefix`/filename_prefix (`story_studio/media.py:37–45`), configured to the adv_pictures family in both Studio configurations. A durable future rebuild therefore needs a second configured family for the actual adv_still directory and `ADV_still_` filename prefix, retaining duplicate-key rejection and the old family. A small family list with the legacy single-prefix fallback is the cohesive extension. The already-published Site can consume a guarded catalog addition independently; do not rebuild the entire asset package just to discover this one texture.

After the source reviewer/root approves the node packet, only the directly observed10450056:26/27 `character_image` fields need the bare key, with their actual blank-field/stable-key preconditions. Both nodes should explicitly retain the same illustration resource rather than treating a blank native field as picture inheritance. The existing same-image transition check can then preserve the image across their text, and28 can use its own separately reviewed content. This investigation does not approve node28's acting, scenario types, commands, waits or any motion token.

## What native geometry actually establishes

Input texture ratio3:4 is not, by itself, the final card or viewport geometry. The original rendering path is a composed scene:

- InitScenario callsite0x124d90c passes `ScenarioUtil.IsAnimeAsset` to UI.SetAnimeView at0x124d920. The predicate at0x17178a0 includes **nonempty character_image**, as well as its separately checked movie category. UI.SetAnimeView0x168bc50 selects CardBehaviour.SetAnimeView0x1255b78; that sets a square mask of width `CalcWidth()` (0x1255c10). At the reference1080×1920 canvas/viewport, that width is1080. This square card mask does not mean the still PNG should be cropped to a square before publication.
- `View.SetCardImage` instantiates the ADVPanel prefab using scale `Screen.width*16/(Screen.height*9)` (0x168f2b4–0x168f360), centered position(0,0,-6.7), and assigns the input texture to its renderer. The corresponding original prefab is APK member `assets/bin/Data/54f1215e512b2f145b888053158aa105`; its ADVPanel/Quad transforms and renderer reference are retained in `native-advpanel-prefab.json`. The parent render-space camera is a separate30-degree perspective camera at z-10, not the web image element.
- View.SetCardImage calls CardBehaviour.SetCardImageRatio with `Screen.width/Screen.height` at0x168f470–0x168f4a0. That delegates to CardUVSetter.SetRatio0x1705298, which only lowers the stored ratio. InitRatio0x170528c resets it to1.
- CardUVSetter.LateUpdate0x1705108 constructs a centered UV rectangle for the **rendered card texture** and writes RawImage.uvRect at0x1705268. With ratio p and serialized wh/v, its final rectangle is `((1-p)/2, v+(wh-p)/2, p, p)`, after the bounded rect-width adjustment. The original scene's serialized values at bytes32–43 are `(0.5625,1,0)` and the reference9:16 ratio selects p0.5625. These are render-texture/card UVs, not a crop recipe to apply directly to ADV_still_006.

`native-prefab-geometry-v3.json` is the corrected geometry readout. The earlier v1 used the wrong MonoBehaviour field offset and v2 had a diagnostic variable-shadowing error; neither is the authority for the serialized ratio or transform inventory. The final script explicitly accounts for the installed ARM UnityPy load_file API and did not alter that environment. These investigations only read serialized objects, transforms and cameras; no texture pixels were decoded or displayed.

This proves that native presentation involves camera, mask and render-texture UV stages. It does not yet establish their complete final numerical transfer to CSS, particularly the runtime render-target sizing and all material/camera state. Do not call either generic CSS contain or generic cover a complete native renderer projection on this evidence alone.

## Concrete geometry candidate and its acceptance boundary

The source reviewer `/root/p30_felt_entry_review` supplied an **already completed** original-frame observation for CG26 (for example529.999s): the steady image fills the approximately9:16 story area, while the1536×2048 PNG's outer left/right content is excluded. It is not the complete3:4 image inset with upper/lower letterbox. White edges belong to the radial transition, not steady letterboxing. This message reuses the reviewer's existing image work; this task did not request or perform another visual review.

The current shared CSS is `#picture,#movie { ... object-fit:contain }`. At a logical1080×1920 viewport, contain displays this texture at1080×1440, y240, leaving240-pixel upper/lower margins. That is a concrete mismatch with the transferred steady-frame observation. The smallest candidate is **only for resource ADV_still_006**: object-fit cover, centered50%/50%, retaining the full input PNG and black display plate. At1080×1920 this gives1440×1920 at x-180/y0, equivalently excluding192 original source pixels from each side. These values are mathematical consequences of the candidate fit, not recovered native crop constants.

Use an isolated picture-presentation helper/config, analogous to movie_view's resource policy, and assign/reset the profile on **every** picture resource change. A proposed internal configuration is `illustrations.default_fit:"contain"` and `illustrations.resources.ADV_still_006:{fit:"cover",position:"50% 50%"}`. Existing seven ADV_pic entries retain their current behavior. This belongs to renderer configuration, not native scenario CSV or a source-derived command. Avoid a global picture/movie fit change or a per-scene scale constant.

For root's next necessary26→27→28 QA, retain one bounded image-load/layout event with resource, natural dimensions, viewport/card/image element rectangles, selected profile/fit/object-position and effective display background. The existing CardIn/CardOut/commit logs can establish lifecycle. The independent image reviewer should compare the same CG landmarks and visible side boundaries against the already reviewed full source interval, including transitions and return to actor. Accept or revise the profile only on that comparison. No source-time Wait, inherited thumbnail, guessed motion or new native command is required by this proposal.

The naming/resource plan can be reviewed now. The resource-specific centered-cover geometry is a concrete candidate with a remaining actual-playback comparison; exact native camera/UV/material equivalence and radial transition fidelity stay explicitly unknown.
