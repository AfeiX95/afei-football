---
name: dashboard-js-pitfalls
description: "交互式HTML仪表盘开发的常见JS陷阱与修复方案。适用于内嵌Chart.js+48队数据库+Wikipedia回退的静态单页仪表盘（如79D_智能搜索版），记录innerHTML覆盖DOM、嵌套模板字面量、重复对象键等运行时错误的根因与修复模式。"
version: 1.0.0
author: afei
license: MIT
metadata:
  hermes:
    tags: [javascript, html, dashboard, debugging, pitfalls, frontend]
    related_skills: [match-model-pipeline, afei-football-writer]
---

# HTML仪表盘JS陷阱手册

## When to Use

- 开发/修改 79D 智能搜索仪表盘或其他交互式HTML数据面板时遇到白屏、信息栏缺失、控制台报错
- 用户报告"点了没反应"、"信息栏没显示"、"搜索不工作"
- 需要调试 `getElementById` 返回 null、Chart.js 不渲染、模板不更新的问题

## 陷阱1：innerHTML 覆盖 DOM 元素 ID（⚠️ 最高频）

**症状：** `TypeError: Cannot set properties of null (setting 'textContent')`

**根因：** `element.innerHTML = '...'` 替换了该元素内的全部子节点。如果新 HTML 中没有带上被覆盖元素的 `id`，后续 `getElementById('xxx')` 返回 null。

**修复模式：**
```javascript
// ❌ 错误：新模板中 <span> 没带 id
document.getElementById('dashTitle').innerHTML = `<span>${hName} VS ${aName}</span> <span>${group}</span>`;
document.getElementById('dashGroup').textContent = group; // ← crash! dashGroup was replaced!

// ✅ 正确：新模板中包含 id
document.getElementById('dashTitle').innerHTML = `<span>${hName} VS ${aName}</span> <span id="dashGroup">${group}</span>`;
document.getElementById('dashGroup').textContent = group; // ✓ works
```

**防御策略：** 每次 `innerHTML` 赋值后，所有被替换区域内的 `getElementById` 调用都要重新检查——元素已经没了。要么（a）新模板里带上 id，要么（b）先取引用再赋值 innerHTML，要么（c）改用 `textContent` 单独更新目标元素。

## 陷阱2：3层+嵌套模板字面量（`` ` `` 套 `` ` `` 套 `` ` ``）

**症状：** JS 解析通过但运行时报错；或模板不渲染、函数后续代码全部跳过。

**根因：** JavaScript 的模板字面量（backtick）虽然支持嵌套，但超过2层时引擎容易混淆起止位置，且不同浏览器/Node版本行为不一致。

**修复模式：**
```javascript
// ❌ 错误：3层嵌套
document.getElementById('foo').innerHTML = `
  ${condition ? `inner ${x > 5 ? `deep ${val}` : 'other'}` : 'fallback'}
`;

// ✅ 正确：用 IIFE 或普通函数 + 字符串拼接
document.getElementById('foo').innerHTML = (function(){
  let result = '模型对' + team + '胜率定价 <strong>' + pct + '%</strong>';
  if(condition) {
    result += '品牌溢价系数 <strong>+' + premium + 'pp</strong>';
    if(x > 5) result += '价值信号指向 <strong>' + direction + '</strong>';
  }
  return result;
})();
```

**规则：** 任何包含三元运算符且分支内有 backtick 表达式的场景，提取成独立函数或 IIFE，用 `+` 拼接字符串。

## 陷阱3：对象字面量中重复键名

**症状：** 预期属性在运行时 undefined；代码逻辑走分支 A 但实际走了分支 B。

**根因：** JS 对象字面量中重复的 key，**最后一个覆盖前面的**。

```javascript
const DB = {
  cape_verde: { name: '佛得角', note: '非洲新军' },  // ← 被覆盖！
  // ... 中间代码 ...
  cape_verde: { name: '佛得角' }  // ← 生效（无note属性）
};
// DB.cape_verde.note → undefined! 但没报错，静默丢失
```

**防御策略：** 
- 大对象定义时用 `search_files` 或 Python 脚本检查重复键
- 把分散定义的同类条目合并在一起，不要分两处
- 每次编辑大对象后，用正则查重复：`re.findall(r'(\w+):\{name:', text)`

## 陷阱4：file:// 协议阻塞 fetch 请求

**症状：** CORS 错误、Wikipedia API 404（实际是请求根本没发出去）

**根因：** 浏览器安全策略禁止 `file://` 协议的页面发起 `fetch` 请求。

**解决：** 必须通过本地服务器或 HTTPS 打开
```bash
python -m http.server 8080
# → http://localhost:8080/index.html
```

如果用 file:// 双击打开，所有外部 API（Chart.js CDN、Wikipedia fetch）全部不可用。

## 陷阱5：Chart.js CDN 未加载导致图表渲染中断

**症状：** 控制台报 `Chart is not defined`，图表区域空，后续 JS 不执行（如果没用 try/catch）。

**解决：**
- CDN 用 `chart.umd.min.js`（UMD 格式兼容性好）
- 图表渲染代码包裹 `try/catch`
- 备选：内联一个最小化的 Chart.js（不推荐，包太大）

```javascript
function initMCCharts(h,a,hl,al){
  try {
    // ... 创建图表
  } catch(e) { console.error('Chart渲染失败，可能是CDN未加载', e); }
}
```

## 陷阱6：async 函数未捕获错误导致静默失败

**症状：** 点了搜索按钮但没有任何反应，也不报错

**根因：** `handleSearch` 是 async 函数，内部 await 的 fetch 如果抛出异常且外层 catch 不完善，Promise 被静默吞掉。

**解决：**
- 所有 `.catch()` 必须跟随
- `fetch(url).catch(() => null)` 而不是 `fetch(url)`
- 搜索入口加外层 try/catch

```javascript
async function handleSearch(){
  try {
    // ...
    let r = await fetch(url).catch(() => null);
    if(!r || !r.ok) { setStatus('获取失败','error'); return; }
    // ...
  } catch(e) { setStatus('出错了：'+e.message,'error'); }
}
```
