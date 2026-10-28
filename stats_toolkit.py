import csv
import math
from pathlib import Path

DATA_PATH = Path("data") / "agent_deposits (1).csv"

def load_column(path: Path, column: str) -> tuple[list[float], list[tuple[int, str]]]:
    """Return (valid_values, rejected) where rejected holds (row_number, raw_value) pairs."""
    values = []
    rejected = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise ValueError(f"Column {column!r} was not found in {path}")
        for row_number, row in enumerate(reader, start=2):
            raw = row.get(column)
            text = "" if raw is None else raw.strip()
            try:
                value = float(text)
                if not math.isfinite(value):
                    raise ValueError
            except (TypeError, ValueError):
                rejected.append((row_number, "" if raw is None else raw))
            else:
                values.append(value)
    return values, rejected


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("median requires at least one value")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def mode(values: list[float]) -> list[float]:
    """Return all most-frequent values; return [] if every value occurs once."""
    if not values:
        return []
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    highest = max(counts.values())
    if highest == 1:
        return []
    return sorted(value for value, count in counts.items() if count == highest)


def variance(values: list[float], sample: bool = True) -> float:
    """Sample variance (n - 1) by default; population variance (n) when sample is False."""
    denominator = len(values) - 1 if sample else len(values)
    if denominator <= 0:
        raise ValueError("variance requires at least two values for a sample or one for a population")
    average = mean(values)
    return sum((value - average) ** 2 for value in values) / denominator


def std_dev(values: list[float], sample: bool = True) -> float:
    return math.sqrt(variance(values, sample))


def quartiles(values: list[float]) -> tuple[float, float, float]:
    """Return (Q1, Q2, Q3) using Tukey's median-of-halves method (exclude center for odd n)."""
    if not values:
        raise ValueError("quartiles requires at least one value")
    ordered = sorted(values)
    center = len(ordered) // 2
    q2 = median(ordered)
    if len(ordered) % 2:
        lower, upper = ordered[:center], ordered[center + 1:]
    else:
        lower, upper = ordered[:center], ordered[center:]
    if not lower:
        return q2, q2, q2
    return median(lower), q2, median(upper)


def iqr_outliers(values: list[float], k: float = 1.5) -> dict:
    """Return the IQR, the lower and upper fences, and the values outside them."""
    if not values:
        raise ValueError("IQR outlier detection requires at least one value")
    if k < 0:
        raise ValueError("k must be non-negative")
    q1, _, q3 = quartiles(values)
    spread = q3 - q1
    lower = q1 - k * spread
    upper = q3 + k * spread
    return {"iqr": spread, "lower_fence": lower, "upper_fence": upper,
            "outliers": [value for value in values if value < lower or value > upper]}


