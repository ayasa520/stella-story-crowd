# 第一章显式场景连接窄核（rootfalse）

**直接可修候选为 0。** 当前第一章除前三话的 31 话／路线，已有明确正目标的 119 个场景对，全部保留在 own-chart 和实际目录投影规则中；未发现已有原生目标却遗漏目录边或指错 section 的点。没有新增连线、执行程序或正式数据修改。

本次绑定 D `026a7c4ca58ff3f7be483b0976d7807de3d55732`、C `6630ac70f17332efa031d021af00532d42307568`。按旧 sealed 报告排除 sections `1001/1014/1019`，未读取其 22 个 native/review 文件。当前范围是 144 个目录场景、129 份已恢复 native、5300 行；15 个缺脚本场景明确保留。609 是先前全目录卡片数量，不能当作每话实际绘线验收。

本次只刷新 native 场景目标投影：120 条正目标 FINISH 对应 119 对连接，均有 own-chart 和 effective directory edge，目标脚本均存在；没有多 transition 分支或不一致的 target section。唯一重复对是 `10090013/26/261` 与 `/27/271` 均到 `10090014`，后者沿用既有 intentionally superseded 分类，不另补线。119 对及 120 个正目标对象与旧 `scene-flow-fresh-catalog-audit-20261122-v1` 完全一致。14 份 native 全文件 SHA 已有正常发布变化，不能声称整个文件不变。34 条原 master section 关系也都保留。

当前仍有 227 个空分支（211 choice、16 next）和 6 个无目的地 FINISH，后者包含后来正常保存的 P21/P22 结尾。这些不是有依据的新场景目标；本次不改变 terminal，不把空分支补到相邻卡。先前全 267 sections 审计及 `remaining-chapter1-native-edge-candidates-rootfalse-v1` 直接引用，未重做全目录统计／原片审核。

## 第10话 1045

五场景 180 行，四条明确连接为：

| source → target | 原生 scenario / branch | transition UID | 原生文件转移行 |
|---|---|---|---|
| 10450054 → 10450055 | 52 / 521 | 1045005410521 | 2494 |
| 10450055 → 10450056 | 20 / 201 | 1045005510201 | 943 |
| 10450056 → 10450057 | 53 / 531 | 1045005610531 | 2542 |
| 10450057 → 10450058 | 18 / 181 | 1045005710181 | 877 |

四条原生 FINISH、各自 own-chart 目标和既有 review `repairEvidence.maps`／`graphs/result-v2/chart-overlay.json` 逐对象一致。后者 `/changes/59..62/additions/0/evidenceRoutes/0` 记录已审核的 **source → named-title handoff**，有明确的 `handoffKind`、前台词及目标标题证据；不是从录像邻接或 ID 顺序新推断。原 captured foreign chart 行的 `next_scene_list` 都为空，不能把这些恢复边冒称成已恢复的原版 1045 chart payload。本次不读取图片、重新签 source 审核。

54/22/223、56/22/223、57/7/72、57/17/172、58/21/213、58/26/262 的六个 choice 目标仍未知。58/37/371 的 FINISH 没有目标字段，own-chart 也没有后继；保持结束。各 UID、JSON pointer、整对象 SHA 和旧来源均在 findings 中。

## 两层目录与 renderer

- `lib/story-directory.ts:57–94`：master／manifest 提供卡片，own-chart 生成 scene 边，保存的 override/deletion 随后生效；位置和顺序不生成连线。
- `lib/directory-flow.ts:6–37`、`public/studio/directory_flow.js:8–29`：按所选话及 revision 取全话 native 边，独立于 active workspace；返回身份不符／失败会留下错误。
- `public/studio/directory.js:247–287`：本话图使用所选 section；ready 返回的边完整传给 map。`directory_map.js:56–93` 对每条可见 source 边生成 line 与 hit 两个 path，外部目标生成 portal；END 装饰 path 另算。
- 本章各话使用 section 关系，与本话各场景的 native chart 边分开。1045 收到 `section-edge:1004:1045`；原 master 的 1045 `next_section_id=[]`、`is_end=true` 不提供新的场景后继。
- `lib/preview.ts:60–84` 的 dialogue-node 可执行图另有 missing／terminal 语义，不能因 node 图某处无边就判定目录 renderer 漏画。

1045 源码预期 **5 cards / 4 edges / 8 connection paths / 0 portals**。六个图构建／编译源文件与旧封存 SHA 一致。未执行浏览器或 API，因此没有新的真实 DOM／SVG 可见验收；这与“未发现静态漏边”分别保留。

下一步没有可提交的 leaf 修复。如需确认用户所见缺线，应由 root 另行授权普通 UI 选择 1045 并保留真实 revision、flow response、DOM/SVG 和错误日志；本包没有创建或执行 runtime helper。

`observations.rootfalse.json` 保留一次原 Adv.d 的 `sqlite3.DatabaseError: file is not a database`；未解码、重试或推测格式／原因。上述 master 结论引用已存在、重新绑定 SHA 的 `native-directory.json`，不将其当作本次成功读取 Adv.d。另一次 inspection 误用 manifest 的 `nativePath` 键造成 ENOENT，已明确属于本包检查代码的路径键错误；实际键为 `path`，不混同 JSON／业务门禁异常。

全部结果仍是 rootfalse，只供复核；没有执行、保存或绘图验收授权。
