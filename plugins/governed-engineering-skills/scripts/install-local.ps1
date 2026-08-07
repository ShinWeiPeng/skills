[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:LogPath = Join-Path ([System.IO.Path]::GetTempPath()) 'governed-engineering-skills-install.log'

function Write-InstallLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [ValidateSet('INFO', 'WARN', 'ERROR')]
        [string]$Level = 'INFO'
    )

    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    $line | Out-File -FilePath $script:LogPath -Append -Encoding utf8
    if ($Level -eq 'ERROR') {
        Write-Host $line -ForegroundColor Red
    }
    elseif ($Level -eq 'WARN') {
        Write-Host $line -ForegroundColor Yellow
    }
    else {
        Write-Host $line
    }
}

function Stop-Install {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ExitCode,

        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-InstallLog -Message $Message -Level ERROR
    Write-InstallLog -Message "Installation log: $script:LogPath"
    exit $ExitCode
}

function Resolve-CodexCommand {
    $command = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $command) {
        return $command.Source
    }

    $localAppData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
    if (-not [string]::IsNullOrWhiteSpace($localAppData)) {
        $desktopBin = Join-Path $localAppData 'OpenAI\Codex\bin'
        foreach ($fileName in @('codex.exe', 'codex.cmd')) {
            $desktopCandidate = Join-Path $desktopBin $fileName
            if (Test-Path -LiteralPath $desktopCandidate -PathType Leaf) {
                Write-InstallLog -Message "Codex CLI resolved from the Codex Desktop runtime: $desktopCandidate"
                return (Resolve-Path -LiteralPath $desktopCandidate).Path
            }
        }

        if (Test-Path -LiteralPath $desktopBin -PathType Container) {
            $nestedDesktopCandidate = Get-ChildItem -LiteralPath $desktopBin `
                -File -Recurse -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -in @('codex.exe', 'codex.cmd') } |
                Sort-Object LastWriteTimeUtc -Descending |
                Select-Object -First 1
            if ($null -ne $nestedDesktopCandidate) {
                Write-InstallLog -Message "Codex CLI resolved from the Codex Desktop runtime: $($nestedDesktopCandidate.FullName)"
                return $nestedDesktopCandidate.FullName
            }
        }
    }

    Stop-Install -ExitCode 11 -Message (
        'Codex CLI was not found in PATH or the Codex Desktop runtime below ' +
        '%LOCALAPPDATA%\OpenAI\Codex\bin. Install or repair Codex, then ' +
        'double-click the launcher again.'
    )
}

function Invoke-CodexCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CodexCommand,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-InstallLog -Message ('Running: codex ' + ($Arguments -join ' '))
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $CodexCommand @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    catch {
        $exitCode = 9009
        $output = @($_.Exception.Message)
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $lines = @($output | ForEach-Object { $_.ToString() })
    foreach ($line in $lines) {
        Write-InstallLog -Message $line
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $lines
    }
}

function Open-CodexPluginPage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PluginUri
    )

    Write-InstallLog -Message "Codex plugin page: $PluginUri"
    $capturePath = [Environment]::GetEnvironmentVariable(
        'GOVERNED_PLUGIN_URI_CAPTURE'
    )
    $simulateFailure = [Environment]::GetEnvironmentVariable(
        'GOVERNED_PLUGIN_URI_LAUNCH_FAILURE'
    )

    if ($simulateFailure -eq '1') {
        return $false
    }

    try {
        if (-not [string]::IsNullOrWhiteSpace($capturePath)) {
            Set-Content -LiteralPath $capturePath -Value $PluginUri -Encoding utf8
        }
        else {
            Start-Process -FilePath $PluginUri -ErrorAction Stop | Out-Null
        }
        return $true
    }
    catch {
        Write-InstallLog -Message (
            'Unable to open the Codex plugin page: ' + $_.Exception.Message
        ) -Level ERROR
        return $false
    }
}

function Assert-NoCodexAccessDenial {
    param(
        [Parameter(Mandatory = $true)]
        $Result
    )

    $text = $Result.Output -join "`n"
    if ($text -match '(?i)access\s+is\s+denied|access.*denied') {
        Stop-Install -ExitCode 12 -Message "Windows denied access to Codex CLI. Repair the Codex installation or run the launcher from an account allowed to execute Codex. Detail: $text"
    }
}

try {
    Set-Content -LiteralPath $script:LogPath -Value '' -Encoding utf8

    $pluginRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $pluginRoot '..\..'))
    $marketplacePath = Join-Path $repoRoot '.agents\plugins\marketplace.json'
    $pluginManifestPath = Join-Path $pluginRoot '.codex-plugin\plugin.json'

    foreach ($requiredPath in @($marketplacePath, $pluginManifestPath)) {
        if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            Stop-Install -ExitCode 10 -Message "Required manifest was not found: $requiredPath"
        }
    }

    $marketplace = Get-Content -Raw -Encoding utf8 -LiteralPath $marketplacePath |
        ConvertFrom-Json
    $pluginManifest = Get-Content -Raw -Encoding utf8 -LiteralPath $pluginManifestPath |
        ConvertFrom-Json

    $marketplaceName = [string]$marketplace.name
    $pluginName = [string]$pluginManifest.name
    if ([string]::IsNullOrWhiteSpace($marketplaceName) -or
        [string]::IsNullOrWhiteSpace($pluginName)) {
        Stop-Install -ExitCode 10 -Message 'Marketplace or plugin name is missing from its manifest.'
    }

    $entry = @($marketplace.plugins | Where-Object { $_.name -eq $pluginName }) |
        Select-Object -First 1
    if ($null -eq $entry) {
        Stop-Install -ExitCode 10 -Message "Marketplace '$marketplaceName' does not contain plugin '$pluginName'."
    }

    $declaredSource = [string]$entry.source.path
    $resolvedSource = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $declaredSource))
    if (-not [string]::Equals(
            $resolvedSource.TrimEnd('\'),
            $pluginRoot.TrimEnd('\'),
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        Stop-Install -ExitCode 10 -Message "Marketplace source resolves to '$resolvedSource', expected '$pluginRoot'."
    }

    $codexCommand = Resolve-CodexCommand
    Write-InstallLog -Message "Repository: $repoRoot"
    Write-InstallLog -Message "Marketplace: $marketplaceName"
    Write-InstallLog -Message "Plugin: $pluginName"

    $marketplaceResult = Invoke-CodexCommand -CodexCommand $codexCommand -Arguments @(
        'plugin', 'marketplace', 'add', $repoRoot
    )
    Assert-NoCodexAccessDenial -Result $marketplaceResult
    if ($marketplaceResult.ExitCode -ne 0) {
        $marketplaceText = $marketplaceResult.Output -join "`n"
        if ($marketplaceText -match '(?i)already.*(exists|registered)|marketplace.*(exists|registered)|duplicate') {
            Write-InstallLog -Message 'Marketplace is already registered; continuing to the Codex Desktop install page.' -Level WARN
        }
        else {
            Stop-Install -ExitCode 20 -Message (
                "Unable to add the local marketplace (Codex exit " +
                "$($marketplaceResult.ExitCode)). Review the CLI output above."
            )
        }
    }

    $encodedPluginName = [Uri]::EscapeDataString($pluginName)
    $encodedMarketplacePath = [Uri]::EscapeDataString($marketplacePath)
    $pluginUri = 'codex://plugins/{0}?marketplacePath={1}' -f (
        $encodedPluginName,
        $encodedMarketplacePath
    )
    if (-not (Open-CodexPluginPage -PluginUri $pluginUri)) {
        Stop-Install -ExitCode 23 -Message (
            'The marketplace is registered, but the Codex Desktop plugin page ' +
            "could not be opened. Open this URI manually: $pluginUri"
        )
    }

    Write-InstallLog -Message "READY: marketplace '$marketplaceName' is registered."
    Write-InstallLog -Message (
        "ACTION REQUIRED: In Codex Desktop, click Install for '$pluginName'."
    ) -Level WARN
    Write-InstallLog -Message (
        'After installation, start a new Codex task so the plugin skills are loaded.'
    )
    exit 0
}
catch {
    $message = $_.Exception.Message
    if ($message -match '(?i)access.*denied') {
        Stop-Install -ExitCode 12 -Message "Windows denied access to Codex CLI. Repair the Codex installation or run the launcher from an account allowed to execute Codex. Detail: $message"
    }
    Stop-Install -ExitCode 99 -Message "Unexpected installer failure: $message"
}
