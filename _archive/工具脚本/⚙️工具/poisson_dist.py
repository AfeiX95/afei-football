import math

def poisson_prob(k, lam):
    return (lam**k) * math.exp(-lam) / math.factorial(k)

# TPS vs 坦山猫
lh, la = 1.528, 1.243
print("=== TPS图尔 vs 坦山猫 — 泊松比分分布 ===")
print("lambda_home=1.528, lambda_away=1.243")
print()
all_scores = []
for h in range(6):
    for a in range(6):
        p = poisson_prob(h, lh) * poisson_prob(a, la)
        all_scores.append(((h,a), p))
all_scores.sort(key=lambda x:-x[1])
print(" 比分     概率     累计")
cumul = 0.0
for (h,a), p in all_scores[:12]:
    cumul += p*100
    print(f"  {h}-{a}     {p*100:6.2f}%   {cumul:5.1f}%")
home_win = sum(p for (h,a),p in all_scores if h>a)
draw = sum(p for (h,a),p in all_scores if h==a)
away_win = sum(p for (h,a),p in all_scores if h<a)
print(f"\n主胜: {home_win*100:.1f}%  平局: {draw*100:.1f}%  客胜: {away_win*100:.1f}%")

print()
print("=== 玛丽港 vs 拉赫蒂 — 泊松比分分布 ===")
lh, la = 1.240, 1.499
print("lambda_home=1.240, lambda_away=1.499")
print()
all_scores = []
for h in range(6):
    for a in range(6):
        p = poisson_prob(h, lh) * poisson_prob(a, la)
        all_scores.append(((h,a), p))
all_scores.sort(key=lambda x:-x[1])
print(" 比分     概率     累计")
cumul = 0.0
for (h,a), p in all_scores[:10]:
    cumul += p*100
    print(f"  {h}-{a}     {p*100:6.2f}%   {cumul:5.1f}%")
home_win = sum(p for (h,a),p in all_scores if h>a)
draw = sum(p for (h,a),p in all_scores if h==a)
away_win = sum(p for (h,a),p in all_scores if h<a)
print(f"\n主胜: {home_win*100:.1f}%  平局: {draw*100:.1f}%  客胜: {away_win*100:.1f}%")
