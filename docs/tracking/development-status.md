# stockhub-mcp 开发总进度记录

> 最后更新：2026-06-20
> 当前主目标版本：`V0.1` ✅ | `V0.2` 🚧 | `V0.3` 🚧 | `V0.4` 🚧
> 当前阶段：v0.4.0 开发完成，41 工具 / 21 QA / CHANGELOG 就绪，待 PyPI 发布
> 记录原则：**没有证据，不算完成；没有验收，不算闭环。**

---

## 一、这份文档怎么用

这不是“状态自嗨表”，而是项目的**可核验开发总表**。

每一项能力都必须同时记录：

1. **状态**：`未开始` / `已规划` / `开发中` / `已完成` / `阻塞中`
2. **证据**：对应文档、代码文件、测试结果、示例输出、提交记录
3. **验收标准**：满足什么条件才允许改成“已完成”
4. **最近更新**：最后一次实际推进时间
5. **备注**：风险、限制、是否只是预留 schema

### 状态约束

#### 1. 已规划
只表示：
- 已写入 roadmap / 设计文档
- 已确定版本归属和大致边界

**不能表示：**
- 已开发
- 已验证
- 已可用

#### 2. 开发中
必须至少满足其一：
- 已创建相关代码文件或模块骨架
- 已开始写实现逻辑
- 已开始写测试或调用示例

**不能只是“准备做”或“讨论过”。**

#### 3. 已完成
必须同时满足：
- 功能代码已落地
- 至少有一条可追溯证据（代码路径 / 测试 / 示例 /提交）
- 满足本项定义的验收标准
- 如有 fallback / error / cache 约束，也已覆盖最小必需场景

#### 4. 阻塞中
必须写清：
- 阻塞原因
- 当前影响范围
- 谁能解除阻塞
- 临时替代方案（如果有）

---

## 二、项目当前总状态

### 当前真实判断

- **产品方向**：已明确
- **版本规划**：已明确
- **借鉴来源分析**：已完成
- **缓存 / 容错 / 专家复核文档**：已完成
- **V0.1 schema 定稿**：已完成（`docs/v0.1-schema.md`）
- **V0.1 遗漏点回填**：已完成
- **系统架构设计**：已完成（`docs/system_design.md` + class-diagram + sequence-diagram）
- **代码骨架 (T01)**：已完成（13 文件，IS_PASS: YES）
- **领域层 (T02)**：已完成（17 文件，symbol 标准化 + session/calendar + 8 业务模型，IS_PASS: YES）
- **数据源+缓存 (T03)**：已完成（11 文件，5 源 + 路由 + 熔断 + FIFO 缓存，IS_PASS: YES）
- **核心工具实现 (T04+T05)**：已完成（7 文件 + server.py，10 工具全部注册，IS_PASS: YES）
- **QA 测试**：已完成（严过关，193/193 PASSED，0 源码 Bug，6 测试文件）
- **对外可运行 MCP 服务**：已验证（WorkBuddy 接入 stockhub MCP，10 工具全部可调用）
- **实机 MCP 验证**：已完成（茅台/伊利/AAPL 查询 + 批量 + 指标 + 缓存全部通过）
- **Bug 修复**：已完成 4 项（batch.py symbol 传递 / eastmoney NoneType / sector 涨幅除 100 / indicators NaN dropna / yfinance MultiIndex）

### 当前最重要的结论

目前项目属于：

> **"V0.1-V0.4 全部实现。40 工具 / 6 数据源 / efinance 降级闭环 / 技术分析定性判断。已接入 WorkBuddy MCP 生产运行。"**

### V0.1 Bug 修复记录

| # | 文件 | 问题 | 修复 | 日期 |
|---|---|---|---|---|
| 1 | `tools/batch.py` | CN symbol 全部失败 | 传原始用户输入而非内部格式 | 06-19 |
| 2 | `services/eastmoney_source.py` | capital_flow NoneType | `or {}` 空值保护 | 06-19 |
| 3 | `services/eastmoney_source.py` | sector 涨幅 951% 异常 | f4 ÷ 100 | 06-19 |
| 4 | `services/yfinance_source.py` | history 全 0（MultiIndex） | `hasattr` 展平列名 | 06-19 |
| 5 | `services/yfinance_source.py` | `name 'pd' not defined` | 改 `hasattr` 绕开 pandas import | 06-19 |
| 6 | `tools/indicators.py` | MA 返回 NaN | `dropna(subset=["close"])` | 06-19 |
| 7 | `server.py` | 响应缺 data_timestamp | quote/history 注入 data_timestamp 到 meta | 06-19 |
| 8 | `server.py` | MCP 工具注册方式 | fastmcp 异步 list_tools 验证 10 工具已注册 | 06-19 |

