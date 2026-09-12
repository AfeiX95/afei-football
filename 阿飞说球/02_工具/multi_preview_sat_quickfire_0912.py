# -*- coding: utf-8 -*-
"""
周六四场速览(头条 docx) — 2026-09-12
周六007 弗赖堡vs门兴(21:30) / 周六009 多特蒙德vs帕德博恩(21:30)
周六012 切尔西vs赫尔城(22:00) / 周六016 利物浦vs富勒姆(22:00)

选场依据(信息指数 = 结构差×25 + 深热度 + 悬念度×4 + 冷门空间):
  012 = 16.1 / 009 = 15.6 (两场深盘, 结构差约 40 点, 当日最高)
  016 = 11.1 (中腰段, 深热-1盘) 007 = 10.9 (用户点名)
  未选: 025/026 分数虽高(13.4/15.2), 但属T3深夜档, 按赛道纪律另开一篇
类型不重复: 009/012 是深盘受让方; 016 是热门赢不够; 007 是数据挤水分
"""
import os
import sys

BASE = r'D:\Hermes\football'
TOOL = os.path.join(BASE, '阿飞说球', '02_工具')
sys.path.insert(0, TOOL)

import multi_preview as MP  # noqa: E402

MP.OUT_DIR = os.path.join(BASE, '阿飞说球', '04_赛事文章', '2026-09', '周六四场速览')
os.makedirs(os.path.join(MP.OUT_DIR, 'charts'), exist_ok=True)   # 覆写 OUT_DIR 后必须重建图表目录

MP.TITLE = "周六007+009+012+016:两场深盘,热门赢不够?"
MP.TAGS = "#德甲 #英超 #多特蒙德 #切尔西 #利物浦 #弗赖堡"
MP.INFO_CARD = [
    "【赛事】德甲/英超 2026 常规赛 | 2026-09-12 21:30、22:00 四场连台",
    "【对阵】弗赖堡vs门兴、多特蒙德vs帕德博恩(21:30) | 切尔西vs赫尔城、利物浦vs富勒姆(22:00)",
    "【场地】欧洲各主场 | 天气以官方播报为准",
]
MP.OPENING = "\n\n".join([
    "周六21:30和22:00这四场,深盘和中腰段各两场。",
    "两场深盘是同一个现象:热门赢球概率接近八成,让球盘却只给四成不到。",
    "中腰这两场,热门同样让一球,门槛深浅却差得很远。",
])
MP.ENDING_HOOK = "这四场里,你觉得哪一场的让球门槛最不合理?评论区挑一场说说。"
MP.SUMMARY = "\n\n".join([
    "四场摆在一起,深盘那两场的让球线都在热门赢球概率的一半以下,受让方不败都排到四成上下。",
    "中腰两场反过来,016的让球门槛偏浅,007是让球盘最偏受让方的一场,而且两队上轮都刚出过状况。",
])

MP.CFGS = [
    (os.path.join(TOOL, 'match_configs', '多特蒙德vs帕德博恩.json'),
     "多特蒙德 vs 帕德博恩", "21:30",
     {'label': '多特 vs 帕德博恩(交锋)', 'w': 0, 'd': 0, 'l': 0,
      'note': '两队近年无正式交锋记录,首次交手数据空白'},
     [
         "多特1.16的热度配-2让球,让胜36.9%、让负41.8%,受让方那侧还更重。",
         "总进球期望3.67是四场里最高的,大2.5给到71.4%。",
         "冷门空间只有0.14,市场把这场定价做得很充分。",
         "半全场最低档是主主1.56,市场认定多特会从头领先到尾。",
     ],
     ("深盘里的那道门槛", "首次交手的空白", "比分落在哪一档")),
    (os.path.join(TOOL, 'match_configs', '切尔西vs赫尔城.json'),
     "切尔西 vs 赫尔城", "22:00",
     {'label': '切尔西 vs 赫尔城(交锋)', 'w': 0, 'd': 0, 'l': 0,
      'note': '近年无交锋记录,历史对位数据空白'},
     [
         "切尔西1.11是当天最热的一场,主胜隐含79.8%,英超级别的深热。",
         "让球线-2,让胜38.2%对让负39.4%,两边几乎一样重,走水22.4%。",
         "总进球期望3.49,大2.5给到68.0%。",
         "这场和009几乎是同一个模子:热门赢球八成,让两球却只有不到四成。",
     ],
     ("八成与四成的错位", "深盘的两面", "比分落在哪一档")),
    (os.path.join(TOOL, 'match_configs', '利物浦vs富勒姆.json'),
     "利物浦 vs 富勒姆", "22:00",
     {'label': '利物浦 vs 富勒姆(交锋)', 'w': 0, 'd': 0, 'l': 0,
      'note': '近年交锋数据待补,首次入选速览'},
     [
         "利物浦1.35,主胜隐含65.6%,让球线只有-1。",
         "让胜给到43.8%,走水23.0%,让负33.2%,受让方那侧是三成出头。",
         "和上一场比一下就看出差别:同样是深热,这场只让一球,门槛浅得多。",
         "翻本管线八月底那场记录:利物浦主场对诺丁汉森林,市场给到68.1%,最后2比2,市场高估了热门那一侧。",
     ],
     ("同热度不同门槛", "八月底那场留下的记录", "比分落在哪一档")),
    (os.path.join(TOOL, 'match_configs', '弗赖堡vs门兴.json'),
     "弗赖堡 vs 门兴", "21:30",
     {'label': '弗赖堡 vs 门兴(交锋)', 'w': 0, 'd': 0, 'l': 0,
      'note': '近年交锋数据待补'},
     [
         "弗赖堡1.57,主胜隐含56.4%,让球线-1。",
         "让胜34.0%对让负42.2%,受让方那侧是四场里最重的一场。",
         "门兴上轮主场3比4输给埃尔沃斯堡,盘口是让一球还输,防线刚出过状况。",
         "弗赖堡那边9月5日客场1比0赢了帕德博恩,是这四场里唯一一场近期客场零封。",
     ],
     ("让球盘最偏的一场", "两队上轮都刚交过手", "比分落在哪一档")),
]

def _main_no_images():
    """速览稿专用: 不产配图、不产比分参考表(用户 2026-09-12 定: 纯文字, 配图另配)"""
    cfgs, models = MP.run_all()
    MP._cfgs_pub, MP._models_pub = cfgs, models
    import os as _os
    blocks_md = MP.build_content(cfgs, models, sub_headings=True, with_images=False)
    blocks_docx = MP.build_content(cfgs, models, sub_headings=False, with_images=False)
    stem = MP.safe_name(MP.TITLE)
    p_md = _os.path.join(MP.OUT_DIR, stem + '.md')
    open(p_md, 'w', encoding='utf-8').write(MP.render_md(blocks_md))
    print('MD →', p_md)
    p_dx = _os.path.join(MP.OUT_DIR, stem + '.docx')
    MP.render_docx(blocks_docx, p_dx, with_images=False, publish=False, score_table=False)
    print('DOCX(纯文字版) →', p_dx)
    p_pub = _os.path.join(MP.OUT_DIR, stem + '_发布导入版.docx')
    MP.render_docx(blocks_docx, p_pub, with_images=False, publish=True, score_table=False)
    print('DOCX(头条导入版: 0 图 / 0 表格 / Heading2 层级 / 无图注) →', p_pub)


if __name__ == '__main__':
    _main_no_images()
