<#
.SYNOPSIS
    Creates a Python environment in WSL and registers the Jupyter Bash kernel inside it.

.DESCRIPTION
    bash_kernel relies on pexpect.spawn and does not run natively on Windows. This script
    therefore runs setup-bash-kernel.sh inside the WSL distribution, in the current
    directory. Afterwards connect VS Code with "WSL: Reopen Folder in WSL" so the kernel
    shows up in the kernel picker.

.PARAMETER Venv
    Environment path relative to the current directory. Default: .venv

.PARAMETER Python
    Python command inside WSL. Default: python3

.PARAMETER Distribution
    WSL distribution. Default: the default distribution.

.EXAMPLE
    .\setup-bash-kernel.ps1 -Venv .venv
#>
#Requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Venv = '.venv',
    [string]$Python = 'python3',
    [string]$Distribution
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'wsl.exe not found. Install WSL: wsl --install -d Ubuntu'
}

$wslArgs = @()
if ($Distribution) { $wslArgs += @('-d', $Distribution) }

function ConvertTo-WslPath([string]$WindowsPath) {
    $converted = & wsl.exe @wslArgs -- wslpath -a "$WindowsPath"
    if ($LASTEXITCODE -ne 0 -or -not $converted) {
        throw "wslpath could not convert $WindowsPath."
    }
    return ([string]$converted).Trim()
}

$location = (Get-Location).ProviderPath
if ($location -notlike '\\wsl*') {
    Write-Warning 'The environment will live under /mnt/... For better performance keep the project in the WSL file system.'
}

$locationWsl = ConvertTo-WslPath $location
$scriptWsl = ConvertTo-WslPath (Join-Path $PSScriptRoot 'setup-bash-kernel.sh')

& wsl.exe @wslArgs --cd "$locationWsl" -- bash "$scriptWsl" --venv "$Venv" --python "$Python"
if ($LASTEXITCODE -ne 0) {
    throw "setup-bash-kernel.sh failed with exit code $LASTEXITCODE."
}
