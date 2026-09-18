@echo off
if defined FAKE_PYTHON_INVALID_LOG echo %*>>"%FAKE_PYTHON_INVALID_LOG%"
if "%~1"=="-c" (
  echo this-is-not-a-python-probe
  exit /b 0
)
exit /b 95
