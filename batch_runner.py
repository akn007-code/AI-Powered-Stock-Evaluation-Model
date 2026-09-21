"""
Stock Evaluation Model — Batch Runner
-----------------------------------------
Pulls data and calculates investment scores for a list of tickers in one
go, then ranks them. Run this locally (Colab/Jupyter/your machine) where
internet access is available.

Requires: data_pipeline.py and scoring_model.py in the same folder.
"""

import pandas as pd
from data_pipeline import get_company_metrics
from scoring_model import calculate_investment_score

# Scoped to the top 5 tech companies by market cap. Keeping the model
# single-industry avoids the sector-adjustment problem entirely (no more
# missing/incompatible metrics like we saw with JPM) since these five
# report financials in a broadly comparable way.
TICKERS = [
    "AAPL",   # Apple - consumer electronics
    "MSFT",   # Microsoft - software/cloud
    "NVDA",   # NVIDIA - semiconductors
    "GOOGL",  # Alphabet - search/cloud/advertising
    "AMZN",   # Amazon - e-commerce/cloud (lower margin profile than the other four)
]


def run_batch(tickers: list) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        try:
            metrics = get_company_metrics(ticker)
            result = calculate_investment_score(metrics)
            row = {
                "ticker": result["ticker"],
                "name": result["name"],
                "overall_score": result["overall_score"],
                **result["category_scores"],
            }
            rows.append(row)
        except Exception as e:
            print(f"Skipped {ticker}: {e}")

    df = pd.DataFrame(rows)
    df = df.sort_values("overall_score", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    results_df = run_batch(TICKERS)
    print(results_df.to_string(index=False))

    # Uncomment to save results for your GitHub repo / README screenshots
    # results_df.to_csv("investment_scores.csv", index=False)
