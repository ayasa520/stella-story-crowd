# P29 10040052／第18节点：完整原片身份审核

结论：本节点可见演员支持 **`live2d/AC_subaru_tshirt01`，仅 character 一叶**。这是本子代理的有范围身份结论，rootConfirmed／installationAuthorized 仍为 false。独立复审由 root 另行协调；我没有读取其结论。没有改 D／C、运行 native helper、Git、API或新视频解码／probe。

完整原片270帧来自 root 已结束的单次采集：原PTS274.023–282.989、timebase1/16000，原录像 SHA `2301181cfd466b5126f1a37df45194b6b1fac71c15ffdd7ee90146f5109e6a90`。root 独立关闭收据 SHA `b84197aec6c4991ecebd896048e21376cd6f873d98826dfec1fa36793a5abb03`；全部 media／test browser 和采集CLI已退。本人只由已有JPEG生成23张完整顺序contacts，每帧恰好出现一次，图集8496550B，生成CLI9973c2 exit0后才识图。270原JPEG前后SHA均与原index一致，未改原图；没有取样或新FFmpeg。

我逐张看完全部23张图集，并另外直接打开19张原尺寸480×856的原帧：S001、020、021、024、025、026、027、029、030、096、131、142、143、144、145、148、149、153、270。并不声称270张都各自全尺寸打开。图集缩略图保留完整画面，关键原幅直接验证衣领、双肩和两袖。

|窗口内原帧|原PTS秒|观察|
|---|---|---|
|S001–S019|274.023–274.623|Prior Rom body visible and held; predecessor line.|
|S020–S020|274.656–274.656|Prior Rom body fading.|
|S021–S025|274.689–274.823|No stage body; outgoing panel remnant then bare blurred background. Native S24/S25 are clear boundaries.|
|S026–S029|274.856–274.956|Target black-haired dark-shirt actor enters: faint at S26, stronger S27-S29.|
|S030–S142|274.989–278.723|Target actor fully visible and held: rounded double-rim crew neck, fabric covers both shoulders and upper arms, distinct short sleeve hems, bare forearms. Same costume throughout typewriter/hold; full target line readable by native S131.|
|S143–S144|278.756–278.789|Same target actor fades out; sleeves remain present in the fading image.|
|S145–S148|278.823–278.923|Target absent; panel remnant then blank blurred background. Native S145/S148 bound the exit.|
|S149–S152|278.956–279.056|Rom becomes visible again and enters.|
|S153–S270|279.089–282.989|Successor Rom fully visible and held through the end, with successor line.|

这一完整过程中的黑发演员始终穿深色圆领短袖：双肩／上臂有布料覆盖，两个袖口明确，袖口下是裸露前臂，衣身没有外套领、N标志或橙白条。S030／096／131／142的原幅清楚保留这些结构；淡入淡出没有换装。依据是实际舞台身体，未用说话者名字来选模型。

原模型鉴别使用已绑定的原始MOC／PNG／prefab／controller与历史正式参照。本人直接看了原模型对照图（SHA `81b78b8b8faec5412b307ffb5e54349e2dd25597f9b830cd9e6e57754534354e`）：01有短袖、双肩覆盖；02裸肩无袖，不能作为等价alias。原纹理两张在前一步已直接看过，本轮重新核了其原文件及当前模型哈希；两套当前descriptor/MOC/texture均与各自原始资源一致。controller各9层／138 clip slots，并不靠同脸或相近控制器来决定模型。

历史正式P17／10020049节点16与P18／10250051节点18当前已保存相同的短袖身份；其 review.performance 分别指向 root-confirmed 的 accepted-p17-tshirt-v18（SHA `687134de8a2a2d5b946aa17905941e099ffe5db313c1275865348801b4620d06`）和accepted-p18-tshirt-v18（SHA `d5fe5ba2c08d9adf9878789bb5a79c41af74d6831b9e0506155079c97d199d70`）。历史原片P17参考也直接看过。它们只佐证资源映射，不能代替本次P29的270原帧；历史场景本身仍draft，不冒称整场验收。

候选 packet 为 `character-only.packet.rootfalse.json`，SHA `5da5a24b3b9152b93c53b8a1b07ea830a3035aeec66e1c0b84b54f55baaf3a40`。只含一个change：10040052／scenario18／arrayIndex17／UID1004005200018／stableKey s10040052-p29-at0276，`character: "" -> "live2d/AC_subaru_tshirt01"`。expected完整保留13项（含command、台词和其他演出字段）；另绑定完整当前native row、全38行身份顺序、原branch_list及SHA、native/review整文件SHA、源270帧index／关闭收据／原资源SHA。没有改动另外12个字段、分支、顺序、侧车或已接受的158字段；不把本节点结论自动用于其余pending行。

封包时只读工作树metadata观察 D=`71da3385c31ed81ad7af3e300ff9a4ecbafeea25`，C=`6630ac70f17332efa031d021af00532d42307568`；P29 native仍 `e19a64b116e098ef0445d54470ca635585ccc72acfc3e833e62e7aece48fc61d`，review仍 `b33e497ebc719eedbf1cd9f69d5f51dc465c4b4105b3bb97ed852b61dca61c22`。root后续前端审计推进HEAD属于正常进展；正式stage前应fresh重绑当前HEAD和原文件guard，不能因此重采这个已核原片窗口。

本结论不恢复原CSV中的literal，不签motion／body／face／原生CMD阶段／速度或时长／投影灯光／口型语音贡献，也不验证当前已保存后的正常播放、整场或整话。所列淡入／保持／退场是原录像可见事实，不是命令阶段或时序字段的授权。
