# stockhub-mcp 当前已完成功能总结

> 一句话概览：`stockhub-mcp` 当前已交付一个可直接运行的金融数据 MCP 服务，覆盖 43 个工具，面向 A 股 / 港股 / 美股 / 基金 / ETF / 期货 / 指数 / 研究分析 / 组合风险场景，默认走免费公开数据源并提供统一响应结构。
> 文档定位：**这份文档只回答“当前已经能做什么”；待开发、风险与维护口径请看 `development-status.md`，统一导航请回到 `docs/INDEX.md`。**

---

## 当前版本 / 当前状态

- **当前发布口径**：PyPI `v0.4.0`
- **当前能力规模**：43 个 MCP 工具
- **当前数据源实现**：`efinance`、东方财富、腾讯、新浪、`yfinance`、`AkShare`
- **当前运行形态**：FastMCP 服务，入口为 `src/stockhub_mcp/server.py`
- **当前工程状态**：不是原型骨架，核心工具、领域层、响应模型、路由、缓存、降级都已落代码

这份文档只回答“**现在已经能做什么**”和“**当前版本到哪里为止**”。
如果要看待开发事项、维护规则、风险与少量历史边界，请看 `development-status.md`。

---

## 已完成功能分组摘要

### 1. 行情与历史查询

已完成统一的基础行情能力，覆盖单标的、批量、历史 K 线和交易日信息：

- `get_realtime_quote`：单标的实时报价
- `get_batch_quotes`：批量报价（适合 AI 一次性比较多只标的）
- `get_price_history`：历史 K 线，支持多周期与复权口径
- `get_trading_calendar`：按市场查询交易日、假期、下一交易日
- `get_source_status`：查看数据源健康状态
- `clear_quote_cache`：清理本地价格缓存

这一组能力的底层已经形成统一基础设施：

- Symbol 解析与标准化
- Market session / timezone / trading calendar
- 本地缓存与 cache 清理
- 数据源路由与 fallback
- 统一 `meta / error / warnings / quality_flag` 响应结构

### 2. 技术分析与一键分析

已完成本地技术指标计算与组合式快速分析：

- `get_technical_indicators`：MA / EMA / RSI / MACD / BOLL / KDJ
- `get_quick_analysis`：行情 + 技术指标 + 趋势/信号的一键组合分析

当前特点：

- 指标计算主要在本地完成，不依赖外部分析服务
- 返回不只是原始数值，还包含趋势、量能、信号等定性结果
- 已经作为独立工具能力交付，不是仅供内部调用的辅助模块

### 3. A 股增强能力

已完成一组偏 A 股场景的增强工具：

- `get_sector_boards`：行业 / 概念板块榜单
- `get_capital_flow`：市场或板块资金流
- `get_northbound_flow` / `get_southbound_flow`：北向 / 南向资金
- `get_dragon_tiger_list`：龙虎榜
- `get_sector_constituents`：板块成分股
- `get_price_limits`：涨跌停价格计算
- `get_symbol_status`：停牌 / 退市 / 正常状态查询

当前实现特点：

- A 股增强能力优先利用 `efinance` / 东方财富等免费源
- 多个工具已经写了显式 fallback，而不是单源强绑定
- 这部分是当前版本的正式交付内容，不是规划中的增强项

### 4. 基金、ETF、期货

已完成中国市场常见的基金 / ETF / 期货查询能力：

- 基金：`get_fund_quote`、`get_fund_nav_history`、`get_fund_rankings`、`search_fund`
- ETF：`get_etf_quote`、`get_etf_history`、`get_etf_info`
- 期货：`search_futures_contract`、`get_futures_contract_info`、`get_futures_position_rank`、`get_futures_basis_history`

这一组说明当前版本不只覆盖“股票行情”，而是已经扩到常见投研上下文需要的多资产查询。

### 5. 研究、估值与对比分析

已完成围绕个股研究的估值、财务和横向对比工具：

- `get_financial_statements`
- `get_valuation_metrics`
- `get_quality_metrics`
- `get_valuation_percentile`
- `get_dividends_splits`
- `get_holders`
- `compare_stocks`
- `search_symbol`

