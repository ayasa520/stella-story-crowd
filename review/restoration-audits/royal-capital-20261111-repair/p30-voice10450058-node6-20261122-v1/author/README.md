# P30 10450058/6：短 voice cue 普通保存候选

本包只准备一个 `native_repair.node_fields` 候选及当前输入守卫；不执行 stage/audit/apply。所有接受、安装和执行批准位 false，最终 HEAD 为 null。Root独立决定窄字段是否接受；原候选未试听/false flags 是证据状态，不是用户禁止继续准备。

唯一候选为 scene10450058/scenario6、UID1045005800006、array index5、stableKey `s10450058-p30-at0812p5`：`voice: "" → "vo_adv_julius,advk_julius_emilia"`。完整13个 expected 来自当前原行，包含 Julius 模型、原对白及空 motion/voice/SE；37行全数组、UID/branch顺序、目标旧行和当前 native/review/ownership summary 都绑定。当前 whole pair 仍为 `a8c59288…`／`b48ef7cf…`，与原packet/addendum相同。分支5/51→6/61→7及所有 quote_voice 保持；其余36行、此行其他叶、ID/order/背景/BGM/身体/脸/command/SE完全不改。

原测量 `voice58-6-measurements.json` 和 verifier 源码只读，没有执行。既存 native 链为 CueName index29→CueId29/sequence29/track29/synth29/waveform29→StreamAwbId38（AWB entry233120–239872），原32kHz/26230 samples，短cue约0.8196875秒。现有4kHz源PCM轴811–818秒内 active abs NCC0.991323、whole cue0.986398；三个不重叠片段在同一 cue-zero812.39275附近均为正，末片保留浮点尾差；三个指定 named competitors 中最大0.222486。这是有限三对照，不是全bank/全库排除。原 signed/absolute值、native字段与精确source pointers见 `source-evidence.rootfalse.json`，不把分数当正确率。

当前 review 的811.9–817秒区间、`bili-capital-30`、日文原文和旧source event203匹配该行；812.39275落在该区间内，仅支持该短cue的保守行内放置。约0.82秒cue不等于约5.1秒整句对白已配音，原声中字面内容也没有经本轮试听。cue-zero是PCM匹配轴，不是native命令时间，不写offset/gain、原CSV/phase或loop参数；不把native waveform LoopFlag当字段参数。`listeningPerformed:false`、`originalCsvRecovered:false`、`originalVoiceFieldRecovered:false`、`phaseOffsetGainOrSourceTimingRecovered:false`、`fullDialogueSpokenByCueAccepted:false`、saved播放/whole-episode false均保留。

本轮按root明确允许，对既有4kHz源WAV8053500B和已安装短cue52504B各读完整字节核SHA一次，分别仍 `ce16138f…`／`b7ab09e6…`；只哈希，不解码、重采样、NCC计算或播放。source/reference等其他大音频、ACB/AWB不重复读取或哈希，其SHA只作旧seal来源引用。原视频仅stat（116796723B），引用旧 `d7d29c63…` SHA，不能称fresh视频哈希。当前catalog、bank index和package cue记录/小cue payload一致；bank index8654B SHA `af186a85…`。这些界限均在 `bounded-payload-bindings.rootfalse.json` 和 target guards中区分。

保存接口完全复用已实际成功P21 stage51541/audit216c24/apply4d1620形状，不另造工具。Root接受窄身份/行内放置范围后，在新文件克隆packet并设该change的 `rootConfirmed:true`；最终HEAD仍需重新绑定，不能把此处报告的 audit-only8e33当未来授权。Root同时检查当前全局集合、其他139 pairs、protected22、代码/资源和完整目标行。原 node_fields 不强制 baseSha、UID、array index或全pair guards，这些外部检查不得丢失。

```sh
nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python -B -m story_studio.recovery.native_repair \
  --root /home/rikka/Projects/stella \
  --target /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/data-checkout \
  --directory /home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/native-directory.json \
  --node-fields /ABS/NEW-ROOT-APPROVED-VOICE58-PACKET.json --output /ABS/NEW-ABSENT-STAGE
```

随后原 `story_studio.recovery.native_install --root ROOT --target D --staging SAME-STAGE` 先audit（无 `--apply`）。Root审核 scenes1/counts.voice1，native只 `/scenario_list/5/voice` 一叶，完整37行及所有分支深等；sidecar仅原流程追加voice证据/必要unknown warning刷新，保留其他既有字段及证据。仅该场必要manifest summary、ownership pair/summary和新batch可更新，manifest也可能字节不变，不要求固定Git修改文件数。独立审核后才批准同命令加 `--apply`；发生错误保留原输出后停，不重跑parser或换入口。

当前不运行normal保存或5→6→7播放器核验，不伪造cue已试听、自然结束、progress、Stop清理或整句配音验收。本包是可供rootreview的候选，不提升旧strict-ready bucket，也不把旧作者的建议新增为用户要求的试听许可流程。

独立静审 receipt `c08d6b23…`／review `a9a92c21…` 已按原SHA引用，cue-identity must-fix0，同样只支持短cue/保守此行放置，root接受和试听仍false。其只读metadata指出preview Opus3885B已tracked，但没有package索引项；本包不冒称该项存在，也不因此要求重登已有原WAV。后续正常播放器交付仍待实际核验。本作者的8MB/52KB opaque SHA核对不归于peer，peer没有读取音频字节。
