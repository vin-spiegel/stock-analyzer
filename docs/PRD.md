# PRD: Stock Analyzer MCP Server & Claude Custom Connector

**버전**: 1.0  
**작성일**: 2026-06-24  
**프로젝트**: [stock-analyzer](https://github.com/ccosigi/stock-analyzer)  

---

## 1. 배경 및 목적

### 현재 상태
`stock-analyzer`는 Streamlit 기반 웹 대시보드로, 다음 두 가지 핵심 기능을 제공한다:

| 기능 | 설명 |
|------|------|
| 시장 감정 탭 | 공포&탐욕 지수, VIX, PCI, RSI(S&P500), QQQ 200MA, 버핏 지수, 원달러 환율 실시간 표시 |
| N일 후 분석 탭 | 특정 종목이 X% 이상 하락한 날 기준 N일 후 가격 방향 통계 분석 |

데이터 소스: `yfinance` (시세), 웹 스크래핑 (FGI, PCI, 버핏지수)  
지원 종목: 미국 주식 전체 티커 + 한국 주식 약 2,000여 종목 (종목명/코드 검색)

### 문제
현재 서비스는 브라우저에서만 접근 가능하다. Claude, GPT 등 AI 어시스턴트에서 직접 주식 데이터를 조회하거나 분석을 요청할 수 없다.

### 목표
1. **MCP 서버 구축**: 기존 분석 로직을 Claude Code 및 Claude Desktop에서 직접 호출 가능한 MCP 도구로 노출
2. **Claude Custom Connector**: Claude.ai 웹/모바일에서 Remote MCP를 통해 연결 가능한 HTTP 서버 배포
3. **Railway 배포**: 기존 Streamlit 서비스와 병렬로 MCP 서버를 Railway에 별도 서비스로 배포

---

## 2. 사용자 및 사용 시나리오

### 대상 사용자
- Claude Code/Desktop 사용자 (개발자, 투자자)
- Claude.ai 웹/모바일 Custom Connector 사용자

### 핵심 시나리오

**시나리오 A - Claude Code에서 직접 분석**
```
사용자: "QQQ가 3% 이상 하락한 날 30일 후 회복률이 어떻게 돼?"
Claude: [analyze_stock_drops 호출] → 통계 결과 + 전략 제안 반환
```

**시나리오 B - 시장 브리핑**
```
사용자: "오늘 시장 상황 요약해줘"
Claude: [get_market_indicators 호출] → FGI, VIX, RSI, 버핏지수 등 종합 해석
```

**시나리오 C - 종목 검색**
```
사용자: "삼성전자 티커가 뭐야? 최근 3개월 주가는?"
Claude: [search_korean_stock → get_stock_price 호출] → 티커 + 현재가 반환
```

**시나리오 D - Claude.ai Connector 등록**
```
Settings > Connectors > Add → MCP 서버 URL 입력 → 인증 없이 바로 연결
→ 이후 Claude.ai 대화에서 주식 도구 자동 사용 가능
```

---

## 3. 기술 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                  Railway                            │
│                                                     │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Service 1      │    │  Service 2              │ │
│  │  Streamlit App  │    │  MCP Server             │ │
│  │  (app.py)       │    │  (mcp_server.py)        │ │
│  │  Port: 8080     │    │  Port: 8000             │ │
│  │                 │    │  /mcp endpoint          │ │
│  └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
   브라우저 접근              Claude Code / Desktop /
   (기존 서비스)              Claude.ai Custom Connector
```

### MCP 서버 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | **FastMCP 3.x** (`pip install fastmcp`) | 공식 MCP SDK 위에서 동작, Railway 공식 템플릿 존재, Python 3.10+ 지원 |
| Transport | **Streamable HTTP** | Claude.ai Remote MCP 표준 (SSE는 점진적 폐지 예정) |
| 인증 | **없음 (초기)** | 빠른 연결 검증 우선; 이후 Bearer token 추가 가능 |
| 엔드포인트 | `POST /mcp` | FastMCP 기본값 |
| 헬스체크 | `GET /health` | Railway healthcheck용 |

### 데이터 흐름

```
Claude 요청
    │
    ▼
FastMCP (mcp_server.py)
    │  @mcp.tool() 데코레이터로 등록된 함수 호출
    │
    ├── yfinance API (시세 데이터)
    ├── requests + BeautifulSoup (FGI, PCI 스크래핑)
    └── stock_library.py (한국 주식 DB)
    │
    ▼
JSON 결과 반환
```

---

## 4. MCP 도구 명세

### Tool 1: `get_market_indicators`
```python
def get_market_indicators() -> dict
```
**설명**: 현재 시장 심리 지표 전체를 한 번에 조회  
**반환 예시**:
```json
{
  "fear_greed_index": { "value": 72, "label": "탐욕적", "signal": "매도 신호" },
  "vix": { "value": 18.3, "label": "변동성 중간", "signal": "중립" },
  "put_call_ratio": { "value": 0.72, "label": "중립적", "signal": "중립" },
  "rsi_sp500": { "value": 61.2, "label": "중립", "signal": "중립" },
  "qqq_vs_200ma": { "current": 487.2, "sma200": 451.3, "diff_pct": 7.96, "signal": "상승 추세" },
  "buffett_indicator": { "value": 186.4, "label": "심각한 고평가", "signal": "강력한 매도 신호" },
  "usd_krw": { "rate": 1378.5, "change": -3.2, "change_pct": -0.23 },
  "timestamp": "2026-06-24T14:30:00"
}
```

### Tool 2: `analyze_stock_drops`
```python
def analyze_stock_drops(
    ticker: str,
    drop_threshold_pct: float = 1.0,
    days_after: int = 3,
    start_date: str = "2020-01-01"
) -> dict
```
**설명**: 특정 종목이 X% 이상 하락한 날 기준 N일 후 통계 분석  
**파라미터**:
- `ticker`: 종목 티커 또는 한국 회사명 (예: `QQQ`, `삼성전자`, `005930`)
- `drop_threshold_pct`: 하락 기준 퍼센트 (기본 1.0%)
- `days_after`: 며칠 후를 분석할지 (기본 3일, 지원: 1/3/5/7/14/30/90/180/365)
- `start_date`: 분석 시작일 (YYYY-MM-DD)

**반환 예시**:
```json
{
  "ticker": "QQQ",
  "total_signals": 142,
  "win_count": 58,
  "lose_count": 84,
  "win_rate": 40.8,
  "avg_change_pct": 1.23,
  "strategy": "wait",
  "recommendation": "QQQ 종목이 1.0% 이상 하락해도 3일 정도는 기다려보세요.",
  "period": { "start": "2020-01-01", "end": "2026-06-24" }
}
```

### Tool 3: `get_stock_price`
```python
def get_stock_price(ticker_or_name: str) -> dict
```
**설명**: 미국/한국 주식, 인덱스, 코인 현재가 및 기본 정보 조회  
**반환 예시**:
```json
{
  "ticker": "005930.KS",
  "company_name": "삼성전자",
  "current_price": 62800,
  "currency": "KRW",
  "change_pct": -0.95,
  "volume": 12345678,
  "market": "KRX"
}
```

### Tool 4: `search_korean_stock`
```python
def search_korean_stock(query: str) -> list
```
**설명**: 한국 주식 종목명 부분 검색  
**반환 예시**:
```json
[
  { "ticker": "005930.KS", "name": "삼성전자", "code": "005930" },
  { "ticker": "005935.KS", "name": "삼성전자우", "code": "005935" }
]
```

---

## 5. 파일 구조

```
stock-analyzer/
├── app.py                  # 기존 Streamlit 앱 (수정 없음)
├── stock_library.py        # 한국 주식 DB (수정 없음)
├── mcp_server.py           # NEW: FastMCP 서버
├── agents.md               # NEW: 에이전트용 MCP 설치 가이드
├── requirements.txt        # UPDATED: fastmcp 추가
├── start.sh                # 기존 Streamlit 시작 스크립트
├── start_mcp.sh            # NEW: MCP 서버 시작 스크립트
├── railway.json            # 기존 Streamlit 서비스 설정
├── docs/
│   └── PRD.md              # 이 문서
└── .claude/
    └── settings.local.json
```

---

## 6. 배포 계획

### Railway 구성

**Service 1** (기존): Streamlit App
- 시작 명령: `./start.sh`
- 포트: `$PORT` (Railway 자동 할당)

**Service 2** (신규): MCP Server
- 시작 명령: `./start_mcp.sh`
- 포트: `$PORT` (Railway 자동 할당)
- 도메인: Railway 자동 생성 (`*.up.railway.app`)
- Healthcheck: `GET /health`

### MCP 서버 시작 스크립트 (`start_mcp.sh`)
```bash
#!/bin/bash
export PORT=${PORT:-8000}
python mcp_server.py
```

### Claude Custom Connector 등록 방법
1. Claude.ai → Settings → Connectors → Add connector
2. URL: `https://<mcp-service>.up.railway.app/mcp`
3. 인증: 없음 (초기 버전)
4. 연결 테스트 후 저장

---

## 7. requirements.txt 변경사항

```
# 기존
streamlit>=1.28.0
yfinance>=0.2.18
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
beautifulsoup4>=4.11.0

# 추가
fastmcp>=2.3.0
```

> **주의**: FastMCP는 Python 3.10+ 필요. Railway Nixpacks는 runtime.txt의 버전을 따름. `runtime.txt`를 `python-3.11.0`으로 업데이트 필요.

---

## 8. 구현 단계 (Task Breakdown)

| # | 작업 | 파일 | 예상 난이도 |
|---|------|------|------------|
| 1 | `mcp_server.py` 작성 (4개 Tool 구현) | `mcp_server.py` | 중 |
| 2 | `requirements.txt` 업데이트 | `requirements.txt` | 하 |
| 3 | `runtime.txt` Python 버전 업데이트 | `runtime.txt` | 하 |
| 4 | `start_mcp.sh` 작성 | `start_mcp.sh` | 하 |
| 5 | GitHub push | - | 하 |
| 6 | Railway MCP 서비스 생성 및 배포 | Railway | 중 |
| 7 | Claude Connector 등록 및 테스트 | Claude.ai | 하 |

---

## 9. 제약사항 및 고려사항

### 기술적 제약
- **Python 버전**: FastMCP 3.x는 Python 3.10+ 필요. 현재 환경은 3.9.6 → Railway에서는 3.11 사용
- **응답 크기**: Claude.ai Connector 결과 크기 제한 ~150,000자. `analyze_stock_drops`의 전체 데이터 반환 시 초과 가능 → 요약 통계만 반환하도록 설계
- **타임아웃**: Claude.ai 타임아웃 300초. yfinance + 스크래핑 병렬화로 응답 시간 단축 필요
- **스크래핑 안정성**: FGI, PCI는 외부 사이트 스크래핑 → 실패 시 `null` 반환으로 graceful degradation

### 보안
- 초기 버전은 인증 없이 공개 엔드포인트로 배포 (주식 데이터는 공개 정보)
- 향후 Bearer token 또는 OAuth 추가 고려

### 비용
- Railway 무료 플랜: 월 500시간 → MCP 서버는 요청 시에만 활성화되므로 추가 비용 미미

---

## 10. 성공 기준

| 기준 | 측정 방법 |
|------|----------|
| MCP 서버 Railway 배포 성공 | healthcheck URL 200 응답 |
| 4개 Tool 정상 동작 | MCP Inspector로 각 Tool 테스트 |
| Claude Code 연결 성공 | `claude mcp add` 후 Tool 목록 확인 |
| Claude.ai Connector 등록 성공 | Settings > Connectors에서 활성화 상태 확인 |
| `get_market_indicators` 응답 시간 | < 10초 |
| `analyze_stock_drops` 응답 시간 | < 30초 |
