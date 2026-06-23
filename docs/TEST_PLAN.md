# 테스트 계획 & 성공 기준

**버전**: 1.0  
**작성일**: 2026-06-24  

---

## 1. 테스트 스택

| 도구 | 역할 | 버전 |
|------|------|------|
| `pytest` | 테스트 러너 | >=8.0 |
| `pytest-asyncio` | async 테스트 지원 | >=0.24 |
| `fastmcp` | MCP Client (인메모리 테스트) | >=2.3.0 |
| `pytest-httpx` | HTTP 요청 목킹 (스크래핑 테스트용) | >=0.34 |

### 설치

```bash
pip install pytest pytest-asyncio pytest-httpx fastmcp
```

### `pyproject.toml` 설정 (asyncio_mode 자동)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 2. 테스트 구조

```
stock-analyzer/
└── tests/
    ├── __init__.py
    ├── conftest.py          # pytest fixture (MCP Client)
    ├── test_tools.py        # Tool 단위 테스트
    ├── test_market.py       # 시장 지표 함수 테스트
    ├── test_health.py       # HTTP 헬스체크 테스트
    └── test_korean_stocks.py # 한국 주식 검색 테스트
```

---

## 3. 성공 기준 (Definition of Done)

### 3-1. MCP 서버 기본

| ID | 기준 | 테스트 방법 |
|----|------|-------------|
| S1 | 서버 기동 시 4개 Tool이 등록됨 | `list_tools()` 결과 count == 4 |
| S2 | `/health` 엔드포인트 200 응답 | `GET /health` → `{"status": "ok"}` |
| S3 | `/mcp` 엔드포인트 접근 가능 | MCP Client 연결 성공 |

### 3-2. `get_market_indicators`

| ID | 기준 | 테스트 방법 |
|----|------|-------------|
| M1 | 7개 지표 키 모두 존재 | 응답 dict에 fear_greed_index, vix, put_call_ratio, rsi_sp500, qqq_vs_200ma, buffett_indicator, usd_krw 키 확인 |
| M2 | 각 지표에 value, signal 필드 포함 | 타입 및 키 검증 |
| M3 | 데이터 조회 실패 시 null 반환 (graceful degradation) | 스크래핑 실패 목킹 후 null 확인 |
| M4 | 응답 시간 10초 이내 | `time.time()` 측정 |

### 3-3. `analyze_stock_drops`

| ID | 기준 | 테스트 방법 |
|----|------|-------------|
| A1 | QQQ 기본값 호출 성공 | `ticker="QQQ"` → 응답에 total_signals, win_rate, strategy 포함 |
| A2 | win_rate 0~100 범위 | 숫자 범위 검증 |
| A3 | 한국 종목명 입력 정상 처리 | `ticker="삼성전자"` → 005930.KS 변환 후 분석 성공 |
| A4 | 잘못된 티커 입력 시 에러 메시지 반환 | `ticker="INVALID_XXXX"` → error 필드 포함 |
| A5 | strategy 값이 "sell"/"wait"/"neutral" 중 하나 | enum 검증 |

### 3-4. `get_stock_price`

| ID | 기준 | 테스트 방법 |
|----|------|-------------|
| P1 | 미국 주식 티커 조회 성공 | `ticker_or_name="AAPL"` → current_price > 0 |
| P2 | 한국 종목명으로 조회 성공 | `ticker_or_name="삼성전자"` → current_price > 0, currency == "KRW" |
| P3 | 6자리 코드로 조회 성공 | `ticker_or_name="005930"` → 삼성전자 데이터 |
| P4 | 잘못된 종목 에러 처리 | `ticker_or_name="ZZZZZZZ"` → error 필드 반환 |

### 3-5. `search_korean_stock`

| ID | 기준 | 테스트 방법 |
|----|------|-------------|
| K1 | "삼성" 검색 시 삼성전자 포함 결과 반환 | 결과 list에 005930 포함 확인 |
| K2 | 각 결과에 ticker, name, code 필드 존재 | 구조 검증 |
| K3 | 매칭 없는 검색어 → 빈 list 반환 | `query="존재하지않는회사"` → `[]` |
| K4 | 결과 최대 20개 제한 | len(results) <= 20 |

### 3-6. 배포 (Railway)

| ID | 기준 | 검증 방법 |
|----|------|----------|
| D1 | Railway MCP 서비스 배포 성공 | 대시보드 상태 Active |
| D2 | 공개 URL 헬스체크 통과 | `curl https://fast-stock.up.railway.app/health` → 200 |
| D3 | Claude Code에서 `claude mcp add` 성공 | Tool 목록에 4개 확인 |
| D4 | Claude.ai Connector 등록 성공 | Settings > Connectors 활성화 확인 |

---

## 4. 테스트 예시 코드

### `tests/conftest.py`

```python
import pytest
from fastmcp import Client

@pytest.fixture
async def mcp_client():
    from mcp_server import mcp
    async with Client(mcp) as client:
        yield client
```

### `tests/test_tools.py`

```python
async def test_tools_registered(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = [t.name for t in tools]
    assert len(tools) == 4
    assert "get_market_indicators" in tool_names
    assert "analyze_stock_drops" in tool_names
    assert "get_stock_price" in tool_names
    assert "search_korean_stock" in tool_names

async def test_search_korean_stock(mcp_client):
    result = await mcp_client.call_tool("search_korean_stock", {"query": "삼성"})
    data = result[0].text  # JSON 파싱
    assert any(item["code"] == "005930" for item in data)

async def test_analyze_stock_drops_basic(mcp_client):
    result = await mcp_client.call_tool("analyze_stock_drops", {
        "ticker": "QQQ",
        "drop_threshold_pct": 2.0,
        "days_after": 7
    })
    data = result[0].text
    assert "total_signals" in data
    assert "win_rate" in data
    assert 0 <= data["win_rate"] <= 100

async def test_get_stock_price_korean_name(mcp_client):
    result = await mcp_client.call_tool("get_stock_price", {
        "ticker_or_name": "삼성전자"
    })
    data = result[0].text
    assert data["current_price"] > 0
    assert data["currency"] == "KRW"
```

---

## 5. 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일
pytest tests/test_tools.py

# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=mcp_server tests/
```

---

## 6. CI 연동 (향후)

Railway 배포 전 자동 테스트 실행을 위해 GitHub Actions에 추가 예정:

```yaml
# .github/workflows/test.yml (향후)
- name: Run tests
  run: pytest tests/ -v
```
