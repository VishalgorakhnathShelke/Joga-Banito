# JogaBanito

An AI-assisted Australian tax guidance and compliance review agent.

JogaBanito is a terminal-based LangGraph app that accepts an Australian tax question, searches official ATO/TPB sources through Tavily, optionally includes Reddit/public discussion context, drafts guidance with Gemini, and then asks Groq to review the answer for compliance risk before showing a final response.

> This project provides educational guidance only. It is not the ATO, the TPB, or a registered tax agent, and it cannot guarantee that any tax claim will be accepted.

## What It Does

- Collects an Australian tax-related question from the terminal.
- Searches official Australian Taxation Office and Tax Practitioners Board sources.
- Optionally searches Reddit for public discussion context.
- Keeps search results as structured source records with citation labels.
- Grades the strength of official evidence before the first answer is drafted.
- Identifies missing facts that may need clarification.
- Uses Gemini as Agent 1 to draft cited tax guidance.
- Uses Groq as Agent 2 to verify, correct, cite, and make the answer more compliance-safe.
- Prints a structured final answer with a disclaimer.

## Current Workflow

```text
User question
  -> Tavily search: ATO/TPB sources
  -> Optional Tavily search: Reddit context
  -> Evidence grading + clarification check
  -> Gemini Agent 1: first cited tax guidance answer
  -> Tavily search: fresh verification sources
  -> Groq Agent 2: compliance review with source citations
  -> Final reviewed guidance with Sources checked
```

The implementation lives mainly in:

- `main.py` - terminal entry point and Rich console UI.
- `src/graph_workflow.py` - LangGraph workflow, evidence grading, clarification checks, and node definitions.
- `src/config.py` - environment loading and app settings.
- `src/llm.py` - Gemini and Groq client setup.
- `src/prompts.py` - Agent 1 and Agent 2 prompt templates with citation rules.
- `src/tools/Web_search.py` - reusable Tavily search helpers that return structured source records.
- `ARCHITECTURE_DIAGRAMS.md` - detailed architecture and flow diagrams.

## Requirements

- Python 3.10 or newer
- Gemini API key
- Groq API key
- Tavily API key

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Or, if using `uv`:

```powershell
uv sync
```

Create a `.env` file in the project root. You can use `.env.example_incase_you_want_to_use` as a starting point:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

TAVILY_API_KEY=your_tavily_api_key_here
TAVILY_MAX_RESULTS=5

COUNTRY=Australia
TAX_AUTHORITY=Australian Taxation Office
REGULATOR=Tax Practitioners Board
DEFAULT_TAX_YEAR=2025-2026

APP_ENV=development
DEBUG=True
```

## Run

```powershell
python main.py
```

Then enter a tax question, for example:

```text
Can I claim my laptop if I use it for both university and part-time work?
```

The app will ask whether to include Reddit/public discussion context. Reddit is treated only as optional public discussion, not as official tax evidence.

## Safety Model

The app is designed to be conservative:

- Official ATO/TPB material is the primary evidence source.
- Reddit can only be included as public discussion context.
- Official source results are labelled for citations, such as `[OFFICIAL-A1-1]` and `[OFFICIAL-A2-1]`.
- Evidence strength is graded before Agent 1 drafts an answer.
- Missing facts are passed into the agents as clarification questions.
- Agent 2 checks Agent 1 for unsupported claims, false confidence, compliance risk, and missing evidence.
- Agent 2 must include a "Sources checked" section with official URLs.
- The final answer asks users to confirm important filing decisions with a registered tax agent where appropriate.

## Project Structure

```text
JogaBanito/
|-- main.py
|-- pyproject.toml
|-- requirements.txt
|-- uv.lock
|-- ARCHITECTURE_DIAGRAMS.md
|-- src/
|   |-- config.py
|   |-- graph_workflow.py
|   |-- llm.py
|   |-- prompts.py
|   `-- tools/
|       `-- Web_search.py
`-- README.md
```

