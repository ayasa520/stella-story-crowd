# P21 every07 裸 BGM 单字段包独立静审

无 must-fix。现有证据支持10030001/3只把bg_music空串改为裸ID bgm_adv_every07_cd2_13，仍待root批准并走原正常stage/audit/apply；本peer不签安装、试听或实播。

原opening161116B、location81592B、refinement12903B三份完整JSON已实读，连同全部397条既存候选记录；23/32两个三秒窗各65首的完整signed分数、全部64对照、原参考samples与摘要逐项相符。Every07为+0.7314580997542443/+0.9394449314712879；最强其他对照分别+0.25289731000829374和−0.34117605472333573，保留负号，分数不是概率。23秒三秒query的PCM SHA74103dab…在opening/location一致，原源视频声明SHAb3893cab…在三份原记录与卡3侧车一致。

三秒23–26窗跨过卡3的25秒尾界，所以卡归属使用原refinement的23、23.5、24秒三个一秒窗：+0.777301/+0.836464/+0.848306；原参考samples363/1363/2363及统一referencePCM SHAcfc98a24…保持。这三个窗在已保存23–25卡内。refinement只检索every07；65首对照来自三秒窗，不冒称一秒窗也做过65首负例。32秒564596/282.298只是独立身份control，不能推成23秒加9秒、offset、loop或restart。早期低/空结果不证明整段旁白静音；22.5–23仅原入场括区，不是sample-exact相位。

完整native20行、UID1003000100003、index2、stableKey s10030001-p21-at0023、完整原row/array/branch SHA及13 expected均exact；branch31→4、gain vector和其他19行不动，fields只有一个bg_music裸ID。旧identity包原字符串含,1,false；本候选不采纳其参数，不宣称原CSV/fade/reset/gain/volume/loop/STOP/offset/phase恢复，audioListened仍false。

旧封包的“尚未资源登记”文字及旧catalog/package守卫是历史观察，保持原件不改。独立实读正常安装receipt49249b06…、commit verification57671a87…和production receipt7756ddbe…；4df7c99b已登记，新D catalog009fb807/package47ca071b精确，默认fullcatalog/music/metadata三个200及payload字节匹配由原生产记录保留。此peer不重复登记、网络GET或音频读回。Root需在新的批准克隆中绑定实际最新HEAD/全局/资源守卫和这些新证据，不能执行历史旧metadata锁；其他139pairs/protected22仍由root实际正常门核。

没有读取PCM、NPZ、WAV/Opus/视频或图片，没有新匹配/相关计算、听音、解码、看图、helper、stage、audit、apply、API、浏览器、测试、build或Git调用。仅新peer目录写metadata；D/C、旧包及P30已发布audit未动。全部root/执行/安装/接受flags false，最终HEAD为null。

