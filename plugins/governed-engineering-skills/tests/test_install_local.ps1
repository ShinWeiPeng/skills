Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pluginShell = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $pluginShell '..\..'))
$orchestrator = Join-Path $repoRoot 'scripts\install-local.ps1'
$adapter = Join-Path $pluginShell 'scripts\install-local.ps1'
$launcher = Join-Path $repoRoot 'Install Governed Engineering Skills.cmd'
$fakeCodex = Join-Path $PSScriptRoot 'fixtures\fake-codex.cmd'
$fakeUriLauncher = Join-Path $PSScriptRoot 'fixtures\fake-uri-launcher.cmd'
$fakePythonFailure = Join-Path $PSScriptRoot 'fixtures\fake-python-failure.cmd'
$artifactRoot = Join-Path $repoRoot 'dist\governed-engineering-skills'
$marketplacePath = Join-Path $repoRoot '.agents\plugins\marketplace.json'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('governed-installer-' + [Guid]::NewGuid().ToString('N'))
$fakeBin = Join-Path $testRoot 'bin'
$fakeHome = Join-Path $testRoot 'home'
$installedRoot = Join-Path $fakeHome 'installed\governed-engineering-skills'
$formalArtifact = Join-Path $testRoot 'formal-artifact'
$originalPath = $env:PATH
$originalLocalAppData = $env:LOCALAPPDATA
$realPython = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$gitBin = Split-Path ((Get-Command git -CommandType Application | Select-Object -First 1).Source) -Parent

function Assert-Equal {
    param($Expected, $Actual, [string]$Context)
    if ($Expected -ne $Actual) { throw "$Context expected '$Expected', got '$Actual'." }
}

function Assert-InstalledTree {
    $inventory = Get-Content -Raw -LiteralPath (Join-Path $artifactRoot 'artifact-inventory.json') | ConvertFrom-Json
    $expected = @($inventory.files.path) + @('artifact-inventory.json') | Sort-Object
    $actual = @(Get-ChildItem -LiteralPath $installedRoot -Recurse -File | ForEach-Object {
        $_.FullName.Substring($installedRoot.Length + 1).Replace('\','/')
    }) | Sort-Object
    Assert-Equal ($expected -join "`n") ($actual -join "`n") 'installed Plugin tree'
    $installedInventory = Get-Content -Raw -LiteralPath (Join-Path $installedRoot 'artifact-inventory.json') | ConvertFrom-Json
    Assert-Equal $inventory.content_fingerprint $installedInventory.content_fingerprint 'installed Plugin fingerprint'
}

function Get-TreeEvidence {
    param([string]$Root)
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return '' }
    return (@(Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName | ForEach-Object {
        $relative = $_.FullName.Substring($Root.Length + 1).Replace('\','/')
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
        "$relative`t$hash"
    }) -join "`n")
}

function Restore-FormalArtifact {
    $resolvedTarget = [System.IO.Path]::GetFullPath($artifactRoot)
    $allowedRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'dist'))
    if (-not $resolvedTarget.StartsWith($allowedRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to replace test artifact outside $allowedRoot"
    }
    if (Test-Path -LiteralPath $resolvedTarget) { Remove-Item -Recurse -Force -LiteralPath $resolvedTarget }
    Copy-Item -Recurse -LiteralPath $formalArtifact -Destination $resolvedTarget
}

