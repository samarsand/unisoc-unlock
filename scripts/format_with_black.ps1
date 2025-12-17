<#
Run this from the repository root in PowerShell to format the repo with Black and commit changes.
Usage: .\scripts\format_with_black.ps1
#>
param(
    [switch]$ForceVenv
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
Set-Location ..\

Write-Host "Repo root: $( Get-Location )"

# Determine Python command first (before trying to create venv)
$pythonCmd = $null
$venvPython = Join-Path -Path ".venv" -ChildPath "Scripts\python.exe"

if (Test-Path $venvPython)
{
    $pythonCmd = $venvPython
}
else
{
    # Find available Python command
    if (Get-Command py -ErrorAction SilentlyContinue)
    {
        $pythonCmd = "py"
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue)
    {
        $pythonCmd = "python"
    }
    elseif (Get-Command python3 -ErrorAction SilentlyContinue)
    {
        $pythonCmd = "python3"
    }
}

if (-not $pythonCmd)
{
    Write-Error "Python is not installed or not in PATH. Please install Python or add it to your PATH."
    exit 1
}

if (-not (Test-Path ".venv") -or $ForceVenv)
{
    Write-Host "Creating virtual environment in .venv..."
    & $pythonCmd -m venv .venv
    $venvPython = Join-Path -Path ".venv" -ChildPath "Scripts\python.exe"
    $pythonCmd = $venvPython
}

Write-Host "Using Python command: $pythonCmd"

# Upgrade pip and install dev dependencies
& $pythonCmd -m pip install --upgrade pip
& $pythonCmd -m pip install -r dev-requirements.txt

# Run black to format
Write-Host "Running Black to format the repository..."
& $pythonCmd -m black .

# Commit only if changes are present
$changes = git status --porcelain
if ($changes)
{
    git add -A
    git commit -m "style: format code with Black"
    Write-Host "Committed formatting changes."
}
else
{
    Write-Host "No formatting changes to commit."
}

