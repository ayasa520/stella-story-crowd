# P30 v2 普通 QA 元数据绑定准备

本包只适配已封 `p30-node4-ordinary-entry-owner-kit-rootfalse-v2`，未执行 collector、freeze、prepare、API、浏览器、媒体、语法检查或测试；未读取当前 D/C 成员库存，也未修改它们。最终 `finalDataHead`、输出目录、browserOwner 仍为 null，所有批准位 false。Root 须在 BGM3、P29 node22 与 P30 失败审计发布后选择最终 HEAD；此处不把当前报告的 HEAD 当执行绑定。

原 H `ordinary-QA-root-binding-preparation-v1/prepare-bindings.mjs` 不能仅换 request：它硬编码原7个可变正式路径，并强制 P22 模板、route、kit 和输出。本次完整差异见 `collector-v2-vs-v1.patch`：

- 加入 BGM3 的 `10020001/10020011/10020048` 六个 native/review 路径；原 `10090015` native、P29 `10040052` pair、P22 `10030006` pair、manifest/ownership 保留，共13个允许修改的正式路径。只接受 M；新增仍只接受 restoration-audits 或单层 restoration-batches 的 A。允许路径不代表接受其中任意字段，root 仍审核最终逐文件/逐叶差异。
- 锁定 P30 v2 目录、模板和 plan；移除全部 P22 请求处理、kit/route 绑定和输出。仅产生 inventory、P30 false inputs、五工具记录与 collection receipt；不执行任何下游工具。
- 明确要求 Qv3 历史合并集合仍为5536路径；先全部验证再扩展。旧实际成功 collection/inventory、H author receipt、失败 v1 closure 和 v2 peer receipt 以原 SHA 留在 additionalEvidence，作为历史证据，不能变成 v2 播放通过。原文件未重写。

仍使用原 Qv3 seed `a3ad8841…` 和原工具选择 `b46fc88f…`，不复制大型 JSON。原捕获字节/同次 SHA→JSON.parse、已有输出拒绝、首错留存不重试、全部 final byte/member/HEAD/status 检查未改变。输出目录建立后的 JSON hash/parse 异常保留本次 raw gzip、原 decoded UTF-8 gzip、原 error/offset；不会重读后覆盖失败输入。请求自身在输出目录建立前读取，失败仍按原 H 入口边界以 stderr/exit1 停止。

未来一次采集仍要求 source312/dist234 与 Qv3 完全同成员、同 SHA；22个原 baseline native/review 完全相同。fresh 枚举 D/native 与 D/review 全部成员，包括新 audits/batches；对 D 和 tracked C 输入用实际完整字节构造 Git blob OID，与最终 HEAD tree 比较。所有140个 native 的节点和每个原 branch_list 边数动态求和，不采用旧5624/5870常量。原 section1003/1045资源并集保持，以免缩减历史闭包；这不启动 P22。五工具仍核实际 ARM ELF、binary/launch SHA 与真实路径，Firefox 仍核原 wrapper。工具或资源字节核验只发生于后续独立授权的 collector。

## Root 的后续最小命令

先全文审核本包与固定13项 input bindings，再在新文件克隆 `collection-request.template.rootfalse.json`，填最终 exact committed/ACKed HEAD、全新直接 A 子目录（名称以 `ordinary-QA-root-bindings-` 开头）、owner 和非空 publicationGuards。保留原 additionalEvidence；可加真实本轮发布证据。只在独立批准一次元数据采集后设 `rootConfirmed/inventoryCollectionAuthorized=true`，`browserLaunchAuthorized=false` 不变。禁止改 sealed kit 或本包。

```sh
nice -n 19 taskset -c 0,1 /usr/bin/node \
  /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/ordinary-QA-root-binding-preparation-v2/prepare-bindings.mjs \
  --request /ABS/ROOT-COLLECTION-REQUEST.json --request-sha256 REQUEST_SHA256 \
  --script-sha256 446d90ba90b04c18730aee39c570bb852e04661cac20802daa5ff1819f688275
```

这是未来命令形状，本轮未执行。Node 无 preload/import，NODE_OPTIONS/NODE_PATH 必须未设。collector 成功仍不批准 freeze/API/browser；有错误保留原输出后停，不自动重跑。

Root 审新库存后，再在新文件克隆输出的 `p30-inputs.filled.rootfalse.json`，核 source/数据仍稳定，单独批准其 `rootConfirmed/freezeAuthorized/apiPreparationAuthorized/fullGlobalInventoryApproved=true`，browser 位保持 false。随后仅调用 v2 原 freeze：

```sh
nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python -B \
  /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/p30-node4-ordinary-entry-owner-kit-rootfalse-v2/freeze.py \
  --root-inputs /ABS/ROOT-P30-V2-PREPARATION.json --root-inputs-sha256 ROOT_P30_SHA
```

原 ordinary prepare 仍在 v2 kit cwd 使用 `/usr/bin/node --import ./transport.mjs ./prepare.mjs`，从 frozen binding 的 preparationRelease 读取批准；不采用 P22 环境入口。STELLA_HOSTING 保持未设。实际 prepare 出现未覆盖 before 依赖或失败就保留原 raw 停止，不 seed、换入口或伪造 program。此次不运行 P22 freeze/prepare/browser，不新建 launcher，不声明任何 source motion、phase、身份或实际播放验收。
