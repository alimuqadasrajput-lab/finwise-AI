"""
app.py
------
FinWise AI — Streamlit entry point.

Run with:  streamlit run app.py

Flow:
  1. First screen: the user enters their own OpenAI API key. It is kept
     only in st.session_state for this browser session — never written to
     disk, never logged.
  2. Once the key is validated, the main financial-analysis interface
     (sidebar + form + dashboard) is shown.

This file is UI-only. Deterministic math lives in
src/financial_calculator.py, and all LangChain / OpenAI logic lives in
src/chains.py and src/prompts.py.
"""

import time
import streamlit as st

from src.config import (
    APP_NAME, APP_TAGLINE, FINANCIAL_DISCLAIMER,
    EXPENSE_CATEGORIES, FINANCIAL_GOAL_OPTIONS, CURRENCY_OPTIONS,
    RISK_COLORS, CACHE_OPTIONS, DEFAULT_MODEL, OPENAI_API_KEY_FROM_ENV,
)
from src.cache_manager import set_cache_mode, get_active_cache_name
from src.financial_calculator import run_full_calculation
from src.prompts import build_prompt_inputs, demo_raw_messages
from src.chains import run_analysis, stream_recommendations, test_api_key
from src.utils import safe_parse_analysis, risk_to_streamlit_kind, score_band_label

st.set_page_config(page_title=APP_NAME, page_icon="💰", layout="wide")

# -----------------------------------------------------------------------
# SESSION STATE DEFAULTS
# -----------------------------------------------------------------------
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = OPENAI_API_KEY_FROM_ENV
if "key_confirmed" not in st.session_state:
    st.session_state.key_confirmed = False


