"""
Stock Evaluation Model — Data Pipeline
----------------------------------------
Pulls the raw financial metrics needed to score a company across:
Revenue Growth, Profitability, Valuation, Debt, and Cash Flow.

Requires internet access (run locally, in Colab, or in Jupyter — not in a
sandboxed/offline environment).

Install once with:
    pip install yfinance
"""

import yfinance as yf


def get_company_metrics(ticker_symbol: str) -> dict:
    """
    Pulls the key raw metrics for one company from Yahoo Finance.
    Returns a flat dictionary — this is the raw material our scoring
    model will later turn into a 0-100 investment score.
    """
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    metrics = {
        "ticker": ticker_symbol,
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),

        # --- Growth ---
        "revenue_growth": info.get("revenueGrowth"),        # e.g. 0.08 = 8%
        "earnings_growth": info.get("earningsGrowth"),

        # --- Profitability ---
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "return_on_equity": info.get("returnOnEquity"),

        # --- Valuation ---
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "market_cap": info.get("marketCap"),

        # --- Debt ---
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "total_debt": info.get("totalDebt"),
        "total_cash": info.get("totalCash"),

        # --- Cash Flow ---
        "operating_cashflow": info.get("operatingCashflow"),
        "free_cashflow": info.get("freeCashflow"),
    }

    return metrics


if __name__ == "__main__":
    # Quick test — swap in any ticker
    data = get_company_metrics("AAPL")
    for key, value in data.items():
        print(f"{key}: {value}")
