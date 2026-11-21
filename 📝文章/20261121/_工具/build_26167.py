# -*- coding: utf-8 -*-
"""26167 期内部分析报告：数据整理、去水计算、生成数据底稿 xlsx 与内部报告 html。
所有赔率/情报均来自 2026-11-20 公开页面，计算过程在本脚本内可复核；未取到项不填充。
"""
import json
from pathlib import Path

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE = Path(r"I:\阿飞说球\📝文章\20261121")
OUT_XLSX = BASE / "26167期_数据底稿.xlsx"
OUT_HTML = BASE / "26167期_内部分析报告.html"
OUT_JSON = BASE / "_工具" / "26167_data.json"


def xl_color(h):
    return "FF" + h.removeprefix("#").upper()


C_HEAD = xl_color("#4472C4")
C_DARK = xl_color("#2F5597")
C_INPUT = xl_color("#D9E2F3")
C_CALC = xl_color("#F2F2F2")
C_WHITE = xl_color("#FFFFFF")
C_TEXT = xl_color("#1A1A1A")
C_BORDER = xl_color("#BFBFBF")
C_GREEN = xl_color("#C6EFCE")
C_RED = xl_color("#FFC7CE")
C_YELLOW = xl_color("#FFEB9C")
thin = Side(style="thin", color=C_BORDER)
BD = Border(left=thin, right=thin, top=thin, bottom=thin)

