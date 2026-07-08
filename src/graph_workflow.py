# src/graph_workflow.py

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from tavily import TavilyClient

from src.config import (
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS,
    COUNTRY,
    TAX_AUTHORITY,
    REGULATOR,
    DEFAULT_TAX_YEAR,
)

from src.llm import get_gemini_llm, get_groq_llm, extract_response_text
from src.prompts import CA_AGENT_PROMPT, COMPLIANCE_AGENT_PROMPT


class TaxAgentState(TypedDict):
    """
    Shared state for the LangGraph workflow.
    Each node reads from this state and returns updates to it.
    """

    user_question: str
    include_reddit: bool

    agent_1_official_sources: str
    agent_1_reddit_context: str
    agent_1_answer: str

    agent_2_official_sources: str
    agent_2_reddit_context: str
    final_answer: str


def get_tavily_client() -> TavilyClient:
    """
    Create Tavily client.
    """
    return TavilyClient(api_key=TAVILY_API_KEY)


def format_search_results(results: list[dict]) -> str:
    """
    Convert Tavily search results into clean source text for the LLM.
    """

    if not results:
        return "No relevant search results found."

    formatted_results = []

    for index, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        url = item.get("url", "No URL")
        content = item.get("content", "")

        formatted_results.append(
            f"""
Source {index}
Title: {title}
URL: {url}
Content:
{content}
""".strip()
        )

    return "\n\n".join(formatted_results)


def search_with_domains(query: str, domains: list[str], max_results: int) -> str:
    """
    Search only selected domains.
    Example domains:
    - ato.gov.au
    - tpb.gov.au
    - reddit.com
    """

    client = get_tavily_client()

    response = client.search(
        query=query,
        search_depth="advanced",
        include_domains=domains,
        include_raw_content="text",
        max_results=max_results,
        country="australia",
    )

    results = response.get("results", [])

    return format_search_results(results)


def search_agent_1_sources(state: TaxAgentState) -> dict:
    """
    Node 1:
    Search official ATO/TPB sources.
    Search Reddit only if user selected that option.
    """

    user_question = state["user_question"]
    include_reddit = state["include_reddit"]

    official_query = f"""
Australian tax official guidance from ATO or TPB for this question:
{user_question}
""".strip()

    official_sources = search_with_domains(
        query=official_query,
        domains=["ato.gov.au", "tpb.gov.au"],
        max_results=TAVILY_MAX_RESULTS,
    )

    if include_reddit:
        reddit_query = f"""
Australian tax Reddit discussion practical examples for this question:
{user_question}
""".strip()

        reddit_context = search_with_domains(
            query=reddit_query,
            domains=["reddit.com"],
            max_results=3,
        )
    else:
        reddit_context = "Reddit/public discussion was not requested by the user."

    return {
        "agent_1_official_sources": official_sources,
        "agent_1_reddit_context": reddit_context,
    }


def agent_1_tax_answer(state: TaxAgentState) -> dict:
    """
    Node 2:
    Gemini answers as the CA Tax Guidance Agent.
    """

    gemini_llm = get_gemini_llm()

    prompt = CA_AGENT_PROMPT.format(
        country=COUNTRY,
        tax_authority=TAX_AUTHORITY,
        regulator=REGULATOR,
        tax_year=DEFAULT_TAX_YEAR,
        user_question=state["user_question"],
        official_sources=state["agent_1_official_sources"],
        reddit_context=state["agent_1_reddit_context"],
    )

    response = gemini_llm.invoke(prompt)

    return {
        "agent_1_answer": extract_response_text(response)
    }


def search_agent_2_verification_sources(state: TaxAgentState) -> dict:
    """
    Node 3:
    Search official sources again to verify Agent 1.
    Search Reddit again only if user selected that option.
    """

    user_question = state["user_question"]
    agent_1_answer = state["agent_1_answer"]
    include_reddit = state["include_reddit"]

    official_query = f"""
Verify these Australian tax claims using official ATO or TPB sources.

Original user question:
{user_question}

Agent 1 answer to verify:
{agent_1_answer[:2500]}
""".strip()

    official_sources = search_with_domains(
        query=official_query,
        domains=["ato.gov.au", "tpb.gov.au"],
        max_results=TAVILY_MAX_RESULTS,
    )

    if include_reddit:
        reddit_query = f"""
Australian tax Reddit discussion related to this question:
{user_question}
""".strip()

        reddit_context = search_with_domains(
            query=reddit_query,
            domains=["reddit.com"],
            max_results=3,
        )
    else:
        reddit_context = "Reddit/public discussion was not requested by the user."

    return {
        "agent_2_official_sources": official_sources,
        "agent_2_reddit_context": reddit_context,
    }


def agent_2_compliance_review(state: TaxAgentState) -> dict:
    """
    Node 4:
    Groq verifies Agent 1's answer and produces final compliance-safe guidance.
    """

    groq_llm = get_groq_llm()

    prompt = COMPLIANCE_AGENT_PROMPT.format(
        user_question=state["user_question"],
        agent_1_answer=state["agent_1_answer"],
        verification_official_sources=state["agent_2_official_sources"],
        verification_reddit_context=state["agent_2_reddit_context"],
        include_reddit=state["include_reddit"],
    )

    response = groq_llm.invoke(prompt)

    return {
        "final_answer": extract_response_text(response)
    }


def build_tax_guidance_graph():
    """
    Build and compile the LangGraph workflow.
    """

    graph = StateGraph(TaxAgentState)

    graph.add_node("search_agent_1_sources", search_agent_1_sources)
    graph.add_node("agent_1_tax_answer", agent_1_tax_answer)
    graph.add_node("search_agent_2_verification_sources", search_agent_2_verification_sources)
    graph.add_node("agent_2_compliance_review", agent_2_compliance_review)

    graph.add_edge(START, "search_agent_1_sources")
    graph.add_edge("search_agent_1_sources", "agent_1_tax_answer")
    graph.add_edge("agent_1_tax_answer", "search_agent_2_verification_sources")
    graph.add_edge("search_agent_2_verification_sources", "agent_2_compliance_review")
    graph.add_edge("agent_2_compliance_review", END)

    return graph.compile()


def run_langgraph_tax_agent(user_question: str, include_reddit: bool = False) -> str:
    """
    Run the full LangGraph workflow.
    """

    if not user_question or not user_question.strip():
        return "Please enter a valid Australian tax-related question."

    app = build_tax_guidance_graph()

    initial_state: TaxAgentState = {
        "user_question": user_question.strip(),
        "include_reddit": include_reddit,

        "agent_1_official_sources": "",
        "agent_1_reddit_context": "",
        "agent_1_answer": "",

        "agent_2_official_sources": "",
        "agent_2_reddit_context": "",
        "final_answer": "",
    }

    final_state = app.invoke(initial_state)

    return final_state["final_answer"]


if __name__ == "__main__":
    question = input("Enter your Australian tax question: ").strip()
    reddit_choice = input("Do you want Reddit/public discussion context? (y/n): ").strip().lower()

    include_reddit = reddit_choice in ["y", "yes"]

    answer = run_langgraph_tax_agent(
        user_question=question,
        include_reddit=include_reddit,
    )

    print("\n" + "=" * 80)
    print("FINAL REVIEWED TAX GUIDANCE")
    print("=" * 80 + "\n")
    print(answer)