"""
Stock Evaluation Model — Scoring Engine
------------------------------------------
Takes the raw metrics dictionary produced by data_pipeline.py and converts
it into a 0-100 investment score across five categories:

    Revenue Growth | Profitability | Valuation | Debt | Cash Flow

v1 approach: equal weighting (20% each). Each category is normalized
against reasonable benchmark ranges, since raw numbers (a P/E of 38 vs a
debt-to-equity of 78) aren't on comparable scales. This is deliberately a
transparent, rules-based model rather than a black box — every score can
be explained line by line, which matters for a finance audience.

Note: benchmark ranges are general-purpose starting points, not
sector-specific. A sector-relative version is a natural v2.
"""


def clamp(value, low=0, high=100):
    """Keeps a score within 0-100, in case a metric is unusually extreme."""
    return max(low, min(high, value))


def score_revenue_growth(metrics: dict) -> float:
    """
    0% growth -> 0 points. 30%+ growth -> 100 points (near max for a v1 scale).
    Linear in between. Missing data defaults to a neutral 50.
    """
    growth = metrics.get("revenue_growth")
    if growth is None:
        return 50.0
    return clamp((growth / 0.30) * 100)


def score_profitability(metrics: dict) -> float:
    """
    Averages four profitability signals, each normalized against a
    "strong performance" benchmark:
      - Gross margin:      40%+ = full marks
      - Operating margin:  25%+ = full marks
      - Net margin:        20%+ = full marks
      - Return on equity:  25%+ = full marks (capped, since >100% ROE
                            usually reflects high leverage or buybacks
                            rather than pure operating strength)
    """
    gross = metrics.get("gross_margin") or 0
    operating = metrics.get("operating_margin") or 0
    net = metrics.get("net_margin") or 0
    roe = metrics.get("return_on_equity") or 0

    gross_score = clamp((gross / 0.40) * 100)
    operating_score = clamp((operating / 0.25) * 100)
    net_score = clamp((net / 0.20) * 100)
    roe_score = clamp((min(roe, 0.50) / 0.25) * 100)  # cap input at 50% ROE

    return (gross_score + operating_score + net_score + roe_score) / 4


def score_valuation(metrics: dict) -> float:
    """
    Lower valuation multiples score higher (cheaper relative to
    fundamentals = more attractive on a value basis).
      - P/E:  15x or below = 100 points, 45x+ = 0 points
      - P/B:  2x or below  = 100 points, 15x+ = 0 points
    Averaged across both. This intentionally does NOT judge whether a
    premium is "justified" (e.g. by growth) — that nuance belongs in your
    own read of the results, not the raw score.
    """
    pe = metrics.get("trailing_pe")
    pb = metrics.get("price_to_book")

    pe_score = 50.0 if pe is None else clamp(100 - ((pe - 15) / 30) * 100)
    pb_score = 50.0 if pb is None else clamp(100 - ((pb - 2) / 13) * 100)

    return (pe_score + pb_score) / 2


def score_debt(metrics: dict) -> float:
    """
    Lower debt-to-equity and healthier current ratio score higher.
      - Debt/Equity: 0 = 100 points, 100+ = 0 points
      - Current ratio: 2.0+ = 100 points, 0.5 or below = 0 points
    """
    dte = metrics.get("debt_to_equity")
    current = metrics.get("current_ratio")

    dte_score = 50.0 if dte is None else clamp(100 - (dte / 100) * 100)
    current_score = 50.0 if current is None else clamp(((current - 0.5) / 1.5) * 100)

    return (dte_score + current_score) / 2


