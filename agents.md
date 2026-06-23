# Stock Analyzer MCP Server

주식/지수/코인 시장 분석 도구를 제공하는 MCP 서버입니다.
미국 주식, 한국 주식(약 2,000종목), 시장 심리 지표, N일 후 하락 분석 기능을 포함합니다.

**MCP Server URL**: `https://mcp-server-production-8fc7.up.railway.app/mcp`

---

## 빠른 설치 (Claude Code)

터미널에서 아래 명령어 하나로 설치됩니다:

```bash
claude mcp add --transport http stock-analyzer https://mcp-server-production-8fc7.up.railway.app/mcp
```

설치 확인:

```bash
claude mcp get stock-analyzer
```

---

## 플랫폼별 설치 방법

### Claude Code (CLI)

```bash
# 현재 프로젝트에만 적용 (기본값)
claude mcp add --transport http stock-analyzer https://mcp-server-production-8fc7.up.railway.app/mcp

# 모든 프로젝트에 적용
claude mcp add --transport http --scope user stock-analyzer https://mcp-server-production-8fc7.up.railway.app/mcp

# 팀 전체 공유 (.mcp.json에 저장)
claude mcp add --transport http --scope project stock-analyzer https://mcp-server-production-8fc7.up.railway.app/mcp
```

### .mcp.json (프로젝트 공유)

프로젝트 루트에 `.mcp.json` 파일을 생성하거나 추가:

```json
{
  "mcpServers": {
    "stock-analyzer": {
      "type": "http",
      "url": "https://mcp-server-production-8fc7.up.railway.app/mcp"
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json` 파일에 추가:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stock-analyzer": {
      "type": "http",
      "url": "https://mcp-server-production-8fc7.up.railway.app/mcp"
    }
  }
}
```

### Claude.ai Custom Connector

1. [claude.ai](https://claude.ai) → Settings → Connectors → **Add connector**
2. URL 입력: `https://mcp-server-production-8fc7.up.railway.app/mcp`
3. 인증: 없음
4. **Save** 클릭

---

## 제공 도구 (Tools)

### `get_market_indicators`

현재 시장 심리 지표를 전부 조회합니다.

**파라미터**: 없음

**반환 데이터**:
- 공포&탐욕 지수 (Fear & Greed Index)
- VIX 변동성 지수
- Put/Call 비율
- RSI (S&P500)
- QQQ vs 200일 이동평균
- 버핏 지수 (시가총액/GDP)
- 원달러 환율

**예시 질문**:
> "오늘 시장 심리 지표 전체 요약해줘"
> "지금 매수 타이밍이야 매도 타이밍이야?"

---

### `analyze_stock_drops`

특정 종목이 X% 이상 하락한 날, N일 후 가격 방향을 통계적으로 분석합니다.

**파라미터**:
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `ticker` | string | 필수 | 종목 티커, 한국 종목명, 또는 6자리 코드 |
| `drop_threshold_pct` | float | 1.0 | 하락 기준 퍼센트 |
| `days_after` | int | 3 | 며칠 후를 볼지 (1/3/5/7/14/30/90/180/365) |
| `start_date` | string | "2020-01-01" | 분석 시작일 (YYYY-MM-DD) |

**예시 질문**:
> "QQQ가 3% 이상 떨어진 날 30일 후 회복 확률이 어떻게 돼?"
> "삼성전자가 2% 이상 하락한 날 기다리는 게 나을까 바로 팔아야 할까?"
> "AAPL 1% 하락 후 1주일 뒤 통계 알려줘"

---

### `get_stock_price`

미국 주식, 한국 주식, 인덱스, 코인의 현재가와 기본 정보를 조회합니다.

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| `ticker_or_name` | string | 티커(QQQ, BTC-USD), 한국 종목명(삼성전자), 또는 6자리 코드(005930) |

**예시 질문**:
> "삼성전자 지금 주가 얼마야?"
> "BTC-USD 현재가 알려줘"
> "SPY, QQQ, IWM 현재가 비교해줘"

---

### `search_korean_stock`

한국 주식 종목명을 부분 검색합니다.

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| `query` | string | 검색할 회사명 키워드 |

**예시 질문**:
> "SK 관련 한국 주식 종목 목록 알려줘"
> "현대로 시작하는 종목들 찾아줘"

---

## 지원 종목

- **미국 주식**: yfinance 지원 전체 티커 (QQQ, SPY, AAPL, TSLA 등)
- **한국 주식**: KRX 상장 약 2,000종목 (종목명 또는 6자리 코드로 검색)
- **인덱스**: ^GSPC, ^IXIC, ^DJI, ^KS11 등
- **코인**: BTC-USD, ETH-USD 등 yfinance 지원 심볼

---

## 헬스체크

서버 상태 확인:

```bash
curl https://mcp-server-production-8fc7.up.railway.app/health
```

정상 응답: `{"status": "ok"}`

---

## 관련 링크

- **Streamlit 대시보드**: https://stock-analyzer.up.railway.app
- **GitHub**: https://github.com/ccosigi/stock-analyzer
- **MCP 서버**: https://mcp-server-production-8fc7.up.railway.app/mcp
