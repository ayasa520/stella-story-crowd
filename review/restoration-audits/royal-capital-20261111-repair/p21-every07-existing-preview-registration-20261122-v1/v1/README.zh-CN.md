every07 既有 preview 的最小登记准备，rootfalse；finalHEAD / expectedBaseHead 均为 null。只写此小 metadata 目录，没有 materialize 两份完整候选 catalog/package，也未修改当前 QA 的 13-path freeze。

当前实际仍缺 full catalog 的 `music.bgm_adv_every07_cd2_13` 和 full package 的两个 preview 文件记录。compact entry 与原 WAV member alias 已存在；Opus 文件本次仅 stat 为 1,234,086 B，未打开或重算 SHA。完整摘要来自旧 preflight 的有效 seal：

- `preview/music/bgm_adv_every07_cd2_13.opus`：`a18e0d54d0ecc2fb7539252b846fbed3d896f87b1c01249d6be3458cd48e2617`。
- `preview/music/bgm_adv_every07_cd2_13.json`：287 B，`c7fbf10e16be73440337bdec9cd19b77c17618872473fc504914ee9f0a8b4f41`；该 metadata JSON 本次重新核对相同。

只需两份正式 metadata 文件：

1. `assets/catalog.json` 增加 compact entry 的精确值：label=bgm_adv_every07_cd2_13、url=preview/music/bgm_adv_every07_cd2_13.opus、metadata_url=preview/music/bgm_adv_every07_cd2_13.json。
2. `assets/package.json` 增加上述两份已有文件的 bytes/SHA 记录；同时把 `files["catalog.json"]` 更新为新 catalog 的实际 bytes/SHA，并重算 package.bytes。

当前 catalog 的 package record 完整旧值是 bytes4,606,032／SHA8bc553f5d67a0740466e0e75c23bfa5cda9504e1b95c40fa504482f9c86d9e7c。package.bytes537,535,025 与现有全部 member bytes 之和一致。新增 preview records 共1,234,373 B，所以新总数应为 `537535025 + 1234373 + (newCatalogBytes - 4606032)`。新 catalog 尚未序列化，不编造新摘要或字节数。其余 catalog/package 旧键值必须保持精确相同。

当前 `manifest.json` **没有 assets 字段**。这里实际的 catalog 摘要机制是 `assets/package.json.files["catalog.json"]`，来源见 `crowd_assets.py:69–78,96–103,425–429`。canonical `lib/resources.ts:26–38` 按 immutable revision 读取 catalog；成功的 bg070b metadata 登记也保留 manifest 和 ownership。因此本资源登记不新增 manifest.assets、不修改 manifest、preview catalog 或 story 数据。后续正常场景保存涉及的 manifest summary 属于 root 另一个正常事务。

沿用已成功的 `A/apply-asset-plan.py`，不是新实现。它的参数为两个位置参数：reviewed plan JSON、全新 receipt JSON；没有 dry-run 开关，调用会实际写文件。`integration-plan.template.rootfalse.json` 的 HEAD/source/新文件 bytes/SHA 仍空，当前不能调用。root 结束 P30v2 QA 后，应重新绑定真实 HEAD 和六份 metadata locks，materialize 两份候选 metadata，填完 plan；由原 integrator 检查 reused payload 的真实 SHA、旧目标摘要、additive catalog 保留关系及写后 readback。CLI argv 模板与完整 old-entry guards 在 proposal 中。该脚本本身不 commit/push，仍由 root 完成正式发布。

本次检查的 `/api/assets`、`/api/music/[id]`、`/music/[id]` 均为读取入口，没有发送请求或当成写 API。正常 native installer 使用 full catalog 验证 music key 与 metadata_url，因此 compact 已可见不能替代这次 full 登记；现有 logical music resolver 直接使用 url/metadata_url，最小方案无需另加 full archive-member alias，也不复制或重新编码 payload。

后续场景仅作上下文记录：10030001/3、UID1003000100003、stableKey s10030001-p21-at0023，目前原始 bg_music 仍为 ""；本包不生成或安装字段变化。原 P21 source PCM／location-card 资源身份接受保留，原包 rootfalse、audioListened=false、CSV/fade/reset/phase/gain/loop/offset/STOP 与整场接受限制不变。资源 metadata 的 loop=true 不等于原节点 CSV 参数已恢复。

未 import/执行业务 helper、校验器、API、媒体、测试或构建；没有读取 Opus 内容，没有新增 freeze path，没有修改 D/C 或旧 seal。root 将在当前 QA closure 后另行执行并核验。
