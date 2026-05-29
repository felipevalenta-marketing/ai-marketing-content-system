try {
  $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
  Write-Host ("Health: {0}" -f ($response.data.status ?? "unknown"))
} catch {
  Write-Host ("Health check failed: {0}" -f $_.Exception.Message)
  exit 1
}