# =========================================================================
# SCREEN 1 - API key entry (shown until a valid key is confirmed)
# =========================================================================
def render_key_entry_screen():
    st.title(f"💰 {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.info(FINANCIAL_DISCLAIMER)

    st.subheader("Connect your OpenAI API key")
    st.write(
        "FinWise AI needs an OpenAI API key to generate financial insights. "
        "Your key is used only for this browser session and is never saved "
        "to disk or sent anywhere except OpenAI."
    )

    with st.form("api_key_form"):
        api_key_input = st.text_input(
            "OpenAI API key",
            value=st.session_state.openai_api_key,
            type="password",
            placeholder="sk-...",
            help="Get a key at platform.openai.com under API keys.",
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Continue", use_container_width=True)
        with col2:
            skip_validation = st.checkbox("Skip validation (faster, less safe)", value=False)

    if submitted:
        if not api_key_input.strip():
            st.warning("Please enter an API key.")
            return

        st.session_state.openai_api_key = api_key_input.strip()

        if skip_validation:
            st.session_state.key_confirmed = True
            st.rerun()
        else:
            with st.spinner("Validating your API key..."):
                is_valid, error = test_api_key(st.session_state.openai_api_key)
            if is_valid:
                st.session_state.key_confirmed = True
                st.rerun()
            else:
                st.error(f"That key didn't work: {error}")

    st.caption(
        "Don't have a key yet? Create one at "
        "[platform.openai.com/api-keys](https://platform.openai.com/api-keys)."
    )


# =========================================================================
# SCREEN 2 - main financial analysis app (only after key is confirmed)
# =========================================================================
def render_main_app():
    api_key = st.session_state.openai_api_key

    # -------------------------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------------------------
    with st.sidebar:
        st.title(f"💰 {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.warning(FINANCIAL_DISCLAIMER)

        st.subheader("Model configuration")
        st.text(f"Model: {DEFAULT_MODEL}")
        cache_mode = st.selectbox("Caching", CACHE_OPTIONS, index=0,
                                   help="InMemoryCache = RAM only, fastest, cleared on restart. "
                                        "SQLiteCache = saved to a .db file, survives restarts.")
        active_cache = set_cache_mode(cache_mode)
        st.caption(f"Active cache: **{active_cache}**")

        st.divider()
        if st.button("🔄 Reset session", use_container_width=True):
            for key in ["last_result", "last_calc"]:
                st.session_state.pop(key, None)
            st.rerun()

        if st.button("🔑 Change API key", use_container_width=True):
            st.session_state.key_confirmed = False
            st.rerun()

        st.divider()
        st.caption("Built for the LangChain + Streamlit FinTech assignment. "
                   "Educational prototype only — not financial advice.")

    # -------------------------------------------------------------------
    # MAIN AREA - header + disclaimer
    # -------------------------------------------------------------------
    st.title(f"{APP_NAME} — Smart Budget Assistant")
    st.info(FINANCIAL_DISCLAIMER)

    st.subheader("Tell us about your finances")

    with st.form("financial_form"):
        col1, col2 = st.columns(2)
        with col1:
            monthly_income = st.number_input("Monthly income", min_value=0.0, step=100.0, value=0.0)
            savings = st.number_input("Current monthly savings", min_value=0.0, step=50.0, value=0.0)
        with col2:
            financial_goal = st.selectbox("Financial goal", FINANCIAL_GOAL_OPTIONS)
            currency = st.selectbox("Currency", CURRENCY_OPTIONS)

        st.write("**Monthly expenses**")
        expenses = {}
        with st.expander("Enter your expenses by category", expanded=True):
            exp_cols = st.columns(2)
            for i, (key, label) in enumerate(EXPENSE_CATEGORIES):
                with exp_cols[i % 2]:
                    expenses[key] = st.number_input(label, min_value=0.0, step=10.0, value=0.0, key=f"exp_{key}")

        submitted = st.form_submit_button("Analyse my finances", use_container_width=True)

    # -------------------------------------------------------------------
    # ON SUBMIT
    # -------------------------------------------------------------------
    if submitted:
        if monthly_income <= 0:
            st.warning("Please enter a monthly income greater than 0.")
            st.stop()

        # ---- Deterministic Python calculations (no AI here) ------------
        calc = run_full_calculation(monthly_income, expenses, savings)
        st.session_state.last_calc = calc

        st.divider()
        st.subheader("📊 Financial overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly income", f"{currency.split()[0]} {monthly_income:,.2f}")
        m2.metric("Total expenses", f"{currency.split()[0]} {calc['total_expenses']:,.2f}")
        m3.metric("Remaining balance", f"{currency.split()[0]} {calc['remaining_income']:,.2f}",
                   delta=f"{calc['savings_ratio']:.1f}% savings ratio")
        m4.metric("Current savings", f"{currency.split()[0]} {savings:,.2f}")

        prompt_inputs = build_prompt_inputs(calc, financial_goal, currency)

        # ---- Structured JSON analysis (LLMChain) ------------------------
        start = time.time()
        try:
            with st.spinner("Analysing your finances..."):
                raw_output = run_analysis(prompt_inputs, api_key)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:  # network / API errors, never crash the app
            st.error(f"Something went wrong calling the AI service: {exc}")
            st.info("If this mentions authentication, your API key may be invalid — "
                     "use **Change API key** in the sidebar to update it.")
            st.stop()
        elapsed = time.time() - start

        data, error = safe_parse_analysis(raw_output)

        st.subheader("🧭 AI-generated recommendation")
        st.write_stream(stream_recommendations(prompt_inputs, api_key))
        st.info(FINANCIAL_DISCLAIMER)

        if error:
            st.error(error)
            with st.expander("Raw AI output (for debugging)"):
                st.code(raw_output)
            st.stop()

        st.subheader("📈 AI financial analysis")

        score = data["financial_health_score"]
        band = score_band_label(score)
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Financial health score", f"{score}/100", delta=band)
        sc2.metric("Risk level", f"{RISK_COLORS.get(data['risk_level'], '')} {data['risk_level']}")
        sc3.metric("Response time", f"{elapsed:.2f}s | cache: {get_active_cache_name()}")
        st.progress(score / 100, text=f"Financial health: {band} ({score}/100)")

        kind = risk_to_streamlit_kind(data["risk_level"])
        getattr(st, kind)(f"**Summary:** {data['financial_summary']}")

        if data["risk_level"] == "CRITICAL":
            st.error("🚨 Your numbers show a critical risk pattern (e.g. spending well beyond income). "
                      "Consider speaking with a licensed financial counselor as soon as possible.")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Spending analysis", "Priorities & budget", "Savings strategy", "Next month's plan",
        ])

        with tab1:
            for item in data["spending_analysis"]:
                with st.expander(f"📂 {item.get('category', 'Category')}"):
                    st.write(f"**Observation:** {item.get('observation', '')}")
                    st.write(f"**Recommendation:** {item.get('recommendation', '')}")

        with tab2:
            st.write("**Top priorities**")
            for p in data["top_priorities"]:
                st.write(f"- {p}")
            st.write("**Budget recommendations**")
            for b in data["budget_recommendations"]:
                st.write(f"- {b}")

        with tab3:
            for s in data["savings_strategy"]:
                st.write(f"- {s}")

        with tab4:
            for step in data["next_month_action_plan"]:
                st.write(f"- {step}")

        st.success("Analysis complete. Submit the same inputs again to see caching speed it up.")
        st.info(FINANCIAL_DISCLAIMER)

        with st.expander("🔧 Developer: raw System/Human/AIMessage demo"):
            st.caption("Shows the LangChain message objects used directly, "
                        "as required by the assignment's learning objectives.")
            demo_msgs = demo_raw_messages(data["financial_summary"])
            for msg in demo_msgs:
                st.write(f"**{msg.__class__.__name__}:** {msg.content}")

        with st.expander("🧮 Developer: raw Python calculation output"):
            st.caption("These figures were computed deterministically in "
                        "financial_calculator.py — no AI involved.")
            st.json(calc)


# =========================================================================
# ROUTER
# =========================================================================
if not st.session_state.key_confirmed:
    render_key_entry_screen()
else:
    render_main_app()
