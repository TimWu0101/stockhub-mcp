# StockHub MCP

> 一个零配置、免费的金融数据 MCP 服务器，覆盖 A 股、港股、美股、基金、ETF、期货、指数，为 AI 应用提供统一的行情与分析接口。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tools](https://img.shields.io/badge/tools-40-orange)](#工具列表)

---

## 能做什么

| 类别 | 能力 |
|---|---|
| 📈 实时行情 | A 股/港股/美股实时报价、批量查询 |
| 📊 历史数据 | 多周期 K 线（日/周/月），前复权/后复权 |
| 🔬 技术分析 | MA/MACD/RSI/KDJ/布林带 + 智能定性判断 |
| 🏭 板块资金 | 行业板块/概念板块涨跌、市场资金流向 |
| 🀄 A 股特色 | 龙虎榜、涨跌停计算、停牌查询、板块成分股 |
| 💰 基金 ETF | 净值查询、历史净值、排名、ETF 详情 |
| 📋 基本面 | 估值指标（PE/PB/PS/PEG）、盈利能力、财务三表 |
| 💸 分红持仓 | 分红历史、拆股记录、机构持仓 |
| 🏛️ 指数对比 | 标普/纳斯达克/恒生等指数行情与多指数对比 |
| 🔮 分析预测 | 分析师预测、期权链（美股） |
| ⚡ 快捷分析 | 一键组合：行情 + 技术指标 + 趋势判断 |

## 覆盖范围

| 市场 | 资产类型 | 数据源 |
|---|---|---|
| 🇨🇳 A 股 | 股票、板块、资金流、龙虎榜 | efinance、腾讯、新浪、东方财富 |
| 🇭🇰 港股 | 股票、指数 | 腾讯、yfinance |
| 🇺🇸 美股 | 股票、期权、基本面 | yfinance |
| 💰 基金 | 公募基金净值/排名/搜索 | 东方财富 |
| 📦 ETF | 行情/历史/元数据 | 东方财富、yfinance |
| 🛢️ 期货 | 合约/仓单/基差 | AkShare |

**6 个数据源，多级降级：** efinance → 东方财富 HTTP → 腾讯 → 新浪 → yfinance → AkShare，自动 fallback，无需配置。

## 快速开始

### 安装

```bash
pip install stockhub-mcp

# 可选增强（A 股龙虎榜/资金流更稳定）
pip install efinance
```

### MCP 客户端配置

安装后，在 MCP 客户端配置文件中添加：

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

如果你使用的是 **Claude Desktop**，配置文件路径为 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）。

## 使用示例

### 查行情

```
→ 帮我查贵州茅台的实时行情

← 贵州茅台 (600519)：¥1,215.00，跌幅 -2.02%，成交量 574 万手
   今开 1,235 / 最高 1,238.87 / 最低 1,211.22
```

### 技术分析

```
→ 帮我分析茅台的技术指标

← 贵州茅台 (600519) │ 数据日期：2026-06-18
   📉 空头排列 | MA5=1,254.74 | MACD 死叉
   📊 RSI6=17.25 超卖 | KDJ J=-3.02 钝化
   🟡 信号：卖出（评分 10）| 理由：MACD死叉 + RSI超卖反弹信号
```

### 估值对比

```
→ 对比一下茅台和五粮液的估值

← 贵州茅台：PE=18.4 / PB=8.5 / 股息率=0.36%
   五粮液：PE=14.2 / PB=7.1 / 股息率=3.5%
```

### 龙虎榜

```
→ 今天龙虎榜有哪些

← 100 只上榜股票：
   中钨高新 +10.0% 净买入 6.39 亿 | 铂力特 +20% 涨停
   光迅科技 +10.0% 净卖出 9,652 万 | 兆易创新 +7.3%
```

## 工具列表

| # | 工具 | 说明 |
|---|---|---|
| 1 | `get_realtime_quote` | 单股实时行情 |
| 2 | `get_price_history` | K 线历史数据 |
| 3 | `get_batch_quotes` | 批量行情查询 |
| 4 | `get_technical_indicators` | 技术指标 + 定性分析 |
| 5 | `get_sector_boards` | 行业/概念板块 |
| 6 | `get_capital_flow` | 市场资金流向 |
| 7 | `search_symbol` | 标的模糊搜索 |
| 8 | `get_source_status` | 数据源健康检查 |
| 9 | `get_trading_calendar` | 交易日历查询 |
| 10 | `clear_quote_cache` | 清空行情缓存 |
| 11 | `get_northbound_flow` | 北向资金流 |
| 12 | `get_southbound_flow` | 南向资金流 |
| 13 | `get_dragon_tiger_list` | 龙虎榜 |
| 14 | `get_sector_constituents` | 板块成分股 |
| 15 | `get_price_limits` | 涨跌停计算 |
| 16 | `get_symbol_status` | 标的交易状态 |
| 17 | `get_fund_quote` | 基金净值 |
| 18 | `get_fund_nav_history` | 基金历史净值 |
| 19 | `get_fund_rankings` | 基金排名 |
| 20 | `search_fund` | 基金搜索 |
| 21 | `get_etf_quote` | ETF 行情 |
| 22 | `get_etf_history` | ETF K线历史 |
| 23 | `get_etf_info` | ETF 元数据 |
| 24 | `search_futures_contract` | 期货合约搜索 |
| 25 | `get_futures_contract_info` | 期货合约详情 |
| 26 | `get_futures_position_rank` | 期货持仓排名 |
| 27 | `get_futures_basis_history` | 期货基差历史 |
| 28 | `get_financial_statements` | 财务三表 |
| 29 | `get_valuation_metrics` | 估值指标 |
| 30 | `get_quality_metrics` | 盈利能力指标 |
| 31 | `get_dividends_splits` | 分红/拆股历史 |
| 32 | `get_holders` | 机构持仓 |
| 33 | `get_analyst_forecasts` | 分析师预测 |
| 34 | `get_options_chain` | 期权链 |
| 35 | `get_index_quote` | 指数行情 |
| 36 | `get_index_history` | 指数历史 |
| 37 | `compare_stocks` | 股票估值对比 |
| 38 | `compare_indices` | 指数收益对比 |
| 39 | `get_valuation_percentile` | PE/PB 历史分位 |
| 40 | `get_quick_analysis` | 一键组合分析 |

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

## 免责声明

⚠️ 数据来自公开免费接口（腾讯、新浪、东方财富、yfinance、AkShare、efinance），不保证实时性、完整性和准确性。本项目不构成任何投资建议，使用者自行承担投资风险。

## 许可证

MIT
