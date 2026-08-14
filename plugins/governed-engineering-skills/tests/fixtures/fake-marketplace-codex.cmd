@echo off
echo %*>> "%FAKE_MARKETPLACE_CODEX_LOG%"
echo Successful Codex diagnostic 1>&2

if "%FAKE_MARKETPLACE_CODEX_FAILURE%"=="plugin-add" if "%~1"=="plugin" if "%~2"=="add" (
  echo Actionable simulated plugin failure 1>&2
  exit /b 42
)

if "%~1"=="--version" (
  echo codex-cli 0.147.0
  exit /b 0
)

if "%~1"=="plugin" if "%~2"=="marketplace" if "%~3"=="list" (
  echo {"marketplaces":[]}
  exit /b 0
)

if "%~1"=="plugin" if "%~2"=="list" (
  echo {"installed":[{"pluginId":"governed-engineering-skills@governed-engineering"}]}
  exit /b 0
)

exit /b 0