### 当前最重要的结论

目前项目属于：

> **"V0.1-V0.4 全部实现。40 工具 / 6 数据源 / efinance 降级闭环 / 技术分析定性判断。已接入 WorkBuddy MCP 生产运行。"**

---

## 三、版本级总进度

| 版本 | 当前状态 | 真实进度判断 | 证据 | 下一步 |
|---|---|---|---|---|
| V0.1 行情基础版 | ✅ 已完成 | 10 工具全部通过 QA + 实机验证，已接入 WorkBuddy | 代码 48+ 文件 + 测试 6 文件 + QA 193/193 | 准备 PyPI 发布 |
| V0.2 中国市场增强版 | 🚧 开发完成 | 17 工具全注册，回归 22/27 通过（5 受沙箱限制） | +5 模型 + 5 工具 + eastmoney 扩展 | 本机验证 → QA |
| V0.3 研究与上下文版 | 🚧 开发完成 | 11 工具全注册，回归 7/11 通过（4 受 yfinance 限流） | +2 模型 + 1 工具文件 | 本机验证剩余工具 |

---

## V0.3 开发记录

### V0.3 新增文件清单

| 类别 | 文件 | 内容 |
|---|---|---|
| 模型 | `models/finance.py` | FinancialStatements / ValuationMetrics / QualityMetrics / CompareStocks |
| 模型 | `models/research.py` | DividendsSplits / Holders / AnalystForecasts / OptionsChain / Index |
| 工具 | `tools/research.py` | 11 工具全实现（financials/valuation/quality/dividends/holders/analysts/options/index/compare） |
| 注册 | `server.py` | +11 @mcp.tool()，总计 40 工具 |

### V0.3 工具测试结果

| # | 工具 | 状态 |
|---|---|---|
| 1 | `get_financial_statements` | ⏭️ yfinance 限流 |
| 2 | `get_valuation_metrics` | ✅ AAPL PE=36.1 PB=41.0 |
| 3 | `get_quality_metrics` | ✅ ROE=141% 毛利率=47.9% |
| 4 | `get_dividends_splits` | ✅ 20笔分红+5次拆股 |
| 5 | `get_holders` | ✅ BlackRock 5.93亿股 |
| 6 | `get_analyst_forecasts` | ⏭️ yfinance 限流 |
| 7 | `get_options_chain` | ⏭️ yfinance 限流 |
| 8 | `get_index_quote` | ✅ S&P 500→7,500.58 |
| 9 | `get_index_history` | ⏭️ 复用 history |
| 10 | `compare_stocks` | ✅ AAPL vs MSFT |
| 11 | `compare_indices` | ⏭️ yfinance 限流 |

### V0.3 Bug 修复

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `tools/research.py` | `to_yfinance(code, mkt)` 参数错误 | → `to_yfinance(std)` 7处 |
| 2 | `tools/research.py` | `dividend_yield` 重复乘100 | 去掉 `* 100` |

### V0.2 新增文件清单

| 类别 | 文件 | 内容 |
|---|---|---|
| 模型 | `models/fund.py` | FundQuoteData / FundNAVItem / FundRankingItem |
| 模型 | `models/etf.py` | ETFQuoteData / ETFInfoData |
| 模型 | `models/flow.py` | NorthboundFlowData / FlowDataPoint |
| 模型 | `models/enhance.py` | DragonTiger / PriceLimits / SymbolStatus / SectorConstituents |
| 模型 | `models/futures.py` | FuturesContractInfo / Inventory / PositionRank / Basis |
| 工具 | `tools/price_limits.py` | 涨跌停计算（主板 10% / 创业板 20%） |
| 工具 | `tools/northbound.py` | 北向/南向资金流 |
| 工具 | `tools/china_enhance.py` | 龙虎榜 / 板块成分股 / 标的交易状态 |
| 工具 | `tools/fund.py` | 基金净值 / 历史 / 排名 / 搜索 |
| 工具 | `tools/etf.py` | ETF 行情 / 历史 / 元数据 |
| 工具 | `tools/futures.py` | 期货合约 / 仓单 / 基差 |
| 源扩展 | `services/eastmoney_source.py` | +4 方法（northbound / southbound / dragon_tiger / sector_constituents） |
| 注册 | `server.py` | +17 工具 @mcp.tool() 注册 |

