@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1" %*
set "_hackmd_result=%errorlevel%"
if not "%HACKMD_NOTE_WRITER_NO_PAUSE%"=="1" pause
exit /b %_hackmd_result%
