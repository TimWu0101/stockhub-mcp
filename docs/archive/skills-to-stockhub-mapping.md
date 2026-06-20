# Skills / 仓库 到 stockhub-mcp 的映射清单

这份文档把当前已经分析过的 skill / GitHub 仓库，映射成：

- 借鉴来源
- 可用接口 / 能力
- 对应 `stockhub-mcp` 的工具方向
- 建议归属版本
- 是否适合作为默认免费主链路
- 风险 / 限制

用于后续开发时快速查找，不再反复翻对话记录。

---

## 一、总原则

### 1. 数据源分层
- **默认免费主链路**：零配置或尽量少配置，适合作为开源项目默认能力
- **免费增强 / 兜底源**：免费可用，但稳定性、覆盖面或依赖条件略弱
- **可选增强源**：需要 API Key、SDK、终端或特定环境，仅作为可选扩展
- **设计 / 架构参考**：不直接当数据源，但可借鉴工具设计、schema、抓取链路、输出结构

### 2. 版本归属原则
- **V0.1**：基础行情闭环
- **V0.2**：中国市场增强
- **V0.3**：研究与上下文
- **V1.1**：高价值但结构化程度更高、或免费接口稳定性仍需继续验证的增强能力

---

## 二、逐项映射

## 1. a-stock-quote-1.9.0

### 借鉴来源
- 腾讯财经实时行情 API：`qt.gtimg.cn`
- 新浪财经备用行情 API：`hq.sinajs.cn`
- 腾讯分时 API：`ifzq.gtimg.cn`
- 腾讯 K 线 API：`web.ifzq.gtimg.cn`
- 东方财富资金流 / 北向资金 / 板块排名 / 龙虎榜

### 对应我们可做的工具
- `get_realtime_quote`
- `get_price_history`
- `get_intraday_minutes`
- `search_symbol`
- `get_capital_flow`
- `get_northbound_flow`
- `get_sector_boards`
- `get_dragon_tiger_list`

### 建议版本
- `V0.1`：实时行情、历史、分时、搜索、板块、资金流
- `V0.2`：北向资金、龙虎榜

### 是否免费
- **是**，适合当默认免费主链路

### 定位
- **默认免费主链路（A股 / 指数 / 中国市场特色能力）**

### 风险 / 限制
- 公开接口稳定性需要 fallback
- 字段格式可能变化
- 适合搭配新浪 / 东方财富多源兜底

---

## 2. straightflush-1.0.0

### 借鉴来源
- `search_symbols`
- `klines`
- `intraday_data`
- `depth`
- `big_order_flow`
- `call_auction_anomaly`
- `ths_industry`
- `ths_concept`
- `block_constituents`
- `news`
- `corporate_action`
- `ipo_today` / `ipo_wait`

### 对应我们可做的工具
- `search_symbol`
- `get_intraday_minutes`
- `get_order_book`（候选）
- `get_big_order_flow`（候选）
- `get_call_auction_anomalies`（候选）
- `get_sector_constituents`
- `get_company_news`（增强）
- `get_dividends_splits`
- `get_ipo_calendar`

### 建议版本
- `V0.2`：板块成分股
- `V0.3`：公司行动、资讯增强
- `V1.1`：盘口、大单、竞价异动、IPO 增强

### 是否免费
- **不完全按“零配置公开接口”理解**，更适合作为增强层参考

### 定位
- **免费增强 / 可选增强 / 设计参考**

### 风险 / 限制
- 依赖 SDK / 环境
- 稳定性和授权边界需单独评估
- 不建议作为默认主链路

---

## 3. tdx-1.0.0

### 借鉴来源
- 实时行情
- 历史 K 线
- 指数行情
- 分钟数据
- 财务报表解析
- 本地通达信数据读取

### 对应我们可做的工具
- `get_realtime_quote`
- `get_price_history`
- `get_intraday_minutes`
- `get_index_quote`
- `get_financial_statements`

### 建议版本
- `V0.2`：作为 A股 / 指数增强备源
- `V0.3`：财务数据解析增强

### 是否免费
- **偏免费，但依赖环境较重**

### 定位
- **免费增强 / 备源参考**

### 风险 / 限制
- 环境依赖重
- 不适合作为默认零配置链路

---

## 4. tdx-pro-1.0.0

