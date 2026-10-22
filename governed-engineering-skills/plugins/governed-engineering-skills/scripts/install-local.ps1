[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArtifactRoot,
    [Parameter(Mandatory = $true)][string]$MarketplacePath,
    [string]$CodexCommand,
    [string]$UriLauncherCommand,
    [string]$LogPath = (Join-Path ([System.IO.Path]::GetTempPath()) 'governed-engineering-skills-install.log')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-InstallLog {
    param([string]$Message, [ValidateSet('INFO','WARN','ERROR')][string]$Level = 'INFO')
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    $line | Out-File -FilePath $LogPath -Append -Encoding utf8
    Write-Host $line
}

function Stop-Install {
    param([int]$ExitCode, [string]$Message)
    Write-InstallLog $Message 'ERROR'
    Write-InstallLog "Installation log: $LogPath"
    exit $ExitCode
}

function Resolve-CodexCommand {
    $candidates = [System.Collections.Generic.List[string]]::new()
    $pathCommand = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $pathCommand -and -not [string]::IsNullOrWhiteSpace([string]$pathCommand.Source)) {
        $candidates.Add([string]$pathCommand.Source)
    }

    $localAppData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
    if (-not [string]::IsNullOrWhiteSpace($localAppData)) {
        $bin = Join-Path $localAppData 'OpenAI\Codex\bin'
        foreach ($name in @('codex.exe','codex.cmd')) {
            $candidate = Join-Path $bin $name
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $candidates.Add((Resolve-Path -LiteralPath $candidate).Path)
            }
        }
        if (Test-Path -LiteralPath $bin -PathType Container) {
            Get-ChildItem -LiteralPath $bin -File -Recurse -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -in @('codex.exe','codex.cmd') } |
                Sort-Object LastWriteTimeUtc -Descending |
                ForEach-Object { $candidates.Add($_.FullName) }
        }
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($candidate in $candidates) {
        if (-not $seen.Add($candidate)) { continue }
        $probe = Invoke-Codex $candidate @('--version')
        if ($probe.ExitCode -eq 0) {
            Write-InstallLog "Selected executable Codex runtime: $candidate"
            return $candidate
        }
        Write-InstallLog "Codex runtime candidate could not execute; trying the next candidate: $candidate" 'WARN'
    }
    Stop-Install 11 'Codex CLI was not found or could not execute from PATH or the Codex Desktop runtime. Install or repair Codex and try again.'
}

function Invoke-Codex {
    param([string]$Command, [string[]]$Arguments)
    Write-InstallLog ('Running: codex ' + ($Arguments -join ' '))
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $Command @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    catch { $output = @($_.Exception.Message); $exitCode = 9009 }
    finally { $ErrorActionPreference = $oldPreference }
    $lines = @($output | ForEach-Object { [string]$_ })
    foreach ($line in $lines) { Write-InstallLog $line }
    return [pscustomobject]@{ ExitCode = $exitCode; Output = $lines }
}

function Assert-NoAccessDenial {
    param($Result)
    if (($Result.Output -join "`n") -match '(?i)access\s+is\s+denied|access.*denied') {
        Stop-Install 12 'Windows denied access to Codex CLI. Repair Codex or use an account allowed to execute it.'
    }
}

function Open-PluginPage {
    param([string]$Uri, [string]$LauncherCommand)
    try {
        if (-not [string]::IsNullOrWhiteSpace($LauncherCommand)) {
            & $LauncherCommand $Uri
            if ($LASTEXITCODE -ne 0) { return $false }
        }
        else { Start-Process -FilePath $Uri -ErrorAction Stop | Out-Null }
        return $true
    }
    catch { return $false }
}