## Implemented Agentic Safeguards

These safeguards make the project more trustworthy as an agent system:

- Structured source records: search results now keep labels, titles, URLs, content, and source type.
- Mandatory citation prompting: important official-source-based tax claims must cite labels like `[OFFICIAL-A1-1]`.
- Evidence grading: the graph grades whether official evidence is strong, moderate, limited, or very weak.
- Clarification checks: the graph identifies missing facts such as tax year, work-use percentage, logbook details, or evidence records.
- Final source list: Agent 2 is instructed to include a "Sources checked" section with exact official URLs.

## Suggestions To Improve Next

### 1. Align Dependency Files

`requirements.txt` and `pyproject.toml` currently do not fully match. For example, the code imports `langchain_google_genai`, and `requirements.txt` includes `langchain-google-genai`, but `pyproject.toml` lists `langchain-openai` instead.

Suggested fix:

- Make `pyproject.toml` the source of truth.
- Add `langchain-google-genai` to `pyproject.toml`.
- Remove unused packages such as `langchain-openai` if they are not needed.
- Regenerate `uv.lock` after updating dependencies.

### 2. Rename The Example Environment File

The example file is currently named:

```text
.env.example_incase_you_want_to_use
```

Suggested fix:

```text
.env.example
```

This is the common convention and makes setup easier for new contributors.

### 3. Add Tests Around The Workflow

There are no tests yet, but this app has several important behaviors that should not regress.

Good first tests:

- Empty questions return a friendly validation response.
- Reddit context is excluded when the user chooses `False`.
- Reddit context is included only in a separate section when requested.
- Search formatting handles missing titles, URLs, and content.
- Agent 2 prompt receives the Agent 1 answer and fresh verification sources.
- Evidence grading behaves conservatively when official sources are weak.
- Clarification questions appear when key facts are missing.

Use mocks for Tavily, Gemini, and Groq so tests do not call live APIs.

### 4. Improve Error Handling

The terminal currently catches broad exceptions and prints the error text.

Suggested improvements:

- Detect missing API keys before the workflow starts.
- Show clearer messages for Tavily failures, rate limits, and network errors.
- Separate user-facing errors from debug logs.
- Add retry/backoff for transient search or model failures.

### 5. Add Logging And Traceability

For a compliance-oriented app, it helps to know what happened during a run.

Suggested improvements:

- Log workflow steps, selected models, and source URLs checked.
- Avoid logging user secrets or sensitive tax documents.
- Store optional run summaries in `outputs/` for debugging.

### 6. Add A Non-Interactive CLI Mode

The app currently uses `input()`, which is friendly for demos but harder to automate.

Suggested improvement:

```powershell
python main.py --question "Can I claim a laptop?" --include-reddit false
```

This would make the project easier to test, script, and integrate into other tools.

### 7. Add Guardrails For Tax Scope

The prompts are tax-focused, but the app can still accept unrelated questions.

Suggested improvements:

- Add a lightweight classifier node before search.
- Reject clearly non-tax questions.
- Add an interactive follow-up mode when clarification questions are detected.

### 8. Prepare For Document Uploads Later

The `.gitignore` already excludes sensitive uploaded documents, and the environment example mentions uploads and outputs.

Possible future features:

- Receipt/PDF extraction.
- Work-use percentage calculation.
- Deduction evidence checklist.
- Exportable summary for a registered tax agent.

## Development Notes

Run basic syntax checks:

```powershell
python -m compileall main.py src
```

If tests are added later:

```powershell
pytest
```

If Ruff is installed:

```powershell
ruff check .
```

## Important Disclaimer

This project is an educational AI assistant for Australian tax guidance. It does not provide professional tax advice and should not be used as the sole basis for lodging a tax return. Users should confirm final decisions with a registered tax agent, especially for complex, high-value, or uncertain claims.
