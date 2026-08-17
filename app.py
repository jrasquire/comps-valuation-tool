"""
Private Company Comps Valuation Assistant
------------------------------------------
Pulls market data for public comparable companies, computes valuation
multiples (EV/Revenue, EV/EBITDA), applies them to a private target
company's financials, and uses Claude to generate a plain-English
valuation memo.

Run locally with:
    streamlit run app.py

Requires an Anthropic API key set as the ANTHROPIC_API_KEY environment
variable (see .env.example).
"""

import os
import statistics
from dataclasses import dataclass, field

import streamlit as st
import yfinance as yf
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Comps Valuation Assistant", layout="wide")


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------

@dataclass
class CompData:
    ticker: str
    name: str = ""
    market_cap: float | None = None
    enterprise_value: float | None = None
    revenue: float | None = None
    ebitda: float | None = None
    ev_revenue: float | None = None
    ev_ebitda: float | None = None
    error: str | None = None


# ---------------------------------------------------------------------
# Data fetching + multiple calculation
# ---------------------------------------------------------------------

def fetch_comp(ticker: str) -> CompData:
    """Pull key financials for one public comparable via yfinance."""
    comp = CompData(ticker=ticker.upper())
    try:
        t = yf.Ticker(comp.ticker)
        info = t.info

        comp.name = info.get("shortName", comp.ticker)
        comp.market_cap = info.get("marketCap")
        comp.enterprise_value = info.get("enterpriseValue")
        comp.revenue = info.get("totalRevenue")
        comp.ebitda = info.get("ebitda")

        if comp.enterprise_value and comp.revenue:
            comp.ev_revenue = comp.enterprise_value / comp.revenue
        if comp.enterprise_value and comp.ebitda and comp.ebitda > 0:
            comp.ev_ebitda = comp.enterprise_value / comp.ebitda

        if comp.ev_revenue is None and comp.ev_ebitda is None:
            comp.error = "No usable revenue/EBITDA data returned."

    except Exception as e:  # noqa: BLE001 - surface any fetch issue to the UI
        comp.error = str(e)

    return comp


def summarize_multiples(comps: list[CompData]) -> dict:
    """Compute median/average multiples across comps with valid data."""
    ev_rev = [c.ev_revenue for c in comps if c.ev_revenue]
    ev_ebitda = [c.ev_ebitda for c in comps if c.ev_ebitda]

    return {
        "ev_revenue_median": statistics.median(ev_rev) if ev_rev else None,
        "ev_revenue_avg": statistics.mean(ev_rev) if ev_rev else None,
        "ev_ebitda_median": statistics.median(ev_ebitda) if ev_ebitda else None,
        "ev_ebitda_avg": statistics.mean(ev_ebitda) if ev_ebitda else None,
    }


def implied_valuation(target_revenue, target_ebitda, mult_summary):
    """Apply comp multiples to the target's financials for an implied range."""
    results = {}

    if target_revenue and mult_summary["ev_revenue_median"]:
        results["EV/Revenue (median)"] = target_revenue * mult_summary["ev_revenue_median"]
    if target_revenue and mult_summary["ev_revenue_avg"]:
        results["EV/Revenue (avg)"] = target_revenue * mult_summary["ev_revenue_avg"]
    if target_ebitda and mult_summary["ev_ebitda_median"]:
        results["EV/EBITDA (median)"] = target_ebitda * mult_summary["ev_ebitda_median"]
    if target_ebitda and mult_summary["ev_ebitda_avg"]:
        results["EV/EBITDA (avg)"] = target_ebitda * mult_summary["ev_ebitda_avg"]

    return results


# ---------------------------------------------------------------------
# Claude-generated narrative
# ---------------------------------------------------------------------

