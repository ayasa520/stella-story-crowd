# P29 第22节点：独立原窗口采集准备，未执行

唯一目标10040052 / scenario22 / array21 / UID1004005200022 / stableKey `s10040052-p29-at0294p5`。当前 character 为空，模型未选，fieldsProposed 为空。完整行、13 expected 字段、38行顺序和显式21→22→23连接只作为元数据守卫，不构成身份或演出验收。

拟采唯一原PTS半开窗口 **[292,301)**，9秒、480×856；真实帧数以后从解码结果读取，约270只是规划值。原录像和SHA保持已正常执行node20的原源，不重转码原录像，不取样或改PTS。旧窗口止于290.989秒，新窗口从292秒起选，存在未采间隔；本次不读、复制、解码或拼接旧270帧，旧索引仅作上下文。完整入场/保持/退场及后继边界是否足够未知，未来实际采集完全关闭后再交子代理逐帧审核；不足保留结果报告，不自动扩窗。

`capture.py`复用已成功执行的node20脚本`9151cdad8699aba7e0f73f3c3e43290edf029226e5fd9b6511f2da3853cc15b7`。新SHA **1d7135622f82b39a8ba7c0c7698cc1d27f2f5a4aaf2a94a1e4a77a19e19cc962**，445行/23158B。只6个单行字面替换：node标签、START/END、PTS错误文案、select窗口、CLI描述、receipt schema；逆转后恢复原脚本完整SHA。输出目录由新脚本自身HERE限定为本新目录run-1，旧证据不改。完整diff在`node20-to-node22.minimal.diff`；未增加通用launcher或修改预算/清理内核。

保留原ARM venv `-I -B`、nice19/CPU0,1、FFmpeg和native线程各1；工具AArch64 ELF、实际Python/FFmpeg/Pillow105项和整源SHA在媒体前后fresh核，失败后各after观察独立保留。原始整数PTS/timebase、固定RGB24块、RAM先编码JPEG95再预算检查、无rawRGB落盘均不变。整个准备目录及run-1硬96MiB，普通写80MiB，16MiB失败预留，stderr1MiB，120秒，300帧是失败哨兵，成功必须自然EOF且低于300。owned进程TERM/KILL/wait/reap/PID/PG及reader事实闭合，首个解码错误不被清理错误掩盖。预计32–56MiB，当前可用空间仅为元数据快照，运行时仍重新检查至少96MiB。

本次只读取源码/JSON/当前目标元数据；未读或重hash源录像、JPEG、MOC、纹理和工具ELF，未import候选/Pillow，未运行helper、测试、编译、AST、probe、decoder、contacts、API、浏览器或Git，未写D/C。原源和工具摘要继承已关闭run/receipt，未冒充本轮fresh工具字节验证。当前只读HEAD观察为`6a6093e84895dd8292cdfbfb4154373bc36dc773`，native/review与已发布node20后的metadata exact，正式发布若发生应另fresh绑定。

所有rootConfirmed/executionAuthorized/installationAuthorized仍false；这些JSON标签不是CLI内部授权门。计划argv只是可审查文本，无自动执行入口；root/peer静审后，还须root给一次准确执行指令。P30冻结保持；不签角色、动作、表情、phase、原CSV字面、时序或实播。
