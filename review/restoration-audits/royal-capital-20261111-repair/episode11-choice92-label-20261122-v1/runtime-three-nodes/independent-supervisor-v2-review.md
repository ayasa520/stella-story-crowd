M1限定复审通过；must-fix为零，仅适用于run.v2.py SHA97c849f37e801f0275bc5996f72f5b9d36b4f030278d4f5981b8083e70fd0b95。旧run.py仍受M1阻断，不能据此放行它。

显式mkdtemp不自动删profile；每role stop与log.close独立捕获，不能打断其他owned清理。全部stop及输入核验之后读取真实OS清单，仅已知owned PID和PGID全空才进入唯一rmtree；有残留或清单未知就保留profile/path/log/errors并失败。早期stop错误即便最终进程均退出也保留为非零supervisor结果。各closure写入独立尝试并有stdout，物理I/O失败不冒称必有文件。

精确diff仅cleanup、显式profile生命周期、证据失败处理及run.v2自绑定。8个原sealed文件未变，3个Popen调用AST、原release/input门及play.mjs均未变；不扩M2，不改route/API/program/before/renderer/input/clock。旧完整46节点成功closure与先前报告原样保留。

此peer仅静态源码/AST/hash，未执行helper、fault path、API、browser、Git或业务工具。root仍需新release绑定v2与当前完整guards/program/sole owner；运行后须独立核escaped/PID/PGID/port/监督器退出，再审3张原JPEG。
