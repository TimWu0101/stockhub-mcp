# 工具列表

> stockhub-mcp v0.4.0 — 43 工具

---

## 行情类

| # | 工具 | 说明 |
|---|---|---|
| 1 | `get_realtime_quote` | 单股实时行情（价格/涨跌/量/成交额） |
| 2 | `get_batch_quotes` | 批量查询（最多 20 只） |
| 3 | `get_source_status` | 数据源健康检查 |
| 4 | `clear_quote_cache` | 清空本地行情缓存 |

## 历史类

| # | 工具 | 说明 |
|---|---|---|
| 5 | `get_price_history` | K 线历史（日/周/月，前复权/后复权） |
| 6 | `get_trading_calendar` | 交易日历（按市场查询） |

## 技术分析

| # | 工具 | 说明 |
|---|---|---|
| 7 | `get_technical_indicators` | MA/MACD/RSI/KDJ/BOLL + 定性判断 |
| 8 | `get_quick_analysis` | Pipeline 一键组合：行情 + 指标 + 趋势 + 信号 |

## A 股特色

| # | 工具 | 说明 |
|---|---|---|
| 9 | `get_sector_boards` | 行业/概念板块涨跌榜 |
| 10 | `get_capital_flow` | 市场资金流向 |
| 11 | `get_northbound_flow` | 北向资金流 |
| 12 | `get_southbound_flow` | 南向资金流 |
| 13 | `get_dragon_tiger_list` | 龙虎榜（efinance/东方财富） |
| 14 | `get_sector_constituents` | 板块成分股 |
| 15 | `get_price_limits` | 涨跌停价格计算 |
| 16 | `get_symbol_status` | 停牌/退市/正常状态查询 |

## 基金 ETF

| # | 工具 | 说明 |
|---|---|---|
| 17 | `get_fund_quote` | 基金净值 |
| 18 | `get_fund_nav_history` | 基金历史净值 |
| 19 | `get_fund_rankings` | 基金排名 |
| 20 | `search_fund` | 基金搜索 |
| 21 | `get_etf_quote` | ETF 行情 |
| 22 | `get_etf_history` | ETF K 线历史 |
| 23 | `get_etf_info` | ETF 元数据 |

## 期货

| # | 工具 | 说明 |
|---|---|---|
| 24 | `search_futures_contract` | 期货合约搜索 |
| 25 | `get_futures_contract_info` | 期货合约详情 |
| 26 | `get_futures_position_rank` | 期货持仓排名 |
| 27 | `get_futures_basis_history` | 期货基差历史 |

## 研究估值

| # | 工具 | 说明 |
|---|---|---|
| 28 | `get_financial_statements` | 财务三表（利润/资产/现金流） |
| 29 | `get_valuation_metrics` | PE/PB/PS/PEG 估值指标 |
| 30 | `get_quality_metrics` | ROE/毛利率/净利率/股息率 |
| 31 | `get_valuation_percentile` | PE/PB 历史分位 |
| 32 | `get_dividends_splits` | 分红/拆股历史 |
| 33 | `get_holders` | 机构持仓 |
| 34 | `compare_stocks` | 多股票估值对比 |
| 35 | `search_symbol` | 标的模糊搜索 |

## 指数期权

| # | 工具 | 说明 |
|---|---|---|
| 36 | `get_index_quote` | 指数行情 |
| 37 | `get_index_history` | 指数历史 |
| 38 | `compare_indices` | 多指数收益对比 |
| 39 | `get_analyst_forecasts` | 分析师预测 |
| 40 | `get_options_chain` | 期权链（美股） |

## 组合风险

| # | 工具 | 说明 |
|---|---|---|
| 41 | `get_risk_metrics` | 波动率/最大回撤/夏普/VaR/Beta |
| 42 | `get_correlation_matrix` | 多标的相关性矩阵 |
| 43 | `analyze_portfolio_exposure` | 组合集中度/风险暴露 |
