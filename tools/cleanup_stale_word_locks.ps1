$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath "deliverables").Path
$locks = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter "*.docx" | Where-Object {
    $_.Name.StartsWith("~") -and $_.Length -lt 1024
})
foreach ($lock in $locks) {
    if (-not $lock.FullName.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete a file outside the deliverables root."
    }
    $lock.Delete()
    Write-Output ("Removed stale Word lock: " + $lock.FullName)
}
