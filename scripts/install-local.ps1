[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$PythonCommand,
    [string]$CodexCommand,
    [string]$UriLauncherCommand,
    [string]$ArtifactAccessScript,
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
    $pythonSelector = Join-Path $RepositoryRoot 'scripts\python-runtime-selection.ps1'
    if ([string]::IsNullOrWhiteSpace($ArtifactAccessScript)) {
        $ArtifactAccessScript = Join-Path $RepositoryRoot 'scripts\windows-artifact-access.ps1'
    }
    $artifactAccess = [System.IO.Path]::GetFullPath($ArtifactAccessScript)
    $adapter = Join-Path $RepositoryRoot 'plugins\governed-engineering-skills\scripts\install-local.ps1'
    $artifact = Join-Path $RepositoryRoot 'dist\governed-engineering-skills'
    $marketplace = Join-Path $RepositoryRoot '.agents\plugins\marketplace.json'
    foreach ($required in @($assembler, $validator, $pythonSelector, $artifactAccess, $adapter, $marketplace)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            Write-InstallLog "Required installer component is missing: $required" 'ERROR'
            exit 10
        }
    }

    . $pythonSelector
    $pythonSelection = Resolve-CompatiblePython -ExplicitCommand $PythonCommand
    foreach ($diagnostic in $pythonSelection.Diagnostics) {
        Write-InstallLog ([string]$diagnostic.Message) ([string]$diagnostic.Level)
    }
    if (-not $pythonSelection.Valid) { exit 13 }
    $selectedPython = $pythonSelection.Executable

    . $artifactAccess
    $accessDecision = Ensure-GovernedArtifactAccess -RepositoryRoot $RepositoryRoot -ArtifactPath $artifact
    Write-InstallLog ([string]$accessDecision.Diagnostic) $(if ($accessDecision.Valid) { 'INFO' } else { 'ERROR' })
    if (-not $accessDecision.Valid) { exit 14 }

    Invoke-AssemblyStep $selectedPython @($assembler, 'assemble', '--repo-root', $RepositoryRoot, '--output', $artifact) 'Assembling the governed Plugin.'
    Invoke-AssemblyStep $selectedPython @($validator) 'Validating the assembled Plugin distribution.'
    Invoke-AssemblyStep $selectedPython @($assembler, 'localize', '--repo-root', $RepositoryRoot, '--artifact', $artifact) 'Refreshing the local Codex cache identity.'
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
