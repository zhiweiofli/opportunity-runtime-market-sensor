# Market Sensor 验证记录

业务版本：0.2.0。部署不代表正式异常规则或交易策略已验收。

| 阶段 | 状态 |
| --- | --- |
| 私有 GitHub 仓库 | 已创建 zhiweiofli/opportunity-runtime-market-sensor |
| 指南/原稿/代码推送 | 待推送 |
| 本地离线测试/CLI | Python 3.9.6，8/8 通过；fixture 3 条记录→2 条演示 Signal |
| Actions CI / 手动 fixture | 待实跑 |
| Tushare Secret / 真实 HTTPS | 用户已确认设置；GitHub Secret 名称查询暂未显示，待 Actions 实跑验证 |
| 正式规则/定时行情 | 未确定市场/标的/历史基准/阈值/频率，不启用 |
| Codex Cloud | CLI 已确认有账户环境，但尚无此新仓库对应环境；未提交开发任务 |

执行后更新实际 commit、run URL、artifact 与 Cloud 回执；失败也保留事实。
