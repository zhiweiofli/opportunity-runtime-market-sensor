<!-- Google Doc: https://docs.google.com/document/d/1Zyt7oOWc7Y-h6QDwBckP3mcuILJHCIv7gjTMRCeUOus/edit?usp=drivesdk
Drive ID: 1Zyt7oOWc7Y-h6QDwBckP3mcuILJHCIv7gjTMRCeUOus
Modified: 2026-10-27T09:43:30.105Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: IBF-20261027-LegacyCNC-RS232-WirelessDNCBridge
* Source Signal References:
   * Signal ID: IBF-20261027-LegacyCNC-RS232-WirelessDNCBridge
   * Generated At: 2026-10-27T17:15:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/1Ue9ml6b14nJTn0H3gH1c8R6oKfaAeCsYiMgo-HenU-g/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-27T17:05:34+08:00
* Research Level: R1 — Quick Structure
* Stage Result: KILL
* Unknown Ledger:
   * Known: 老款数控机床（Fanuc 0i/16i/18i/21i, Haas Classic）因内存微小（128KB-2MB）无法容纳现代大体积 3D 刀路，且依赖软盘或易掉线的便宜 USB 串口线，在车间确实存在传输摩擦；但深入实证调研表明：
      1. 市场早已存在大量极其成熟且价格低廉的标准商业硬件产品（如 Highland DNC 生产的 ShopLink Wireless DNC 蓝牙/Wi-Fi 转换器起步价仅 $189，以及 Micro DNC USB 读卡器、AsiaMachinery BT-232B 等），且深耕工业数控市场十余年，市场供给充沛且已触及硬件成本底线。
      2. 交付与商业模式严重违背小团队约束：该方案的核心交付物为“制造实体工业硬件套件（光耦隔离 DB25 适配盒、ESP32 模块、工业电源与 3D 打印/注塑外壳）”，伴随繁重的工厂车间电磁干扰、不同机床控制柜引脚线序差异、波特率调试以及长尾退换货/保修/售后支持（甚至面临机床切削中途撞刀报废工件的高额连带法律索赔风险）；严重违背 1-3 人小团队“轻资产、零实体库存、低客服、高毛利”的核心约束。
   * Unknown: 无。
   * Decision-Critical Unknown: 无（已在 R1 确认强反证并终止）。
* Gate Checks:
   * Money: 通过。小微机加工厂主愿意为免除软盘跑腿支付 $150-$200 一次性硬件费。
   * Mechanism: 未通过。低成本无线串口/DNC 适配器并非市场供给真空，已有成熟标准答案（Highland DNC ShopLink $189 起）；不存在未被满足的结构性断层。
   * Persistence: 未评估（R1 阶段终止）。
   * Capture: 未通过。该场景严重违背小团队核心约束：
      1. 实体硬件制造与库存占用：需要生产、组装、测试、仓储与物流发货专用硬件套件。
      2. 重度工业售后与现场兼容性客服：不同年份 Fanuc/Haas 机床的参数（如 0000#2、0102#0、TV Check 校验、RS-232 硬件流控管脚接线）极其零碎，工厂强电磁干扰容易引发偶发丢包，客服负担极重。
      3. 连带损害赔偿风险：若外挂串口盒在在线滴注加工（Drip Feed）时发生固件死机导致机床主轴撞击虎钳，小团队无法承受高额工业索赔。
* Final Status: KILL
* Evidence:
   1. Highland DNC 官方产品页面《ShopLink Wireless DNC System》：成熟的低成本无线 CNC 串口通信套件起步价仅 $189，兼容 Fanuc、Haas 等主流系统，市场已有成熟低价供给。
   2. Industrial Monitor Direct 行业技术专文《CNC Floppy to USB: Fanuc Sneakernet Replacement Guide》（2026-09 发布）：详述无线 DNC 在车间落地面临的金属屏蔽死区、工业级安全隔离及持续 IT 维护负担。
   3. Reddit r/Machinists 讨论帖《Rant: Legacy CNC file transfers suck》（2026-03）：揭示机床车间环境恶劣且各类老旧控制器参数千差万别。
* Counter Evidence:
   1. 商业低价竞品充分：Highland DNC 等已有 $189 现成硬件。
   2. 硬件库存与极重工业售后客服：涉及实体硬件交付、强电干扰与撞刀连带责任，不符合小团队轻资产进入约束。
* Stop Reason: 存在足够强反证可 KILL。该摩擦已有成熟的低成本标准化工业硬件解决方案，且商业交付必须依赖实体硬件制造与重度工业现场售后，伴随潜在设备碰撞连带法律责任，完全违背 1-3 人小团队轻资产、低客服偏好。
* Resume Condition: 不适用（已 KILL）。
* What became more likely: 小型车间将继续通过采购市售低价 DNC 盒子（如 ShopLink）或在设备更新时直接购置带网络功能的新机床。
* What became less likely: 独立软件团队能以纯软件/轻资产形态切入机加车间老旧数控机床的物理串口改造市场。
* What did we rule out: 彻底排除了将涉及工业实体硬件与高危物理设备控制的改造项目作为小团队轻资产创业方向的可能。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-27T17:38:48+08:00
* Role Spec Status: reviewed