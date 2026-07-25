# Hermes 插件与浏览器后端配置

> 为足球项目配置 Web 搜索/抓取/浏览器自动化能力的操作记录

---

## 一、Web 搜索插件

### Tavily（推荐，当前已启用）

| 项目 | 内容 |
|:-----|:------|
| 状态 | ✅ **已启用 + API Key已配置** |
| 安装 | `hermes plugins enable web-tavily` |
| API Key | 注册 https://app.tavily.com → 免费额度1000次/月 |
| 配置 | `hermes config set providers.tavily.api_key "你的key"` |
| 验证 | `pip install tavily-python` → Python测试搜索 |

### Firecrawl（不可用）

域名 `firecrawl.ai` 标价$350,000出售中。不可用。

---

## 二、浏览器自动化后端

### 本地 Chromium（默认，稳定可用）

当前使用的浏览器后端，无需API Key。

```bash
hermes config set browser.provider ""  # 恢复默认
```

### CamoFox（免费，需本地搭建，Windows有兼容问题）

Camofox 是开源反检测浏览器（基于 Firefox 魔改版 Camoufox）。

| 项目 | 内容 |
|:-----|:------|
| 源码 | https://github.com/redf0x1/camofox-browser |
| 安装 | `npm install -g camofox-browser` |
| 启动 | `camofox-browser` |
| 配置 | `hermes config set browser.provider camofox` |

**Windows 注意：**
- `better-sqlite3` 需要 C++ 编译工具（node-gyp）
- `npm install` 可能因 EBUSY 文件锁失败，需手动清理 `%APPDATA%/npm/node_modules/camofox-browser`
- 首次 `npm install` 先用 `--ignore-scripts` 跳过编译，再单独装 native 模块

---

## 三、插件管理常用命令

```bash
hermes plugins list              # 列出所有插件
hermes plugins enable <name>     # 启用
hermes plugins disable <name>    # 停用
hermes config show               # 查看所有配置
hermes config set <key> <value>  # 设置配置项
```

插件启用后需 `/reset` 或重启 Hermes 会话才生效。