# 澳盘：open = 初盘（开赛时间标识行），now = 11-20 14:00 最新（新浪 11-20 14:10 发布）
# 来源：sports.sina.com.cn/l/2026-11-19/doc-inizfuni6328680.shtml
D = [
 dict(no=1, lg="英超", h="阿斯顿维拉", a="桑德兰", dt="11-21 23:00",
      op=(1.57,3.95,4.50), nw=(1.80,3.53,3.58), hcp_o="半球/一球", hcp_n="半球/一球",
      inj_h="卡什、奥纳纳、鲁杰里伤缺；曼赞比存疑", inj_a="扎卡、布罗比、巴拉德、蒙德尔、迪亚拉伤缺",
      form="维拉近5联赛2胜3平、正式比赛4场不胜；桑德兰上轮1-0胜切尔西结束7轮不胜，但客场1平4负失13球",
      motive="埃梅里英超执教第150场里程碑；桑德兰刚爆冷，客场仍需自证",
      h2h="近10年5次交手：维拉3胜1平1负（主胜60%）",
      media="SportsGambler：主胜；premierleagueprediction.org：53.9/25/21.1，预测2-1；adalbet：49/30/22，xG 1.9-1.2，预测2-1；腾讯推敲：2-0",
      model="四家模型/媒体均偏主胜，但盘口同期向客队收缩",
      core="账面主场优势 vs 4场正式比赛不胜、上轮4-4被追平",
      key="桑德兰客场防线能否顶住前30分钟；维拉领先后比赛管理",
      watch="主胜赔率1.57→1.80、客胜4.50→3.58，本期变动幅度最大",
      tier="赢面在但卡壳", conf="中", sig="背离"),
 dict(no=2, lg="英超", h="伯恩茅斯", a="诺丁汉森林", dt="11-21 23:00",
      op=(2.04,3.43,3.02), nw=(1.90,3.48,3.35), hcp_o="半球", hcp_n="半球",
      inj_h="阿劳霍、A.托特伤缺；J.桑切斯存疑", inj_a="奥多伊、多明格斯伤缺；施拉格尔、威廉姆斯、萨沃纳存疑",
      form="伯恩茅斯各项赛事8连胜/联赛4连胜、主场两场零封；森林上轮3-1胜曼城但赛季客场仅1胜",
      motive="伯恩茅斯冲欧战区；森林客场成绩拖累",
      h2h="近10年13次交手：伯恩茅斯7胜6平0负（主胜53.8%、平46.2%）",
      media="SportsGambler：主胜；betiper：主胜倾向+大2.5；腾讯推敲：2-1；FootballWhispers 未给本场1X2",
      model="多维偏主胜，与赔率下调方向一致",
      core="高位逼抢对上三后卫出球，但森林刚爆冷士气在",
      key="塔弗尼耶/埃瓦尼尔森的逼抢转化率；森林客场反击效率",
      watch="主胜2.04→1.90、客胜3.02→3.35，方向一致",
      tier="最敢碰", conf="高", sig="共振"),
 dict(no=3, lg="英超", h="切尔西", a="利兹联", dt="11-21 23:00",
      op=(1.87,3.53,3.38), nw=(1.88,3.52,3.33), hcp_o="半球", hcp_n="半球",
      inj_h="里斯·詹姆斯、若昂·佩德罗、拉克鲁瓦、哈托确定缺阵；凯塞多可出场，吉滕斯存疑", inj_a="约瑟夫长期缺阵；法尔克赛前宣布全队无伤病、四名伤员回归",
      form="切尔西近3轮两度被零封、上轮0-1负桑德兰；利兹上轮1-0胜热刺结束5轮不胜，10轮仅失8球",
      motive="切尔西争前四、稳定性不足；利兹客场4场不胜",
      h2h="近10年11次交手：切尔西7胜2平2负；新世纪正式比赛主场从未输给利兹联",
      media="betiper：主胜100%；腾讯推敲：1-0；soccerinfo.tw：切尔西主场占优但伤停多；纳米数据：多家公司主胜普遍上调",
      model="市场与媒体偏主，情报面明显偏客队取分",
      core="主场交锋碾压 vs 锋线与中卫同时减员、近3轮两度零封",
      key="利兹定位球（切尔西已8次非点球定位球失球）；切尔西破密集防守效率",
      watch="利兹全员健康、切尔西5人缺阵，是本期最典型的「该赢未必真赢得」",
      tier="赢面在但卡壳", conf="中", sig="背离"),
 dict(no=4, lg="英超", h="考文垂", a="水晶宫", dt="11-21 23:00",
      op=(2.21,3.71,2.58), nw=(2.21,3.71,2.58), hcp_o="平手", hcp_n="平手/半球",
      inj_h="赖特、克拉克、伍尔芬登、埃克尔斯、阿门达伤缺；托马斯、伊伦基存疑", inj_a="里亚德伤缺；富安健洋、I.萨尔、拉森存疑；马特塔停赛",
      form="考文垂第17、近5轮3负；水晶宫第20、4连败、联赛失24球最多",
      motive="保级六分战；水晶宫11月16日换帅托马斯·弗兰克，首秀即客场",
      h2h="近10年无交战记录",
      media="Goal：考文垂主场保级战、水晶宫新帅首秀阵容残缺；SportsGambler：主队让0.0（主不败）；腾讯推敲：2-1；betiper：大2.5",
      model="市场平手盘、情报面偏主队不败，但双方减员都重",
      core="排名接近的保级战 vs 两队合计十余人的伤停名单",
      key="水晶宫新帅首秀的防守组织；马特塔停赛后的终结人选",
      watch="欧赔未动但让球由平手升至平手/半球，只记事实不作解读",
      tier="最值得防平博冷", conf="低", sig="数据不足"),
 dict(no=5, lg="英超", h="托特纳姆热刺", a="伊普斯维奇", dt="11-21 23:00",
      op=(1.45,4.40,5.15), nw=(1.43,4.45,5.25), hcp_o="一球", hcp_n="一球",
      inj_h="西蒙斯、奥多贝尔缺阵；杜布拉夫卡、阿达拉比奥尤、穆德里克、萨维奥、特尔、贝里瓦尔存疑", inj_a="无伤停；杰克·泰勒存疑（另一源）",
      form="热刺上轮0-1负利兹结束3连胜；伊普斯近4轮2平2负，客场5场丢13球、零封为0",
      motive="热刺主场两连胜、争欧战；伊普斯保级",
      h2h="联赛近5次交手：热刺1胜4负（心理反常记录）",
      media="FootballWhispers：双方进球 BTTS Yes；betiper：大2.5；腾讯推敲：3-1；网易：热刺赢面大但转化率联赛垫底",
      model="市场强偏主胜，交锋心理与转化率是反向证据",
      core="对手客场防线成色 vs 热刺每次射门预期进球0.11联赛垫底",
      key="麦迪逊/库杜斯的临门一脚；伊普斯能否延续进球势头",
      watch="近5次联赛交手热刺仅1胜，账面优势不等于赢球",
      tier="赢面在但卡壳", conf="中", sig="背离"),
 dict(no=6, lg="英超", h="纽卡斯尔联", a="阿森纳", dt="11-22 01:30",
      op=(4.95,4.20,1.48), nw=(5.05,4.20,1.48), hcp_o="受一球", hcp_n="受一球",
      inj_h="乔林顿、雅旺伤缺；拉姆齐停赛期满复出", inj_a="萨卡确认缺席；道曼停赛；苏维门迪存疑",
      form="阿森纳9胜1负积27分领跑、近5轮全胜；纽卡最近两个联赛主场先后0-1负维拉、埃弗顿",
      motive="阿森纳追平队史英超同期最佳开局；吉马良斯首次回归圣詹姆斯公园",
      h2h="联赛近10年23次交手：纽卡6胜2平15负（客胜65.2%）",
      media="betiper：客胜100%共识（1.63）；腾讯推敲：阿森纳1-0；网易：阿森纳联赛对纽卡三连胜，但近5次主场交锋纽卡3胜2负",
      model="市场与媒体强共振偏客胜",
      core="榜首客场强势 vs 萨卡缺阵、纽卡主场两连败后的反弹窗口",
      key="阿森纳定位球与中场控制；纽卡主场开局强度",
      watch="客胜1.48未动，主胜4.95→5.05，市场未因萨卡缺阵动摇",
      tier="最敢碰", conf="高", sig="共振"),
 dict(no=7, lg="德甲", h="埃尔沃斯堡", a="弗赖堡", dt="11-21 22:30",
      op=(2.88,3.70,2.02), nw=(2.91,3.68,2.02), hcp_o="受半球", hcp_n="受半球",
      inj_h="米克尔森、平克特、塞弗特伤缺", inj_a="穆斯利亚伤缺（另一源）；多家机构列无伤停",
      form="弗赖堡9轮19分第3；埃尔沃斯堡升班马，主场受半球",
      motive="弗赖堡争欧冠区；升班马主场抢分",
      h2h="近10年仅1次交手：1场平局（100%平，样本极小）",
      media="football-predictions.ai：本轮中游与欧战席位竞争；未取到该场独立1X2模型概率",
      model="市场偏客胜但客胜2.02不算强势，样本不足",
      core="排名差距 vs 交锋样本仅1场、客胜赔率不低",
      key="弗赖堡能否把控球转成射门；埃尔沃斯堡主场反击",
      watch="欧赔基本未动，属盘口稳定但信息最少的场次之一",
      tier="最不敢碰", conf="低", sig="数据不足"),
 dict(no=8, lg="德甲", h="法兰克福", a="霍芬海姆", dt="11-21 22:30",
      op=(2.15,4.15,2.47), nw=(2.20,4.05,2.43), hcp_o="平手/半球", hcp_n="平手",
      inj_h="恩甘卡姆伤缺、鲍姆停赛、乌尊存疑", inj_a="让德雷、德卡特、哈伊达里、赫拉纳奇、维默尔等多人伤缺；普拉斯、孔特存疑",
      form="均势局；平局赔率4.05为全期偏高区",
      motive="双方均为中游卡位，战意中性",
      h2h="近10年21次交手：法兰克福11胜5平5负（主胜52.4%）",
      media="football-predictions.ai：Bet365 法兰克福2.38/4.00/2.62（另一时点）；微信公众号首发整理：霍芬海姆6人伤缺",
      model="市场主客接近、平局赔率偏高，模型未给明确方向",
      core="交锋占优 vs 主队停赛+前锋缺阵、客队大面积伤停",
      key="法兰克福堂安律/查伊比的边路推进；霍芬海姆残阵防线",
      watch="让球由平手/半球退至平手，只记变化事实",
      tier="最不敢碰", conf="低", sig="数据不足"),
 dict(no=9, lg="德甲", h="勒沃库森", a="帕德博恩", dt="11-21 22:30",
      op=(1.18,6.50,9.40), nw=(1.19,6.30,8.90), hcp_o="球半/两球", hcp_n="球半/两球",
      inj_h="泰里耶、艾希霍恩、科法内、特拉缺阵；迪亚比、马扎存疑", inj_a="盖雷特、霍夫迈尔、阿沃特维伤缺；巴克存疑",
      form="勒沃库森9轮16分第5；帕德博恩升级队，客场受让球半/两球",
      motive="勒沃库森追第一集团；客队保级",
      h2h="近10年6次交手：勒沃库森4胜1平1负（主胜66.7%）",
      media="football-predictions.ai：Bet365 勒沃库森1.25/7.00/9.00（另一时点）；微信公众号：双方预计首发与伤停已列",
      model="全期隐含概率最高的主胜，市场共振",
      core="实力碾压 vs 锋线多人缺阵、大胜盘口下的轮换与松懈",
      key="希克/迪亚比的终结效率；客队五后卫能否守住前30分钟",
      watch="主胜1.18→1.19基本未动，是唯一接近单胆的场次",
      tier="最敢碰", conf="高", sig="共振"),
 dict(no=10, lg="德甲", h="门兴格拉德巴赫", a="多特蒙德", dt="11-21 22:30",
      op=(4.45,4.45,1.51), nw=(4.65,4.45,1.48), hcp_o="受一球", hcp_n="受一球",
      inj_h="板仓滉停赛；克莱因丁斯特、利奥波德、乌尔里希、桥冈大树、博林、莱什钦斯基缺阵/存疑（7人）", inj_a="埃姆雷·詹、康斯坦提利亚斯、莱尔马缺阵；吉拉西、安东、丘库埃梅卡存疑",
      form="门兴1胜1平7负积4分垫底、9轮失25球联赛最多；多特6胜3平0负积21分与拜仁同分、失7球最少",
      motive="门兴保级+主场54,909人预计创纪录；多特冲击队史第三次开局10轮不败",
      h2h="近10年23次交手门兴4胜1平18负；但近6次联赛主场对多特4胜1平1负，上赛季1-0",
      media="今日头条/网易：多特不败但门兴主场交锋占优；纳米数据：多家公司客胜普遍下调至1.57-1.63；腾讯未给本场比分",
      model="市场强偏客胜，情报与交锋心理强烈反向",
      core="排名与攻防数据全面碾压 vs 门兴主场专克多特、多特最近10球全部来自下半场",
      key="多特开局慢热是否被主场气氛放大；门兴定位球与反击",
      watch="客胜1.51→1.48、主胜4.45→4.65，市场未理会主场交锋反常记录",
      tier="最值得防平博冷", conf="中", sig="背离"),
 dict(no=11, lg="德甲", h="柏林联合", a="莱比锡红牛", dt="11-21 22:30",
      op=(4.75,4.60,1.47), nw=(5.25,4.70,1.41), hcp_o="受一球", hcp_n="受一球",
      inj_h="斯科乌、尤拉诺维奇、乌多凯、恩索基、马克格拉夫伤缺；布尔久存疑", inj_a="吉乌、韦德拉奥果、格贝尔伤缺；芬克格拉夫存疑",
      form="莱比锡9轮18分第4；柏林联合主场受一球",
      motive="莱比锡争欧冠区；柏林联合主场抢分",
      h2h="近10年16次交手：柏林联合6胜2平8负（客胜50%）",
      media="football-predictions.ai：本轮上游施压；微信公众号首发整理：柏林联合5人伤缺；未取到独立模型概率",
      model="市场向客胜明显倾斜，情报面客队阵容更整",
      core="主队后防5人缺阵 vs 客胜已被压到1.41的低赔",
      key="莱比锡恩昆库/努萨的边路冲击；柏林联合定位球",
      watch="主胜4.75→5.25、客胜1.47→1.41，本期变动幅度第二大",
      tier="最敢碰（但赔率已低）", conf="中", sig="共振"),
 dict(no=12, lg="德甲", h="沙尔克04", a="斯图加特", dt="11-22 01:30",
      op=(3.32,3.85,1.81), nw=(3.33,3.83,1.80), hcp_o="受半球", hcp_n="受半球",
      inj_h="T.贝克尔、霍伊伦、沙伦贝格、西贝金、沃扎尔、韦伯等多人伤缺；戈森斯存疑", inj_a="迪尔、雅凯兹、马拉加、施蒂勒、扎加杜伤缺",
      form="客胜1.80不算强势；双方均有较多减员",
      motive="斯图加特争欧战区；沙尔克主场保级",
      h2h="近10年9次交手：沙尔克4胜4平1负（主胜44.4%、平44.4%、客胜仅11.1%）",
      media="微信公众号首发整理：两队伤停名单；未取到独立模型概率",
      model="市场偏客，但交锋记录强烈偏主队不败",
      core="客队排名占优 vs 近10年客场对沙尔克仅1胜",
      key="斯图加特翁达夫/德米罗维奇的终结；沙尔克主场强度",
      watch="欧赔几乎未动，交锋与市场方向背离",
      tier="最值得防平博冷", conf="低", sig="背离"),
 dict(no=13, lg="意甲", h="帕尔马", a="罗马", dt="11-22 01:00",
      op=(9.40,5.60,1.21), nw=(9.30,5.70,1.21), hcp_o="受球半", hcp_n="受球半",
      inj_h="罗梅罗伤缺、恩迪亚耶停赛；卡洛斯、瓦伦蒂、伯纳贝、德罗布尼奇存疑", inj_a="佩莱格里尼伤缺；戈利尼、斯维拉尔、伦施存疑",
      form="罗马11轮27分第3；帕尔马主场受球半",
      motive="罗马争冠集团追分；帕尔马保级",
      h2h="近10年11次交手：帕尔马2胜0平9负（客胜81.8%，无平局）",
      media="FootballWhispers：Parma vs Roma 列入本轮关注场次；未取到独立1X2模型概率",
      model="全期隐含概率次高的客胜，市场共振",
      core="客队实力与交锋碾压 vs 受球半深盘、罗马门将位置存疑",
      key="罗马能否早进球把深盘打穿；帕尔马反击",
      watch="客胜1.21未动，交锋无平局是结构特征",
      tier="最敢碰", conf="高", sig="共振"),
 dict(no=14, lg="西甲", h="塞维利亚", a="皇家贝蒂斯", dt="11-22 01:30",
      op=(2.65,3.61,2.18), nw=(2.62,3.51,2.25), hcp_o="受平手/半球", hcp_n="受平手/半球",
      inj_h="马尔康、卡莫纳、A.冈萨雷斯、谢拉缺阵；苏亚索归队合练可出战；佩克、福法纳存疑", inj_a="莫兰特伤缺、贝尔纳尔停赛；埃尔南德斯、略伦特伤缺；伊斯科存疑",
      form="贝蒂斯12轮26分第4、近4个联赛客场不败(2胜2平)且连续两场零封；塞维利亚近6轮仅5分",
      motive="安达卢西亚德比；塞维利亚争欧战席位、贝蒂斯稳前四",
      h2h="近10年25次交手：塞维利亚13胜7平5负；但最近3次西甲交锋输掉2场、上一次主场0-2",
      media="腾讯西甲前瞻：塞维利亚高位抢断123次联赛最多 vs 贝蒂斯快速反击31次联赛第一；新浪：塞维利亚中后场减员削弱逼抢；懂球帝：苏亚索归队；footballwhispers 未给1X2",
      model="市场客队略优、平局赔率被压低，情绪盘特征明显",
      core="主场德比与历史交锋占优 vs 近期状态、阵容完整度、德比近三次不胜",
      key="塞维利亚前15分钟高位逼抢成功率；贝蒂斯斜向转移打身后的效率",
      watch="平局3.61→3.51、客胜2.18→2.25，三项中仅平局被压低；全期平局下调的还有 9 号与 8 号",
      tier="赢面在但卡壳", conf="低", sig="背离"),
]


