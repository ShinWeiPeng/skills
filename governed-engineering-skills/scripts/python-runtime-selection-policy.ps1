Set-StrictMode -Version Latest

function Select-CompatiblePythonCandidate {
    param(
        [ValidateSet('explicit', 'path', 'launcher', 'resolved-launcher')][string]$Stage,
        [AllowNull()][object]$ProbeResult
    )
    $valid = ($null -ne $ProbeResult -and [bool]$ProbeResult.Valid)
    switch ($Stage) {
        'explicit' { return $(if ($valid) { 'accept-explicit' } else { 'reject-explicit' }) }
        'path' { return $(if ($valid) { 'accept-path' } else { 'probe-launcher' }) }
        'launcher' { return $(if ($valid) { 'probe-resolved-launcher' } else { 'reject-all' }) }
        'resolved-launcher' { return $(if ($valid) { 'accept-launcher' } else { 'reject-all' }) }
    }
}