function Restore-LocalizedArtifact {
    Restore-FormalArtifact
    & $realPython (Join-Path $repoRoot 'scripts\assemble_plugin.py') localize `
        --repo-root $repoRoot --artifact $artifactRoot *> $null
    Assert-Equal 0 $LASTEXITCODE 'localized adapter fixture'
}

function Invoke-AdapterScenario {
    param([string]$Scenario, [int]$ExpectedExit, [int]$ExpectedCalls, [bool]$ExpectUri, [string]$ExpectedLog)
    $callLog = Join-Path $testRoot "$Scenario.calls"
    $uriCapture = Join-Path $testRoot "$Scenario.uri"
    $installLog = Join-Path $testRoot "$Scenario.install.log"
    Restore-LocalizedArtifact
    $installedBefore = if ($Scenario -eq 'plugin-failure') { Get-TreeEvidence $installedRoot } else { $null }
    $env:FAKE_CODEX_SCENARIO = $Scenario
    $env:FAKE_CODEX_LOG = $callLog
    $env:FAKE_CODEX_INSTALL_SOURCE = $artifactRoot
    $env:FAKE_CODEX_INSTALL_TARGET = $installedRoot
    $env:FAKE_URI_LOG = $uriCapture
    $env:FAKE_URI_SCENARIO = if ($Scenario -eq 'uri-launch-failure') { 'failure' } else { 'success' }

    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $adapter `
        -ArtifactRoot $artifactRoot -MarketplacePath $marketplacePath `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath $installLog *> $null
    Assert-Equal $ExpectedExit $LASTEXITCODE $Scenario
    [array]$calls = if (Test-Path -LiteralPath $callLog) { Get-Content -LiteralPath $callLog } else { @() }
    Assert-Equal $ExpectedCalls $calls.Count "$Scenario Codex call count"
    Assert-Equal $ExpectUri (Test-Path -LiteralPath $uriCapture) "$Scenario URI"
    if ((Get-Content -Raw -LiteralPath $installLog) -notmatch $ExpectedLog) {
        throw "$Scenario did not log actionable recovery matching '$ExpectedLog'."
    }
    if ($Scenario -eq 'plugin-failure') {
        Assert-Equal $installedBefore (Get-TreeEvidence $installedRoot) 'plugin failure must not remove the prior installed tree'
    }
    if ($ExpectedExit -eq 0) { Assert-InstalledTree }
}

New-Item -ItemType Directory -Path $fakeBin -Force | Out-Null
Copy-Item -LiteralPath $fakeCodex -Destination (Join-Path $fakeBin 'codex.cmd')
try {
    foreach ($subject in @($orchestrator, $adapter, $launcher, $fakeCodex, $fakeUriLauncher, $fakePythonFailure)) {
        if (-not (Test-Path -LiteralPath $subject -PathType Leaf)) { throw "Required test subject is missing: $subject" }
    }
    & $realPython (Join-Path $repoRoot 'scripts\assemble_plugin.py') assemble --repo-root $repoRoot --output $formalArtifact *> $null
    Assert-Equal 0 $LASTEXITCODE 'formal artifact fixture assembly'
    foreach ($script in @($orchestrator, $adapter)) {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($script, [ref]$tokens, [ref]$errors)
        Assert-Equal 0 @($errors).Count "PowerShell parse errors in $script"
    }
    $launcherText = Get-Content -Raw -LiteralPath $launcher
    if ($launcherText -notmatch '(?i)%~dp0' -or $launcherText -match '(?im)^\s*(pause|set\s+/p)\b') {
        throw 'Launcher must be location-relative and non-interactive.'
    }

    $env:PATH = "$fakeBin;$originalPath"
    $env:LOCALAPPDATA = $fakeHome
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'orchestrator.calls'
    $env:FAKE_CODEX_INSTALL_SOURCE = $artifactRoot
    $env:FAKE_CODEX_INSTALL_TARGET = $installedRoot
    $env:FAKE_URI_LOG = Join-Path $testRoot 'orchestrator.uri'
    $env:FAKE_URI_SCENARIO = 'success'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot -PythonCommand $realPython `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'orchestrator.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'assembly-first orchestrator'
    $manifest = Get-Content -Raw -LiteralPath (Join-Path $artifactRoot '.codex-plugin\plugin.json') | ConvertFrom-Json
    $package = Get-Content -Raw -LiteralPath (Join-Path $pluginShell 'package.json') | ConvertFrom-Json
    if ([string]$manifest.version -notmatch ('^' + [regex]::Escape([string]$package.version) + '\+codex\.')) {
        throw 'Local artifact does not have a cachebuster preserving the formal package version.'
    }
    & python (Join-Path $artifactRoot 'scripts\version_governance.py') check --local *> $null
    Assert-Equal 0 $LASTEXITCODE 'localized artifact version governance'
    Assert-InstalledTree
    $firstLocalVersion = [string]$manifest.version

    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot -PythonCommand $realPython `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'orchestrator-repeat.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'repeated full installation'
    $repeatManifest = Get-Content -Raw -LiteralPath (Join-Path $artifactRoot '.codex-plugin\plugin.json') | ConvertFrom-Json
    if ([string]$repeatManifest.version -eq $firstLocalVersion) { throw 'Repeated installation did not replace the stale local cache identity.' }
    Assert-InstalledTree

    Invoke-AdapterScenario 'success' 0 2 $true 'READY:.*is installed'
    Invoke-AdapterScenario 'duplicate-marketplace' 0 2 $true 'already registered; continuing with reinstall'
    Invoke-AdapterScenario 'marketplace-failure' 20 1 $false 'Unable to register the local Marketplace'
    Invoke-AdapterScenario 'plugin-failure' 21 2 $false 'Marketplace remains registered; rerun this installer to retry'
    Invoke-AdapterScenario 'access-denied' 12 1 $false 'Windows denied access'
    Invoke-AdapterScenario 'uri-launch-failure' 23 2 $true 'Open manually: codex://plugins/'

    $env:LOCALAPPDATA = Join-Path $testRoot 'missing-runtime'
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot\System32\WindowsPowerShell\v1.0;$gitBin"
    $env:FAKE_CODEX_SCENARIO = 'missing-cli'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'missing.calls'
    Restore-LocalizedArtifact
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $adapter `
        -ArtifactRoot $artifactRoot -MarketplacePath $marketplacePath `
        -LogPath (Join-Path $testRoot 'missing.log') *> $null
    Assert-Equal 11 $LASTEXITCODE 'missing Codex runtime'
    if ((Get-Content -Raw -LiteralPath (Join-Path $testRoot 'missing.log')) -notmatch 'Codex CLI was not found') { throw 'Missing-runtime recovery guidance is absent.' }

    $incomplete = Join-Path $testRoot 'incomplete-artifact'
    New-Item -ItemType Directory -Path $incomplete | Out-Null
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $adapter `
        -ArtifactRoot $incomplete -MarketplacePath $marketplacePath `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'incomplete.log') *> $null
    Assert-Equal 10 $LASTEXITCODE 'incomplete artifact'
    if ((Get-Content -Raw -LiteralPath (Join-Path $testRoot 'incomplete.log')) -notmatch 'incomplete or stale') { throw 'Incomplete-artifact recovery guidance is absent.' }

    $env:PATH = "$fakeBin;$originalPath"
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'assembly-failure.calls'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot -PythonCommand $fakePythonFailure `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'assembly-failure.log') *> $null
    Assert-Equal 30 $LASTEXITCODE 'simulated partial assembly failure'
    Assert-Equal $false (Test-Path -LiteralPath $env:FAKE_CODEX_LOG) 'Codex must not run after assembly failure'

    $env:GOVERNED_INSTALLER_NO_DELAY = '1'
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'launcher.calls'
    $env:FAKE_URI_LOG = Join-Path $testRoot 'launcher.uri'
    $env:FAKE_URI_SCENARIO = 'success'
    $launcherCommand = "call `"$launcher`" -RepositoryRoot `"$repoRoot`" -PythonCommand `"$realPython`" -CodexCommand `"$fakeCodex`" -UriLauncherCommand `"$fakeUriLauncher`""
    & $env:ComSpec /d /c $launcherCommand *> $null
    Assert-Equal 0 $LASTEXITCODE 'double-click launcher'
    Assert-InstalledTree

    Write-Host 'PASS: local assembly, cache refresh, registration, reinstall, and failure contracts'
}
finally {
    foreach ($name in @('FAKE_CODEX_SCENARIO','FAKE_CODEX_LOG','FAKE_CODEX_INSTALL_SOURCE','FAKE_CODEX_INSTALL_TARGET','FAKE_URI_LOG','FAKE_URI_SCENARIO','GOVERNED_INSTALLER_NO_DELAY')) {
        Remove-Item "Env:\$name" -ErrorAction SilentlyContinue
    }
    $env:PATH = $originalPath
    $env:LOCALAPPDATA = $originalLocalAppData
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -Recurse -Force -LiteralPath $testRoot }
}
