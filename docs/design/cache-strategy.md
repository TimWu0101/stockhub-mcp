# stockhub-mcp 动态缓存策略

本文定义 `stockhub-mcp` 在价格查询类工具中的本地缓存策略，用于降低免费接口消耗、抑制大模型短时间重复调用，并避免在关键交易时点返回过时数据。

---

## 一、目标

### 主要目标
- 降低大模型在复杂回答中对同一标的的短时间重复调用
- 减少免费 / 限额接口在几分钟内被快速消耗
- 在非交易时段尽量复用已获取过的稳定价格数据
- 在关键交易时点（开盘、集合竞价、收盘前后）避免使用过期缓存

### 非目标
- 不是长期数据缓存
- 不是数据库级历史存储
- 不是为了替代真实行情刷新
- 不用于新闻、公告、资金流等高语义复杂数据的首版缓存

---

## 二、首版适用范围

### 首版启用缓存的工具
- `get_realtime_quote`
- `get_batch_quotes`（按 symbol 独立缓存）
- `get_index_quote`（如后续加入）

### 首版暂不启用缓存的工具
- `get_market_news`
- `get_company_news`
- `get_capital_flow`
- `get_northbound_flow`
- `get_dragon_tiger_list`
- `get_macro_news`
- `get_pre_market_briefing`
- 盘口深度 / 大单 / 竞价异动类工具

原因：这些能力的数据变化语义更复杂，缓存策略应在后续单独设计。

---

## 三、核心原则

### 1. 只对价格类查询做本地缓存
缓存目标是抑制“短时间内同一 symbol 被模型反复查询”，而不是让系统长期返回旧数据。

### 2. 首版同时支持两种过期方式
- **绝对过期时间**：缓存到某个明确时刻失效，适用于 A股 / 中国香港股票的午休、收盘后、周末与节假日
- **相对 TTL**：缓存若干秒后失效，适用于美股盘前 / 盘后等仍较活跃的场景

### 3. 越接近关键交易时点，越保守
例如：
- A股集合竞价前后
- A股开盘前关键窗口
- A股收盘前关键窗口
- 中国香港股票开市前时段与收市竞价时段
- 美股美东时间开盘前 5 分钟

这些场景默认不缓存。

### 4. 所有缓存命中都必须对调用方可见
返回结果中必须包含缓存元信息，避免调试困难和“模型误以为拿到的是实时数据”。

### 5. 交易日历或市场时段判断失败时，默认不缓存
如果 `trading_calendar` 或 `market_session` 判断失败，缓存策略必须退回最保守模式：
- 不命中旧缓存
- 不写入新缓存
- `warning` 中记录原因

---

## 四、首版正式规则

## 1. A股（中国大陆）

| 场景 | 过期方式 | 正式规则 |
|---|---|---|
| 连续竞价时段（09:30-11:30，13:00-14:55） | 禁用缓存 | 不缓存 |
| 集合竞价 / 开盘前关键窗口（09:10-09:30） | 禁用缓存 | 不缓存 |
| 收盘前关键窗口（14:55-15:00） | 禁用缓存 | 不缓存 |
| 午休时段（11:30-13:00） | 绝对过期 | 缓存到当日 `13:00:00` |
| 收盘后（15:00起） | 绝对过期 | 缓存到**下一交易日 `09:00:00`** |
| 周末 / 节假日 | 绝对过期 | 缓存到**下一交易日 `09:00:00`** |

### 说明
- A股首版不再用“午休 60-120s / 收盘后 300s”这类区间值，而是改成明确的绝对过期时间
- 选择次日 `09:00`，是为了避开 `09:15` 后集合竞价敏感窗口

---

## 2. 中国香港股票

| 场景 | 过期方式 | 正式规则 |
|---|---|---|
| 上午持续交易时段（09:30-12:00） | 禁用缓存 | 不缓存 |
| 开市前时段（含竞价相关窗口） | 禁用缓存 | 不缓存 |
| 午休时段（12:00-13:00） | 绝对过期 | 缓存到当日 `13:00:00` |
| 下午持续交易时段（13:00-16:00） | 禁用缓存 | 不缓存 |
| 收市竞价交易时段（16:00-16:10） | 禁用缓存 | 不缓存 |
| 收盘后（16:10起） | 绝对过期 | 缓存到**下一交易日 `09:00:00`** |
| 周末 / 节假日 | 绝对过期 | 缓存到**下一交易日 `09:00:00`** |

### 说明
- 中国香港股票首版采用与 A股同类的绝对过期思路，但明确避开开市前与收市竞价时段
- 中国香港股票午休固定缓存到当日 `13:00:00`
- 若交易所出现半日市、临时停市或特殊安排，应由 `trading_calendar` / `market_session` 返回精确 session；缓存层仅依赖该判断结果
- 若中国香港股票实际 session 判断失败，则默认不缓存

---

## 3. 美股

