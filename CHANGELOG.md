# CHANGELOG

## v0.4.1 (2025-06-21)

### 文档收敛

- 收敛文档导航与总览入口，补充 `archive/`、`design/`、`tracking/` 目录说明
- 修订安装与启动说明，强化 PyPI 安装路径和 MCP 配置指引
- 整理历史资料归档与当前能力说明，保持 patch 级文档发布范围

## v0.4.0 (2025-06-20)

### 新功能

- `get_risk_metrics`：波动率、最大回撤、夏普比率、VaR(95%)、Beta（纯本地计算）
- `get_correlation_matrix`：多标的相关系数矩阵（2-10 只，并行获取历史）
- `analyze_portfolio_exposure`：组合集中度、波动率、各标的年化收益/风险
- `get_quick_analysis`：一键组合分析（行情 + 技术指标），基于 Pipeline 流水线引擎
- `get_valuation_percentile`：PE/PB 历史分位估算
- `core/pipeline.py`：异步流水线引擎，支持链式调用和错误传递

### 数据源增强

- 新增 `efinance_source.py`：基于 efinance SDK 的 A 股数据源（龙虎榜/资金流）
- 6 工具降级闭环：efinance → eastmoney → error
- `STANDARD_COLUMNS` 标准化列名（`services/base.py`）

### 技术分析增强

- 定性判断：7 档趋势状态、5 档量能定性、综合评分 0-100
- RSI 超卖加分修复：RSI<30 加 10 分反弹信号
- `data_timestamp` 注入：quote/history/indicators 三层覆盖

### 文档重构

- README 全面重写：用途/范围/示例/MCP 配置
- docs 重组为 `design/` `tracking/` `archive/` 三目录
- `v0.1-schema.md` → `schema-reference.md`：去版本号的活文档
- 全部文档旧名 `market-data-mcp` → `stockhub-mcp`
- 新增 `INDEX.md` 文档导航
- roadmap 标记 V0.1-V0.4 `[已完成]`
- 免责声明 + MIT License
- `.pypirc` PyPI token 自动配置

### 发布

- PyPI 发布：`pip install stockhub-mcp`
- https://pypi.org/project/stockhub-mcp/
- wheel 构建 + `[build-system]` setuptools 配置
- `[project.urls]` GitHub 链接
- `readme` / `keywords` / `classifiers` 元数据

### Bug 修复

- search 模型 exchange/currency 改为可选字段
- etf_info 字段映射修正
- fund timestamp/排名解析修正
- dividend_yield 重复乘 100
- `to_yfinance()` 参数错误（7 处）
- quick_analysis 错误传递修复
- 旧 `pip install -e .` 残留清理

### 配置

- `.env.example` 重写：中英双语注释，对齐 `config.py` 6 个配置项
- `pyproject.toml`：version `0.4.0`，efinance 作为可选增强依赖
- `[build-system]` setuptools 配置

### QA

- 24 测试全部通过（模型校验 + 错误路径 + Pipeline + 风险指标 + 组合分析）

### 发布

- PyPI 发布：`pip install stockhub-mcp`
- https://pypi.org/project/stockhub-mcp/

---

## v0.1.0 (2025-06-15)

### 初始版本

- 10 个核心工具：行情、K线、指标、板块、资金流、搜索、日历、缓存、源状态
- 5 个数据源：yfinance、腾讯、新浪、东方财富、AkShare
- 统一响应格式、动态缓存、熔断降级
- 193 个 QA 测试通过
