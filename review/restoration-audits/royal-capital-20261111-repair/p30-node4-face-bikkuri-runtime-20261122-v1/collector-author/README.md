# P30 face-bikkuri：v3 formal metadata collector 准备

这是旧 v2 collector 的小范围静态适配，仅供已封 `p30-node4-face-bikkuri-owner-kit-rootfalse-v1` 使用。当前未 import、执行、语法/AST检查或测试 collector/freezer；没有采集新库存、读取工具ELF/媒体、请求API、启动浏览器或运行Git，也未读取或改写正式 D/C。最终 HEAD、owner、输出目录仍为 null，所有候选/准备/执行/浏览器批准位 false。Root选择最终已提交/ACK的HEAD后才可另行批准一次元数据采集；当前报告的 cleanup-audit HEAD不被当作最终执行绑定。

完整差异见 `collector-v3-vs-v2.patch`。只改：新 kit/模板/plan 路径；允许 root 已发布 every07 资源登记的 `assets/catalog.json`、`assets/package.json` 和 P21 `10030001` native/review 四个 M 路径（原13全部保留，共17）；绑定两份既有完整 source/closed-baseline actual review receipt；填新模板所需的 false metadata 字段。新增仍只准 restoration-audits 或单层 restoration-batches 的 A，不能把新的正式修改静默归类为审核文件。

`reuse-proof.rootfalse.json` 对五个完整核心源块作 v2→v3 逐字和 SHA 比较：JSON同次实际字节/SHA→parse与原失败留存、capture/实际Git blob/SHA与cached JSON、动态完整140场nodes/原branch计数、五ARM工具/launch、最终全部字节/成员/HEAD/status关闭门。它们均保持原字节，不执行这些函数。原 Qv3 5536旧路径先全部核验再扩集、tracked C source312/dist234精确成员和SHA、protected22、当前D/native+D/review全部成员及新audit/batch、资源并集和真实HEAD blob校验均保留。节点/边/global/data成员数始终从未来实际输入动态计算，不复制旧计数。

原 JSON 失败边界没有改：输出目录建立后的 hash/parse 异常保存本次 raw gzip、decoded UTF-8 gzip、原 error/offset；停下不重试、不改 parser。最初 request 在输出目录建立前读取，失败仍按旧入口边界保留 stderr/exit1。任何后续快照差异都须 root审核，不声称旧异常原因已修复。

`collection-request.template.rootfalse.json` 的 `sourceReviewGuards` 恰含两份原 receipt：primary `f4ede181…`，independent `0973607d…`。这些 receipt 明确保留 face mismatch / 当前不可安装结论；绑定其 SHA 不接受 face_bikkuri 或原 phase。相关既有 addendum、原metadata成功 collection/inventory、旧失败closure及旧collector也保留为原SHA历史证据，不复用旧批准位或旧 alias。

collector仅输出正式文件与证据的 fresh inventory、`p30-inputs.filled.rootfalse.json`、工具和 collection receipt。新模板会填真实 formal HEAD/source、global/publication/sourceReview/kit/tool/protected refs；`controlledNativeCandidateAuthorized`、所有授权位仍 false，`candidateAlias` 和 `budgets` 仍 null。**不产生 staged native、alias、修改后的 program/before或任何 frozen/prepared 文件**。未来只由原 sealed freeze 生成单叶 private52-row native及alias；该alias不是Git commit。本包不改正式motion，不签 body/face/phase、画面或 whole-scene 接受。

## Root 后续最小调用

全文审核代码、完整diff、reuseproof、request和新kit/独立peer。等最后正式/审计发布均完成后，在新文件克隆 request，填 `finalDataHead`、owner、非空真实 publicationGuards，以及全新直接A子目录，名字以 **`controlled-QA-root-bindings-`** 开头。保留 sourceReviewGuards 与历史 evidence。只批准本次读取时设 `rootConfirmed/inventoryCollectionAuthorized=true`；其余六个执行/候选/准备位和 browser位必须保持false。Node无preload，NODE_OPTIONS/NODE_PATH未设。

```sh
nice -n 19 taskset -c 0,1 /usr/bin/node \
  /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/controlled-QA-root-binding-preparation-v3/prepare-bindings.mjs \
  --request /ABS/ROOT-COLLECTION-REQUEST.json --request-sha256 REQUEST_SHA256 \
  --script-sha256 79345156ff52eed5192146bd5c0c1819c53b3da316779234b0e09868ce656334
```

这是未执行的未来命令。采集失败保留原输出和error后停，不自动重跑。成功输出仍不授权freeze/API/browser。

Root独立核全部 fresh guards 后，再在新文件克隆 filled false P30 inputs，明确填实际budgets及所需新的 `rootConfirmed/freezeAuthorized/apiPreparationAuthorized/fullGlobalInventoryApproved/controlledNativeCandidateAuthorized=true`，browserLaunch保持false。原freezer参数仍为：

```sh
nice -n 19 taskset -c 0,1 env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python -B \
  /home/rikka/Projects/stella/artifacts/stella-script-continuation-20261121/p30-node4-face-bikkuri-owner-kit-rootfalse-v1/freeze.py \
  --root-inputs /ABS/NEW-ROOT-FACE-PREPARATION.json --root-inputs-sha256 ROOT_PREPARATION_SHA
```

随后新kit cwd的原 prepare 必须在任何请求前加载 `./transport.mjs`：`/usr/bin/node --import ./transport.mjs ./prepare.mjs`，读取新 frozen binding 中的 preparationRelease。Root须独立审核 fresh baseline与candidate完整program、真实before、唯一face差异与原schema限定aliasURL差异，再决定独立一次browser release。这里不执行这些步骤，也不预填 alias、stage、token override、等待或程序替代。P22不再采集或运行。
