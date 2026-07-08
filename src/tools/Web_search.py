# src/tools/web_search.py

from tavily import TavilyClient

from src.config import TAVILY_API_KEY, TAVILY_MAX_RESULTS


OFFICIAL_DOMAINS = [
    "ato.gov.au",
    "tpb.gov.au",
]

REDDIT_DOMAINS = [
    "reddit.com",
]


def get_tavily_client() -> TavilyClient:
    """
    Create Tavily client using API key from .env.
    """
    if not TAVILY_API_KEY:
        raise ValueError(
            "Missing TAVILY_API_KEY. Please add it to your .env file."
        )

    return TavilyClient(api_key=TAVILY_API_KEY)


def format_search_results(results: list[dict]) -> str:
    """
    Convert Tavily search results into clean text that can be passed to an LLM.
    """

    if not results:
        return "No relevant search results found."

    formatted_results = []

    for index, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        url = item.get("url", "No URL")
        content = item.get("content", "")
        raw_content = item.get("raw_content", "")

        best_content = raw_content if raw_content else content

        formatted_results.append(
            f"""
Source {index}
Title: {title}
URL: {url}
Content:
{best_content}
""".strip()
        )

    return "\n\n".join(formatted_results)


def search_official_tax_sources(user_question: str) -> str:
    """
    Search official Australian tax sources only.

    This should be used by Agent 1 and Agent 2 for ATO/TPB evidence.
    """

    client = get_tavily_client()

    query = f"""
Australian tax rule official guidance: {user_question}
""".strip()

    response = client.search(
        query=query,
        include_domains=OFFICIAL_DOMAINS,
        search_depth="advanced",
        include_raw_content="text",
        max_results=TAVILY_MAX_RESULTS,
        country="australia",
    )

    results = response.get("results", [])

    return format_search_results(results)


def search_reddit_context(user_question: str) -> str:
    """
    Search Reddit only for practical public discussion.

    Reddit must NOT be treated as official tax guidance.
    It is only useful for understanding common questions, confusion,
    practical cases, or risks people discuss.
    """

    client = get_tavily_client()

    query = f"""
Australian tax Reddit discussion practical examples: {user_question}
""".strip()

    response = client.search(
        query=query,
        include_domains=REDDIT_DOMAINS,
        search_depth="basic",
        include_raw_content=False,
        max_results=3,
        country="australia",
    )

    results = response.get("results", [])

    return format_search_results(results)


def search_all_tax_sources(user_question: str) -> dict:
    """
    Search both official sources and Reddit context.

    Returns a dictionary so agents can clearly separate official evidence
    from public discussion.
    """

    official_sources = search_official_tax_sources(user_question)
    reddit_context = search_reddit_context(user_question)

    return {
        "official_sources": official_sources,
        "reddit_context": reddit_context,
    }


def search_verification_sources(user_question: str, agent_1_answer: str) -> dict:
    """
    Agent 2 uses this to independently verify Agent 1's answer.

    It searches using both the original question and key claims from Agent 1.
    """

    verification_query = f"""
Original user question:
{user_question}

Claims to verify:
{agent_1_answer[:1500]}
""".strip()

    official_sources = search_official_tax_sources(verification_query)
    reddit_context = search_reddit_context(user_question)

    return {
        "official_sources": official_sources,
        "reddit_context": reddit_context,
    }


if __name__ == "__main__":
    test_question = "Can I claim a laptop used for university and part-time work in Australia?"

    print("Searching official ATO/TPB sources...\n")
    official = search_official_tax_sources(test_question)
    print(official)

    print("\n" + "=" * 80 + "\n")

    print("Searching Reddit context...\n")
    reddit = search_reddit_context(test_question)
    print(reddit)