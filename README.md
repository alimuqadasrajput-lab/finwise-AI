# FinWise AI

An educational Streamlit + LangChain prototype that takes a user's income,
expenses, and savings, computes deterministic financial ratios in Python,
and uses an LLM to produce structured, educational budgeting guidance.

> ⚠️ **This is an educational prototype only.** It does not provide
> guaranteed investment advice, does not connect to real bank accounts, and
> does not execute transactions. Always consult a licensed financial
> professional for real decisions.

## Features

- In-app **API key entry screen** — each user pastes their own OpenAI key
  on first launch; it's kept only in `st.session_state`, never on disk
- Deterministic financial math, fully separated from AI (`financial_calculator.py`)
- `ChatOpenAI` integration via `langchain-openai`
- `PromptTemplate` and `ChatPromptTemplate` (System + Human messages)
- Raw `SystemMessage` / `HumanMessage` / `AIMessage` demo
- Structured JSON output with safe parsing (never crashes on bad JSON)
- Reusable `LLMChain` for the analysis
- Live streaming recommendation via `.stream()` + `st.write_stream`
- Switchable `InMemoryCache` and `SQLiteCache`
- Full FinTech dashboard: metrics, progress bar, tabs, expanders, alerts
- Reset-session button

## Project structure

```
finwise_ai/
├── app.py                     # Streamlit UI - run this
├── requirements.txt
├── .env.example
├── README.md
└── src/
    ├── __init__.py
    ├── config.py                # settings + form options
    ├── financial_calculator.py    # deterministic maths - no AI
    ├── prompts.py                  # PromptTemplate + ChatPromptTemplate + JSON schema
    ├── chains.py                    # ChatOpenAI, LLMChain, streaming
    ├── cache_manager.py              # in-memory + SQLite caching
    └── utils.py                       # safe JSON parsing + helpers
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

No `.env` file is required to run the app. `.env.example` is an *optional*
convenience for local development — copy it to `.env` and fill in a key
if you want the key-entry screen pre-filled automatically.

## Run

```bash
streamlit run app.py
```

The app opens on a **key-entry screen**:

1. Paste your OpenAI API key (get one at
   [platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
2. Click **Continue**. The app makes one tiny test call to confirm the key
   works before letting you in (tick "Skip validation" to bypass this).
3. The key stays only in `st.session_state` for that browser session.

Once inside: enter your income, expenses, savings, financial goal and
currency, pick a caching mode in the sidebar, then click **Analyse my
finances**. Use **🔄 Reset session** or **🔑 Change API key** in the
sidebar at any time.

## Python calculations vs. AI insight

Per the assignment's design, these are kept strictly separate:

- **`financial_calculator.py` (deterministic, no AI):** total expenses,
  remaining income, savings ratio, expense ratio, and a transparent
  0-100 preliminary score built from four weighted components (savings
  ratio, remaining income, expense ratio, debt burden). Given the same
  inputs, this always returns the same output, and guards against
  divide-by-zero when income is 0.
- **The LLM (`prompts.py` + `chains.py`):** takes those already-computed
  numbers as ground truth and adds qualitative, educational insight —
  spending observations, priorities, budget/savings recommendations, and
  a next-month action plan. It does not recompute the numbers.

## Caching: InMemoryCache vs SQLiteCache

Both are registered with `set_llm_cache(...)` from `langchain.globals`;
once registered, LangChain automatically checks the cache for a matching
(prompt, model, params) hash before calling the API.

| | InMemoryCache | SQLiteCache |
|---|---|---|
| Storage | RAM only | A `.db` file on disk |
| Speed | Fastest | Fast, marginally slower than RAM |
| Survives app restart? | No | Yes |
| Best for | Quick repeated calls within one running session | Reusing cached results across multiple runs/days |

To see it in action: pick a cache mode in the sidebar, submit the form,
then submit the **exact same** inputs again — the second run should be
noticeably faster and make no new billed API call.

## Testing scenarios

| # | Input | Expected calculation | Expected AI response |
|---|---|---|---|
| 1 | Income 8000, expenses ~2000 | Large positive remaining; high savings ratio | High score; LOW risk; growth-focused tips |
| 2 | Income 2000, expenses ~2600 | Negative remaining; expense ratio >100% | Low score; HIGH risk; urgent cost-cutting |
| 3 | Income 5000, debt 2500 | High debt share of income | MEDIUM/HIGH risk; debt-reduction priorities |
| 4 | Income 4000, savings 1200 | Savings ratio ~30% | High score; LOW risk; reinforce good habits |
| 5 | Income 3000, expenses 3000 | Remaining = 0 | MEDIUM/HIGH risk; find room to save |

## Notes on safety design

- The system prompt (`src/prompts.py`) hard-codes the safety rules: no
  guaranteed outcomes, no specific investment recommendations, no claim of
  executing real transactions, and always defer to a licensed professional.
- The disclaimer (`src/config.py::FINANCIAL_DISCLAIMER`) is rendered on the
  key-entry screen, the sidebar, the main page, and again in the results.
- `safe_parse_analysis` in `src/utils.py` guarantees a malformed model
  response is shown as a friendly error with the raw text for debugging,
  rather than crashing the app.