class StatisticsAnalyzer:
    """Wraps one numeric column and exposes every statistic above as a method."""

    def __init__(self, values: list[float], name: str = "values") -> None:
        if not values:
            raise ValueError("StatisticsAnalyzer requires at least one value")
        self.values = list(values)
        self.name = name
        self._sorted = sorted(self.values)
        self.rejected: list[tuple[int, str]] = []
        self.rows_read = len(self.values)
        self.records: list[tuple[float, str, str]] = []

    @classmethod
    def from_csv(cls, path: Path, column: str) -> "StatisticsAnalyzer":
        values, rejected = load_column(path, column)
        analyzer = cls(values, column)
        analyzer.rejected = rejected
        with Path(path).open("r", newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            analyzer.records = []
            for row in reader:
                raw = (row.get(column) or "").strip()
                try:
                    value = float(raw)
                    if math.isfinite(value):
                        analyzer.records.append((value, row.get("date", ""), row.get("agent_id", "")))
                except ValueError:
                    continue
        analyzer.rows_read = len(values) + len(rejected)
        return analyzer

    def summary(self) -> dict:
        q1, q2, q3 = quartiles(self.values)
        outlier_info = iqr_outliers(self.values)
        return {"count": len(self.values), "mean": mean(self.values), "median": q2,
                "mode": mode(self.values), "variance": variance(self.values),
                "std_dev": std_dev(self.values), "min": self._sorted[0], "max": self._sorted[-1],
                "q1": q1, "q3": q3, "iqr": outlier_info["iqr"],
                "lower_fence": outlier_info["lower_fence"], "upper_fence": outlier_info["upper_fence"],
                "outliers": outlier_info["outliers"]}

    def without_outliers(self) -> "StatisticsAnalyzer":
        outliers = iqr_outliers(self.values)["outliers"]
        removed = set(outliers)
        kept = [value for value in self.values if value not in removed]
        if not kept:
            raise ValueError("Removing outliers left no values")
        result = StatisticsAnalyzer(kept, self.name)
        result.records = [record for record in self.records if record[0] not in removed]
        result.rows_read = len(kept)
        return result

    def report(self) -> str:
        """Build the report text in the supplied expected layout."""
        clean = self.without_outliers()
        all_stats =self.summary()
        clean_stats = clean.summary()
        lines = [f"=== Statistics report: {self.name} ===",
                 f"Rows read         : {self.rows_read}", f"Valid values      : {len(self.values)}",
                 f"Rejected values   : {len(self.rejected)}"]
        for row_number, raw in self.rejected:
            stripped = raw.strip()
            if not stripped:
                reason = "blank value"
            elif stripped.lower() in {"-", "n/a", "na", "null", "none"}:
                reason = f"placeholder {stripped!r} is not numeric"
            else:
                reason = "not a finite numeric value"
            lines.append(f"  row {row_number}: {raw!r} ({reason})")
        lines += ["", "                    all data      outliers removed"]
        rows = [("count", "count"), ("mean", "mean"), ("median", "median"), ("mode", "mode"),
                ("variance (sample)", "variance"), ("std dev (sample)", "std_dev")]
        for label, key in rows:
            a, b = all_stats[key], clean_stats[key]
            if key == "mode":
                a = ", ".join(f"{x:g}" for x in a) if a else "none"
                b = ", ".join(f"{x:g}" for x in b) if b else "none"
            elif key != "count":
                a, b = f"{a:.2f}", f"{b:.2f}"
            lines.append(f"{label:<20}{str(a):<14}{b}")
        lines.append(f"{'min / max':<20}{all_stats['min']:.2f} / {all_stats['max']:.2f}  "
                     f"{clean_stats['min']:.2f} / {clean_stats['max']:.2f}")
        lines.append(f"{'Q1 / Q3':<20}{all_stats['q1']:.2f} / {all_stats['q3']:.2f}  "
                     f"{clean_stats['q1']:.2f} / {clean_stats['q3']:.2f}")
        lines.append(f"{'IQR':<20}{all_stats['iqr']:.2f}          {clean_stats['iqr']:.2f}")
        lines += ["", f"Outlier fences      : lower {all_stats['lower_fence']:.2f}, upper {all_stats['upper_fence']:.2f}"]
        record_lookup = {(value, date, agent) for value, date, agent in self.records}
        outlier_text = []
        for value in all_stats["outliers"]:
            match = next(((date, agent) for val, date, agent in record_lookup if val == value), ("unknown date", "unknown agent"))
            outlier_text.append(f"{value:.2f} ({match[0]}, {match[1]})")
        lines.append("Outliers            : " + (", ".join(outlier_text) if outlier_text else "none"))
        lines += ["", "Risk team: A high outlier may reflect fraud, an unusual legitimate deposit, or a recording error.",
                  "A low outlier may indicate a float shortage, temporary closure, or a missing transaction batch.",
                  "Review the source records and agent context before taking action; the IQR flag alone does not establish cause."]
        return "\n".join(lines) + "\n"


def compare_with_numpy(analyzer: StatisticsAnalyzer) -> dict[str, bool]:
    """Import numpy HERE, recompute each statistic and return {name: matches}."""
    import numpy as np

    values = np.asarray(analyzer.values, dtype=float)
    q1, q2, q3 = quartiles(analyzer.values)
    numpy_q1, numpy_q3 = np.quantile(values, [0.25, 0.75], method="averaged_inverted_cdf")
    # Tukey hinges use medians of the two halves; this also handles small/even samples.
    sorted_values = np.sort(values)
    mid = len(sorted_values) // 2
    low = sorted_values[:mid] if len(sorted_values) % 2 else sorted_values[:mid]
    high = sorted_values[mid + 1:] if len(sorted_values) % 2 else sorted_values[mid:]
    np_q1 = float(np.median(low)) if len(low) else float(np.median(sorted_values))
    np_q3 = float(np.median(high)) if len(high) else float(np.median(sorted_values))
    tol = 1e-9
    return {"mean": math.isclose(mean(analyzer.values), float(np.mean(values)), rel_tol=tol, abs_tol=tol),
            "median": math.isclose(median(analyzer.values), float(np.median(values)), rel_tol=tol, abs_tol=tol),
            "variance": math.isclose(variance(analyzer.values), float(np.var(values, ddof=1)), rel_tol=tol, abs_tol=tol),
            "std_dev": math.isclose(std_dev(analyzer.values), float(np.std(values, ddof=1)), rel_tol=tol, abs_tol=tol),
            "quartiles": math.isclose(q1, np_q1, rel_tol=tol, abs_tol=tol) and math.isclose(q3, np_q3, rel_tol=tol, abs_tol=tol)}


if __name__ == "__main__":
    analyzer = StatisticsAnalyzer.from_csv(DATA_PATH, "daily_deposits_kes")
    report = analyzer.report()
    output_path = Path("output") / "stats_report.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report, end="")
    print("\n=== NumPy verification ===")
    checks = compare_with_numpy(analyzer)
    labels = {"mean": "mean", "median": "median", "variance": "variance", "std_dev": "std dev", "quartiles": "Q1 / Q3"}
    for key, label in labels.items():
        extra = "  (ddof=1)" if key in ("variance", "std_dev") else "  (method=Tukey median-of-halves)" if key == "quartiles" else ""
        print(f"{label:<10}{'MATCH' if checks[key] else 'MISMATCH'}{extra}")
