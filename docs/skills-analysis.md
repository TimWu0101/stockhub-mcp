# mcp开发辅助 / skills 分析结论

本文整理桌面 `mcp开发辅助/skills` 中与 `market-data-mcp` 相关、可直接借鉴或可作为后续增强能力参考的 skill / 接口。

## 一、先给结论

这批 skill 里，**最值得我们借鉴的不是“完整照搬某个 skill”**，而是把它们拆成三类参考资产：

1. **A股免费行情与中国市场特色能力**
   - `a-stock-quote-1.9.0`
   - `straightflush-1.0.0`
   - `tdx-1.0.0`
   - `tdx-pro-1.0.0`
   - `tdxuse-1.0.0`

2. **新闻、快讯、舆情与事件层**
   - `cnfinancialscraper-1.0.15`
   - `topnews-1.0.1`
   - `tencent-news`

3. **研究层 / 分析层 / 结果输出层**
   - `stock-fundamental-analysis-v2-1.0.1`
   - `stock-selecter-3.2.0`

如果按对 `market-data-mcp` 的帮助大小排序，我建议优先关注：

1. `a-stock-quote-1.9.0`
2. `straightflush-1.0.0`
3. `cnfinancialscraper-1.0.15`
4. `topnews-1.0.1`
5. `tdx-pro-1.0.0` / `tdx-1.0.0`
6. `stock-selecter-3.2.0`

---

## 二、逐个看哪些接口/能力值得借鉴

## 1. a-stock-quote-1.9.0

**这是当前最贴近我们 V0.1 / V1.1 需求的 skill。**

### 可直接借鉴的接口与来源
- **腾讯财经实时行情 API**：`qt.gtimg.cn`
- **新浪财经备用行情 API**：`hq.sinajs.cn`
- **腾讯分时 API**：`ifzq.gtimg.cn`
- **腾讯 K 线 API**：`web.ifzq.gtimg.cn`
- **东方财富资金流接口**
- **东方财富北向资金接口**
- **东方财富板块排名 / 龙虎榜接口**

### 对我们最有价值的点
- 已经验证了一条 **“免费 + 无 API Key 的 A 股主链路”**
- 覆盖了我们 V0.1 很多核心能力：
  - 实时行情
  - 指数查询
  - 1 分钟分时
  - MA 均线
  - 个股资金流
  - 北向资金
  - 行业板块涨跌幅
  - 龙虎榜
- skill 里已经明确了 **主源 + 备用源** 思路：
  - 腾讯主源
  - 新浪备用
  - 东方财富承接扩展数据

### 对 `market-data-mcp` 的借鉴建议
- 可直接作为 **A 股 V0.1 数据源路由设计样板**
- 可把下面这些能力纳入：
  - `get_realtime_quote`
  - `get_price_history`
  - `get_intraday_minutes`
  - `get_capital_flow`
  - `get_northbound_flow`
  - `get_sector_boards`
  - `get_dragon_tiger_list`
- 它还给了我们一个重要启发：
  **中国市场很多特色能力不需要先上付费源，免费公开接口已经能先做出来。**

---

## 2. straightflush-1.0.0

这是基于 `thsdk` 的能力包，**更适合做 V1.1 或增强层参考**。

### 可借鉴的接口能力
- `search_symbols`
- `klines`
- `intraday_data`
- `min_snapshot`
- `depth`
- `big_order_flow`
- `call_auction_anomaly`
- `ths_industry`
- `ths_concept`
- `market_data_block`
- `block_constituents`
- `market_data_index`
- `market_data_cn`
- `market_data_hk`
- `market_data_us`
- `market_data_future`
- `news`
- `corporate_action`
- `ipo_today` / `ipo_wait`

### 最大价值
- 它把 **A股 / 港股 / 美股 / 期货 / 板块 / 资讯** 放在一个统一 SDK 里
- 有比较完整的：
  - symbol 搜索/解析
  - 多市场行情
  - 分时、盘口、大单
  - 行业/概念板块
  - 资讯快讯
  - 公司行动（分红、送转等）

### 对我们最有帮助的部分
- **symbol 标准化 / 搜索流程** 很值得借鉴
- **分钟线、盘口、大单流向、竞价异动** 是我们后续增强层的重要候选
- **公司行动 / IPO / 资讯** 对 V1.1 很有价值

### 注意点
- 这类 SDK 的稳定性、授权边界、平台依赖要单独评估
- 不建议直接把它当默认主链路
- 更适合作为：
  - 增强源
  - 替代源
  - 研究型能力源

---

## 3. cnfinancialscraper-1.0.15

这个 skill **不是行情源**，但它对“研究层”“新闻层”“公告层”价值很大。

