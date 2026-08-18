# 📊 Private Company Comps Valuation Assistant

An interactive valuation analysis tool that bridges real-time equity market data with LLM narrative synthesis. It pulls financial metrics for public comparable companies, computes valuation multiples (EV/Revenue, EV/EBITDA), applies them to a private target company, and uses Anthropic's Claude to draft a structured investment valuation memo.

---

## 🚀 Live Demo
👉 **[Launch the Live App](https://comps-valuation-tool.streamlit.app/)** *(Replace with your actual Streamlit link)*

---

## 💡 How It Works

1. **Target Company Inputs:** Enter the target's financial profile (Annual Revenue, EBITDA, and business model description).
2. **Real-Time Market Data Ingestion:** Input public comparable tickers (e.g., `SYM, TER, CGNX, ROK`). The app fetches enterprise values, revenues, EBITDAs, and market caps via `yfinance`.
3. **Deterministic Multiples Engine:** Calculates median and benchmark average multiples across valid comps, handling missing data or negative margins gracefully.
4. **Implied Valuation Range:** Applies comp multiples to target financials to generate implied enterprise value benchmarks.
5. **AI Investment Memo Synthesis:** Prompts Claude to produce a plain-English valuation memo covering:
   - **One-Line Valuation Takeaway**
   - **Key Valuation Assumptions**
   - **Risks, Caveats & Liquidity Haircuts**

---

## 🛠️ Tech Stack

- **Frontend / Framework:** [Streamlit](https://streamlit.io/)
- **Market Data Engine:** [yfinance](https://github.com/ranaroussi/yfinance) (Zero API key required; full market coverage)
- **AI / LLM Layer:** [Anthropic Claude API](https://docs.anthropic.com/) (`claude-haiku-4-5` with model fallback)
- **Environment Management:** `python-dotenv`

---

## ⚙️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/jrasquire/comps-valuation-tool.git
cd comps-valuation-tool