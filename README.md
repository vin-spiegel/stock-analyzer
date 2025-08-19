# 📈 주식 분석 대시보드

실시간 시장 지표와 주식 분석 도구를 제공하는 Streamlit 기반 웹 애플리케이션입니다.

## ✨ 주요 기능

### 📊 시장 감정 지표
- **공포 & 탐욕 지수**: 시장 심리 분석
- **VIX 지수**: 시장 변동성 측정
- **Put/Call 비율**: 옵션 거래 분석
- **RSI**: 상대강도지수 (S&P 500 기준)
- **QQQ vs 200일 이동평균**: 나스닥 추세 분석
- **버핏 지수**: Wilshire 5000 기반 시장 밸류에이션
- **원달러 환율**: 실시간 환율 정보

### 📉 N일 후 분석기
- 특정 하락률 기준으로 매수/매도 타이밍 분석
- 한국 주식 및 해외 주식 지원
- 통계적 승률 계산 및 투자 전략 제안

## 🚀 빠른 시작

### Windows 사용자

#### 1. 초기 설정 (처음 한 번만)
```bash
# setup.bat 더블클릭 또는 명령프롬프트에서 실행
setup.bat
```

#### 2. 연결 테스트
```bash
# test.bat 더블클릭 또는 명령프롬프트에서 실행
test.bat
```

#### 3. 앱 실행
```bash
# start.bat 더블클릭 또는 명령프롬프트에서 실행
start.bat
```

브라우저에서 http://localhost:8501 으로 접속하세요.

### Linux/Mac 사용자

#### 1. 초기 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

#### 2. 앱 실행
```bash
# 개발 모드
streamlit run app.py

# 또는 start.sh 사용
chmod +x start.sh
./start.sh
```

## 📦 필요 패키지

```
streamlit>=1.28.0
yfinance>=0.2.18
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
beautifulsoup4>=4.11.0
```

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Data Source**: Yahoo Finance (yfinance)
- **Backend**: Python 3.8+
- **Deployment**: Railway (선택사항)

## 📊 지원 주식

### 해외 주식
- 미국 주식: QQQ, SPY, AAPL, MSFT, GOOGL 등 (티커 검색)
- ETF: VTI, VOO, IVV 등

### 한국 주식  
- 종목명 검색: "삼성전자", "SK하이닉스" 등
- 종목 코드: "005930", "000660" 등
- 전체 티커: "005930.KS" 등

## ⚠️ 주의사항

- 이 도구는 참고 목적으로만 사용하세요
- 실제 투자 결정의 유일한 근거로 사용하지 마세요
- 과거 데이터 기반 분석이므로 미래 수익을 보장하지 않습니다
- 투자에는 항상 리스크가 따릅니다

## 🔗 배포

Railway를 통한 자동 배포가 설정되어 있습니다.

## 📄 라이선스

MIT License