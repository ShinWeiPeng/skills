Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pluginRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $pluginRoot '..\..'))
$installer = Join-Path $pluginRoot 'scripts\install-local.ps1'
$launcher = Join-Path $repoRoot 'Install Governed Engineering Skills.cmd'
$fakeCodex = Join-Path $PSScriptRoot 'fixtures\fake-codex.cmd'
$marketplacePath = Join-Path $repoRoot '.agents\plugins\marketplace.json'
$expectedUri = 'codex://plugins/governed-engineering-skills?marketplacePath=' +
    [Uri]::EscapeDataString($marketplacePath)
$installLog = Join-Path ([System.IO.Path]::GetTempPath()) (
    'governed-engineering-skills-install.log'
)
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
    'governed-installer-test-' + [Guid]::NewGuid().ToString('N')
)
$originalLocalAppData = $env:LOCALAPPDATA
$originalPath = $env:PATH

function Assert-Equal {
    param(
        [Parameter(Mandatory = $true)]$Expected,
        [Parameter(Mandatory = $true)]$Actual,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ($Expected -ne $Actual) {
        throw "$Context expected '$Expected', got '$Actual'."
    }
}

function Invoke-InstallerScenario {
    param(
        [Parameter(Mandatory = $true)][string]$Scenario,
        [Parameter(Mandatory = $true)][int]$ExpectedExit,
        [Parameter(Mandatory = $true)][bool]$ExpectPluginPage
    )

    $fakeLog = Join-Path $testRoot "$Scenario.log"
    $uriCapture = Join-Path $testRoot "$Scenario.uri"
    $env:GOVERNED_CODEX_CLI = $fakeCodex
    $env:FAKE_CODEX_SCENARIO = $Scenario
    $env:FAKE_CODEX_LOG = $fakeLog
    $env:GOVERNED_PLUGIN_URI_CAPTURE = $uriCapture
    Remove-Item Env:\GOVERNED_PLUGIN_URI_LAUNCH_FAILURE -ErrorAction SilentlyContinue
    if ($Scenario -eq 'uri-launch-failure') {
        $env:GOVERNED_PLUGIN_URI_LAUNCH_FAILURE = '1'
    }

    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $installer *> $null
    Assert-Equal -Expected $ExpectedExit -Actual $LASTEXITCODE -Context $Scenario

    [array]$calls = if (Test-Path -LiteralPath $fakeLog) {
        Get-Content -Encoding Default -LiteralPath $fakeLog
    }
    else {
        @()
    }
    Assert-Equal -Expected 1 -Actual $calls.Count -Context "$Scenario call count"
    if ($calls[0] -notmatch '^plugin marketplace add ') {
        throw "$Scenario invoked an unsupported Codex plugin command."
    }

    Assert-Equal -Expected $ExpectPluginPage -Actual (
        Test-Path -LiteralPath $uriCapture
    ) -Context "$Scenario plugin-page launch"
    if ($ExpectPluginPage) {
        $capturedUri = (
            Get-Content -Raw -Encoding utf8 -LiteralPath $uriCapture
        ).Trim()
        Assert-Equal -Expected $expectedUri -Actual $capturedUri -Context (
            "$Scenario plugin URI"
        )
    }
}

New-Item -ItemType Directory -Path $testRoot | Out-Null
try {
    foreach ($path in @($installer, $launcher, $fakeCodex)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required test subject is missing: $path"
        }
    }

    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $installer,
        [ref]$tokens,
        [ref]$parseErrors
    )
    Assert-Equal -Expected 0 -Actual @($parseErrors).Count -Context (
        'PowerShell parse errors'
    )

    $installerText = Get-Content -Raw -Encoding utf8 -LiteralPath $installer
    if ($installerText -match (
            "(?i)'plugin'\s*,\s*'(add|list)'|codex plugin (add|list)"
        )) {
        throw 'Installer must not invoke unsupported plugin add/list commands.'
    }

    $launcherText = Get-Content -Raw -Encoding Default -LiteralPath $launcher
    if ($launcherText -match '(?im)^\s*(pause|set\s+/p)\b' -or
        $launcherText -match '(?i)Read-Host') {
        throw 'Launcher must not request interactive console input.'
    }
    if ($launcherText -notmatch '(?i)%~dp0') {
        throw 'Launcher must resolve files relative to its own path.'
    }
    if ($launcherText -match '(?i)installation completed successfully' -or
        $launcherText -notmatch '(?i)click Install') {
        throw 'Launcher must describe the required Codex Desktop install action.'
    }

    Invoke-InstallerScenario -Scenario 'success' -ExpectedExit 0 `
        -ExpectPluginPage $true
    Invoke-InstallerScenario -Scenario 'duplicate-marketplace' -ExpectedExit 0 `
        -ExpectPluginPage $true
    Invoke-InstallerScenario -Scenario 'marketplace-failure' -ExpectedExit 20 `
        -ExpectPluginPage $false
    $failureLog = Get-Content -Raw -Encoding utf8 -LiteralPath $installLog
    if ($failureLog -notmatch 'Simulated marketplace failure' -or
        $failureLog -match 'Codex exit 9009') {
        throw 'Native Codex stderr and exit code were not preserved.'
    }
    Invoke-InstallerScenario -Scenario 'access-denied' -ExpectedExit 12 `
        -ExpectPluginPage $false
    Invoke-InstallerScenario -Scenario 'uri-launch-failure' -ExpectedExit 23 `
        -ExpectPluginPage $false
    $uriFailureLog = Get-Content -Raw -Encoding utf8 -LiteralPath $installLog
    if ($uriFailureLog -notmatch [regex]::Escape($expectedUri)) {
        throw 'URI launch failure must provide the manual Codex plugin URI.'
    }

    $desktopLocalAppData = Join-Path $testRoot 'desktop-localappdata'
    $desktopBin = Join-Path $desktopLocalAppData 'OpenAI\Codex\bin'
    New-Item -ItemType Directory -Path $desktopBin | Out-Null
    Copy-Item -LiteralPath $fakeCodex -Destination (
        Join-Path $desktopBin 'codex.cmd'
    )
    Remove-Item Env:\GOVERNED_CODEX_CLI -ErrorAction SilentlyContinue
    $env:LOCALAPPDATA = $desktopLocalAppData
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot\System32\WindowsPowerShell\v1.0"
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'desktop-fallback.log'
    $env:GOVERNED_PLUGIN_URI_CAPTURE = Join-Path $testRoot (
        'desktop-fallback.uri'
    )
    Remove-Item Env:\GOVERNED_PLUGIN_URI_LAUNCH_FAILURE -ErrorAction SilentlyContinue
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $installer *> $null
    Assert-Equal -Expected 0 -Actual $LASTEXITCODE -Context (
        'Codex Desktop CLI fallback'
    )
    Assert-Equal -Expected 1 -Actual @(
        Get-Content -Encoding Default -LiteralPath $env:FAKE_CODEX_LOG
    ).Count -Context 'Codex Desktop fallback call count'

    $env:LOCALAPPDATA = Join-Path $testRoot 'missing-localappdata'
    $env:FAKE_CODEX_SCENARIO = 'missing-cli'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'missing-cli.log'
    $env:GOVERNED_PLUGIN_URI_CAPTURE = Join-Path $testRoot 'missing-cli.uri'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $installer *> $null
    Assert-Equal -Expected 11 -Actual $LASTEXITCODE -Context 'missing CLI'

    $launcherLog = Join-Path $testRoot 'launcher.log'
    $launcherUri = Join-Path $testRoot 'launcher.uri'
    $env:GOVERNED_CODEX_CLI = $fakeCodex
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = $launcherLog
    $env:GOVERNED_PLUGIN_URI_CAPTURE = $launcherUri
    $env:GOVERNED_INSTALLER_NO_DELAY = '1'
    $env:LOCALAPPDATA = $originalLocalAppData
    $env:PATH = $originalPath
    & $env:ComSpec /d /c "call `"$launcher`"" *> $null
    Assert-Equal -Expected 0 -Actual $LASTEXITCODE -Context (
        'double-click launcher'
    )
    Assert-Equal -Expected 1 -Actual @(
        Get-Content -Encoding Default -LiteralPath $launcherLog
    ).Count -Context 'launcher call count'
    Assert-Equal -Expected $true -Actual (
        Test-Path -LiteralPath $launcherUri
    ) -Context 'launcher plugin-page launch'

    Write-Host 'PASS: marketplace registration and Codex Desktop launch scenarios'
}
finally {
    Remove-Item Env:\GOVERNED_CODEX_CLI -ErrorAction SilentlyContinue
    Remove-Item Env:\FAKE_CODEX_SCENARIO -ErrorAction SilentlyContinue
    Remove-Item Env:\FAKE_CODEX_LOG -ErrorAction SilentlyContinue
    Remove-Item Env:\GOVERNED_PLUGIN_URI_CAPTURE -ErrorAction SilentlyContinue
    Remove-Item Env:\GOVERNED_PLUGIN_URI_LAUNCH_FAILURE -ErrorAction SilentlyContinue
    Remove-Item Env:\GOVERNED_INSTALLER_NO_DELAY -ErrorAction SilentlyContinue
    $env:LOCALAPPDATA = $originalLocalAppData
    $env:PATH = $originalPath
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -Recurse -Force -LiteralPath $testRoot
    }
}
