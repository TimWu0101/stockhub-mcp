# stockhub-mcp 错误模型与容错设计

本文定义 `stockhub-mcp` 的统一错误模型、部分成功机制、质量标记和核心容错策略，用于保证主流程可闭环，并在多数据源、跨市场、AI 高频调用场景下保持可解释性和稳定性。

---

## 一、设计目标

### 目标
- 对外返回统一、可预测的错误结构
- 区分永久错误与临时错误
- 支持 fallback、partial success、warning 与质量标记
- 让 AI 能够基于返回结构做更稳的回答，而不是只看到一段模糊错误文案

### 非目标
- 不追求所有数据源返回完全同一字段
- 不要求所有工具首版都实现所有 warning 类型
- 不把所有异常都上升为全局失败

---

## 二、统一响应层级

## 1. 成功
```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

## 2. 部分成功
```json
{
  "success": true,
  "partial_success": true,
  "data": {},
  "warnings": [],
  "meta": {}
}
```

## 3. 完全失败
```json
{
  "success": false,
  "error": {
    "code": "SOURCE_TIMEOUT",
    "type": "temporary",
    "message": "主数据源请求超时，备用源也失败",
    "retryable": true
  },
  "meta": {}
}
```

---

## 三、错误分类

建议统一使用三大类：

### 1. `input_error`
用户输入非法或不完整导致无法执行。

### 2. `business_error`
输入合法，但业务条件不满足。

### 3. `source_error`
数据源、网络、解析、fallback 失败。

### 4. `system_error`
内部实现或未预期异常。

---

## 四、推荐错误码

## 1. 输入类错误

| 错误码 | 含义 | retryable |
|---|---|---|
| `INVALID_SYMBOL` | 标的格式非法 | false |
| `SYMBOL_NOT_FOUND` | 找不到该标的 | false |
| `AMBIGUOUS_SYMBOL` | 标的有歧义，需要 уточ定市场 | false |
| `INVALID_PERIOD` | period 非法 | false |
| `INVALID_INTERVAL` | interval 非法 | false |
| `INVALID_ARGUMENT` | 其他参数非法 | false |
| `TOO_MANY_SYMBOLS` | compare / batch 超过数量上限 | false |

## 2. 业务类错误

| 错误码 | 含义 | retryable |
|---|---|---|
| `MARKET_NOT_SUPPORTED` | 当前市场暂不支持 | false |
| `TOOL_NOT_SUPPORTED_FOR_MARKET` | 工具不支持该市场 | false |
| `NO_DATA_AVAILABLE` | 当前无可用数据 | false |
| `TRADING_HALTED` | 停牌 | false |
| `DELISTED_SYMBOL` | 已退市 | false |
| `MARKET_CLOSED` | 市场休市（可作为提示，不一定是失败） | false |
| `EMPTY_SCREEN_RESULT` | 筛选结果为空 | false |

## 3. 数据源类错误

| 错误码 | 含义 | retryable |
|---|---|---|
| `SOURCE_TIMEOUT` | 主源超时 | true |
| `SOURCE_UNAVAILABLE` | 数据源不可用 | true |
| `SOURCE_RATE_LIMITED` | 数据源限流 | true |
| `SOURCE_RESPONSE_INVALID` | 返回结构异常 | true |
| `SOURCE_STALE_DATA` | 数据过旧 | true |
| `FALLBACK_EXHAUSTED` | 所有备用源都失败 | true |
| `PARTIAL_SOURCE_FAILURE` | 部分源失败 | true |

## 4. 系统类错误

| 错误码 | 含义 | retryable |
|---|---|---|
| `CACHE_ERROR` | 缓存层异常 | true |
| `INTERNAL_ERROR` | 未预期内部错误 | true |
| `NOT_IMPLEMENTED` | 功能未实现 | false |

---

## 五、错误结构建议

```json
{
  "success": false,
  "error": {
    "code": "SOURCE_TIMEOUT",
    "type": "source_error",
    "message": "主数据源请求超时",
    "retryable": true,
    "details": {
      "market": "CN",
      "symbol": "600519",
      "attempted_sources": ["tencent", "sina"],
      "fallback_exhausted": true
    }
  },
  "meta": {
    "request_id": "...",
    "market_session": "post_close"
  }
}
```

### 建议字段
- `code`：机器可读错误码
- `type`：错误分类
- `message`：给用户/模型看的简明说明
- `retryable`：是否值得稍后重试
- `details`：诊断信息

---

## 六、部分成功机制

很多金融工具不应该“全有全无”。

### 典型场景
- 批量报价：5 只股票中 4 只成功，1 只失败
- 股票比较：某一只股票缺少 PB 或 ROE
- 新闻聚合：宏观新闻成功，公司新闻失败
- quote 成功，但附加元数据来自 fallback

### 建议结构
```json
{
  "success": true,
  "partial_success": true,
  "data": {},
  "warnings": [
    {
      "code": "PARTIAL_SOURCE_FAILURE",
      "message": "部分标的报价获取失败",
      "details": {
        "failed_symbols": ["XXXX"]
      }
    }
  ]
}
```

---

## 七、warning 体系

warning 不等于 error。

### 建议 warning 场景
- 使用了 fallback 源
- 数据延迟较高
- 当前市场休市，返回的是最近一次收盘价
- 新闻抓取只拿到部分来源
- compare 时某些字段缺失
- 命中缓存

### 常见 warning code
- `FALLBACK_USED`
- `STALE_DATA_WARNING`
- `MARKET_CLOSED_LAST_CLOSE_USED`
- `CACHE_HIT`
- `PARTIAL_FIELD_MISSING`
- `NEWS_SOURCE_PARTIAL`

---

## 八、质量标记（quality flags）

建议所有核心工具统一返回质量元信息。

### 推荐字段
```json
{
  "meta": {
    "source": "tencent",
    "fallback_used": ["sina"],
    "market": "CN",
    "market_session": "post_close",
    "is_realtime": false,
    "data_delay": "close_based",
    "quality_flag": "fallback_source"
  }
}
```

### `quality_flag` 候选值
- `primary_source`
- `fallback_source`
- `cached`
- `delayed`
- `estimated`
- `partial`
- `stale`

---

## 九、缓存相关错误与提示

结合动态 TTL 缓存层，建议支持：

### 错误码
- `CACHE_ERROR`
- `CACHE_POLICY_INVALID`

### warning
- `CACHE_HIT`
- `CACHE_BYPASSED`
- `CACHE_DISABLED_NEAR_SESSION_BOUNDARY`

### meta 字段
```json
{
  "cache": {
    "hit": true,
    "ttl_remaining": 120,
    "cached_at": "2026-06-15T15:01:10+08:00",
    "policy": "cn_post_close_300s",
    "bypass_cache": false
  }
}
```

---

## 十、按工具类型的容错要求

## 1. 价格类工具
必须具备：
- 主源失败自动切备用源
- 市场状态识别
- 缓存命中元信息
- 数据延迟 / quality flag
- 标的不存在与停牌区分

## 2. 历史 K 线工具
必须具备：
- 复权口径说明
- period / interval 非法检查
- 数据为空时明确原因
- 跨市场字段统一

## 3. 新闻类工具
必须具备：
- 多源部分成功
- 新闻为空不等于系统失败
- 发布时间标准化
- 来源标记

## 4. 对比 / 批量工具
必须具备：
- `partial_success`
- 单标的失败列表
- 缺失字段 warning

---

## 十一、为什么这套错误模型适合 AI 调用

因为大模型不是传统 UI，它会：
- 短时间大量调用
- 在部分失败时继续推理
- 根据 warning 和质量标记调整措辞
- 在 `retryable=true` 时选择重试或降级回答

如果只有一段自然语言报错，AI 很难稳定处理。

---

## 十二、首版必须落地的最小集合

建议在首版先强制实现这些：

### 错误码
- `SYMBOL_NOT_FOUND`
- `INVALID_ARGUMENT`
- `MARKET_NOT_SUPPORTED`
- `SOURCE_TIMEOUT`
- `FALLBACK_EXHAUSTED`
- `INTERNAL_ERROR`

### warning
- `FALLBACK_USED`
- `CACHE_HIT`
- `MARKET_CLOSED_LAST_CLOSE_USED`

### meta
- `source`
- `market`
- `market_session`
- `is_realtime`
- `quality_flag`

### 结构
- `success`
- `partial_success`
- `warnings`
- `error`

---

## 十三、总结

`stockhub-mcp` 真正要做到“闭环”，不只是能拿到数据，还要做到：

- 失败时知道为什么失败
- 临时失败时知道能不能重试
- 部分成功时知道哪些字段可信
- fallback 时知道是否降级
- 缓存命中时知道数据是否可能过时

这套错误模型和容错结构，就是把“能跑”升级成“能长期稳定给 AI 用”。
