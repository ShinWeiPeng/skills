[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$PythonCommand,
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

function Invoke-AssemblyStep {
    param([string]$Python, [string[]]$Arguments, [string]$Description)
    Write-InstallLog $Description
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $Python @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }
    foreach ($line in $output) { Write-InstallLog ([string]$line) }
    if ($exitCode -ne 0) {
        Write-InstallLog "$Description failed with exit code $exitCode." 'ERROR'
        exit 30
    }
}

try {
    Set-Content -LiteralPath $LogPath -Value '' -Encoding utf8
    if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
        $RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    }
    $RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
    $assembler = Join-Path $RepositoryRoot 'scripts\assemble_plugin.py'
    $validator = Join-Path $RepositoryRoot 'scripts\validate_distribution.py'
    $adapter = Join-Path $RepositoryRoot 'plugins\governed-engineering-skills\scripts\install-local.ps1'
    $artifact = Join-Path $RepositoryRoot 'dist\governed-engineering-skills'
    $marketplace = Join-Path $RepositoryRoot '.agents\plugins\marketplace.json'
    foreach ($required in @($assembler, $validator, $adapter, $marketplace)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            Write-InstallLog "Required installer component is missing: $required" 'ERROR'
            exit 10
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($PythonCommand)) {
        $python = $PythonCommand
    }
    else {
        $pythonApplication = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $pythonApplication -or [string]::IsNullOrWhiteSpace([string]$pythonApplication.Source)) {
            Write-InstallLog 'Python was not found. Install Python 3.11 or newer, then run the installer again.' 'ERROR'
            exit 13
        }
        $python = $pythonApplication.Source
    }

    Invoke-AssemblyStep $python @($assembler, 'assemble', '--repo-root', $RepositoryRoot, '--output', $artifact) 'Assembling the governed Plugin.'
    Invoke-AssemblyStep $python @($validator) 'Validating the assembled Plugin distribution.'
    Invoke-AssemblyStep $python @($assembler, 'localize', '--repo-root', $RepositoryRoot, '--artifact', $artifact) 'Refreshing the local Codex cache identity.'
    $adapterArguments = @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $adapter,
        '-ArtifactRoot', $artifact,
        '-MarketplacePath', $marketplace,
        '-LogPath', $LogPath
    )
    if (-not [string]::IsNullOrWhiteSpace($CodexCommand)) {
        $adapterArguments += @('-CodexCommand', $CodexCommand)
    }
    if (-not [string]::IsNullOrWhiteSpace($UriLauncherCommand)) {
        $adapterArguments += @('-UriLauncherCommand', $UriLauncherCommand)
    }
    & powershell.exe @adapterArguments
    exit $LASTEXITCODE
}
catch {
    Write-InstallLog ("Unexpected installer orchestration failure: " + $_.Exception.Message) 'ERROR'
    exit 99
}
