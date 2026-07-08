# JogaBanito System and Architecture Diagrams

This document explains the current code structure in simple language.

The project is now a LangGraph-based terminal app. The user enters an Australian tax question and chooses whether Reddit/public discussion should be included. The app searches official ATO/TPB sources with Tavily, optionally searches Reddit, asks Gemini to create the first tax guidance answer, searches official sources again to verify that answer, asks Groq to perform the compliance review, and prints the final safer answer.

## 1. Big Picture System Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart TB
    user["User<br/>tax question + Reddit choice"]
    main["main.py<br/>terminal UI with Rich panels"]

    subgraph workflow["src/graph_workflow.py - LangGraph workflow"]
        direction LR
        search1["Node 1<br/>Search sources<br/>for Agent 1"]
        agent1["Node 2<br/>Gemini Agent 1<br/>CA guidance draft"]
        search2["Node 3<br/>Search fresh<br/>verification sources"]
        agent2["Node 4<br/>Groq Agent 2<br/>compliance review"]
        search1 --> agent1 --> search2 --> agent2
    end

    final["Final reviewed guidance<br/>printed in terminal"]

    subgraph support["Shared support files"]
        direction LR
        prompts["src/prompts.py<br/>prompt templates"]
        llm["src/llm.py<br/>LLM builders"]
        config["src/config.py + .env<br/>keys, models, tax settings"]
    end

    subgraph services["External services and sources"]
        direction LR
        tavily["Tavily search API"]
        official["ATO/TPB official domains"]
        reddit["Optional Reddit context"]
    end

    user --> main --> workflow
    workflow --> final --> main

    support -. "prompts, LLM builders,<br/>keys and settings" .-> workflow
    workflow -. "searches through" .-> tavily
    tavily --> official
    tavily -. "only if user says yes" .-> reddit
    llm -. "creates Gemini/Groq clients" .-> workflow

    classDef person fill:#dcfce7,stroke:#15803d,color:#14532d,stroke-width:3px
    classDef app fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef graphNode fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-width:3px
    classDef agent fill:#ede9fe,stroke:#7c3aed,color:#3b0764,stroke-width:3px
    classDef search fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef external fill:#ffe4e6,stroke:#e11d48,color:#881337,stroke-width:3px
    classDef output fill:#bbf7d0,stroke:#15803d,color:#14532d,stroke-width:3px

    class user person
    class main app
    class workflow graphNode
    class search1,search2,prompts,llm,config search
    class agent1,agent2 agent
    class tavily,official,reddit external
    class final output
```

## 2. Step-by-Step Runtime Flow

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart TD
    start["1. Run app<br/>python main.py"]
    welcome["2. Show welcome<br/>and disclaimer"]
    question["3. Ask tax question"]
    valid{"4. Question entered?"}
    error["Stop<br/>validation error"]
    reddit_choice["5. Ask Reddit<br/>yes/no"]
    status["6. Show workflow<br/>status messages"]
    run["7. Call<br/>run_langgraph_tax_agent()"]

    subgraph graph_phase["LangGraph phase - src/graph_workflow.py"]
        direction LR
        n1["8. search_agent_1_sources"]
        n2["9. agent_1_tax_answer"]
        n3["10. search_agent_2_verification_sources"]
        n4["11. agent_2_compliance_review"]
        n1 --> n2 --> n3 --> n4
    end

    output["12. Print final answer<br/>inside Rich panel"]
    catch["If exception happens<br/>print Error panel"]

    start --> welcome --> question --> valid
    valid -->|"no"| error
    valid -->|"yes"| reddit_choice --> status --> run
    run --> n1
    n4 --> output
    run -. "try / except" .-> catch

    classDef startEnd fill:#bbf7d0,stroke:#15803d,color:#14532d,stroke-width:3px
    classDef app fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-width:3px
    classDef node fill:#ede9fe,stroke:#7c3aed,color:#3b0764,stroke-width:3px
    classDef stopNode fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:3px

    class start,output startEnd
    class welcome,question,reddit_choice,status,run app
    class valid decision
    class n1,n2,n3,n4 node
    class error,catch stopNode
```

