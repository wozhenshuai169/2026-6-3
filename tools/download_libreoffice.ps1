$ErrorActionPreference = "Stop"
$url = "https://mirrors.tuna.tsinghua.edu.cn/libreoffice/libreoffice/stable/26.2.4/win/x86_64/LibreOffice_26.2.4_Win_x86-64.msi"
$packageDir = (Resolve-Path "tools\runtime\libreoffice-package").Path
$outputPath = Join-Path $packageDir "LibreOffice.msi"
$arguments = @("-L", "--ssl-no-revoke", "--fail", "--retry", "3", "--output", $outputPath, $url)
$process = Start-Process -FilePath "curl.exe" -ArgumentList $arguments -PassThru -WindowStyle Hidden -RedirectStandardOutput "tools\runtime\libreoffice-curl.out" -RedirectStandardError "tools\runtime\libreoffice-curl.err"
Write-Output $process.Id