此外还包含偏美股研究场景的：

- `get_analyst_forecasts`
- `get_options_chain`

当前可以认为：

- “基础行情”与“研究查询”已经是两层完整能力
- 支持跨市场统一查询，但不同工具的真实可用性仍受底层免费源覆盖差异影响

### 6. 指数与组合风险

已完成指数工具和组合层风控工具：

- 指数：`get_index_quote`、`get_index_history`、`compare_indices`
- 风险：`get_risk_metrics`
- 组合：`get_correlation_matrix`、`analyze_portfolio_exposure`

当前特点：

- 风险指标与相关性分析主要走本地计算
- 已支持从“单标的查询”扩展到“多标的组合诊断”
- 这部分已是当前发布集的一部分，不需要等待后续版本才可用

---

## 共用枚举与领域约定

`src/stockhub_mcp/enums.py` 是当前领域枚举的唯一真源；文档这里只说明“分组与作用范围”，不重复维护完整取值表，避免与实现双重漂移。

当前已沉淀的关键枚举可按能力层理解为：

- **市场与标的识别**：`Market`、`InstrumentType`，用于 market 归类、symbol 解析、工具入参与响应元信息对齐
- **交易时段判断**：`MarketSession`，服务于交易日历、盘中/盘后判断、缓存策略和实时性说明
- **数据源路由**：`DataSource`（含 `yfinance`、`tx`、`sina`、`eastmoney`、`akshare`、`tushare`、`computed`），服务于 source adapter、fallback、`meta.source` 与源状态观测
- **历史价格口径**：`AdjustType`，用于历史 K 线查询与技术指标依赖的复权语义
- **数据质量标记**：`QualityFlag`，用于 freshness/fallback 表达，以及缓存写入与 warning 判定
- **错误分类**：`ErrorType`，用于统一错误模型顶层分层，不替代具体 error code
- **源健康状态**：`SourceStatus`，用于 `get_source_status` 以及数据源降级/不可用表达
- **缓存清理作用域**：`CacheScope`，用于 `clear_quote_cache` 的清理粒度约束

维护建议：后续新增工具或字段时，优先复用这些共用枚举；如果语义需要扩展，应先修改 `enums.py`，再同步更新引用文档中的说明文字，而不是反过来在文档里先发明新值。

若要查具体值与响应字段映射：

- 代码真源：`src/stockhub_mcp/enums.py`
- 响应字段与枚举速查：`docs/design/schema-reference.md`

---

## 当前版本边界

以下内容**不应被视为当前已交付能力**：

- **新闻 / 宏观 / 政策解读闭环**：仓库里没有形成当前可交付的新闻型工具集
- **付费数据源依赖的主流程**：当前默认闭环仍以免费公开数据源为主，不要求用户配置付费 token
- **完全稳定一致的全市场深度数据**：不同市场 / 工具仍受免费源本身稳定性、字段完整性、限流情况影响
- **无限制分钟级 / 高频数据平台**：当前重点仍是 AI 可消费的统一查询与分析，不是专业高频终端
- **账户、交易、下单、持仓同步**：当前项目是数据与分析 MCP，不是交易执行系统
- **所有 roadmap 条目均已实现**：路线图中仍有后续增强项，不能把 roadmap 直接等同于当前能力

---

## 对后续迭代最有价值的上下文

- **先看能力，再看规划**：当前已交付能力以本文件和 `server.py` 已注册工具为准
- **优先保护统一中间层**：后续迭代应继续复用 symbol、market、response、router、circuit breaker、cache 等共用层
- **不要假设所有工具共用同一套 fallback**：A 股增强、港美股、期货、交易日等场景的真实 source adapter 并不完全相同
- **主要风险在上游免费源波动**：后续更有价值的工作通常是补充验证、增强容错、澄清边界，而不是重写架构

## 后续阅读入口

- **看当前已完成能力**：`docs/tracking/current-capabilities.md`
- **看待开发、规则、风险**：`docs/tracking/development-status.md`
- **看版本规划**：`docs/tracking/roadmap.md`
- **看工具全量列表**：`docs/TOOLS.md`
- **看架构与设计**：`docs/design/system_design.md`
