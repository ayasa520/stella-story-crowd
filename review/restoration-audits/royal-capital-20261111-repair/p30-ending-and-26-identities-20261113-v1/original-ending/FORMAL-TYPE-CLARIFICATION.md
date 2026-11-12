# Correction: node35 is already a native TEXT/narration node

The earlier report incorrectly called node35's authored numeric type1 a TITLE.
That was this review's enum interpretation error. The directly observed source
picture and the preserved formal numeric value are unchanged.

The canonical production definitions are explicit:

- `artifacts/stella-site-repair-source/.sites-checkout/lib/native.ts:20`:
  `0:"标题",1:"文章",2:"对白 / 卡片",3:"短片"`.
- `artifacts/stella-site-repair-source/.sites-checkout/lib/preview.ts:35` maps
  `row.scenario_type` through `config/semantics.json` to the compiled `kind`.
  That config maps0 to`title`,1 to`text`,2 to`card`,3 to`movie`.
- `lib/preview.ts:39` selects title mode only when the resulting kind is
  `title`. Therefore type1 does not dispatch NativeTitle presentation.

At the bound immutable data commit
`0108b5f6c260d62d585f613facba2f3535ac8920`, scene10450058/node35 retains
`scenario_type:1`, sourceText`―完―`, translated`——完——`, no character, and
an empty continuation on branch351. Its existing type1 is correct for the
source's actor-absent rectangular narration panel over the ruins.

The term"authored TITLE35" in `REPORT.md`, `source-review.json`,
`RESOURCE-NOTE.md` and the preceding ordinal150–end review is a mistaken
human label, **not the actual compiled type or a reason to change it**.
Those historical artifacts are preserved; this note explicitly corrects
their interpretation. No formal type change or conversion is required.

The remaining structural gap starts **after** this correct narration row:
the source shows the full closing door, a separate type0 CLEAR title, then
the own-episode END chart/reward. Any reviewed authored suffix must preserve
node35 and all existing IDs, and must not infer a next chapter from the
recording's final reward screen. This correction changes no formal file,
old evidence, source image or previously delivered draft.
