@echo off
echo %*>> "%FAKE_MARKETPLACE_CODEX_LOG%"
if defined FAKE_MARKETPLACE_CODEX_CWD_LOG echo %CD%>> "%FAKE_MARKETPLACE_CODEX_CWD_LOG%"
echo Successful Codex diagnostic 1>&2

if "%FAKE_MARKETPLACE_CODEX_FAILURE%"=="plugin-add" if "%~1"=="plugin" if "%~2"=="add" (
  echo Actionable simulated plugin failure 1>&2
  exit /b 42
)

if "%~1"=="--version" (
  echo codex-cli 0.147.0
  exit /b 0
)

if "%~1"=="plugin" if "%~2"=="marketplace" if "%~3"=="list" (
  if "%FAKE_MARKETPLACE_CODEX_SCENARIO%"=="local-conflict" (
    echo {"marketplaces":[{"name":"governed-engineering","root":"C:\\fixture\\skills"}]}
    exit /b 0
  )
  if "%FAKE_MARKETPLACE_CODEX_SCENARIO%"=="matching-git" (
    echo {"marketplaces":[{"name":"governed-engineering","root":"C:\\fixture\\marketplace","marketplaceSource":{"sourceType":"git","source":"https://github.com/ShinWeiPeng/skills.git"}}]}
    exit /b 0
  )
  if "%FAKE_MARKETPLACE_CODEX_SCENARIO%"=="wrong-git" (
    echo {"marketplaces":[{"name":"governed-engineering","root":"C:\\fixture\\other","marketplaceSource":{"sourceType":"git","source":"https://github.com/example/other.git"}}]}
    exit /b 0
  )
  if "%FAKE_MARKETPLACE_CODEX_SCENARIO%"=="duplicate" (
    echo {"marketplaces":[{"name":"governed-engineering","marketplaceSource":{"sourceType":"git","source":"https://github.com/ShinWeiPeng/skills.git"}},{"name":"governed-engineering","root":"C:\\fixture\\local"}]}
    exit /b 0
  )
  echo {"marketplaces":[]}
  exit /b 0
)

if "%~1"=="plugin" if "%~2"=="list" (
  echo {"installed":[{"pluginId":"governed-engineering-skills@governed-engineering"}]}
  exit /b 0
)

exit /b 0
