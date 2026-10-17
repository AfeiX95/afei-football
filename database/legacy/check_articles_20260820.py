# -*- coding: utf-8 -*-
import re

articles = [
    ('马竞', r'I:\阿飞说球\📝文章\20260819\周三002_马竞vs马拉加_头条版.md'),
    ('奈梅亨', r'I:\阿飞说球\📝文章\20260819\周三007_奈梅亨vs博德闪耀_头条版.md'),
]

banned = ['赔率', '盘口', '庄家', '泊松', '蒙特卡洛', 'EV', '凯利', '打穿', '欧赔',
          '今晚', '今天', '明天', '昨天', '赢盘率']

for name, path in articles:
    text = open(path, encoding='utf-8').read()
    found = [k for k in banned if k in text]
    title = text.split('\n')[0].replace('# ', '')
    lines = text.split('\n')
    content_lines = [l for l in lines if not l.startswith('#') and not l.startswith('数据不会') and not l.startswith('**配图')]
    cn = len(re.findall(r'[\u4e00-\u9fff]', ''.join(content_lines)))
    dash = text.count('——')
    oral = ['说白了', '说句不好听的', '别急着', '真要', '确实', '你看看', '你信不信', '先别急着']
    fo = [w for w in oral if w in text]
    # 五五开 检查(奈梅亨篇是核心概念允许)
    print('=== %s ===' % name)
    print('标题(%d字): %s' % (len(title), title))
    print('禁用词: %s' % (found if found else '无'))
    print('中文字数: %d' % cn)
    print('破折号: %d' % dash)
    print('口语化: %s' % fo)
    print()
