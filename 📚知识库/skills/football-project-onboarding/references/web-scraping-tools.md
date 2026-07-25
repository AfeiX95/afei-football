# Web Scraping Tools — 可用性与配置

> 足球分析依赖数据采集（竞彩网、懂球帝、ESPN等），以下是在当前环境验证过的工具。

## 一、当前可用的工具

| 工具 | 类型 | 状态 | 是否需要Key | 说明 |
|:----|:-----|:----|:-----------|:------|
| `web_extract` | 内置工具 | ✅ 可用 | 否 | 页面内容提取为Markdown，适合静态页面 |
| `browser` | 内置工具 | ✅ 可用 | 否 | 本地Chromium，适合JS动态渲染页 |
| `web_search` | 内置工具 | ✅ 可用 | 否 | 网页搜索，默认5条结果 |
| **Tavily** | 插件/已启用 | ✅ 已配置 | `TAVILY_API_KEY` | 网页搜索+内容提取+crawl，免费额度1000次/月 |

## 二、Tavily（已配置可用）

### 状态
- ✅ 插件 `web-tavily` 已启用
- ✅ API Key 已配置（`TAVILY_API_KEY`）
- ✅ `tavily-python` 包已安装
- 下次 `/reset` 后生效

### 验证方法
```python
from tavily import TavilyClient
client = TavilyClient()
r = client.search(query="关键词", search_depth="basic")
# 返回5条结果，含title/url/content
```

## 三、曾尝试但不可用的方案

### Firecrawl ❌
- 域名 `firecrawl.ai` **在出售**（标价35万美元）
- 服务不可用，无法注册
- 替代方案：Tavily

### CamoFox ⛔
- 不是云API服务，是**本地自托管工具**
- 基于开源 [Camoufox](https://github.com/daijro/camoufox)（Firefox魔改版，引擎级反检测）
- 如果未来需要：`npm install -g camofox-browser` + 本地启动服务
- 当前环境未安装Node.js + 未配置

### Jina Reader ❓
- `https://r.jina.ai/URL` 理论可用（免费URL转Markdown）
- 当前环境测试不稳定，不推荐依赖

## 四、推荐数据采集方案

| 场景 | 推荐工具 | 原因 |
|:-----|:---------|:------|
| 竞彩网赔率 | `curl` API | 直接拉JSON，最快最稳 |
| 竞彩网页面数据 | `browser` | JS动态渲染，需浏览器 |
| 懂球帝/ESPN文章 | `web_extract` | 静态内容，直接提取 |
| 综合搜索 | `web_search` + Tavily | 多源对比 |
| 深度爬取 | Tavily crawl | 自带crawl功能 |

## 五、环境配置记录

```bash
# Tavily（已完成）
hermes plugins enable web-tavily
pip install tavily-python
# 写入 .env: TAVILY_API_KEY=***

# 如果未来要装CamoFox（未执行）
npm install -g camofox-browser
camofox-browser  # 启动服务
hermes config set browser.provider camofox
```
