# 昴 tshirt01 / tshirt02 实际服装对照

六行都支持 `live2d/AC_subaru_tshirt01`：10450054 的 4、6，以及 10450056 的 14、19、21、28。对应草稿是 `six-character-only-draft.json`，仅提议填当前空白 character，逐行保留 stableKey、日文与录像区间，`rootConfirmed:false`。

关闭回执允许后，直接看了两套实际渲染的完整 ready 与 actor 图，以及六行各自的原片 full frame。实际 MODEL_READY 和模型请求把图片分别绑定到原生 tshirt01 / tshirt02，reference program 为 persisted:false。

可见区分足够明确：**tshirt01 是完整短袖，布料盖住上臂，袖口平整；tshirt02 的袖子在肩部成为卷皱/破袖状边缘，整段上臂露出。**六张原片都清楚显示两侧完整短袖；节点6虽改变头和手臂姿势，节点28虽改为蓝色背景，袖子区分仍独立可见。没有依据姓名、表情、台词内容或相邻节点填入。

每一张原图都与两套实际渲染直接比较，六个原 full frame 路径如下：

- 10450054:4：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/visual-low/p30-felt5-source-entry-review-v1/frames/frame-0001.png`
- 10450054:6：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/repair-20261111/visual-low/p30-felt5-source-entry-review-v1/frames/frame-0320.png`
- 10450056:14：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/ocr/30/root-review/frames/d7d29c63dc09-013650.jpg`
- 10450056:19：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/ocr/30/root-review/frames/d7d29c63dc09-014370.jpg`
- 10450056:21：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/ocr/30/root-review/frames/d7d29c63dc09-014640.jpg`
- 10450056:28：`/home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/ocr/30/root-review/frames/d7d29c63dc09-016380.jpg`

这是角色/服装审核。参考 `act_normal` 只用于呈现服装，不是已恢复的剧情动作；motion、face、extra、原 CSV、几何、时序、声音及整段正式播放都未由本次审核确认。未提取新图片、未启动浏览器、未改正式数据或 Git。
