@echo off
if defined FAKE_PYTHON_CANDIDATE_LOG echo %*>>"%FAKE_PYTHON_CANDIDATE_LOG%"
if "%~1"=="-c" (
  echo CODEX_PYTHON_PROBE^|3^|10^|0^|%~f0
  exit /b 0
)
exit /b 91