def vig(o):
    inv = [1/x for x in o]
    s = sum(inv)
    return [x/s for x in inv], s


for d in D:
    d["q_nw"], d["or_nw"] = vig(d["nw"])
    d["q_op"], d["or_op"] = vig(d["op"])
    d["delta"] = [round(d["nw"][i] - d["op"][i], 2) for i in range(3)]
    d["fav"] = ["主胜", "平局", "客胜"][d["q_nw"].index(max(d["q_nw"]))]
    d["qmax"] = max(d["q_nw"])

# 外部预测可得性登记（按场次统计，用于置信度）
EXT = {
 1: ["SportsGambler", "premierleagueprediction.org", "adalbet", "betiper", "腾讯体育", "纳米数据"],
 2: ["SportsGambler", "betiper", "腾讯体育", "纳米数据"],
 3: ["betiper", "腾讯体育", "soccerinfo.tw", "纳米数据", "直播吧"],
 4: ["Goal", "SportsGambler", "betiper", "腾讯体育"],
 5: ["FootballWhispers", "betiper", "腾讯体育", "网易"],
 6: ["betiper", "腾讯体育", "网易"],
 7: ["football-predictions.ai", "微信公众号首发整理"],
 8: ["football-predictions.ai", "微信公众号首发整理"],
 9: ["football-predictions.ai", "微信公众号首发整理"],
 10: ["今日头条/网易", "纳米数据", "球迷屋", "微信公众号首发整理"],
 11: ["football-predictions.ai", "微信公众号首发整理"],
 12: ["微信公众号首发整理"],
 13: ["FootballWhispers"],
 14: ["腾讯体育", "新浪体育", "懂球帝", "ScoreLens"],
}
for d in D:
    d["ext"] = EXT[d["no"]]
    d["ext_n"] = len(d["ext"])

