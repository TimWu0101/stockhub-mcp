# stockhub-mcp design 文档入口

> 本目录用于存放统一设计约定与历史设计背景材料。
>
> **当前能力现状** 不在 `design/` 查看，请看 [`../tracking/current-capabilities.md`](../tracking/current-capabilities.md)。

---

## 一、当前定义层

这些文档用于回答“当前统一约定是什么”：

- [`schema-reference.md`](./schema-reference.md)：响应结构、通用字段、枚举语义与 schema 速查主入口
- [`error-model.md`](./error-model.md)：错误模型、warning、partial success 与容错语义说明
- [`cache-strategy.md`](./cache-strategy.md)：价格类缓存策略、缓存字段与缓存/错误联动规则

## 二、历史背景层

这些文档用于回答“之前的设计方案和评审背景是什么”，**不作为当前实现主入口**：

- [`system_design.md`](./system_design.md)：历史系统设计稿 / 架构背景参考
- [`expert-review-notes.md`](./expert-review-notes.md)：历史阶段的设计评审记录 / 背景参考
- [`class-diagram.mermaid`](./class-diagram.mermaid)：历史设计稿配套类图
- [`sequence-diagram.mermaid`](./sequence-diagram.mermaid)：历史设计稿配套时序图

## 三、推荐阅读顺序

1. 先看 [`../tracking/current-capabilities.md`](../tracking/current-capabilities.md) 确认当前能力现状
2. 再看 [`schema-reference.md`](./schema-reference.md)
3. 按需查看 [`error-model.md`](./error-model.md) / [`cache-strategy.md`](./cache-strategy.md)
4. 只有在需要追溯背景时再看历史背景层文档
