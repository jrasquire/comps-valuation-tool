# Private Company Comps Valuation Assistant

A small tool that helps value a private company using public market comps,
with Claude drafting the plain-English valuation memo.

**How it works**
1. You enter a private target company's revenue/EBITDA and a short description.
2. You enter tickers for a few public comparable companies.
3. The app pulls live market data via the Alpha Vantage API and gets each
   comp's EV/Revenue and EV/EBITDA multiples directly.
4. It applies the median/average multiples to the target's financials to get
   an implied valuation range.
5. It sends the numbers to Claude, which drafts a short valuation memo —
   including caveats about the limitations of a simple comps approach
   (e.g. private companies typically trade at a liquidity discount vs.
   public comps).

## Setup

```bash
# 1. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate    # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API keys
cp .env.example .env
# then edit .env and paste in:
#   - your Anthropic key from https://console.anthropic.com/
#   - a free Alpha Vantage key from https://www.alphavantage.co/support/#api-key
```

## Run it

```bash
streamlit run app.py
```

This opens the app in your browser (usually http://localhost:8501).

## Deploying (e.g. Streamlit Community Cloud)

Add both `ANTHROPIC_API_KEY` and `ALPHA_VANTAGE_API_KEY` as secrets in your
hosting platform's settings — never commit your `.env` file to GitHub.

## Example inputs to try

- **Target:** a Series B robotics/automation startup, $20M revenue, $2M EBITDA
- **Comps:** `IRBT, TER, ROK` (public industrial automation/robotics companies)

Swap in comps from whatever sector matches the company you're evaluating —
just make sure the tickers are real and currently listed.

## Notes / limitations

- **Alpha Vantage's free tier is rate-limited** (around 25 requests/day,
  5/minute as of writing). Each comp ticker uses one request. If you hit
  the limit, wait a bit and try again, or use fewer comps at once.
- Not every ticker will have EBITDA populated; the app skips those
  gracefully and computes whatever multiples it can.
- This is a simplified comps model for demonstration purposes — real deal
  analysis would also consider growth rates, margins, capital structure,
  and comp selection quality far more rigorously.
- An earlier version of this app used `yfinance` (free, no API key), but
  it's unreliable on cloud hosts because Yahoo Finance rate-limits/blocks
  shared server IP ranges. Alpha Vantage's API-key-based access is more
  reliable for a deployed app, at the cost of a lower daily request limit.

## Possible next steps

- Auto-suggest comp tickers based on sector/industry instead of typing them in.
- Add EV/EBIT and P/E multiples.
- Let the user upload target financials from a CSV/Excel file instead of
  typing them in manually.
- Cache comp data so repeated runs don't re-hit the API every time.
