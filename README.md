# Wakala Plus Statistical Analysis Toolkit


## Overview

Wakala Plus operates M-Pesa agent networks around Nairobi, Thika, Machakos, and Nakuru. The risk team reviews daily deposits for unusually high or low amounts that could point to fraud, a float shortage, or a data-entry error.

This toolkit analyzes the `daily_deposits_kes` column in the supplied 40-day dataset. It calculates summary statistics using plain Python, records missing and invalid entries, flags potential outliers using the interquartile range (IQR), and checks selected results against NumPy. It then prints and saves a report for the risk team.

## Project files

```text
Statistical-Analysis
├── stats_toolkit.py
├── test_stats_toolkit.py
├── data/
│   └── agent_deposits.csv
├── output/
│   └── stats_report.txt
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9 or later
- NumPy 2.5.3, used only to verify calculations in `compare_with_numpy()`

The supplied requirements file is a full Anaconda environment export with many packages and machine-specific `file:///...` paths. Those paths may not work on another computer. This toolkit only needs NumPy as a third-party dependency, so a portable project `requirements.txt` can contain:

```text
numpy==2.5.3
```

Install the project dependency from the project directory:

```bash
python -m pip install -r requirements.txt
```

All statistics are calculated in plain Python. The toolkit does not use Python’s `statistics` module. CSV handling, numeric validation, square roots, and file operations use the Python standard library.

## Run the toolkit

From the project directory, run:

```bash
python stats_toolkit.py
```

The script prints the report and NumPy verification results, then saves the report to:

```text
output/stats_report.txt
```

The script creates the `output` directory if it does not already exist. The input CSV location is set by `DATA_PATH` near the top of `stats_toolkit.py`.

## Run the tests

The tests use Python’s built-in `unittest` framework:

```bash
python -m unittest -v
```

The suite uses small, hand-checkable examples and a temporary CSV file. It covers central tendency, empty input, sample and population variance, standard deviation edge cases, quartiles, outlier detection, rejected CSV values, and the `StatisticsAnalyzer` class.

## Approach and assumptions

### Calculations

Mean, median, mode, variance, standard deviation, quartiles, and IQR outlier detection are implemented directly in Python.

- `mode()` returns every value tied for the highest frequency. It returns an empty list for empty input or when every value appears once.
- Mean, median, and quartiles raise `ValueError` when given empty input.
- Variance and standard deviation support sample and population formulas. They use the **sample** formula (`n - 1`) by default because the observed days are treated as a sample of an ongoing deposit process. Pass `sample=False` to use the population formula when the data represents the entire population of interest.
- Sample variance and standard deviation require at least two values; population variance and standard deviation require at least one.

### Quartiles and outliers

Quartiles use **Tukey’s median-of-halves method**. Q2 is the median of the full dataset. When there is an odd number of values, Q2 is excluded from both halves; Q1 and Q3 are the medians of the lower and upper halves.

The IQR is `Q3 - Q1`. With the default `k = 1.5`, the fences are:

```text
Lower fence = Q1 - 1.5 × IQR
Upper fence = Q3 + 1.5 × IQR
```

Only values strictly outside the fences are flagged. The NumPy comparison uses the same quartile method. An outlier is a review flag, not proof of fraud or an error.

### Data cleaning

`load_column(path, column)` returns valid values as floats and rejected entries as `(row_number, raw_value)` pairs. It accepts values that Python can parse as finite numbers. Blank cells, placeholders such as `-` and `n/a`, malformed entries such as `12,40O`, and non-finite values such as `NaN` or infinity are rejected.

The toolkit does not guess, correct, or fill rejected values. The report provides a reason for each rejection based on its raw text. CSV row numbers count the header as row 1.

### Analyzer class and report

`StatisticsAnalyzer` keeps the values and related CSV details together.

- `from_csv()` loads a column and creates an analyzer.
- `summary()` returns the statistics in a dictionary.
- `without_outliers()` returns a new analyzer with flagged values removed; it leaves the original analyzer unchanged.
- `report()` formats the full-data and cleaned-data summaries, rejection details, outlier records, and risk-team notes.

The analyzer stores a sorted copy of the values for reuse.

### NumPy verification

NumPy is imported only inside `compare_with_numpy()`. It checks the mean, median, sample variance, sample standard deviation, and quartiles against the toolkit’s results using a numerical tolerance. The variance and standard deviation checks use `ddof=1` to match the sample formulas.

## Limitations

The IQR method can flag legitimate unusual activity, and different quartile conventions can produce different fences. Review flagged deposits against source records and agent context before deciding what they mean. This teaching toolkit is not a fraud-detection system.

