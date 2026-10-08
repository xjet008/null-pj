param(
  [string]$Python,
  [string]$Dependencies,
  [int]$Port=4177,
  [int]$Device=0,
  [ValidateSet('auto','cuda','cpu')][string]$Backend='cuda',
  [switch]$NoBrowser
)
$ErrorActionPreference='Stop'
$nativeRoot=$PSScriptRoot
if (-not $Python) {
  $bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if(Test-Path -LiteralPath $bundled){$Python=$bundled}
  elseif(Get-Command python -ErrorAction SilentlyContinue){$Python=(Get-Command python).Source}
  else{throw 'Install Python 3.12+ x64, then pass -Python C:\path\python.exe'}
}
if(-not $Dependencies){$Dependencies=Join-Path $nativeRoot '.runtime\deps'}
$env:PYTHONPATH=$Dependencies
& $Python -c "import numpy,PIL,cryptography; import nvidia.cuda_nvrtc"
if($LASTEXITCODE -ne 0){
  & $Python -m pip install --target $Dependencies -r (Join-Path $nativeRoot 'requirements.txt')
  if($LASTEXITCODE -ne 0){throw 'Dependency setup failed'}
}
$serverPath=Join-Path $nativeRoot 'local_server.py'
if($NoBrowser){& $Python $serverPath --port $Port --device $Device --backend $Backend;exit $LASTEXITCODE}
$arguments=@(('"' + $serverPath + '"'),'--port',"$Port",'--device',"$Device",'--backend',$Backend)
$process=Start-Process -FilePath $Python -ArgumentList $arguments -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $nativeRoot 'server.log') -RedirectStandardError (Join-Path $nativeRoot 'server-error.log')
try{
  $ready=$false
  for($attempt=0;$attempt -lt 120;$attempt++){
    if($process.HasExited){throw 'Local CUDA server exited. Read native/server-error.log'}
    try{$status=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v3/status" -TimeoutSec 2;$ready=$true;break}
    catch{Start-Sleep -Milliseconds 500}
  }
  if(-not $ready){throw 'Local CUDA initialization timed out'}
  Start-Process "http://127.0.0.1:$Port"
  Write-Host "$($status.backend) rendering on $($status.device) at http://127.0.0.1:$Port"
  $process.WaitForExit()
}finally{if(-not $process.HasExited){Stop-Process -Id $process.Id}}

