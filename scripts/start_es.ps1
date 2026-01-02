param(
    [int]$TimeoutSeconds = 180
)

# Move to repository root (assumes script is located in repo/scripts)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

Write-Host "Starting Elasticsearch via Docker Compose..." -ForegroundColor Green
docker compose up -d

$endTime = (Get-Date).AddSeconds($TimeoutSeconds)
$health = $null

while ((Get-Date) -lt $endTime) {
    try {
        $health = Invoke-RestMethod -Uri http://localhost:9200/_cluster/health -UseBasicParsing -ErrorAction Stop
        Write-Host "Elasticsearch cluster status: $($health.status)" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 3
    }
}

if (-not $health) {
    Write-Host "Elasticsearch did not become healthy within $TimeoutSeconds seconds." -ForegroundColor Red
    exit 1
}

Write-Host "Elasticsearch is ready!" -ForegroundColor Green
Write-Host "Next steps (examples):" -ForegroundColor Cyan
Write-Host "  1) Create index mapping:"
Write-Host "     curl -X PUT \"http://localhost:9200/pharmacy\" -H \"Content-Type: application/json\" -d @es/pharmacy_mapping.json"
Write-Host "     (PowerShell alternative:)"
Write-Host "     Invoke-RestMethod -Method Put -Uri http://localhost:9200/pharmacy -InFile es/pharmacy_mapping.json -ContentType 'application/json'"
Write-Host "  2) Generate embeddings & bulk file:"
Write-Host "     python scripts/embed_and_export.py --input src/main/resources/pharmacy_sample.jsonl --output src/main/resources/pharmacy_index.jsonl --es-bulk --index-name pharmacy"
Write-Host "  3) Bulk index (recommended using curl/Git Bash):"
Write-Host "     curl -s -H \"Content-Type: application/json\" -XPOST \"http://localhost:9200/_bulk\" --data-binary @src/main/resources/pharmacy_index.bulk.json"
Write-Host "  4) Test queries via Java app or via ES directly"
Write-Host "If you need to stop and remove resources: docker compose down -v"
