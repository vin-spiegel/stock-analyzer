@echo off
REM 윈도우용 환경 설정 스크립트
REM 처음 설치시에만 실행하면 됩니다

echo ===================================
echo 주식 분석 대시보드 환경 설정
echo ===================================

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo 오류: Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치하고 다시 시도하세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 설치 확인 완료
python --version

REM 가상환경 생성
echo.
echo 가상환경 생성 중...
if exist "venv" (
    echo 기존 가상환경을 삭제합니다...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo 가상환경 생성 실패
    pause
    exit /b 1
)

REM 가상환경 활성화
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip

REM 패키지 설치
echo.
echo 필요한 패키지들을 설치합니다...
pip install -r requirements.txt

if errorlevel 1 (
    echo 패키지 설치 실패
    pause
    exit /b 1
)

echo.
echo ===================================
echo 설정 완료!
echo ===================================
echo.
echo 이제 start.bat 파일을 실행하여 앱을 시작하세요.
echo 또는 다음 명령어를 실행하세요:
echo   venv\Scripts\activate.bat
echo   streamlit run app.py
echo.

pause