### 可借鉴的接口/模块
- `stock_list_updater.py`：A股全量上市公司名单 + 行情快照
- `announcement_scraper.py`：公告搜索、PDF 下载
- `company_report_scraper.py`：上市公司定期报告
- `research_report_scraper.py`：券商研报（评级/目标价/分析师）
- `news_scraper.py`：新闻资讯爬取
- `comprehensive_report_scraper.py`：统一入口
- `report_indexer.py`：SQLite + 断点续扫
- `document_parser.py`：PDF/Word/Excel 解析
- `scrapable_registry.py`：可爬取机构注册表
- `web_parser.py`：基金/ETF/FOF/股票/债券页面解析

### 数据来源
- 东方财富
- 巨潮资讯
- 同花顺
- 天天基金
- 各基金公司官网
- 监管机构与行业协会站点

### 对我们的价值
它非常适合作为后续这些模块的参考：
- `get_company_announcements`
- `get_research_reports`
- `get_fund_company_profile`
- `get_market_news`
- `get_company_news`
- `get_document_text`

### 最值得借鉴的不是某个接口，而是架构
- 爬虫分层
- 机构注册表
- 文档下载与解析
- 批量爬取
- SQLite 索引
- 断点续扫
- 动态页面 / 反爬应对

这对我们以后做 **新闻与事件层、公告层、研究资料层** 很有帮助。

---

## 4. topnews-1.0.1

### 价值定位
更适合借鉴 **新闻采集与分析处理链路**，不是直接当金融数据主源。

### 值得借鉴的点
- collectors 分层
- 多源抓取
- 并发采集
- fallback
- 情感分析
- 重要性评分
- 板块 / 主题映射
- 报告生成
- 调度与通知器分层

### 对我们的帮助
如果以后做：
- `get_market_news`
- `get_company_news`
- `get_macro_news`
- `get_pre_market_briefing`
- `get_event_summary`

那它的整体处理链路很值得借鉴。

---

## 5. tencent-news

### 价值定位
它更像 **新闻搜索入口模板**。

### 值得借鉴的点
- CLI 封装方式
- 先读 help 再调用子命令的设计
- 统一错误处理
- 输出格式规范
- 热点 / 快讯 / 分类新闻获取方式

### 对我们的帮助
- 可借鉴 `get_market_news` 的交互形态
- 可参考“脚本层处理基础设施，业务层只选子命令和参数”的设计思想

### 限制
- 偏通用新闻，不够金融专用
- 缺少标的关联、行情联动、事件结构化

---

## 6. tdx-1.0.0

### 价值定位
偏 **通达信数据接入封装**，适合作为中国市场数据备源参考。

### 可借鉴能力
- 实时行情
- 历史 K 线
- 指数行情
- 分钟数据
- 财务报表解析
- 本地通达信数据读取

### 对我们的帮助
- 适合作为 **A 股 / 指数 / 期货** 的一个备选源研究
- “自动优选服务器 + 重试 + 友好错误提示”值得借鉴
- 财务数据解析思路对 V0.3 以后有帮助

### 限制
- 对环境和依赖要求更重
- 更适合增强源或研究用途，不适合作为零配置默认主源

---

## 7. tdx-pro-1.0.0

### 价值定位
这是更完整的 `pytdx` API 参考层。

### 值得借鉴的接口方向
- `get_realtime_quote`
- `get_batch_quotes`
- `get_kline_data`
- `get_index_kline_data`
- `get_minute_time_data`
- `get_security_list`
- `get_finance_info`
- `get_block_info`

### 对我们的帮助
- 适合补强 **板块信息、财务信息、批量行情**
- 可借鉴 **连接模式**：短连接 / 长连接 / 连接池 / 自适应
- 可借鉴 **自动服务器选择与故障切换策略**

### 限制
- 和 `tdx-1.0.0` 一样，更像技术备源，不适合直接当开源项目默认主链路

---

## 8. tdxuse-1.0.0

### 价值定位
这个更偏 **TQ 量化终端能力集合**，很强，但离我们当前主线稍远。

### 有价值的能力
- 市场行情 / 快照
- 财务字段查询
- 板块列表 / 板块成分股
- 市场交易数据
- IPO 数据
- 分红因子 / 股本信息
- ETF 跟踪指数信息
- 可转债信息
- 自定义板块管理
- 实时订阅

### 对我们的帮助
后续如果我们要做 V1.1 / V0.3+ 的扩展，可重点借鉴：
- `get_dividends_splits`
- `get_ipo_info`
- `get_etf_info`
- `get_convertible_bond_info`
- `get_sector_constituents`

### 限制
- 和终端生态耦合较深
- 不适合作为默认对外开源免费方案的第一层实现

---

## 9. stock-selecter-3.2.0

### 价值定位
这不是数据源 skill，而是 **策略层 / 分析层**。

