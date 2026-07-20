$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$document = $word.Documents.Add()
try {
    $document.Content.Text = "render test"
    $pdfPath = Join-Path (Resolve-Path ".").Path "word-render-test.pdf"
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output $pdfPath
}
finally {
    $document.Close($false)
    $word.Quit()
}
