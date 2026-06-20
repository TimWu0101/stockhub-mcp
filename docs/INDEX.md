# 文档索引

> 项目：stockhub-mcp | 最后更新：2026-06-20

枚举/常量/错误码以代码为唯一真源，文档引用不重复定义。

---

## 一、核心设计

| 文档 | 说明 |
|---|---|
| [system_design.md](./design/system_design.md) | 架构决策：分层、数据源、领域模型、任务分解 |
| [schema-reference.md](./design/schema-reference.md) | 通用 Schema：响应结构/字段/枚举/错误码速查 |
| [error-model.md](./design/error-model.md) | 错误码/Warning/质量标记/容错策略完整定义 |
| [cache-strategy.md](./design/cache-strategy.md) | 缓存策略：A股/港股/美股 TTL 规则、Key 格式、盘中全清 |
| [expert-review-notes.md](./design/expert-review-notes.md) | 设计决策记录 (ADR) |
| [class-diagram.mermaid](./design/class-diagram.mermaid) | 领域模型类图 |
| [sequence-diagram.mermaid](./design/sequence-diagram.mermaid) | 核心调用时序图 |

---

## 二、开发跟踪

| 文档 | 说明 |
|---|---|
| [development-status.md](./tracking/development-status.md) | 进度记录：版本状态 / 工具清单 / Bug / QA |
| [roadmap.md](./tracking/roadmap.md) | 版本路线：V0.1 → V1.1 |

---

## 三、归档

| 文档 | 说明 |
|---|---|
| [referenced-repos.md](./archive/referenced-repos.md) | 借鉴仓库清单（规划期） |
| [skills-analysis.md](./archive/skills-analysis.md) | Skills 分析（规划期） |
| [skills-to-stockhub-mapping.md](./archive/skills-to-stockhub-mapping.md) | 接口映射表（规划期） |

---

## 文档约定

- **枚举/常量**：代码 `stockhub_mcp/enums.py` 唯一真源
- **错误码**：`design/error-model.md` 唯一定义
- **缓存策略**：`design/cache-strategy.md` 唯一定义
- **新增文档**：放入对应目录，在此注册
- **归档**：移至 `archive/`
