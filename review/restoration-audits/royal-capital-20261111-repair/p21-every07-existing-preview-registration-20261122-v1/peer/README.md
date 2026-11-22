# P21 every07 两文件资源登记独立静审

无 must-fix。候选 seal5654c6d0、catalog009fb807、package47ca071b与完整原件 SHA/字节一致。完整 JSON 对象比对仅有声明的新增及记账更新：music20→21；package records5449→5451；加入已存在 Opus1234086B与metadata287B两记录，更新catalog记录，并把总bytes537535025改为538769567。总差1234542=两payload索引1234373+catalog新增169；新旧package.bytes分别等于全部成员bytes之和。

另做原字节核对：catalog完整原文件在偏移3010271处只插入169B指定music键/row，0原字节删除或改写；package候选与原对象加精确声明差异后的compact UTF-8/newline字节完全相同。Node compact JSON本身未逐字节重现新旧catalog，报告保留这项事实；该格式差异不被归因或修正，catalog使用更直接的完整原字节单插入证明。

全部旧键值与旧索引顺序保持，compact已有music row完全相同。19个既有输入、六metadata locks、两reusedPayloadLocks均核完整SHA/bytes；manifest.assets仍缺省、外部manifest/ownership/native/review守卫一致，10030001/3的bg_music仍为空。Opus仅按不透明字节算SHA，没有解码、播放、读波形或媒体内容审核。

原A/apply-asset-plan.py完整3500B、SHAff5ef8fa接口已静读：两个位置参数、无dry-run，验证真实HEAD/所有metadata与复用payload、全候选及旧值后直接写catalog/package并读回。模板恰好两个变更，expectedBaseHead为null且root/execution flags仍false；root单独绑定实际HEAD及决定应用。原helper未import/执行。

此包仅资源登记。它没有node_fields/import请求，也不接受BGM字段、原CSV/fade/reset/volume/loop/offset/STOP/phase、播放或整场。所有root/执行/安装/接受flags仍false，finalHEAD=null。未修改D/C、payload、manifest、ownership、native或P30已发布证据；没有调用项目helper/API/浏览器/FFmpeg/ffprobe/测试/构建/Git。