def score_cash_flow(metrics: dict) -> float:
    """
    Two signals, averaged:
      - Cash yield: free cash flow as a % of market cap.
        3%+ yield = 100 points, 0% or negative = 0 points.
      - FCF conversion quality: free cash flow / operating cash flow.
        High conversion (close to or above 1.0) suggests earnings are
        backed by real cash, not just accounting profit. 70%+ = full marks.
    """
    fcf = metrics.get("free_cashflow")
    ocf = metrics.get("operating_cashflow")
    market_cap = metrics.get("market_cap")

    if fcf is None or market_cap in (None, 0):
        yield_score = 50.0
    else:
        cash_yield = fcf / market_cap
        yield_score = clamp((cash_yield / 0.03) * 100)

    if fcf is None or ocf in (None, 0):
        conversion_score = 50.0
    else:
        conversion = fcf / ocf
        conversion_score = clamp((conversion / 0.70) * 100)

    return (yield_score + conversion_score) / 2


def calculate_investment_score(metrics: dict, weights: dict = None) -> dict:
    """
    Combines all five category scores into one overall investment score.
    Default weighting is equal (20% each) for v1.
    """
    if weights is None:
        weights = {
            "revenue_growth": 0.20,
            "profitability": 0.20,
            "valuation": 0.20,
            "debt": 0.20,
            "cash_flow": 0.20,
        }

    category_scores = {
        "revenue_growth": score_revenue_growth(metrics),
        "profitability": score_profitability(metrics),
        "valuation": score_valuation(metrics),
        "debt": score_debt(metrics),
        "cash_flow": score_cash_flow(metrics),
    }

    overall = sum(category_scores[cat] * weights[cat] for cat in category_scores)

    return {
        "ticker": metrics.get("ticker"),
        "name": metrics.get("name"),
        "category_scores": {k: round(v, 1) for k, v in category_scores.items()},
        "overall_score": round(overall, 1),
    }


if __name__ == "__main__":
    # Real data pulled from data_pipeline.py for AAPL, MSFT, NVDA
    sample_companies = [
        {
            "ticker": "AAPL", "name": "Apple Inc.",
            "revenue_growth": 0.164, "earnings_growth": 0.287,
            "gross_margin": 0.48653, "operating_margin": 0.32623,
            "net_margin": 0.27619, "return_on_equity": 1.48751,
            "trailing_pe": 38.148106, "forward_pe": 34.703167,
            "price_to_book": 45.145380, "market_cap": 4849207869440,
            "debt_to_equity": 78.445, "current_ratio": 1.003,
            "total_debt": 84343996416, "total_cash": 62399000576,
            "operating_cashflow": 146723995648, "free_cashflow": 107721875456,
        },
        {
            "ticker": "MSFT", "name": "Microsoft Corporation",
            "revenue_growth": 0.177, "earnings_growth": 0.317,
            "gross_margin": 0.67944, "operating_margin": 0.45111,
            "net_margin": 0.40305, "return_on_equity": 0.34039,
            "trailing_pe": 27.627090, "forward_pe": 21.025343,
            "price_to_book": 8.320827, "market_cap": 3680323239936,
            "debt_to_equity": 29.118, "current_ratio": 1.230,
            "total_debt": 128812998656, "total_cash": 76842999808,
            "operating_cashflow": 182934994944, "free_cashflow": 16545500160,
        },
        {
            "ticker": "NVDA", "name": "NVIDIA Corporation",
            "revenue_growth": 1.059, "earnings_growth": 1.278,
            "gross_margin": 0.74674, "operating_margin": 0.66237,
            "net_margin": 0.63663, "return_on_equity": 1.17211,
            "trailing_pe": 27.631645, "forward_pe": 14.022135,
            "price_to_book": 23.019087, "market_cap": 5271048421376,
            "debt_to_equity": 16.971, "current_ratio": 4.589,
            "total_debt": 38860001280, "total_cash": 62469001216,
            "operating_cashflow": 134359998464, "free_cashflow": 41809874944,
        },
    ]

    for company in sample_companies:
        result = calculate_investment_score(company)
        print(f"\n{result['name']} ({result['ticker']})")
        print(f"  Overall Score: {result['overall_score']}/100")
        for category, score in result["category_scores"].items():
            print(f"    {category}: {score}")
