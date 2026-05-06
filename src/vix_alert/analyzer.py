"""Fetch VIX data and calculate statistical thresholds."""

from __future__ import annotations

import io
import urllib.request
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


class VIXAnalyzer:
    """Fetch and analyze VIX historical prices."""

    def __init__(self, ticker: str = "^VIX") -> None:
        self.ticker = ticker
        self.data: pd.DataFrame | None = None
        self.stats: dict[str, float | str] = {}

    def fetch_data(self, period: str = "1y") -> pd.DataFrame:
        """Fetch VIX data with multiple fallback sources."""
        errors = []

        for source_name, fetcher in [
            ("Yahoo Finance (yfinance)", self._fetch_from_yahoo),
            ("Stooq", self._fetch_from_stooq),
            ("Yahoo Finance (direct)", self._fetch_from_yahoo_direct),
        ]:
            try:
                data = fetcher(period)

                if data is None or data.empty:
                    raise ValueError(f"No data retrieved from {source_name}")

                self.data = data.sort_index()
                return self.data
            except Exception as exc:
                errors.append(f"{source_name}: {exc}")

        raise RuntimeError(
            "Failed to fetch VIX data from all sources:\n" + "\n".join(errors)
        )

    def _fetch_from_yahoo(self, period: str) -> pd.DataFrame:
        import yfinance as yf

        data = yf.download(
            self.ticker,
            period=period,
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data.dropna(subset=["Close"])

    def _fetch_from_stooq(self, period: str) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = self._period_to_start_date(period, end_date)
        url = (
            "https://stooq.com/q/d/l/"
            f"?s=vix.us&i=d&d1={start_date:%Y%m%d}&d2={end_date:%Y%m%d}"
        )

        data = pd.read_csv(url, parse_dates=["Date"])

        if data.empty or "Close" not in data.columns:
            raise ValueError("Stooq returned no usable VIX data")

        data = data.set_index("Date")
        return data.dropna(subset=["Close"])

    def _fetch_from_yahoo_direct(self, period: str) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = self._period_to_start_date(period, end_date)

        period1 = int(start_date.timestamp())
        period2 = int(end_date.timestamp())
        url = (
            "https://query1.finance.yahoo.com/v7/finance/download/%5EVIX"
            f"?period1={period1}&period2={period2}&interval=1d&events=history"
        )

        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            csv_text = response.read().decode("utf-8")

        data = pd.read_csv(io.StringIO(csv_text), parse_dates=["Date"])

        if data.empty or "Close" not in data.columns:
            raise ValueError("Yahoo direct CSV returned no usable data")

        data = data.set_index("Date")
        data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
        return data.dropna(subset=["Close"])

    @staticmethod
    def _period_to_start_date(period: str, end_date: datetime) -> datetime:
        period = period.lower().strip()

        if period.endswith("mo"):
            return end_date - timedelta(days=30 * int(period[:-2]))
        if period.endswith("y"):
            return end_date - timedelta(days=365 * int(period[:-1]))
        if period.endswith("d"):
            return end_date - timedelta(days=int(period[:-1]))

        return end_date - timedelta(days=365)

    def calculate_statistics(self) -> dict[str, float | str]:
        """Calculate mean and standard-deviation thresholds from close prices."""
        if self.data is None or self.data.empty:
            raise ValueError("No data available. Call fetch_data() first.")

        close_prices = self.data["Close"]
        mean = float(close_prices.mean())
        std = float(close_prices.std())

        self.stats = {
            "mean": mean,
            "std": std,
            "mean_minus_2std": mean - 2 * std,
            "mean_minus_1std": mean - std,
            "mean_plus_1std": mean + std,
            "mean_plus_2std": mean + 2 * std,
            "current_vix": float(close_prices.iloc[-1]),
            "last_updated": self.data.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
            "observations": float(len(close_prices)),
        }
        return self.stats

    def get_current_level(self) -> tuple[float, str]:
        """Return current VIX value and its level relative to thresholds."""
        if not self.stats:
            self.calculate_statistics()

        current = float(self.stats["current_vix"])

        if current >= float(self.stats["mean_plus_2std"]):
            level = "EXTREME HIGH (>+2std)"
        elif current >= float(self.stats["mean_plus_1std"]):
            level = "HIGH (+1std to +2std)"
        elif current >= float(self.stats["mean"]):
            level = "ABOVE AVERAGE (mean to +1std)"
        elif current >= float(self.stats["mean_minus_1std"]):
            level = "BELOW AVERAGE (-1std to mean)"
        elif current >= float(self.stats["mean_minus_2std"]):
            level = "LOW (-2std to -1std)"
        else:
            level = "EXTREME LOW (<-2std)"

        return current, level

    def get_summary(self) -> str:
        """Generate a formatted summary of VIX statistics."""
        if not self.stats:
            self.calculate_statistics()

        current, level = self.get_current_level()

        return (
            "\nVIX ANALYSIS SUMMARY\n"
            f"{'=' * 50}\n"
            f"Last Updated: {self.stats['last_updated']}\n"
            f"Observations: {int(float(self.stats['observations']))}\n\n"
            f"Current VIX: {current:.2f}\n"
            f"Status: {level}\n\n"
            "Statistical Thresholds:\n"
            f"{'=' * 50}\n"
            f"Mean + 2std:  {float(self.stats['mean_plus_2std']):.2f}\n"
            f"Mean + 1std:  {float(self.stats['mean_plus_1std']):.2f}\n"
            f"Mean:         {float(self.stats['mean']):.2f}\n"
            f"Mean - 1std:  {float(self.stats['mean_minus_1std']):.2f}\n"
            f"Mean - 2std:  {float(self.stats['mean_minus_2std']):.2f}\n\n"
            f"Standard Deviation: {float(self.stats['std']):.2f}\n"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return calculated statistics as a JSON-serializable dictionary."""
        if not self.stats:
            self.calculate_statistics()
        return dict(self.stats)
