# P30 已保存26角色身份／衣装：画面对照通过

**`characterIdentityAccepted:true`，`acceptedCount:26`，`actualDirectViewCount:26`。**
本次直接查看 `source-pairs-v1/pair-10450058-09.jpg` 至 `-34.jpg` 全部26组，逐项对照原片完整源图和正常保存数据截图，无遗漏；另直接打开保存原尺寸 `saved-10450058-21.jpg`、`saved-10450058-26.jpg`。26个不同actual画面均直接看过，图像工具共查看28张（26组对照＋2张原尺寸补看）。不是仅凭模型字段、文件存在或日志判定。

| 角色／衣装 | 节点10450058 | 数量 | 直接可见的匹配点 |
|---|---|---:|---|
|`AC_subaru_tshirt01`|10、12、14、17、19、20、23、24、26、29、32、33、34|13|棕色短刺发、昴脸型、深色圆领短袖上衣及裸露前臂一致，未混用运动外套|
|`AC_julius01`|11、13、15、16、18|5|紫发、脸型、白色骑士披肩、红内衬高领、黑色边线和金色扣件一致|
|`AC_emilia01`|9、21、22、25、27、28、30、31|8|银色长发／辫冠、白花紫带与蝶饰、白紫高领／绿吊坠、白紫胸衣一致|

13、15虽在谈运动服，原片普通人物仍穿骑士披肩，本次保存图也正确保留。21的原片和当前图都有选择界面遮挡，银发辫冠、花饰、颈部和可见白紫衣装足以确认艾米莉亚；原尺寸保存图已补看。选择头像不是character判据。

26使用新补的 **`choice-before/frame-0012.jpg`（约944.5秒，初始选项仍有普通短袖昴）**，并保留此前完整审过的 `frame-0005.jpg`（约941秒正文）证据。当前保存图清楚显示深色短袖普通昴，原尺寸也已打开确认。954.998秒空背景属于后来的选中答句阶段，未拿它或选择头像来补判正文人物。

识图前已读取 `closure.json`：browser/CLI/录制FFmpeg/adapter均退出，matches为空。`characters-result.json` 是 `saved26_characters_completed_at34_ja`、27visits、单个正常program、26张图片、无错误、cleanupPassedtrue；21选212、26选263，最后34ready／ja。此运行绑定Root报告的applied batch `1e448bcfb562f3da6ef6`；源图决策各自的早期不可变提交只提供来源，不冒称它们已包含本次新保存字段。

配对脚本以nice19／CPU0、1在关闭后运行，只对已有源图和已保存JPEG作完整画幅缩放拼接，未裁切人物、未改原图，未重提取源片、未解码视频或运行浏览器。逐项源图路径、时间、stableKey／日文、保存图、参考绑定和具体判定保留在 `formal-character-image-review.json` 的 `rows[]`。

**仅身份和衣装通过。** 原片有抬手、不同头部姿态、闭眼笑、眉眼和嘴形变化；当前静态保存图与这些演出有可见差异，本次不将其写为表演一致。`actingAccepted`、`faceAccepted`、`extrasAccepted`、`geometryAccepted`、`timingAccepted`、`wholeEpisodeAccepted` 全为false，音频／原始命令相位也未接受。完整门→CLEAR→完成图录像由另一审核者独立负责，本报告不提前签结尾视频。无正式源／数据／Git修改。
