# stockhub-mcp 文档导航

> 项目：`stockhub-mcp` | 最后更新：2026-06-20

这份文档是维护入口，不承担逐条设计展开，也不重复记录所有历史过程。

维护时优先按四类信息查阅：**现状**、**约定**、**规划**、**历史**。

---

## 一、先看哪里

### 如果你只想快速判断“现在是什么状态”

- **当前能力总览**：[`tracking/current-capabilities.md`](./tracking/current-capabilities.md)
  - 用途：回答“当前已经能做什么、当前版本边界到哪里”
  - 适合场景：看已交付工具范围、能力分组、当前发布边界

- **开发跟踪与维护重点**：[`tracking/development-status.md`](./tracking/development-status.md)
  - 用途：回答“现在还要继续跟踪什么、有哪些风险、维护时按什么口径更新”
  - 适合场景：看待验证事项、阻塞项、维护规则、少量必要历史边界

- **版本规划与后续增强**：[`tracking/roadmap.md`](./tracking/roadmap.md)
  - 用途：回答“下一步准备做什么、哪些属于后续版本而不是当前能力”
  - 适合场景：看版本边界、待开发方向、能力扩展路线

---

## 二、按维护场景查阅

| 维护场景 | 首选文档 | 说明 |
|---|---|---|
| 想确认当前已交付能力 | [`tracking/current-capabilities.md`](./tracking/current-capabilities.md) | 当前能力的主说明文档 |
| 想确认 design 文档怎么分工、当前应先看什么 | [`design/README.md`](./design/README.md) | design 子目录入口；先看当前定义层，再按需追溯历史背景 |
| 想查响应结构、字段和 schema | [`design/schema-reference.md`](./design/schema-reference.md) | 通用响应结构、字段和枚举/错误码速查 |
| 想查错误模型与 warning 约定 | [`design/error-model.md`](./design/error-model.md) | 错误分类、错误码、partial success、warning、质量标记 |
| 想查缓存策略与缓存返回字段 | [`design/cache-strategy.md`](./design/cache-strategy.md) | 价格类缓存规则、key 设计、bypass/clear 约定 |
| 想看当前风险、阻塞与待验证项 | [`tracking/development-status.md`](./tracking/development-status.md) | 发布后维护主入口 |
| 想看后续版本规划 | [`tracking/roadmap.md`](./tracking/roadmap.md) | V1.1 及以后规划 |
| 想追溯历史分析材料 | [`archive/README.md`](./archive/README.md) | 归档总入口；再按需进入映射主文与参考仓库清单 |

---

## 三、文档分工

### 1. 现状

这些文档回答“**现在项目是什么**”：

| 文档 | 角色 |
|---|---|
| [`tracking/current-capabilities.md`](./tracking/current-capabilities.md) | 当前能力总览；维护者判断“已交付范围”的第一入口 |
| [`docs/TOOLS.md`](./TOOLS.md) | 工具列表与对外能力清单补充入口 |
| `README.md` | 对外使用、安装与项目介绍入口 |

### 2. 约定

这些文档回答“**系统怎么约定、字段怎么理解、哪些规则是统一的**”：

| 文档 | 角色 |
|---|---|
| [`design/schema-reference.md`](./design/schema-reference.md) | Schema、字段、枚举分组、错误码速查入口 |
| [`design/error-model.md`](./design/error-model.md) | 错误模型、warning、质量标记、容错语义唯一说明入口 |
| [`design/cache-strategy.md`](./design/cache-strategy.md) | 缓存策略、缓存行为和缓存相关返回字段唯一说明入口 |

补充约定：

- **枚举/常量唯一真源**：代码实现
- **字段/结构速查**：`schema-reference.md`
- **错误语义**：`error-model.md`
- **缓存语义**：`cache-strategy.md`

### 3. 规划

这些文档回答“**后面准备做什么**”：

| 文档 | 角色 |
|---|---|
| [`tracking/roadmap.md`](./tracking/roadmap.md) | 版本规划与后续增强方向 |
| [`tracking/development-status.md`](./tracking/development-status.md) | 当前待验证、待推进、阻塞与维护事项 |

### 4. 历史

这些文档回答“**之前怎么想过、有哪些旧分析可供追溯**”：

| 文档 | 角色 |
|---|---|
| [`design/system_design.md`](./design/system_design.md) | 历史架构方案 / 设计背景参考，不作为当前实现主入口 |
| [`design/expert-review-notes.md`](./design/expert-review-notes.md) | 历史阶段设计评审记录 / 背景参考 |
| [`archive/README.md`](./archive/README.md) | archive 总入口与收敛说明 |
| [`archive/skills-to-stockhub-mapping.md`](./archive/skills-to-stockhub-mapping.md) | 历史映射主文 |
| [`archive/referenced-repos.md`](./archive/referenced-repos.md) | 规划期参考仓库清单 |

---

## 四、推荐阅读顺序

### 新维护者首次接手

1. [`tracking/current-capabilities.md`](./tracking/current-capabilities.md)
2. [`tracking/development-status.md`](./tracking/development-status.md)
3. [`design/schema-reference.md`](./design/schema-reference.md)
4. [`design/error-model.md`](./design/error-model.md)
5. [`design/cache-strategy.md`](./design/cache-strategy.md)
6. [`tracking/roadmap.md`](./tracking/roadmap.md)
7. [`design/system_design.md`](./design/system_design.md)（仅在需要追溯设计背景时阅读）

### 准备新增工具或扩展能力

1. [`tracking/current-capabilities.md`](./tracking/current-capabilities.md)
2. [`tracking/roadmap.md`](./tracking/roadmap.md)
3. [`design/schema-reference.md`](./design/schema-reference.md)
4. [`design/error-model.md`](./design/error-model.md)
5. [`design/cache-strategy.md`](./design/cache-strategy.md)
6. [`design/system_design.md`](./design/system_design.md)

### 准备修正文档或统一口径

1. 先确认现状：[`tracking/current-capabilities.md`](./tracking/current-capabilities.md)
2. 再确认维护口径：[`tracking/development-status.md`](./tracking/development-status.md)
3. 最后补充设计约定：`design/` 下对应专题文档

---

## 五、维护规则

- 不要把 **当前能力**、**后续规划**、**历史设计过程** 混写在同一主入口里。
- 若某项内容已进入当前发布能力，优先更新 [`tracking/current-capabilities.md`](./tracking/current-capabilities.md)。
- 若某项内容仍是待开发、待验证或风险事项，优先更新 [`tracking/development-status.md`](./tracking/development-status.md)。
- 若某项内容属于统一字段、错误、缓存或领域约定，优先更新 `design/` 下对应专题文档。
- 若内容主要用于追溯背景，不再是当前维护主线，应下沉到历史文档或 `archive/`。

---

## 六、快速判断规则

- **看当前能力** → [`tracking/current-capabilities.md`](./tracking/current-capabilities.md)
- **看 design 目录入口与阅读顺序** → [`design/README.md`](./design/README.md)
- **看历史架构方案/设计背景** → [`design/system_design.md`](./design/system_design.md)
- **看枚举定义与 schema** → [`design/schema-reference.md`](./design/schema-reference.md)
- **看错误模型 / 缓存策略 / 领域约定** → `design/` 下专题文档
- **看待开发 / 版本规划** → [`tracking/development-status.md`](./tracking/development-status.md) + [`tracking/roadmap.md`](./tracking/roadmap.md)
- **看历史归档** → [`archive/README.md`](./archive/README.md)
