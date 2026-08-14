[CmdletBinding()]
param([switch]$NonInteractive)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$marketplace = 'governed-engineering'
$repository = 'https://github.com/ShinWeiPeng/skills.git'
$ref = 'marketplace-release'
$plugin = 'governed-engineering-skills'
$codexVersion = '0.147.0'

function Invoke-Checked([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed with exit code $LASTEXITCODE" }
}

function Get-CodexVersion([string]$Command) {
    $output = @(& $Command --version 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $output -notmatch '(\d+\.\d+\.\d+)') { return $null }
    return [version]$Matches[1]
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

try {
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'winget is required. Install or repair App Installer, then rerun.'
    }
    $needsSystemPackages = (
        -not (Get-Command git.exe -ErrorAction SilentlyContinue) -or
        -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)
    )
    if ($NonInteractive -and $needsSystemPackages -and -not (Test-IsAdministrator)) {
        throw 'Non-interactive prerequisite installation requires an elevated PowerShell session.'
    }
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
        Invoke-Checked winget.exe @('install','--id','Git.Git','--exact','--accept-source-agreements','--accept-package-agreements')
    }
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        Invoke-Checked winget.exe @('install','--id','OpenJS.NodeJS.LTS','--exact','--accept-source-agreements','--accept-package-agreements')
        $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
    }
    $codexCommand = Get-Command codex.exe,codex.cmd -ErrorAction SilentlyContinue | Select-Object -First 1
    $installedVersion = if ($codexCommand) { Get-CodexVersion $codexCommand.Source } else { $null }
    if ($null -eq $installedVersion -or $installedVersion -lt [version]$codexVersion) {
        Invoke-Checked npm.cmd @('install','--global',("@openai/codex@$codexVersion"))
    }
    $codexCommand = Get-Command codex.exe,codex.cmd -ErrorAction SilentlyContinue | Select-Object -First 1
    $codex = if ($codexCommand) { $codexCommand.Source } else { $null }
    if ([string]::IsNullOrWhiteSpace($codex)) { throw 'Codex installation completed but the command is unavailable on PATH.' }
    $installedVersion = Get-CodexVersion $codex
    if ($null -eq $installedVersion -or $installedVersion -lt [version]$codexVersion) {
        throw "Codex $installedVersion is older than required $codexVersion after installation."
    }

    & $codex login status *> $null
    if ($LASTEXITCODE -ne 0) {
        if ($NonInteractive) { throw 'Codex authentication is required before a non-interactive install.' }
        Invoke-Checked $codex @('login','--device-auth')
    }

    $marketplaces = @(& $codex plugin marketplace list --json 2>$null) -join "`n" | ConvertFrom-Json
    if (@($marketplaces.marketplaces | Where-Object name -eq $marketplace).Count -gt 0) {
        Invoke-Checked $codex @('plugin','marketplace','upgrade',$marketplace)
    } else {
        Invoke-Checked $codex @('plugin','marketplace','add',$repository,'--ref',$ref,'--sparse','.agents/plugins','--sparse','plugins/governed-engineering-skills')
    }
    Invoke-Checked $codex @('plugin','add',("$plugin@$marketplace"))
    $plugins = @(& $codex plugin list --json 2>$null) -join "`n" | ConvertFrom-Json
    if (@($plugins.installed | Where-Object pluginId -eq "$plugin@$marketplace").Count -eq 0) {
        throw 'Codex did not report the expected installed Plugin.'
    }
    Write-Host "READY: $plugin is installed from $marketplace. Start a new Codex task."
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
