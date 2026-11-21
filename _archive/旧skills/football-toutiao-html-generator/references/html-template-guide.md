# 头条号深色主题HTML模板参考

## 完整HTML结构

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body>
<div style="background:#0f0f1a;color:#e0e0e0;
  font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
  line-height:1.8;padding:20px;max-width:720px;margin:0 auto;">

  <!-- 标题 -->
  <h2>赫根主场迎战三连胜索尔纳，残阵防线扛得住吗？</h2>
  <p style="color:#888;font-size:0.9em;">#瑞典超 #赫根 #索尔纳 · 第14轮</p>
  <hr>

  <!-- 正文段落 -->
  <p>开篇文字...</p>

  <!-- 表格 -->
  <table style="width:100%;border-collapse:collapse;text-align:center;margin:16px 0;">
    <tr style="background:#1e3a5f;">
      <th style="padding:8px;border:1px solid #333;color:#fff;">维度</th>
      <th style="padding:8px;border:1px solid #333;color:#fff;">赫根</th>
    </tr>
    <tr style="background:#16213e;">
      <td style="padding:8px;border:1px solid #333;color:#ddd;">数据</td>
      <td style="padding:8px;border:1px solid #333;color:#ddd;">值</td>
    </tr>
  </table>

  <!-- SVG图表嵌入 (直接粘贴SVG代码) -->
  <svg xmlns="...">...</svg>
  <p style="text-align:center;color:#888;font-size:0.85em;">⬆ 图表说明</p>

  <!-- 结尾 -->
  <hr>
  <p style="font-size:0.85em;color:#888;">免责声明</p>
</div>
</body>
</html>
```

## 色板

| 用途 | 色值 | 示例 |
|:-----|:----:|:----:|
| 背景 | `#0f0f1a` | 全页深色底 |
| 卡片/表格行1 | `#16213e` | 交替行 |
| 表格行2 | `#1a1a2e` | 交替行 |
| 表头 | `#1e3a5f` | 表头深蓝 |
| 正文 | `#e0e0e0` | 主文字 |
| 小字 | `#888888` | 说明/标签 |
| 主队/正数 | `#4fc3f7` | 蓝色高亮 |
| 平局/中性 | `#ffd93d` | 黄色高亮 |
| 客队/负数 | `#ff6b6b` | 红色高亮 |
| 健康 | `#4caf50` | 绿点/状态 |
| 边框/分隔 | `#333333` | 表格边框 |

## 头条号注意事项

1. **最大宽度720px** — 头条编辑器默认内容区宽度
2. **禁用JS** — 所有图表必须用SVG静态代码，不能用JavaScript
3. **禁用外部资源** — 所有图片/SVG必须inline嵌入，不能用`<img src="url">`
4. **颜色对比度** — 深色背景+浅色文字，确保可读性
5. **移动端适配** — SVG加`width="100%" style="max-width:600px"`
6. **字号** — 正文建议用浏览器默认（不设font-size），小字用0.85em
7. **段落间距** — 不需要额外margin，line-height:1.8自动控制
