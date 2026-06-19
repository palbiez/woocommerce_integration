param(
    [string]$PythonVersion = "3.13"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $RepoRoot ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    py -$PythonVersion -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Write-Host "Python venv bereit: $PythonExe"
Write-Host "Aktivieren: .\.venv\Scripts\Activate.ps1"
