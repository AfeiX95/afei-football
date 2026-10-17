import re

with open('I:/阿飞说球/📚知识库/文章归档/20260720/瑞超两场_厄格里特佐加顿斯_卡尔马马尔默.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 删除一、百家欧赔 & 凯莉指数（注意HTML中的&amp;）
c = re.sub(r'<h3>一、百家欧赔[^<]*</h3>\s*<table>.*?</table>\s*', '', c, flags=re.DOTALL)

# 删除二、定价趋势
c = re.sub(r'<h3>二、定价趋势[^<]*</h3>\s*<table>.*?</table>\s*<p>.*?</p>\s*', '', c, flags=re.DOTALL)

# 重新编号 三→一 到 十三→十一
mapping = [
    ('三、基础数据', '一、基础数据'),
    ('四、近期状态', '二、近期状态'),
    ('五、战术对比', '三、战术对比'),
    ('六、关键对位分析', '四、关键对位分析'),
    ('七、关键球员对位', '五、关键球员对位'),
    ('八、天气', '六、天气'),
    ('九、更衣室', '七、更衣室'),
    ('十、数学模型', '八、数学模型'),
    ('十一、比赛剧本', '九、比赛剧本'),
    ('十二、外媒', '十、外媒'),
    ('十三、伤停', '十一、伤停'),
]
for old, new in mapping:
    c = c.replace(old, new)

with open('I:/阿飞说球/📚知识库/文章归档/20260720/瑞超两场_厄格里特佐加顿斯_卡尔马马尔默.html', 'w', encoding='utf-8') as f:
    f.write(c)

remaining = re.findall(r'[一二三四五六七八九十]+、', c)
print('剩余编号:', remaining)
ok = all(f'{i}、' in c for i in ['一','二','三','四','五','六','七','八','九','十','十一'])
print('一至十一连续:', '✅' if ok else '❌')
