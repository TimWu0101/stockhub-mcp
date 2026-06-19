"""SymbolResolver: user input → internal standard symbol.

Implements three-layer symbol standardization:
  Layer 1 – User input:  "茅台" / "600519" / "AAPL"
  Layer 2 – Internal:     "CN:600519" / "US:AAPL"
  Layer 3 – Source:        handled by SymbolNormalizer
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from market_data_mcp.enums import InstrumentType, Market


# ---------------------------------------------------------------------------
# StandardSymbol
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StandardSymbol:
    """Internal standard representation of a financial instrument.

    Format: ``"{market}:{code}"``, e.g. ``"CN:600519"``.
    """

    market: Market
    code: str

    def to_internal(self) -> str:
        """Return the canonical string: ``"CN:600519"``."""
        return f"{self.market.value}:{self.code}"

    @classmethod
    def from_internal(cls, s: str) -> StandardSymbol:
        """Parse a canonical string like ``"CN:600519"`` back into a StandardSymbol."""
        market_str, code = s.split(":", 1)
        return cls(market=Market(market_str), code=code)


@dataclass
class ResolveResult:
    """Outcome of symbol resolution.

    If *resolved* is True, *symbol* holds the single match.
    If *resolved* is False, *candidates* contains the ambiguity list.
    """

    resolved: bool = False
    symbol: Optional[StandardSymbol] = None
    candidates: list[ResolveCandidate] = field(default_factory=list)


@dataclass
class ResolveCandidate:
    """A possible match returned when the input is ambiguous."""

    symbol: StandardSymbol
    name: str = ""
    instrument_type: InstrumentType = InstrumentType.STOCK
    display_name: str = ""
    exchange: str = ""
    currency: str = ""


# ---------------------------------------------------------------------------
# Market detection helpers
# ---------------------------------------------------------------------------

# Regex patterns for code-based market detection.
_RE_CN_CODE = re.compile(r"^(sh|sz|SH|SZ)?(\d{6})$")
_RE_HK_CODE = re.compile(r"^(\d{1,5})$")
_RE_US_CODE = re.compile(r"^[A-Za-z]{1,5}(\.[A-Z]{1,2})?$")
_RE_CN_CODE_WITH_PREFIX = re.compile(r"^(sh|sz|SH|SZ)(\d{6})$")

# Well-known stocks for fuzzy name matching (首版硬编码常见标的).
_KNOWN_SYMBOLS: dict[Market, list[dict]] = {
    Market.CN: [
        {"code": "600519", "name": "贵州茅台", "pinyin": "guizhoumaotai", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000858", "name": "五粮液", "pinyin": "wuliangye", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "000001", "name": "平安银行", "pinyin": "pinganyinxing", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "600036", "name": "招商银行", "pinyin": "zhaoshangyinxing", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000002", "name": "万科A", "pinyin": "wankea", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "601318", "name": "中国平安", "pinyin": "zhongguopingan", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "600900", "name": "长江电力", "pinyin": "changjiangdianli", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "300750", "name": "宁德时代", "pinyin": "ningdeshidai", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "002594", "name": "比亚迪", "pinyin": "biyadi", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "688981", "name": "中芯国际", "pinyin": "zhongxinguoji", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "601398", "name": "工商银行", "pinyin": "gongshangyinxing", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000651", "name": "格力电器", "pinyin": "gelidianqi", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "002415", "name": "海康威视", "pinyin": "haikangweishi", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "600276", "name": "恒瑞医药", "pinyin": "hengruiyiyao", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "601888", "name": "中国中免", "pinyin": "zhongguozhongmian", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000333", "name": "美的集团", "pinyin": "meidijituan", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "600030", "name": "中信证券", "pinyin": "zhongxinzhengquan", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "600887", "name": "伊利股份", "pinyin": "yiligufen", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000725", "name": "京东方A", "pinyin": "jingdongfanga", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "603259", "name": "药明康德", "pinyin": "yaomingkangde", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000063", "name": "中兴通讯", "pinyin": "zhongxingtongxun", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "600809", "name": "山西汾酒", "pinyin": "shanxifenjiu", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "600585", "name": "海螺水泥", "pinyin": "hailuoshuini", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "601166", "name": "兴业银行", "pinyin": "xingyeyinxing", "exchange": "SSE", "type": InstrumentType.STOCK},
        {"code": "000568", "name": "泸州老窖", "pinyin": "luzhoulaojiao", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "000776", "name": "广发证券", "pinyin": "guangfazhengquan", "exchange": "SZSE", "type": InstrumentType.STOCK},
        {"code": "510050", "name": "上证50ETF", "pinyin": "shangzheng50etf", "exchange": "SSE", "type": InstrumentType.ETF},
        {"code": "510300", "name": "沪深300ETF", "pinyin": "hushen300etf", "exchange": "SSE", "type": InstrumentType.ETF},
        {"code": "159915", "name": "创业板ETF", "pinyin": "chuangyebanyetf", "exchange": "SZSE", "type": InstrumentType.ETF},
        {"code": "000300", "name": "沪深300", "pinyin": "hushen300", "exchange": "SSE", "type": InstrumentType.INDEX},
        {"code": "000001", "name": "上证指数", "pinyin": "shangzhengzhishu", "exchange": "SSE", "type": InstrumentType.INDEX},
        {"code": "399001", "name": "深证成指", "pinyin": "shenzhenchengzhi", "exchange": "SZSE", "type": InstrumentType.INDEX},
        {"code": "399006", "name": "创业板指", "pinyin": "chuangyebanzhi", "exchange": "SZSE", "type": InstrumentType.INDEX},
    ],
    Market.HK: [
        {"code": "00700", "name": "腾讯控股", "pinyin": "tengxunkonggu", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "09988", "name": "阿里巴巴-SW", "pinyin": "alibab", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "09999", "name": "网易-S", "pinyin": "wangyi", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "01810", "name": "小米集团-W", "pinyin": "xiaomijituan", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "00388", "name": "香港交易所", "pinyin": "xianggangjiaoyisuo", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "02020", "name": "安踏体育", "pinyin": "antatiyu", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "03690", "name": "美团-W", "pinyin": "meituan", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "09618", "name": "京东集团-SW", "pinyin": "jingdongjituan", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "09888", "name": "百度集团-SW", "pinyin": "baidujituan", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "01211", "name": "比亚迪股份", "pinyin": "biyadigufen", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "02318", "name": "中国平安", "pinyin": "zhongguopingan", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "00941", "name": "中国移动", "pinyin": "zhongguoyidong", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "00005", "name": "汇丰控股", "pinyin": "huifengkonggu", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "01299", "name": "友邦保险", "pinyin": "youbangbaoxian", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "02269", "name": "药明生物", "pinyin": "yaomingshengwu", "exchange": "HKEX", "type": InstrumentType.STOCK},
        {"code": "02800", "name": "盈富基金", "pinyin": "yingfujijin", "exchange": "HKEX", "type": InstrumentType.ETF},
        {"code": "800000", "name": "恒生指数", "pinyin": "hengshengzhishu", "exchange": "HKEX", "type": InstrumentType.INDEX},
    ],
    Market.US: [
        {"code": "AAPL", "name": "Apple Inc.", "pinyin": "apple", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "GOOGL", "name": "Alphabet Inc.", "pinyin": "google", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "MSFT", "name": "Microsoft Corp.", "pinyin": "microsoft", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "AMZN", "name": "Amazon.com, Inc.", "pinyin": "amazon", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "META", "name": "Meta Platforms, Inc.", "pinyin": "meta", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "TSLA", "name": "Tesla, Inc.", "pinyin": "tesla", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "NVDA", "name": "NVIDIA Corp.", "pinyin": "nvidia", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "BRK.B", "name": "Berkshire Hathaway Inc.", "pinyin": "berkshire", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "JPM", "name": "JPMorgan Chase & Co.", "pinyin": "jpmorgan", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "V", "name": "Visa Inc.", "pinyin": "visa", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "JNJ", "name": "Johnson & Johnson", "pinyin": "johnson", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "WMT", "name": "Walmart Inc.", "pinyin": "walmart", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "BAC", "name": "Bank of America Corp.", "pinyin": "bofa", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "DIS", "name": "The Walt Disney Company", "pinyin": "disney", "exchange": "NYSE", "type": InstrumentType.STOCK},
        {"code": "NFLX", "name": "Netflix, Inc.", "pinyin": "netflix", "exchange": "NASDAQ", "type": InstrumentType.STOCK},
        {"code": "SPY", "name": "SPDR S&P 500 ETF", "pinyin": "spy", "exchange": "NYSE", "type": InstrumentType.ETF},
        {"code": "QQQ", "name": "Invesco QQQ Trust", "pinyin": "qqq", "exchange": "NASDAQ", "type": InstrumentType.ETF},
        {"code": "^GSPC", "name": "S&P 500", "pinyin": "sp500", "exchange": "NYSE", "type": InstrumentType.INDEX},
        {"code": "^DJI", "name": "Dow Jones Industrial Average", "pinyin": "dowjones", "exchange": "NYSE", "type": InstrumentType.INDEX},
        {"code": "^IXIC", "name": "NASDAQ Composite", "pinyin": "nasdaq", "exchange": "NASDAQ", "type": InstrumentType.INDEX},
    ],
}


def _detect_market_by_code(user_input: str) -> Optional[Market]:
    """Try to determine market purely from code patterns.

    Returns:
        A single Market if unambiguously detected, or None.
    """
    stripped = user_input.strip()

    # Check for CN code patterns: optional sh/sz prefix + 6 digits
    m = _RE_CN_CODE.match(stripped)
    if m and m.group(2):
        return Market.CN

    # Check for HK code patterns: 1-5 digits (but not matching CN 6-digit)
    m = _RE_HK_CODE.match(stripped)
    if m and not _RE_CN_CODE.match(stripped):
        return Market.HK

    # Check for US code patterns: alphabetic ticker
    m = _RE_US_CODE.match(stripped)
    if m:
        return Market.US

    return None


def _strip_cn_code(code: str) -> str:
    """Remove exchange prefix from a CN code, returning the 6-digit core."""
    m = _RE_CN_CODE_WITH_PREFIX.match(code)
    if m:
        return m.group(2)
    return code


# ---------------------------------------------------------------------------
# SymbolResolver
# ---------------------------------------------------------------------------


class SymbolResolver:
    """Resolve user input to a StandardSymbol.

    Supports:
    - Code-based: ``"600519"``, ``"sh600519"``, ``"AAPL"``, ``"00700"``
    - Name-based: ``"贵州茅台"``, ``"Apple"``
    - Pinyin: ``"maotai"``, ``"guizhoumaotai"``
    """

    def __init__(self) -> None:
        """Initialise the resolver with the hardcoded symbol database."""
        self._db: dict[Market, list[dict]] = _KNOWN_SYMBOLS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        user_input: str,
        preferred_market: Optional[Market] = None,
        instrument_type: Optional[InstrumentType] = None,
    ) -> ResolveResult:
        """Resolve user input to a single StandardSymbol or an ambiguity list.

        Args:
            user_input: Raw input – code, name, or pinyin.
            preferred_market: Narrow resolution to this market when supplied.
            instrument_type: Filter candidates by instrument type.

        Returns:
            *ResolveResult* – check ``.resolved``; if True use ``.symbol``,
            otherwise present ``.candidates`` to the caller.
        """
        user_input = user_input.strip()
        if not user_input:
            return ResolveResult(resolved=False)

        # --- Step 1: code-based detection ---
        detected_market = _detect_market_by_code(user_input)

        if detected_market is not None:
            # Pure code input – unambiguous market
            code = _strip_cn_code(user_input) if detected_market == Market.CN else user_input.rstrip().upper()
            symbol = StandardSymbol(market=detected_market, code=code)
            return ResolveResult(resolved=True, symbol=symbol)

        # --- Step 2: name / pinyin fuzzy match ---
        search_markets: list[Market]
        if preferred_market:
            search_markets = [preferred_market]
        else:
            search_markets = [Market.CN, Market.HK, Market.US]

        candidates: list[ResolveCandidate] = []

        query_lower = user_input.lower().replace(" ", "")
        query_pinyin = query_lower  # pinyin is already lowercase

        for market in search_markets:
            for entry in self._db.get(market, []):
                if instrument_type and entry["type"] != instrument_type:
                    continue

                # Match by exact code
                if entry["code"] == user_input:
                    candidates.append(self._build_candidate(market, entry))
                    continue

                # Match by name (substring)
                if query_lower in entry["name"].lower():
                    candidates.append(self._build_candidate(market, entry))
                    continue

                # Match by pinyin (substring)
                if query_pinyin in entry.get("pinyin", ""):
                    candidates.append(self._build_candidate(market, entry))
                    continue

        if len(candidates) == 1:
            return ResolveResult(
                resolved=True,
                symbol=candidates[0].symbol,
                candidates=candidates,
            )
        elif len(candidates) > 1:
            return ResolveResult(resolved=False, candidates=candidates)

        return ResolveResult(resolved=False)

    def search(
        self,
        query: str,
        market: Optional[Market] = None,
        instrument_type: Optional[InstrumentType] = None,
        max_results: int = 10,
    ) -> list[ResolveCandidate]:
        """Fuzzy-search for matching symbols.

        Args:
            query: Search string (code / name / pinyin).
            market: Narrow to this market.
            instrument_type: Filter by instrument type.
            max_results: Maximum number of results.

        Returns:
            Ordered list of candidates (best match first).
        """
        result = self.resolve(query, preferred_market=market, instrument_type=instrument_type)
        candidates = result.candidates

        if result.resolved and result.symbol:
            # Insert the exact match at the front
            exact = ResolveCandidate(
                symbol=result.symbol,
                name="",
                instrument_type=InstrumentType.STOCK,
                display_name=result.symbol.to_internal(),
            )
            candidates = [exact] + [c for c in candidates if c.symbol != result.symbol]

        return candidates[:max_results]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_candidate(market: Market, entry: dict) -> ResolveCandidate:
        symbol = StandardSymbol(market=market, code=entry["code"])
        name: str = entry["name"]
        code: str = entry["code"]
        exchange: str = entry.get("exchange", "")
        inst_type: InstrumentType = entry.get("type", InstrumentType.STOCK)
        currency: str = "CNY" if market == Market.CN else ("HKD" if market == Market.HK else "USD")

        return ResolveCandidate(
            symbol=symbol,
            name=name,
            instrument_type=inst_type,
            display_name=f"{name} ({code})",
            exchange=exchange,
            currency=currency,
        )
