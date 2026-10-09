import unittest

from calc.pricing import apply_discount


class ApplyDiscount(unittest.TestCase):
    def test_whole_amounts(self):
        self.assertEqual(apply_discount(1000, 10), 900)
        self.assertEqual(apply_discount(0, 50), 0)

    def test_rounds_to_nearest_cent(self):
        self.assertEqual(apply_discount(999, 10), 899)   # 899.1
        self.assertEqual(apply_discount(15, 50), 8)      # 7.5 rounds up

    def test_rejects_invalid_percent(self):
        for bad in (-1, 101):
            with self.assertRaises(ValueError):
                apply_discount(1000, bad)


if __name__ == "__main__":
    unittest.main()
