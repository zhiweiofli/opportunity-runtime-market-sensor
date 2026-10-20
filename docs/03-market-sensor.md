# Market Sensor

## 1. 使命

Market Sensor 负责发现：

> **资金流、价格、风险和结构关系中值得进一步研究的异常。**

它不负责荐股，也不负责直接下单。

---

## 2. 重点观察

- Price
- Volume
- ETF Flow
- Futures Basis
- Yield Spread
- Credit Spread
- Volatility
- IV / RV
- Skew
- Positioning
- Borrow Cost
- Funding Cost
- Relative Value
- Valuation
- Regime Change
- Liquidity

---

## 3. 核心问题

Market Sensor 不问：

> 哪个资产会上涨？

而问：

> **哪里出现了可能具有经济意义的异常定价或资金结构变化？**

---

## 4. Signal 类型

### Flow Shift

资金显著流入 / 流出某类资产。

### Relative Mispricing

两个历史或经济上相关的资产关系出现异常。

### Carry / Basis

存在持续可观察的收益差或基差。

### Volatility Mispricing

隐含波动和实际波动关系出现异常。

### Positioning Extreme

市场仓位明显拥挤。

### Regime Shift

利率、流动性、美元、商品、信用等结构关系发生变化。

---

## 5. 原始素材

尽量使用结构化数据。

- Market Price
- Volume
- Futures
- Options
- ETF Flow
- Rates
- FX
- Commodities
- Fundamental Data
- Macro Data
- Positioning Data

文本信息只用于解释异常，不用于生成核心 Signal。

---

## 6. Signal 格式

```text
Signal

Anomaly
发生了什么市场异常？

Instrument
涉及什么资产 / spread / strategy universe？

Magnitude
历史分位、偏离程度或其他量化描述。

Persistence
一次性 / 持续 / 正在扩大。

Possible Mechanism
可能的经济解释，但明确区分事实与推测。

Data Quality
数据是否可靠、是否足够长。

Next Question
下一步需要验证什么？
```

---

## 7. 触发 Research

至少满足：

- 异常可量化
- 有足够历史背景
- 不是单个价格跳动
- 有潜在经济机制
- 有可交易工具
- 流动性不明显不足

---

## 8. Market Research 升级条件

要形成 Trade Hypothesis，至少需要回答：

- What is mispriced?
- Why?
- Why does it persist?
- What closes the gap?
- How long?
- What does it cost to express?
- What invalidates it?

然后停止 narrative research，进入：

- Backtest
- Walk-forward
- Out-of-sample
- Slippage
- Transaction Cost
- Capacity
- Risk

---

## 9. 快速 Kill

优先 Kill：

- 数据不足
- 异常不可重复
- 流动性不足
- 成本吃掉全部收益
- 没有 convergence / catalyst
- 只是“价格很便宜”
- 解释完全依赖宏观故事
- 需要无法获得的数据才能验证

---

## 10. Sensor 不应该做什么

不要：

- 推荐买卖
- 根据新闻预测价格
- 让 LLM 在整个行情里“凭感觉找机会”
- 把回测前的想法当策略

它只负责回答：

> **哪里的钱可能被错误定价？**
