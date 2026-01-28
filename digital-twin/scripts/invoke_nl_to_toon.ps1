# Call NL-to-TOON and show full response (including raw_toon when present)
$body = '{"text": "3 stations in Bangalore, 2 in Mumbai, high demand", "city": "Bangalore"}'
try {
  $response = Invoke-WebRequest -Uri "http://localhost:8000/api/nl-to-toon" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
  $json = $response.Content | ConvertFrom-Json
  Write-Host "=== Full response (JSON) ==="
  $response.Content
  Write-Host "`n=== Parsed .toon ==="
  $json.toon | ConvertTo-Json -Depth 5
  if ($json.raw_toon) {
    Write-Host "`n=== raw_toon (what Gemini returned) ==="
    Write-Host $json.raw_toon
  }
} catch {
  Write-Host "Error: $_"
  if ($_.Exception.Response) {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    Write-Host $reader.ReadToEnd()
  }
}
