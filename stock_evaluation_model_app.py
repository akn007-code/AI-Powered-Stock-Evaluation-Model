"""
Stock Evaluation Model — Interactive Dashboard (v2)
--------------------------------------------------------
Tells the "story" behind each company's investment score with one chart
per category (Revenue Growth, Profitability, Valuation, Debt, Cash Flow),
each showing the real underlying numbers next to the benchmark used to
score them — plus a radar chart summarizing all five scores, and a gauge
for the overall score.

Run locally with:
    pip install streamlit plotly
    streamlit run streamlit_app.py

Requires data_pipeline.py and scoring_model.py in the same folder.
"""

import streamlit as st
import plotly.graph_objects as go

from data_pipeline import get_company_metrics
from scoring_model import calculate_investment_score

# ---------------------------------------------------------------------
# Theme — dark navy/black background with neon blue-to-teal-green accents
# ---------------------------------------------------------------------
COLOR_BG = "#05070d"
COLOR_CARD = "#0a1120"
COLOR_ACTUAL = "#2dd4bf"      # teal/green — the company's real number
COLOR_BENCHMARK = "#3b82f6"   # electric blue — the benchmark/target
COLOR_TEXT = "#e8f6f4"
GAUGE_COLORWAY = ["#1e3a8a", "#0e7490", "#0891b2", "#14b8a6", "#34d399"]

PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=COLOR_CARD,
        plot_bgcolor=COLOR_CARD,
        font=dict(color=COLOR_TEXT, family="Arial"),
        colorway=[COLOR_ACTUAL, COLOR_BENCHMARK],
        margin=dict(l=30, r=30, t=50, b=30),
    )
)

st.set_page_config(page_title="Stock Evaluation Model", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 20% 0%, #0a1a2e 0%, {COLOR_BG} 55%);
        color: {COLOR_TEXT};
    }}
    h1, h2, h3, p, label, .stMarkdown {{
        color: {COLOR_TEXT} !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {COLOR_CARD};
        border-color: #2dd4bf;
    }}
    .stButton > button {{
        background-color: #0891b2;
        color: white;
        border: none;
    }}
    .stButton > button:hover {{
        background-color: #2dd4bf;
        color: #05070d;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {COLOR_CARD};
        border: 1px solid #14385e;
        border-radius: 10px;
        padding: 8px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI-Powered Stock Evaluation Model")
st.write(
    "A first-pass investment score built from five categories: Revenue Growth, "
    "Profitability, Valuation, Debt, and Cash Flow — each chart below shows the "
    "real numbers behind the score, not just the score itself. "
    "Built and validated on the top 5 technology companies by market cap."
)

FOCUS_COMPANIES = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "NVIDIA (NVDA)": "NVDA",
    "Alphabet (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
}

choice = st.selectbox(
    "Choose a company, or type your own ticker below:",
    options=list(FOCUS_COMPANIES.keys()) + ["Custom ticker..."],
)

if choice == "Custom ticker...":
    ticker_input = st.text_input("Enter a stock ticker (e.g. TSLA)", value="")
else:
    ticker_input = FOCUS_COMPANIES[choice]

run_button = st.button("Evaluate")


# ---------------------------------------------------------------------
# Chart builders — each one pairs the real metric against its benchmark
# ---------------------------------------------------------------------

def bar_actual_vs_benchmark(title, labels, actual_values, benchmark_values, value_suffix=""):
    """Generic grouped bar: the company's real numbers vs the benchmark used to score them."""
    fig = go.Figure()
    fig.add_bar(name="Actual", x=labels, y=actual_values,
                text=[f"{v:.1f}{value_suffix}" for v in actual_values], textposition="outside")
    fig.add_bar(name="Benchmark", x=labels, y=benchmark_values,
                text=[f"{v:.1f}{value_suffix}" for v in benchmark_values], textposition="outside")
    fig.update_layout(template=PLOTLY_TEMPLATE, title=title, barmode="group", height=320,
                       title_font_size=15)
    return fig


def make_revenue_chart(metrics):
    growth = (metrics.get("revenue_growth") or 0) * 100
    return bar_actual_vs_benchmark(
        "Revenue Growth", ["Revenue Growth"], [growth], [30],
        value_suffix="%",
    )


def make_profitability_chart(metrics):
    labels = ["Gross Margin", "Operating Margin", "Net Margin", "Return on Equity"]
    actual = [
        (metrics.get("gross_margin") or 0) * 100,
        (metrics.get("operating_margin") or 0) * 100,
        (metrics.get("net_margin") or 0) * 100,
        (metrics.get("return_on_equity") or 0) * 100,
    ]
    benchmark = [40, 25, 20, 25]
    return bar_actual_vs_benchmark("Profitability", labels, actual, benchmark, value_suffix="%")


def make_valuation_chart(metrics):
    labels = ["P/E Ratio", "P/B Ratio"]
    actual = [metrics.get("trailing_pe") or 0, metrics.get("price_to_book") or 0]
    benchmark = [15, 2]  # "attractive" ceiling — lower is better here
    fig = bar_actual_vs_benchmark("Valuation (lower is more attractive)", labels, actual, benchmark, "x")
    return fig


def make_debt_chart(metrics):
    labels = ["Debt-to-Equity", "Current Ratio"]
    actual = [metrics.get("debt_to_equity") or 0, metrics.get("current_ratio") or 0]
    benchmark = [0, 2.0]  # 0 D/E and 2.0 current ratio are the "ideal" reference points
    return bar_actual_vs_benchmark("Debt", labels, actual, benchmark)


def make_cashflow_chart(metrics):
    fcf = metrics.get("free_cashflow")
    ocf = metrics.get("operating_cashflow")
    market_cap = metrics.get("market_cap")

    cash_yield = (fcf / market_cap * 100) if fcf and market_cap else 0
    conversion = (fcf / ocf * 100) if fcf and ocf else 0

    labels = ["Cash Yield (FCF/Mkt Cap)", "FCF Conversion (FCF/OCF)"]
    actual = [cash_yield, conversion]
    benchmark = [3, 70]
    return bar_actual_vs_benchmark("Cash Flow", labels, actual, benchmark, "%")


def make_radar_chart(category_scores):
    labels = [c.replace("_", " ").title() for c in category_scores.keys()]
    values = list(category_scores.values())
    # Close the loop for a proper radar polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=labels_closed, fill="toself",
        line=dict(color=COLOR_ACTUAL), fillcolor="rgba(34, 197, 94, 0.35)",
        name="Category Scores",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        polar=dict(
            bgcolor=COLOR_CARD,
            radialaxis=dict(visible=True, range=[0, 100], color=COLOR_TEXT),
            angularaxis=dict(color=COLOR_TEXT),
        ),
        showlegend=False, title="Score Story — All Five Categories", height=400,
        title_font_size=15,
    )
    return fig


