# -*- coding: utf-8 -*-
"""周一010 马拉加vs拉科 头条版合规体检 (pipeline Step 6)"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'I:\阿飞说球\📝文章\20260825\周一010_马拉加vs拉科_头条版.md'
text = open(path, encoding='utf-8').read()

banned = ['赔率', '盘口', '庄家', '泊松', '蒙特卡洛', 'EV', '凯利', '打穿', '欧赔', '赢盘',
          '今晚', '今天', '明天', '昨天', '刚刚', '几个小时', '北京时间',
          '基本盘', '成色', '互相印证', '真金白银', '高度集中', '完全吻合', '完全一致', '拉满', '闭眼赢',
          '表面看', '说白了', '实锤', '推荐', '稳胆', '红单', '串关', '过关', '下注', '投注',
          '上车', '跟单', '重仓', '梭哈', '公号', '私信', '进群', '带红', '押',
          # 头条社区规范红线(2025-12-01): 荐股荐彩/引流/夸大
          '彩票', '六合彩', '赌球', '博彩', '荐彩', '推荐购买', '跟进购买', '买主胜', '买客队',
          '必发', '稳赢', '必中', '万无一失', '100%稳', '微信号', '二维码', '加群', '联系方式',
          'bet365', '皇冠', '威廉希尔', '赌']
found = {}
for k in banned:
    n = text.count(k)
    if n:
        found[k] = n

title = text.split('\n')[0].replace('# ', '')
lines = text.split('\n')
content_lines = [l for l in lines if not l.startswith('#')]
cn = len(re.findall(r'[\u4e00-\u9fff]', ''.join(content_lines)))
dash = text.count('——')
arrow = text.count('→')
arrows = text.count('->')
oral = ['说白了', '说句不好听的', '别急着', '真要', '确实', '你看看', '你信不信', '先别急着', '说实话', '说真的', '难说']
fo = [w for w in oral if w in text]

print('标题(%d字): %s' % (len(title), title))
print('禁用词: %s' % (found if found else '无'))
print('中文字数: %d' % cn)
print('破折号(——): %d (金句除外≤3)' % dash)
print('箭头(→): %d (应0)' % (arrow + arrows))
print('口语化标记: %s' % fo)
print('数字合规检查(具体小数赔率如 1.37/2.33 直接出现):')
for m in re.finditer(r'(?<!\d)(\d\.\d{2})(?!\d)', text):
    print('  WARN: 小数数字 "%s" 上下文: ...%s...' % (m.group(1), text[max(0, m.start()-18):m.end()+12].replace('\n', ' ')))
print('检查完成')
