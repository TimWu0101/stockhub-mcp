# market-data-mcp 路线图

## 一、产品目标

`market-data-mcp` 的目标是做一个面向 AI 的统一金融数据 MCP 服务器，覆盖：

- 美股
- A股
- 中国香港股票
- 公募基金与 ETF
- 期货
- 宏观与政策上下文

核心原则：

- 默认零配置可用，增强能力按需开启
- 优先使用免费公开数据源、开源接口与可复用抓取方案
- 付费数据源只作为可选增强，不作为主闭环前提
- 返回统一 schema，方便 AI 消费
- 采用适合开源维护的工程结构
- 优先做分层 fallback，不依赖单一脆弱数据源

## 二、数据源策略

### 1. 数据源优先级

按成本与开源可用性，统一采用以下优先级：

1. **免费公开 / 开源数据源**
   - `yfinance`
   - `AkShare`
   - 参考 `leek-fund` 的公开接口思路
   - 新浪财经 / 腾讯行情 / 东方财富 / 天天基金等公开可访问接口
2. **免费但稳定性一般的兜底源**
   - 社区维护的非官方封装
   - 网页抓取型补充源
   - `AkShare` 中部分更适合作为 fallback 的接口
3. **可选付费增强源**
   - `Tushare`
   - 后续可扩展的其他付费金融 API

### 2. 默认核心数据源

- 美股 / 中国香港股票：`yfinance`
- 中国市场免费源：参考 `leek-fund` 的公开接口思路
  - 新浪财经
  - 腾讯行情 / 搜索
  - 东方财富板块与资金流
- 本地计算层：`pandas` / `numpy`

### 3. 增强数据源

- `AkShare`：作为中国市场免费兜底与增强层
  - A股历史与基础资料
  - 公募基金与 ETF
  - 期货研究型数据
  - 宏观与政策数据
- `Tushare`：仅在用户主动配置 token 时作为 A 股增强源

### 4. 数据源角色定义

- 主数据源：默认请求优先命中的免费源
- 兜底数据源：主源失败或覆盖不足时启用的免费源
- 增强数据源：用于 richer 模块，不一定参与每次请求
- 付费增强源：仅在用户显式配置后参与请求，不影响默认可用性

### 5. 主版本收录规则

功能是否进入主闭环版本，统一按以下规则判断：

- **能靠免费接口稳定完成**：进入主版本
- **免费接口可做但稳定性一般**：进入主版本，但标记为 fallback / 实验性
- **免费接口难找或不稳定**：后置到 `V1.1`
- **只能依赖付费源**：不进入主闭环，只做可选增强

## 三、版本规划

## V0.1 - 行情基础版

### 目标

先交付一个最小可用闭环，让 AI 已经可以完成基础市场分析。

AI 至少要能：

- 查实时行情
- 查历史 K 线
- 算技术指标
- 看 A 股板块轮动和资金流
- 搜索股票代码 / 标的

### 范围

#### 核心工具

- `get_realtime_quote`
- `get_price_history`
- `get_batch_quotes`（至少预留 schema 与批量调用能力）
- `get_technical_indicators`
- `get_sector_boards`
- `get_capital_flow`
- `search_symbol`

#### 覆盖市场

- 美股
- A股
- 中国香港股票

#### 数据能力

- 实时行情
- 日 / 周 / 月历史数据
- 在数据源允许时提供基础分钟级支持
- 技术指标：`MA`、`EMA`、`RSI`、`MACD`
- A股板块列表
- A股板块资金流
- 标的搜索与市场自动路由
- 指数查询能力预留（后续独立增强为 `get_index_quote` / `get_index_history`）

#### 数据源安排

- 美股 / 中国香港行情与历史：`yfinance`
- A股实时行情：新浪 / 腾讯类公开接口
- A股历史：公开源主用，`AkShare` 作为免费 fallback
- 板块与资金流：东方财富类公开接口

#### V0.1 必带基础设施

- 统一 quote schema
- 统一 history schema
- `get_price_history` 明确支持 `none` / `qfq` / `hfq` 复权口径，并返回实际使用口径
- 市场识别与 symbol 标准化（用户输入层 / 内部标准层 / 数据源适配层）
- `market_timezone` / `market_session` / `trading_calendar` 基础模块
- 面向价格类查询的本地动态 TTL 缓存层（非交易时段优先缓存，关键交易时点禁用缓存）
- 主动清缓存能力（支持按 `symbol` / `market` / `tool` / `scope` 清除本地价格缓存）
- batch quote readiness（至少预留 schema 与错误模型）
- 返回结果附带元信息：
  - `source`
  - `currency`
  - `timezone`
  - `market`
  - `market_session`
  - `is_realtime`
  - `quality_flag`
