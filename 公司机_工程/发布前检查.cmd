@echo off
rem ============================================================
rem 发布前检查.cmd — 一次跑完三道闸(2026-09-15 建, 公众号被屏蔽事件后)
rem 用法:
rem   发布前检查.cmd "文章.md"
rem   发布前检查.cmd "文章.docx" "阿飞说球\02_工具\match_configs\xxx.json"
rem 判定: 平台风险扫描 A/B 级必须为 0; AI 嫌疑分 单场<2.5 / 串烧<2.0
rem ============================================================
setlocal
set "F=%~1"
if "%F%"=="" (
  echo 用法: 发布前检查.cmd "文章.md" [config.json]
  exit /b 2
)
echo.
echo ========== 1/3 平台风险扫描(公众号: A/B 级必须为 0) ==========
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" "阿飞说球\02_工具\risk_scan.py" "%F%"
echo.
echo ========== 2/3 本地 AI 嫌疑(单场 ^<2.5 / 串烧 ^<2.0) ==========
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" "阿飞说球\02_工具\zhuque_local_check.py" --file "%F%"
if not "%~2"=="" (
  echo.
  echo ========== 3/3 发布合规终检(docx) ==========
  powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" "阿飞说球\02_工具\check_release.py" --docx "%F%" --config "%~2"
)
echo.
echo ========== 检查完毕: 上面有任何 A 级词 / 推荐性表述 / 低分, 一律先改再发 ==========
endlocal
