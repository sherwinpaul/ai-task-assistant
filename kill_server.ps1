Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn src.app*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
