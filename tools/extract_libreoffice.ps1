$ErrorActionPreference = "Stop"
$packagePath = (Resolve-Path "tools\runtime\libreoffice-package\LibreOffice.msi").Path
$targetDir = "D:\codex-lo-runtime"
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
$arguments = @("/a", $packagePath, "TARGETDIR=$targetDir", "/qn", "/norestart", "/l*v", "tools\runtime\libreoffice-extract.log")
$process = Start-Process -FilePath "msiexec.exe" -ArgumentList $arguments -PassThru -WindowStyle Hidden
Write-Output $process.Id
