# Wakala Plus Statistical Analysis Toolkit

## Overview

Wakala Plus runs a network of M-Pesa agents around Nairobi, Thika, Machakos and Nakuru. The risk team monitors daily deposit totals because unusually high or low days may point to fraud, a float shortage, or a data-entry error.

This project analyzes the `daily_deposits_kes` column in the supplied agent deposit dataset. It implements the statistical calculations in plain Python, records invalid and missing values, detects outliers using the interquartile range (IQR), and compares the results with NumPy. The toolkit also generates a report for the risk team.

## Project files

```text
day3-stats-toolkit/
├── stats_toolkit.py
├── test_stats_toolkit.py
├── data/
│   └── agent_deposits.csv
├── output/
│   └── stats_report.txt
├── requirements.txt
└── README.md
```

## Requirements and dependencies

- Python 3.9 or later
- NumPy, used only to verify the calculations

The calculations are implemented in plain Python. The toolkit does not use Python’s `statistics` module. CSV handling, calculations, and file operations use Python’s standard library.

Install the dependency from the project directory:

```bash
python -m pip install -r requirements.txt
```

The `requirements.txt` file contains:

```text
numpy
```

## Running the toolkit

From the project directory, run:

```bash
python stats_toolkit.py
```

The script prints the statistical report and NumPy comparison results in the terminal. It also creates the `output` folder if needed and saves the report to:

```text
output/stats_report.txt
```

The input CSV path is set by `DATA_PATH` near the top of `stats_toolkit.py`.

## Running the tests

The test suite uses Python’s built-in `unittest` framework, so no separate test framework is required.

```bash
python -m unittest -v
```

The tests use small, hand-checkable examples and a temporary CSV file rather than relying on the supplied dataset. They cover means, odd and even medians, tied modes, empty inputs, sample and population variance, standard deviation edge cases, quartiles, outlier detection, rejected CSV values, and the `StatisticsAnalyzer` class.

## Statistical approach and choices

### Mean, median, and mode

Mean, median, and mode are implemented directly in Python.

- The mean is the sum of the values divided by the number of values.
- The median is the middle value after sorting, or the average of the two middle values when the list length is even.
- The mode function returns a list of every value tied for the highest frequency. It returns an empty list when the input is empty or every value occurs once, because there is no repeated value to report as a mode.

Mean and median raise `ValueError` for empty input.

### Variance and standard deviation

The variance and standard deviation functions support both sample and population formulas.

- Sample variance divides by `n - 1`.
- Population variance divides by `n`.
- Sample variance and standard deviation are used by default.

The 40 days in this dataset are treated as observations from an ongoing deposit process. Sample variance is therefore used to estimate the process’s broader variability. If the values being analyzed represent the complete population of interest, pass `sample=False` to use the population formula.

Sample variance requires at least two values. Population variance requires at least one value.

### Quartiles and IQR outliers

Quartiles use **Tukey’s median-of-halves method**:

- Q2 is the median of the full sorted dataset.
- When the number of values is odd, Q2 is excluded from both halves.
- Q1 is the median of the lower half; Q3 is the median of the upper half.

The IQR is calculated as:

```text
IQR = Q3 - Q1
```

Using the default `k = 1.5`, the fences are:

```text
Lower fence = Q1 - 1.5 × IQR
Upper fence = Q3 + 1.5 × IQR
```

Values strictly below the lower fence or strictly above the upper fence are flagged as outliers. A value equal to a fence is not flagged. Quartile conventions can differ, so NumPy verification uses the same median-of-halves approach as the toolkit.

An outlier is a signal to review the record. It does not, by itself, establish fraud or a data-entry error.

### Missing and invalid values

`load_column(path, column)` reads the selected CSV column and returns:

1. Valid values converted to floats.
2. Rejected `(row_number, raw_value)` pairs.

A value is accepted only if Python can parse it as a finite float. Blank cells, placeholders such as `-` and `n/a`, malformed values such as `12,40O`, and non-finite values such as `NaN` or infinity are rejected. The toolkit does not guess, correct, or impute rejected values.

The report records a reason for each rejected value based on its raw text. CSV row numbering counts the header as row 1.

### `StatisticsAnalyzer`

`StatisticsAnalyzer` keeps a dataset and its related information together, including its column name, rejected rows, and available date and agent details.

- `StatisticsAnalyzer.from_csv()` loads the requested column from a CSV file and creates an analyzer.
- `summary()` returns the calculated statistics in a dictionary.
- `without_outliers()` returns a new analyzer containing values retained by the IQR rule. It does not change the original analyzer.
- `report()` formats the full-data and outliers-removed statistics, rejected values, outlier details, and risk-team notes.

The analyzer stores a sorted copy of its values for reuse.

### NumPy verification

NumPy is imported only inside `compare_with_numpy()`. It verifies the toolkit’s mean, median, sample variance, sample standard deviation, and quartiles. Comparisons use a numerical tolerance rather than exact equality. The NumPy variance and standard deviation checks use `ddof=1`, matching the toolkit’s sample formulas.

## Assumptions and limitations

- The supplied CSV contains daily deposit values in Kenyan shillings.
- Valid numeric values are analyzed as entered; the toolkit does not correct suspected typos.
- The IQR rule is a screening method. Unusual deposits may be legitimate, so flagged records should be checked against the source data and agent context.
- This small teaching dataset and toolkit are not a fraud-detection system.

## GitHub submission

Before submitting the project, push the code, dataset, generated report, tests, `requirements.txt`, and this README to a public GitHub repository, or to a private repository shared with the instructor. Then provide the repository URL on Squad and submit the project.
```
