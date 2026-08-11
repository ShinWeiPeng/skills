@echo off
setlocal
cd /d "%~dp0"

set "INSTALLER=%~dp0scripts\install-local.ps1"
if not exist "%INSTALLER%" (
  echo ERROR: Installer not found: %INSTALLER%
  set "INSTALL_EXIT=10"
  goto finish
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" %*
set "INSTALL_EXIT=%ERRORLEVEL%"

:finish
echo.
if "%INSTALL_EXIT%"=="0" (
  echo Governed Engineering Skills is installed for Codex Desktop and CLI.
  echo Start a new Codex task to load the refreshed skills.
) else (
  echo Installation failed with exit code %INSTALL_EXIT%.
)
echo Log: %TEMP%\governed-engineering-skills-install.log

if not "%GOVERNED_INSTALLER_NO_DELAY%"=="1" (
  echo This window will close automatically in 15 seconds.
  timeout.exe /t 15 /nobreak >nul
)

exit /b %INSTALL_EXIT%
