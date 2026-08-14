Set-StrictMode -Version Latest

$selectionPolicy = Join-Path $PSScriptRoot 'python-runtime-selection-policy.ps1'
if (-not (Test-Path -LiteralPath $selectionPolicy -PathType Leaf)) {
    throw "Python runtime selection policy is missing: $selectionPolicy"
}
. $selectionPolicy

function New-PythonProbeResult {
    param(
        [bool]$Valid,
        [string]$Label,
        [AllowNull()][string]$Version,
        [AllowNull()][string]$Executable,
        [AllowNull()][string]$Reason
    )
    return [pscustomobject]@{
        Valid = $Valid
        Label = $Label
        Version = $Version
        Executable = $Executable
        Reason = $Reason
    }
}

function New-PythonSelectionResult {
    param(
        [bool]$Valid,
        [AllowNull()][string]$Version,
        [AllowNull()][string]$Executable,
        [object[]]$Diagnostics
    )
    return [pscustomobject]@{
        Valid = $Valid
        Version = $Version
        Executable = $Executable
        Diagnostics = @($Diagnostics)
    }
}

function Invoke-PythonProbe {
    param(
        [string]$Command,
        [string[]]$PrefixArguments = @(),
        [string]$Label
    )
    $probeScript = "import sys; print('CODEX_PYTHON_PROBE|%d|%d|%d|%s' % (sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.executable))"
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $probeOutput = @(& $Command @PrefixArguments '-c' $probeScript 2>&1)
        $probeExitCode = $LASTEXITCODE
    }
    catch {
        return New-PythonProbeResult $false $Label $null $null $_.Exception.Message
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }

    if ($probeExitCode -ne 0) {
        $probeDiagnostic = (@($probeOutput | ForEach-Object { [string]$_ }) -join ' ').Trim()
        if ([string]::IsNullOrWhiteSpace($probeDiagnostic)) { $probeDiagnostic = 'no diagnostic output' }
        return New-PythonProbeResult $false $Label $null $null "probe exited with code $probeExitCode ($probeDiagnostic)"
    }
    $probeLine = @($probeOutput | ForEach-Object { [string]$_ } | Where-Object {
        $_ -match '^CODEX_PYTHON_PROBE\|\d+\|\d+\|\d+\|.+$'
    } | Select-Object -Last 1)
    if ($probeLine.Count -ne 1 -or $probeLine[0] -notmatch '^CODEX_PYTHON_PROBE\|(\d+)\|(\d+)\|(\d+)\|(.+)$') {
        return New-PythonProbeResult $false $Label $null $null 'probe returned malformed version information'
    }

    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $micro = [int]$Matches[3]
    $reportedExecutable = [string]$Matches[4]
    $version = "$major.$minor.$micro"
    if (-not (($major -gt 3) -or ($major -eq 3 -and $minor -ge 11))) {
        return New-PythonProbeResult $false $Label $version $reportedExecutable "Python $version is older than the required Python 3.11"
    }
    try {
        $absoluteExecutable = [System.IO.Path]::GetFullPath($reportedExecutable)
    }
    catch {
        return New-PythonProbeResult $false $Label $version $reportedExecutable 'probe returned an invalid executable path'
    }
    if (-not (Test-Path -LiteralPath $absoluteExecutable -PathType Leaf)) {
        return New-PythonProbeResult $false $Label $version $absoluteExecutable 'probe returned an executable path that does not exist'
    }
    return New-PythonProbeResult $true $Label $version $absoluteExecutable $null
}

