@echo off
if defined FAKE_PYTHON_RUNTIME_LOG echo %*>>"%FAKE_PYTHON_RUNTIME_LOG%"
if "%~1"=="-c" (
  echo CODEX_PYTHON_PROBE^|3^|11^|0^|%~f0
  exit /b 0
)
"%FAKE_REAL_PYTHON%" %*
exit /b %ERRORLEVEL%
