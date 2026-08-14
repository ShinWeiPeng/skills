[CmdletBinding()]
param(
    [switch]$ElevatedRepair,
    [string]$ElevatedRepositoryRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ArtifactAccessScriptPath = $PSCommandPath

function New-ArtifactAccessResult {
    param(
        [bool]$Valid,
        [bool]$Repaired = $false,
        [bool]$Elevated = $false,
        [string]$Diagnostic = ''
    )
    return [PSCustomObject]@{
        Valid = $Valid
        Repaired = $Repaired
        Elevated = $Elevated
        Diagnostic = $Diagnostic
    }
}

function Test-GovernedArtifactPathSafety {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$ArtifactPath
    )
    try {
        $resolvedRepository = [System.IO.Path]::GetFullPath($RepositoryRoot).TrimEnd('\', '/')
        $resolvedDist = [System.IO.Path]::GetFullPath((Join-Path $resolvedRepository 'dist')).TrimEnd('\', '/')
        $resolvedArtifact = [System.IO.Path]::GetFullPath($ArtifactPath).TrimEnd('\', '/')
        $expectedArtifact = [System.IO.Path]::GetFullPath((Join-Path $resolvedDist 'governed-engineering-skills')).TrimEnd('\', '/')
        if (-not $resolvedArtifact.Equals($expectedArtifact, [System.StringComparison]::OrdinalIgnoreCase)) {
            return New-ArtifactAccessResult $false -Diagnostic "Refusing ACL recovery outside the exact governed artifact: $expectedArtifact"
        }
        if (-not $resolvedArtifact.StartsWith($resolvedDist + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            return New-ArtifactAccessResult $false -Diagnostic "Refusing ACL recovery outside the repository dist directory: $resolvedDist"
        }
        foreach ($boundary in @($resolvedRepository, $resolvedDist, $resolvedArtifact)) {
            if (Test-Path -LiteralPath $boundary) {
                $item = Get-Item -Force -LiteralPath $boundary
                if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                    return New-ArtifactAccessResult $false -Diagnostic "Refusing ACL recovery for a symbolic link, junction, or reparse point: $boundary"
                }
            }
        }
        return New-ArtifactAccessResult $true -Diagnostic $expectedArtifact
    }
    catch {
        return New-ArtifactAccessResult $false -Diagnostic ("Unable to validate the governed artifact boundary: " + $_.Exception.Message)
    }
}

function Test-GovernedArtifactReplaceAccess {
    param([Parameter(Mandatory = $true)][string]$ArtifactPath)
    if (-not (Test-Path -LiteralPath $ArtifactPath)) { return $true }
    $activeProbe = $null
    try {
        $root = Get-Item -Force -LiteralPath $ArtifactPath -ErrorAction Stop
        $entries = @($root) + @(Get-ChildItem -Force -Recurse -LiteralPath $ArtifactPath -ErrorAction Stop)
        foreach ($entry in $entries) {
            if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
            if (-not $entry.PSIsContainer) {
                $stream = [System.IO.File]::Open(
                    $entry.FullName,
                    [System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::Read,
                    ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
                )
                $stream.Dispose()
            }
        }
        foreach ($directory in @($entries | Where-Object { $_.PSIsContainer })) {
            $activeProbe = Join-Path $directory.FullName ('.codex-access-probe-' + [Guid]::NewGuid().ToString('N'))
            [void][System.IO.Directory]::CreateDirectory($activeProbe)
            [System.IO.File]::WriteAllText((Join-Path $activeProbe 'probe.tmp'), 'access-probe')
            [System.IO.Directory]::Delete($activeProbe, $true)
            $activeProbe = $null
        }
        foreach ($entry in $entries) {
            $parent = Split-Path -Parent $entry.FullName
            $entryDelete = Test-CurrentPrincipalFileSystemRight -Path $entry.FullName -Right ([System.Security.AccessControl.FileSystemRights]::Delete)
            $parentDeleteChild = Test-CurrentPrincipalFileSystemRight -Path $parent -Right ([System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles)
            if (-not $entryDelete -and -not $parentDeleteChild) { return $false }
        }
        return $true
    }
    catch {
        if ($activeProbe -and [System.IO.Directory]::Exists($activeProbe)) {
            try { [System.IO.Directory]::Delete($activeProbe, $true) } catch { }
        }
        return $false
    }
}

function Test-CurrentPrincipalFileSystemRight {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][System.Security.AccessControl.FileSystemRights]$Right
    )
    try {
        $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $principalSids = @($identity.User.Value) + @($identity.Groups | ForEach-Object { $_.Value })
        $security = Get-Acl -LiteralPath $Path -ErrorAction Stop
        $rules = $security.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
        $allowed = $false
        foreach ($rule in $rules) {
            if ($principalSids -notcontains $rule.IdentityReference.Value) { continue }
            if (([int]$rule.FileSystemRights -band [int]$Right) -ne [int]$Right) { continue }
            if ($rule.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Deny) { return $false }
            if ($rule.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Allow) { $allowed = $true }
        }
        return $allowed
    }
    catch {
        return $false
    }
}

function Invoke-OneInheritedAclReset {
    param([Parameter(Mandatory = $true)][string]$Path)
    & icacls.exe $Path '/inheritance:e' '/C' '/Q' '/L' *> $null
    if ($LASTEXITCODE -ne 0) { return $false }
    & icacls.exe $Path '/reset' '/C' '/Q' '/L' *> $null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-InheritedArtifactAclRepair {
    param([Parameter(Mandatory = $true)][string]$ArtifactPath)
    if (-not (Get-Command icacls.exe -CommandType Application -ErrorAction SilentlyContinue)) { return $false }
    if (-not (Test-Path -LiteralPath $ArtifactPath)) { return $true }
    try {
        if (-not (Invoke-OneInheritedAclReset -Path $ArtifactPath)) { return $false }
        $pending = [System.Collections.Generic.Queue[string]]::new()
        $pending.Enqueue($ArtifactPath)
        while ($pending.Count -gt 0) {
            $directory = $pending.Dequeue()
            foreach ($entry in @(Get-ChildItem -Force -LiteralPath $directory -ErrorAction Stop)) {
                if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
                if (-not (Invoke-OneInheritedAclReset -Path $entry.FullName)) { return $false }
                if ($entry.PSIsContainer) { $pending.Enqueue($entry.FullName) }
            }
        }
        return $true
    }
    catch {
        return $false
    }
}

function Invoke-ElevatedArtifactAclRepair {
    param([Parameter(Mandatory = $true)][string]$RepositoryRoot)
    $escapedScript = $script:ArtifactAccessScriptPath.Replace("'", "''")
    $escapedRoot = ([System.IO.Path]::GetFullPath($RepositoryRoot)).Replace("'", "''")
    $command = "& '$escapedScript' -ElevatedRepair -ElevatedRepositoryRoot '$escapedRoot'"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    try {
        $process = Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -Wait -PassThru `
            -ArgumentList @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $encoded)
        return ($process.ExitCode -eq 0)
    }
    catch {
        return $false
    }
}

function Ensure-GovernedArtifactAccess {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$ArtifactPath,
        [scriptblock]$AccessProbe,
        [scriptblock]$OrdinaryRepair,
        [scriptblock]$ElevationRepair
    )
    $safety = Test-GovernedArtifactPathSafety -RepositoryRoot $RepositoryRoot -ArtifactPath $ArtifactPath
    if (-not $safety.Valid) { return $safety }
    if (-not $AccessProbe) { $AccessProbe = { param($Path) Test-GovernedArtifactReplaceAccess -ArtifactPath $Path } }
    if (-not $OrdinaryRepair) { $OrdinaryRepair = { param($Path) Invoke-InheritedArtifactAclRepair -ArtifactPath $Path } }
    if (-not $ElevationRepair) { $ElevationRepair = { param($Root) Invoke-ElevatedArtifactAclRepair -RepositoryRoot $Root } }

    if (& $AccessProbe $ArtifactPath) {
        return New-ArtifactAccessResult $true -Diagnostic 'The governed artifact is already replaceable.'
    }
    if (& $OrdinaryRepair $ArtifactPath) {
        $postOrdinarySafety = Test-GovernedArtifactPathSafety -RepositoryRoot $RepositoryRoot -ArtifactPath $ArtifactPath
        if ($postOrdinarySafety.Valid -and (& $AccessProbe $ArtifactPath)) {
            return New-ArtifactAccessResult $true -Repaired $true -Diagnostic 'Inherited artifact access was restored without elevation.'
        }
    }
    if (-not (& $ElevationRepair $RepositoryRoot)) {
        return New-ArtifactAccessResult $false -Diagnostic 'Windows elevation was declined or the bounded ACL repair failed. Approve the UAC prompt and rerun the installer.'
    }
    $postElevationSafety = Test-GovernedArtifactPathSafety -RepositoryRoot $RepositoryRoot -ArtifactPath $ArtifactPath
    if (-not $postElevationSafety.Valid -or -not (& $AccessProbe $ArtifactPath)) {
        return New-ArtifactAccessResult $false -Elevated $true -Diagnostic 'The exact governed artifact remained inaccessible after elevated ACL repair.'
    }
    return New-ArtifactAccessResult $true -Repaired $true -Elevated $true -Diagnostic 'Inherited artifact access was restored through the approved UAC repair.'
}

if ($ElevatedRepair) {
    if ([string]::IsNullOrWhiteSpace($ElevatedRepositoryRoot)) { exit 40 }
    $target = Join-Path ([System.IO.Path]::GetFullPath($ElevatedRepositoryRoot)) 'dist\governed-engineering-skills'
    $decision = Test-GovernedArtifactPathSafety -RepositoryRoot $ElevatedRepositoryRoot -ArtifactPath $target
    if (-not $decision.Valid) { exit 41 }
    if (-not (Invoke-InheritedArtifactAclRepair -ArtifactPath $target)) { exit 42 }
    $decision = Test-GovernedArtifactPathSafety -RepositoryRoot $ElevatedRepositoryRoot -ArtifactPath $target
    if (-not $decision.Valid) { exit 43 }
    exit 0
}