def generate_memo(target_name, target_desc, target_revenue, target_ebitda,
                   comps: list[CompData], mult_summary, valuation_range) -> str:
    """Call Claude to turn the numbers into a plain-English valuation memo."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ("_(No ANTHROPIC_API_KEY found — set it in your environment "
                "or a .env file to enable the AI-generated memo.)_")

    client = Anthropic(api_key=api_key)

    comp_lines = "\n".join(
        f"- {c.name} ({c.ticker}): EV/Revenue = "
        f"{c.ev_revenue:.2f}x" if c.ev_revenue else f"- {c.name} ({c.ticker}): EV/Revenue = n/a"
        for c in comps if not c.error
    )

    prompt = f"""You are a private markets analyst. Write a concise, plain-English
valuation memo (roughly 200-300 words) for the following private company,
based on comparable public company multiples. Be direct about assumptions
and limitations of this simplified comps approach (e.g. small private
companies often trade at a discount to public comps for liquidity reasons).

Target company: {target_name}
Description: {target_desc}
Target revenue: {target_revenue}
Target EBITDA: {target_ebitda}

Comparable companies and EV/Revenue multiples:
{comp_lines}

Summary multiples: {mult_summary}
Implied valuation range from applying these multiples: {valuation_range}

Structure the memo with: (1) a one-line valuation takeaway, (2) key
assumptions, (3) a couple of risks or caveats an analyst should flag."""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    return "".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------

st.title("📊 Private Company Comps Valuation Assistant")
st.caption(
    "Enter a private target company's financials and a handful of public "
    "comparables. The tool computes implied valuation multiples and uses "
    "Claude to draft a plain-English valuation memo."
)

with st.sidebar:
    st.header("Target company")
    target_name = st.text_input("Company name", "Acme Robotics Inc.")
    target_desc = st.text_area(
        "Short description",
        "Series B industrial robotics startup selling automation hardware "
        "and software subscriptions to warehouses.",
    )
    target_revenue = st.number_input("Annual revenue (USD)", min_value=0.0,
                                      value=20_000_000.0, step=1_000_000.0)
    target_ebitda = st.number_input("Annual EBITDA (USD, can be negative)",
                                     value=2_000_000.0, step=500_000.0)

    st.header("Comparable public companies")
    comp_input = st.text_area(
        "Tickers (comma-separated)",
        "IRBT, TER, ROK",
        help="Use real, currently-listed tickers of public companies in a similar sector.",
    )

    run = st.button("Run valuation", type="primary")

if run:
    tickers = [t.strip() for t in comp_input.split(",") if t.strip()]

    if not tickers:
        st.warning("Add at least one comparable ticker.")
        st.stop()

    with st.spinner("Pulling market data for comparables..."):
        comps = [fetch_comp(t) for t in tickers]

    st.subheader("Comparable companies")
    table_rows = []
    for c in comps:
        if c.error:
            st.warning(f"{c.ticker}: {c.error}")
        table_rows.append({
            "Ticker": c.ticker,
            "Name": c.name,
            "Market Cap": c.market_cap,
            "Enterprise Value": c.enterprise_value,
            "Revenue": c.revenue,
            "EBITDA": c.ebitda,
            "EV/Revenue": round(c.ev_revenue, 2) if c.ev_revenue else None,
            "EV/EBITDA": round(c.ev_ebitda, 2) if c.ev_ebitda else None,
        })
    st.dataframe(table_rows, use_container_width=True)

    mult_summary = summarize_multiples(comps)
    st.subheader("Summary multiples")
    st.json(mult_summary)

    valuation_range = implied_valuation(target_revenue, target_ebitda, mult_summary)
    st.subheader("Implied valuation range")
    if valuation_range:
        st.dataframe(
            [{"Method": k, "Implied EV (USD)": f"{v:,.0f}"} for k, v in valuation_range.items()],
            use_container_width=True,
        )
    else:
        st.info("Not enough comp data to compute an implied valuation. Try different tickers.")

    st.subheader("🧠 AI-generated valuation memo")
    with st.spinner("Asking Claude to draft the memo..."):
        memo = generate_memo(
            target_name, target_desc, target_revenue, target_ebitda,
            comps, mult_summary, valuation_range,
        )
    st.markdown(memo)

else:
    st.info("Fill in the target company and comps in the sidebar, then click **Run valuation**.")
