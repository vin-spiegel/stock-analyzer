"""MCP Tool 단위 테스트 - 성공 기준 S1, A1~A5, P1~P4"""
import json
import pytest


def _parse(result):
    """call_tool 결과에서 dict/list 파싱."""
    content = result.content if hasattr(result, "content") else result
    text = content[0].text if hasattr(content[0], "text") else str(content[0])
    return json.loads(text)


# ── S1: 4개 Tool 등록 확인 ────────────────────────────────────────────────────

async def test_tools_registered(mcp_client):
    tools = await mcp_client.list_tools()
    names = [t.name for t in tools]
    assert len(tools) == 4, f"Tool 수 불일치: {names}"
    assert "get_market_indicators" in names
    assert "analyze_stock_drops" in names
    assert "get_stock_price" in names
    assert "search_korean_stock" in names


# ── A1~A5: analyze_stock_drops ───────────────────────────────────────────────

async def test_analyze_basic(mcp_client):
    """A1: QQQ 기본 호출 성공, 필수 키 존재"""
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "QQQ",
        "drop_threshold_pct": 1.0,
        "days_after": 7,
        "start_date": "2022-01-01",
    })
    data = _parse(result)
    assert "total_signals" in data
    assert "win_rate" in data
    assert "strategy" in data


async def test_analyze_win_rate_range(mcp_client):
    """A2: win_rate 0~100 범위"""
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "SPY",
        "drop_threshold_pct": 1.0,
        "days_after": 5,
        "start_date": "2022-01-01",
    })
    data = _parse(result)
    if "win_rate" in data:
        assert 0 <= data["win_rate"] <= 100


async def test_analyze_korean_name(mcp_client):
    """A3: 한국 종목명 입력 정상 처리"""
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "삼성전자",
        "drop_threshold_pct": 1.0,
        "days_after": 3,
        "start_date": "2023-01-01",
    })
    data = _parse(result)
    assert "ticker" in data
    assert "005930.KS" in data.get("ticker", "")


async def test_analyze_invalid_ticker(mcp_client):
    """A4: 잘못된 티커 입력 시 error 필드 반환"""
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "INVALID_XXXX_ZZZ",
        "drop_threshold_pct": 1.0,
        "days_after": 3,
        "start_date": "2023-01-01",
    })
    data = _parse(result)
    assert "error" in data


async def test_analyze_strategy_values(mcp_client):
    """A5: strategy 값이 sell/wait/neutral 중 하나"""
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "QQQ",
        "drop_threshold_pct": 1.0,
        "days_after": 7,
        "start_date": "2022-01-01",
    })
    data = _parse(result)
    if "strategy" in data:
        assert data["strategy"] in ("sell", "wait", "neutral")


# ── P1~P4: get_stock_price ────────────────────────────────────────────────────

async def test_price_us_ticker(mcp_client):
    """P1: 미국 주식 티커 조회 성공"""
    result = await mcp_client.call_tool("get_stock_price", {"ticker_or_name": "AAPL"})
    data = _parse(result)
    assert "error" not in data, f"에러 발생: {data.get('error')}"
    assert data["current_price"] > 0


async def test_price_korean_name(mcp_client):
    """P2: 한국 종목명으로 조회 성공"""
    result = await mcp_client.call_tool("get_stock_price", {"ticker_or_name": "삼성전자"})
    data = _parse(result)
    assert "error" not in data, f"에러 발생: {data.get('error')}"
    assert data["current_price"] > 0
    assert data["currency"] == "KRW"


async def test_price_korean_code(mcp_client):
    """P3: 6자리 코드로 조회 성공"""
    result = await mcp_client.call_tool("get_stock_price", {"ticker_or_name": "005930"})
    data = _parse(result)
    assert "error" not in data, f"에러 발생: {data.get('error')}"
    assert data["current_price"] > 0


async def test_price_invalid_ticker(mcp_client):
    """P4: 잘못된 종목 에러 처리"""
    result = await mcp_client.call_tool("get_stock_price", {"ticker_or_name": "ZZZZZZZZZ"})
    data = _parse(result)
    assert "error" in data
