# P29 observed ending: minimal terminal FINISH proposal

Proposal only. No repair builder, compiler, player, installer, browser or server was executed, and no formal data/source/Git file was changed. The companion draft is deliberately noninstallable. This review reuses the full original-tail review in `target-p29-five-missing-edges-source-audit-20261112-v1/REPORT.md`; it adds no image or audio acceptance.

## Source-backed result and the missing native payload

The reviewed sequence is existing scene10040053 node49 (`s10040053-p29-at0740`, branch491), the complete native `adv_dive01_out`, then `CLEAR` / `本編：ユリウスVer.`, followed by the chapter chart with END and its reward popup. No automatic1045 entry appears before the recording ends. The current scene still ends at49, its maximum scenario ID is49, branch491 has an empty transition list, and its video list is empty. Existing node49 text, IDs, commands and other fields should remain intact apart from the separately reviewed connection.

The original game does support FINISH without a real successor. This is stronger and narrower than inventing a new completion opcode or a destination1045:

- Preserved original `data/localization/ja-originals/main/rezelos-2020-intro.json:2356–2361` has TITLE41 `GAME OVER` with FINISH, `next_scenario_id:0`, and destination pair `-1,-1`. Its last card102 has FINISH transition10701 at`:5307–5311`, with both destination fields absent. These are captured original objects, not Studio-generated transitions; their provenance is retained in `data/localization/ja-originals/manifest.json` and points to `data/captures/rezelos-2020-intro.json` / the original `story/1/0/1.json` source. These examples establish supported native representations; the GAME OVER and tutorial contexts do not recover P29's exact payload.
- Original `logs/adv.html:7051–7084` distinguishes FINISH from an ordinary local node link. For normal ADV, a same-section FINISH loads the specified next scene; a different-section FINISH calls `FinishScenario()` instead. That function calls `ADVFinish(isClear)` (`:7312–7321`), and its bridge dispatches `ADVFinish` without a successor argument (`:2858–2876`). A missing or`-1` section takes that different-section branch in this JavaScript. Tutorial0 has a separate explicit exception which requests section1; do not transfer it to P29.
- The master `is_end` flag draws the END marker; it is not an executable FINISH. Likewise CLEAR wording is presentation text, not an execution signal. Existing `story_studio/flow.py:31–45` documents native end-title classification from TITLE plus FINISH, not its wording.

Therefore an explicitly **authored, source-backed P29 terminal FINISH with no destination** is a reasonable reconstruction proposal. It must retain `originalPayloadRecovered:false`; neither the particular omitted-field representation nor its authored IDs were recovered from P29.

## Present builder and player behavior

`story_studio/recovery/native_repair.py:252–258` unconditionally requires a positive `packet.finish` successor/root. Its final connection at`:299–303` always supplies that destination, and`:332–343` adds the resulting map line across owned documents. `build_reviewed_unique_endings.py:19,35–37,87–90` intentionally excludes P29 and only packages unique master successors. Expanding its part set or choosing matching route1045 would exceed the evidence.

The canonical compiler currently classifies a TITLE as an end title when it has FINISH (`lib/preview.ts:39`). The player then skips the opening chart, runs title phase1, displays the title for the existing1.6s presentation setting, runs phase2, and follows its sole edge (`public/player/player.js:627–659`). That1.6s is existing renderer behavior, not a P29 timing recovery. A cross-section FINISH already stops media/card work, retains the existing music handle, marks the source scene complete, and shows the completed section chart (`:608–621`); it does **not** automatically play the referenced next section. Its present status text nevertheless asserts a next-section target. `flow_view.js:55–58` makes the completed chart's continuation button disabled. Original reward accounting/popup and the native CLEAR collage remain separate presentation gaps.

Appending an ordinary TITLE with an empty transition would open the chart before CLEAR and then fail at the missing edge. A same-section/self/root FINISH would instead enter another scene or loop. Neither is the required terminal behavior. Current native validators also reject omitted or`-1` FINISH destinations (`native_rough.py:716–721`; canonical `lib/native.ts:64`), despite the original examples.

## Exact narrow schema and code changes proposed

