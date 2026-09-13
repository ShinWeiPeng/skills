@echo off
if defined FAKE_PYTHON_INVALID_LOG echo %*>>"%FAKE_PYTHON_INVALID_LOG%"
if "%~1"=="-c" (
  echo CODEX_PYTHON_PROBE^|2^|7^|18^|%~f0
  exit /b 0
)
exit /b 94