def make_score_gauge(overall_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_score,
        title={"text": "Overall Investment Score"},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLOR_TEXT},
            "bar": {"color": COLOR_ACTUAL},
            "steps": [
                {"range": [0, 40], "color": GAUGE_COLORWAY[0]},
                {"range": [40, 60], "color": GAUGE_COLORWAY[1]},
                {"range": [60, 80], "color": GAUGE_COLORWAY[2]},
                {"range": [80, 100], "color": GAUGE_COLORWAY[3]},
            ],
        },
    ))
    fig.update_layout(template=PLOTLY_TEMPLATE, height=300, title_font_size=15)
    return fig


# ---------------------------------------------------------------------
# Main display
# ---------------------------------------------------------------------

if run_button and ticker_input:
    with st.spinner(f"Pulling data for {ticker_input.upper()}..."):
        try:
            metrics = get_company_metrics(ticker_input.upper())
            result = calculate_investment_score(metrics)
        except Exception as e:
            st.error(f"Couldn't retrieve data for '{ticker_input}': {e}")
            st.stop()

    if not metrics.get("name"):
        st.warning("No data found for that ticker — double-check the symbol and try again.")
        st.stop()

    st.subheader(f"{result['name']} ({result['ticker']})")

    left_col, right_col = st.columns([1, 2.4])

    # Left panel: overall score gauge + radar "score story", stacked
    with left_col:
        with st.container(border=True):
            st.plotly_chart(make_score_gauge(result["overall_score"]), use_container_width=True)
        with st.container(border=True):
            st.plotly_chart(make_radar_chart(result["category_scores"]), use_container_width=True)

    # Right panel: 3-across top row, 2-centered bottom row of category charts
    with right_col:
        top_row = st.columns(3)
        with top_row[0]:
            with st.container(border=True):
                st.plotly_chart(make_revenue_chart(metrics), use_container_width=True)
        with top_row[1]:
            with st.container(border=True):
                st.plotly_chart(make_profitability_chart(metrics), use_container_width=True)
        with top_row[2]:
            with st.container(border=True):
                st.plotly_chart(make_valuation_chart(metrics), use_container_width=True)

        bottom_row = st.columns([1, 3, 3, 1])
        with bottom_row[1]:
            with st.container(border=True):
                st.plotly_chart(make_debt_chart(metrics), use_container_width=True)
        with bottom_row[2]:
            with st.container(border=True):
                st.plotly_chart(make_cashflow_chart(metrics), use_container_width=True)

    with st.expander("See raw financial metrics"):
        st.json(metrics)

    st.caption(
        "This is a first-pass screening tool, not investment advice. "
        "Scores are based on a rules-based model with equal 20% weighting "
        "across categories, benchmarked for large technology companies."
    )

st.divider()
st.caption("Built by Avnika Nayee — github.com/akn007-code")
