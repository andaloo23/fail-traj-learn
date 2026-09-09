# Append GPU temperature/power/utilization, CPU load and free RAM to a CSV every N seconds, so an unexpected
# shutdown leaves a trace of the last known thermal/power state. Detach it with:
#   Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File <this file>'
# Log: outputs/sensors.csv next to the project (not tracked by git). Stop it by killing the powershell process.
param([int]$IntervalSec = 30, [string]$Out = "$PSScriptRoot\..\..\outputs\sensors.csv")
$Out = [System.IO.Path]::GetFullPath($Out)
if (-not (Test-Path $Out)) { "time,gpu_temp_c,gpu_power_w,gpu_util_pct,gpu_mem_mib,cpu_pct,ram_avail_mb" | Out-File -Encoding ascii $Out }
while ($true) {
  try {
    $g = (nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu,memory.used --format=csv,noheader,nounits) -replace ' ', ''
    $cpu = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue, 1)
    $ram = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$g,$cpu,$ram" | Out-File -Encoding ascii -Append $Out
  } catch { }
  Start-Sleep -Seconds $IntervalSec
}
