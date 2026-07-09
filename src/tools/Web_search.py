from tavily import TavilyClient
from typing_extensions import TypedDict

from src.config import TAVILY_API_KEY, TAVILY_MAX_RESULTS


class SearchSource(TypedDict):
    """
    Structured source record used by the graph and prompt layer.
    Keeping this structured makes citations and audit trails easier.
    """

    label: str
    title: str
    url: str
    content: str
    source_type: str


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


def normalize_search_results(
    results: list[dict],
    source_type: str,
    label_prefix: str | None = None,
) -> list[SearchSource]:
    """
    Convert Tavily search results into structured source records.
    """

    structured_results: list[SearchSource] = []

    for index, item in enumerate(results, start=1):
        title = item.get("title") or "No title"
        url = item.get("url") or "No URL"
        content = item.get("content") or ""
        raw_content = item.get("raw_content") or ""
        best_content = raw_content if raw_content else content

        structured_results.append(
            {
                "label": f"{label_prefix or source_type.upper()}-{index}",
                "title": title,
                "url": url,
                "content": best_content.strip(),
                "source_type": source_type,
            }
        )

    return structured_results


def format_search_results(sources: list[SearchSource]) -> str:
    """
    Convert structured search results into citation-friendly prompt text.
    """

    if not sources:
        return "No relevant search results found."

    formatted_results = []

    for source in sources:
        formatted_results.append(
            f"""
[{source["label"]}]
Source type: {source["source_type"]}
Title: {source["title"]}
URL: {source["url"]}
Content:
{source["content"]}
""".strip()
        )

    return "\n\n".join(formatted_results)


def format_source_list(sources: list[SearchSource]) -> str:
    """
    Create a compact list of source labels and URLs for final citations.
    """

    if not sources:
        return "No sources available."

    return "\n".join(
        f"- [{source['label']}] {source['title']} - {source['url']}"
        for source in sources
    )


def search_with_domains(
    query: str,
    domains: list[str],
    max_results: int,
    source_type: str,
    label_prefix: str | None = None,
    search_depth: str = "advanced",
    include_raw_content: bool | str = "text",
) -> list[SearchSource]:
    """
    Search selected domains and return structured citation records.
    """

    client = get_tavily_client()

    response = client.search(
        query=query,
        include_domains=domains,
        search_depth=search_depth,
        include_raw_content=include_raw_content,
        max_results=max_results,
        country="australia",
    )

    results = response.get("results", [])

    return normalize_search_results(
        results,
        source_type=source_type,
        label_prefix=label_prefix,
    )


def search_official_tax_sources(
    user_question: str,
    label_prefix: str | None = None,
) -> list[SearchSource]:
    """
    Search official Australian tax sources only.

    This should be used by Agent 1 and Agent 2 for ATO/TPB evidence.
    """

    query = f"""
Australian tax rule official guidance: {user_question}
""".strip()

    return search_with_domains(
        query=query,
        domains=OFFICIAL_DOMAINS,
        search_depth="advanced",
        include_raw_content="text",
        max_results=TAVILY_MAX_RESULTS,
        source_type="official",
        label_prefix=label_prefix,
    )


def search_reddit_context(
    user_question: str,
    label_prefix: str | None = None,
) -> list[SearchSource]:
    """
    Search Reddit only for practical public discussion.

    Reddit must NOT be treated as official tax guidance.
    It is only useful for understanding common questions, confusion,
    practical cases, or risks people discuss.
    """

    query = f"""
Australian tax Reddit discussion practical examples: {user_question}
""".strip()

    return search_with_domains(
        query=query,
        domains=REDDIT_DOMAINS,
        search_depth="basic",
        include_raw_content=False,
        max_results=3,
        source_type="reddit",
        label_prefix=label_prefix,
    )


def search_all_tax_sources(user_question: str) -> dict[str, list[SearchSource]]:
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


def search_verification_sources(user_question: str, agent_1_answer: str) -> dict[str, list[SearchSource]]:
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
    print(format_search_results(official))

    print("\n" + "=" * 80 + "\n")

    print("Searching Reddit context...\n")
    reddit = search_reddit_context(test_question)
    print(format_search_results(reddit))
