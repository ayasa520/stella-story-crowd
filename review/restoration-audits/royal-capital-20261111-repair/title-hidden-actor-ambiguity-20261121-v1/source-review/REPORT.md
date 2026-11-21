# scene10100012 TITLE：上游身体动作提示与当前呈现范围

当前这句“这里的背景、身体动作会随来路变化”把**保存的上游 body 差异**当成了**标题实际需要的身体动作**。两个上游的 body 确有差异，但当前标题没有人物，随后 node3 也为空人物并明确设置水果店背景，node4 才以显式 `act_tameiki` 重新出场。这条正常路线中，旧 body 不应阻塞 TITLE；真实背景冲突仍须选择入线。

本包只提供离线证据和候选 v2，不表示正式修好。`rootConfirmed=false`、`formalApplied=false`、`browserExecutionReleased=false`、`serverExecutionReleased=false`、`nativeAppRun=false`。正式数据、canonical 源码、renderer、时钟、脚本均未修改；没有 browser/server、安装、commit 或 push。CPU 0,1、nice 19，复用 ARM 工具和既有原生证据；没有提取或复制录像/帧。空间恢复后本包新增远小于 5 MB。

## 当前真实数据和两条来路

固定版本：data `db23843217c80693e893279c1f60760105997510`（干净），canonical HEAD `7f32a3cde97d9a379828619242d2ba12f94f6514`。保留 root 已授权的两个 Player retirement JS 工作区改动和原有 `scripts/__pycache__/`；其字节在 probe 前后核对一致。`input-binding.json`、`candidate-input-binding-v2.json` 记录文件 SHA、工具 SHA 和工作区状态。

目标唯一 ID 以当前 review sidecar 实际投影为准：

`node:10100012:node_869ba28d7d51`，scenario 2、uniq_id `1010001200002`、原生 JSON `scenario_type=0`、root、标题“前往贫民街”。当前 authored character/motion/bg_picture 均空；command 为 `["StopBGM","",""]`。

| 正常入线 | 当前来源 JSON | 解析 model | 解析 body | 解析背景 |
| --- | --- | --- | --- | --- |
| 未选 | 两条 FINISH 合流 | `subaru01` | `null` | `null` |
| scene10100011 / node33 / branch332 | character=`live2d/AC_subaru01`，motion=`act_unazuku02` | `subaru01` | `act_unazuku02` | `bg/bg018a_bridge` |
| scene10100019 / node18 / branch181 | character=`live2d/AC_subaru01`，motion=`act_nayamu` | `subaru01` | `act_nayamu` | `bg/bg039a_castletown` |

来源 stable IDs / edges：

- `node:10100011:node_0b5e8e45b8fb` → `edge:node:10100011:node_0b5e8e45b8fb:1010001110332:332`。其 FINISH 目标 scenario 0 经正常 root 选择进入目标 2。
- `node:10100019:node_df0fabc0da7a` → `edge:node:10100019:node_df0fabc0da7a:1010001910181:181`。其 FINISH 明确目标 scenario 2。

以上 motion 是**当前还原 JSON 中的实际字段**。本包没有找到这些场景遗失的日文原始 payload，manifest 将这些来源标为 `reconstructed`；不能把这些当前 token 签作已取回的原版 token。

所有三种入线经过正常 projection/resolve 后：

| 当前节点 | 类型 / stable ID 后缀 | model / body / 背景 | 未选入线的 ambiguous |
| --- | --- | --- | --- |
| 2 | TITLE / `node_869ba28d7d51` | 表中上游历史值；当前不显示 Live2D | 当前 `[bg_picture, body]`；候选 `[bg_picture]` |
| 3 | TEXT / `node_fae8df1a8710` | `""` / `""` / `bg/bg008a_fruitshop` | `[]` |
| 4 | CARD / `node_d2a9a06c162a` | `subaru01` / `act_tameiki` / `bg/bg008a_fruitshop` | `[]` |

node3 同时明确开始 `bgm_adv_every02_cd2_07`。TITLE 的 StopBGM 和 node3 新 BGM 均保留。当前三条路线没有实际 ambient 冲突；本包没有伪造 ambient/BGM/effects 冲突来冒充真实场景验证。

## 当前源码为什么给出过宽提示

`lib/studio-state.ts` 的 TITLE 分支（约 74 行）执行音乐、三段指令和背景，不清除保存的上游 model/body/face/extras 等。最后约 147 行直接把 `display` 中除 music_source 外的所有 null 作为 blocking ambiguous，未判断当前节点是否呈现该字段。`public/studio/media.js` 155–157 行据其 labels 生成提示；正常 `player/prepare` 也据同一 ambiguous 拒绝播放。

