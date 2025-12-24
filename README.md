# AI Scientist CI

AI Scientist CI is an advanced, automated scientific discovery system designed for the Compressed Imaging (SCI) domain. It leverages a multi-agent architecture orchestrated by a state-driven graph (LangGraph) to autonomously plan, execute, analyze, and refine scientific experiments.

## 🚀 Key Features

*   **Autonomous Research Loop**: A fully automated cycle of hypothesis (plan), experiment (execute), and analysis (learn).
*   **Multi-Agent Architecture**: Specialized agents for planning, reviewing, execution, and analysis.
*   **State-Driven Workflow**: Uses [LangGraph](https://github.com/langchain-ai/langgraph) for robust, cyclic, and self-correcting workflow orchestration.
*   **LLM-Powered Insights**: Utilizes Large Language Models (LLMs) for generating experiment configurations, verifying validity, and deriving scientific insights from results.
*   **Pareto Optimization**: Automatically identifies and refines trade-offs (e.g., Image Quality vs. Reconstruction Speed) using Pareto front analysis.
*   **Unified Persistence**: Ensures all experiment results and analytical insights are securely persisted to a World Model (SQLite/SQLAlchemy).

## 🛠️ Architecture

The system is built upon a modular architecture where agents act as nodes in a workflow graph. The state flows between these nodes, carrying the context of the current research cycle.

### Agents

1.  **PlannerAgent (`src/agents/sci/planner.py`)**: Uses LLMs and historical data to propose new experiment configurations. It balances exploration (trying new things) and exploitation (refining best results).
2.  **PlanReviewerAgent (`src/agents/sci/reviewer.py`)**: Acts as a critic. It validates proposed plans against safety rules and strategic goals, providing feedback to the Planner if revisions are needed.
3.  **ExecutorAgent (`src/agents/sci/executor.py`)**: Responsible for running experiments. It can interface with a real remote SCI service or run in a local mock mode for testing.
4.  **AnalysisAgent (`src/agents/sci/analysis.py`)**: Analyzes experiment results to compute statistics, identify Pareto frontiers, and generate high-level scientific insights using LLMs.

### Workflow Graph

The core logic is defined in `sci_loop.py` and `src/core/workflow_graph.py`. The workflow follows this high-level topology:

```mermaid
graph TD
    Start([Start]) --> Planner
    Planner --> Reviewer
    Reviewer -->|Approved| Executor
    Reviewer -->|Rejected| Planner
    Executor --> PersistenceResults[Persistence (Results)]
    PersistenceResults --> Analyzer
    Analyzer --> PersistenceInsights[Persistence (Insights)]
    PersistenceInsights -->|Continue Cycle| Planner
    PersistenceInsights -->|Budget Exhausted| End([End])
```

1.  **Planning**: The `Planner` proposes a batch of experiments.
2.  **Review**: The `Reviewer` checks the plan. If rejected, it loops back to `Planner` with feedback.
3.  **Execution**: Approved plans are executed by the `Executor` (async/parallel).
4.  **Persistence (Results)**: Raw experiment results are saved to the World Model.
5.  **Analysis**: The `Analyzer` processes results, updating the Pareto front and generating insights.
6.  **Persistence (Insights)**: Analysis insights are saved.
7.  **Loop/Terminate**: The system checks the budget. If remaining, it starts a new cycle; otherwise, it terminates.

## 📂 Project Structure

```
├── config/
│   └── default.yaml         # Configuration for agents, LLMs, and experiments
├── sci_loop.py              # Main entry point for the application
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── base.py          # Base Agent class
│   │   ├── sci/             # SCI-domain specific agent logic
│   │   │   ├── planner.py   # PlannerAgent
│   │   │   ├── reviewer.py  # PlanReviewerAgent
│   │   │   ├── executor.py  # ExecutorAgent
│   │   │   ├── analysis.py  # AnalysisAgent
│   │   │   ├── world_model.py # Data access layer (WorldModel)
│   │   │   └── structures.py # Data classes (ExperimentResult, SCIConfiguration, etc.)
│   ├── core/                # Core framework components
│   │   ├── workflow_graph.py # LangGraph node wrappers and builder
│   │   ├── state.py          # Global AgentState definition
│   │   └── world_model_base.py # Abstract base class for World Models
│   └── llm/                 # LLM client utilities
└── pyproject.toml           # Project dependencies
```

## 🚦 Getting Started

### Prerequisites

*   Python 3.12+
*   `uv` (recommended) or `pip`
*   OpenAI API Key (or compatible) for LLM features

### Installation

```bash
# Install dependencies
uv sync
# OR
pip install -r requirements.txt # (if generated)
```

### Configuration

Edit `config/default.yaml` to set your preferences, such as:
*   `llm`: API key and model selection.
*   `experiment`: Budget and cycle limits.
*   `executor`: Mock mode vs. real service URL.

### Running

Run the main loop:

```bash
# Run with default settings (Mock mode enabled by default in config)
python sci_loop.py

# Run with specific budget and cycles
python sci_loop.py --budget 10 --cycles 3

# Run against real service (disable mock)
python sci_loop.py --no-mock
```

## 🧪 Mock Service

A mock service is included (`mock_service.py`) to simulate the SCI training API for local development and testing without GPU resources.

```bash
# Start the mock service
uv run python mock_service.py
```
