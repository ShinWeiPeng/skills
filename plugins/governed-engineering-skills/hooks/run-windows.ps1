# Host adapter only: use an explicit runtime or this project's provisioned venv.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
# Windows PowerShell -Command pipelines consult the process-global encoding.
$global:OutputEncoding = $utf8
$payload = $null
try {
    $raw = [Console]::In.ReadToEnd()
    $payload = $raw | ConvertFrom-Json
    $runtime = $env:GOVERNED_ENGINEERING_PYTHON
    if ([string]::IsNullOrWhiteSpace($runtime)) {
        $runtime = Join-Path ([string]$payload.cwd) '.codex-arch-deps\venv\Scripts\python.exe'
    }
    if (-not (Test-Path -LiteralPath $runtime -PathType Leaf)) {
        throw 'Set GOVERNED_ENGINEERING_PYTHON to an existing Python 3.11+ executable, or provision the project venv. PATH python is not trusted to be compatible.'
    }
    & $runtime -X utf8 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'The configured hook runtime must be Python 3.11 or newer.' }
    $script = Join-Path $env:PLUGIN_ROOT 'skills\implement\scripts\discussion_hook.py'
    $response = @($raw | & $runtime -X utf8 $script)
    if ($LASTEXITCODE -ne 0) { throw "Hook process exited with code $LASTEXITCODE." }
    $parsed = ($response -join "`n") | ConvertFrom-Json
    $parsed | ConvertTo-Json -Depth 30 -Compress
} catch {
    $reason = 'Discussion hook runtime unavailable: ' + $_.Exception.Message
    $readOnly = $false
    if ($null -ne $payload -and $payload.PSObject.Properties['tool_name']) {
        $readOnly = [string]$payload.tool_name -in @('Read', 'Glob', 'Grep', 'read_file', 'list_directory')
        if ([string]$payload.tool_name -in @('Bash', 'exec_command') -and $payload.PSObject.Properties['tool_input']) {
            $toolInput = $payload.tool_input
            $command = ''
            if ($null -ne $toolInput -and $toolInput.PSObject.Properties['cmd']) { $command = [string]$toolInput.cmd }
            elseif ($null -ne $toolInput -and $toolInput.PSObject.Properties['command']) { $command = [string]$toolInput.command }
            $readOnly = $command -match '^(Get-Content|Get-ChildItem|Get-Location)( |$)' -and $command -notmatch '[;|&><`$\r\n{}()]'
        }
    }
    if ($null -ne $payload -and $payload.PSObject.Properties['hook_event_name'] -and $payload.hook_event_name -eq 'PreToolUse' -and -not $readOnly) {
        @{hookSpecificOutput=@{hookEventName='PreToolUse';permissionDecision='deny';permissionDecisionReason=$reason}} | ConvertTo-Json -Depth 5 -Compress
    } else {
        @{systemMessage=$reason + " Discussion remains available; SPEC synchronization is not verified."} | ConvertTo-Json -Compress
    }
}