function Resolve-CompatiblePython {
    param([string]$ExplicitCommand)

    $diagnostics = @()
    if (-not [string]::IsNullOrWhiteSpace($ExplicitCommand)) {
        $explicitResult = Invoke-PythonProbe -Command $ExplicitCommand -Label 'explicit Python'
        $explicitAction = Select-CompatiblePythonCandidate -Stage explicit -ProbeResult $explicitResult
        if ($explicitAction -eq 'reject-explicit') {
            $diagnostics += [pscustomobject]@{
                Level = 'ERROR'
                Message = "Rejected explicit Python command '$ExplicitCommand': $($explicitResult.Reason). Install Python 3.11 or newer, or pass its executable path with -PythonCommand."
            }
            return New-PythonSelectionResult $false $null $null $diagnostics
        }
        $diagnostics += [pscustomobject]@{ Level = 'INFO'; Message = "Selected explicit Python $($explicitResult.Version): $($explicitResult.Executable)" }
        return New-PythonSelectionResult $true $explicitResult.Version $explicitResult.Executable $diagnostics
    }

    $pathApplication = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $pathApplication -and -not [string]::IsNullOrWhiteSpace([string]$pathApplication.Source)) {
        $pathResult = Invoke-PythonProbe -Command ([string]$pathApplication.Source) -Label 'PATH Python'
        $pathAction = Select-CompatiblePythonCandidate -Stage path -ProbeResult $pathResult
        if ($pathAction -eq 'accept-path') {
            $diagnostics += [pscustomobject]@{ Level = 'INFO'; Message = "Selected PATH Python $($pathResult.Version): $($pathResult.Executable)" }
            return New-PythonSelectionResult $true $pathResult.Version $pathResult.Executable $diagnostics
        }
        $observedPathVersion = if ($null -ne $pathResult.Version) { " $($pathResult.Version)" } else { '' }
        $diagnostics += [pscustomobject]@{ Level = 'WARN'; Message = "Rejected PATH Python$observedPathVersion at '$($pathApplication.Source)': $($pathResult.Reason)." }
    }
    else {
        $diagnostics += [pscustomobject]@{ Level = 'WARN'; Message = 'PATH Python was not found; checking the Windows Python Launcher.' }
    }

    $launcherApplication = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $launcherApplication -and -not [string]::IsNullOrWhiteSpace([string]$launcherApplication.Source)) {
        $launcherResult = Invoke-PythonProbe -Command ([string]$launcherApplication.Source) -PrefixArguments @('-3') -Label 'Windows Python Launcher'
        $launcherAction = Select-CompatiblePythonCandidate -Stage launcher -ProbeResult $launcherResult
        if ($launcherAction -eq 'probe-resolved-launcher') {
            $resolvedResult = Invoke-PythonProbe -Command $launcherResult.Executable -Label 'launcher-selected Python'
            $resolvedAction = Select-CompatiblePythonCandidate -Stage resolved-launcher -ProbeResult $resolvedResult
            if ($resolvedAction -eq 'accept-launcher') {
                $diagnostics += [pscustomobject]@{ Level = 'INFO'; Message = "Selected Windows Launcher Python $($resolvedResult.Version): $($resolvedResult.Executable)" }
                return New-PythonSelectionResult $true $resolvedResult.Version $resolvedResult.Executable $diagnostics
            }
            $diagnostics += [pscustomobject]@{ Level = 'WARN'; Message = "Rejected launcher-selected Python at '$($launcherResult.Executable)': $($resolvedResult.Reason)." }
        }
        else {
            $observedLauncherVersion = if ($null -ne $launcherResult.Version) { " $($launcherResult.Version)" } else { '' }
            $diagnostics += [pscustomobject]@{ Level = 'WARN'; Message = "Rejected Windows Python Launcher candidate${observedLauncherVersion}: $($launcherResult.Reason)." }
        }
    }
    else {
        $diagnostics += [pscustomobject]@{ Level = 'WARN'; Message = 'Windows Python Launcher was not found.' }
    }

    $diagnostics += [pscustomobject]@{
        Level = 'ERROR'
        Message = 'No compatible Python runtime was found. Install Python 3.11 or newer, ensure it is registered with the Windows Python Launcher, or pass its executable path with -PythonCommand.'
    }
    return New-PythonSelectionResult $false $null $null $diagnostics
}