1. **Repair-packet ownership:** add a version2 ending packet discriminator `terminal:{kind:"finish-without-successor",nativeRepresentation:"omitted-destination-fields",rootConfirmed:true,evidence:[...],originalPayloadRecovered:false}`. It is mutually exclusive with legacy `finish:{sectionId,sceneId}`. This belongs to the repair/evidence packet and its review sidecar, not a new native field. Keep the old positive-target mode and directory checks unchanged. The companion draft has approval false and cannot be passed to the current importer.
2. **Builder:** in `ending_sequence`, keep the existing guarded empty branch, suffix-only allocation and old-row preservation. In terminal mode append only door/TITLE, emit ordinary internal links, and emit final FINISH with `next_scenario_id:0` and **both destination fields omitted**. NativeIdentifiers allocates new authored IDs only; no IDs from the intro are copied. Retain `nativeIdOrigin:"authored"`, `originalScenarioIdRecovered:false`, `originalPayloadRecovered:false` and unknown phase/audio metadata. Mark terminal branch provenance reviewed/authored, not `verification:"original"` as the existing final-branch path does. Skip the entire map-edge propagation block for terminal mode: no1045 edge and no unrelated native document changes.
3. **Native validation:** accept the exact terminal FINISH alternatives below in both Python staging/install validation and canonical TypeScript validation. Preserve original omitted fields or `-1,-1` on read/write; do not normalize them into0 or a real section. Partial destination pairs, nulls, zeros, invalid numeric values, and destination-free FINISH with a nonzero local node remain errors. Positive destination pairs retain current validation. Blank transition lists stay unresolved.
4. **Compiler ownership:** derive `flow_action:"complete"` only from the explicit recognized native terminal FINISH. Keep `native_transition` equal to the supplied native object, `target:""`, destination display strings empty, and `available:true` for that valid terminal action. Do not synthesize `section:0`/`scene:0`. TITLE remains `title_mode:"end"` because of its real FINISH label. No inference from CLEAR, master layout or absent ordinary edges.
5. **Player ownership:** make terminal `flow_action:"complete"` reuse the existing completed-section/chart lifecycle alongside the positive cross-section FINISH path. Report simply that the chapter ended, without asserting another section. It must return before node lookup/enter. Reuse the actual traversed route and existing cancellation behavior; do not register or follow1045. No new renderer completion field is needed on native rows.

The shared recognition rule should be this narrow (illustrative TypeScript; not implemented):

```ts
function isTerminalFinish(tr: NativeTransition): boolean {
  if (tr.next_scenario_label !== "FINISH" || tr.next_scenario_id !== 0) return false;
  const absent = !Object.hasOwn(tr, "next_section_id") &&
    !Object.hasOwn(tr, "next_scene_id");
  const sentinel = tr.next_section_id === -1 && tr.next_scene_id === -1;
  return absent || sentinel;
}
```

This is compatibility with observed original native forms, not proof that P29 used either form. Before implementation acceptance, focused checks should cover both original terminal examples, an ordinary missing edge remaining unavailable, a positive same-section FINISH retaining scene entry, a positive cross-section FINISH retaining completion, malformed pairs remaining errors, and the authored P29 terminal producing no map/destination. No broad byte audit is needed to decide this semantic change.

## Door continuation, phases and music still need explicit authorship

The complete movie already plays to its `ended` event (`player.js:661–672`). With all three command strings empty, the movie subsequently reaches `ready` and waits for ordinary user Continue (`:493–523`), rather than automatically proceeding to CLEAR. Existing phase2 `CardOut` would remove that extra click (`:190–198,520–522`). If root chooses it, `command:["","","CardOut"]` is a minimal **newly authored playback convention**, not a recovered P29 command phase. This report proposes that convention only as an explicit separate decision. It does not choose `Wait,500`, `StopBGM`, another phase placement or source-timestamp waits.

The draft therefore leaves native commands and BGM null/pending. Null cannot be serialized into native command/string fields. Root must explicitly resolve authored defaults/conventions before any staging. An empty BGM field would actively inherit upstream music; it is not a claim of silence or a recovered P29 music assignment. The old waveform candidate does not authorize `bgm_btl_adv_win01` here. The existing completion path's `keepMusic:true` also does not establish source audio correctness. Door audio, BGM stop boundary and CLEAR cue remain unaccepted.

The practical next implementation is thus terminal-FINISH compatibility plus the explicitly reviewed two-node suffix, with any chosen automatic-movie continuation labelled authored. The next ordinary playback must verify full door → CLEAR → completed1004 chart and no1045 entry; it cannot be called a fully faithful ending while music, exact phase/timing, collage and reward presentation remain pending.
