# Stella 剧情共修 · 前两话试点

本仓库保存主线前两话的原生剧情脚本、独立校对证据和浏览器预览资源，供原剧情恢复工作台在线校对并直接提交。

[打开在线工作台](https://stella-story-crowd-pilot.poisedwaxwing2.chatgpt.site) · [维护者连接 GitHub](https://stella-story-crowd-pilot.poisedwaxwing2.chatgpt.site/setup)

试点网站当前仅限维护者访问。完成 GitHub App 仓库授权后，贡献者使用 GitHub 登录，网页保存会直接向本仓库 main 分支提交 commit，作者为登录账户。可以在「原生脚本 / 导入初稿」中导入本地生成的原生 JSON，检查差异后提交。尚未点击保存的节点编辑会保留本机草稿。

- `native/scenes/<scene_id>.json`：游戏原生静态剧情内容，直接使用 `scenario_list`、`video_list`、`branch_work_list`、`chartmap`。不包含 Studio 节点外壳或玩家账户数据。
- `review/scenes/<scene_id>.json`：日文参考、录像时间、待恢复分支、转换差异和审核备注。
- `manifest.json`：五个场景的目录、来源与结构就绪状态。
- `assets/catalog.json`：按原生资源 ID 索引的预览素材。BGM 试听文件按原始音库采样范围制作，循环点保存在对应元数据中。
- `review/conversion-report.json`、`assets/package.json`：首次转换和资源包的来源摘要。

原稿场景 10010020、10010001 保留原始数组顺序、节点与分支标识及未建模字段。10010016、10140002、10140003 来自已有人工还原；尚缺的七个选择目标明确列为未恢复。原生格式草稿不等于已经恢复完整的场景，不应把空转移直接投入游戏。

校对请保持空字段的原生继承语义，不按录像时间重排 `scenario_list`。修改对白、素材或演出后，附上对应录像时间及理由。工作台在保存时合并不同字段的修改；同字段冲突会保留草稿供核对。提交记录和署名可在 GitHub 查看。

此仓库为恢复与校对试点。原游戏素材及已有录像、译文的来源归属不因本仓库而改变。录像通过 B 站原播放器查看，完整录像不在仓库中。
