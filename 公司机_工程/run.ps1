# 阿飞·赛博聊球 — 一键运行(也可用同目录 运行.cmd 双击调用)
# 用法:
#   .\run.ps1 阿飞说球\02_工具\afei_generator.py --config "阿飞说球\02_工具\match_configs\xx.json"
#   .\run.ps1 阿飞说球\02_工具\check_release.py --docx "xx.docx" --config "xx.json"
#   .\run.ps1 采集数据\官网\fetch_squads.py
#
# 作用: 统一用项目 .venv(Python 3.11) 跑脚本, 并设好本机必需的环境变量。
# ⚠️ 本机 PowerShell 执行策略禁止直接运行 .ps1, 命令行请用: powershell -ExecutionPolicy Bypass -File run.ps1 ...
#    (或直接双击/调用 运行.cmd, 它已带 Bypass)
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    Write-Host "❌ 未找到 .venv, 先建环境:" -ForegroundColor Red
    Write-Host "   uv venv --python 3.11 .venv"
    Write-Host "   uv pip install --python .venv\Scripts\python.exe -r requirements.txt"
    exit 2
}
if (-not $Args -or $Args.Count -eq 0) {
    Get-Content (Join-Path $root 'requirements.txt') -TotalCount 12
    exit 0
}

$env:PYTHONIOENCODING = 'utf-8'
$env:UV_CACHE_DIR = Join-Path $root '.uv-cache'
# 不设 PLAYWRIGHT_BROWSERS_PATH: 本机用系统 Chrome/Edge(channel='chrome'), 无需自带 chromium

& $py @Args
$code = $LASTEXITCODE
if ($null -eq $code) { $code = 0 }
exit $code
