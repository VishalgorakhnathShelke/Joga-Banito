# src/agents.py

from llm import get_gemini_llm, get_groq_llm
# from .llm import get_gemini_llm, get_groq_llm
from prompts import CA_AGENT_PROMPT, COMPLIANCE_AGENT_PROMPT
from config import (
    COUNTRY,
    TAX_AUTHORITY,
    REGULATOR,
    DEFAULT_TAX_YEAR,
)


def extract_response_text(response) -> str:
    """
    LangChain model responses usually return an object with .content.
    This helper safely extracts the text.
    """
    if hasattr(response, "content"):
        return response.content

    return str(response)


def run_ca_guidance_agent(user_question: str) -> str:
    """
    Agent 1:
    Uses Gemini as the CA Tax Guidance Agent.

    It gives the first tax guidance answer.
    """

    gemini_llm = get_gemini_llm()

    prompt = CA_AGENT_PROMPT.format(
        country=COUNTRY,
        tax_authority=TAX_AUTHORITY,
        regulator=REGULATOR,
        tax_year=DEFAULT_TAX_YEAR,
        user_question=user_question,
    )

    response = gemini_llm.invoke(prompt)

    return extract_response_text(response)


def run_compliance_review_agent(user_question: str, ca_agent_answer: str) -> str:
    """
    Agent 2:
    Uses Groq as the Senior CA Compliance Review Agent.

    It reviews Agent 1's answer and produces the final safer response.
    """

    groq_llm = get_groq_llm()

    prompt = COMPLIANCE_AGENT_PROMPT.format(
        user_question=user_question,
        ca_agent_answer=ca_agent_answer,
    )

    response = groq_llm.invoke(prompt)

    return extract_response_text(response)


if __name__ == "__main__":
    test_question = "I bought a laptop for university and part-time work. Can I claim it in my Australian tax return?"

    print("\nRunning Agent 1: CA Tax Guidance Agent...\n")
    ca_answer = run_ca_guidance_agent(test_question)
    print(ca_answer)

    print("\n" + "=" * 80 + "\n")

    print("Running Agent 2: Senior Compliance Review Agent...\n")
    final_answer = run_compliance_review_agent(test_question, ca_answer)
    print(final_answer)