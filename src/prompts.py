"""
prompts.py
----------
Financial-assistant system prompt, JSON schema instructions, a reusable
PromptTemplate, and ChatPromptTemplates (System + Human) that carry the
deterministic calculations (from financial_calculator.py) into the LLM.
"""

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ---------------------------------------------------------------------
# 1. Safety system prompt
# ---------------------------------------------------------------------
SYSTEM_SAFETY_RULES = """You are FinWise AI, an educational personal-finance
assistant embedded in a prototype app. You are NOT a licensed financial
advisor and must never claim to be one.

Non-negotiable rules you must always follow:
- NEVER guarantee any financial outcome or investment return.
- NEVER recommend specific stocks, cryptocurrencies, or investment products.
- NEVER claim to execute transactions, move money, or connect to real
  accounts — you only give general, educational observations.
- ALWAYS recommend that the user consult a qualified, licensed financial
  professional for real decisions.
- Be encouraging and non-judgmental, even when the numbers are concerning.
  Frame problems as opportunities to improve, not failures.
- Use the deterministic numbers you are given (already calculated in
  Python) as ground truth — do not recompute or contradict them.
- If remaining income is negative or the expense ratio is over 100%, treat
  this as a meaningful financial-risk signal and set risk_level to HIGH or
  CRITICAL accordingly, with urgent-but-constructive next steps.
"""

# ---------------------------------------------------------------------
# 2. JSON schema instructions
# ---------------------------------------------------------------------
JSON_SCHEMA_INSTRUCTIONS = """You must respond with ONLY a single valid JSON
object and nothing else — no markdown fences, no preamble, no explanation
outside the JSON. Match this exact structure and key names:

{{
  "financial_summary": "one or two sentence plain-language summary of the user's situation",
  "financial_health_score": 0,
  "spending_analysis": [ {{ "category": "string", "observation": "string", "recommendation": "string" }} ],
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "top_priorities": ["string", "string"],
  "budget_recommendations": ["string", "string"],
  "savings_strategy": ["string", "string"],
  "next_month_action_plan": ["string", "string"]
}}

Rules for the JSON:
- "financial_health_score" must be an integer 0-100. Use the preliminary
  score you were given as your starting point; you may adjust it slightly
  based on qualitative context (e.g. financial goal), but stay close to it.
- "spending_analysis" should cover the 2-4 largest expense categories.
- "risk_level" must be exactly one of: LOW, MEDIUM, HIGH, CRITICAL.
- All list fields must contain at least one item.
- Do not wrap the JSON in ```json fences. Return raw JSON only.
"""

# ---------------------------------------------------------------------
# 3. PromptTemplate — reusable single-string template
# ---------------------------------------------------------------------
FINANCIAL_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "monthly_income", "total_expenses", "remaining_income", "savings",
        "savings_ratio", "expense_ratio", "financial_goal",
        "expense_breakdown", "preliminary_score", "currency",
    ],
    template="""Financial information (currency: {currency}):
- Monthly income: {monthly_income}
- Total expenses: {total_expenses}
- Remaining income after expenses: {remaining_income}
- Current monthly savings: {savings}
- Savings ratio: {savings_ratio}%
- Expense ratio: {expense_ratio}%
- Preliminary rule-based score (0-100, calculated in Python): {preliminary_score}
- Expense breakdown: {expense_breakdown}
- Financial goal: {financial_goal}

Please analyse this situation and produce the structured guidance
described in your instructions.""",
)

# ---------------------------------------------------------------------
# 4. ChatPromptTemplate — System + Human, for the structured JSON call
# ---------------------------------------------------------------------
ANALYSIS_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_SAFETY_RULES + "\n" + JSON_SCHEMA_INSTRUCTIONS),
    ("human", FINANCIAL_PROMPT_TEMPLATE.template),
])

# ---------------------------------------------------------------------
# 5. ChatPromptTemplate — used purely for the streamed narrative
# ---------------------------------------------------------------------
NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_SAFETY_RULES + """
Write a short, warm, encouraging narrative paragraph (4-6 sentences)
summarising the user's financial situation and general direction in plain
language. Do NOT output JSON here — plain prose only. Always end by
reminding the user this is educational, not professional financial
advice."""),
    ("human", FINANCIAL_PROMPT_TEMPLATE.template),
])


def build_prompt_inputs(calc: dict, financial_goal: str, currency: str) -> dict:
    """Merge the deterministic calculation dict with the remaining prompt vars."""
    return {
        "monthly_income": f"{calc['monthly_income']:,.2f}",
        "total_expenses": f"{calc['total_expenses']:,.2f}",
        "remaining_income": f"{calc['remaining_income']:,.2f}",
        "savings": f"{calc['savings']:,.2f}",
        "savings_ratio": calc["savings_ratio"],
        "expense_ratio": calc["expense_ratio"],
        "preliminary_score": calc["preliminary_score"],
        "expense_breakdown": calc["expense_breakdown"],
        "financial_goal": financial_goal,
        "currency": currency,
    }


def demo_raw_messages(summary_text: str) -> list:
    """
    Learning-objective helper: shows System/Human/AIMessage used directly
    (without a template), so students can see how a raw conversation is
    built and how an AIMessage would slot back in for a follow-up turn.
    """
    return [
        SystemMessage(content=SYSTEM_SAFETY_RULES),
        HumanMessage(content=f"Here is my financial situation: {summary_text}"),
        # In a real multi-turn chat you'd append the model's previous reply
        # back into the list like this before asking a follow-up question:
        # AIMessage(content=previous_response_text),
    ]
