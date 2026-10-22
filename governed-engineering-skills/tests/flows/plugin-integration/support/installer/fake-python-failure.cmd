@echo off
if "%~1"=="-c" (
  echo CODEX_PYTHON_PROBE^|3^|11^|0^|%~f0
  exit /b 0
)
echo Simulated assembly failure. 1>&2
exit /b 9
