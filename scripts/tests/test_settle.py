# -*- coding: utf-8 -*-
"""盘口结算引擎单元测试（python -m unittest discover -s scripts/tests -t .）"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settle import (  # noqa: E402
    FULL_LOSS, FULL_WIN, HALF_LOSS, HALF_WIN, PUSH,
    ev_ah, five_state, is_quarter, settle_ah, settle_ou, state_profit,
)


class TestQuarter(unittest.TestCase):
    def test_is_quarter(self):
        for line in (0.25, -0.25, 0.75, -1.25, 2.75):
            self.assertTrue(is_quarter(line), line)
        for line in (0, -0.5, 1.0, 2.5):
            self.assertFalse(is_quarter(line), line)


class TestAH(unittest.TestCase):
    def test_quarter_125_margin1_is_half_loss(self):
        # 让 1.25、净胜 1 球：让 1 走水 + 让 1.5 输 → 半输（不是整笔走水）
        self.assertEqual(settle_ah(1, -1.25), HALF_LOSS)

    def test_quarter_125_margin2_full_win(self):
        self.assertEqual(settle_ah(2, -1.25), FULL_WIN)

    def test_quarter_125_margin0_full_loss(self):
        self.assertEqual(settle_ah(0, -1.25), FULL_LOSS)

    def test_quarter_075_margin1_half_win(self):
        # 让 0.75、净胜 1 球：让 0.5 赢 + 让 1 赢半 → 半赢
        self.assertEqual(settle_ah(1, -0.75), HALF_WIN)

    def test_quarter_025_margin0_half_loss(self):
        # 让 0.25、打平：平手走水 + 让 0.5 输 → 半输
        self.assertEqual(settle_ah(0, -0.25), HALF_LOSS)

    def test_receive_quarter_margin0_half_win(self):
        # 受让 0.25、打平 → 半赢
        self.assertEqual(settle_ah(0, 0.25), HALF_WIN)

    def test_level_ball_push(self):
        self.assertEqual(settle_ah(0, 0), PUSH)

    def test_integer_line_push(self):
        self.assertEqual(settle_ah(2, -2), PUSH)
        self.assertEqual(settle_ah(1, -2), FULL_LOSS)

    def test_half_ball_never_pushes(self):
        self.assertNotEqual(settle_ah(0, -0.5), PUSH)
        self.assertEqual(settle_ah(1, -0.5), FULL_WIN)


class TestOU(unittest.TestCase):
    def test_275_goals2_full_loss(self):
        # 2.75 = 2.5 + 3.0：两球两注都输 → 全输
        self.assertEqual(settle_ou(2, 2.75), FULL_LOSS)

    def test_275_goals3_half_win(self):
        # 3 球：过 2.5 赢，过 3.0 走水 → 半赢
        self.assertEqual(settle_ou(3, 2.75), HALF_WIN)

    def test_275_goals4_full_win(self):
        self.assertEqual(settle_ou(4, 2.75), FULL_WIN)

    def test_225_goals2_half_loss(self):
        # 2 球：过 2.0 走水，过 2.5 输 → 半输
        self.assertEqual(settle_ou(2, 2.25), HALF_LOSS)

    def test_225_goals3_full_win(self):
        self.assertEqual(settle_ou(3, 2.25), FULL_WIN)

    def test_integer_ou_push(self):
        self.assertEqual(settle_ou(3, 3.0), PUSH)
        self.assertEqual(settle_ou(4, 3.0), FULL_WIN)

    def test_half_ou(self):
        self.assertEqual(settle_ou(3, 2.5), FULL_WIN)
        self.assertEqual(settle_ou(2, 2.5), FULL_LOSS)


class TestProfit(unittest.TestCase):
    def test_profit_values(self):
        self.assertAlmostEqual(state_profit(FULL_WIN, 0.90), 0.90)
        self.assertAlmostEqual(state_profit(HALF_WIN, 0.90), 0.45)
        self.assertAlmostEqual(state_profit(PUSH, 0.90), 0.0)
        self.assertAlmostEqual(state_profit(HALF_LOSS, 0.90), -0.5)
        self.assertAlmostEqual(state_profit(FULL_LOSS, 0.90), -1.0)


class TestEVConsistency(unittest.TestCase):
    def setUp(self):
        lh = la = 1.3
        g = [[math.exp(-lh) * lh ** i / math.factorial(i) * math.exp(-la) * la ** j / math.factorial(j)
              for j in range(8)] for i in range(8)]
        s = sum(sum(r) for r in g)
        self.grid = [[x / s for x in r] for r in g]

    def test_both_sides_negative_with_vig(self):
        ev_h, ev_a, _ = ev_ah(self.grid, 0.0, 0.90, 0.90)
        self.assertLess(ev_h, 0.0)
        self.assertLess(ev_a, 0.0)

    def test_quarter_ev_equals_half_stake_average(self):
        """让 0.75 的 EV 必须等于 让 0.5 与 让 1.0 各半仓之和"""
        p075 = sum(p * state_profit(s, 0.90) for s, p in five_state(self.grid, -0.75, "ah").items())
        p05 = sum(p * state_profit(s, 0.90) for s, p in five_state(self.grid, -0.5, "ah").items())
        p10 = sum(p * state_profit(s, 0.90) for s, p in five_state(self.grid, -1.0, "ah").items())
        self.assertAlmostEqual(p075, 0.5 * p05 + 0.5 * p10, places=9)

    def test_five_state_sums_to_one(self):
        d = five_state(self.grid, -0.25, "ah")
        self.assertAlmostEqual(sum(d.values()), 1.0, places=9)

    def test_ou_push_case(self):
        d = five_state(self.grid, 3.0, "ou")
        self.assertGreater(d[PUSH], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
