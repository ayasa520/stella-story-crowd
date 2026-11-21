# 第六话10020037／13：罗姆角色身份

依据独立审核的164个完整入场原帧与原装素材，只补
`scenario13.character: "" → "live2d/AC_rom01"`。
19条原行、ID、分支、台词、动作、表情、音频与命令保持原值；未知133不接线。
本次只接受角色资源身份，不接受身体动作、表情、额外层、阶段或精确时序。

使用现有native_repair／native_install：正常staging、无apply审计、root审批后apply均通过。
batch为`663ed9212407728ceb0c`，正式写集5文件：来源native／review、manifest摘要、
ownership及该batch记录。全部其他139场景、前三话22文件、资源与canonical源码未变。
当前状态仍为rough/in-progress；正常保存后的11→12→13选132→14连续实播尚待验收。

首次原stage在读取既有owned数据时出现JSONDecodeError，尚未进入本字段修改。
实际exception.doc已保留，与当前review/scenes/10020013.json仅5字节不同：
原ASCII `5e743` 在异常文档中变成5个NUL。该文件路径来自独立字节比较及源码循环推断，
首次故障没有捕获现场raw/path，不能将推断冒充现场输入。

随后只增加原异常traceback frame取证的单次原业务观测通过；解析器、业务模块与
来源文件没有修改，没有fallback或自动重试循环。该正常stage及安装门可以核验
本次保存，但并没有解释或修复首次读取异常。原失败和未知原因均保留。