## 3. File and Module Logic

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart TD
    root["JogaBanito project folder"]

    main["main.py<br/>terminal entry point"]
    workflow["src/graph_workflow.py<br/>LangGraph state, nodes,<br/>search helpers, graph runner"]
    prompts["src/prompts.py<br/>CA and compliance prompts"]
    llm["src/llm.py<br/>Gemini/Groq client builders<br/>extract_response_text()"]
    config["src/config.py<br/>loads .env and defaults"]
    tools["src/tools/Web_search.py<br/>standalone Tavily search helper module"]
    init["src/__init__.py<br/>package marker"]
    tools_init["src/tools/__init__.py<br/>tools package marker"]

    env[".env<br/>real local secrets"]
    env_example[".env.example_incase_you_want_to_use<br/>example env values"]
    req["requirements.txt<br/>runtime dependency list"]
    pyproject["pyproject.toml<br/>project metadata and tool config"]
    lock["uv.lock<br/>locked dependency resolution"]
    gitignore[".gitignore<br/>ignored files"]
    docs["ARCHITECTURE_DIAGRAMS.md<br/>this diagram source"]
    pngs["*.png<br/>rendered diagram images"]

    root --> main
    root --> workflow
    root --> prompts
    root --> llm
    root --> config
    root --> tools
    root --> init
    root --> tools_init
    root --> env
    root --> env_example
    root --> req
    root --> pyproject
    root --> lock
    root --> gitignore
    root --> docs
    root --> pngs

    main -->|"imports run_langgraph_tax_agent"| workflow
    workflow -->|"uses prompts"| prompts
    workflow -->|"uses LLM builders"| llm
    workflow -->|"uses settings"| config
    llm -->|"uses model keys"| config
    config -->|"loads"| env
    tools -->|"also uses"| config

    classDef rootNode fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-width:3px
    classDef app fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef source fill:#ede9fe,stroke:#7c3aed,color:#3b0764,stroke-width:3px
    classDef configNode fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef setup fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:3px
    classDef docsNode fill:#dcfce7,stroke:#15803d,color:#14532d,stroke-width:3px

    class root rootNode
    class main app
    class workflow,prompts,llm,tools,init,tools_init source
    class config,env,env_example configNode
    class req,pyproject,lock,gitignore setup
    class docs,pngs docsNode
```

## 4. LangGraph Workflow and State

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart LR
    start(["START"])
    state0["Initial TaxAgentState<br/>user_question<br/>include_reddit<br/>empty answer/source fields"]

    node1["search_agent_1_sources<br/>official ATO/TPB search<br/>optional Reddit search"]
    state1["State update<br/>agent_1_official_sources<br/>agent_1_reddit_context"]

    node2["agent_1_tax_answer<br/>Gemini uses CA_AGENT_PROMPT"]
    state2["State update<br/>agent_1_answer"]

    node3["search_agent_2_verification_sources<br/>fresh official verification search<br/>optional Reddit verification context"]
    state3["State update<br/>agent_2_official_sources<br/>agent_2_reddit_context"]

    node4["agent_2_compliance_review<br/>Groq uses COMPLIANCE_AGENT_PROMPT"]
    state4["State update<br/>final_answer"]
    endNode(["END"])

    start --> state0 --> node1 --> state1 --> node2 --> state2 --> node3 --> state3 --> node4 --> state4 --> endNode

    classDef startEnd fill:#bbf7d0,stroke:#15803d,color:#14532d,stroke-width:3px
    classDef state fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef search fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef agent fill:#ede9fe,stroke:#7c3aed,color:#3b0764,stroke-width:3px

    class start,endNode startEnd
    class state0,state1,state2,state3,state4 state
    class node1,node3 search
    class node2,node4 agent
```

## 5. Configuration and External Services

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart LR
    env[".env"]
    dotenv["python-dotenv<br/>load_dotenv()"]
    config["src/config.py"]

    required["Required keys<br/>GEMINI_API_KEY<br/>GROQ_API_KEY<br/>TAVILY_API_KEY"]
    optional["Optional/default settings<br/>GEMINI_MODEL<br/>GROQ_MODEL<br/>TAVILY_MAX_RESULTS<br/>COUNTRY<br/>TAX_AUTHORITY<br/>REGULATOR<br/>DEFAULT_TAX_YEAR<br/>APP_ENV<br/>DEBUG"]

    tavily["TavilyClient<br/>official and Reddit searches"]
    gemini["ChatGoogleGenerativeAI<br/>Agent 1"]
    groq["ChatGroq<br/>Agent 2"]

    env --> dotenv --> config
    config --> required
    config --> optional
    required --> tavily
    required --> gemini
    required --> groq
    optional --> tavily
    optional --> gemini
    optional --> groq

    classDef loader fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef configNode fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef warning fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:3px
    classDef optionalNode fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-width:3px
    classDef service fill:#ffe4e6,stroke:#e11d48,color:#881337,stroke-width:3px

    class env,dotenv loader
    class config configNode
    class required warning
    class optional optionalNode
    class tavily,gemini,groq service
