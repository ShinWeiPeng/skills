@echo off
setlocal

if not "%FAKE_CODEX_LOG%"=="" (
  echo %*>>"%FAKE_CODEX_LOG%"
)

if /i "%FAKE_CODEX_SCENARIO%"=="duplicate-marketplace" (
  if /i "%~1"=="plugin" if /i "%~2"=="marketplace" if /i "%~3"=="add" (
    echo Marketplace already exists.
    exit /b 1
  )
)

if /i "%FAKE_CODEX_SCENARIO%"=="marketplace-failure" (
  if /i "%~1"=="plugin" if /i "%~2"=="marketplace" if /i "%~3"=="add" (
    echo Simulated marketplace failure. 1>&2
    exit /b 7
  )
)

if /i "%FAKE_CODEX_SCENARIO%"=="access-denied" (
  echo Access is denied.
  exit /b 5
)

echo Simulated Codex success.
exit /b 0
