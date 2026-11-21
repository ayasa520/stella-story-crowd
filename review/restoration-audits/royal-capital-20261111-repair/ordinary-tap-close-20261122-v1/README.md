# Ordinary tap Close：已部署实现与正常两路线 QA 审计

此包记录 canonical `6630ac70f17332efa031d021af00532d42307568` 的普通 tap Close 修复、Qv3 两条正常路线和现有 Cloudflare Worker `stella-preview` 的部署／回读。部署版本为 `dbb81ee9-7ce9-4c27-9739-e5350075c5da`。这里只归档既有证据，不重新执行或改写历史收据。

Qv3 是 source6630／data `d8fbcb0d3e123ec7cf0df66908d8b526c51c78e5` 的正常本地 Worker／浏览器 QA，两个case退出0，共16个节点／16张原JPEG（1422107B）。部署后 production默认data为 `71da3385c31ed81ad7af3e300ff9a4ecbafeea25`；既有HTTP回读核对工作台200、两个player模块与canonical原字节、完整native／普通prepare及talk0投影。它没有做新的production连续播放。root预部署记录说明两次data间只有不相干10090015的talk0叶和审计变化，section1003未变；不能把本地QA称为部署后整条实播。

- ending路线：10030002的38→39→41自然movie→42标题／complete。381是普通tap触发Close的正例；41自然ended、真实ready后可信411，42按当前程序自动421，没有手动跳标题。
- IF/CG路线：10030002的16可信163→40→10030005的1自动11→2→3→4→5→6→7→8→9可信93→10ready。71是另一Close正例。未知92未点，最终101未执行。
- 两个Close正例均记录outgoing事件在follow／next-enter前发出；没有把out动画完成当作follow等待条件。当前正常功能回归不等于原作自动性／原命令阶段／精确时序恢复。

`qa-v3/terminal-acceptance.json`、process和独立root closure为原始回执；`selected-events.json`是明确标注的静态摘录，完整保留选中原record的rawEntry／sequence／时间戳和原JSON数组指针，并绑定完整result及case-result SHA。它不是完整raw trace。大`result.json`保留原件SHA，列为可选发布；不要用摘录覆盖原文件。16个JPEG只逐字节复制，没有解码／裁切／缩放／重编码。manifest给出全部from/to、bytes、SHA。

阅读图审请先看 `image-review/ERRATUM-v2.md` 和 `erratum-v2.rootfalse.json`。原十六图审最初将CG8查看显示为黑色推断为JPEG缺CG；原review／contrast／README保持原字节，**这项JPEG内容推断已被勘误撤回**。独立已有解码统计显示CG8所查中央122200、上方16900和整宽下区206800像素与CG7完全一致，前两区非黑。两个查看器黑色呈现观察和正向DOM/layout原记录仍并列保留，原因unknown。不能据此宣称查看器正常、浏览器paint故障已定位、clean paint或完整16图视觉签字。其余15张静态可见身份／BG／选择／标题等原结论保持；HUD遮挡和movie只一张中段图的限制保留。

原Qv2 attempt-1退出1，不改成通过：ending到42之后，四个scene-thumbnail500来自private guard缺少四个既有PNG key；第二IF/CG case未启动，71和自动11未观察。原异常、HTTP和关闭收据在 `prior-qv2-failure/`；旧release耗尽。Qv3是另一次完整证据，不能擦除旧失败。13个Normal hitch、历史unattached GL loss与零attached actor loss分别保留，不声称零overhead或精确时序。

root独立核Qv3 supervisor／server／browser／driver和组退出、ports拒连、profile移除及原guards／16JPEG精确后才准图审；本包是那些既有收据的副本，不是新OS/API检查。部署日志／predeploy／final receipt和production原HTTP gzip载荷在各自目录；不新建Worker／远程，不改数据库／secrets。

补充旧talk0审计见 `prior-talk0/` 的最终71 main ACK和final publication receipt，以及相邻既有[第5话silent54审计](../episode5-silent54-20261121-v1/README.md)。此补充仅证明已保存／发布／投影的窄字段，不重新安装、不接受原CSV值／body／face／phase／整场或saved continuous playback。

本包不签原作整体验收、动作／表情、精确嘴形／geometry、命令阶段、时序／音频／全字形、整场／整话。部署与普通功能证据、原JPEG、查看器呈现、有限解码像素统计和原作演出验收是不同证据范围。