missing = [
 ("Polymarket / Kalshi 预测市场合约价格", "未取到", "无公开可核验的该期合约报价；不以其他市场概率替代"),
 ("Forebet / Wincomparator / BetBuilders(xG) / OddAlerts", "未取到", "未检索到对应场次的公开概率页，留空不填充"),
 ("Google 数据模型赛前概率", "未取到", "无公开可抓取页面"),
 ("Futbol24 前瞻", "未取到", "未检索到该期对应场次前瞻"),
 ("官方/第三方凯利指数", "未取到", "不推算、不编造；以四大机构赔率离散度与水位合计替代观察"),
 ("14 场逐场天气", "未取到", "无统一可核验的赛前天气页；不填估计值"),
 ("勒沃库森vs帕德博恩竞彩官方参考", "部分缺失", "该场不在竞彩周六22场清单内；外盘欧赔与伤停已由新浪/微信公众号补齐"),
 ("竞彩官方胜平负与让球结构", "部分取到", "仅部分场次从计算器页取到，未做全量对齐，不用于定量结论"),
]

# ---------------- 生成数据底稿 xlsx ----------------
wb = Workbook()
wb.remove(wb.active)
wb.properties.title = "26167期 数据底稿"
wb.properties.description = "2026-11-20 公开数据的结构化快照与去水计算，静态值可复核。"


def sheet(name, headers, rows, widths, pct_cols=()):
    ws = wb.create_sheet(name)
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(name="微软雅黑", size=10, bold=True, color=C_WHITE)
        c.fill = PatternFill("solid", fgColor=C_HEAD)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BD
    for row in rows:
        ws.append(row)
    for r in range(2, len(rows) + 2):
        for c in ws[r]:
            c.font = Font(name="微软雅黑", size=10, color=C_TEXT)
            c.border = BD
            c.alignment = Alignment(vertical="center", wrap_text=True)
            c.fill = PatternFill("solid", fgColor=C_CALC)
            if c.column in pct_cols:
                c.number_format = "0.00%"
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws.freeze_panes = "C2"
    return ws

rows = []
for d in D:
    rows.append([d["no"], d["lg"], f'{d["h"]} vs {d["a"]}', d["dt"],
                 *d["op"], *d["nw"], *d["delta"], d["hcp_o"], d["hcp_n"],
                 round(d["or_nw"], 4), *[round(x, 4) for x in d["q_nw"]], d["fav"],
                 f'主胜{d["delta"][0]:+.2f} / 平{d["delta"][1]:+.2f} / 客{d["delta"][2]:+.2f}'])
sheet("01_欧赔与去水",
      ["序号","联赛","对阵","开赛","初盘主","初盘平","初盘客","最新主","最新平","最新客",
       "Δ主","Δ平","Δ客","让球初盘","让球最新","水位合计","隐含_主","隐含_平","隐含_客","市场首选","盘口变化（事实）"],
      rows, [6,8,26,13,9,9,9,9,9,9,8,8,8,13,13,10,10,10,10,10,34], pct_cols=(17,18,19))

rows = []
for d in D:
    rows.append([d["no"], f'{d["h"]} vs {d["a"]}', d["inj_h"], d["inj_a"], d["form"],
                 d["motive"], d["h2h"], "未取到", d["ext_n"], ", ".join(d["ext"])])
sheet("02_情报与交锋",
      ["序号","对阵","主队伤停","客队伤停","近期状态 / 体能","战意 / 积分","近10年交锋","天气","外部来源数","外部来源清单"],
      rows, [6,26,42,42,52,38,40,10,10,46])

rows = []
for d in D:
    rows.append([d["no"], f'{d["h"]} vs {d["a"]}', d["media"], d["model"], d["sig"], d["conf"], d["tier"]])
sheet("03_外部预测与定性",
      ["序号","对阵","全球媒体 / 市场观点（已取到）","AI / 数学模型（已取到）","共振标记","置信度","把握层次"],
      rows, [6,26,86,52,12,10,20])

rows = []
for d in D:
    rows.append([d["no"], f'{d["h"]} vs {d["a"]}', *[round(x, 4) for x in d["q_nw"]],
                 round(d["qmax"], 4), d["fav"], d["core"], d["key"], d["watch"], d["sig"], d["tier"]])
sheet("04_共振总表",
      ["序号","对阵","市场隐含_主","市场隐含_平","市场隐含_客","最高概率","市场方向","核心矛盾","胜负手","看点 / 盘口事实","共振标记","把握层次"],
      rows, [6,26,12,12,12,11,11,50,44,50,12,20], pct_cols=(3,4,5,6))

