# 仪表盘部署到 GitHub Pages

## 适用场景

把 79D_全维数据仪表盘_智能搜索版.html 发到手机/分享给别人，对方无需搭建环境，打开浏览器就能跑模型。

## 前置条件

1. 注册 GitHub 账号（https://github.com/signup）
2. 电脑上配好 SSH key（`ssh-keygen -t ed25519 -C "your@email.com"`，公钥加到 https://github.com/settings/ssh/new）

## 部署步骤

```bash
# 1. 进入项目目录
cd "C:\Users\wuyan\Documents\Claude\Projects\阿飞说球"

# 2. 初始化 Git
git init
git config user.name "你的GitHub用户名"
git config user.email "你的邮箱"
git add -A
git commit -m "初始提交"

# 3. 去 GitHub 创建空仓库（https://github.com/new）
#    仓库名随意，Public，不勾任何初始化选项

# 4. 关联远程仓库并推送
git remote add origin git@github.com:你的用户名/仓库名.git
git push -u origin master

# 5. 启用 GitHub Pages
#    打开 https://github.com/你的用户名/仓库名/settings/pages
#    Source → Deploy from a branch
#    Branch → master / (root) → Save

# 6. 等待1-2分钟，访问：
#    https://你的用户名.github.io/仓库名/20260622/79D_全维数据仪表盘_智能搜索版.html
```

## 更新仪表盘

修改 79D HTML 文件后：

```bash
cd "C:\Users\wuyan\Documents\Claude\Projects\阿飞说球"
git add -A
git commit -m "更新说明"
git push
```

GitHub Pages 自动重部署（约1分钟）。

## 注意事项

- **必须用 HTTPS 访问**（GitHub Pages 自带），不能双击 HTML 文件
- 48队数据库已内嵌，大部分数据无网络也可用
- Wikipedia 回退和 Chart.js CDN 需要联网
- 文件名含中文，URL 会被编码，不影响访问

## 仪表盘开发陷阱

### ⚠️ innerHTML 覆盖子元素 ID
```javascript
// ❌ 错误：新 innerHTML 中没有 id，后续 getElementById 返回 null
parent.innerHTML = `<span>内容</span>`;
document.getElementById('myId').textContent = 'xxx'; // 💥 Cannot set properties of null

// ✅ 正确：重新 innerHTML 时必须包含所有需要的 id 属性
parent.innerHTML = `<span id="myId">内容</span>`;
document.getElementById('myId').textContent = 'xxx';
```

### ⚠️ 嵌套模板字面量崩溃
```javascript
// ❌ 3层 `` ` `` 嵌套导致 JS 解析中断，函数在此处静默崩溃
html = `外层 ${cond ? `内层 ${cond2 ? `更内层` : 'nope'}` : 'no'}`;

// ✅ 使用 IIFE 或普通字符串拼接
html = `外层 ${(function(){ return cond ? 'yes' : 'no'; })()}`;
```

### ⚠️ 渲染函数必须 try/catch 包裹
```javascript
function renderAll() {
  try {
    renderSection1();
    renderSection2();
    renderSection3(); // 即使这里崩溃，前两个 section 的内容已写入 DOM
  } catch(e) { console.error('Render error:', e); }
}
```
没有 try/catch 时，任何一个 section 的 JS 错误都会导致后续所有 section 不被渲染（页面部分空白）。

### ⚠️ file:// 协议阻塞所有 API 请求
```text
双击 HTML 文件打开 → URL 以 file:// 开头 → 浏览器禁止发送 fetch
→ Wikipedia 回退全部失败 → 即使 URL 正确也返回 404

解决方案：
  python -m http.server 8080  # 本地测试
  GitHub Pages                  # 线上分享（自动 HTTPS）
```
