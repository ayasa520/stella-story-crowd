# 正式站回读

脚本提交 d0ab8d7c7029d92f37851bd8c49c92a689f66899 已实际 push，随后 ls-remote 精确确认 main。正式站默认 native/source 返回该真实提交，完整 native/review 与已审查提交一致；正常 player/prepare 使用返回的真实提交、node23 与空 choices。

两次 HTTP 均为200；本场景38节点、40出边及入口 before JSON 与本地实播输入完全一致。正式站按section载入120节点，本地实播载入全库5619节点，未声称完整程序或线上实播等价。保留原响应gzip、实际headers、SHA及只读验证代码。没有改前端或重新部署Worker。

暂存核对曾因调用工具默认1MiB缓冲区中断；增大原始字节读取限额后78个已提交文件均与审查字节相同。该观察工具故障不被改写成脚本或JSON解析故障。整场和完整还原目标仍未验收。
