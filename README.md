# VIX Alert

Installable Python package for fetching VIX data and calculating mean and ±1/±2 standard-deviation thresholds.

No notification sending is included.

## Install

```bash
uv venv
.venv\Scripts\Activate.ps1
uv pip install -e .
```

Or with pip:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## CLI

Run the default 1-year analysis:

```bash
vix-alert
```

Choose another period:

```bash
vix-alert --period 6mo
vix-alert --period 30d
```

Output JSON:

```bash
vix-alert --json
```

## Python usage

```python
from vix_alert import VIXAnalyzer

analyzer = VIXAnalyzer()
analyzer.fetch_data(period="1y")
stats = analyzer.calculate_statistics()
print(stats)
print(analyzer.get_summary())
```

## Output

The package calculates:

- Current VIX
- Mean
- Standard deviation
- Mean ±1 standard deviation
- Mean ±2 standard deviations
- Current level relative to thresholds
