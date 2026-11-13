import unittest

from backtest import validate_plan, simulate_trade, PIP_SIZE, calculate_net_pips


def candle(open_, high, low, close):
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


class TestValidatePlan(unittest.TestCase):
    def test_valid_long(self):
        self.assertEqual(
            validate_plan("long", 1.1000, 1.0980, 1.1030)[0],
            True,
        )

    def test_valid_short(self):
        self.assertEqual(
            validate_plan("short", 1.1000, 1.1020, 1.0970)[0],
            True,
        )

    def test_long_stop_wrong_side(self):
        self.assertFalse(
            validate_plan("long", 1.1000, 1.1000, 1.1040)[0]
        )

    def test_short_take_wrong_side(self):
        self.assertFalse(
            validate_plan("short", 1.1000, 1.1020, 1.1000)[0]
        )

    def test_rr_below_minimum(self):
        ok, message = validate_plan(
            "long", 1.1000, 1.0990, 1.1010
        )
        self.assertFalse(ok)
        self.assertIn("R:R", message)

    def test_unknown_direction(self):
        self.assertFalse(
            validate_plan("wait", 1.1000, 1.0990, 1.1020)[0]
        )


class TestSimulateTrade(unittest.TestCase):
    def test_long_take_profit(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1030, 1.0995, 1.1020),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020
        )
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["exit_reason"], "take")
        self.assertAlmostEqual(result["pips"], 20.0)

    def test_short_take_profit(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1005, 1.0970, 1.0980),
        ]
        result = simulate_trade(
            candles, 0, "short", 1.1000, 1.1020, 1.0980
        )
        self.assertEqual(result["result"], "win")
        self.assertAlmostEqual(result["pips"], 20.0)

    def test_long_stop_loss(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1010, 1.0970, 1.0990),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1040
        )
        self.assertEqual(result["result"], "loss")
        self.assertEqual(result["exit_reason"], "stop")
        self.assertAlmostEqual(result["pips"], -20.0)

    def test_gap_through_long_stop(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.0960, 1.0970, 1.0950, 1.0965),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1040
        )
        self.assertEqual(result["result"], "loss")
        self.assertAlmostEqual(result["exit"], 1.0960)
        self.assertAlmostEqual(result["pips"], -40.0)

    def test_stop_wins_when_both_levels_hit(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1030, 1.0970, 1.1000),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020
        )
        self.assertEqual(result["result"], "loss")
        self.assertEqual(result["exit_reason"], "stop")

    def test_gap_through_short_stop(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1050, 1.1060, 1.1040, 1.1055),
        ]
        result = simulate_trade(
            candles, 0, "short", 1.1000, 1.1020, 1.0960
        )
        self.assertEqual(result["result"], "loss")
        self.assertAlmostEqual(result["exit"], 1.1050)
        self.assertAlmostEqual(result["pips"], -50.0)

    def test_negative_timeout(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1005, 1.0985, 1.0990),
            candle(1.0990, 1.0995, 1.0975, 1.0980),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0970, 1.1040,
            max_hold=2,
        )
        self.assertEqual(result["result"], "timeout")
        self.assertAlmostEqual(result["pips"], -20.0)

    def test_custom_pip_size(self):
        candles = [
            candle(150.00, 150.10, 149.90, 150.00),
            candle(150.00, 150.10, 149.85, 149.90),
        ]
        result = simulate_trade(
            candles, 0, "long", 150.00, 149.80, 150.40,
            max_hold=1, pip_size=0.01,
        )
        self.assertEqual(result["result"], "timeout")
        self.assertAlmostEqual(result["pips"], -10.0)

    def test_timeout(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1000),
            candle(1.1000, 1.1010, 1.0990, 1.1005),
            candle(1.1005, 1.1010, 1.0995, 1.1002),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1040,
            max_hold=2,
        )
        self.assertEqual(result["result"], "timeout")
        self.assertEqual(result["bars_held"], 2)
        self.assertAlmostEqual(result["pips"], 2.0)

    def test_entry_candle_take_profit_is_checked_when_enabled(self):
        candles = [
            candle(1.1000, 1.1030, 1.0995, 1.1020),
            candle(1.1020, 1.1030, 1.1010, 1.1025),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020,
            max_hold=1, check_entry_candle=True,
        )
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["exit_reason"], "take")
        self.assertEqual(result["bars_held"], 0)

    def test_entry_candle_stop_wins_if_both_levels_hit(self):
        candles = [
            candle(1.1000, 1.1030, 1.0970, 1.1000),
            candle(1.1000, 1.1010, 1.0990, 1.1005),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020,
            max_hold=1, check_entry_candle=True,
        )
        self.assertEqual(result["result"], "loss")
        self.assertEqual(result["exit_reason"], "stop")
        self.assertEqual(result["bars_held"], 0)

    def test_short_entry_candle_take_profit_is_checked(self):
        candles = [
            candle(1.1000, 1.1010, 1.0970, 1.1000),
            candle(1.1000, 1.1005, 1.0975, 1.0980),
        ]
        result = simulate_trade(
            candles, 0, "short", 1.1000, 1.1020, 1.0980,
            max_hold=1, check_entry_candle=True,
        )
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["exit_reason"], "take")
        self.assertEqual(result["bars_held"], 0)

    def test_max_hold_counts_entry_candle_when_enabled(self):
        candles = [
            candle(1.1000, 1.1010, 1.0990, 1.1005),
            candle(1.1005, 1.1030, 1.1000, 1.1025),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020,
            max_hold=1, check_entry_candle=True,
        )
        self.assertEqual(result["result"], "timeout")
        self.assertEqual(result["bars_held"], 0)
        self.assertAlmostEqual(result["exit"], 1.1005)

    def test_entry_candle_is_not_checked(self):
        candles = [
            candle(1.1000, 1.1030, 1.0970, 1.1000),
            candle(1.1000, 1.1010, 1.0990, 1.1005),
        ]
        result = simulate_trade(
            candles, 0, "long", 1.1000, 1.0980, 1.1020,
            max_hold=1,
        )
        self.assertEqual(result["result"], "timeout")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestMarketAnalyzer(unittest.TestCase):
    @staticmethod
    def make_candles(count=60):
        return [
            {
                "time": 1791500000 + i * 3600,
                "open": 1.1000,
                "high": 1.1010,
                "low": 1.0990,
                "close": 1.1000,
            }
            for i in range(count)
        ]

    def test_closed_only_excludes_last_candle(self):
        candles = self.make_candles()
        candles[-1]["close"] = 1.1005

        from logic import MarketAnalyzer
        analyzer = MarketAnalyzer(candles, closed_only=True)

        self.assertEqual(len(analyzer.df), len(candles) - 1)
        self.assertAlmostEqual(float(analyzer.df["close"].iloc[-1]), 1.1000)

    def test_long_trade_plan_has_correct_levels(self):
        from logic import MarketAnalyzer
        analyzer = MarketAnalyzer(self.make_candles())

        plan = analyzer.calc_trade_plan(
            action="long",
            price=1.1000,
            atr=0.0010,
            levels={"supports": [], "resistances": [1.1200]},
            structure={"swing_lows": [{"price": 1.0950}], "swing_highs": []},
        )

        self.assertIsNotNone(plan)
        self.assertLess(plan["stop_loss"], plan["entry"])
        self.assertGreater(plan["take_profit"], plan["entry"])
        self.assertGreaterEqual(plan["risk_reward"], 1.3)

    def test_short_trade_plan_has_correct_levels(self):
        from logic import MarketAnalyzer
        analyzer = MarketAnalyzer(self.make_candles())

        plan = analyzer.calc_trade_plan(
            action="short",
            price=1.1000,
            atr=0.0010,
            levels={"supports": [1.0800], "resistances": []},
            structure={"swing_lows": [], "swing_highs": [{"price": 1.1050}]},
        )

        self.assertIsNotNone(plan)
        self.assertGreater(plan["stop_loss"], plan["entry"])
        self.assertLess(plan["take_profit"], plan["entry"])
        self.assertGreaterEqual(plan["risk_reward"], 1.3)

    def test_swing_needs_right_hand_confirmation(self):
        from logic import MarketAnalyzer

        candles = self.make_candles(20)
        candles[10]["high"] = 1.1100

        # Пик на последней свече ещё не может быть подтверждён:
        # справа от него недостаточно свечей.
        candles[-1]["high"] = 1.1200

        analyzer = MarketAnalyzer(candles)
        highs, _ = analyzer._swings(order=3)

        self.assertIn(10, [point["index"] for point in highs])
        self.assertNotIn(19, [point["index"] for point in highs])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestCalculateNetPips(unittest.TestCase):
    def test_no_costs_preserves_gross_result(self):
        trades = [{"pips": 20.0}, {"pips": -10.0}]
        self.assertAlmostEqual(
            calculate_net_pips(trades), 10.0
        )

    def test_costs_are_charged_per_trade(self):
        trades = [{"pips": 20.0}, {"pips": -10.0}]
        self.assertAlmostEqual(
            calculate_net_pips(
                trades, spread_pips=0.8, slippage_pips=0.2
            ),
            8.0,
        )

    def test_empty_trades(self):
        self.assertEqual(calculate_net_pips([]), 0.0)

    def test_negative_costs_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_net_pips(
                [{"pips": 10.0}], spread_pips=-0.1
            )
