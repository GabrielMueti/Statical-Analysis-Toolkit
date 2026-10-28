"""Unit tests for the toolkit. Run with:  python -m unittest -v   (or pytest)."""
import unittest
import tempfile
from pathlib import Path

from stats_toolkit import (
    mean, median, mode, variance, std_dev, quartiles, iqr_outliers,
    load_column, StatisticsAnalyzer,
)


class TestCentralTendency(unittest.TestCase):
    def test_mean_of_known_values(self):
        self.assertEqual(mean([2, 4, 6]), 4)

    def test_median_even_and_odd_lengths(self):
        self.assertEqual(median([1, 3, 5]), 3)
        self.assertEqual(median([1, 3, 5, 7]), 4)

    def test_mode_with_ties(self):
        self.assertEqual(mode([1, 1, 2, 2, 3]), [1, 2])
        self.assertEqual(mode([1, 2, 3]), [])

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            mean([])
        with self.assertRaises(ValueError):
            median([])


class TestSpread(unittest.TestCase):
    def test_sample_vs_population_variance(self):
        self.assertEqual(variance([2, 4, 6], sample=True), 4)
        self.assertAlmostEqual(variance([2, 4, 6], sample=False), 8 / 3)

    def test_std_dev_single_value(self):
        with self.assertRaises(ValueError):
            std_dev([5])
        self.assertEqual(std_dev([5], sample=False), 0)


class TestOutliers(unittest.TestCase):
    def test_no_outliers_in_uniform_data(self):
        result = iqr_outliers([4, 4, 4, 4, 4])
        self.assertEqual(result["outliers"], [])
        self.assertEqual(result["iqr"], 0)

    def test_detects_obvious_outlier(self):
        result = iqr_outliers([1, 2, 3, 4, 5, 6, 7, 8, 100])
        self.assertEqual(result["outliers"], [100])
        self.assertLess(result["lower_fence"], result["upper_fence"])

    def test_quartiles_use_median_of_halves(self):
        self.assertEqual(quartiles([1, 2, 3, 4, 5]), (1.5, 3, 4.5))


class TestLoading(unittest.TestCase):
    def test_invalid_and_missing_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_text(
                "date,amount\n2026-01-01,10.5\n2026-01-02,\n2026-01-03,n/a\n2026-01-04,12\n",
                encoding="utf-8",
            )
            values, rejected = load_column(path, "amount")
        self.assertEqual(values, [10.5, 12.0])
        self.assertEqual(rejected, [(3, ""), (4, "n/a")])

    def test_analyzer_summary_and_without_outliers(self):
        analyzer = StatisticsAnalyzer([1, 2, 3, 4, 5, 6, 7, 8, 100])
        self.assertEqual(analyzer.summary()["count"], 9)
        cleaned = analyzer.without_outliers()
        self.assertEqual(cleaned.values, [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(analyzer.values, [1, 2, 3, 4, 5, 6, 7, 8, 100])


if __name__ == "__main__":
    unittest.main()