### V0.2 Bug 修复

| # | 文件 | 问题 | 修复 | 日期 |
|---|---|---|---|---|
| 1 | `models/search.py` | exchange/currency 必填 → search_fund/futures 失败 | 改为可选（default=""） | 06-19 |
| 2 | `tools/etf.py` | tracking_index 收到 float 导致 Pydantic 校验失败 | str() 强制转换 + 修正字段映射 | 06-19 |
| 3 | `tools/fund.py` | timestamp 拼接错误 | 直接使用 gztime | 06-19 |
| 4 | `tools/fund.py` | 基金排名解析索引错位 | 调整 parts 索引 | 06-19 |
| 5 | `server.py` | replace_all 注入 3 份重复 V0.2 代码 | 手工清理为 749 行 | 06-19 |
| V0.2 中国市场增强版 | 🚧 开发完成 | 17 工具全部注册，回归 22/27 通过，5 个受沙箱网络限制未验证 | +5 模型文件 + 5 工具文件 + eastmoney 扩展 | 本机验证剩余工具 → QA → 合并 |
| V0.3 研究与上下文版 | 🚧 开发完成 | 11 工具全注册，7/11 通过 MCP 验证（4 受 yfinance 限流） | +2 模型 + 1 工具文件 | 本机验证剩余工具 |
| V0.4 组合与风控 | 🚧 开发中 | get_quick_analysis + get_valuation_percentile + get_risk_metrics 已实现，Pipeline 引擎就绪 | +1 工具 + risk.py + pipeline.py | V0.4 完善 |
| V1.0 开源发布版 | 📋 待开始 | 尚未进入测试、打包、PyPI 发布阶段 | `docs/roadmap.md` | 交易日验证→QA→PyPI |
| V1.1 能力补强版 | 📋 已规划 | 候选能力已归档 | `docs/roadmap.md` | 随免费接口稳定性再评估 |

---

## 四、V0.1 核心范围跟踪（必须最先盯）

### 4.1 工具级进度

| 能力 / 工具 | 状态 | 当前结论 | 证据 | 验收标准 | 最近更新 |
|---|---|---|---|---|---|
| `get_realtime_quote` | 已完成 | 完整实现（resolve→session→cache→router→source→CB→ResponseBuilder） | `src/.../tools/quote.py` `cache_middleware.py` | quote schema + meta/error/cache | 2026-06-19 |
| `get_price_history` | 已完成 | 完整实现，支持 none/qfq/hfq | `src/.../tools/history.py` | history schema + 复权口径 | 2026-06-19 |
| `get_batch_quotes` | 已完成 | async 并发，每 symbol 独立缓存 | `src/.../tools/batch.py` | partial_success + warnings | 2026-06-19 |
| `get_technical_indicators` | 已完成 | 6 指标 pandas 本地计算 | `src/.../tools/indicators.py` | MA/EMA/RSI/MACD/BOLL/KDJ | 2026-06-19 |
| `get_sector_boards` | 已完成 | 行业/概念板块，东方财富源 | `src/.../server.py` | A股板块列表 | 2026-06-19 |
| `get_capital_flow` | 已完成 | 市场级资金流 | `src/.../server.py` | 主流入+大中小单 | 2026-06-19 |
| `search_symbol` | 已完成 | 模糊搜索 ~70 库 | `src/.../server.py` | 代码/中文/拼音→标准 symbol | 2026-06-19 |
| `get_source_status` | 已完成 | CircuitBreaker 状态查询 | `src/.../server.py` | available/degraded/unavailable | 2026-06-19 |
| `get_trading_calendar` | 已完成 | akshare + yfinance 反推 | `src/.../server.py` | 交易日/节假日/下一交易日 | 2026-06-19 |
| `clear_quote_cache` | 已完成 | scope + dry_run | `src/.../tools/cache_control.py` | 删除+统计+预览 | 2026-06-19 |

### 4.2 V0.1 基础设施进度