### 借鉴来源
- `get_realtime_quote`
- `get_batch_quotes`
- `get_kline_data`
- `get_index_kline_data`
- `get_minute_time_data`
- `get_security_list`
- `get_finance_info`
- `get_block_info`

### 对应我们可做的工具
- `get_realtime_quote`
- `get_batch_quotes`
- `get_price_history`
- `search_symbol`
- `get_financial_statements`
- `get_sector_constituents`

### 建议版本
- `V0.2`：板块与批量行情增强
- `V0.3`：财务信息增强

### 是否免费
- **偏免费，但有环境成本**

### 定位
- **免费增强 / 技术备源**

### 风险 / 限制
- 环境与连接管理较复杂
- 更适合备源，不适合作为默认主链路

---

## 5. tdxuse-1.0.0

### 借鉴来源
- 板块列表 / 成分股
- IPO 数据
- 分红因子 / 股本信息
- ETF 跟踪指数信息
- 可转债信息
- 实时订阅

### 对应我们可做的工具
- `get_sector_constituents`
- `get_ipo_info`
- `get_dividends_splits`
- `get_etf_info`
- `get_convertible_bond_info`

### 建议版本
- `V0.3`：ETF / 分红增强
- `V1.1`：IPO / 可转债 / 订阅类能力

### 是否免费
- **更偏终端能力，不适合作为默认免费主链路**

### 定位
- **可选增强 / 设计参考**

### 风险 / 限制
- 与终端生态耦合深
- 不适合开源项目默认实现

---

## 6. yfinance-mcp-server-0.1.2

### 借鉴来源
- `tool_get_stock_price`
- `tool_get_stock_info`
- `tool_get_history`
- `tool_get_financials`
- `tool_get_recommendations`
- `tool_get_options`
- `tool_get_dividends`
- `tool_compare_stocks`
- `tool_get_market_movers`
- `tool_screen_stocks`
- `tool_search_stocks`
- `tool_get_news`

### 对应我们可做的工具
- `get_realtime_quote`
- `get_price_history`
- `search_symbol`
- `get_financial_statements`
- `get_dividends_splits`
- `get_analyst_forecasts`
- `compare_stocks`
- `get_market_movers`
- `screen_stocks`
- `get_company_news`
- `get_options_chain`

### 建议版本
- `V0.1`：美股 / 中国香港股票基础行情与历史
- `V0.3`：研究与上下文能力
- `V1.1`：movers / screener / 更完整研究型工具

### 是否免费
- **是**，适合做默认免费主链路的一部分

### 定位
- **默认免费主链路（美股 / 中国香港股票 / 全球市场基础层）**

### 风险 / 限制
- 本质是 Yahoo Finance 单源
- 不适合作为 A股主链路
- 新闻能力偏轻

---

## 7. topnews-1.0.1

### 借鉴来源
- 东方财富 API
- 新浪财经备用源
- 财联社 7×24 快讯
- 新浪 Feed 国际财经新闻
- akshare 北向资金（可选）
- collectors / report / scheduler / notifier 分层

### 对应我们可做的工具
- `get_market_news`
- `get_macro_news`
- `get_pre_market_briefing`
- `get_market_sentiment`（候选）
- `get_capital_flow_summary`（候选）

### 建议版本
- `V0.3`：市场新闻、宏观新闻、简版盘前简报
- `V1.1`：盘中 / 盘后智能简报增强、结构化新闻层

### 是否免费
- **大体免费可用**，可作为默认免费新闻主链路的重要参考

### 定位
- **默认免费新闻主链路参考 + 架构参考**

### 风险 / 限制
- 更像盘前简报项目，不是完整通用新闻 MCP
- 标的绑定、去重、情绪增强仍需补齐
- LLM 结论增强部分可能需要额外 Key

---

## 8. cnfinancialscraper-1.0.15

### 借鉴来源
- 公告爬取
- 研报爬取
- 新闻爬取
- PDF / Word / Excel 解析
- SQLite 索引
- 批量采集与断点续扫

### 对应我们可做的工具
- `get_company_announcements`
- `get_research_reports`
- `get_market_news`
- `get_company_news`
- `get_document_text`
- `get_fund_company_profile`

### 建议版本
- `V0.3`：轻量公告 / 新闻 / 研报入口
- `V1.1`：统一索引、结构化事件层、文档解析增强

### 是否免费
- **以公开站点抓取为主，可视为免费路线**

