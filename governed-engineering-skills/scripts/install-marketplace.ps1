[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [ValidateSet('', 'codex', 'claude', 'both')]
    [string]$Target = '',
    [string]$CodexCommand,
    [string]$ClaudeCommand
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$marketplace = 'governed-engineering'
$repository = 'https://github.com/ShinWeiPeng/skills.git'
$ref = 'marketplace-release'
$plugin = 'governed-engineering-skills'
$codexVersion = '0.147.0'
$claudeMarketplace = 'mattpocock'
$claudeSource = 'ShinWeiPeng/skills'
$claudePlugin = 'mattpocock-skills'
$claudeInstallDocs = 'https://code.claude.com/docs/en/setup'

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

function Invoke-CodexChecked([string]$Command, [string[]]$Arguments, [string]$Product = 'Codex') {
    $result = Invoke-CodexNative $Command $Arguments
    if ($result.ExitCode -ne 0) {
        $details = if ([string]::IsNullOrWhiteSpace($result.Stderr)) { $result.Stdout } else { $result.Stderr }
        $suffix = if ([string]::IsNullOrWhiteSpace($details)) { '' } else { ": $details" }
        throw "$Product command '$($Arguments -join ' ')' failed with exit code $($result.ExitCode)$suffix"
    }
    return $result.Stdout
}

function Get-CodexVersion([string]$Command) {
    $result = Invoke-CodexNative $Command @('--version')
    if ($result.ExitCode -ne 0 -or $result.Stdout -notmatch '(\d+\.\d+\.\d+)') { return $null }
    return [version]$Matches[1]
}

function Resolve-NativeCommand([string]$RequestedCommand, [string[]]$Names) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedCommand)) {
        $resolved = Resolve-Path -LiteralPath $RequestedCommand -ErrorAction SilentlyContinue
        $result = if ($resolved) { $resolved.Path } else { $null }
        return $result
    }
    $candidate = Get-Command $Names -ErrorAction SilentlyContinue | Select-Object -First 1
    $result = if ($candidate) { $candidate.Source } else { $null }
    return $result
}

function Resolve-CodexCommand([string]$RequestedCommand) {
    return Resolve-NativeCommand $RequestedCommand @('codex.exe','codex.cmd')
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Select-InstallTarget([string]$RequestedTarget) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedTarget)) { return $RequestedTarget }
    if ($NonInteractive) { return 'codex' }
    Write-Host 'Install Governed Engineering Skills for:'
    Write-Host '  1) Codex Desktop and CLI'
    Write-Host '  2) Claude Code'
    Write-Host '  3) Both'
    while ($true) {
        $answer = Read-Host 'Choose 1, 2 or 3 [1]'
        switch ($answer.Trim()) {
            '' { return 'codex' }
            '1' { return 'codex' }
            '2' { return 'claude' }
            '3' { return 'both' }
            default { Write-Host 'Enter 1, 2 or 3.' }
        }
    }
}

function Install-Prerequisites([bool]$NeedsNode) {
    $needsSystemPackages = (
        -not (Get-Command git.exe -ErrorAction SilentlyContinue) -or
        ($NeedsNode -and -not (Get-Command npm.cmd -ErrorAction SilentlyContinue))
    )
    if ($needsSystemPackages -and -not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'winget is required. Install or repair App Installer, then rerun.'
    }
    if ($NonInteractive -and $needsSystemPackages -and -not (Test-IsAdministrator)) {
        throw 'Non-interactive prerequisite installation requires an elevated PowerShell session.'
    }
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
        Invoke-Checked winget.exe @('install','--id','Git.Git','--exact','--accept-source-agreements','--accept-package-agreements')
        $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
    }
    if ($NeedsNode -and -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        Invoke-Checked winget.exe @('install','--id','OpenJS.NodeJS.LTS','--exact','--accept-source-agreements','--accept-package-agreements')
        $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
    }
}

function Install-Codex {
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
}

function Test-ClaudeMarketplaceSource($Entry) {
    $repoProperty = $Entry.PSObject.Properties['repo']
    $urlProperty = $Entry.PSObject.Properties['url']
    $repo = if ($null -ne $repoProperty) { [string]$repoProperty.Value } else { '' }
    $url = if ($null -ne $urlProperty) { [string]$urlProperty.Value } else { '' }
    return (
        $repo -eq $claudeSource -or
        $url -eq "https://github.com/$claudeSource" -or
        $url -eq "https://github.com/$claudeSource.git"
    )
}

function Install-Claude {
    $claude = Resolve-NativeCommand $ClaudeCommand @('claude.exe','claude.cmd')
    if ([string]::IsNullOrWhiteSpace($claude)) {
        throw "Claude Code CLI 'claude' was not found on PATH. Install Claude Code from $claudeInstallDocs, open a new terminal, then rerun this installer."
    }

    $marketplaces = Invoke-CodexChecked $claude @('plugin','marketplace','list','--json') 'Claude Code' | ConvertFrom-Json
    [array]$matchingMarketplaces = @($marketplaces | Where-Object { $_.name -eq $claudeMarketplace })
    [array]$matchingSources = @($matchingMarketplaces | Where-Object { Test-ClaudeMarketplaceSource $_ })
    if ($matchingMarketplaces.Count -eq 1 -and $matchingSources.Count -eq 1) {
        [void](Invoke-CodexChecked $claude @('plugin','marketplace','update',$claudeMarketplace) 'Claude Code')
    } elseif ($matchingMarketplaces.Count -gt 0) {
        throw "Claude Code marketplace '$claudeMarketplace' conflicts with the required source '$claudeSource'. Remove it with 'claude plugin marketplace remove $claudeMarketplace', then rerun."
    } else {
        [void](Invoke-CodexChecked $claude @('plugin','marketplace','add',$claudeSource) 'Claude Code')
    }
    [void](Invoke-CodexChecked $claude @('plugin','install',("$claudePlugin@$claudeMarketplace"),'--scope','user') 'Claude Code')
    $plugins = Invoke-CodexChecked $claude @('plugin','list','--json') 'Claude Code' | ConvertFrom-Json
    if (@($plugins | Where-Object { $_.id -eq "$claudePlugin@$claudeMarketplace" }).Count -eq 0) {
        throw 'Claude Code did not report the expected installed Plugin.'
    }
    Write-Host "READY: $claudePlugin is installed from $claudeMarketplace. Start a new Claude Code session."
}

try {
    $selectedTarget = Select-InstallTarget $Target
    $installCodex = $selectedTarget -in @('codex','both')
    $installClaude = $selectedTarget -in @('claude','both')
    Install-Prerequisites $installCodex

    $failures = @()
    if ($installCodex) {
        try { Install-Codex } catch { $failures += "Codex: $($_.Exception.Message)" }
    }
    if ($installClaude) {
        try { Install-Claude } catch { $failures += "Claude Code: $($_.Exception.Message)" }
    }
    if ($failures.Count -gt 0) { throw ($failures -join [Environment]::NewLine) }
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
