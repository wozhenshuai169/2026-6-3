$ErrorActionPreference = "Stop"
$python = "C:\Users\44585\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$renderer = "C:\Users\44585\.codex\plugins\cache\openai-primary-runtime\documents\26.715.12143\skills\documents\render_docx.py"
$loProgram = "D:\codex-lo-runtime\program"
$tempRoot = "D:\codex-docx-temp"
$qaRoot = "D:\codex-docx-qa"
$inputRoot = "D:\codex-docx-input"

$env:PATH = $loProgram + ";" + $env:PATH
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null
New-Item -ItemType Directory -Path $inputRoot -Force | Out-Null

$documents = @(Get-ChildItem -LiteralPath "deliverables" -Recurse -File -Filter "*.docx" | Sort-Object FullName)
if ($documents.Count -ne 3) {
    throw "Expected exactly three submission DOCX files, found $($documents.Count)."
}

$index = 0
foreach ($document in $documents) {
    $index += 1
    $outputDir = Join-Path $qaRoot ("doc" + $index)
    $inputCopy = Join-Path $inputRoot ("doc" + $index + ".docx")
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Copy-Item -LiteralPath $document.FullName -Destination $inputCopy -Force
    Write-Output ("START " + $index + " " + $document.FullName)
    & $python $renderer $inputCopy --output_dir $outputDir --emit_pdf --verbose
    if ($LASTEXITCODE -ne 0) {
        throw "Rendering failed for document $index with exit code $LASTEXITCODE."
    }
    Write-Output ("DONE " + $index + " " + $outputDir)
}