- 数据源基础熔断/降级策略（基于连续失败次数的源暂时降级 + 冷静期恢复）
- `get_source_status` 源健康检查工具（返回每个源的 `available` / `degraded` / `unavailable`）
- `get_trading_calendar` 交易日历查询工具（对外暴露，不止内部使用）
- 批量调用超时策略
- 统一错误模型：
  - 标的不存在
  - 数据源超时
  - 市场暂不支持
  - `partial_success` / `warnings` / `retryable`

### V0.1 不做

- 完整基金模块
- 完整期货模块
- 财务报表与估值
- 新闻聚合
- 宏观日历
- 组合分析
- 高级风险提示
- 任何必须依赖付费 API 才能成立的能力

## V0.2 - 中国市场增强版

### 目标

把项目从“基础行情服务器”升级成更强的中国市场研究工具。

### 范围

#### 公募基金与 ETF

- `get_fund_quote`
- `get_fund_nav_history`
- `get_fund_rankings`
- `search_fund`
- `get_etf_quote`
- `get_etf_history`
- `get_etf_info`（跟踪指数 / 行业主题等交易视角增强）

#### 中国市场增强能力（根据新发现的免费接口前移）

- `get_northbound_flow`
- `get_southbound_flow`
- `get_dragon_tiger_list`
- `get_sector_constituents`
- `get_price_limits`（A股涨跌停价格计算）
- `get_symbol_status`（停牌/退市/正常交易状态查询）
- 行业板块与概念板块区分
- `get_symbol_themes`（预留）

#### 期货研究层

- `search_futures_contract`
- `get_futures_contract_info`
- `get_futures_inventory_history`
- `get_futures_warehouse_receipt`
- `get_futures_position_rank`
- `get_futures_basis_history`

#### 数据源安排

- 基金 / ETF：优先 `AkShare` 与公开网页接口
- 期货研究数据：优先 `AkShare`
- A股增强：继续免费公开接口优先，`Tushare` 仅作可选增强
- 现有免费公开接口在更稳定更简单时继续作为主源

### V0.2 不做

- 完整基本面
- 宏观事件层
- 结构化新闻
- 组合分析
- 不强行承诺 ETF 资金流、两融余额、市场宽度等仍需进一步验证稳定免费接口的能力

## V0.3 - 研究与上下文版

### 目标

把项目从行情 MCP 升级成“研究助手后端”。

### 范围

#### 基本面与估值

- `get_financial_statements`
- `get_valuation_metrics`
- `get_valuation_percentile`（PE/PB 等指标的历史分位）
- `get_quality_metrics`
- `compare_stocks`
- `get_dividends_splits`
- `get_holders`
- `get_analyst_forecasts`
- `get_options_chain`（美股期权链）
- `get_index_quote`
- `get_index_history`
- `compare_indices`

#### 新闻与事件上下文

##### 市场级新闻
- `get_market_news`
- `get_macro_news`
- `get_pre_market_briefing`

##### 标的级新闻
- `get_company_news`

##### 宏观与事件工具
- `get_macro_calendar`
- `get_policy_rate_events`
- `get_credit_impulse_data`

#### 宏观与政策支持

优先用 `AkShare` 宏观模块承接：

- GDP
- CPI / PPI
- PMI / 财新 PMI
- 出口 / 进口 / 贸易帐
- M2
- LPR
- 存款准备金率
- 社融
- 新增信贷
- 失业率
- 房价指数
- 消费者信心 / 企业景气

### 免费优先约束

- 美股 / 中国香港基本面优先使用 `yfinance`
- 中国市场基本面能用免费源先用免费源
- `get_market_news` / `get_macro_news` / `get_pre_market_briefing` 优先参考 `topnews-1.0.1`、`tencent-news`、`cnfinancialscraper` 与公开新闻源组合实现
- `get_company_news` 先做轻量版，优先返回基础新闻列表，标的关联增强、去重聚合、情绪打分后置
- 若某类事件或新闻无法稳定免费获取，可缩减范围或后置到 `V1.1`
- 不因为付费接口可用就把默认行为绑定到付费链路

## V0.4 - 组合与风控版

### 目标

加入组合视角和风险视角，让它更像真正的投资研究助手。

### 范围

- `analyze_portfolio_exposure`
- `analyze_portfolio_risk`
- `get_correlation_matrix`
- `get_drawdown_stats`
- `get_risk_alerts`

潜在指标：

- 集中度
- 行业暴露
- 市值风格暴露
- 波动率
- beta
- 最大回撤
- 相关性聚类

### 免费优先约束

这一版尽量基于前面版本已沉淀的免费历史数据和本地计算完成，不新增必须依赖付费 API 的核心逻辑。

## V1.0 - 开源发布版

### 目标

把项目打磨到适合外部用户安装、使用、提 issue 和扩展的状态。

### 范围

#### 工程化

- 稳定的工具 schema 定义
- 文档化的返回结构约定
- 数据源优先级配置系统
- 缓存与超时策略
- 日志
- 测试与 fixtures
- 数据源健康度与 caveat 说明

