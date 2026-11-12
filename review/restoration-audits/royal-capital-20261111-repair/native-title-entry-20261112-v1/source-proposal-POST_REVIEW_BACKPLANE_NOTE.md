The proposal's transparent outer-panel inference is withdrawn. Preserve
`review.patch` and its author report as provenance; the root implementation
correctly retains `.native-title-view { background:#000 }` throughout title
presentation while the native animated root fades its children to zero.

The later direct original P29 tail review found overall darkening at753.121s,
full black at753.154s, continued black through754.221s (Connecting), then the
chart at754.254s. Neither the old stage background nor the chart shows through
the title fade. A transparent outer panel was therefore not supported by that
recording. Keep the black backplane until TitleProc completes. This correction
does not add a story Wait or simulate the recording's network delay.

No production source was changed by this follow-up note. The shared Normal
clock, native2.5s event boundary, alpha/spacing tracks and generation ownership
are unaffected. Independent actual-frame review is recorded separately under
`../../target-native-title-entry-runtime-20261112-v1/native-entry-image-review.md`.

Further direct ordinary-title evidence limits the correction above to the end
case. Original P29 ordinary frames0131/0132 at approximately433.333/433.367s
show the sharp stealshop room under the fading collage/title;0133 is room only.
The initial runtime normal-ja instead fades to black and introduces the room
later. Therefore neither an unconditional transparent panel nor an unconditional
black panel is accepted for every title. Root is separating the presentation by
the existing typed `title_mode`, retaining black for end titles, with ordinary
stage/lifecycle behavior pending a new actual capture. Route type and the text
"CLEAR" must not select this behavior. The final goal is the source-visible
underlying stage, not merely removing a CSS fill. No production change was made
by this additional observation.
