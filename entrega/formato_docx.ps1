# Da formato con Word a un complementario generado con pandoc: Arial, títulos sin numeración heredada,
# tablas con bordes, encabezado repetido y ajuste al contenido; página horizontal si se pide. Exporta también el PDF.
# Uso: powershell -File entrega/formato_docx.ps1 -Doc <ruta .docx con barras invertidas> [-Horizontal 1]
param([string]$Doc, [int]$Horizontal = 0)
$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
$d = $null
for ($k = 0; $k -lt 5 -and $d -eq $null; $k++) { try { $d = $w.Documents.Open($Doc, $false, $false) } catch { Start-Sleep -Seconds 2 } }
if ($d -eq $null) { "ERROR: no se pudo abrir $Doc"; $w.Quit(); exit 1 }
try {
  foreach ($s in $d.Styles) { try { if (@('Times New Roman', 'Cambria', 'Calibri', 'Calibri Light') -contains $s.Font.Name) { $s.Font.Name = 'Arial' } } catch {} }
  foreach ($p in $d.Paragraphs) { if ($p.OutlineLevel -lt 10 -and $p.Range.ListFormat.ListType -ne 0) { $p.Range.ListFormat.RemoveNumbers() } }
  if ($Horizontal -eq 1) { foreach ($sec in $d.Sections) { $sec.PageSetup.Orientation = 1 } }
  foreach ($t in $d.Tables) {
    $t.Range.Font.Name = 'Arial'; $t.Range.Font.Size = 9
    $t.Range.ParagraphFormat.SpaceAfter = 2; $t.Range.ParagraphFormat.SpaceBefore = 2; $t.Range.ParagraphFormat.LineSpacingRule = 0
    $t.Borders.Enable = 1; $t.Borders.InsideColor = 12632256; $t.Borders.OutsideColor = 8421504
    $t.Rows.Item(1).Range.Font.Bold = 1
    $t.Rows.Item(1).Shading.BackgroundPatternColor = 15333864
    $t.Rows.Item(1).HeadingFormat = -1
    $t.AutoFitBehavior(1); $t.AutoFitBehavior(2)
  }
  $d.Save()
  $d.ExportAsFixedFormat([System.IO.Path]::ChangeExtension($Doc, ".pdf"), 17)
  "ok $Doc tablas=" + $d.Tables.Count
} finally { $d.Close(0); $w.Quit() }
