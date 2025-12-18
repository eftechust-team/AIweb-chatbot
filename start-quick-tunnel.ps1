param(
    [int]$Port = 8080,
    [switch]$SkipTunnel
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\x1\OneDrive\Desktop\elevatefoods\From Siyu\Food_AI-master"
Set-Location $root

$python = Join-Path $root ".venv\\Scripts\\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python venv not found at $python. Activate or create the venv first."
    exit 1
}

Write-Host "Starting Flask on port $Port ..."
Start-Process -FilePath $python -ArgumentList "main.py" -WorkingDirectory $root
Start-Sleep -Seconds 2

if ($SkipTunnel) {
    Write-Host "SkipTunnel flag set; not starting cloudflared."
    exit 0
}

$cloudflared = Join-Path $env:USERPROFILE "cloudflared.exe"
if (-not (Test-Path $cloudflared)) {
    Write-Error "cloudflared.exe not found at $cloudflared. Download it first."
    exit 1
}

Write-Host "Starting cloudflared quick tunnel to http://localhost:$Port ..."
Write-Host "Watch the cloudflared window for the public URL (trycloudflare.com)."
Start-Process -FilePath $cloudflared -ArgumentList "tunnel --url http://localhost:$Port" -WorkingDirectory $root
