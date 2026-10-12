"""Unit tests for the calculation, alert and interface logic. Run: python3 -m unittest -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import calculator as c
from src.config import Config, ConfigError
from src.interfaces import InterfaceError, read_counters, select_interface


class SpeedTests(unittest.TestCase):
    def test_rate_from_counter_difference(self):
        self.assertEqual(c.compute_rate(1000, 3048, 2.0), 1024.0)

    def test_counter_reset_gives_zero(self):
        self.assertEqual(c.compute_rate(5000, 100, 1.0), 0.0)

    def test_zero_elapsed_gives_zero(self):
        self.assertEqual(c.compute_rate(0, 100, 0), 0.0)

    def test_unit_conversion(self):
        self.assertAlmostEqual(c.bytes_to_kbps(2048), 2.0)
        self.assertAlmostEqual(c.bytes_to_mbps(125_000), 1.0)  # 1,000,000 bits/s
        self.assertAlmostEqual(c.bytes_to_mb(1024 * 1024), 1.0)


class UtilizationTests(unittest.TestCase):
    def test_unavailable_capacity(self):
        self.assertIsNone(c.utilization_percent(1000, 1000, None))
        self.assertIsNone(c.utilization_percent(1000, 1000, 0))

    def test_known_capacity(self):
        # 6.25 MB/s = 50 Mbps on a 100 Mbps link -> 50 %
        self.assertAlmostEqual(c.utilization_percent(0, 6_250_000, 100), 50.0)


class AlertTests(unittest.TestCase):
    cfg = Config(warning_mbps=5, critical_mbps=20)

    def test_normal(self):
        self.assertEqual(c.classify(1000, 1000, None, self.cfg), c.NORMAL)

    def test_warning(self):  # 1 MB/s = 8 Mbps
        self.assertEqual(c.classify(0, 1_000_000, None, self.cfg), c.WARNING)

    def test_critical(self):  # 3 MB/s = 24 Mbps
        self.assertEqual(c.classify(0, 3_000_000, None, self.cfg), c.CRITICAL)

    def test_utilization_can_escalate(self):
        self.assertEqual(c.classify(0, 100_000, 95.0, self.cfg), c.CRITICAL)
        self.assertEqual(c.classify(0, 100_000, 75.0, self.cfg), c.WARNING)

    def test_messages(self):
        self.assertIn("normal", c.message_for(c.NORMAL))
        self.assertIn("WARNING", c.message_for(c.WARNING))
        self.assertIn("CRITICAL", c.message_for(c.CRITICAL))


class ConfigTests(unittest.TestCase):
    def test_bad_thresholds_rejected(self):
        with self.assertRaises(ConfigError):
            Config(warning_mbps=30, critical_mbps=20).validate()


class InterfaceTests(unittest.TestCase):
    def test_missing_interface(self):
        with self.assertRaises(InterfaceError):
            select_interface("does_not_exist0")
        with self.assertRaises(InterfaceError):
            read_counters("does_not_exist0")


if __name__ == "__main__":
    unittest.main()
