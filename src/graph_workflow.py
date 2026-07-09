# src/graph_workflow.py

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from src.config import (
    COUNTRY,
    TAX_AUTHORITY,
    REGULATOR,
    DEFAULT_TAX_YEAR,
)

from src.llm import get_gemini_llm, get_groq_llm, extract_response_text
from src.prompts import CA_AGENT_PROMPT, COMPLIANCE_AGENT_PROMPT
from src.tools.Web_search import (
    SearchSource,
    format_search_results,
    format_source_list,
    search_official_tax_sources,
    search_reddit_context,
)


class TaxAgentState(TypedDict):
    """
    Shared state for the LangGraph workflow.
    Each node reads from this state and returns updates to it.
    """

    user_question: str
    include_reddit: bool

    needs_clarification: bool
    clarification_questions: str
    evidence_grade: str
    evidence_summary: str

    agent_1_official_sources: list[SearchSource]
    agent_1_reddit_sources: list[SearchSource]
    agent_1_answer: str

    agent_2_official_sources: list[SearchSource]
    agent_2_reddit_sources: list[SearchSource]
    official_source_citations: str
    reddit_source_citations: str
    final_answer: str


QUESTION_KEYWORDS_TO_FACTS = {
    "laptop": "work-use percentage and evidence of work use",
    "computer": "work-use percentage and evidence of work use",
    "phone": "work-use percentage and phone records or a reasonable usage calculation",
    "internet": "work-use percentage and a reasonable usage calculation",
    "car": "logbook or cents-per-kilometre method details",
    "vehicle": "logbook or cents-per-kilometre method details",
    "travel": "purpose of the travel and whether it was work-related or private",
    "home office": "actual hours worked from home and running expense records",
    "wfh": "actual hours worked from home and running expense records",
    "rental": "rental income, private-use periods, and expense evidence",
    "crypto": "transaction history, dates, proceeds, cost base, and exchange records",
    "shares": "purchase/sale dates, proceeds, cost base, and dividend statements",
    "study": "whether the study directly relates to current income-earning work",
    "course": "whether the course directly relates to current income-earning work",
}


STOP_WORDS = {
    "about",
    "after",
    "also",
    "australia",
    "australian",
    "because",
    "before",
    "claim",
    "could",
    "deduct",
    "deduction",
    "does",
    "from",
    "have",
    "this",
    "that",
    "their",
    "there",
    "what",
    "when",
    "where",
    "which",
    "with",
    "work",
    "would",
}


def extract_question_keywords(user_question: str) -> set[str]:
    """
    Pull simple matching keywords from the question for evidence grading.
    """

    words = {
        word.strip(".,?!:;()[]{}'\"").lower()
        for word in user_question.split()
    }

    return {
        word for word in words
        if len(word) >= 4 and word not in STOP_WORDS
    }


def grade_official_evidence(user_question: str, sources: list[SearchSource]) -> tuple[str, str]:
    """
    Give the agents a conservative quality signal before they answer.
    """

    if not sources:
        return (
            "Very weak",
            "No official ATO/TPB source was found. Treat the answer as unclear and avoid firm claims.",
        )

    keywords = extract_question_keywords(user_question)

    if not keywords:
        return (
            "Limited",
            "Official sources were found, but the question has few concrete facts to match against.",
        )

    total_matches = 0

    for source in sources:
        searchable_text = f"{source['title']} {source['content']}".lower()
        total_matches += sum(1 for keyword in keywords if keyword in searchable_text)

    average_matches = total_matches / max(len(sources), 1)

    if len(sources) >= 3 and average_matches >= 2:
        return (
            "Strong",
            "Multiple official sources appear related to the user's facts. Key claims still need citations.",
        )

    if len(sources) >= 2 and average_matches >= 1:
        return (
            "Moderate",
            "Some official sources appear related, but the agents should avoid overconfident conclusions.",
        )

    return (
        "Limited",
        "Official sources were found, but they may only partially match the user's specific facts.",
    )


def build_clarification_questions(user_question: str, evidence_grade: str) -> tuple[bool, str]:
    """
    Identify facts that would materially change the tax answer.
    """

    question_lower = user_question.lower()
    missing_facts = []

    if "202" not in question_lower and "fy" not in question_lower and "tax year" not in question_lower:
        missing_facts.append(f"Which tax year is this for? The current default is {DEFAULT_TAX_YEAR}.")

    for keyword, fact in QUESTION_KEYWORDS_TO_FACTS.items():
        if keyword in question_lower:
            missing_facts.append(f"What is the {fact}?")

    if evidence_grade in {"Very weak", "Limited"}:
        missing_facts.append(
            "What exact facts or documents support the claim, and are there official ATO/TPB pages that apply?"
        )

    if not missing_facts:
        return False, "No high-priority clarification questions detected."

    unique_facts = list(dict.fromkeys(missing_facts))

    return True, "\n".join(f"- {fact}" for fact in unique_facts)


