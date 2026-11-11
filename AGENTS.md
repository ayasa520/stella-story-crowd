# Stella project instructions

These instructions apply only to `/home/rikka/Projects/stella` and this project's repositories. They are not global preferences for other projects.

- 每完成一个经过核验、可审查的小进展，立即在对应的已配置远程仓库提交并 push，不等待整批或整章完成。允许无签名提交，例如 `git -c commit.gpgsign=false commit`。
- 只提交本次负责的文件，保留无关工作；不要因父目录没有 remote 就擅自创建远程或推送到其他项目。剧情数据仓库是 `story_crowd_data`；网站源使用已绑定的 canonical Site checkout。
- 严格限制 CPU：本任务的重计算及其子进程统一使用 nice 19，固定 CPU 22、23，FFmpeg 使用 1 个线程；先核实可用 CPU，若条件变化先记录证据再调整。
- 全项目同时最多一个测试 Chrome 会话。只有主代理明确指定的一个浏览器负责人可启动它；其他子代理只做离线工作。采集结束立即关闭并核实 CLI 和相关进程已退出，然后再审核本地图片。
- 识图全部交给子代理，主线程不查看图片；动作和表情必须对照原片完整入场过程，不能仅凭定格或技能结论填入。
- 未知原因先收集日志，不猜测，不归咎用户未安装最新版或缓存。复杂、重要代码修改保留详细英文注释。
