# P29 CLEAR exit: observed exposed presentation

The source-visible result is **the complete CLEAR title presentation darkening to black, followed later by the completed chart**. The prior weapon-shop background does not become visible during this exit, and the chart is not visible underneath the fading CLEAR collage.

This focused review reused the already extracted original frames. The reviewer directly viewed `original-ending-tail/contact-08.jpg` (all frames421–480 in order) and full frames0424,0425,0457,0458 under `../target-p29-five-missing-edges-source-audit-20261112-v1/`. No extraction, browser, replay or production change occurred.

| Existing source frame | Source PTS seconds | Direct visible observation |
| --- | --- | --- |
| 0421–0424 | 753.021–753.121 | The original normal collage and both text lines darken together; at0424 they remain dimly visible against black. No earlier scene or chart appears. |
| 0425 | 753.154 | The game area is black; the recording watermark remains. |
| 0426–0457 | 753.187–754.221 | Black persists. A bottom-right native `Connecting` indicator becomes visible during this interval; full0457 shows it clearly. |
| 0458 | 754.254 | The completed chapter chart appears, including `今度こそ取り戻す → END` and Julius route text, while `Connecting` is still present. |
| 0459–0480 | 754.287–754.987 | Chart continues and the reward popup appears. |

These observations establish the required visible black exposure for this transition, not the original engine's precise alpha object hierarchy or whether its black comes from an underlying plate, a scene transition owner or another original view. In particular, the finite root-alpha animation alone does not establish what the web component should reveal beneath it.

For the proposed native entry animation, allowing the transparent/fading title root to expose the previously installed script background would disagree with this P29 source transition. The title presentation lifecycle needs a black exposed surface through its root fade, with the chart replacing it after completion. Root owns the implementation and actual playback comparison. The retained Connecting interval is an observed loading boundary, not an authored Wait duration; no new Wait or network-delay emulation is proposed. The existing static1.6-second title acceptance remains separate from this unaccepted2.5-second animation work.
