@echo off
REM 윈도우용 주식 분석 대시보드 시작 스크립트
REM 가상환경 활성화 및 Streamlit 앱 실행

echo ===================================
echo 주식 분석 대시보드 시작
echo ===================================

REM 가상환경이 있는지 확인
if not exist "venv\Scripts\activate.bat" (
    echo 가상환경이 없습니다. 가상환경을 생성합니다...
    python -m venv venv
    if errorlevel 1 (
        echo 가상환경 생성 실패. Python이 설치되어 있는지 확인하세요.
        pause
        exit /b 1
    )
)

REM 가상환경 활성화
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM 패키지 설치 확인
echo 필요한 패키지 설치 확인 중...
pip install -r requirements.txt

REM Streamlit 설정
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

REM Streamlit 앱 실행
echo.
echo ===================================
echo Streamlit 앱을 시작합니다...
echo 브라우저에서 http://localhost:8501 을 열어주세요
echo 종료하려면 Ctrl+C를 누르세요
echo ===================================
echo.

streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause