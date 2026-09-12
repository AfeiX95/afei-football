# 阿飞·赛博聊球 — 一键运行(PowerShell 版)
# 用法:
#   .\run.ps1 阿飞说球\02_工具\afei_generator.py --config "阿飞说球\02_工具\match_configs\xx.json"
#   .\run.ps1 阿飞说球\02_工具\check_release.py --docx "xx.docx" --config "xx.json"
#   .\run.ps1 采集数据\官网\fetch_squads.py
#
# 作用: 统一用项目 .venv(Python 3.11) 跑脚本, 并设好两个本机必需的环境变量:
#   PYTHONIOENCODING=utf-8      → 控制台输出中文不乱码
#   UV_CACHE_DIR / .uv-cache    → uv 缓存放在工作区内(默认缓存目录被沙箱拒写)
#   PLAYWRIGHT_BROWSERS_PATH    → 浏览器目录指向工作区(本机用系统 Chrome, 一般用不到)
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
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $root '.playwright-browsers'

& $py @Args
$code = $LASTEXITCODE
if ($null -eq $code) { $code = 0 }
exit $code
