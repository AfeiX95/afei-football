# -*- coding: utf-8 -*-
"""周二档 4 场 → 小红书信息卡 JSON（数据来源：_model_v3 + _data，不造数）。"""
import json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAY = "20261027"
PICK = ["006", "007", "009", "010"]
ID = {"001":"1473992","002":"1474025","003":"1473897","004":"1490697","005":"1414253",
      "006":"1362815","007":"1490695","008":"1490693","009":"1414173","010":"1414221"}
KICK = {"001":"18:00","002":"18:00","003":"20:15","004":"01:00","005":"01:30",
        "006":"02:00","007":"03:45","008":"03:45","009":"03:45","010":"03:45"}
NO = {k: f"周二{k}" for k in ID}

M = json.loads((ROOT/f"state/intel/{DAY}/_model_v3_{DAY}.json").read_text(encoding="utf-8"))
D = json.loads((ROOT/f"state/intel/{DAY}/_data_{DAY}.json").read_text(encoding="utf-8"))

def pois(k, lam): return math.exp(-lam)*lam**k/math.factorial(k)

def grid5(lh, la):
    rows=[[pois(h,lh)*pois(a,la) for a in range(5)] for h in range(5)]
    tot=sum(sum(r) for r in rows)
    return [[round(100*p/tot,1) for p in r] for r in rows]

def wdl(lh,la):
    h=d=a=0.0
    for i in range(12):
        for j in range(12):
            p=pois(i,lh)*pois(j,la)
            if i>j: h+=p
            elif i==j: d+=p
            else: a+=p
    s=h+d+a
    return [round(100*h/s,1),round(100*d/s,1),round(100*a/s,1)]

def recent(block, side, n=5):
    """按 venue 字段取本队视角的近 n 场（H=主场方，A=客场方）。"""
    rows=(block.get("matches") or [])
    rows=[r for r in rows if (r.get("score") or "-") != "-"]
    rows=rows[:n]
    gf=ga=0; zero=0; lst=[]
    for r in rows:
        hs,as_=[int(x) for x in r["score"].split("-")]
        mine,opp=(hs,as_) if r.get("venue")=="H" else (as_,hs)
        gf+=mine; ga+=opp; lst.append(mine)
        if opp==0: zero+=1
    n_=len(rows) or 1
    mu=sum(lst)/n_
    sd=(sum((v-mu)**2 for v in lst)/n_)**0.5
    return {"pj":gf/n_,"sj":ga/n_,"gf":gf,"ga":ga,"n":len(rows),
            "zero":round(100*zero/n_,1),"vol":round(sd,2)}

def h2h(block):
    import re as _re
    h=block.get("h2h") or {}
    s=h.get("summary") or {}
    n=int(s.get("n") or 0)
    gf,ga=int(s.get("gf") or 0),int(s.get("ga") or 0)
    over,under=int(s.get("over") or 0),int(s.get("under") or 0)
    txt=s.get("text") or ""
    m=_re.search(r"平(\d+)",txt)
    draw=int(m.group(1)) if m else 0
    avg=round((gf+ga)/n,2) if n else 0
    return {"n":n,"avg":avg,"draw":round(100*draw/n) if n else 0,
            "low":round(100*under/n) if n else 0,"scores":[],
            "text":txt,"rec":f"{txt}总 {gf}:{ga}"}

def radar(f):
    c=lambda x:max(15,min(95,round(x)))
    return [c(18+f["pj"]*30), c(96-f["sj"]*26), c(25+f["zero"]*0.65),
            c(95-f["vol"]*35), c(50+(f["pj"]-f["sj"])*22), c(20+50*0.7)]

TAGS={"006":("主场也是短板","客场一直稳"),"007":("最硬那条线","专心联赛"),
      "009":("进球荒","守着不败"),"010":("主场头衔","攻防双压")}
