# Concrete patches for parent review

These patches are proposals only. Their production destinations were read, not edited. No P29 native/review packet, commands, music or map data was changed. The earlier `REPORT.md` and noninstallable draft are preserved.

Apply/review roots are deliberately separate:

| Patch | Intended checkout root | Scope |
| --- | --- | --- |
| `runtime-terminal-finish.patch` | `artifacts/stella-site-repair-source/.sites-checkout` | Shared TypeScript destination classifier, native validation, compiler projection, player completed-chart handling. |
| `python-terminal-finish.patch` | Project root | Matching classifier and Python native validation. Three existing rough-compiler destination reads also skip terminal forms, preventing an absent-field KeyError after accepting the original-native form. |
| `builder-terminal-option.patch` | Project root | Optional, separate v2 ending-packet terminal mode. Legacy positive-target endings retain their existing checks and map path. Terminal mode records authored provenance and returns before map propagation. |

`prepare_patch_proposal.py` produced exact-context unified diffs and review-only candidate copies under `patch-candidates`. It fails rather than overwriting a patch. It imports only Python standard-library modules, reads production sources, and writes only here. No candidate was imported or run. Both Python candidate files passed `ast.parse`; the player candidate passed `/usr/bin/node --check`. TypeScript type checking, semantic execution, installer execution and actual playback were not performed by this task.

The destination rule is identical in both languages: FINISH plus a nonnegative safe integer next node; terminal only at next node0 with both destination properties absent or exactly numeric`-1,-1`; otherwise both destination numbers must be positive safe integers. Partial/mixed/zero/null pairs remain invalid. The compiler also uses the shared classifier, so a malformed section value cannot become an available cross-section completion just because it differs from the current section. Source transition objects are never rewritten.

For a valid terminal, the projected edge has `flow_action:"complete"`, `available:true`, `target:""`, empty section/scene display strings and empty `target_scene`; `native_transition` remains the original object. Positive same-section and cross-section FINISH retain their existing scene/section actions. The player reuses the existing completion block for complete/section, returns before node entry, and says `本话已结束。`. It retains the existing music handle without assigning a cue.

The optional builder packet owns the new field: `version:2`, with `terminal:{kind:"finish-without-successor",nativeRepresentation:"omitted-destination-fields",rootConfirmed:true,evidence:[...],originalPayloadRecovered:false}` and no non-null `finish`. Exactly one mode is required. The final authored transition omits both destination fields; final branch metadata says `verification:"observed"`, `nativeIdOrigin:"authored"`, `nativeTransitionOrigin:"authored"`, `originalPayloadRecovered:false`. This does not recover P29's original IDs or payload. The current noninstallable P29 draft still has approval false and null command/music decisions.

## Meaningful ad hoc checks after parent application

Use the actual patched classifier, native validator and compiler rather than reimplementing the expected rule. No unit test files are proposed.

| Input | Required result |
| --- | --- |
| Preserved intro102 FINISH, next node0, both destination fields absent | Python/TS classify terminal; native validators accept that destination shape; compiled complete edge has empty destinations and unchanged native object. |
| Preserved intro TITLE41 FINISH, next node0, destination`-1,-1` | Same terminal result; preserve the negative pair verbatim in the raw native object. Do not copy GAME OVER text/semantics into P29. |
| Valid positive same-section FINISH to an explicit scene/root present in sources | Classify target; compiler action scene and actual root target; retain current availability and scene-entry behavior. |
| Valid positive cross-section FINISH | Classify target; compiler action section and current completion behavior; target provenance remains intact. |
| Absent pair with nonzero next node; only one destination field;`-1,positive`;`positive,-1`;`0,0`; explicit nulls; booleans; fractional or unsafe numbers | Classify invalid; native validators reject; compiler edge remains unavailable with invalid-destination error. No complete/section action becomes available. |
| Ordinary branch with an empty transition list | Remains missing/unavailable. CLEAR wording and master is_end must not change that. |
| Fresh in-memory builder packet with both finish and terminal, neither mode, terminal approval false, missing terminal evidence, or version1 terminal | Reject before any suffix mutation. |
| Fresh in-memory reviewed v2 terminal builder fixture | Append only reviewed suffix, retain existing IDs/array order, emit destination-free final FINISH, retain authored provenance, and add no map edge/change to another scene. Use a fixture, not formal P29, until phase/music decisions are separately approved. |

A focused lifecycle check should supply a compiled terminal edge to the actual player completion path and verify complete phase, completed source scene, final chart, message, cancellation and no `enter` call. A positive same-section FINISH must still enter its destination. These checks establish control flow; they do not accept CLEAR collage/reward UI, audio or P29 phase conventions. Parent owns application, executable checks, publication and the eventual single ordinary playback.