保留历史状态本身有用途，不能为了隐藏提示而把 `body:null` 写成空串。本次修正只针对 mandatory diagnostic projection。

当前两个 Player 的 `title()` 均 `scene.clear(); display('empty')`。`display` 隐藏 solo actor 和 cast，且只 `clearCommand()`；它没有重建 Animator，也不能被描述成已经实施原生 GameObject disable/reset。TITLE 之后使用 bg_picture/clut、标题和指令/音乐；`NativeActorLighting.apply` 只读取 `{bg_picture,clut}`，不读取旧 body。

也核对了 `enter()`：它在分派 `title()` 前**可能**为节点自身 authored model/actors 准备动作。所以候选 v2 限定为 `kind==="title" && !target.model && !target.actors.length`，不放行未核的“标题自身带人物”路径。当前目标满足这项条件，因此不会在标题准备阶段消费旧 body/extras。

## 最小候选 v2：只过滤当前空人物 TITLE 的人物诊断

审查文件：`title-inactive-actor-ambiguity.candidate-v2.patch`，SHA-256 `da2d4f9ef8e6e6a0f255fd670f44f1074a6f2db1b6b19fe592fc81c9231c6e20`。

只修改 `resolveStudioState` 最后收集 ambiguous 的逻辑。满足上述空人物 TITLE 条件时，不把 `model/body/face/face_reset/extras/actors` 及 extras 子层的未知值列为当前阻塞字段。所有 before/entry/display/after、上游 choices、源 JSON 和命令均原样保留。BG/clut、BGM、ambient（包括子 cue）、wipe、junction 和真实 effects 的处理不变；不全清 ambiguous。

原先宽泛 TITLE 候选保留为 `*.candidate.patch` 和非 v2 结果，只作探索历史，已被 v2 收窄替代，不应申请应用。v2 patch 已通过 `git apply --check`（仅检查，未 apply）。未新建 unit 测试，也没有修改正式代码以暴露日志。

对当前未选 TITLE，提示从：

> 这里的背景、身体动作会随来路变化，请选择预览入线后再播放。

变为根据同一 UI 模板得出的：

> 这里的背景会随来路变化，请选择预览入线后再播放。

其 prepare **仍为 422**。这是真实背景需要选择，不是绕过入线规则。已选两条正常来路仍各为 200。

## 真实 `/api/player/prepare` 的有界离线 proof

`normal_api_candidate_probe.mjs` 在内存编译并执行 canonical 的真实 `app/api/[...path]/route.ts` POST handler、`studioPost`、`loadStudioSnapshot`、`studioProject`、`resolveStudioState`，未传 override。使用 Workers 的 section scope，实际读取 `[10100010,10100018,10100011,10100019,10100012]`，没有合成 program 或替换业务逻辑。

离线替代仅限 I/O：`GitHubRepository.readBatch` 暂时委托该类原有、会校验 revision/path 的 `read()`；fetch 只接受固定 db238432 的 public raw GET 并返回与 guard SHA 一致的本地原字节，其他 URL/方法立即拒绝。这样保留正常 scope/路由/序列化/status/prepare 的真实逻辑；GitHub auth/GraphQL、Cloudflare runtime 和真实网络没有执行。Next request/session 函数不属于这条只读路径，未调用。两种 bundle 均只在内存，最后恢复 I/O bridge。

baseline 与候选 v2 各执行三种入线 × 节点 2/3/4，每组分别执行 resolve 和 prepare，共 36 次实际 handler 调用。结果在 `normal-api-candidate-results-v2.json`：

- baseline 的九次 resolve 与此前未修改 canonical 纯函数结果逐项深等。
- 九组的 before/entry/display/after 全部逐项深等；music/phases/unsupported/warnings/incoming 也逐项深等。
- 唯一结果变化：未选 TITLE 的 ambiguous 从 `[bg_picture,body]` 到 `[bg_picture]`（以及对应 label/error 文案）。其 prepare 保持 422。
- 其余八组完整 resolve 一致；八个成功 prepare 的完整规范 JSON payload SHA 也一致。
- **现有正常 node3 的未选 prepare 本来就返回 200，且返回真实 `before.body=null`、`before.bg_picture=null`。** `studioPost` 使用的是 `before:resolved.before`，不是 display，也没有把未知值改写为空。

