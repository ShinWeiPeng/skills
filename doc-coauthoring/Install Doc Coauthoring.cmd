@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1" %*
set "_doc_result=%errorlevel%"
if not "%DOC_COAUTHORING_NO_PAUSE%"=="1" pause
exit /b %_doc_result%
