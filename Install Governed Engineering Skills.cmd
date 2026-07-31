@echo off
setlocal
cd /d "%~dp0"

set "INSTALLER=%~dp0plugins\governed-engineering-skills\scripts\install-local.ps1"

if not exist "%INSTALLER%" (
  echo ERROR: Installer not found:
  echo %INSTALLER%
  set "INSTALL_EXIT=10"
  goto finish
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%"
set "INSTALL_EXIT=%ERRORLEVEL%"

:finish
echo.
if "%INSTALL_EXIT%"=="0" (
  echo The local marketplace is ready.
  echo Codex Desktop should now show Governed Engineering Skills.
  echo Click Install in Codex Desktop to finish the installation.
) else (
  echo Marketplace setup failed with exit code %INSTALL_EXIT%.
)
echo Log: %TEMP%\governed-engineering-skills-install.log

if not "%GOVERNED_INSTALLER_NO_DELAY%"=="1" (
  echo This window will close automatically in 15 seconds.
  timeout.exe /t 15 /nobreak >nul
)

exit /b %INSTALL_EXIT%