try {
    $ArtifactRoot = [System.IO.Path]::GetFullPath($ArtifactRoot)
    $MarketplacePath = [System.IO.Path]::GetFullPath($MarketplacePath)
    $manifestPath = Join-Path $ArtifactRoot '.codex-plugin\plugin.json'
    $inventoryPath = Join-Path $ArtifactRoot 'artifact-inventory.json'
    foreach ($required in @($MarketplacePath, $manifestPath, $inventoryPath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { Stop-Install 10 "The assembled Plugin is incomplete or stale; required file was not found: $required" }
    }
    $marketplace = Get-Content -Raw -Encoding utf8 -LiteralPath $MarketplacePath | ConvertFrom-Json
    $manifest = Get-Content -Raw -Encoding utf8 -LiteralPath $manifestPath | ConvertFrom-Json
    $inventory = Get-Content -Raw -Encoding utf8 -LiteralPath $inventoryPath | ConvertFrom-Json
    $pluginName = [string]$manifest.name
    $marketplaceName = [string]$marketplace.name
    $entry = @($marketplace.plugins | Where-Object { $_.name -eq $pluginName }) | Select-Object -First 1
    if ($null -eq $entry -or [string]::IsNullOrWhiteSpace($marketplaceName) -or [string]::IsNullOrWhiteSpace($pluginName)) {
        Stop-Install 10 'Marketplace and Plugin identities are incomplete.'
    }
    $marketplaceRoot = [System.IO.Path]::GetFullPath((Split-Path $MarketplacePath -Parent | Split-Path -Parent | Split-Path -Parent))
    $resolvedSource = [System.IO.Path]::GetFullPath((Join-Path $marketplaceRoot ([string]$entry.source.path)))
    if (-not [string]::Equals($resolvedSource.TrimEnd('\'), $ArtifactRoot.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Install 10 "Marketplace source resolves to '$resolvedSource', expected '$ArtifactRoot'."
    }
    if ([string]$inventory.plugin_name -ne $pluginName -or [string]$inventory.version -ne [string]$manifest.version -or [string]$manifest.version -notmatch '\+codex\.') {
        Stop-Install 10 'The local artifact identity or cachebuster is invalid.'
    }

    $codex = if ([string]::IsNullOrWhiteSpace($CodexCommand)) { Resolve-CodexCommand } else { $CodexCommand }
    $marketplaceResult = Invoke-Codex $codex @('plugin','marketplace','add',$marketplaceRoot)
    Assert-NoAccessDenial $marketplaceResult
    if ($marketplaceResult.ExitCode -ne 0) {
        $text = $marketplaceResult.Output -join "`n"
        if ($text -notmatch '(?i)already.*(exists|registered)|marketplace.*(exists|registered)|duplicate') {
            Stop-Install 20 "Unable to register the local Marketplace (Codex exit $($marketplaceResult.ExitCode))."
        }
        Write-InstallLog 'Marketplace is already registered; continuing with reinstall.' 'WARN'
    }

    $pluginResult = Invoke-Codex $codex @('plugin','add',("$pluginName@$marketplaceName"))
    Assert-NoAccessDenial $pluginResult
    if ($pluginResult.ExitCode -ne 0) {
        Stop-Install 21 "Unable to install the Plugin (Codex exit $($pluginResult.ExitCode)). The local Marketplace remains registered; rerun this installer to retry."
    }

    $uri = 'codex://plugins/{0}?marketplacePath={1}' -f ([Uri]::EscapeDataString($pluginName)), ([Uri]::EscapeDataString($MarketplacePath))
    if (-not (Open-PluginPage $uri $UriLauncherCommand)) { Stop-Install 23 "Plugin installed, but its Codex page could not be opened. Open manually: $uri" }
    Write-InstallLog "READY: '$pluginName' is installed from local Marketplace '$marketplaceName'."
    Write-InstallLog 'Start a new Codex task so the refreshed skills are loaded.' 'WARN'
    exit 0
}
catch {
    if ($_.Exception.Message -match '(?i)access.*denied') { Stop-Install 12 ('Windows denied access: ' + $_.Exception.Message) }
    Stop-Install 99 ('Unexpected installer failure: ' + $_.Exception.Message)
}
