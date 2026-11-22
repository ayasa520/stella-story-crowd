P21 every07 当前资源登记候选（rootfalse v2）

已形成可直接审阅的两份完整候选 metadata，均仅写在此 A 目录的 assets/ 下。D HEAD 前后实际观察相同：24ea1d188d1d22ee50b37776cd2a1faf9576f219。observedHEAD 只是本次观察，finalHEAD 和模板 expectedBaseHead 仍为 null；所有执行／root flags 仍 false，原 helper 未运行。

| 文件 | 当前 bytes／SHA256 | 候选 bytes／SHA256 |
| --- | --- | --- |
| assets/catalog.json | 4606032／8bc553f5d67a0740466e0e75c23bfa5cda9504e1b95c40fa504482f9c86d9e7c | 4606201／009fb8072b8cf56f6c95ade4587f4132cabd2eae9e7ee74af130c4582087ff87 |
| assets/package.json | 1972679／55f78e9a5035544e6bfc9b2ed63cb3bb0c619be482e90ade4c84f5b277f67e1b | 1972951／47ca071baf350f30aff163b743e6c315e426e338537b7b09f8d8cd34c5cb5fde |

差异只有：full catalog 增加 music.bgm_adv_every07_cd2_13，精确复用 compact row；package 增加既有 Opus 与 metadata 的两个索引记录，更新 files["catalog.json"] 的摘要，并把总字节从537535025改为538769567。精确旧值、新值和JSON pointers见 semantic-diff.rootfalse.json。两份原件均能由选定 compact UTF-8/newline serializer逐字节重现，候选沿用同一格式；全部旧 catalog/package 键值在声明差异之外保持相同，没有重排文件索引或修改其他资源。

两份现存 payload 本次均只读取原文件字节计算完整 SHA，无解码、播放或重编码：

- preview/music/bgm_adv_every07_cd2_13.opus：1234086 B，a18e0d54d0ecc2fb7539252b846fbed3d896f87b1c01249d6be3458cd48e2617。
- preview/music/bgm_adv_every07_cd2_13.json：287 B，c7fbf10e16be73440337bdec9cd19b77c17618872473fc504914ee9f0a8b4f41。

两摘要与原 v1 及其旧 seal一致，现存 payload 不复制、不改动。原 v1 的5个文件全部核对且保持原字节。当前 manifest.assets 仍不存在；catalog 的实际摘要记录在 assets/package.json.files["catalog.json"]。本候选不改 manifest、preview catalog、members/asset_members maps、ownership 或任何场景。

integration-plan.template.rootfalse.json 已填两份候选的实际 source/bytes/SHA、六份 metadata locks 和两份 reusedPayloadLocks；唯独最终 HEAD／root 批准仍留给 root。既有 A/apply-asset-plan.py 的接口仍是两个位置参数（reviewed plan、new receipt），会在真实 HEAD／摘要／additive gates后直接写入，没有 dry-run开关。本次只读其原源码与接口，没有 import 或执行，也没有新增执行脚本。

根目标后续仍需正常 BGM 字段 source 审核和保存。10030001/3、UID1003000100003、stableKey s10030001-p21-at0023 当前 bg_music仍为空；本包没有生成 node_fields/import请求，也没有把旧资源身份接受提升成字段安装授权。原 location-card／PCM identity scope、rootfalse、audioListened=false，以及原 CSV/fade/reset/gain/loop/offset/STOP/phase／演出与整场未接受的限制均保留。

19个既有输入前后字节／SHA相同，候选 metadata已独立读回匹配。无D/C/Git写入、helper／测试／构建／FFmpeg／ffprobe／编码／浏览器／媒体播放，其他旧包和未提交工作未动。
