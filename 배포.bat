@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   CTR EHS 대시보드 - 순찰 데이터 배포
echo ============================================
echo.
echo [1/3] CSV를 patrol_data.js로 변환 중...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0csv_to_patrol.ps1"
if errorlevel 1 (
  echo.
  echo [실패] 변환 오류 - jonghap_new.csv 가 이 폴더에 있는지 확인하세요.
  pause & exit /b 1
)
echo.
echo [2/3] 변경사항 저장(커밋)...
git add patrol_data.js index.html sg_data.js
git commit -m "대시보드 업데이트(순찰/신구비교) %date%" >nul 2>&1
if errorlevel 1 echo   (변경 없음 - 새로 올릴 내용 없음)
echo.
echo [3/3] GitHub에 업로드...
git push
if errorlevel 1 (
  echo.
  echo [실패] 업로드 오류 - Git 설치/로그인 상태를 확인하세요.
  pause & exit /b 1
)
echo.
echo [완료] 1~2분 후 사이트를 새로고침(Ctrl+F5)하면 반영됩니다.
timeout /t 4 >nul
