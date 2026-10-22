@echo off
if defined FAKE_PYTHON_INVALID_LOG echo %*>>"%FAKE_PYTHON_INVALID_LOG%"
echo Simulated non-executable Python candidate. 1>&2
exit /b 96