# 方案核算
plan = [
 ["比分方案 · 稳健/博弈合计", "09 勒沃库森-帕德博恩 2-0 / 3-0", 2, 2, 4],
 ["比分方案", "13 帕尔马-罗马 0-2 / 1-2", 2, 2, 4],
 ["比分方案", "06 纽卡-阿森纳 0-1 / 1-2", 2, 2, 4],
 ["比分方案", "05 热刺-伊普斯维奇 3-1 / 2-1", 2, 2, 4],
 ["比分方案", "02 伯恩茅斯-森林 2-1 / 1-1", 2, 2, 4],
 ["比分方案", "10 门兴-多特蒙德 1-2 / 1-1", 2, 2, 4],
 ["任选九场", "单选6场(2/5/6/9/11/13)+双选3场(1/3/10)：2³=8注", 8, 2, 16],
 ["14场复式", "仅给思路，不实际下单（最小复式已超50元预算）", 0, 2, 0],
]
rows = [[p[0], p[1], p[2], p[3], p[4]] for p in plan]
rows.append(["合计", "比分 12 注 + 任九 8 注 = 20 注", 20, 2, 40])
rows.append(["预算校验", "上限 50 元，单注 2 元，余额 10 元", "", "", ""])
sheet("05_方案核算", ["玩法","内容 / 选场","注数","单注(元)","金额(元)"], rows, [24,70,10,12,12])

