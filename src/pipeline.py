# src/pipeline.py

from agents import run_ca_guidance_agent, run_compliance_review_agent


def run_tax_guidance_pipeline(user_question: str) -> str:
    """
    Main project pipeline.

    Flow:
    1. Receive user's tax question
    2. Send question to Agent 1: CA Tax Guidance Agent
    3. Send Agent 1 answer to Agent 2: Senior Compliance Review Agent
    4. Return final reviewed answer

    This follows the MVP requirement:
    User question -> Agent 1 -> Agent 2 -> Final terminal output
    """

    if not user_question or not user_question.strip():
        return "Please enter a valid tax-related question."

    cleaned_question = user_question.strip()

    print("\nStep 1: Sending question to CA Tax Guidance Agent...\n")
    ca_agent_answer = run_ca_guidance_agent(cleaned_question)

    print("\nStep 2: Sending CA answer to Senior Compliance Review Agent...\n")
    final_reviewed_answer = run_compliance_review_agent(
        user_question=cleaned_question,
        ca_agent_answer=ca_agent_answer,
    )

    return final_reviewed_answer


if __name__ == "__main__":
    test_question = "I bought a laptop for university and part-time work. Can I claim it in my Australian tax return?"

    final_answer = run_tax_guidance_pipeline(test_question)

    print("\n" + "=" * 80)
    print("Final Reviewed Guidance")
    print("=" * 80 + "\n")
    print(final_answer)