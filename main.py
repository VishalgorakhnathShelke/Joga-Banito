# main.py

from rich.console import Console
from rich.panel import Panel

from src.graph_workflow import run_langgraph_tax_agent


console = Console()


def show_welcome_message() -> None:
    """
    Show welcome and safety message.
    """

    welcome_text = """
AI Tax Guidance and Compliance Review Agent

This tool provides educational guidance only.
It does not replace a registered tax agent.
It does not guarantee that any claim will be accepted by the ATO.

Official ATO/TPB-style sources are used for tax guidance.
Reddit can be shown only as optional public discussion context.
"""

    console.print(
        Panel(
            welcome_text.strip(),
            title="Australian Tax Guidance Agent",
            border_style="blue",
        )
    )


def get_user_question() -> str:
    """
    Ask the user to enter a tax-related question.
    """

    console.print("\nEnter your Australian tax-related question below:")
    console.print("Example: Can I claim my laptop for part-time work?\n")

    user_question = input("Your question: ")

    return user_question.strip()


def ask_include_reddit() -> bool:
    """
    Ask whether user wants to see Reddit/public discussion context.
    """

    console.print(
        "\nDo you want to also see Reddit/public discussion context?"
    )
    console.print(
        "Note: Reddit is not official tax guidance. It only shows what people discuss publicly.\n"
    )

    answer = input("Include Reddit context? (y/n): ").strip().lower()

    return answer in ["y", "yes"]


def main() -> None:
    """
    Main terminal entry point.
    """

    show_welcome_message()

    user_question = get_user_question()

    if not user_question:
        console.print("[red]No question entered. Please run again and enter a valid question.[/red]")
        return

    include_reddit = ask_include_reddit()

    console.print("\n[yellow]Running LangGraph tax guidance workflow...[/yellow]")
    console.print("[yellow]Step 1: Searching official sources...[/yellow]")
    console.print("[yellow]Step 2: Grading evidence and checking missing facts...[/yellow]")
    console.print("[yellow]Step 3: Running Agent 1...[/yellow]")
    console.print("[yellow]Step 4: Verifying with Agent 2...[/yellow]\n")

    try:
        final_answer = run_langgraph_tax_agent(
            user_question=user_question,
            include_reddit=include_reddit,
        )

        console.print(
            Panel(
                final_answer,
                title="Final Reviewed Tax Guidance",
                border_style="green",
            )
        )

    except Exception as error:
        console.print(
            Panel(
                str(error),
                title="Error",
                border_style="red",
            )
        )


if __name__ == "__main__":
    main()
