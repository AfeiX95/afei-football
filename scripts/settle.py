# -*- coding: utf-8 -*-
"""盘口结算引擎（五状态口径）

设计原则（用户 m01262 评审要求）：
- 支持整数盘、半球盘、四分之一球盘；
- 结算结果一律落到五状态：全赢 / 半赢 / 走水 / 半输 / 全输；
- 四分之一球盘 = 两注半仓（line-0.25 与 line+0.25），绝不把「半赢/半输」写成「走水」；
- 盈亏按香港盘水位（HK water，1.00 = 本金等值）计算：
    全赢 +w / 半赢 +w/2 / 走水 0 / 半输 -0.5 / 全输 -1
  香港盘 0.90 等价于欧洲十进制 1.90；如需十进制请调用 hk_to_decimal。

用法：
    from settle import settle_ah, settle_ou, ev_ah, ev_ou, five_state
    state = settle_ah(margin=1, line=-1.25)        # 让 1.25，净胜 1 球 → 半输
    pnl   = state_profit(state, 0.90)              # → -0.5
"""
from __future__ import annotations

FULL_WIN = "全赢"
HALF_WIN = "半赢"
PUSH = "走水"
HALF_LOSS = "半输"
FULL_LOSS = "全输"
STATES = (FULL_WIN, HALF_WIN, PUSH, HALF_LOSS, FULL_LOSS)


def is_quarter(line: float) -> bool:
    """四分之一球盘：小数部分 .25 或 .75"""
    frac = abs(line) % 1
    return abs(frac - 0.25) < 1e-9 or abs(frac - 0.75) < 1e-9


def _base_state(diff: float) -> str:
    """整数/半球盘的单一结算（diff = 让球后的净胜差）"""
    if diff > 1e-9:
        return FULL_WIN
    if diff < -1e-9:
        return FULL_LOSS
    return PUSH


def settle_ah(margin: int, line: float) -> str:
    """亚盘结算（主队视角）。margin = 主队净胜球；line = 主队让球数（主让 1.25 → line=-1.25）。"""
    diff = margin + line
    if not is_quarter(line):
        return _base_state(diff)
    s1 = _base_state(margin + (line - 0.25))
    s2 = _base_state(margin + (line + 0.25))
    pair = {s1, s2}
    if pair == {FULL_WIN}:
        return FULL_WIN
    if pair == {FULL_WIN, PUSH}:
        return HALF_WIN
    if pair == {PUSH}:
        return PUSH
    if pair == {PUSH, FULL_LOSS}:
        return HALF_LOSS
    if pair == {FULL_LOSS}:
        return FULL_LOSS
    raise AssertionError(f"非法四分之一球组合: {s1}/{s2} (margin={margin}, line={line})")


def settle_ou(goals: int, line: float) -> str:
    """大小球结算（大球视角）。"""
    diff = goals - line
    if not is_quarter(line):
        return _base_state(diff)
    s1 = _base_state(goals - (line - 0.25))
    s2 = _base_state(goals - (line + 0.25))
    pair = {s1, s2}
    if pair == {FULL_WIN}:
        return FULL_WIN
    if pair == {FULL_WIN, PUSH}:
        return HALF_WIN
    if pair == {PUSH}:
        return PUSH
    if pair == {PUSH, FULL_LOSS}:
        return HALF_LOSS
    if pair == {FULL_LOSS}:
        return FULL_LOSS
    raise AssertionError(f"非法四分之一球组合: {s1}/{s2} (goals={goals}, line={line})")


def state_profit(state: str, water: float) -> float:
    """以 1 单位本金计的净盈亏（香港盘水位）"""
    if state == FULL_WIN:
        return water
    if state == HALF_WIN:
        return water / 2
    if state == PUSH:
        return 0.0
    if state == HALF_LOSS:
        return -0.5
    if state == FULL_LOSS:
        return -1.0
    raise ValueError(f"未知状态: {state}")


def hk_to_decimal(water: float) -> float:
    return 1.0 + water


def decimal_to_hk(odds: float) -> float:
    return odds - 1.0


def five_state(grid, line: float, kind: str = "ah"):
    """把完整比分概率矩阵折算成五状态概率。

    grid[i][j] = P(主 i 球, 客 j 球)（或任一方的比分矩阵，kind="ou" 时只用 i+j）
    返回 {state: prob}
    """
    out = {s: 0.0 for s in STATES}
    for i, row in enumerate(grid):
        for j, p in enumerate(row):
            if p <= 0:
                continue
            st = settle_ah(i - j, line) if kind == "ah" else settle_ou(i + j, line)
            out[st] += p
    return out


def ev_ah(grid, line: float, water_home: float, water_away: float):
    """亚盘 EV（主/客各 1 单位本金）与五状态分布"""
    dist = five_state(grid, line, "ah")
    ev_h = sum(p * state_profit(s, water_home) for s, p in dist.items())
    # 客队五状态与主队镜像：全赢↔全输，半赢↔半输
    mirror = {FULL_WIN: FULL_LOSS, HALF_WIN: HALF_LOSS, PUSH: PUSH,
              HALF_LOSS: HALF_WIN, FULL_LOSS: FULL_WIN}
    ev_a = sum(p * state_profit(mirror[s], water_away) for s, p in dist.items())
    return ev_h, ev_a, dist


def ev_ou(grid, line: float, water_over: float, water_under: float):
    """大小球 EV（大/小各 1 单位本金）"""
    dist = five_state(grid, line, "ou")
    ev_o = sum(p * state_profit(s, water_over) for s, p in dist.items())
    mirror = {FULL_WIN: FULL_LOSS, HALF_WIN: HALF_LOSS, PUSH: PUSH,
              HALF_LOSS: HALF_WIN, FULL_LOSS: FULL_WIN}
    ev_u = sum(p * state_profit(mirror[s], water_under) for s, p in dist.items())
    return ev_o, ev_u, dist
