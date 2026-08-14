Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pluginShell = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $pluginShell '..\..'))
$orchestrator = Join-Path $repoRoot 'scripts\install-local.ps1'
$pythonSelector = Join-Path $repoRoot 'scripts\python-runtime-selection.ps1'
$pythonSelectionPolicy = Join-Path $repoRoot 'scripts\python-runtime-selection-policy.ps1'
$artifactAccess = Join-Path $repoRoot 'scripts\windows-artifact-access.ps1'
$adapter = Join-Path $pluginShell 'scripts\install-local.ps1'
$launcher = Join-Path $repoRoot 'Install Governed Engineering Skills.cmd'
$fakeCodex = Join-Path $PSScriptRoot 'fixtures\fake-codex.cmd'
$fakeCodexAccessDenied = Join-Path $PSScriptRoot 'fixtures\fake-codex-access-denied.cmd'
$fakeUriLauncher = Join-Path $PSScriptRoot 'fixtures\fake-uri-launcher.cmd'
$fakePythonFailure = Join-Path $PSScriptRoot 'fixtures\fake-python-failure.cmd'
$fakePythonIncompatible = Join-Path $PSScriptRoot 'fixtures\fake-python-incompatible.cmd'
$fakePythonLauncher = Join-Path $PSScriptRoot 'fixtures\fake-python-launcher.cmd'
$fakePython2 = Join-Path $PSScriptRoot 'fixtures\fake-python2.cmd'
$fakePythonMalformed = Join-Path $PSScriptRoot 'fixtures\fake-python-malformed.cmd'
$fakePythonCompatibleRuntime = Join-Path $PSScriptRoot 'fixtures\fake-python-compatible-runtime.cmd'
$fakePythonProbeFailure = Join-Path $PSScriptRoot 'fixtures\fake-python-probe-failure.cmd'
$fakeArtifactAccess = Join-Path $PSScriptRoot 'fixtures\fake-artifact-access.ps1'
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
$powershellExe = Join-Path $PSHOME 'powershell.exe'

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
    foreach ($subject in @($orchestrator, $pythonSelector, $pythonSelectionPolicy, $artifactAccess, $adapter, $launcher, $fakeCodex, $fakeCodexAccessDenied, $fakeUriLauncher, $fakePythonFailure, $fakePythonIncompatible, $fakePythonLauncher, $fakePython2, $fakePythonMalformed, $fakePythonCompatibleRuntime, $fakePythonProbeFailure, $fakeArtifactAccess)) {
        if (-not (Test-Path -LiteralPath $subject -PathType Leaf)) { throw "Required test subject is missing: $subject" }
    }
    & $realPython (Join-Path $repoRoot 'scripts\assemble_plugin.py') assemble --repo-root $repoRoot --output $formalArtifact *> $null
    Assert-Equal 0 $LASTEXITCODE 'formal artifact fixture assembly'
    foreach ($script in @($orchestrator, $pythonSelector, $pythonSelectionPolicy, $artifactAccess, $adapter)) {
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
    $env:FAKE_ARTIFACT_ACCESS_SCENARIO = 'ordinary'
    $env:FAKE_ARTIFACT_ACCESS_LOG = Join-Path $testRoot 'artifact-access.calls'
    Copy-Item -LiteralPath $fakePythonLauncher -Destination (Join-Path $fakeBin 'py.cmd') -Force
    $env:FAKE_PYTHON_LAUNCHER_LOG = Join-Path $testRoot 'compatible-path-launcher.calls'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot `
        -ArtifactAccessScript $fakeArtifactAccess `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'orchestrator-auto-python.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'automatic Python discovery orchestrator'
    Assert-Equal $false (Test-Path -LiteralPath $env:FAKE_PYTHON_LAUNCHER_LOG) 'compatible PATH Python must not invoke the Windows Python Launcher'
    [array]$artifactAccessCalls = Get-Content -LiteralPath $env:FAKE_ARTIFACT_ACCESS_LOG
    Assert-Equal 1 $artifactAccessCalls.Count 'artifact access recovery call count'
    if ($artifactAccessCalls[0] -notmatch [regex]::Escape($artifactRoot)) {
        throw 'Artifact access recovery did not receive the exact governed artifact path.'
    }
    Assert-InstalledTree
    $recoveredManifest = Get-Content -Raw -LiteralPath (Join-Path $installedRoot '.codex-plugin\plugin.json') | ConvertFrom-Json
    if ([string]$recoveredManifest.version -notmatch '^0\.7\.4\+codex\.') {
        throw "Recovered installation did not expose the formal 0.7.4 prefix: $($recoveredManifest.version)"
    }
    Remove-Item Env:\FAKE_ARTIFACT_ACCESS_SCENARIO, Env:\FAKE_ARTIFACT_ACCESS_LOG -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $fakeBin 'py.cmd') -Force

    Copy-Item -LiteralPath $fakePythonIncompatible -Destination (Join-Path $fakeBin 'python.cmd') -Force
    Copy-Item -LiteralPath $fakePythonLauncher -Destination (Join-Path $fakeBin 'py.cmd') -Force
    $selectedPythonRuntime = Join-Path $testRoot 'selected-python-runtime.cmd'
    Copy-Item -LiteralPath $fakePythonCompatibleRuntime -Destination $selectedPythonRuntime
    $env:FAKE_REAL_PYTHON = $realPython
    $env:FAKE_PYTHON_EXECUTABLE = $selectedPythonRuntime
    $env:FAKE_PYTHON_CANDIDATE_LOG = Join-Path $testRoot 'python-path-candidate.calls'
    $env:FAKE_PYTHON_LAUNCHER_LOG = Join-Path $testRoot 'python-launcher.calls'
    $env:FAKE_PYTHON_RUNTIME_LOG = Join-Path $testRoot 'python-selected-runtime.calls'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'python-launcher-fallback.codex.calls'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'orchestrator-python-launcher-fallback.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'incompatible PATH Python must fall back to the Windows Python Launcher'
    $launcherProbe = (Get-Content -LiteralPath $env:FAKE_PYTHON_LAUNCHER_LOG) -join ''
    if ($launcherProbe -notmatch '^-3 -c ' -or $launcherProbe -notmatch 'CODEX_PYTHON_PROBE') {
        throw "Windows Python Launcher was not probed through 'py -3 -c': $launcherProbe"
    }
    $pythonFallbackLog = Get-Content -Raw -LiteralPath (Join-Path $testRoot 'orchestrator-python-launcher-fallback.log')
    if ($pythonFallbackLog -notmatch 'Rejected PATH Python.*3\.10\.0' -or $pythonFallbackLog -notmatch [regex]::Escape($selectedPythonRuntime)) {
        throw 'Python fallback log must identify the rejected version and selected absolute interpreter.'
    }
    [array]$selectedRuntimeCalls = Get-Content -LiteralPath $env:FAKE_PYTHON_RUNTIME_LOG
    Assert-Equal 4 $selectedRuntimeCalls.Count 'selected Python probe plus installation phase count'
    if ($selectedRuntimeCalls[0] -notmatch '^-c .*CODEX_PYTHON_PROBE') { throw 'Selected Python was not revalidated before assembly.' }
    if ($selectedRuntimeCalls[1] -notmatch 'assemble_plugin\.py.* assemble ') { throw 'Selected Python did not execute Plugin assembly.' }
    if ($selectedRuntimeCalls[2] -notmatch 'validate_distribution\.py') { throw 'Selected Python did not execute distribution validation.' }
    if ($selectedRuntimeCalls[3] -notmatch 'assemble_plugin\.py.* localize ') { throw 'Selected Python did not execute cache localization.' }
    Assert-InstalledTree
    Remove-Item -LiteralPath (Join-Path $fakeBin 'python.cmd'), (Join-Path $fakeBin 'py.cmd') -Force

    foreach ($invalidPython in @(
        @{ Name = 'python2'; Command = $fakePython2; Pattern = 'Python 2\.7\.18' },
        @{ Name = 'malformed'; Command = $fakePythonMalformed; Pattern = 'malformed version information' },
        @{ Name = 'non-executable'; Command = $fakePythonProbeFailure; Pattern = 'probe exited with code 96' }
    )) {
        $artifactBeforeProbeFailure = Get-TreeEvidence $artifactRoot
        $env:FAKE_CODEX_LOG = Join-Path $testRoot "$($invalidPython.Name)-python.codex.calls"
        $env:FAKE_PYTHON_INVALID_LOG = Join-Path $testRoot "$($invalidPython.Name)-python.probe.calls"
        $invalidPythonLog = Join-Path $testRoot "$($invalidPython.Name)-python.log"
        & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
            -RepositoryRoot $repoRoot -PythonCommand $invalidPython.Command `
            -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
            -LogPath $invalidPythonLog *> $null
        Assert-Equal 13 $LASTEXITCODE "$($invalidPython.Name) explicit Python preflight"
        Assert-Equal $artifactBeforeProbeFailure (Get-TreeEvidence $artifactRoot) "$($invalidPython.Name) must stop before artifact mutation"
        Assert-Equal $false (Test-Path -LiteralPath $env:FAKE_CODEX_LOG) "$($invalidPython.Name) must stop before Codex"
        [array]$invalidPythonCalls = Get-Content -LiteralPath $env:FAKE_PYTHON_INVALID_LOG
        Assert-Equal 1 $invalidPythonCalls.Count "$($invalidPython.Name) probe-only call count"
        if ($invalidPythonCalls[0] -notmatch '^-c ' -or $invalidPythonCalls[0] -match 'assemble_plugin\.py|validate_distribution\.py') {
            throw "$($invalidPython.Name) crossed the preflight-to-assembly boundary."
        }
        if ((Get-Content -Raw -LiteralPath $invalidPythonLog) -notmatch $invalidPython.Pattern) {
            throw "$($invalidPython.Name) did not report its observed incompatibility."
        }
    }

    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot\System32\WindowsPowerShell\v1.0"
    & $powershellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'orchestrator-missing-python.log') *> $null
    Assert-Equal 13 $LASTEXITCODE 'missing Python runtime'
    if ((Get-Content -Raw -LiteralPath (Join-Path $testRoot 'orchestrator-missing-python.log')) -notmatch 'No compatible Python runtime was found') {
        throw 'Missing-Python recovery guidance is absent.'
    }
    $env:PATH = "$fakeBin;$originalPath"

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

    $desktopRuntime = Join-Path $fakeHome 'OpenAI\Codex\bin\build-id\codex.cmd'
    New-Item -ItemType Directory -Path (Split-Path $desktopRuntime -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $fakeCodexAccessDenied -Destination $desktopRuntime
    Copy-Item -LiteralPath $fakeCodex -Destination (Join-Path $fakeBin 'codex.cmd') -Force
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'path-runtime.calls'
    $env:FAKE_URI_LOG = Join-Path $testRoot 'path-runtime.uri'
    $env:FAKE_URI_SCENARIO = 'success'
    Restore-LocalizedArtifact
    & $powershellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $adapter `
        -ArtifactRoot $artifactRoot -MarketplacePath $marketplacePath `
        -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'path-runtime.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'an executable PATH Codex must precede the Desktop runtime'
    [array]$pathRuntimeCalls = Get-Content -LiteralPath $env:FAKE_CODEX_LOG
    Assert-Equal 3 $pathRuntimeCalls.Count 'PATH Codex probe and installation call count'
    Assert-Equal '--version' $pathRuntimeCalls[0] 'PATH Codex must be probed before installation'
    Assert-InstalledTree

    Copy-Item -LiteralPath $fakeCodex -Destination $desktopRuntime -Force
    Copy-Item -LiteralPath $fakeCodexAccessDenied -Destination (Join-Path $fakeBin 'codex.cmd') -Force
    $env:FAKE_CODEX_SCENARIO = 'success'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'desktop-runtime.calls'
    $env:FAKE_URI_LOG = Join-Path $testRoot 'desktop-runtime.uri'
    $env:FAKE_URI_SCENARIO = 'success'
    Restore-LocalizedArtifact
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $adapter `
        -ArtifactRoot $artifactRoot -MarketplacePath $marketplacePath `
        -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'desktop-runtime.log') *> $null
    Assert-Equal 0 $LASTEXITCODE 'Codex Desktop runtime must replace an inaccessible PATH candidate'
    [array]$desktopRuntimeCalls = Get-Content -LiteralPath $env:FAKE_CODEX_LOG
    Assert-Equal 3 $desktopRuntimeCalls.Count 'Desktop Codex probe and installation call count'
    Assert-Equal '--version' $desktopRuntimeCalls[0] 'Desktop Codex must be probed before installation'
    Assert-InstalledTree

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
    $artifactBeforeAccessFailure = Get-TreeEvidence $artifactRoot
    $env:FAKE_ARTIFACT_ACCESS_SCENARIO = 'blocked'
    $env:FAKE_ARTIFACT_ACCESS_LOG = Join-Path $testRoot 'artifact-access-blocked.calls'
    $env:FAKE_CODEX_LOG = Join-Path $testRoot 'artifact-access-blocked.codex.calls'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $orchestrator `
        -RepositoryRoot $repoRoot -PythonCommand $realPython `
        -ArtifactAccessScript $fakeArtifactAccess `
        -CodexCommand $fakeCodex -UriLauncherCommand $fakeUriLauncher `
        -LogPath (Join-Path $testRoot 'artifact-access-blocked.log') *> $null
    Assert-Equal 14 $LASTEXITCODE 'blocked artifact access recovery'
    Assert-Equal $artifactBeforeAccessFailure (Get-TreeEvidence $artifactRoot) 'blocked artifact access must stop before artifact mutation'
    Assert-Equal $false (Test-Path -LiteralPath $env:FAKE_CODEX_LOG) 'Codex must not run after artifact access recovery failure'
    if ((Get-Content -Raw -LiteralPath (Join-Path $testRoot 'artifact-access-blocked.log')) -notmatch 'Simulated bounded ACL recovery refusal') {
        throw 'Blocked artifact access recovery did not preserve actionable guidance.'
    }
    Remove-Item Env:\FAKE_ARTIFACT_ACCESS_SCENARIO, Env:\FAKE_ARTIFACT_ACCESS_LOG -ErrorAction SilentlyContinue

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
    $launcherCommand = "call `"$launcher`" -RepositoryRoot `"$repoRoot`" -CodexCommand `"$fakeCodex`" -UriLauncherCommand `"$fakeUriLauncher`""
    & $env:ComSpec /d /c $launcherCommand *> $null
    Assert-Equal 0 $LASTEXITCODE 'launcher automatic Python discovery'
    Assert-InstalledTree

    Write-Host 'PASS: local assembly, cache refresh, registration, reinstall, and failure contracts'
}
finally {
    foreach ($name in @('FAKE_CODEX_SCENARIO','FAKE_CODEX_LOG','FAKE_CODEX_INSTALL_SOURCE','FAKE_CODEX_INSTALL_TARGET','FAKE_URI_LOG','FAKE_URI_SCENARIO','FAKE_REAL_PYTHON','FAKE_PYTHON_EXECUTABLE','FAKE_PYTHON_CANDIDATE_LOG','FAKE_PYTHON_LAUNCHER_LOG','FAKE_PYTHON_RUNTIME_LOG','FAKE_PYTHON_INVALID_LOG','FAKE_ARTIFACT_ACCESS_SCENARIO','FAKE_ARTIFACT_ACCESS_LOG','GOVERNED_INSTALLER_NO_DELAY')) {
        Remove-Item "Env:\$name" -ErrorAction SilentlyContinue
    }
    $env:PATH = $originalPath
    $env:LOCALAPPDATA = $originalLocalAppData
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -Recurse -Force -LiteralPath $testRoot }
}
