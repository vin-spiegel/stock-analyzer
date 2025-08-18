#!/bin/bash

# Railway 배포용 시작 스크립트
# Streamlit 애플리케이션을 헤드리스 모드로 실행

export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=${PORT:-8080}
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Streamlit 실행
streamlit run app.py \
  --server.headless true \
  --server.port $STREAMLIT_SERVER_PORT \
  --server.address 0.0.0.0 \
  --browser.gatherUsageStats false