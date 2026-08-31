"""
chains.py
---------
Builds the ChatOpenAI model, wraps it in a reusable LLMChain for the
structured JSON financial analysis, and exposes a streaming generator for
the human-readable narrative.

The OpenAI API key is passed in at call time (from st.session_state,
entered by the user on the key-entry screen in app.py) rather than read
only from a .env file, so each user can supply their own key.
"""

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from src.config import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from src.prompts import (
    ANALYSIS_CHAT_TEMPLATE,
    NARRATIVE_CHAT_TEMPLATE,
)


def build_llm(api_key: str, streaming: bool = False, temperature: float = DEFAULT_TEMPERATURE) -> ChatOpenAI:
    """Create a ChatOpenAI instance using the given API key."""
    if not api_key or not api_key.strip():
        raise ValueError("No OpenAI API key was provided.")
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=temperature,
        api_key=api_key.strip(),
        streaming=streaming,
    )


def build_analysis_chain(llm: ChatOpenAI) -> LLMChain:
    """The required reusable LLMChain for the structured financial analysis."""
    return LLMChain(llm=llm, prompt=ANALYSIS_CHAT_TEMPLATE)


def run_analysis(inputs: dict, api_key: str) -> str:
    """Run the structured JSON analysis chain and return the raw text."""
    llm = build_llm(api_key, streaming=False)
    chain = build_analysis_chain(llm)
    result = chain.invoke(inputs)
    return result["text"]


def stream_recommendations(inputs: dict, api_key: str):
    """
    Generator that yields chunks of the human-readable narrative as they
    arrive from the model, for use with st.write_stream().

    Usage inside app.py:
        st.write_stream(stream_recommendations(inputs, api_key))
    """
    llm = build_llm(api_key, streaming=True)
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content


def test_api_key(api_key: str) -> tuple:
    """
    Makes a tiny, cheap call to confirm the key actually works before
    letting the user into the main app. Returns (is_valid, error_message).
    """
    try:
        llm = build_llm(api_key, streaming=False, temperature=0)
        llm.invoke("Say OK.")
        return True, None
    except Exception as exc:
        return False, str(exc)
