This is an offline review patch for the next TitleView entry change. Production
source, story data and the independently publishing settled-title change were
not edited. `review.patch` applies to the five selected settled source snapshots
in `base/`; `proposal/` contains the resulting files plus the entry helper.

The implementation reuses the existing finite19-track projection in
`public/player/native-title.json`. Normal/IF selection remains the original
numeric `route_type` predicate, independent of ordinary/end-title transport.
Both selected entry clips carry `OnAnimationEvent` at2.5s. Native Setup passes
its callback into the entry/event binding (RVA168777c–16877a0 →1687c98;
the binding stores its event delegate at1687d84). This supports proposing the
2.5s completion boundary in place of the generic1.6s hold. It creates no story
Wait and keeps phase1 → title → phase2 → existing transition ordering.

The projected sequence is source-derived cubic evaluation, without new easing:

- Normal black layer active, alpha1→0 over0–0.5s; IF black layer inactive.
- Root alpha1 until2.333333s, then fades to0 at2.5s.
- Subtitle/title alpha0 until0.5s, then1 at0.833333s.
- Subtitle/title characterSpacing−10 at0.5s, −2 at0.833333s,0 at2s.
- Scene/number remain absent: native SetText disables those objects despite
  their retained group alpha/Y tracks. Background size and text anchors stay
  on the settled implementation; this patch adds no guessed geometry.

The first-character palette and reviewed tint-index whitelist remain fixed.
Each text layer has its own canvas; changing DOM opacity never changes glyph
bitmap colors/alpha. Only spacing or viewport changes trigger text layout and
paint. Root opacity includes BG/black/text, with a transparent outer flow panel
so a synthetic black fill cannot suppress the native root fade.

Title rows explicitly select native font units. The selected original TMP
excerpt is `../target-p29-clear-native-reference-20261112-v1/TMP-character-spacing-native-excerpt.txt`:
GenerateTextMesh adds raw spacing before current font/glyph scale at10035f4→1003604.
Thus ordinary-glyph design spacing is
`raw * effectiveFontSize / font.point_size * font.scale` (Matisse37/scale1).
Raw−10 means−32.432432px at120,−13.513514px at50. Existing dialogue rows retain
their current spacing unit. Rich-size, sprites, per-glyph scale and compressed
width variants are outside this narrow conversion.

The original selected prefab Animator19 explicitly has `m_UpdateMode:0`
(Normal), recorded in `title-prefab-layout.json`. The helper therefore uses
the existing `public/studio/visual_frame_clock.js` now/subscribe interface.
The2.5s boundary is native clip/game-frame time, not an independent wall-RAF
interval. Existing capped deltas and preview-rate ownership remain shared with
native transitions. The helper owns one subscription only. StoryPlayer supplies
the existing generation check and pending-cancellation set. Checks run before
paint and at completion; all success/cancel/error paths clear subscription and
pending ownership without resetting or disposing the document clock.
NativeTitleView additionally refuses a stale presentation handle. No view
introduces another playback generation or independently follows story edges.

ARM `node --check` passed for all five proposed JS files. Bounded offline checks
passed for finite sampling/source endpoints,2499/2500ms **clip-time** completion,
the actual shared clock's capped hitch behavior, generation change, stop
cancellation, late callbacks and paint-error cleanup. The first draft's separate
wall-RAF timing was corrected before this review packet was finalized. These checks
are source validation, not original-video or browser acceptance. The static
patch can publish separately; root/peer must review and run this candidate
before accepting actual animation fidelity.

Limits remain explicit: exact TMP auto-fit/baseline/material-outline behavior,
decorative orb materials/effects, async LoaderSetNativeSize side effects and IF
recording comparison are unverified. `adv_skip_char_color` remains unknown;
the closed bounded search is not reopened and quoted-title tint is not guessed.
Raw Unity NaN tangent diagnostics remain untouched. The shared Normal clock owns
native maximumDelta/timeScale and preview speed; this helper never assigns a
separate speed or clock owner. Source/video comparison must assess normal ordinary
title, P29 CLEAR/end flow and IF separately; preserving the accepted first-three
scripts is required. No render, acting, browser, install or publication claim
is made by this author packet.
