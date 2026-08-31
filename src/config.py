"""
config.py
---------
Holds static configuration: form options, app identity, disclaimers, and
an optional fallback API key loaded from .env for local development.

The primary way a user supplies an API key is the in-app key-entry screen
(see app.py) — .env is never required.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------
# API / model settings
# ---------------------------------------------------------------------
OPENAI_API_KEY_FROM_ENV = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.3

APP_NAME = "FinWise AI"
APP_TAGLINE = "AI-Powered Personal Financial Analysis & Smart Budget Assistant"

# ---------------------------------------------------------------------
# Disclaimer text (used on every relevant screen)
# ---------------------------------------------------------------------
FINANCIAL_DISCLAIMER = (
    "⚠️ **FinWise AI is an educational prototype, not a financial advisor.** "
    "It does not provide guaranteed investment advice, does not connect to "
    "real bank accounts, and does not execute transactions. Nothing here is "
    "a guarantee of any financial outcome. For real financial decisions, "
    "please consult a qualified, licensed financial professional."
)

# ---------------------------------------------------------------------
# Form options
# ---------------------------------------------------------------------
EXPENSE_CATEGORIES = [
    ("housing", "Housing / Rent"),
    ("food", "Food"),
    ("transportation", "Transportation"),
    ("utilities", "Utilities"),
    ("education", "Education"),
    ("healthcare", "Healthcare"),
    ("entertainment", "Entertainment"),
    ("debt", "Loan / Debt payments"),
    ("insurance", "Insurance"),
    ("other", "Other"),
]

FINANCIAL_GOAL_OPTIONS = [
    "Save money", "Build an emergency fund", "Pay off debt",
    "Save for a vacation", "Start a business", "Improve budgeting",
]

CURRENCY_OPTIONS = ["USD ($)", "PKR (₨)", "EUR (€)", "GBP (£)", "AED (د.إ)", "INR (₹)"]

RISK_COLORS = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "CRITICAL": "🔴",
}

CACHE_OPTIONS = ["No caching", "In-Memory Cache", "SQLite Cache"]

SQLITE_CACHE_PATH = ".langchain_cache.db"
