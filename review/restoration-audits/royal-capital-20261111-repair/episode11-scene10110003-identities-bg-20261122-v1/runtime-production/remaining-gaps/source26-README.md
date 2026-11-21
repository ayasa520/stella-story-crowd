scene10110003/node26 的完整原片过程审核已完成：授权窗口405.0–416.0秒，唯一一次提取330原帧（13,773,066 bytes），真实PTS405.023–415.990、time_base1/16000。原P38 SHA前后同为 `738ac54778796cd4e51dcb35a23d15ef20c05ed90a5083c29eb2d4cf7f61e9b6`；逐帧PTS/showinfo与SHA见 `source-frame-manifest.json`。没有fps滤镜、补帧、setpts或猜测时间。FFmpeg decoder/filter/encoder各1线程，nice19/CPU0,1；supervisor27822、decoder/PGID27824均已退出，相关组和CLI为空，关闭记录先于识图。

全部330帧通过8页连续审核图逐帧查看，并重开12张完整原帧确认眼口细节。完整覆盖：25末句保持/退场 → 26淡入、表情变化、保持及退出 → 27夜街入场/地点框。窗口尾部只露出28入场开头，不签28完整过程。

| 原片观测 | 实际PTS范围及边界 |
|---|---|
| 25 Felt保持后退场 | 405.023–406.523；406.3附近开始退场，接模糊店内背景。|
| 26入场/眼睑变化 | 406.556起隐约入场，406.59已见Subaru；406.723–407.023附近收至细缝/近闭，头颈肩轻微俯斜，随后睁回窄眼。|
| 26脸部持续差异 | 407.123后形成窄眼、皱眉、横向张口/露齿形状，407.256–409.256反复可见。此前actual26单图为更开眼、闭口的中性脸；本任务没有新actual过程或时钟对齐，不能由一张旧actual推断其全程。嘴形驱动来源仍未知。|
| 店内擦黑 | 409.290起从画面右向左擦除，至409.99主舞台黑；旧对白框/烧录字幕和顶部、底部UI仍在。对白框约410.1后退去，UI保留。|
| 黑舞台/夜街显现 | 黑舞台保持到412.690，412.723起从左向右显现夜街；约413.4后地点框入场，27无actor。|

身体证据不足：只看到轻微头肩变化、双袖近垂直，未见充分的抬手或叉腰过程，手/下臂可见范围受限；**bodyAccepted=false，不选body token**。已有原/LIMEOS导出曲线和controller绑定仅提供 `face_punpun`、`face_kurushimu` 候选及 `face_ikaru` 辨别对照，各entry/hold曲线SHA、参数段和binding见 `controller-curve-candidates.rootfalse.json`。名称、单个参数值和单张脸都不构成token接受；face/body均未正式签。

`source-process-review.json` 与 `review-receipt.json` 保存完整过程、原PTS、擦除方向和UI边界。观察到的黑舞台约2.7秒不能写成猜测Wait、CardOut或命令阶段。`future-private-face-only-gate.rootfalse.json` 只记录尚缺的fresh normal program/resources冻结、独立peer及完整actual face-only控制门；全部rootfalse，未执行私有对照。

只写本新私有目录，未改D/C、旧证据、正式motion/source脚本。没有OCR、安装依赖、browser/API/server/Git；没有第二次解码，也不签实播或整话完成。
