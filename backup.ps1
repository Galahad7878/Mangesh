param(
    [string]$DestinationDir = "$HOME\Desktop\Backups_NaviAgent"
)

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$ZipFileName = "backup_LOIs_${Timestamp}.zip"

if (-not (Test-Path $DestinationDir)) {
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
}

$ZipFilePath = Join-Path $DestinationDir $ZipFileName

# Exclusiones estrictas
$ExcludeDirs = @('.venv', 'venv', 'env', '.env', 'node_modules', '__pycache__', '.git', '.pytest_cache', '.idea', '.vscode', '.system_generated')
$ExcludeExts = @('.pyc', '.pyo', '.pyd', '.log', '.tmp')

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   NAVIAGENT - COPIA DE SEGURIDAD AUTOMATICA (POWERSHELL)" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "[*] Origen:   $ProjectDir"
Write-Host "[*] Destino:  $ZipFilePath"
Write-Host "[*] Ignorado: $($ExcludeDirs -join ', ')"
Write-Host "---------------------------------------------------------"

$AllFiles = Get-ChildItem -Path $ProjectDir -Recurse -File | Where-Object {
    $filePath = $_.FullName
    $relPath = $filePath.Substring($ProjectDir.Length).TrimStart('\', '/')
    $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    
    foreach ($part in $parts) {
        if ($ExcludeDirs -contains $part) { return $false }
    }
    if ($ExcludeExts -contains $_.Extension.ToLower()) { return $false }
    if ($_.Name.StartsWith("backup_") -and $_.Extension.ToLower() -eq ".zip") { return $false }

    return $true
}

$TempStaging = Join-Path ([System.IO.Path]::GetTempPath()) "backup_staging_${Timestamp}"
if (Test-Path $TempStaging) { Remove-Item -Recurse -Force $TempStaging }
New-Item -ItemType Directory -Path $TempStaging -Force | Out-Null

try {
    foreach ($file in $AllFiles) {
        $relPath = $file.FullName.Substring($ProjectDir.Length).TrimStart('\', '/')
        $targetPath = Join-Path $TempStaging $relPath
        $targetDir = [System.IO.Path]::GetDirectoryName($targetPath)
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        Write-Host "  + $relPath" -ForegroundColor DarkGray
    }

    if (Test-Path $ZipFilePath) { Remove-Item -Force $ZipFilePath }
    
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($TempStaging, $ZipFilePath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

    $ZipSizeKB = [math]::Round((Get-Item $ZipFilePath).Length / 1KB, 1)
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host "OK: Copia de seguridad completada con exito!" -ForegroundColor Green
    Write-Host "Total archivos: $($AllFiles.Count)"
    Write-Host "Tamano ZIP:     $ZipSizeKB KB"
    Write-Host "Ubicacion:      $ZipFilePath" -ForegroundColor Yellow
    Write-Host "=========================================================" -ForegroundColor Cyan
}
finally {
    if (Test-Path $TempStaging) {
        Remove-Item -Recurse -Force $TempStaging -ErrorAction SilentlyContinue
    }
}
