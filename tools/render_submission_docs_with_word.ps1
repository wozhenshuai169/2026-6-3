$ErrorActionPreference = "Stop"

$deliverablesRoot = (Resolve-Path -LiteralPath "deliverables").Path
$documents = @(Get-ChildItem -LiteralPath $deliverablesRoot -Recurse -File -Filter "*.docx" | Sort-Object FullName)
if ($documents.Count -ne 3) {
    throw "Expected exactly three submission DOCX files, found $($documents.Count)."
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $index = 0
    foreach ($item in $documents) {
        $index += 1
        $docRoot = $item.DirectoryName
        $docPath = $item.FullName
        $qaDir = Join-Path (Join-Path $docRoot "qa") ("doc" + $index)
        New-Item -ItemType Directory -Path $qaDir -Force | Out-Null
        $pdfPath = Join-Path $qaDir ([System.IO.Path]::GetFileNameWithoutExtension($item.Name) + ".pdf")

        $doc = $word.Documents.Open($docPath, $false, $false)
        try {
            $doc.Repaginate()
            foreach ($toc in $doc.TablesOfContents) {
                $toc.Update()
            }
            $doc.Fields.Update() | Out-Null
            $doc.Repaginate()
            $doc.Save()
            $doc.ExportAsFixedFormat($pdfPath, 17)
            Write-Output "$($item.Name) -> $pdfPath"
        }
        finally {
            $doc.Close($false)
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
        }
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