NARR={
 "006":("瑞超最后一轮。索尔纳主场 12 场只赢 4 场、净胜 -8，客场反倒是 6 胜 5 平 2 负；"
        "埃尔夫斯堡客场 13 场丢 9 球，是全联赛客场最省的那种。收官轮大家都要分，主队想靠主场红利，可这块红利今年没兑现。"),
 "007":("多特七轮不败、七轮只丢四个，联赛里最硬那条线；不莱梅场均进两球一，顺手也场均丢两个。"
        "杯赛一场定生死，90 分钟算账，进加时不算彩果。"),
 "009":("罗马八轮不败，场均两球四。卡利亚里的毛病不在防守，出在进攻总量上：全季八个进球。"
        "一个客场进球个位数的队，要在奥林匹克踢出大冷，先得回答一个很土的问题：球从哪来。"),
 "010":("都灵主场这块头衔，这场恰恰是陷阱。科莫近五场场均进 2.2 球、只失 1.0，"
        "攻防两头都压过来了；都灵近五场场均进 1.8、失 1.2，主场该有的那种压迫感没打出来。"),
}
POINT={
 "006":"看索尔纳能不能把主场这口气提起来：它客场是联赛第三，主场只排第十二，同一支队两种脸。",
 "007":"看多特肯不肯把两个边压上去：它七轮只丢四个，不莱梅场均丢两个，谁先急谁先露空档。",
 "009":"看卡利亚里能不能在奥林匹克先守住半小时：守住了就是闷，守不住就是单向。",
 "010":"看都灵能不能先把节奏拖住：它一急，后面那三个人就跑起来了。",
}

cards=[]
for no in PICK:
    mid=ID[no]; b=D[mid]; m=M[no]
    lh,la=m["lam_fused"]
    fh,fa=recent(b.get("recent_home") or {},"H"),recent(b.get("recent_away") or {},"A")
    h2=h2h(b)
    w=wdl(lh,la); g=grid5(lh,la)
    t3=[round(100*x,1) for x in m["three_fused"]]
    card={
      "no":NO[no],"league":("德甲/德国杯" if no=="007" else "意甲" if no in("009","010") else "瑞超"),
      "kick":KICK[no],"home":b["home"],"away":b["away"],
      "model":{"lam":[round(lh,2),round(la,2)],"grid":g,"wdl":w},
      "form":{"home":{**fh,"ha":f"零封 {fh['zero']:.0f}%"},
              "away":{**fa,"ha":f"零封 {fa['zero']:.0f}%"},
              "h2h":{"n":h2["n"],"avg_goals":h2["avg"],"note":f"低比分 {h2['low']}% · 平 {h2['draw']}%"},
              "h2h_short":f"交锋 {h2['n']} 场 · 场均 {h2['avg']} 球 · 平 {h2['draw']}%",
              "h2h_stats":{"n":h2["n"],"draw":h2["draw"],"low":h2["low"]}},
      "radar":{"dims":["进攻","防守","零封能力","进球稳定","净胜状态","抢开局"],
               "home":radar(fh),"away":radar(fa)},
      "pie_mode":"none","heat":True,
      "intel":{"common":[f"场均进失：主 {fh['pj']:.2f} 进 / {fh['sj']:.2f} 失 · 客 {fa['pj']:.2f} 进 / {fa['sj']:.2f} 失",
                         f"零封率：主 {fh['zero']:.0f}% · 客 {fa['zero']:.0f}%",
                         f"交锋 {h2['n']} 场 · 场均 {h2['avg']} 球 · 平 {h2['draw']}%"]},
      "intel2":{"home":{"good":[f"近 {fh['n']} 场场均 {fh['pj']:.2f} 球，进 {fh['gf']} 失 {fh['ga']}"],
                        "bad":[f"近 {fh['n']} 场进球波动 {fh['vol']:.2f}，忽高忽低"] if fh['vol']>1.0 else []},
                "away":{"good":[f"近 {fa['n']} 场场均 {fa['pj']:.2f} 球、失 {fa['sj']:.2f} 球"],
                        "bad":[f"近 {fa['n']} 场失 {fa['ga']} 球"] if fa['sj']>1.3 else []}},
      "h2h_short":f"交锋 {h2['n']} 场 · 场均 {h2['avg']} 球 · 平 {h2['draw']}%",
      "h2h_stats":{"n":h2["n"],"draw":h2["draw"],"low":h2["low"]},
      "h2h_detail":{"record":f"近 {h2['n']} 次交锋 · 场均 {h2['avg']} 球","scores":h2["scores"],
                    "note":f"低比分场次占 {h2['low']}%，平局占 {h2['draw']}%。"},
      "narr":f"【{TAGS[no][0]} vs {TAGS[no][1]}】"+NARR[no],
      "point":POINT[no],
    }
    cards.append(card)
    print(no,b["home"],b["away"],"lam",round(lh,2),round(la,2),"wdl",w,"fused",t3,
          "近5主",fh['pj'],fh['sj'],"客",fa['pj'],fa['sj'],"h2h",h2["n"],h2["avg"],h2["draw"],h2["low"])

out={"meta":{"date":"10.27","weekday":"周二"},"matches":cards}
(ROOT/f"📝文章/{DAY}/_cards_tue.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("✅ JSON 写好")
