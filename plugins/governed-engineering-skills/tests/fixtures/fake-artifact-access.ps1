function Ensure-GovernedArtifactAccess {
    param([string]$RepositoryRoot, [string]$ArtifactPath)
    if (-not [string]::IsNullOrWhiteSpace($env:FAKE_ARTIFACT_ACCESS_LOG)) {
        "$RepositoryRoot`t$ArtifactPath" | Out-File -FilePath $env:FAKE_ARTIFACT_ACCESS_LOG -Append -Encoding utf8
    }
    if ($env:FAKE_ARTIFACT_ACCESS_SCENARIO -eq 'blocked') {
        return [PSCustomObject]@{
            Valid = $false
            Repaired = $false
            Elevated = $false
            Diagnostic = 'Simulated bounded ACL recovery refusal.'
        }
    }
    return [PSCustomObject]@{
        Valid = $true
        Repaired = $true
        Elevated = ($env:FAKE_ARTIFACT_ACCESS_SCENARIO -eq 'elevated')
        Diagnostic = 'Simulated exact-target ACL recovery.'
    }
}
