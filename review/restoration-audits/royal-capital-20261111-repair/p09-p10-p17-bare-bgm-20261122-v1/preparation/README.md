# P09/P10/P17：三项 bare BGM 正常保存准备

**仅准备三个空→bare resource ID，全部root/执行/安装标志false，finalDataHead=null。** 没有helper/stage/audit/apply、测试、API/browser/media/Git或D/C写入，没有读模型、音频、视频、图片或压缩文件字节；未试听、重算相关或接受连续播放。没有复制P12/P15的已保存字段，旧成功包只作为正常workflow参照。

|part|scene/scenario；数组index|实际UID|stableKey|唯一候选|
|---|---|---|---|---|
|P09|10020001/2；1|1002000100002|s10020001-p09-summary|bg_music=`bgm_adv_fuon01_cd2_03`|
|P10|10020011/2；1|1002001100002|s10020011-p10-at0022|bg_music=`bgm_adv_fuon02_cd2_14`|
|P17|10020048/7；6|1002004800007|s10020048-p17-at0048|bg_music=`bgm_adv_fuon02_cd2_14`|

原seal当前实际剩4项，只有这3项进入packet。P21/10030001:3 `bgm_adv_every07_cd2_13` 的正常catalog/package登记另行处理，完全排除；P08/P12/P15及P21/P22 CLEAR等已保存项不重复。P17只属于Julius的第7对白卡，不能挪到开场旁白。

已完整读 `chapter1-audio-five-remaining-offline-preflight-v1` seal/report，核原三个source packet JSON及当前6个native/review完整文件。新packet保留完整13项expected；`target-guards.rootfalse.json`另有whole oldrow、branch_list、UID/原数组index、完整scenario数组与每行branch身份顺序、review/manifest entry/ownership原字节和摘要哈希。三行仍bg_music空，所有声明precondition匹配，无其他候选叶。三个scene都已owned，不adopt。其余137场景的fresh全局守卫由root最终stage前提供，本包没有生成另一个大库存或冒称已核整库门禁。

来源差异如实保留：P09旧source packet的sourceText为当前中文native，当前review的JP另存且用于新change.sourceText，未把旧中文当原稿JP；P10旧packet没有UID，新UID来自当前唯一native行，旧包不被追认为签过它。P09多窗、P10 moderate多窗+既有8k复核、P17单主窗及已有细化的来源/negative controls/限制仍由原seal及旧source packet精确SHA绑定；本轮没有再次测量或试听。

## 文件和资源边界

- `node-fields.rootfalse.json`：单个正常node_fields packet，3个changes，每项rootConfirmed=false，fields仅一个bg_music；无CSV逗号参数、motion、command、volume/loop/phase/offset/STOP字段。
- `target-guards.rootfalse.json`：当前整pair/row/branch/order、ownership及catalog/package byteguards。fuon01正常full catalog指向已注册的preview Opus/JSON；fuon02正常指向full music Opus/JSON。full catalog entry和package中的bytes/SHA声明均与原seal相符。音频及单独music metadata payload只做filesystem存在/尺寸观察；其SHA来自原seal，**本轮未重新读取/哈希这些payload**，不标成fresh audio验证。
- `root-request.template.rootfalse.json`：packet/guards/code/目录精确引用、正常CLI参数、预期3scenes/counts.bg_music=3，final HEAD/global guard/新stage目录均留null。不是可执行业务runner，也没有自动批准行为。
- `input-bindings.rootfalse.json`：本轮仅28份metadata/源码输入。包含原bare-ID语法和fade/reset来源，不读取其指向的音频/视频/模型文件。

bare ID 的原生语法与P12/P15正常stage60718→audit3a315f→apply24f845、发布6fe247…/exactACK/production完整readback已有参照。仅resource-id是候选；旧包装常量的fade/reset后缀不复制到字段，也不能改说成volume/loop。原CSV字面值、fade/reset、gain/loop、STOP/offset、CMD phase、主观听感、声音同步和整场仍未接受。资源metadata的loop=true不能变成原节点作者参数证据。

## Root 未来最小操作参数

先在独立新目录克隆packet和request。root阅读窄来源后才批准顶层及**每个change** rootConfirmed，并明确仅resource-id；保持13expected、3个bare ID、UID/branch/order/其他字段完整。最终stage前读取届时真实HEAD/clean/原pair/ownership/目录及resource/global守卫，填新的final HEAD与全局绑定，重算各JSON SHA。不要硬绑6a、1f或本轮任何过渡audit HEAD；如期间资源登记或正式数据变化，也必须fresh核对。原packet/本准备目录保持不动。

源码真实约束：`native_repair.py:193–216`只强制每change.rootConfirmed、stableKey和declared expected；不会强制baseSha、UID、arrayIndex、sourceText、整文件/资源receipt或顶层executionAuthorized。上述额外byteguards必须由root外部核对。`InstalledSnapshot`只加载已owned场景并核其原文件/summary；`stage`保持原身份/顺序并刷新正常review warnings。`native_install.py:80–109`再核ownership快照和full catalog资源，先不写audit，再明确apply。

以下仅原参数说明，本轮未执行；cwd项目根。root使用另行批准的真实路径，stage必须新且不存在，并在D外：

```sh
nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 python -B -m story_studio.recovery.native_repair \
  --root /home/rikka/Projects/stella \
  --target /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/data-checkout \
  --directory /home/rikka/Projects/stella/data/native_recovery/royal-capital-20261110/native-directory.json \
  --node-fields /ABS/ROOT-APPROVED-THREE-BGM.json --output /ABS/NEW-ABSENT-STAGE

nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 python -B -m story_studio.recovery.native_install \
  --root /home/rikka/Projects/stella \
  --target /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/data-checkout \
  --staging /ABS/NEW-ABSENT-STAGE
```

预期stage为3个目标scene、counts.bg_music=3；逐scene native只这一叶空→ID，所有行/分支/UID/order/台词/其他12项expected精确。sidecar正常变化仅本target新增bg_music evidence、移除bg_music unknown及对应warning/派生summary，不要求整个review byte-identical，也不扩大draft/source文本等接受。其他scene及前三话原22保护保持。root独立审stage语义和原audit通过后，才在第二条同stage命令追加 `--apply`；无`--baseSha/--audit/--dry-run`参数。若出现额外scene/叶、原parser/资源门禁错误，保留原raw/日志并停，不重试、换parser、绕owned或直接写文件。

正式允许变化只限三对native/review、必要manifest/ownership及一个实际新batch；不强制Git modified文件数，manifest可byte-identical。之后root按正常精确commit/push/ACK及普通production native/review readback发布，连续播放/听感另行核验。本包未批准、执行或签署任何这些后续步骤。