def search_agent_1_sources(state: TaxAgentState) -> dict:
    """
    Node 1:
    Search official ATO/TPB sources.
    Search Reddit only if user selected that option.
    """

    user_question = state["user_question"]
    include_reddit = state["include_reddit"]

    official_sources = search_official_tax_sources(
        user_question,
        label_prefix="OFFICIAL-A1",
    )

    if include_reddit:
        reddit_sources = search_reddit_context(
            user_question,
            label_prefix="REDDIT-A1",
        )
    else:
        reddit_sources = []

    return {
        "agent_1_official_sources": official_sources,
        "agent_1_reddit_sources": reddit_sources,
    }


def grade_evidence_and_clarify(state: TaxAgentState) -> dict:
    """
    Node 2:
    Grade official evidence strength and identify missing facts before drafting.
    """

    evidence_grade, evidence_summary = grade_official_evidence(
        user_question=state["user_question"],
        sources=state["agent_1_official_sources"],
    )
    needs_clarification, clarification_questions = build_clarification_questions(
        user_question=state["user_question"],
        evidence_grade=evidence_grade,
    )

    return {
        "needs_clarification": needs_clarification,
        "clarification_questions": clarification_questions,
        "evidence_grade": evidence_grade,
        "evidence_summary": evidence_summary,
    }


def agent_1_tax_answer(state: TaxAgentState) -> dict:
    """
    Node 3:
    Gemini answers as the CA Tax Guidance Agent.
    """

    gemini_llm = get_gemini_llm()
    reddit_context = (
        format_search_results(state["agent_1_reddit_sources"])
        if state["include_reddit"]
        else "Reddit/public discussion was not requested by the user."
    )

    prompt = CA_AGENT_PROMPT.format(
        country=COUNTRY,
        tax_authority=TAX_AUTHORITY,
        regulator=REGULATOR,
        tax_year=DEFAULT_TAX_YEAR,
        user_question=state["user_question"],
        official_sources=format_search_results(state["agent_1_official_sources"]),
        reddit_context=reddit_context,
        evidence_grade=state["evidence_grade"],
        evidence_summary=state["evidence_summary"],
        needs_clarification=state["needs_clarification"],
        clarification_questions=state["clarification_questions"],
    )

    response = gemini_llm.invoke(prompt)

    return {
        "agent_1_answer": extract_response_text(response)
    }


def search_agent_2_verification_sources(state: TaxAgentState) -> dict:
    """
    Node 4:
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

    official_sources = search_official_tax_sources(
        official_query,
        label_prefix="OFFICIAL-A2",
    )

    if include_reddit:
        reddit_sources = search_reddit_context(
            user_question,
            label_prefix="REDDIT-A2",
        )
    else:
        reddit_sources = []

    all_official_sources = state["agent_1_official_sources"] + official_sources
    all_reddit_sources = state["agent_1_reddit_sources"] + reddit_sources

    return {
        "agent_2_official_sources": official_sources,
        "agent_2_reddit_sources": reddit_sources,
        "official_source_citations": format_source_list(all_official_sources),
        "reddit_source_citations": format_source_list(all_reddit_sources),
    }


def agent_2_compliance_review(state: TaxAgentState) -> dict:
    """
    Node 5:
    Groq verifies Agent 1's answer and produces final compliance-safe guidance.
    """

    groq_llm = get_groq_llm()
    reddit_context = (
        format_search_results(state["agent_2_reddit_sources"])
        if state["include_reddit"]
        else "Reddit/public discussion was not requested by the user."
    )

    prompt = COMPLIANCE_AGENT_PROMPT.format(
        user_question=state["user_question"],
        agent_1_answer=state["agent_1_answer"],
        verification_official_sources=format_search_results(state["agent_2_official_sources"]),
        verification_reddit_context=reddit_context,
        include_reddit=state["include_reddit"],
        evidence_grade=state["evidence_grade"],
        evidence_summary=state["evidence_summary"],
        needs_clarification=state["needs_clarification"],
        clarification_questions=state["clarification_questions"],
        official_source_citations=state["official_source_citations"],
        reddit_source_citations=state["reddit_source_citations"],
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
    graph.add_node("grade_evidence_and_clarify", grade_evidence_and_clarify)
    graph.add_node("agent_1_tax_answer", agent_1_tax_answer)
    graph.add_node("search_agent_2_verification_sources", search_agent_2_verification_sources)
    graph.add_node("agent_2_compliance_review", agent_2_compliance_review)

    graph.add_edge(START, "search_agent_1_sources")
    graph.add_edge("search_agent_1_sources", "grade_evidence_and_clarify")
    graph.add_edge("grade_evidence_and_clarify", "agent_1_tax_answer")
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

        "needs_clarification": False,
        "clarification_questions": "",
        "evidence_grade": "",
        "evidence_summary": "",

        "agent_1_official_sources": [],
        "agent_1_reddit_sources": [],
        "agent_1_answer": "",

        "agent_2_official_sources": [],
        "agent_2_reddit_sources": [],
        "official_source_citations": "",
        "reddit_source_citations": "",
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