### 定位
- **免费增强 / 架构参考**

### 风险 / 限制
- 抓取稳定性与反爬要处理
- 更适合作为增强层，不建议一开始就压进主链路

---

## 9. tencent-news

### 借鉴来源
- CLI 封装方式
- 先读 help 再调用子命令
- 输出格式规范
- 错误处理
- 热点 / 快讯 / 分类新闻查询模式

### 对应我们可做的工具
- `get_market_news`（交互形态参考）
- `get_macro_news`（交互形态参考）
- `get_pre_market_briefing`（输出形式参考）

### 建议版本
- 不作为主版本的数据源直接承诺
- 作为 `V0.3` / `V1.1` 的设计参考与可选增强源

### 是否免费
- **否，需 API Key**

### 定位
- **设计参考 + 可选增强源**

### 风险 / 限制
- 需要 API Key
- 不适合作为默认零配置免费主源
- 更偏通用新闻，不够金融专用

---

## 10. stock-selecter-3.2.0

### 借鉴来源
- 多策略统一入口
- 评分机制
- 结果 schema
- 策略组合（AND / OR / SCORE）
- HTML 报告输出

### 对应我们可做的工具
- `screen_stocks`
- `rank_stocks`
- `compare_candidates`
- `get_strategy_signals`

### 建议版本
- `V0.3`：开始借鉴 schema
- `V1.1`：筛选 / 排名类研究工具

### 是否免费
- **不是数据源问题，偏设计参考**

### 定位
- **设计 / schema / 输出参考**

### 风险 / 限制
- 不是底层数据接口来源
- 不适合当前主线优先实现

---

## 11. stock-fundamental-analysis-v2-1.0.1

### 借鉴来源
- 基本面分析模板
- 风险框架
- 估值框架
- 输出结构

### 对应我们可做的工具
- `analyze_fundamentals`
- `compare_stocks`
- `build_investment_note`

### 建议版本
- `V0.3`：输出规范参考
- `V1.1`：研究型分析工具

### 是否免费
- **偏方法论，不是数据源**

### 定位
- **分析模板 / 输出结构参考**

### 风险 / 限制
- 不提供底层数据接口

---

## 12. 之前分析过的 GitHub 仓库

### `mcp-yfinance-server` / `yfinance-mcp` / `yahoo-finance-mcp`
- **用途**：美股 / 中国香港股票 / ETF / 基础研究能力参考
- **适合版本**：`V0.1`、`V0.3`
- **定位**：默认免费主链路参考

### `StockMCP`
- **用途**：AI 工具组织方式、查询接口设计
- **适合版本**：全局参考
- **定位**：设计参考

### `leek-fund`
- **用途**：中国市场免费公开接口路线
- **适合版本**：`V0.1`、`V0.2`
- **定位**：默认免费主链路参考

### `AkShare`
- **用途**：中国市场增强、基金 / ETF / 期货研究 / 宏观
- **适合版本**：`V0.2`、`V0.3`
- **定位**：免费增强 / fallback

---

## 三、当前最值得优先落地的来源

### 第一梯队：直接决定主链路
1. `a-stock-quote-1.9.0`
2. `yfinance-mcp-server-0.1.2`
3. `leek-fund`
4. `AkShare`

### 第二梯队：决定增强能力
5. `topnews-1.0.1`
6. `straightflush-1.0.0`
7. `tdx-pro-1.0.0`
8. `cnfinancialscraper-1.0.15`

### 第三梯队：决定研究层与交互层
9. `tencent-news`
10. `stock-selecter-3.2.0`
11. `stock-fundamental-analysis-v2-1.0.1`

---

## 四、当前可直接指导开发的结论

### 默认免费主链路
- 美股 / 中国香港股票：`yfinance` 系
- A股 / 中国市场特色能力：腾讯 / 新浪 / 东方财富 / `leek-fund` 路线
- 中国市场增强：`AkShare`

### 已确认可前移到主版本的
- 北向资金
- 龙虎榜
- 板块成分股
- 市场新闻
- 宏观新闻
- 简版盘前简报

### 继续放在 V1.1 的
- 标的级新闻绑定
- 去重聚合
- 情感打分
- 盘口 / 大单 / 竞价异动
- ETF 资金流
- 两融余额
- 市场宽度
- 结构化事件层
- 盘中 / 盘后智能简报增强
