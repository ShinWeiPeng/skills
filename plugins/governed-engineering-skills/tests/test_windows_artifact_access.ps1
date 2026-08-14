Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pluginShell = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $pluginShell '..\..'))
$helper = Join-Path $repoRoot 'scripts\windows-artifact-access.ps1'
$orchestrator = Join-Path $repoRoot 'scripts\install-local.ps1'

function Assert-Equal {
    param($Expected, $Actual, [string]$Context)
    if ($Expected -ne $Actual) { throw "$Context expected '$Expected', got '$Actual'." }
}

if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
    throw "Windows artifact access helper is missing: $helper"
}

. $helper

$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('governed-acl-' + [Guid]::NewGuid().ToString('N'))
$fixtureRepo = Join-Path $testRoot 'repo'
$distRoot = Join-Path $fixtureRepo 'dist'
$artifact = Join-Path $distRoot 'governed-engineering-skills'
$sibling = Join-Path $distRoot 'other-plugin'
$outside = Join-Path $testRoot 'outside'

try {
    New-Item -ItemType Directory -Path $artifact, $sibling, $outside -Force | Out-Null

    foreach ($unsafe in @($fixtureRepo, $distRoot, $sibling, $outside)) {
        $decision = Test-GovernedArtifactPathSafety -RepositoryRoot $fixtureRepo -ArtifactPath $unsafe
        Assert-Equal $false $decision.Valid "unsafe target $unsafe"
    }
    $safe = Test-GovernedArtifactPathSafety -RepositoryRoot $fixtureRepo -ArtifactPath $artifact
    Assert-Equal $true $safe.Valid 'exact governed artifact'

    Remove-Item -Recurse -Force -LiteralPath $artifact
    New-Item -ItemType Junction -Path $artifact -Target $outside | Out-Null
    $redirected = Test-GovernedArtifactPathSafety -RepositoryRoot $fixtureRepo -ArtifactPath $artifact
    Assert-Equal $false $redirected.Valid 'reparse target'
    Remove-Item -Force -LiteralPath $artifact
    New-Item -ItemType Directory -Path $artifact | Out-Null

    $nestedRedirect = Join-Path $artifact 'nested-link'
    New-Item -ItemType Junction -Path $nestedRedirect -Target $outside | Out-Null
    Assert-Equal $false (Test-GovernedArtifactReplaceAccess -ArtifactPath $artifact) 'nested reparse target'
    $outsideAclBefore = (Get-Acl -LiteralPath $outside).Sddl
    Assert-Equal $false (Invoke-InheritedArtifactAclRepair -ArtifactPath $artifact) 'repair must refuse nested reparse target'
    Assert-Equal $outsideAclBefore (Get-Acl -LiteralPath $outside).Sddl 'repair must not change junction destination ACL'
    Remove-Item -Force -LiteralPath $nestedRedirect

    $restricted = Join-Path $testRoot 'restricted-existing-tree'
    $restrictedFile = Join-Path $restricted 'existing.txt'
    New-Item -ItemType Directory -Path $restricted | Out-Null
    Set-Content -LiteralPath $restrictedFile -Value 'existing' -Encoding ascii
    $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    try {
        & icacls.exe $restricted '/inheritance:r' '/grant:r' "*$($currentSid):(OI)(CI)(RX,W)" *> $null
        Assert-Equal 0 $LASTEXITCODE 'restrict existing tree ACL'
        & icacls.exe $restrictedFile '/inheritance:r' '/grant:r' "*$($currentSid):(R,W)" *> $null
        Assert-Equal 0 $LASTEXITCODE 'restrict existing file ACL'
        Assert-Equal $false (Test-GovernedArtifactReplaceAccess -ArtifactPath $restricted) 'existing child without delete access'
    }
    finally {
        & icacls.exe $restricted '/reset' '/T' '/C' '/Q' *> $null
    }

    $calls = [System.Collections.Generic.List[string]]::new()
    $probeCount = 0
    $recovered = Ensure-GovernedArtifactAccess -RepositoryRoot $fixtureRepo -ArtifactPath $artifact `
        -AccessProbe {
            param($Path)
            $script:probeCount++
            $script:calls.Add("probe:$Path")
            return ($script:probeCount -ge 2)
        } `
        -OrdinaryRepair {
            param($Path)
            $script:calls.Add("ordinary:$Path")
            return $true
        } `
        -ElevationRepair {
            param($Root)
            $script:calls.Add("elevated:$Root")
            return $true
        }
    Assert-Equal $true $recovered.Valid 'ordinary inherited-access recovery'
    Assert-Equal $false $recovered.Elevated 'ordinary recovery must not elevate'
    Assert-Equal "probe:$artifact`nordinary:$artifact`nprobe:$artifact" ($calls -join "`n") 'ordinary recovery order'

    $calls.Clear()
    $probeCount = 0
    $elevated = Ensure-GovernedArtifactAccess -RepositoryRoot $fixtureRepo -ArtifactPath $artifact `
        -AccessProbe {
            param($Path)
            $script:probeCount++
            $script:calls.Add("probe:$Path")
            return ($script:probeCount -ge 2)
        } `
        -OrdinaryRepair {
            param($Path)
            $script:calls.Add("ordinary:$Path")
            return $false
        } `
        -ElevationRepair {
            param($Root)
            $script:calls.Add("elevated:$Root")
            return $true
        }
    Assert-Equal $true $elevated.Valid 'bounded elevated recovery'
    Assert-Equal $true $elevated.Elevated 'elevation marker'
    Assert-Equal "probe:$artifact`nordinary:$artifact`nelevated:$fixtureRepo`nprobe:$artifact" ($calls -join "`n") 'elevated recovery order'

    $denied = Ensure-GovernedArtifactAccess -RepositoryRoot $fixtureRepo -ArtifactPath $artifact `
        -AccessProbe { return $false } -OrdinaryRepair { return $false } -ElevationRepair { return $false }
    Assert-Equal $false $denied.Valid 'denied elevation must block'

    $orchestratorText = Get-Content -Raw -LiteralPath $orchestrator
    if ($orchestratorText -notmatch 'Ensure-GovernedArtifactAccess' -or
        $orchestratorText.IndexOf('Ensure-GovernedArtifactAccess') -gt $orchestratorText.IndexOf("Invoke-AssemblyStep `$selectedPython")) {
        throw 'The public installer must enforce artifact access before assembly.'
    }

    Write-Host 'PASS: bounded Windows artifact access contracts'
}
finally {
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -Recurse -Force -LiteralPath $testRoot }
}
