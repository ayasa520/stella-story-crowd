# P21 every07：单字段普通保存候选

本包只作离线准备。全部 root/执行/安装批准位 false，最终 HEAD 为 null；资源登记完成并由 root fresh 绑定新 HEAD、完整文件守卫后，才可走原 native_repair → native_install audit → apply。本轮没有执行业务 helper、API、播放、FFmpeg、测试或正式写入。

结论：现有原测量和既有源卡审核足以支持 **10030001/3（UID1003000100003、array index2、stableKey `s10030001-p21-at0023`）仅 `bg_music: "" → "bgm_adv_every07_cd2_13"`** 的资源身份候选。不是从“商业街”地点名称或资源名推导时间；也没有恢复原 CSV 或命令相位。

本次实际读取原 `p21-opening-measurements.json`、`p21-location-measurements.json` 和 `p21-opening-entry-refinement.json` 的全部测量 JSON。每窗完整 query PCM 的既存 SHA、来源视频 SHA、65首名单/全部64个其他曲目 signed scores、精确参考样本位置和 JSON pointers 见 `measurement-review.rootfalse.json`；没有读取或重算 PCM、NPZ、WAV/Opus 或视频字节。

|既存源窗|every07 signed correlation|最强其他曲目 control|
|---|---:|---|
|23–26秒，完整65首|0.7314580997542443|heartwarm03：+0.25289731000829374|
|32–35秒，完整65首|0.9394449314712879|heartwarm04：−0.34117605472333573|

23秒 query PCM SHA `74103dab…` 在 opening/location 两份记录完全一致。3秒窗跨过节点3的25秒尾界，所以另外检查了 refinement 的23、23.5、24秒三个一秒窗；它们全部落在当前 review 已记录的23–25秒卡内，signed scores 为0.777301、0.836464、0.848306，参考样本363→1363→2363按2kHz、每0.5秒1000样本推进。22/22.5秒的一秒结果仅−0.069332/−0.101175，不能据此把音乐倒填到较早旁白。空或低相关也不冒称整段静音。

当前 review 原文 `王都の商業街・昼`、recordingId `bili-capital-21`、源 SHA `b3893cab…`、23–25秒区间与旧身份审核精确相符；沿用旧已审核源帧 metadata（12秒标题、14/18秒旁白、23秒该卡），本轮未看图。32秒最佳参考位置282.298秒是独立身份 control，不等于23秒参考位置加9秒；不据此写 offset、循环或重启参数。22.5–23只保留为已观察卡入场括区，不接受 sample-exact 原命令开始点。

`node-fields.rootfalse.json` 使用已成功三BGM包的原 schema：只有一个 fields 键，完整13个 expected；`target-guards.rootfalse.json` 另绑完整当前行、20行全数组/UID/branch顺序、whole native/review byte SHA 和 ownership summary。当前 pair SHA仍分别是旧身份包声明的 `cd22c03c…`／`25a35896…`。不改原 branch31→4、voice/SE、motion、背景、文本、gain vector、任何其他行或场景；不补 `,1,false`、fade/reset/volume/gain/loop/offset/STOP 或 phase。`audioListened:false`，不升 whole-scene/continuous-playback 验收。

资源条件尚未满足：本轮当前正式 full catalog/package 仍未登记 every07。只引用 `p21-every07-current-root-preparation-rootfalse-v2` 的两 metadata 候选及原 SHA；不会把它们当作已安装。Root须先独立批准、正常落盘/发布登记，再绑定真实新 HEAD、catalog/package/payload守卫和正式登记/ACK记录；payload SHA仅继承资源负责人测量，本轮不重新读取音频或metadata payload。其后 fresh 核其他139 pairs、protected22及完整当前全局集合；本包没有提前生成大库存或声称这些已通过。

原 CLI 参数形状保存在 `root-request.template.rootfalse.json`。Root在新文件克隆批准 packet，校验所有 guards，才把变更的 rootConfirmed 设 true；原 node_fields 只强制 stableKey 与已声明 expected，不强制此处的 final HEAD、UID、array index、完整 pair/资源 guards，外部门必须由 root保留。stage 目录必须全新且在 D 外；没有 `--baseSha` 或 `--dry-run` 参数。

```sh
nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python -B -m story_studio.recovery.native_repair \
  --root /home/rikka/Projects/stella \
  --target /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/data-checkout \
  --directory /home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/native-directory.json \
  --node-fields /ABS/NEW-ROOT-APPROVED-P21-PACKET.json --output /ABS/NEW-ABSENT-STAGE
```

随后原 `story_studio.recovery.native_install --root ROOT --target D --staging SAME-STAGE` 先 audit（无 `--apply`）。Root检查 scenes1/counts.bg_music1、仅 native `/scenario_list/2/bg_music` 一叶、其余19行及全20行分支深等、必要 sidecar evidence/unknown warning刷新、该场必要 manifest summary、ownership和新 batch 后，才独立批准同命令加 `--apply`。保留 sidecar既有内容，允许原流程追加本字段证据；manifest可能字节完全不变，不强制 Git 修改文件数。任何错误保留原输出后停止，不自动重试、换 parser、换字段入口或重跑既有三BGM保存。
