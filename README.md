# StockHub MCP

> 零配置、免费、43 工具的金融数据 MCP 服务器 —— A 股/港股/美股/基金/ETF/期货/指数，多源自动降级，为 AI 应用提供统一行情与分析接口。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.4.0-blue)](https://pypi.org/project/stockhub-mcp/)
[![Tools](https://img.shields.io/badge/tools-43-orange)](https://github.com/TimWu0101/stockhub-mcp/blob/main/docs/TOOLS.md)

---

## 为什么选 StockHub

| 特色 | 其他 MCP | StockHub |
|---|---|---|
| 配置要求 | 要配 API Key | **零配置可用**，6 源自动 fallback |
| 市场覆盖 | 单市场（美股为主） | **三市场统一**，A 股/港股/美股一套 schema |
| 技术分析 | 只给数字 | **智能定性**：7 档趋势 + 5 档量能 + 综合评分 |
| 风险分析 | 无或需付费 | **纯本地计算**：波动率/夏普/回撤/VaR/Beta/相关性矩阵 |
| AI 调用效率 | 一个请求一个指标 | **Pipeline 一键组合**：1 次调用 = 行情 + 6 指标 + 定性 |

---

## 能做什么

| 类别 | 能力 |
|---|---|
| 📈 实时行情 | A 股/港股/美股实时报价、批量查询 [→工具](./docs/TOOLS.md#行情类) |
| 📊 历史数据 | 多周期 K 线（日/周/月），前复权/后复权 [→工具](./docs/TOOLS.md#历史类) |
| 🔬 技术分析 | MA/MACD/RSI/KDJ/布林带 + 智能定性判断 [→工具](./docs/TOOLS.md#技术分析) |
| 🏭 板块资金 | 行业板块/概念板块涨跌、市场资金流向 [→工具](./docs/TOOLS.md#A股特色) |
| 🀄 A 股特色 | 龙虎榜、涨跌停、停牌查询、南/北向资金 [→工具](./docs/TOOLS.md#A股特色) |
| 💰 基金 ETF | 净值查询、历史净值、排名、ETF 详情 [→工具](./docs/TOOLS.md#基金ETF) |
| 📋 研究估值 | PE/PB/PS/PEG、ROE、财务三表、历史分位 [→工具](./docs/TOOLS.md#研究估值) |
| 📉 组合风险 | 相关性矩阵、组合暴露分析、波动率/夏普/VaR [→工具](./docs/TOOLS.md#组合风险) |
| 🏛️ 指数期权 | 指数行情/对比、期权链（美股）、分析师预测 [→工具](./docs/TOOLS.md#指数期权) |

[完整 43 工具列表 →](./docs/TOOLS.md)

## 数据源架构

**6 数据源，自动降级，零配置：**

```
efinance → 东方财富 → 腾讯 → 新浪 → yfinance → AkShare
  (A股增强)   (主要)    (行情)   (备源)   (美股/港股)   (兜底)
```

| 市场 | 数据源 | 免配置 |
|---|---|---|
| 🇨🇳 A 股 | efinance、东方财富、腾讯、新浪 | ✅ |
| 🇭🇰 港股 | 腾讯、yfinance | ✅ |
| 🇺🇸 美股 | yfinance | ✅ |
| 💰 基金/ETF | 东方财富 | ✅ |
| 🛢️ 期货 | AkShare | ✅ |

---

## 快速开始

```bash
pip install stockhub-mcp

# 可选：A 股龙虎榜/资金流更稳定
pip install efinance
```

### MCP 客户端配置

```json
{
  "mcpServers": {
    "stockhub": {
      "command": "fastmcp",
      "args": ["run", "stockhub_mcp.server:mcp"]
    }
  }
}
```

---

## 使用示例

### 一键 Pipeline 分析

```
→ 快速分析下贵州茅台

← 贵州茅台 ¥1,215.00 跌 -2.02%
   趋势：空头排列 | MACD 死叉 | RSI 超卖(17.25)反弹信号
   阻力：MA5=1,254.74 | 偏离 -3.17%
   信号：卖出(10分) | 量能：正常
```
*一个调用 = 行情 + MA/MACD/RSI/KDJ/BOLL + 趋势定性 + 信号评分*

### 组合相关性矩阵

```
→ 茅台、五粮液、招行、美的四只票相关性怎么样

← 茅台↔五粮液 0.77(高度同步) | 招行↔美的 0.28(最佳分散)
```
*4 只标的，32 次历史查询并行完成，无需任何外部 API*

### 一键风险报告

```
→ 茅台过去一年风险多大

← 年化波动 20.05% | 最大回撤 -21.86%
   夏普比率 -0.83 | 日 VaR(95%) -1.75%
```
*纯 numpy 本地计算，不依赖任何外部服务*

### 技术面深度诊断

```
→ 茅台技术面什么状态

← 空头排列，价格低于全部均线
   MACD 死叉，DIF=-28.22 DIF <- DEA=-26.85
   RSI6=17.25 极度超卖，RSI14=21.17
   KDJ J=-3.02 罕见负值钝化
   跌破布林下轨 1,226.79 → 1215 进入超跌区域
   综合评分：10/100 卖出信号
```
*7 指标联动分析 + 定性判断，不只是数值输出*

### 龙虎榜监控

```
→ 最近龙虎榜有哪些游资动向

← 100 只上榜，净买入前 3：中钨高新 +6.39 亿、铂力特涨停、天和磁材+2.54 亿
   净卖出前 3：光迅科技 -0.97 亿、兆易创新、宁波华翔
```

### 多市场统一查询

```
→ 对比腾讯(港股)和苹果(美股)的估值

← 腾讯：PE=22.4 / PB=5.2 / 股息率=0.3%
   苹果：PE=32.1 / PB=38.5 / 股息率=0.46%
```
*同一工具、同一 schema，不切换数据源*

---

## 架构

```
stockhub_mcp/
├── server.py          # FastMCP 入口，43 工具注册
├── domain/            # 领域层：符号解析、响应构建、交易时段
├── models/            # 17 个 Pydantic 数据模型
├── services/          # 6 个数据源 + 路由 + 熔断 + 缓存
├── tools/             # 17 个工具实现模块
└── core/              # Pipeline 流水线引擎
```

## 文档

- [完整工具列表](./docs/TOOLS.md)
- [Schema 参考](./docs/design/schema-reference.md)
- [路线图](./docs/tracking/roadmap.md)
- [CHANGELOG](./CHANGELOG.md)

## 免责声明

⚠️ 数据来自公开免费接口，不保证实时性、完整性和准确性。本项目不构成任何投资建议。

## 许可证

MIT
