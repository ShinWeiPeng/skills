# Process-local launcher; no plugin, profile edit, or administrator rights are needed.
$ErrorActionPreference = 'Stop'
$forwarded = @($args)
$candidates = @(
    @{ Name = 'py.exe'; Prefix = @('-3') },
    @{ Name = 'python3'; Prefix = @() },
    @{ Name = 'python'; Prefix = @() }
)
$selected = $null
$prefix = @()
foreach ($candidate in $candidates) {
    $runtime = Get-Command $candidate.Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $runtime) { continue }
    if ($runtime.Source -like '*\WindowsApps\python*.exe') { continue }
    $probePrefix = $candidate.Prefix
    try {
        & $runtime.Source @probePrefix -c "import sys; sys.exit(sys.version_info < (3, 9))" 2>$null
    }
    catch { continue }
    if ($LASTEXITCODE -eq 0) {
        $selected = $runtime.Source
        $prefix = $probePrefix
        break
    }
}
if ($null -eq $selected) {
    Write-Host 'Python 3.9 or newer is required. Install Python 3 from https://www.python.org/downloads/ and run this installer again.'
    exit 1
}
$installer = Join-Path $PSScriptRoot 'install.py'
$temporary = $null
try {
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
        $temporary = [System.IO.Path]::GetTempFileName()
        Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/ShinWeiPeng/skills/main/doc-coauthoring/scripts/install.py' -OutFile $temporary
        $installer = $temporary
    }
    & $selected @prefix $installer @forwarded
    $result = $LASTEXITCODE
}
catch {
    Write-Host ('Installation stopped: ' + $_.Exception.Message)
    $result = 1
}
finally {
    if ($null -ne $temporary -and (Test-Path -LiteralPath $temporary)) {
        Remove-Item -LiteralPath $temporary -Force
    }
}
exit $result
