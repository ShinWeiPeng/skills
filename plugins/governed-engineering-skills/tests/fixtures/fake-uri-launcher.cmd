@echo off
setlocal
if not "%FAKE_URI_LOG%"=="" echo %~1>"%FAKE_URI_LOG%"
if /i "%FAKE_URI_SCENARIO%"=="failure" exit /b 1
exit /b 0
