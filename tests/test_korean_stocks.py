"""한국 주식 검색 테스트 - 성공 기준 K1~K4, M1~M2"""
import json
import pytest


def _parse(result):
    if hasattr(result, "data") and result.data is not None:
        return result.data
    content = result.content if hasattr(result, "content") else result
    if not content:
        return []
    text = content[0].text if hasattr(content[0], "text") else str(content[0])
    return json.loads(text)


# ── K1~K4: search_korean_stock ────────────────────────────────────────────────

async def test_search_samsung(mcp_client):
    """K1: '삼성' 검색 시 삼성전자(005930) 포함"""
    result = await mcp_client.call_tool("search_korean_stock", {"query": "삼성"})
    data = _parse(result)
    assert isinstance(data, list)
    codes = [item["code"] for item in data]
    assert "005930" in codes


async def test_search_result_structure(mcp_client):
    """K2: 각 결과에 ticker, name, code 필드 존재"""
    result = await mcp_client.call_tool("search_korean_stock", {"query": "현대"})
    data = _parse(result)
    assert len(data) > 0
    for item in data:
        assert "ticker" in item
        assert "name" in item
        assert "code" in item
        assert item["ticker"].endswith(".KS")


async def test_search_no_match(mcp_client):
    """K3: 매칭 없는 검색어 → 빈 list"""
    result = await mcp_client.call_tool("search_korean_stock", {"query": "존재하지않는회사XYZ"})
    data = _parse(result)
    assert data == []


async def test_search_max_results(mcp_client):
    """K4: 결과 최대 20개 제한"""
    result = await mcp_client.call_tool("search_korean_stock", {"query": "한"})
    data = _parse(result)
    assert len(data) <= 20


# ── M1~M2: get_market_indicators 구조 검증 ────────────────────────────────────

async def test_market_indicators_keys(mcp_client):
    """M1: 7개 지표 키 모두 존재"""
    result = await mcp_client.call_tool("get_market_indicators", {})
    data = _parse(result)
    required_keys = [
        "fear_greed_index", "vix", "put_call_ratio",
        "rsi_sp500", "qqq_vs_200ma", "buffett_indicator", "usd_krw",
    ]
    for key in required_keys:
        assert key in data, f"누락된 키: {key}"


async def test_market_indicators_structure(mcp_client):
    """M2: 각 지표에 value/signal 또는 rate/signal 필드 포함"""
    result = await mcp_client.call_tool("get_market_indicators", {})
    data = _parse(result)
    for key in ["fear_greed_index", "vix", "put_call_ratio", "rsi_sp500"]:
        item = data[key]
        assert "signal" in item, f"{key}에 signal 없음"
        assert item["signal"] in ("bullish", "bearish", "neutral")
    assert "signal" in data["usd_krw"]
    assert "timestamp" in data
