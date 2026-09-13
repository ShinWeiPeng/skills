@echo off
setlocal

if not "%FAKE_CODEX_LOG%"=="" echo %*>>"%FAKE_CODEX_LOG%"

if /i "%FAKE_CODEX_SCENARIO%"=="access-denied" (
  echo Access is denied.
  exit /b 5
)

if /i "%FAKE_CODEX_SCENARIO%"=="duplicate-marketplace" (
  if /i "%~1"=="plugin" if /i "%~2"=="marketplace" if /i "%~3"=="add" (
    echo Marketplace already registered.
    exit /b 1
  )
)

if /i "%FAKE_CODEX_SCENARIO%"=="marketplace-failure" (
  if /i "%~1"=="plugin" if /i "%~2"=="marketplace" if /i "%~3"=="add" (
    echo Simulated marketplace failure. 1>&2
    exit /b 7
  )
)

if /i "%FAKE_CODEX_SCENARIO%"=="plugin-failure" (
  if /i "%~1"=="plugin" if /i "%~2"=="add" (
    echo Simulated plugin installation failure. 1>&2
    exit /b 8
  )
)

if /i "%~1"=="plugin" if /i "%~2"=="add" if not "%FAKE_CODEX_INSTALL_SOURCE%"=="" if not "%FAKE_CODEX_INSTALL_TARGET%"=="" (
  if exist "%FAKE_CODEX_INSTALL_TARGET%" rmdir /s /q "%FAKE_CODEX_INSTALL_TARGET%"
  xcopy /e /i /q /y "%FAKE_CODEX_INSTALL_SOURCE%" "%FAKE_CODEX_INSTALL_TARGET%" >nul
  if errorlevel 1 exit /b 9
)

echo Simulated Codex success.
exit /b 0
