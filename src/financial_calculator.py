"""
financial_calculator.py
------------------------
Pure, deterministic Python math. NO AI/LLM calls happen in this file —
that separation is a specific assignment requirement so students can see
exactly which numbers come from arithmetic and which come from the model.

Given the same inputs, these functions always return the same outputs.
"""

from src.config import EXPENSE_CATEGORIES


def calculate_totals(monthly_income: float, expenses: dict, savings: float) -> dict:
    """
    Compute total_expenses, remaining_income, savings_ratio, expense_ratio.
    Guards against divide-by-zero when income is 0.
    """
    total_expenses = sum(expenses.values())
    remaining_income = monthly_income - total_expenses

    if monthly_income > 0:
        savings_ratio = (savings / monthly_income) * 100
        expense_ratio = (total_expenses / monthly_income) * 100
    else:
        savings_ratio = 0.0
        expense_ratio = 0.0 if total_expenses == 0 else 100.0

    return {
        "total_expenses": round(total_expenses, 2),
        "remaining_income": round(remaining_income, 2),
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
    }


def calculate_preliminary_score(monthly_income: float, expenses: dict, savings: float,
                                 totals: dict) -> int:
    """
    A simple, transparent 0-100 heuristic score, built from four weighted
    components. This is intentionally rule-based (not AI) so the app has a
    deterministic baseline the LLM's narrative can build on.

    Weights:
      - Savings ratio      : 35 points max
      - Remaining income   : 25 points max  (as % of income, leftover after expenses)
      - Expense ratio       : 25 points max  (lower expense ratio = higher score)
      - Debt burden         : 15 points max  (lower debt share of income = higher score)
    """
    if monthly_income <= 0:
        return 0

    savings_ratio = totals["savings_ratio"]
    expense_ratio = totals["expense_ratio"]
    remaining_income = totals["remaining_income"]
    debt = expenses.get("debt", 0)

    # Savings ratio component (target: 20%+ savings is "full marks")
    savings_score = min(savings_ratio / 20.0, 1.0) * 35

    # Remaining-income component (target: 20%+ of income left over)
    remaining_pct = (remaining_income / monthly_income) * 100
    remaining_score = max(0.0, min(remaining_pct / 20.0, 1.0)) * 25

    # Expense ratio component (target: under 70% of income spent = full marks)
    if expense_ratio <= 70:
        expense_score = 25
    elif expense_ratio >= 120:
        expense_score = 0
    else:
        expense_score = 25 * (1 - (expense_ratio - 70) / 50)

    # Debt-burden component (target: debt under 15% of income = full marks)
    debt_ratio = (debt / monthly_income) * 100
    if debt_ratio <= 15:
        debt_score = 15
    elif debt_ratio >= 50:
        debt_score = 0
    else:
        debt_score = 15 * (1 - (debt_ratio - 15) / 35)

    total_score = savings_score + remaining_score + expense_score + debt_score
    return int(round(max(0, min(100, total_score))))


def build_expense_breakdown_text(expenses: dict, total_expenses: float) -> str:
    """Human-readable, sorted breakdown string for the prompt."""
    label_map = dict(EXPENSE_CATEGORIES)
    lines = []
    sorted_items = sorted(expenses.items(), key=lambda kv: kv[1], reverse=True)
    for key, amount in sorted_items:
        if amount <= 0:
            continue
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        label = label_map.get(key, key.title())
        lines.append(f"{label}: {amount:,.2f} ({pct:.1f}% of expenses)")
    return "; ".join(lines) if lines else "No expenses entered."


def run_full_calculation(monthly_income: float, expenses: dict, savings: float) -> dict:
    """Convenience wrapper that returns every deterministic figure at once."""
    totals = calculate_totals(monthly_income, expenses, savings)
    score = calculate_preliminary_score(monthly_income, expenses, savings, totals)
    breakdown = build_expense_breakdown_text(expenses, totals["total_expenses"])
    return {
        "monthly_income": monthly_income,
        "savings": savings,
        "total_expenses": totals["total_expenses"],
        "remaining_income": totals["remaining_income"],
        "savings_ratio": totals["savings_ratio"],
        "expense_ratio": totals["expense_ratio"],
        "preliminary_score": score,
        "expense_breakdown": breakdown,
    }
