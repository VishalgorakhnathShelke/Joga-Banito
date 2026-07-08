# main.py

from rich.console import Console
from rich.panel import Panel

from src.pipeline import run_tax_guidance_pipeline


console = Console()


def show_welcome_message() -> None:
    """
    Show a simple welcome message when the app starts.
    """

    welcome_text = """
AI Tax Guidance and Compliance Review Agent

This tool provides educational guidance only.
It does not replace a registered tax agent.
It does not guarantee that any claim will be accepted by the ATO.
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


def main() -> None:
    """
    Main entry point for the terminal app.

    Flow:
    1. Show welcome/disclaimer message
    2. Ask user for a tax question
    3. Send question to the two-agent pipeline
    4. Print final reviewed guidance
    """

    show_welcome_message()

    user_question = get_user_question()

    if not user_question:
        console.print("[red]No question entered. Please run the app again and enter a valid question.[/red]")
        return

    console.print("\n[yellow]Running the two-agent review process...[/yellow]")

    final_answer = run_tax_guidance_pipeline(user_question)

    console.print("\n")
    console.print(
        Panel(
            final_answer,
            title="Final Reviewed Tax Guidance",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()