因此未知旧 body 可以保留在 `resolved.before`：Player.start 先克隆 before，但不在 start 消费 body；当前 node3 没有 authored model/actors，跳过 motionSelection，显式水果店背景先覆盖旧 bg，最后空人物分支将逻辑 model/body/face/extras 清空并隐藏前景。node4 此后通过显式 Subaru01 + `act_tameiki` 选择动作。这个顺序由实际源码支持，且正常 API 的 node3 返回已证明不依赖伪造入口。它仍是服务端/源码层面的证明，不能冒充一次已执行的 GPU 或动画时钟验证。

这也说明不能把所有“body 会随上游变化”一概判假：同人物持续可见、后续省略动作时，当前 parser 和 player 确会保留上游 body；本次 TITLE 恰好不消费它，并在紧邻后续明确重置。没有把这个局部结论推广到所有节点。

## 原生规则与本次范围

复用的 native ELF/metadata 绑定和完整反汇编在 `episode8-native-reentry-investigation-20261121-v1`，本包 `native-subaru01-binding.json` 对引用逐文件 SHA 绑定。原始 ELF SHA `54c97bce616bdb062f12b0bccba47b1c6ff17f61da450d8bd0efa403f8822c05`，metadata SHA `2cde31e37d9c6c58f3a1bb7bae6b12e51d456af7de03d604bc953116887b1b3e`，不是当前 JavaScript 的函数名猜测。

- 原生 `InitScenario 0x124d7b0` 在 `0x124d878` 检查 TITLE，`0x124d87c` 分支仅跳过 SetupSE，仍在 `0x124d950` 调用 `UIController.SetLive2DChara 0x16891e0`。
- 空 character 经 `HasLive2DChara 0x17179f4` → `View.ShowLive2D 0x1689268` 的空分支 → `HideAllLive2D 0x1deefa0` → `HideLive2D 0x1deefdc`，后者 `0x1def2cc` 实际对槽下 GameObject 子树执行 `SetActive(false)`。Hide 不是 Destroy。
- 同模型缓存复用由 `Util.Play 0x128a0d0` 的 Transform.Find、`SetActive(true)`（`0x128a3ec` / `0x128a484`）再 `PlayMotion`（`0x128a5ac`）构成；对象复用不能等同 controller 状态保持。
- **非空 character 的连续动画**与**空 character 隐藏**必须分开：`PlayMotion 0x1dea508` 的空 motion 分支从 `0x1dea564` 到 `0x1dea940`，跳过 GetAnimator/ClearLayerWeight；它本身不要求选 `face_normal` 或新 body。但是前面若发生 GameObject disable，则另受 Animator keep-state 配置约束。

本包新读 **Subaru01 原始 prefab**，而不是用睡衣 prefab 推广：`ac_subaru01.prefab` SHA `adc6f77fbbe1054d5668c7057974137919fa8f2799e5f4d42a99039c6b25aec3`；Animator PathID `-8909435836621351426`、GO `4124011135497300187`、Controller `7883747241018871188`、`AC_subaru01_ver2`。其 `m_KeepAnimatorControllerStateOnDisable=false`；新读 raw controller 与保留原件逐项相等，原 controller 文件 SHA `b6c3bbdef5f525be008bfff0de18a9b29b43402ad50473a6253a4729c62acffd`。另一个已核 gown 仍只具有自身资源范围。

同版本官方契约：<https://docs.unity3d.com/2019.4/Documentation/ScriptReference/Animator-keepAnimatorControllerStateOnDisable.html>。此前 HTTP 200、访问 `2026-11-21T05:26:22.913032+00:00`、保存 HTML SHA `c10fff7071a5a83c793b2b99964d9c900bcf0c89e653b03a8c7e08632b3791cc`，本次重新核对原件 hash。false 证明关联 GameObject disabled 时清除 **AnimatorController 当前状态**；不证明所有 parameter 值、模型 geometry、原始动作 token、具体帧点或全部角色配置。本次未使用新版更名属性代替 2019.4 页面，没有新增官方直接引文。

因此原生证据支持“空人物边界不是同一可见人物的空 motion 延续”；它不恢复遗失的 scene10100012/episode8 node10 原始 motion，也不能把当前 JavaScript clearCommand 冒充原生重置。episode8 的 source53 资源绑定及既有独立 logplan 原样保留，本包不申请 renderer 生命周期改动，不追加 face_normal，不签原版精确 body。

## rootfalse 交接

请求独立 peer 审查候选 v2 的过滤范围、真实 API I/O bridge、before/null 到 node3 reset 的路径，以及背景/BGM/ambient/effects 的保留。当前只交付可审查 artifact；没有 formal/source apply、浏览器、服务、安装、发布授权。根线程可在独立审通过后决定后续执行，不能据本包提前宣称正式修好。
