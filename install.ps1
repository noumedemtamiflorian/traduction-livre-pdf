# PowerShell Installer for `traduction-livre-pdf` Skill (Windows)
# Installs the skill globally across major AI coding agents and installs Python dependencies.

$ErrorActionPreference = "Stop"
$SkillName = "traduction-livre-pdf"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Installation du Skill '$SkillName' ===" -ForegroundColor Cyan

# 1. Install Python dependencies
Write-Host "[1/2] Verification des dependances Python (pypdf, reportlab, Pillow)..." -ForegroundColor Yellow
python -m pip install -r (Join-Path $SourceDir "requirements.txt") --quiet

# 2. Copy skill to global agent directories
$TargetDirs = @(
    (Join-Path $HOME ".gemini\config\skills\$SkillName"),   # Antigravity (AGY)
    (Join-Path $HOME ".agents\skills\$SkillName"),          # Universal .agents standard / Codex
    (Join-Path $HOME ".claude\skills\$SkillName")           # Claude Code
)

Write-Host "[2/2] Copie des fichiers du skill dans les repertoires globaux..." -ForegroundColor Yellow
foreach ($Dest in $TargetDirs) {
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    Copy-Item -Path (Join-Path $SourceDir "SKILL.md") -Destination $Dest -Force
    Copy-Item -Path (Join-Path $SourceDir "requirements.txt") -Destination $Dest -Force
    Copy-Item -Path (Join-Path $SourceDir "scripts") -Destination $Dest -Recurse -Force
    Copy-Item -Path (Join-Path $SourceDir "references") -Destination $Dest -Recurse -Force
    Write-Host "  -> Installe dans : $Dest" -ForegroundColor Green
}

Write-Host "`nInstallation terminee avec succes ! Votre skill '$SkillName' est pret a etre utilise." -ForegroundColor Cyan
