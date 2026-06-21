# archive 历史归档说明

> 归档说明：`archive/` 保存的是方案讨论期的历史分析、参考映射与来源清单，用于追溯“之前如何判断、参考过什么、为什么这样收敛”。**这里不是当前事实来源**；当前实现状态、维护结论与版本边界请以 `docs/tracking/` 与现行工具清单为准。

## 归档里保存什么

- 方案讨论阶段明确参考过的外部仓库与资料来源。
- 早期对 skill / 仓库能力的映射结论。
- 仍有追溯价值、但不再作为当前维护主入口的历史判断。

## 归档里不保存什么

- 当前已交付能力清单。
- 当前待办、风险、阻塞与发布边界。
- 已在 `tracking/` 或 `design/` 中有唯一口径的现行说明。

## 推荐阅读顺序

1. 先看 [`skills-to-stockhub-mapping.md`](./skills-to-stockhub-mapping.md)：了解历史上哪些来源被映射成了 `stockhub-mcp` 的能力方向，以及最终定位。
2. 再看 [`referenced-repos.md`](./referenced-repos.md)：查看方案期实际参考过哪些外部仓库、各自借鉴点与局限。
3. 若要确认“现在是什么状态”，离开 archive，改看 `docs/tracking/current-capabilities.md` 与 `docs/tracking/development-status.md`。

## 当前保留的核心归档文

- [`skills-to-stockhub-mapping.md`](./skills-to-stockhub-mapping.md)：archive 中的历史映射主文。
- [`referenced-repos.md`](./referenced-repos.md)：外部参考仓库清单。

## 已合并收敛的旧分析

以下旧材料已不再单独保留长文，其仍有价值的结论已吸收进现有归档文：

- `skills-analysis.md`
  - 已吸收内容：
    - 历史上的三类参考分组：行情主链路、新闻/事件层、研究/分析层。
    - “哪些来源最值得优先借鉴”的排序结论。
    - 对 `a-stock-quote`、`yfinance`、`topnews`、`cnfinancialscraper`、`tdx` 系、`stock-selecter` 等来源的最终定位判断。
    - “适合当前主线”与“更适合后续增强层”的收敛结论。

## 维护原则

- archive 只保留“仍值得追溯的历史结论”，不保留大量重复展开。
- 若某历史判断已经变成当前事实，应转写到 `tracking/` 或 `design/`，而不是继续堆在 archive。
- 若某旧稿只是在重复另一篇归档主文，应优先合并、删除或降级为简短说明。