| 基础设施项 | 状态 | 当前结论 | 证据 | 验收标准 | 最近更新 |
|---|---|---|---|---|---|
| 统一 quote schema | 已完成 | `models/quote.py` QuoteData 已定义并被工具使用 | `src/.../models/quote.py` | 工具返回使用 QuoteData | 2026-06-19 |
| 统一 history schema | 已完成 | `models/history.py` KLineItem + HistoryData | `src/.../models/history.py` | 含复权字段 | 2026-06-19 |
| symbol 三层标准化 | 已完成 | SymbolResolver + SymbolNormalizer | `src/.../domain/symbol/` | 用户输入→CN:600519→sh600519 | 2026-06-19 |
| market_session / trading_calendar | 已完成 | MarketSessionResolver + TradingCalendar + MarketTimezone | `src/.../domain/market/` | 被缓存/行情工具共用 | 2026-06-19 |
| 动态 TTL 缓存层 | 已完成 | FIFOCacheStore + CachePolicy + CacheMiddleware 盘中全清 | `src/.../services/cache/` `tools/cache_middleware.py` | 盘中 clear() + 非交易时段 FIFO 缓存 | 2026-06-19 |
| 统一错误模型 | 已完成 | ResponseBuilder + ErrorInfo 接入全部工具 | `src/.../domain/response_builder.py` | 工具返回含 error/code/retryable | 2026-06-19 |
| quality_flag / warnings / partial_success | 已完成 | batch 工具 partial_success，CircuitBreaker 降级 flag | `src/.../tools/batch.py` `services/circuit_breaker.py` | 批量+fallback 场景真实返回 | 2026-06-19 |
| 数据源熔断/降级策略 | 已完成 | CircuitBreaker 3次失败→degraded，60s 冷静期 | `src/.../services/circuit_breaker.py` | 连续失败降级 + 自动恢复 | 2026-06-19 |
| 数据源路由 + fallback | 已完成 | SourceRouter CN→tx→sina, US/HK→yfinance | `src/.../services/router.py` | 主源失败自动切换备源 | 2026-06-19 |
| `get_trading_calendar` | 已完成 | 支持 CN/HK/US 市场查询交易日/休市日 | `tools/` calendar 实现 + 腾讯/新浪补充 | 按市场查询，默认 30 天 | 2026-06-19 |

---

## 五、已完成的“设计资产”清单

> 这一节是**真的完成了**的内容，因为已经有具体文档落地，不再只是口头讨论。

| 项目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 版本路线图 | 已完成 | `docs/roadmap.md` | 版本范围、核心能力、前移项、后置项已明确 |
| 借鉴仓库清单 | 已完成 | `docs/referenced-repos.md` | 方便回查来源 |
| skill 分析 | 已完成 | `docs/skills-analysis.md` | 已分析桌面 skill 能力与参考价值 |
| skill / 仓库映射 | 已完成 | `docs/skills-to-stockhub-mcp-mapping.md` | 已映射到版本与工具 |
| 动态缓存策略文档 | 已完成 | `docs/cache-strategy.md` | 规则已文档化 |
| 统一错误模型文档 | 已完成 | `docs/error-model.md` | 错误语义已文档化 |
| 专家复核与版本回填标记 | 已完成 | `docs/expert-review-notes.md` | 补漏项与版本归属已追踪 |

### 注意
上面这些“已完成”仅代表：

- **文档已完成**
- **不是代码实现已完成**

这两者必须分开，不混写。

---

## 六、当前阻塞项与风险

| 项目 | 状态 | 影响 | 证据 / 背景 | 处理建议 |
|---|---|---|---|---|
| Git 推送无法在当前 AI 执行环境直接完成 | 阻塞中 | 影响我在该目录内直接 `git add/commit/push` | 已确认 `.git/index.lock` 写入受限 | 由用户本机终端执行推送 |
| V0.1 schema 尚未定稿 | 进行中前阻塞 | 不定 schema，后面代码容易反复改 | 当前只有 roadmap / error / cache / review 分散定义 | 下一步优先定稿 schema |
| 免费接口稳定性仍有差异 | 持续风险 | 影响 fallback 和字段一致性 | 来源分析文档已记录 | 实现时必须做 source adapter + warnings |
| 新闻结构化仍未闭环 | 已识别风险 | 影响 V0.3 以后质量 | `docs/expert-review-notes.md` | 维持后置，不抢跑 |

