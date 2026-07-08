# src/llms.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)


def get_gemini_llm():
    """
    Gemini is used as Agent 1:
    CA Tax Guidance Agent.
    """
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.3,
    )


def get_groq_llm():
    """
    Groq is used as Agent 2:
    Senior CA Compliance Review Agent.
    """
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.2,
    )


def extract_response_text(response) -> str:
    """
    Safely extract text from LangChain response objects.
    """
    if hasattr(response, "content"):
        return response.content

    return str(response)


if __name__ == "__main__":
    gemini_llm = get_gemini_llm()
    groq_llm = get_groq_llm()

    print("LLMs loaded successfully.")
    print(f"Gemini model: {GEMINI_MODEL}")
    print(f"Groq model: {GROQ_MODEL}")