| 场景 | 过期方式 | 正式规则 |
|---|---|---|
| 正常盘中交易时段（美东时间 09:30-16:00） | 禁用缓存 | 不缓存 |
| 开盘前 5 分钟（美东时间 09:25-09:30） | 禁用缓存 | 不缓存 |
| 盘前活跃时段（美东时间 04:00-09:25） | 相对 TTL | `10s` |
| 盘后活跃时段（美东时间 16:00-20:00） | 相对 TTL | `10s` |
| 收盘后普通非交易时段（美东时间 20:00-次日04:00） | 相对 TTL | `300s` |
| 周末 / 节假日 | 相对 TTL | `300s` |

### 说明
- 美股首版**不采用“缓存到下一交易日开盘前”的绝对过期策略**
- 原因是美股盘前 / 盘后交易更活跃，直接跨整晚缓存过于激进
- 时间判断以美东时间为准，夏令时 / 冬令时切换必须由 `trading_calendar` / `market_session` 处理
- 若出现提前收盘日或特殊交易日，应由交易日历返回精确 session；缓存层不手写节日特判

---

## 五、缓存 key 正式设计

建议缓存 key 至少包含以下维度：

```text
quote:{tool}:{market}:{instrument_type}:{symbol}:{source}:{session_state}
```

例如：

```text
quote:get_realtime_quote:CN:stock:600519:tx:post_close
quote:get_realtime_quote:US:stock:AAPL:yfinance:pre_market
quote:get_index_quote:HK:index:HSI:yfinance:post_close
```

### 为什么这样设计
- 避免不同工具互相污染
- 避免股票 / 指数 / ETF 混用
- 避免不同市场冲突
- 避免不同数据源混用
- 避免在不同市场状态下错误复用缓存

---

## 六、写缓存条件（正式规则）

只有同时满足以下条件，才允许把结果写入缓存：

1. 请求成功
2. `partial_success = false`
3. 本次请求未显式设置 `bypass_cache = true`
4. `market_session` 判断成功
5. 当前场景的缓存策略允许写入
6. `quality_flag` 不属于以下低质量类别：
   - `stale`
   - `delayed`
   - `fallback_low_confidence`
7. 返回结果包含有效价格与有效时间戳

### 明确禁止写缓存的场景
- 数据源超时后返回不完整结果
- fallback 成功但被标记为低置信度
- `partial_success = true`
- session / calendar 判断失败
- 当前属于关键交易时点禁用缓存窗口

---

## 七、缓存命中与返回结构

### 1. 首版不采用滑动过期
缓存项的 `expires_at` 只允许在**首次写入缓存**时计算一次，后续命中缓存时：
- 不更新 `cached_at`
- 不更新 `expires_at`
- 不重新计算 TTL
- 不因为多次调用而顺延失效时间

只有在缓存已失效、重新回源成功后，才允许生成一条新的缓存记录。

### 2. 返回结构

所有价格类查询建议在返回结构中附带缓存字段：

```json
{
  "cache": {
    "hit": true,
    "expires_at": "2026-06-16T09:00:00+08:00",
    "ttl_remaining": 61200,
    "cached_at": "2026-06-15T15:01:10+08:00",
    "policy": "cn_post_close_until_next_trading_day_0900",
    "bypass_cache": false
  }
}
```

### 字段说明
- `hit`：是否命中缓存
- `expires_at`：缓存失效时间；绝对过期策略下这是核心字段
- `ttl_remaining`：剩余秒数；用于统一调试和日志
- `cached_at`：写入缓存的时间
- `policy`：命中的缓存策略名
- `bypass_cache`：本次请求是否显式跳过缓存

---

## 八、调用方跳过缓存与主动清缓存机制

### 1. 跳过缓存
所有价格类工具首版统一支持：

```json
{
  "symbol": "600519",
  "bypass_cache": true
}
```

### 适用场景
- 用户明确要求“最新价格”
- 调试时验证数据源
- 对关键时点数据做二次确认
- 某些智能体任务认为当前问题对时效特别敏感

### 规则
- `bypass_cache = true` 时，不读取旧缓存
- `bypass_cache = true` 时，本次结果默认也不写入缓存

### 2. 主动清缓存
首版建议增加显式清缓存工具，例如：
- `clear_quote_cache`
- 或统一设计为 `clear_cache`

推荐首版先支持以下入参能力：

```json
{
  "scope": "symbol",
  "market": "CN",
  "symbol": "600519",
  "tool": "get_realtime_quote",
  "source": "tx",
  "dry_run": false
}
```

### 推荐清理范围
- `scope = symbol`：清除单个标的缓存
- `scope = market`：清除某个市场下的价格缓存
- `scope = tool`：清除某个工具名对应的缓存
- `scope = all`：清除全部价格缓存，仅限显式调用

### 首版约束
- `scope = all` 必须显式传入，不允许默认全清
- 清缓存操作只影响本地价格缓存，不影响历史数据、新闻或其他未来缓存层
- 清缓存工具本身不允许模糊推断参数，避免误清
- 建议支持 `dry_run = true`，先返回预计清除的 key 数量与范围
- 建议返回 `deleted_count`、`matched_count`、`deleted_keys_sample`

