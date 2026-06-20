# Schema 参考

> 通用响应结构、字段、枚举、错误码速查。枚举/常量以代码 `stockhub_mcp/enums.py` 为准。
> 覆盖 43 工具（V0.1-V0.4），新增工具按此规范扩展。

---

## 一、通用响应结构

### 1.1 顶层结构

所有工具统一返回以下结构：

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "warnings": [],
  "cache": null
}
```

### 1.2 失败时

```json
{
  "success": false,
  "data": null,
  "meta": {},
  "error": {
    "code": "SOURCE_TIMEOUT",
    "type": "source_error",
    "message": "...",
    "retryable": true,
    "details": {}
  }
}
```

### 1.3 部分成功时

```json
{
  "success": true,
  "partial_success": true,
  "data": {},
  "meta": {},
  "warnings": [
    {
      "code": "PARTIAL_SOURCE_FAILURE",
      "message": "...",
      "details": {}
    }
  ]
}
```

### 1.4 字段清单

| 字段 | 类型 | 必现 | 说明 |
|---|---|---|---|
| `success` | `boolean` | 是 | 请求是否成功 |
| `data` | `object \| null` | 是 | 业务数据；失败时为 `null` |
| `meta` | `object` | 是 | 始终返回的通用元信息 |
| `warnings` | `array` | 否 | 非致命问题的结构化列表 |
| `error` | `object` | 否 | 失败时出现，包含 `code` / `type` / `message` / `retryable` / `details` |
| `partial_success` | `boolean` | 否 | 仅部分成功时出现 |
| `cache` | `object \| null` | 否 | 仅价格类工具 + 启用缓存时出现 |

---

## 二、通用字段

### 2.1 `meta`（必现）

```json
{
  "meta": {
    "request_id": "uuid-string",
    "market": "CN",
    "symbol": "000000.CN",
    "source": "tx",
    "currency": "CNY",
    "timezone": "Asia/Shanghai",
    "market_session": "continuous",
    "is_realtime": true,
    "data_delay_seconds": 0,
    "quality_flag": "live",
    "fallback_used": false,
    "responded_at": "2026-06-15T14:35:00+08:00"
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `request_id` | `string` | 请求唯一标识 |
| `market` | `string` | 市场代码，见 3.1 |
| `symbol` | `string` | 内部标准 symbol，见 3.2 |
| `source` | `string` | 实际使用的数据源，见 3.4 |
| `currency` | `string` | ISO 4217 币种 |
| `timezone` | `string` | IANA 时区 |
| `market_session` | `string` | 当前市场时段，见 3.3 |
| `is_realtime` | `boolean` | 是否实时数据 |
| `data_delay_seconds` | `int` | 数据延迟秒数 |
| `quality_flag` | `string` | 数据质量标记，见 3.6 |
| `fallback_used` | `boolean` | 是否经历了 fallback |
| `data_timestamp` | `string` | 数据来源的时间戳（V0.3+） |
| `responded_at` | `string` | 响应时间 ISO 8601 |

### 2.2 `cache`（价格类工具启用时出现）

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

| 字段 | 类型 | 说明 |
|---|---|---|
| `hit` | `boolean` | 是否命中缓存 |
| `expires_at` | `string` | 缓存失效时间 ISO 8601 |
| `ttl_remaining` | `int` | 剩余秒数 |
| `cached_at` | `string` | 缓存写入时间 ISO 8601 |
| `policy` | `string` | 命中的策略名，见 `cache-strategy.md` |
| `bypass_cache` | `boolean` | 本次请求是否显式跳过缓存 |

### 2.3 `warnings`（部分成功或需关注时出现）

```json
{
  "warnings": [
    {
      "code": "FALLBACK_SOURCE_USED",
      "message": "主源不可用，已切换至备用源",
      "details": {
        "attempted_source": "tx",
        "used_source": "sina"
      }
    }
  ]
}
```

**首版 warning code 清单：**

| code | 说明 |
|---|---|
| `FALLBACK_SOURCE_USED` | 使用了备用数据源 |
| `SOURCE_PARTIALLY_UNAVAILABLE` | 部分源失败 |
| `CACHE_BYPASSED_BY_REQUEST` | 本次显式跳过了缓存 |
| `CACHE_SKIPPED_UNKNOWN_SESSION` | 因 session 判断失败跳过缓存 |
| `CACHE_WRITE_SKIPPED_LOW_QUALITY` | 因数据质量低跳过写缓存 |
| `CACHE_BACKEND_UNAVAILABLE` | 缓存后端不可用 |
| `STALE_DATA` | 返回的是过期数据 |
| `DATA_DELAYED` | 数据有延迟 |
| `MARKET_CLOSED` | 当前市场休市，返回最近一次有效数据 |
| `FIELD_FALLBACK` | 个别字段来自备用源 |
| `FIELD_MISSING` | 个别字段缺失 |

---

## 三、枚举值

### 3.1 市场 `market`

| 值 | 含义 |
|---|---|
| `CN` | A股（沪深） |
| `HK` | 中国香港股票 |
| `US` | 美股 |

### 3.2 symbol 标准化

三层结构：

| 层 | 示例 | 说明 |
|---|---|---|
| 用户输入层 | `茅台` / `600519` / `AAPL` | 用户/模型输入，模糊 |
| 内部标准层 | `CN:600519` / `HK:00700` / `US:AAPL` | 工具内部统一格式 |
| 数据源适配层 | `sh600519` / `00700.HK` / `AAPL` | 按源转换 |

`meta.symbol` 返回内部标准层格式：`{market}:{code}`

### 3.3 市场时段 `market_session`

| 值 | 含义 |
|---|---|
| `pre_opening` | 开盘前（含集合竞价） |
| `continuous` | 连续竞价时段 |
| `lunch_break` | 午休 |
| `auction` | 收市竞价 |
| `post_close` | 收盘后 |
| `closed` | 非交易日（周末/节假日） |
| `unknown` | 无法判断（保守处理） |

### 3.4 数据源 `source`

| 值 | 数据源 |
|---|---|
| `yfinance` | Yahoo Finance |
| `efinance` | 东方财富 efinance SDK |
| `tx` | 腾讯行情 |
| `sina` | 新浪行情 |
| `eastmoney` | 东方财富 |
| `akshare` | AkShare |
| `tushare` | Tushare（可选增强） |
| `computed` | 本地计算（如技术指标） |

### 3.5 复权口径 `adjust`

| 值 | 含义 |
|---|---|
| `none` | 不复权 |
| `qfq` | 前复权 |
| `hfq` | 后复权 |

### 3.6 数据质量 `quality_flag`

| 值 | 含义 | 是否允许写缓存 |
|---|---|---|
| `live` | 实时数据 | 是 |
| `delayed` | 延迟数据 | 否 |
| `stale` | 过旧数据 | 否 |
| `fallback` | 来自备用源 | 是（需配合其他条件） |
| `fallback_low_confidence` | 低置信度 fallback | 否 |
| `estimated` | 估算值 | 否 |
| `computed` | 本地计算值 | 是 |

### 3.7 K 线周期 `period` / `interval`

| `period` | 可用的 `interval` |
|---|---|
| `1d` | `1m` / `5m` / `15m` / `30m` / `60m`（视源能力） |
| `5d` | `1m` / `5m` / `15m` / `30m` / `60m` |
| `1mo` | `1d` |
| `3mo` | `1d` |
| `6mo` | `1d` |
| `1y` | `1d` / `1wk` |
| `2y` | `1d` / `1wk` |
| `5y` | `1d` / `1wk` / `1mo` |
| `max` | `1d` / `1wk` / `1mo` |

---

## 四、工具定义

---

### 4.1 `get_realtime_quote`

**用途**：查询单只标的实时行情。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbol` | `string` | 是 | 用户输入，支持代码/中文名/英文名 |
| `market` | `string` | 否 | 优先市场 `CN` / `HK` / `US`，歧义时建议传入 |
| `bypass_cache` | `boolean` | 否 | 默认 `false`，`true` 时跳过缓存 |

**返回 data：**

```json
{
  "symbol": "000000.CN",
  "name": "贵州茅台",
  "market": "CN",
  "price": 1680.50,
  "change": -12.30,
  "change_pct": -0.73,
  "open": 1695.00,
  "high": 1700.00,
  "low": 1675.00,
  "prev_close": 1692.80,
  "volume": 2345678,
  "turnover": 3945623412.00,
  "timestamp": "2026-06-15T15:00:00+08:00",
  "instrument_type": "stock"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `symbol` | `string` | 内部标准 symbol |
| `name` | `string` | 标的名称 |
| `market` | `string` | 市场 |
| `price` | `float` | 最新价 |
| `change` | `float` | 涨跌额 |
| `change_pct` | `float` | 涨跌幅（%） |
| `open` | `float` | 开盘价 |
| `high` | `float` | 最高价 |
| `low` | `float` | 最低价 |
| `prev_close` | `float` | 前收盘价 |
| `volume` | `int` | 成交量 |
| `turnover` | `float` | 成交额 |
| `timestamp` | `string` | 行情时间 |
| `instrument_type` | `string` | `stock` / `index` / `etf` |

**错误码：** `INVALID_SYMBOL` / `SYMBOL_NOT_FOUND` / `AMBIGUOUS_SYMBOL` / `MARKET_CLOSED` / `TRADING_HALTED` / `SOURCE_TIMEOUT` / `FALLBACK_EXHAUSTED`

---

### 4.2 `get_price_history`

**用途**：查询标的的历史 K 线数据。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbol` | `string` | 是 | 同上 |
| `market` | `string` | 否 | 同上 |
| `period` | `string` | 否 | 默认 `1mo`，见 3.7 |
| `interval` | `string` | 否 | 默认 `1d`，见 3.7 |
| `adjust` | `string` | 否 | 默认 A股 `qfq` / 美股 `none` |

**返回 data：**

```json
{
  "symbol": "000000.CN",
  "market": "CN",
  "period": "1mo",
  "interval": "1d",
  "adjust": "qfq",
  "count": 22,
  "history": [
    {
      "date": "2026-06-15",
      "open": 1695.00,
      "high": 1700.00,
      "low": 1675.00,
      "close": 1680.50,
      "volume": 2345678,
      "turnover": 3945623412.00,
      "change_pct": -0.73
    }
  ]
}
```

**错误码：** 同上 + `INVALID_PERIOD` / `INVALID_INTERVAL` / `NO_DATA_AVAILABLE`

---

### 4.3 `get_batch_quotes`

**用途**：批量查询多只标的实时行情。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbols` | `array<string>` | 是 | 最多 20 个 |
| `bypass_cache` | `boolean` | 否 | 默认 `false` |

**返回 data：**

```json
{
  "quotes": [
    {
      "symbol": "000000.CN",
      "name": "贵州茅台",
      "price": 1680.50,
      "...": "...",
      "cache": { "hit": false, "...": "..." }
    }
  ],
  "failed_symbols": ["INVALID"],
  "summary": {
    "requested": 5,
    "success": 4,
    "failed": 1
  }
}
```

**key rule**：每个 quote item 独立附带各自的 `cache` 字段，按 symbol 独立缓存。

**错误码：** `TOO_MANY_SYMBOLS` / `PARTIAL_SOURCE_FAILURE` / `FALLBACK_EXHAUSTED`

---

### 4.4 `get_technical_indicators`

**用途**：计算指定标的的技术指标。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbol` | `string` | 是 | |
| `market` | `string` | 否 | |
| `period` | `string` | 否 | 默认 `3mo` |
| `interval` | `string` | 否 | 默认 `1d` |
| `indicators` | `array<string>` | 是 | 见下表 |
| `adjust` | `string` | 否 | 默认 A股 `qfq` |

**首版支持指标：**

| 指标 | `indicators` 值 | 说明 |
|---|---|---|
| 移动平均线 | `MA` | 返回 MA5 / MA10 / MA20 / MA60 |
| 指数移动平均 | `EMA` | 返回 EMA12 / EMA26 |
| 相对强弱指标 | `RSI` | 返回 RSI6 / RSI14 / RSI24 |
| MACD | `MACD` | 返回 DIF / DEA / MACD |
| 布林带 | `BOLL` | 返回 upper / middle / lower |
| KDJ | `KDJ` | 返回 K / D / J |

**返回 data：**

```json
{
  "symbol": "000000.CN",
  "adjusted": "qfq",
  "indicators": {
    "MA": { "MA5": 1690.20, "MA10": 1685.00, "MA20": 1670.50, "MA60": 1620.00 },
    "MACD": { "DIF": 12.50, "DEA": 10.20, "MACD": 2.30 },
    "RSI": { "RSI6": 58.2, "RSI14": 52.3, "RSI24": 48.1 }
  }
}
```

**meta.source**：返回 `computed`

---

### 4.5 `get_sector_boards`

**用途**：查询 A股行业/概念板块列表及表现。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | `string` | 否 | 默认 `industry`，可选 `concept` |

**返回 data：**

```json
{
  "sectors": [
    {
      "code": "BK0001",
      "name": "白酒",
      "type": "industry",
      "change_pct": 2.35,
      "leading_stock": "000000.CN",
      "leading_stock_name": "贵州茅台",
      "leading_stock_change_pct": 3.20,
      "stock_count": 18
    }
  ]
}
```

---

### 4.6 `get_capital_flow`

**用途**：查询 A股板块/市场层级资金流向。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scope` | `string` | 否 | 默认 `market`，可选 `sector` |

**返回 data（scope=market）：**

```json
{
  "scope": "market",
  "timestamp": "2026-06-15T15:00:00+08:00",
  "main_net_inflow": 1234567890.00,
  "super_large_net_inflow": 500000000.00,
  "large_net_inflow": 200000000.00,
  "medium_net_inflow": -100000000.00,
  "small_net_inflow": -600000000.00
}
```

---

### 4.7 `search_symbol`

**用途**：模糊搜索标的，返回可能匹配的标准化 symbol。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | `string` | 是 | 代码/中文名/英文名/ETF名/指数名 |
| `market` | `string` | 否 | 缩小范围 |
| `instrument_type` | `string` | 否 | `stock` / `etf` / `index` / `fund` |
| `max_results` | `int` | 否 | 默认 10 |

**返回 data：**

```json
{
  "results": [
    {
      "symbol": "000000.CN",
      "name": "贵州茅台",
      "display_name": "贵州茅台 (600519)",
      "market": "CN",
      "exchange": "SSE",
      "instrument_type": "stock",
      "currency": "CNY"
    }
  ]
}
```

**错误码：** `EMPTY_SCREEN_RESULT`

---

### 4.8 `get_source_status`

**用途**：查询当前各数据源的可用性状态。

**入参：** 无

**返回 data：**

```json
{
  "sources": [
    {
      "name": "tx",
      "status": "available",
      "market_coverage": ["CN"],
      "last_checked": "2026-06-15T14:35:00+08:00",
      "failures_in_window": 0,
      "degraded_since": null
    },
    {
      "name": "yfinance",
      "status": "degraded",
      "market_coverage": ["US", "HK"],
      "last_checked": "2026-06-15T14:35:00+08:00",
      "failures_in_window": 3,
      "degraded_since": "2026-06-15T14:30:00+08:00"
    }
  ]
}
```

**状态值：** `available` / `degraded` / `unavailable`

---

### 4.9 `get_trading_calendar`

**用途**：查询指定市场的交易日历。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `market` | `string` | 是 | |
| `from_date` | `string` | 否 | 默认今天 |
| `to_date` | `string` | 否 | 默认 30 天后 |

**返回 data：**

```json
{
  "market": "CN",
  "from_date": "2026-06-15",
  "to_date": "2026-07-15",
  "total_days": 31,
  "trading_days": 22,
  "holidays": [
    { "date": "2026-06-20", "name": "端午节", "type": "public_holiday" }
  ],
  "next_trading_day": "2026-06-16"
}
```

---

### 4.10 `clear_quote_cache`

**用途**：调用方主动清除本地价格缓存。

**入参：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scope` | `string` | 是 | `symbol` / `market` / `tool` / `all` |
| `market` | `string` | 否 | 配合 `scope=symbol` 或 `scope=market` |
| `symbol` | `string` | 否 | 配合 `scope=symbol` |
| `tool` | `string` | 否 | 配合 `scope=tool` |
| `dry_run` | `boolean` | 否 | 默认 `false` |

**返回 data：**

```json
{
  "scope": "symbol",
  "matched_count": 3,
  "deleted_count": 3,
  "dry_run": false,
  "filters": {
    "market": "CN",
    "symbol": "000000.CN",
    "tool": "get_realtime_quote"
  }
}
```

**约束：** `scope=all` 必须显式传入，不允许默认全清。

---

## 五、错误模型速查

详细定义见 `error-model.md`，以下为最常用项：

| code | type | retryable | 典型场景 |
|---|---|---|---|
| `SYMBOL_NOT_FOUND` | input_error | false | 找不到标的 |
| `AMBIGUOUS_SYMBOL` | input_error | false | 歧义，需指定 market |
| `INVALID_PERIOD` | input_error | false | period 不合法 |
| `MARKET_NOT_SUPPORTED` | business_error | false | 该市场未覆盖 |
| `TRADING_HALTED` | business_error | false | 停牌 |
| `MARKET_CLOSED` | business_error | false | 休市（提示型） |
| `SOURCE_TIMEOUT` | source_error | true | 源超时 |
| `SOURCE_RATE_LIMITED` | source_error | true | 被限流 |
| `FALLBACK_EXHAUSTED` | source_error | true | 所有备用源失败 |
| `NOT_IMPLEMENTED` | system_error | false | 功能未实现 |
