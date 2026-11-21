# QAv3 CG7/8：原 JPEG 与查看显示分歧

**限定结论：CG8 原 JPEG 确含与 CG7 相同的非黑 CG 区域；不能据本次黑色查看显示认定 JPEG 缺 CG。** 原因 unknown，不签工具显示正常、clean paint 或原版 geometry。

仅直接逐张查看 10030005 的 6/7/8/9。6 为卧室浴衣昴，7 明确见粉彩 Ferris CG，8 的 `view_image` 响应在对白板之外呈黑色故事区，9 为卧室 Ferris 和选项。两位审者最初看到 8 黑显示的事实都保留，旧报告不改。

原 7 JPEG：78763 B，SHA `1af38348ff44d407bee70d03947e9b9ff331241070ad95044a9a3888331f7a93`。原 8 JPEG：76102 B，SHA `b7a8f01ab2de4d2803684a783dd67592c1a8d52a91046fa07f735177c5dfe1ff`。4 张原图均在只读统计前后 fresh SHA/bytes 精确等于 manifest。

Pillow 13.0.0 直接读取原 JPEG 的 RGB 像素，仅输出数值和哈希，没有新图、裁切、缩放或重编码。7 与 8 在以下区域逐像素 RGB 完全一致，差异像素均为 0：

| 原截图区域 `[x0,y0,x1,y1)` | 像素数 | 行序 RGB SHA256 |
| --- | ---: | --- |
| `[90,260,350,730)` 中央 CG、对白下方/控件上方 | 122200 | `2d721b6ee59844483c471babd38db22ec04f8a44eae617ed1bb4d1cee47958a7` |
| `[90,60,350,125)` 中央 CG、对白上方 | 16900 | `1028c9ffbfea1a7148ca378858ed5c1eb91a2a952c03531438bc7813f445d0dc` |
| `[0,260,440,730)` 整宽，含两侧黑边 | 206800 | `ba4d48001324e921b60703b2673b0760626713d4dfa4dc92524a1ed3072aa74c` |

前两区的所有像素均 `max(R,G,B)>16`，没有纯黑像素。原日志 7/8 的 imageRect 同为 `(0,58.8833,440,782.2167)`，contentRect 同为 `(89.8565,58.8833,260.2870,782.2167)`。前两区完全在 contentRect 内；整宽区在 imageRect 内，包含黑侧边。此元数据只用于区域对应，不以 DOM visible 代替像素证据，也不接受原版几何。

`observation.rootfalse.json` 保存 4 图绑定、完整统计、7/8 逐像素比较、capture before/after 和 image/contentRect 对应，以及直接查看黑显示与 RGB 非黑的分歧。`tool-bindings.rootfalse.json` 保存 Python、Pillow Python 源文件、JPEG 插件和 AArch64 `_imaging` C 核心的原字节 SHA/bytes、版本及 JPEG 库版本。仅新 metadata 目录有写入；无新采集/视频解码/浏览器/API/代码或 D/C 修改。
