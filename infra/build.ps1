# build.ps1 — Bygg agent.exe med PyInstaller
# Kjøres fra repo-roten: .\infra\build.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$SpecFile = Join-Path $PSScriptRoot "agent.spec"
$BackendEnvDir = Join-Path $RepoRoot "backend\core"
$OutputDir = Join-Path $PSScriptRoot "dist"

Write-Host "[build] Starter bygging av AI-Revisor agent.exe" -ForegroundColor Cyan

# Verifiser at .env eksisterer
$EnvFile = Join-Path $BackendEnvDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Error "[build] Mangler .env i backend/core/. Kopier .env.mal og fyll inn verdier."
}

# Installer avhengigheter
Write-Host "[build] Installerer Python-avhengigheter..." -ForegroundColor Yellow
pip install -r (Join-Path $BackendEnvDir "requirements.txt") -q
pip install pyinstaller -q

# Kjør PyInstaller
Write-Host "[build] Kjører PyInstaller..." -ForegroundColor Yellow
Set-Location $PSScriptRoot
pyinstaller $SpecFile --distpath $OutputDir --workpath (Join-Path $PSScriptRoot "build") --noconfirm

$ExePath = Join-Path $OutputDir "AI-Revisor.exe"
if (Test-Path $ExePath) {
    $Size = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host "[build] Ferdig: $ExePath ($Size MB)" -ForegroundColor Green
} else {
    Write-Error "[build] Bygging mislyktes — AI-Revisor.exe ikke funnet."
}
