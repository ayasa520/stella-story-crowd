找到一组可交 root 评估的下载归档缓存：/var/tmp/stella-arm64-packages-20261109。

精确白名单 archive-whitelist.rootfalse.json 列出37个wheel ZIP及1个Python gzip归档，共38个普通文件。实际逻辑大小429,752,584 B；st_blocks计量可释放allocated bytes为429,846,528 B（约409.93 MiB）。目录du为429,854,720 B，差额是明确保留的configure_target.py与目录元数据；不递归删除整个目录。每个候选的path/size/allocated/dev/inode/mtimeNs/ctimeNs/nlink/uid/gid均已列出，全部dev1050520、nlink1。未对430MB归档计算新SHA；file仅检查archive MIME header，未解包。

实际已安装Python解析到/home/rikka/.local/share/stella/python311/bin/python3.11；现有venv配置引用该路径。PySide6、QtCore/QtWebEngine扩展及QtWebEngineProcess解析到/home/rikka/Projects/stella/.venv-video-ocr内已安装文件。所有这些目标都在staging目录外。36个wheel版本有匹配的已安装dist-info；antlr4_python3_runtime4.9.3未见匹配安装，不补装、不测试。未发现安装环境.pth指向staging，也未见direct_url来源记录指向staging。保留configure_target.py、venv、独立Python树、Qt文件、tablet配置和所有launcher。没有导入PySide/Pillow/UnityPy或运行安装、应用、media/browser。

引用检查范围是audit.rootfalse.json逐项列出的20个metadata路径：实际存在并读取20个、缺失0个。包含当前P29node22源采集输入绑定、shared6a全局inventory与P22输入快照、旧F1/F2/F3/K4保留inventory/release、迁移保护metadata及此前清理receipt。查询为staging完整前缀和38个精确archive basename，均未命中。此结论仅覆盖所列实际读取材料，不能冒称扫描过全部项目、所有历史或外部守卫。不存在的列表项也不当作阴性证据。

进程快照未见pip/package/build进程名或已识别pip/build命令，也未在可读cmd/fd/maps中见staging引用。22个system进程fd/maps不可读取，明确保留此边界；未读取进程environment、浏览器profile/token或非匹配命令行内容。root实际执行前应自己重核白名单stat和live-use事实；本代理没有执行清理。

实际du/stat命令均nice19、CPU0,1。只计量.cache、/var/cache、/tmp、已命名安装缓存/下载目录，并发现该/var/tmp安装归档目录；未做全root hash或遍历原片/venv内容树。辅助计量的cc-switch/paru缓存、Mozilla/Floorp浏览器cache、Tracker DB等不在本白名单；没有删除用户下载、源码、Git objects或证据。/tmp为独立tmpfs，不当作持久备份或root磁盘收益。

本次最后root空闲快照为107,114,496 B，可能随其他工作变化。仅写本新报告目录；no cleanup performed。root将按既有“释放空间”授权独立选择并执行动作，本报告不是新增清理脚本。
