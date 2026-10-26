# gh 代理包装（2026-10-22）
# 原因：本机直连 github.com:443 卡 TLS 握手；api.github.com 亦不可直连。
# 本机 127.0.0.1:7897（Clash Verge）可通，故 gh 每次调用都带上代理。
#
# 用法：
#   pwsh -File scripts/gh.ps1 auth status
#   pwsh -File scripts/gh.ps1 issue list -R AfeiX95/afei-football
#   pwsh -File scripts/gh.ps1 pr view 12
#
# 注意：不改全局环境变量，只在本进程内生效。

$ErrorActionPreference = 'Stop'
$env:HTTPS_PROXY = if ($env:GH_PROXY) { $env:GH_PROXY } else { 'http://127.0.0.1:7897' }
$env:HTTP_PROXY  = $env:HTTPS_PROXY
$env:NO_PROXY    = 'gitee.com,127.0.0.1,localhost'

$gh = 'C:\Program Files\GitHub CLI\gh.exe'
if (-not (Test-Path $gh)) { $gh = 'gh' }

& $gh @args
exit $LASTEXITCODE
