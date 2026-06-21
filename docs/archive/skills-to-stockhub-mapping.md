# Skills / 仓库 到 stockhub-mcp 的历史映射

> 归档说明：本文为方案讨论期的历史映射摘要，保留当时对数据源、能力分层与增强方向的判断；**不代表当前实时状态**。当前事实以 `docs/tracking/development-status.md`、`docs/tracking/current-capabilities.md` 与现行工具清单为准。

本文只保留后续仍有维护价值的历史结论：
- 哪些来源当时被视为主链路参考。
- 哪些来源更适合作为增强层、备源或设计参考。
- 这些来源大致映射到哪些工具方向。
- 它们各自的主要限制是什么。

## 一、历史分组结论

方案期的参考材料最终收敛为三类：

- **基础行情与主链路参考**：`a-stock-quote-1.9.0`、`yfinance-mcp-server-0.1.2`、`leek-fund`、`AkShare`
- **新闻 / 事件 / 研究资料增强**：`topnews-1.0.1`、`cnfinancialscraper-1.0.15`、`tencent-news`
- **研究型工具与输出结构参考**：`straightflush-1.0.0`、`tdx-1.0.0`、`tdx-pro-1.0.0`、`tdxuse-1.0.0`、`stock-selecter-3.2.0`、`stock-fundamental-analysis-v2-1.0.1`

## 二、优先参考来源

历史上最值得优先借鉴的来源主要是：

1. `a-stock-quote-1.9.0`
2. `yfinance-mcp-server-0.1.2`
3. `leek-fund`
4. `AkShare`
5. `topnews-1.0.1`
6. `cnfinancialscraper-1.0.15`

它们分别决定了：
- 免费主链路是否可行。
- 中国市场特色能力能否先用公开接口落地。
- 新闻、公告、研报和研究资料层应如何做增强。

## 三、来源映射摘要

| 来源 | 适用能力 | 最终定位 | 主要限制 |
|---|---|---|---|
| `a-stock-quote-1.9.0` | `get_realtime_quote`、`get_price_history`、`get_intraday_minutes`、`search_symbol`、`get_capital_flow`、`get_northbound_flow`、`get_sector_boards`、`get_dragon_tiger_list` | **A股 / 中国市场特色能力的默认免费主链路参考** | 公开接口稳定性与字段变动需要 fallback |
| `yfinance-mcp-server-0.1.2` | `get_realtime_quote`、`get_price_history`、`search_symbol`、`get_financial_statements`、`get_dividends_splits`、`get_analyst_forecasts`、`compare_stocks`、`screen_stocks`、`get_company_news`、`get_options_chain` | **美股 / 中国香港股票 / 全球基础层主链路参考** | 本质仍是 Yahoo Finance 单源，对 A股深度能力帮助有限 |
| `leek-fund` | A股、基金、ETF、板块、资金流等中国市场免费接口路线 | **中国市场免费公开接口主链路补充参考** | 更偏接口路线参考，仍需自行统一 schema 和稳定性处理 |
| `AkShare` | 基金 / ETF / 期货 / 宏观 / 中国市场扩展数据 | **中国市场增强层与 fallback 参考** | 覆盖广但口径较散，不适合作为单一主链路 |
| `straightflush-1.0.0` | `search_symbol`、`get_intraday_minutes`、`get_sector_constituents`、`get_dividends_splits`、`get_ipo_calendar`，以及盘口 / 大单 / 竞价异动候选能力 | **增强层 / 研究型能力 / 设计参考** | 依赖 SDK 或环境，不适合作为默认零配置主链路 |
| `tdx-1.0.0` | `get_realtime_quote`、`get_price_history`、`get_intraday_minutes`、`get_index_quote`、`get_financial_statements` | **中国市场备源参考** | 环境依赖重，更适合作为增强或备源 |
| `tdx-pro-1.0.0` | `get_batch_quotes`、`get_price_history`、`search_symbol`、`get_financial_statements`、`get_sector_constituents` | **技术备源 / 板块与财务增强参考** | 连接与环境管理复杂，不适合作为默认主链路 |
| `tdxuse-1.0.0` | `get_sector_constituents`、`get_ipo_info`、`get_dividends_splits`、`get_etf_info`、`get_convertible_bond_info` | **可选增强 / 终端能力参考** | 与终端生态耦合深，不适合作为开源默认实现 |
| `topnews-1.0.1` | `get_market_news`、`get_macro_news`、`get_pre_market_briefing`，以及情绪/简报增强候选能力 | **新闻主链路参考 + 处理链路参考** | 更像新闻处理项目，标的绑定、去重、结构化仍需补齐 |
| `cnfinancialscraper-1.0.15` | `get_company_announcements`、`get_research_reports`、`get_market_news`、`get_company_news`、`get_document_text`、`get_fund_company_profile` | **公告 / 研报 / 文档解析增强层参考** | 抓取稳定性与反爬成本较高 |
| `tencent-news` | `get_market_news`、`get_macro_news`、`get_pre_market_briefing` 的交互形态参考 | **设计参考 + 可选增强源** | 需要 API Key，且更偏通用新闻 |
| `stock-selecter-3.2.0` | `screen_stocks`、`rank_stocks`、`compare_candidates`、`get_strategy_signals` | **筛选 / 排名 / 评分 schema 参考** | 不是底层数据源，不适合当前主线优先实现 |
| `stock-fundamental-analysis-v2-1.0.1` | `analyze_fundamentals`、`compare_stocks`、`build_investment_note` | **研究型输出结构与分析模板参考** | 提供的是方法论，不是底层数据接口 |

## 四、保留下来的历史判断

### 默认免费主链路

- 美股 / 中国香港股票：`yfinance` 系来源更适合作为基础层。
- A股 / 中国市场特色能力：腾讯 / 新浪 / 东方财富 / `leek-fund` 路线更适合作为免费主链路。
- 中国市场增强与补充覆盖：`AkShare` 更适合放在增强层或 fallback。

### 当时已判断值得优先推进的能力

- 北向资金
- 龙虎榜
- 板块成分股
- 市场新闻
- 宏观新闻
- 简版盘前简报

### 当时更适合放在后续增强层的能力

- 标的级新闻绑定
- 去重聚合
- 情绪打分
- 盘口 / 大单 / 竞价异动
- ETF 资金流
- 两融余额
- 市场宽度
- 结构化事件层
- 盘中 / 盘后智能简报增强

## 五、如何使用这份归档

- 想追溯“为什么这些来源曾被纳入考虑”时，先看本文。
- 想看更原始的外部仓库参考清单时，再看 [`referenced-repos.md`](./referenced-repos.md)。
- 想确认当前项目事实，不要停留在 archive，直接转去 `docs/tracking/`。