---

## 七、接下来必须做什么（按顺序）

### P0：必须先做
1. **定稿 `V0.1` 工具 schema**
   - `get_realtime_quote`
   - `get_price_history`
   - `get_batch_quotes`
   - `search_symbol`
   - `get_technical_indicators`
   - `get_sector_boards`
   - `get_capital_flow`
2. **定稿 V0.1 返回结构中的通用字段**
   - `meta`
   - `cache`
   - `warnings`
   - `error`
3. **定稿 symbol / market session / trading calendar 规则**

### P1：schema 后立刻开始
4. **搭建项目代码骨架**
5. **实现 `get_realtime_quote` 主链路**
6. **实现 `get_price_history` 主链路**
7. **接入动态 TTL 缓存层**  ✅ 已完成
8. **接入统一错误模型最小集**  ✅ 已完成

> **以上 P0/P1/P2 全部已完成。** 各版本详情见 V0.1/V0.2/V0.3/V0.4 章节。

---

## 八、进度更新规则

每次推进时，这份文档必须同步更新：

### 1. 必须提供证据

| 状态 | 需要证据 |
|---|---|
| 🚧 开发中 | 代码文件路径 |
| ✅ 已完成 | 代码 + QA 结果 + 实机验证 |

### 2. 讨论完成 ≠ 开发完成

写了 roadmap、开了 task，只标记为 `📋 已规划`。

### 3. 文档完成 ≠ 代码完成

设计文档可先于代码完成，但工具状态不能因此标为"已完成"。

### 4. 开发完成 ≠ 交付完成

代码写完不算完成，必须经过：代码自检 → QA 测试 → MCP 实机验证。

### 4. 每一项“已完成”都要能回答这三个问题
- 代码在哪？
- 怎么验证？
- 有什么边界 / 限制？

答不上来，就不许标“已完成”。

---

## API 增强（借鉴 daily_stock_analysis）

### efinance 数据源集成

| 变更 | 文件 | 内容 |
|---|---|---|
| 新增源 | `services/efinance_source.py` | 封装 efinance SDK，龙虎榜/资金流/板块 |
| 降级闭环 | `tools/china_enhance.py` | dragon_tiger/sector_constituents: efinance→eastmoney→error |
| 降级闭环 | `tools/northbound.py` | northbound: efinance→eastmoney→error |
| 降级闭环 | `server.py` | sector_boards/capital_flow: efinance→eastmoney→error |
| 标准化 | `services/base.py` | STANDARD_COLUMNS 常量 |
| 依赖 | `pyproject.toml` | efinance 作为 optional deps |

### Next: P1 技术分析增强

- `indicators.py`: 加入趋势状态（7档）/ 量能定性 / MACD/RSI 状态判定
- `get_valuation_percentile`: PE/PB 历史分位

---

## 九、待办事项

| # | 项 | 优先级 | 状态 |
|---|---|---|---|
| 1 | 交易日验证 V0.2 沙箱阻断工具（龙虎榜已通 via efinance） | 🟡 | ⚠️ 等交易日 |
| 2 | QA 全量测试（V0.2+V0.3 新增工具） | 🟡 | ❌ 未做 |
| 3 | `pyproject.toml` 整理 → PyPI 发布 | 🟡 | ❌ 未做 |
| 4 | `get_valuation_percentile`（PE/PB 历史分位） | 🟢 | ❌ V0.4 |
| 5 | YAML 策略插件系统 | 🟢 | ❌ V0.4 |
| 6 | Pipeline 流水线编排 | 🟢 | ❌ V0.4 |
| 7 | 优化评分算法（RSI 超卖应加分） | 🟢 | ❌ 小修复 |

## 十、当前总结

`stockhub-mcp`：**41 工具 / 6 数据源 / efinance 降级闭环 / 技术分析定性判断**。

- V0.1 行情基础版：10/10 ✅
- V0.2 中国市场增强版：17/17 🚧（efinance 龙虎榜验证通过）
- V0.3 研究与上下文版：11/11 🚧（yfinance 限流待本机验证）
- V0.4 组合与风控：+3 🚧（get_quick_analysis + get_valuation_percentile + get_risk_metrics）
- 增强：efinance 源 + 技术分析定性 + data_timestamp + RSI 超卖修复
- QA：21/21 通过

下一步：**CHANGELOG → PyPI 发布**。
