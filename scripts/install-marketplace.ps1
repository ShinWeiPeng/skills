[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [string]$CodexCommand
)

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

function Invoke-CodexNative([string]$Command, [string[]]$Arguments) {
    $previousErrorActionPreference = $ErrorActionPreference
    $neutralWorkingDirectory = [System.IO.Path]::GetTempPath()
    Push-Location -LiteralPath $neutralWorkingDirectory
    try {
        # Windows PowerShell 5.1 promotes redirected native stderr to ErrorRecord.
        $ErrorActionPreference = 'Continue'
        $records = @(& $Command @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Pop-Location
    }
    $stdout = @($records | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { $_.ToString() }) -join "`n"
    $stderr = @($records | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { $_.Exception.Message }) -join "`n"
    return [pscustomobject]@{ ExitCode = $exitCode; Stdout = $stdout; Stderr = $stderr }
}

function Invoke-CodexChecked([string]$Command, [string[]]$Arguments) {
    $result = Invoke-CodexNative $Command $Arguments
    if ($result.ExitCode -ne 0) {
        $details = if ([string]::IsNullOrWhiteSpace($result.Stderr)) { $result.Stdout } else { $result.Stderr }
        $suffix = if ([string]::IsNullOrWhiteSpace($details)) { '' } else { ": $details" }
        throw "Codex command '$($Arguments -join ' ')' failed with exit code $($result.ExitCode)$suffix"
    }
    return $result.Stdout
}

function Get-CodexVersion([string]$Command) {
    $result = Invoke-CodexNative $Command @('--version')
    if ($result.ExitCode -ne 0 -or $result.Stdout -notmatch '(\d+\.\d+\.\d+)') { return $null }
    return [version]$Matches[1]
}

function Resolve-CodexCommand([string]$RequestedCommand) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedCommand)) {
        $resolved = Resolve-Path -LiteralPath $RequestedCommand -ErrorAction SilentlyContinue
        $result = if ($resolved) { $resolved.Path } else { $null }
        return $result
    }
    $candidate = Get-Command codex.exe,codex.cmd -ErrorAction SilentlyContinue | Select-Object -First 1
    $result = if ($candidate) { $candidate.Source } else { $null }
    return $result
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

try {
    $needsSystemPackages = (
        -not (Get-Command git.exe -ErrorAction SilentlyContinue) -or
        -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)
    )
    if ($needsSystemPackages -and -not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'winget is required. Install or repair App Installer, then rerun.'
    }
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
    $codexPath = Resolve-CodexCommand $CodexCommand
    $installedVersion = if ($codexPath) { Get-CodexVersion $codexPath } else { $null }
    if ($null -eq $installedVersion -or $installedVersion -lt [version]$codexVersion) {
        Invoke-Checked npm.cmd @('install','--global',("@openai/codex@$codexVersion"))
    }
    $codex = Resolve-CodexCommand $CodexCommand
    if ([string]::IsNullOrWhiteSpace($codex)) { throw 'Codex installation completed but the command is unavailable on PATH.' }
    $installedVersion = Get-CodexVersion $codex
    if ($null -eq $installedVersion -or $installedVersion -lt [version]$codexVersion) {
        throw "Codex $installedVersion is older than required $codexVersion after installation."
    }

    $loginStatus = Invoke-CodexNative $codex @('login','status')
    if ($loginStatus.ExitCode -ne 0) {
        if ($NonInteractive) { throw 'Codex authentication is required before a non-interactive install.' }
        [void](Invoke-CodexChecked $codex @('login','--device-auth'))
    }

    $marketplaces = Invoke-CodexChecked $codex @('plugin','marketplace','list','--json') | ConvertFrom-Json
    [array]$matchingMarketplaces = @($marketplaces.marketplaces | Where-Object name -eq $marketplace)
    [array]$matchingGitMarketplaces = @($matchingMarketplaces | Where-Object {
        $sourceProperty = $_.PSObject.Properties['marketplaceSource']
        if ($null -eq $sourceProperty -or $null -eq $sourceProperty.Value) { return $false }
        $sourceTypeProperty = $sourceProperty.Value.PSObject.Properties['sourceType']
        $sourceLocationProperty = $sourceProperty.Value.PSObject.Properties['source']
        return (
            $null -ne $sourceTypeProperty -and $sourceTypeProperty.Value -eq 'git' -and
            $null -ne $sourceLocationProperty -and $sourceLocationProperty.Value -ceq $repository
        )
    })
    if ($matchingMarketplaces.Count -eq 1 -and $matchingGitMarketplaces.Count -eq 1) {
        [void](Invoke-CodexChecked $codex @('plugin','marketplace','upgrade',$marketplace))
    } elseif ($matchingMarketplaces.Count -gt 0) {
        throw "Marketplace '$marketplace' conflicts with the required Git Marketplace '$repository'. Remove or rename the conflicting source, then rerun."
    } else {
        [void](Invoke-CodexChecked $codex @('plugin','marketplace','add',$repository,'--ref',$ref,'--sparse','.agents/plugins','--sparse','plugins/governed-engineering-skills'))
    }
    [void](Invoke-CodexChecked $codex @('plugin','add',("$plugin@$marketplace")))
    $plugins = Invoke-CodexChecked $codex @('plugin','list','--json') | ConvertFrom-Json
    if (@($plugins.installed | Where-Object pluginId -eq "$plugin@$marketplace").Count -eq 0) {
        throw 'Codex did not report the expected installed Plugin.'
    }
    Write-Host "READY: $plugin is installed from $marketplace. Start a new Codex task."
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
