"""
utils.py
--------
Safe JSON parsing so a malformed model response never crashes the
Streamlit app, plus a couple of small display helpers.
"""

import json
import re

REQUIRED_KEYS = [
    "financial_summary",
    "financial_health_score",
    "spending_analysis",
    "risk_level",
    "top_priorities",
    "budget_recommendations",
    "savings_strategy",
    "next_month_action_plan",
]

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def strip_code_fences(text: str) -> str:
    """Remove accidental ```json ... ``` fences the model sometimes adds."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    return text


def safe_parse_analysis(raw_text: str):
    """
    Try to parse the model's raw output into the expected analysis dict.

    Returns a tuple: (parsed_dict_or_None, error_message_or_None)
    Never raises — callers can always safely branch on the first element.
    """
    cleaned = strip_code_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return None, f"The AI response was not valid JSON ({exc}). Raw output is shown below for debugging."

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        return None, f"The AI response is missing required fields: {', '.join(missing)}."

    if data["risk_level"] not in VALID_RISK_LEVELS:
        data["risk_level"] = "MEDIUM"

    try:
        data["financial_health_score"] = max(0, min(100, int(data["financial_health_score"])))
    except (TypeError, ValueError):
        data["financial_health_score"] = 50

    return data, None


def risk_to_streamlit_kind(risk_level: str) -> str:
    """Map a risk level to a Streamlit alert function name."""
    mapping = {
        "LOW": "success",
        "MEDIUM": "info",
        "HIGH": "warning",
        "CRITICAL": "error",
    }
    return mapping.get(risk_level, "info")


def score_band_label(score: int) -> str:
    """Educational score band, per the assignment spec."""
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Generally healthy"
    if score >= 40:
        return "Needs improvement"
    return "High attention"