### 推荐返回结构

```json
{
  "success": true,
  "scope": "symbol",
  "matched_count": 3,
  "deleted_count": 3,
  "dry_run": false,
  "filters": {
    "market": "CN",
    "symbol": "600519",
    "tool": "get_realtime_quote"
  },
  "warnings": []
}
```

### 为什么要有这个能力
- 调用方可以在怀疑缓存过旧时主动刷新
- 方便调试缓存 key、过期行为和 source fallback
- 对 agent 场景有用：复杂问题回答前可先清掉指定 symbol 缓存，强制拉最新值
- 比单纯等待 `expires_at` 更可控

### 风险控制
- `scope = all` 建议记录审计日志
- 若缓存后端不可用，返回结构化 warning / error，不要静默失败
- 清缓存成功不代表已经重新拉源，调用方若要最新值，仍需再发一次查询请求

---

## 九、`get_batch_quotes` 的正式缓存规则

### 1. 按 symbol 独立缓存
`get_batch_quotes` 不使用整批缓存 key，而是：
- 每个 symbol 独立判断是否命中缓存
- 每个 symbol 独立决定是否回源
- 每个 symbol 独立决定是否写入缓存

### 2. 返回结构按项附带 cache
每个结果项都应包含各自的 `cache` 字段，而不是整批共用一个缓存状态。

### 3. 顶层只保留聚合语义
顶层可保留：
- `partial_success`
- `warnings`
- `meta`

但不应把整批请求误描述为“全部命中缓存”或“全部未命中缓存”。

---

## 十、与错误模型的联动规则

### 1. 缓存层异常不应让主请求失败
例如：
- 内存缓存读失败
- 写缓存失败
- TTL 计算失败

这类问题应：
- 记录到 `warnings`
- 回退为直接请求数据源
- 不单独构成工具级失败

### 2. 只有源请求失败时才进入正式 error
也就是说：
- 缓存 miss 不是错误
- 缓存 backend 异常不是主错误
- 真正的 `error` 仍由数据源请求、fallback 结果和工具执行结果决定

### 3. 建议 warning 示例
- `cache_bypassed_by_request`
- `cache_skipped_due_to_unknown_session`
- `cache_write_skipped_due_to_low_quality`
- `cache_backend_unavailable`

---

## 十一、实现建议

### 1. 缓存层应独立于具体数据源实现
建议设计统一缓存装饰层，而不是在 `yfinance`、腾讯、新浪、东方财富各自重复实现。

### 2. 先做内存缓存，再决定是否扩展磁盘缓存
首版目标是抑制短时间重复请求，所以：
- 优先内存缓存即可
- 不急着做 Redis / SQLite / 磁盘持久化

### 3. 缓存策略必须依赖统一的市场时段判断模块
不要在每个工具里手写时间判断，应统一抽成：
- `trading_calendar`
- `market_session`
- `cache_policy`

### 4. unknown session 一律保守处理
若 `market_session = unknown` 或交易日历不可用：
- 不读缓存
- 不写缓存
- 添加 warning

---

## 十二、建议的策略命名

可考虑使用类似这样的策略名：

- `cn_live_no_cache`
- `cn_lunch_until_1300`
- `cn_post_close_until_next_trading_day_0900`
- `hk_pre_open_no_cache`
- `hk_lunch_until_1300`
- `hk_auction_no_cache`
- `hk_post_close_until_next_trading_day_0900`
- `us_pre_open_no_cache`
- `us_pre_market_10s`
- `us_after_hours_10s`
- `us_deep_offhours_300s`
- `weekend_until_next_trading_day_0900`

这样返回结果和日志都更容易排查。

---

## 十三、首版结论

### 首版正式纳入项目设计的能力
- 对 `get_realtime_quote` 增加本地缓存
- `get_batch_quotes` 按 symbol 独立缓存
- A股与中国香港股票在稳定非交易时段优先使用绝对过期时间
- 美股继续使用保守的短 TTL
- A股 / 中国香港股票的关键竞价与交易切换窗口禁用缓存
- 返回缓存元信息
- 支持 `bypass_cache`
- 与 `error-model.md` 联动 `warnings / partial_success / quality_flag`

### 首版仍不支持的
- 新闻类缓存
- 盘口深度缓存
- 资金流缓存
- 长期持久化缓存

---

## 十四、为什么这个设计适合 stockhub-mcp

因为 `stockhub-mcp` 面向的是 AI 调用场景，而 AI 在复杂问题中容易在几秒内对同一标的发起多次重复请求。与普通前端用户不同，AI 的“重复调用”问题更严重，因此：

- 绝对过期策略能显著降低 A股 / 中国香港股票在非交易时段的无意义重复请求
- 保守短 TTL 能避免美股活跃时段误用旧数据
- 对免费接口和限额接口都很友好

这是一个非常适合统一金融 MCP 的基础设施层能力。
