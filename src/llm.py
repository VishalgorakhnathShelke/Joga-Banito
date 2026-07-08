# src/llms.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)


def get_gemini_llm():
    """
    Create and return the Gemini LLM.

    This model will be used for Agent 1:
    CA Tax Guidance Agent.
    """
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.3,
    )


def get_groq_llm():
    """
    Create and return the Groq LLM.

    This model will be used for Agent 2:
    Senior CA Compliance Review Agent.
    """
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.2,
    )


if __name__ == "__main__":
    gemini_llm = get_gemini_llm()
    groq_llm = get_groq_llm()

    print("LLMs loaded successfully.")
    print(f"Gemini model: {GEMINI_MODEL}")
    print(f"Groq model: {GROQ_MODEL}")
