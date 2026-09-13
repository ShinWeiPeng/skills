@echo off
if defined FAKE_PYTHON_LAUNCHER_LOG echo %*>>"%FAKE_PYTHON_LAUNCHER_LOG%"
if not "%~1"=="-3" exit /b 92
if not "%~2"=="-c" exit /b 93
echo CODEX_PYTHON_PROBE^|3^|11^|0^|%FAKE_PYTHON_EXECUTABLE%
exit /b 0
