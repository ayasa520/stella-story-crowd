# K3 六候选完整过程审核公开候选

`rootConfirmed:false`。六组完整过程均未通过；body、face、正式 motion、整场接受均为 false，无 token winner。本包待主代理独立核验后发布，仅归档 K3，不等待或替代 K4。

已核对原审核记录覆盖实际 **3,201 张原幅 JPEG / 163 张 contact**（500×1000）；本次只读文本并重算输入文本哈希，未新增识图或解码。

| 候选 | 私有 motion | 实际帧 / contact | Normal hitches | 完整过程 |
| --- | --- | ---: | ---: | --- |
| 45-A-body-only | `act_ikaru` | 514 / 26 | 4 | 不通过 |
| 45-B-body-plus-face | `act_ikaru,face_ikaru` | 514 / 26 | 4 | 不通过 |
| 54-A-face-shinken | `act_normal,face_shinken` | 453 / 23 | 3 | 不通过 |
| 54-B-face-shinken02 | `act_normal,face_shinken02` | 453 / 23 | 2 | 不通过 |
| 46-A-face-only | `,face_odoroku2` | 664 / 34 | 3 | 不通过 |
| 46-B-body-only | `act_odoroku2` | 603 / 31 | 3 | 不通过 |

45 两组只有张臂、抬头/上身和紧张保持的有限同族相似，均未证明原片691.388已实显的完整闭眼入场。54 两组在停顿文字展开时开口，原片持续闭嘴；B保持时的眼眉也更圆、更扬。46 两组均只见细眼缝后睁大，未重现原片703.188实闭眼；实际收眼时46文字已出现，原片先反应后出新框。46A的468→469及46B的407→408也没有展示同样分步退场。每项均指捕获画面中的差异，不推定渲染器或资产原因。

原片口径分列：45窗口689.822–701.988含366 unique PTS、366实体JPEG、366 contact显示槽/19张；54/46窗口696.822–708.988含366 unique PTS、371实体JPEG、407显示槽/15张。两窗合并576 unique PTS，curated绑定578实体，完整contact涉及583实体；重复PTS/实体/显示槽不是同一单位，不能把多次审核累加。本授权source仅到门动画前段。

保留旧706.822/706.855首次退场分歧。后续46B原幅细分为706.822角色暗化且框在，706.855角色已离场但框在，706.888仍有极淡框残留，706.988黑；旧报告和哈希不改。早期54把703.155–703.188统称窄缝，后续46原幅进一步区分703.188实闭眼，亦并列留档。

v1直接MJPEG导出在重复原PTS处失败，前四组1934帧完整、46A partial36及失败日志原样保留且未当成完整审核。后来rawRGB传输加原PTS sidecar得到46A664/46B603共1267帧并strict EOF，16/13对重复PTS均保留。它补齐离线导出，不是修复播放器，也不接受body/face/motion。

native phase及body/face/mouth provider未知。Normal hitches、约30Hz X表面非唯一GL帧、46B灰/块帧和裁切/HUD限制保留；tap/weight/alpha为合成后、Core及GL前观测，不是paint或原生generation。未签geometry、tint、timing、audio、allglyph或全场/全话。

精确审计哈希和项目相对指针见 [public-index.rootfalse.json](public-index.rootfalse.json)，全部输入字节/SHA见 [input-receipt.rootfalse.json](input-receipt.rootfalse.json)。未复制私有绝对路径、原图、视频或完整runtime dump；未改旧报告、D/C，无Git/API/browser/新decode或发布操作。
