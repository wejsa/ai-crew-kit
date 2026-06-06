# sync-plugin-agents.ps1  (Windows PowerShell)
#
# 플러그인 노출용 루트 agents\ 미러를 .claude\agents\ 로부터 재생성한다.
# 자세한 배경은 sync-plugin-agents.sh 주석 참조.
# .claude\agents\ 가 SSOT. 에이전트 변경 후 실행하여 agents\ 동기화 + 함께 커밋.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root ".claude\agents"
$dst  = Join-Path $root "agents"

if (-not (Test-Path $src)) { Write-Error "$src 없음"; exit 1 }
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
New-Item -ItemType Directory -Path $dst | Out-Null
Copy-Item "$src\*.md" $dst
$n = (Get-ChildItem "$dst\*.md").Count
Write-Host "synced $n agents -> agents/"