```

## 6. Current Data Flow in One Line

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart LR
    input["Question + Reddit choice"]
    sources1["ATO/TPB sources<br/>optional Reddit context"]
    draft["Gemini Agent 1<br/>draft answer"]
    sources2["Fresh ATO/TPB verification<br/>optional Reddit context"]
    final["Groq Agent 2<br/>final reviewed answer"]
    terminal["Terminal output"]

    input --> sources1 --> draft --> sources2 --> final --> terminal

    classDef inputNode fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef sourceNode fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef agent fill:#ede9fe,stroke:#7c3aed,color:#3b0764,stroke-width:3px
    classDef output fill:#bbf7d0,stroke:#15803d,color:#14532d,stroke-width:3px

    class input inputNode
    class sources1,sources2 sourceNode
    class draft,final agent
    class terminal output
```

## 7. Search Logic and Helper Module

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#ffffff", "primaryTextColor": "#111827", "textColor": "#111827", "lineColor": "#334155", "edgeLabelBackground": "#ffffff", "fontFamily": "Arial", "fontSize": "18px"}}}%%
flowchart TD
    workflow["src/graph_workflow.py<br/>currently used by main.py"]
    inline_search["Inline search helpers<br/>get_tavily_client()<br/>format_search_results()<br/>search_with_domains()"]
    node1["Graph search nodes<br/>search_agent_1_sources<br/>search_agent_2_verification_sources"]

    tools["src/tools/Web_search.py<br/>standalone helper module"]
    official_helper["search_official_tax_sources()"]
    reddit_helper["search_reddit_context()"]
    all_helper["search_all_tax_sources()"]
    verify_helper["search_verification_sources()"]

    tavily["Tavily API"]
    official["ATO/TPB domains"]
    reddit["Reddit domain"]

    workflow --> inline_search --> node1 --> tavily
    tools --> official_helper --> tavily
    tools --> reddit_helper --> tavily
    tools --> all_helper --> tavily
    tools --> verify_helper --> tavily
    tavily --> official
    tavily -. "optional context" .-> reddit

    classDef active fill:#dbeafe,stroke:#2563eb,color:#1e3a8a,stroke-width:3px
    classDef helper fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-width:3px
    classDef search fill:#cffafe,stroke:#0891b2,color:#164e63,stroke-width:3px
    classDef external fill:#ffe4e6,stroke:#e11d48,color:#881337,stroke-width:3px

    class workflow,node1 active
    class inline_search,tools,official_helper,reddit_helper,all_helper,verify_helper helper
    class tavily search
    class official,reddit external
```

## 8. What Each Important File Does

| File | Main responsibility | Easy explanation |
| --- | --- | --- |
| `main.py` | Terminal entry point | Shows the welcome/disclaimer, asks for a tax question, asks whether to include Reddit, runs the LangGraph workflow, and prints the final answer or error. |
| `src/graph_workflow.py` | Main application workflow | Defines the shared graph state, search functions, four LangGraph nodes, graph edges, and `run_langgraph_tax_agent()`. |
| `src/prompts.py` | Prompt library | Stores the CA guidance prompt and compliance review prompt, including official-source and Reddit rules. |
| `src/llm.py` | LLM setup | Builds the Gemini client for Agent 1, the Groq client for Agent 2, and extracts response text. |
| `src/config.py` | Settings loader | Loads `.env`, validates required API keys, and stores model/search/tax settings. |
| `src/tools/Web_search.py` | Search helper module | Contains reusable Tavily helper functions for official-source, Reddit, combined, and verification searches. The current graph duplicates some search logic inline. |
| `requirements.txt` | Runtime dependencies | Lists the smaller current runtime package set. |
| `uv.lock` | Dependency lockfile | Records resolved dependency versions from uv. |

## 9. Plain-English Summary

The current app starts in `main.py`. It asks the user for a question and asks whether Reddit context should be included. Then it calls `run_langgraph_tax_agent()` from `src/graph_workflow.py`.

The LangGraph workflow runs four nodes in order. First it searches official ATO/TPB sources, and optionally Reddit. Then Gemini creates Agent 1's first tax answer. Next, the workflow searches fresh official sources to verify Agent 1's answer, again optionally adding Reddit context. Finally, Groq creates the compliance-reviewed final answer, which `main.py` prints in the terminal.