### 可借鉴内容
- 多策略统一入口设计
- 结果 schema 设计
- 评分机制
- 多策略组合：AND / OR / SCORE
- HTML 报告输出
- 每个策略的参数命名方式
- `metadata` 返回结构

### 对我们的帮助
后续如果 `market-data-mcp` 想做研究型工具或筛选类工具，这个很有参考价值：
- `screen_stocks`
- `rank_stocks`
- `compare_candidates`
- `get_strategy_signals`

### 当前结论
先借鉴 **返回结构和组合方式**，不要把它放进 V0.1 主线。

---

## 10. stock-fundamental-analysis-v2-1.0.1

### 价值定位
这是 **分析方法论模板**，不是接口源。

### 可借鉴内容
- 基本面分析流程
- 事实 / 假设 / 观点分离
- 分析模板
- 风险框架
- 估值框架
- 输出结构

### 对我们的帮助
适合作为未来研究层工具的输出规范参考，比如：
- `analyze_fundamentals`
- `compare_stocks`
- `build_investment_note`

---

## 11. yfinance-mcp-server-0.1.2

### 价值定位
这是一个比较完整的 **Yahoo Finance 单源 MCP Server**，更适合我们借鉴 **工具分层方式、参数设计和研究层工具清单**。

### 可借鉴的工具
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

### 对我们的帮助
- 适合作为 **美股 / 中国香港股票 / 全球市场基础层** 的 MCP 工具设计参考
- `period` / `interval` / `statement_type` / `quarterly` / `max_results` 等参数设计较成熟，适合借鉴到我们的 schema
- 对 `V0.3` 研究与上下文版很有帮助，尤其是：
  - `get_financial_statements`
  - `compare_stocks`
  - `get_dividends_splits`
  - `get_analyst_forecasts`
  - `get_company_news`
  - `screen_stocks`
- 它再次证明：**yfinance 非常适合作为美股与中国香港股票的默认免费基础层**

### 局限
- 本质仍然是 Yahoo Finance / `yfinance` 单源，不适合作为 A股主链路
- 对中国市场特色能力（板块、资金流、北向、龙虎榜、公告、研报）帮助有限
- 新闻能力偏轻，只适合基础新闻列表，不适合作为结构化事件层的直接方案

---

## 三、对 market-data-mcp 最有帮助的“可借鉴接口清单”

## A. V0.1 就能考虑吸收的

### A股 / 指数 / 历史 / 分时
- 腾讯财经实时行情 API
- 新浪财经备用行情 API
- 腾讯分时 API
- 腾讯 K 线 API
- 东方财富板块排名
- 东方财富资金流
- 东方财富北向资金

### 适合映射到我们的工具
- `get_realtime_quote`
- `get_price_history`
- `search_symbol`
- `get_intraday_minutes`
- `get_capital_flow`
- `get_sector_boards`

---

## B. V0.2 / V0.3 可考虑补的
- 东方财富龙虎榜
- 通达信 / pytdx 财务数据
- 通达信板块信息
- ETF / 可转债 / IPO / 分红因子
- 机构名单 / 上市公司名单 / 基金公司名单
- 公告 / 研报爬取

---

## C. V1.1 最值得做的增强层
- 新闻搜索 + 财经快讯
- 新闻情感分析
- 事件结构化
- 板块 / 主题映射
- 大单流向 / 盘口深度 / 集合竞价异动
- 公司行动（分红、拆股、IPO）
- 研究报告 / 公告统一索引

---

## 四、我建议你怎么用这些参考

## 优先级建议

### 第一梯队：直接影响当前主线
1. `a-stock-quote-1.9.0`
2. `straightflush-1.0.0`
3. `tdx-pro-1.0.0`

### 第二梯队：增强层与研究层
4. `cnfinancialscraper-1.0.15`
5. `topnews-1.0.1`
6. `tencent-news`

### 第三梯队：输出与策略设计参考
7. `stock-selecter-3.2.0`
8. `stock-fundamental-analysis-v2-1.0.1`

---

## 五、最终判断

如果只回答一句：

**有，而且不少。**

但最值得我们拿来用的不是“某一个完整 skill”，而是：

- 从 `a-stock-quote` 拿 **A股免费主链路接口组合**
- 从 `straightflush` / `tdx` 系拿 **多市场增强与研究型接口思路**
- 从 `cnfinancialscraper` / `topnews` / `tencent-news` 拿 **新闻、公告、研报与事件层架构**
- 从 `stock-selecter` 拿 **统一 schema、评分、组合策略的设计方式**

如果继续推进，我建议下一步补一份：

`docs/skills-to-market-data-mcp-mapping.md`

把这些 skill 逐个映射成：
- 可借鉴的数据源
- 可借鉴的工具名
- 适合进入哪个版本（V0.1 / V0.2 / V0.3 / V1.1）
- 风险与限制