#### 文档

- 完整 README
- 安装说明
- MCP 客户端配置示例
- roadmap 与 source policy
- contributor notes
- 数据源免责声明

#### 发布准备

- 语义化版本
- changelog
- release notes
- issue templates
- LICENSE

## V1.1 - 能力补强版

### 目标

在主功能已经形成闭环之后，单独迭代那些“很有价值、但依赖是否能找到稳定免费接口”的增强能力。

这一版不强求一次做完，而是按数据源可得性逐步纳入。

### 本轮评估后已前移到主版本的能力

基于近期补充分析的 `a-stock-quote`、`straightflush`、`tdx` 系、`yfinance-mcp-server` 等能力，以下项目已不再后置到 `V1.1`：

- 北向资金：前移到 `V0.2`
- 龙虎榜：前移到 `V0.2`
- 板块成分股：前移到 `V0.2`

### 已缩小不确定性、可优先验证的下一批能力

以下能力虽然暂未正式前移，但已经具备较强候选性，可在验证免费接口稳定性后优先插入主版本：

- IPO 日历 / 待发队列
- 公司行动（分红、拆股等）
- 分钟级增强数据（盘口、大单、竞价异动）

### 适合放到 V1.1 的能力

> 注：`V1.1` 继续承接高价值但免费接口稳定性、结构化程度或工程复杂度更高的能力；复权口径、交易日历 / 市场时段、错误模型最小集合、ETF 交易视角、板块成分股与新闻分层等基础优化项，已分别前移到 `V0.1`、`V0.2`、`V0.3`。

#### 1. 事件驱动层

- 财报日历
- 分红 / 除权除息日历
- 停复牌 / 重要公告
- 宏观事件日历
- 业绩预告 / 解禁 / 回购 / 减持
- IPO 日历与待发队列

#### 2. 估值与质量指标增强层

- 更完整的 PE / PB / PS
- ROE / ROIC
- 毛利率 / 净利率
- 营收增速 / 利润增速
- 现金流质量
- 股息率

#### 3. 中国市场增强流向层

以下能力已具备候选性，但免费接口稳定性仍需继续验证：

- 个股主力资金流
- ETF 资金流
- 两融余额
- 市场宽度（涨跌家数 / 新高新低）
- 做空数据 / 沽空比率

#### 4. 新闻结构化层

- 按标的聚合
- 时间排序
- 去重
- 分类（财报 / 政策 / 并购 / 评级 / 产品）
- 结构化摘要字段
- 盘中 / 盘后智能简报增强

#### 5. 数据质量增强层

- 前复权 / 后复权 / 不复权
- 时区标准化
- 交易日历
- 停牌识别
- 盘前 / 盘后 / 午休状态
- 数据延迟与质量标记

#### 6. 轻量风险提示层

- 财报前提示
- 高波动提示
- 低流动性提示
- 数据时效提示

#### 7. 品种扩展候选

- `get_convertible_bond_info`（可转债，中国市场重要品种）
- IPO 申购信息

### 为什么单独放 V1.1

因为这一批能力的共同特点是：

- 很有价值
- 但不一定能稳定找到免费接口
- 很适合在主闭环完成后按接口可得性逐步增强

这样可以避免主 roadmap 被高不确定性接口拖慢。

## 四、能力与数据源映射建议

| 能力 | 优先数据源 | 次级 / 增强 |
|---|---|---|
| 美股行情 / 历史 | `yfinance` | 后续可加其他免费或高级源 |
| 中国香港行情 / 历史 | 腾讯 / `yfinance` | `AkShare` 视情况补充 |
| A股实时行情 | 新浪 / 腾讯公开接口 | `Tushare` |
| A股历史 | 公开源 | `AkShare`、`Tushare` |
| A股板块 / 资金流 | 东方财富类接口 | `AkShare` 视情况补充 |
| 公募基金 / ETF | `AkShare` / 东方财富公开接口 | `Tushare` |
| 期货研究数据 | `AkShare` | 后续其他公开源 |
| 基本面 | 美股/中国香港先用 `yfinance`，中国市场后补 | `Tushare`、`AkShare` |
| 宏观 / 政策 | `AkShare` | 后续补官方或其他公开源 |

## 五、分阶段开发顺序建议

### Phase A

- schema 定义
- 路由与 symbol 标准化
- `get_realtime_quote`
- `get_price_history`

### Phase B

- `get_technical_indicators`
- `get_sector_boards`
- `get_capital_flow`
- `search_symbol`

### Phase C

- 基金 / ETF
- 期货研究工具
- 中国市场增强源

### Phase D

- 基本面
- 宏观与政策层
- 新闻层

### Phase E

- 组合分析
- 风险层
- 发布打磨

### Phase F

- V1.1 能力补强项按免费接口可得性逐步接入