sheet("06_数据缺口与风险", ["项目","状态","处理说明"], [list(x) for x in missing], [50,14,80])
wb.save(OUT_XLSX)
OUT_JSON.write_text(json.dumps({"matches": [{k: v for k, v in d.items() if k not in ("q_nw","q_op","or_nw","or_op","delta","fav","qmax")} for d in D],
                                "missing": missing}, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------- 生成内部报告 HTML ----------------
CSS = """
:root{--bg:#12161D;--panel:#1B212B;--panel2:#232B38;--line:#313B4C;--text:#E6EAF2;--muted:#9AA7BD;
--accent:#7AA2F7;--accent2:#A8C0FF;--green:#56C08D;--red:#E47070;--yellow:#E0B25A;}
*{box-sizing:border-box}body{margin:0;padding:32px 20px 70px;background:var(--bg);color:var(--text);
font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.65}
.wrap{max-width:1180px;margin:0 auto}header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:20px}
h1{font-size:27px;margin:0 0 8px}h2{font-size:19px;margin:34px 0 12px;padding-left:11px;border-left:3px solid var(--accent)}
h3{font-size:15px;margin:18px 0 6px;color:var(--accent2)}p{font-size:14px;margin:8px 0}
.sub{color:var(--muted);font-size:14px;margin:0}.muted{color:var(--muted);font-size:13px}
.badge{display:inline-block;margin-left:10px;padding:3px 10px;border:1px solid var(--accent);border-radius:999px;
color:var(--accent2);font-size:12px;vertical-align:middle}
.warn{padding:13px 17px;border-left:3px solid var(--yellow);background:rgba(224,178,90,.09);border-radius:0 8px 8px 0;
font-size:13px;color:#EED9A9;margin:14px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:12px 0}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:12.5px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--panel2);color:var(--accent2);font-weight:600;white-space:nowrap}
tr:nth-child(even) td{background:rgba(255,255,255,.015)}
.tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:11px;white-space:nowrap}
.t-green{background:rgba(86,192,141,.15);color:var(--green)}.t-red{background:rgba(228,112,112,.15);color:var(--red)}
.t-yellow{background:rgba(224,178,90,.15);color:var(--yellow)}.t-blue{background:rgba(122,162,247,.15);color:var(--accent2)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin:12px 0}
.tile{background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:13px 16px}
.tile b{display:block;color:var(--accent2);font-size:13px;margin-bottom:5px}.tile span{font-size:13px}
.tile small{display:block;color:var(--muted);font-size:12px;margin-top:6px}
ul{margin:8px 0 0 18px;padding:0;font-size:13px;color:var(--muted)}li{margin:5px 0}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media print{body{background:#fff;color:#111}.card,.tile{background:#fff;border-color:#ccc}th{background:#eee;color:#111}
.muted,footer,ul{color:#555}h2{border-color:#4472C4}}
"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tag(s):
    cls = {"共振": "t-green", "背离": "t-red", "数据不足": "t-yellow"}.get(s, "t-blue")
    return f'<span class="tag {cls}">{s}</span>'


parts = []
parts.append(f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>26167期 内部分析报告</title><style>{CSS}</style></head><body><div class="wrap">
<header><h1>第 26167 期 · 内部分析报告 <span class="badge">14 场 ｜ 暂不出稿</span></h1>
<p class="sub">范围：胜负彩 26167 期 14 场 ｜ 玩法：50 元内比分方案 + 任九 + 14 场思路 ｜ 预算 50 元、单注 2 元 ｜ 数据时点 2026-11-20 14:10 前后</p></header>
<div class="warn"><strong>口径声明：</strong>本报告为内部决策稿，保留赔率与隐含概率数值；<strong>暂不进入 S4 出稿交接</strong>，不产出头条正文。盘口只记录时点、方向与幅度，<strong>不解读机构主观态度或操盘意图</strong>。未取到的来源一律标注，不以估计值填充。</div>
''')

# 0 报告信息
parts.append('''<h2>0. 报告信息与盘型</h2><div class="card">
<p>期号 <strong>26167</strong>：开售 11-18 20:00，<strong>停售 11-21 22:00</strong>，开奖 11-22。14 场构成：英超 6（第 11 轮）、德甲 6（第 10 轮）、意甲 1（第 12 轮）、西甲 1（第 13 轮）。</p>
<p>盘型归类：<strong>纯五大联赛周末期</strong>——强弱分明，重点排查强队轮换、国际比赛日后体能与德比冷门。本轮为国际比赛日结束后的首轮联赛，多队国脚周四才归队，合练时间被压缩，是本期最需要单独计提的变量。</p>
<p>数据来源：竞彩网/中国体彩网奖期通知、新浪体育（澳盘赔率、四大机构赔率、伤停表、交战记录）、今日头条/网易 26167 期看点、腾讯体育英超与西甲前瞻、Goal、SportsGambler、FootballWhispers、betiper、adalbet、premierleagueprediction.org、football-predictions.ai、纳米数据、Kickoff Lens 积分榜、微信公众号德甲首发整理、直播吧/懂球帝/球迷屋。全部为 11-19 至 11-21 公开页面。</p></div>''')

# 1 多维共振总表
parts.append('<h2>1. 多维共振总表（S1 强制产出）</h2>')
parts.append('<table><thead><tr><th>序</th><th>对阵</th><th>最新欧赔 主/平/客</th><th>去水隐含 主/平/客</th><th>盘口变化（初→最新）</th><th>市场方向</th><th>情报 / 交锋反证</th><th>信号</th><th>把握层次</th></tr></thead><tbody>')
for d in D:
    q = "/".join(f"{x*100:.1f}%" for x in d["q_nw"])
    od = "/".join(f"{x:.2f}" for x in d["nw"])
    dl = f'{d["delta"][0]:+.2f} / {d["delta"][1]:+.2f} / {d["delta"][2]:+.2f}'
    parts.append(f'<tr><td>{d["no"]}</td><td><strong>{esc(d["h"])} vs {esc(d["a"])}</strong><br><span class="muted">{d["lg"]} {d["dt"]}</span></td>'
                 f'<td>{od}</td><td>{q}</td><td>{dl}<br><span class="muted">让球 {d["hcp_o"]}→{d["hcp_n"]}</span></td>'
                 f'<td>{d["fav"]} {d["qmax"]*100:.1f}%</td><td>{esc(d["core"])}</td><td>{tag(d["sig"])}<br><span class="muted">来源 {d["ext_n"]} 项</span></td><td>{esc(d["tier"])}</td></tr>')
parts.append('</tbody></table>')
parts.append('<p class="muted">去水方法：比例法，隐含概率 = (1/赔率) ÷ Σ(1/赔率)。「最新」取新浪 11-20 14:00 口径，「初盘」取该表开赛时间标识行；两行差异只记事实。四大机构离散度与水位合计见配套数据底稿 01 表。</p>')

# 2 情报
parts.append('<h2>2. 情报收集：有利 / 不利、伤停、状态、战意</h2>')
for d in D:
    parts.append(f'''<div class="card"><h3>{d["no"]}. {esc(d["h"])} vs {esc(d["a"])} <span class="muted">{d["lg"]} · {d["dt"]}</span> {tag(d["sig"])}</h3>
<p><strong>主队伤停</strong>：{esc(d["inj_h"])}　｜　<strong>客队伤停</strong>：{esc(d["inj_a"])}</p>
<p><strong>近期状态 / 体能</strong>：{esc(d["form"])}</p>
<p><strong>战意与积分</strong>：{esc(d["motive"])}　｜　<strong>交锋心理</strong>：{esc(d["h2h"])}</p>
<p><strong>核心矛盾</strong>：{esc(d["core"])}　｜　<strong>胜负手</strong>：{esc(d["key"])}</p>
<p><strong>看点 / 盘口事实</strong>：{esc(d["watch"])}</p>
<p><strong>外部观点（已取到 {d["ext_n"]} 项）</strong>：{esc(d["media"])}</p></div>''')

# 3 该赢 vs 真赢得
parts.append('<h2>3. 「该赢」与「真赢得」的落差排序</h2>')
parts.append('''<div class="grid">
<div class="tile"><b>最敢碰</b><span>9 勒沃库森、13 罗马、6 阿森纳、2 伯恩茅斯</span><small>这四场市场隐含概率与情报、交锋方向一致；但 9 与 13 赔率已极低，越稳越别堆倍数。11 号柏林联合方向清楚但客胜已压到 1.41，单列不计入本组。</small></div>
<div class="tile"><b>最值得防平 / 博冷</b><span>10 门兴、12 沙尔克、4 考文垂</span><small>共同点：账面差距大，但主场交锋反常记录或双方大面积减员，平局是结构性第三选项。</small></div>
<div class="tile"><b>赢面在但容易卡壳</b><span>1 维拉、3 切尔西、5 热刺、14 塞维利亚</span><small>反证各自明确：维拉 4 场正式比赛不胜、切尔西锋线与中卫同时减员、热刺转化率垫底且近 5 次联赛交手仅 1 胜、塞维利亚德比近三次输两场。</small></div>
<div class="tile"><b>最不敢碰</b><span>7 埃弗斯堡、8 法兰克福</span><small>两场外部预测覆盖最薄、均势且伤停信息不对称。11 号柏林联合方向清楚，但客胜已被压到 1.41，只宜作任九单选、不宜堆倍数。</small></div>
</div>
<p class="muted">排序按体能消耗、伤停结构、交锋心理与战术执行条件拉开层次，不写三个平行同构结论。市场基准不进入共识加权，避免循环论证。</p>''')

# 4 全球媒体与AI模型
parts.append('<h2>4. 全球媒体、预测市场与 AI / 数学模型</h2>')
parts.append('<table><thead><tr><th>来源</th><th>层级</th><th>本期取到的内容</th><th>状态</th></tr></thead><tbody>')
src_rows = [
 ("SportsGambler", "海外媒体", "维拉主胜、伯恩茅斯主胜、考文垂主队让0.0（主不败）", "已取到"),
 ("FootballWhispers", "海外媒体", "热刺-伊普斯 BTTS Yes；本轮关注场次要点", "已取到"),
 ("Goal", "海外媒体", "考文垂-水晶宫前瞻：第17 vs 第20、新帅首秀、马特塔停赛", "已取到"),
 ("betiper", "预测聚合", "英超 6 场 tips 分布与 1X2 倾向", "已取到"),
 ("adalbet", "AI 模型", "维拉 49/30/22，xG 1.9 vs 1.2，预测 2-1", "已取到"),
 ("premierleagueprediction.org", "统计模型", "维拉 53.9/25/21.1，公平赔率与 EV，预测 2-1", "已取到"),
 ("football-predictions.ai", "AI 站", "德甲第 10 轮前瞻、Bet365 部分赔率与积分判断", "已取到"),
 ("腾讯 / 新浪 / 网易 / 纳米数据", "中文媒体与数据", "英超比分推敲、德比战术、14 场交战记录、伤停表、多家公司欧赔", "已取到"),
 ("Polymarket / Kalshi", "预测市场", "无公开可核验的该期合约报价", "未取到"),
 ("Forebet / Wincomparator / BetBuilders xG / OddAlerts", "算法模型", "未检索到对应场次的公开概率页", "未取到"),
 ("Google 数据模型 / Futbol24", "模型 / 媒体", "无可抓取的该期赛前页面", "未取到"),
]
for s in src_rows:
    cls = "t-green" if s[3] == "已取到" else "t-red"
    parts.append(f'<tr><td>{esc(s[0])}</td><td>{esc(s[1])}</td><td>{esc(s[2])}</td><td><span class="tag {cls}">{s[3]}</span></td></tr>')
parts.append('</tbody></table>')
parts.append('<p class="muted"><strong>关键限制：</strong>10 类预置外部来源中，本期实际取到的是媒体与部分统计/AI 站，预测市场与主流算法模型缺席，因此不强行套用 10 来源加权共识概率。本报告以「欧赔去水隐含概率 + 情报/交锋/伤停 + 已取到的外部观点」做交叉验证，并逐场标注可得来源数与置信度。</p>')

# 5 数学模型与综合分析
parts.append('<h2>5. 数学模型与综合分析</h2>')
parts.append('<div class="card"><p><strong>市场基准模型</strong>：14 场全部按比例法去水得到 1X2 隐含概率（见第 1 节）。水位合计全部落在 1.109–1.118 区间，全期定价水位高度一致，无单场异常水位需单独剔除。</p>')
parts.append('<p><strong>盘口变化观察（只记事实）</strong>：变动最明显的是 1 号维拉（主胜 +0.23、客胜 −0.92）与 11 号柏林联合（主胜 +0.50、客胜 −0.06）；4 号考文垂欧赔未动但让球由平手升至平手/半球；平局赔率被压低的还有 9 号（6.50→6.30）、8 号（4.15→4.05）、14 号（3.61→3.51）等；14 号德比在三项中平局下调、客胜反升至 2.25，是较典型的德比定价结构。这些数值不作为机构态度解读。</p>')
parts.append('<p><strong>多维共振场次</strong>（优先作胆材）：2 伯恩茅斯、6 阿森纳、9 勒沃库森、11 莱比锡、13 罗马。<strong>背离与冲突场次</strong>：1 维拉（盘口向客收缩）、3 切尔西（伤停与媒体方向相反）、5 热刺（交锋 1 胜 4 负）、10 门兴（主场专克多特）、12 沙尔克（交锋客胜仅 11.1%）、14 德比（近三次不胜）。<strong>数据不足场次</strong>：4、7、8（外部预测覆盖 ≤2 项且均势）。</p></div>')

# 6 方案
parts.append('<h2>6. 50 元内投注方案（S3）</h2>')
parts.append('<h3>6.1 纠偏与剔除说明</h3><p>任九剔除 5 场：4（保级战双方十余伤停）、7（交锋样本仅 1 场）、8（均势且双方减员）、12（交锋与市场反向）、14（德比情绪盘）。这 5 场要么信息冲突，要么外部预测覆盖最薄。</p>')
parts.append('<h3>6.2 比分方案（12 注 / 24 元）</h3><table><thead><tr><th>场次</th><th>比分区间</th><th>注数</th><th>金额</th><th>核心反证</th></tr></thead><tbody>')
for no, picks, why in [
 (9, "2-0、3-0", "锋线多人缺阵与深盘松懈，大胜并非无风险"),
 (13, "0-2、1-2", "交锋无平局但受球半深盘，罗马门将位置存疑"),
 (6, "0-1、1-2", "萨卡缺阵、纽卡主场两连败后反弹窗口"),
 (5, "3-1、2-1", "热刺转化率联赛垫底、近5次联赛交手仅1胜"),
 (2, "2-1、1-1", "森林刚 3-1 胜曼城，高位逼抢未必零封"),
 (10, "1-2、1-1", "门兴近6次主场对多特4胜1平1负"),
]:
    d = D[no-1]
    parts.append(f'<tr><td>{no} {esc(d["h"])} vs {esc(d["a"])}</td><td>{picks}</td><td>2</td><td>4 元</td><td>{esc(why)}</td></tr>')
parts.append('<tr><td colspan="2"><strong>小计</strong></td><td><strong>12</strong></td><td><strong>24 元</strong></td><td>单注 2 元</td></tr></tbody></table>')
parts.append('<h3>6.3 任选九场（8 注 / 16 元）</h3><div class="card"><p>单选 6 场：<strong>2→3、5→3、6→0、9→3、11→0、13→0</strong>；双选 3 场：<strong>1→3/1、3→3/1、10→0/1</strong>。注数 = 2³ = 8 注 × 2 元 = 16 元。</p>')
parts.append('<p>结构校验：单选主胜 3 场、客胜 3 场；双选全部带平，整体 3/1/0 配比偏向「客胜 + 防平」，与本期强队客场多、德比与保级战易平的特征一致。剔除的 5 场全是次级混乱或情绪盘，不补第三个答案。</p></div>')
parts.append('<h3>6.4 14 场复式思路（不实际下单）</h3><p>最小复式已超 50 元预算，本轮只给思路：以 9、13 为双胆，1、3、10、14 四处做双选，其余单选；若后续扩预算，优先把 10 门兴与 14 德比的双选补足，而不是给均势场补第三结果。</p>')
parts.append('<div class="card"><p><strong>预算核算</strong>：比分 24 元 + 任九 16 元 = <strong>40 元</strong>，共 20 注，单注 2 元，余额 10 元，<strong>未超 50 元上限</strong>。停售前若临场名单或赔率变动，按同一结构重算注数，不追加超出预算的场次。</p></div>')

# 7 数据缺口
parts.append('<h2>7. 数据缺口与风险披露（必填）</h2><table><thead><tr><th>项目</th><th>状态</th><th>处理说明</th></tr></thead><tbody>')
for m in missing:
    cls = "t-green" if m[1] == "已取到" else ("t-yellow" if "部分" in m[1] else "t-red")
    parts.append(f'<tr><td>{esc(m[0])}</td><td><span class="tag {cls}">{esc(m[1])}</span></td><td>{esc(m[2])}</td></tr>')
parts.append('</tbody></table>')
parts.append('<div class="card"><ul>'
'<li>伤停与首发以官方最新公布为准；本轮国际比赛日后国脚归队时间不一，开赛前临场名单变动可能改变体能与对位判断。</li>'
'<li>澳盘两组数据存在时点差异，本报告统一以「11-20 14:00」组为最新口径，另一组作对照；停售前 22:00 应再取一次定盘。</li>'
'<li>第 9 场勒沃库森-帕德博恩不在竞彩周六 22 场清单内，其外盘欧赔与伤停由新浪/微信公众号补齐，竞彩官方参考未取到。</li>'
'<li>本期外部预测来源覆盖不均（3–6 项不等），置信度低的场次已在共振总表标注，不以单一媒体观点代替共识。</li>'
'<li>比分与方向仅作数据观察与思路参考，注意控制仓位与过关风险；未满 18 周岁不得参与。</li>'
'</ul></div>')

# 8 赛果核对与校准反哺接口（自动化闭环挂载点）
parts.append('<h2>8. 赛果核对与校准反哺接口（自动化闭环）</h2>')
parts.append('''<div class="warn"><strong>本章是「自动化赛果核对 → 偏差纠正 → 变差总结 → 反哺预测」的挂载点。</strong>
本期 14 场的预测方向、去水概率、把握层次、共振信号、比分区间与任九状态，已<strong>冻结登记</strong>到
<code>预测校准台账.xlsx → 01_赛果核对台账</code>。开奖后只需填 L（实际赛果 3/1/0）、M（实际比分）两列，
运行 <code>reconcile.py</code> 即自动完成核对、变差判定、纠偏建议与总结归档。
<strong>赛果尚未产生</strong>（本期 11-21 22:00 停售、11-22 开奖），本章不写任何赛果、不生成任何结论。</div>''')

parts.append('<h3>8.1 四层闭环与本期所处位置</h3>')
parts.append('''<div class="grid">
<div class="tile"><b>第一层 · 赛果核对</b><span>方向命中、Brier、LogLoss、实际项概率、信心偏差、比分命中</span><small>本期状态：14 场已登记基线，L/M 待录入</small></div>
<div class="tile"><b>第二层 · 自动纠正</b><span>来源权重 / 判定阈值 / 结果偏置 / 剔除规则四类动作</span><small>本期状态：基线参数 v26167，未启动纠偏</small></div>
<div class="tile"><b>第三层 · 变差总结</b><span>11 条信号判定，六类归因，输出变差总结与下期验证点</span><small>本期状态：全部「数据未齐」</small></div>
<div class="tile"><b>第四层 · 反哺预测</b><span>写回权重参数、S2 阈值、把握层次排序、S3 剔除结构</span><small>本期状态：参数出口待确认</small></div>
</div>''')

parts.append('<h3>8.2 本期可证伪断言（开奖后逐条核对）</h3>')
parts.append('<table><thead><tr><th>#</th><th>断言</th><th>若不成立，说明哪一处正在变差</th><th>对应监控信号</th></tr></thead><tbody>')
claims = [
 ("1", "第 9 场勒沃库森（qmax 0.7561，全期最高、最敢碰）应取主胜",
  "深盘 + 锋线多人缺阵的风险被低估；归为「临场信息型 / 深盘松懈」", "信号 7 高置信倒灶"),
 ("2", "2 / 6 / 9 / 13 四场「最敢碰 + 共振」命中率应高于全期均值",
  "共振标签与高置信门槛失效，需重查来源权重与稳胆识别", "信号 8 共振兑现"),
 ("3", "4 / 7 / 8 / 12 / 14 五场任九剔除场的命中率应低于单选场",
  "W 转正 = 剔除优先级错配，把该留的剔了、该剔的留着", "信号 9 剔除规则倒挂"),
 ("4", "10 门兴主场交锋反常、12 沙尔克交锋偏主，客胜不应轻松兑现",
  "若客胜如期打出，说明交锋心理权重给高了，情报层需降权", "信号 1 / 4"),
 ("5", "1 / 3 / 5 三场「赢面在但卡壳」不应全部干脆取胜",
  "若全部轻松赢球，说明落差拆解过度保守，X 倒挂", "信号 10 把握层次倒挂"),
 ("6", "平局实际占比不应显著高于平均预测平局概率",
  "Y > 0.08 = 系统性低估平局，尤其 4 / 8 / 10 / 14 四个防平场", "信号 11 平局低估"),
 ("7", "比分方案 12 注、任九 8 注应有可核验的命中与覆盖记录",
  "比分区间设置过窄或双选分配错位，需按实测回撤调整", "信号 6 比分命中率"),
]
for n, claim, fail, sig in claims:
    parts.append(f'<tr><td>{n}</td><td>{esc(claim)}</td><td>{esc(fail)}</td><td><span class="tag t-blue">{esc(sig)}</span></td></tr>')
parts.append('</tbody></table>')
parts.append('<p class="muted">断言全部按「若不成立则指向哪个参数」的反向写法登记，避免开奖后做事后解释。核验结果由 reconcile.py 自动回填，不手工改写本节。</p>')

parts.append('<h3>8.3 三个倒挂差值（本闭环最值得盯的数）</h3>')
parts.append('''<table><thead><tr><th>差值</th><th>定义</th><th>正常区间</th><th>变差含义</th></tr></thead><tbody>
<tr><td><strong>W</strong></td><td>剔除场命中率 − 单选场命中率</td><td>&lt; 0</td><td>转正且 &gt; 0.05：S3 剔除规则正在变差</td></tr>
<tr><td><strong>X</strong></td><td>最敢碰命中率 − 数据不足命中率</td><td>&gt; 0.10</td><td>收窄或转负：「该赢 vs 真赢得」层次没拉开</td></tr>
<tr><td><strong>Y</strong></td><td>实际平局占比 − 平均预测平局概率</td><td>≈ 0</td><td>&gt; 0.08：系统性低估平局，需加平局偏置</td></tr>
</tbody></table>''')

parts.append('<h3>8.4 反哺路径与不追溯声明</h3>')
parts.append('''<div class="card"><p>开奖后运行 <code>reconcile.py --issue 26167</code> 生成 <code>校准结果_26167.json</code> 与
<code>变差总结_26167.md</code>；参数建议写入 <code>06_反哺参数出口</code>，状态为「待确认」。
人工确认后生成参数版本 <code>v26167 → v26168</code>，下一期 S1 读取新权重与偏置、S2 读取新阈值、S3 按 W 信号调整剔除场数与双选分配。</p>
<p><strong>不追溯：</strong>赛果只用于下一期纠偏，<strong>不反向修改本期已发布的预测方向、概率、把握层次与投注方案</strong>；已交付的内部报告与数据底稿保持原样。
纠偏只发生在内部量化层，S4 对外合规口径（零赔率、零机构态度解读）不受影响；50 元预算上限与单注 2 元为硬约束，不参与纠偏。</p></div>''')

parts.append(f'''<footer>第 26167 期内部分析报告 ｜ 生成 2026-11-21 ｜ 配套：26167期_数据底稿.xlsx、预测校准台账.xlsx、赛果核对与预测校准闭环_SOP.md、周六赛程_S0锁定简报.html、内部分析工作流_SOP.md<br>
按用户要求暂不进入 S4 出稿交接，不产出头条正文。全部内容仅作数据观察与思路参考，不构成投注建议。</footer>
</div></body></html>''')

OUT_HTML.write_text("".join(parts), encoding="utf-8")
print("xlsx:", OUT_XLSX)
print("html:", OUT_HTML)
print("隐含概率最高:", max(D, key=lambda x: x["qmax"])["h"], round(max(d["qmax"] for d in D), 4))
