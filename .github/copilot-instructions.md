# GitHub Copilot Instructions

This file provides context to GitHub Copilot to help it generate better code for this specific project.

## Project Overview
- **Goal**: Build "GitGrade", an automated grading tool that evaluates student GitHub repositories. It acts as a "Senior Engineering Manager" persona to provide brutal but constructive feedback on employability, maintainability, and developer empathy.
- **Domain**: EdTech, Recruitment, Developer Tools, AI.
- **Core Functionality**:
    1.  Ingest GitHub repository data (File tree, README, Dependencies, Git Log).
    2.  Construct a prompt using the "GitGrade" persona.
    3.  Send to an LLM to generate a structured JSON evaluation.
    4.  Render the evaluation as a report.

## Tech Stack
- **Languages**: Python (Backend/CLI), TypeScript (Frontend/Dashboard - TBD).
- **Frameworks**: FastAPI or Flask (Backend), React (Frontend - TBD).
- **AI/LLM**: OpenAI API or similar for the grading engine.
- **Tools**: Git, Docker.

## Architecture & Patterns
- **Style**: Modular Architecture.
    - `Analyzer`: Extracts raw data from repositories.
    - `Grader`: Manages the LLM interaction and prompt engineering.
    - `Reporter`: Formats the JSON output into human-readable feedback.
- **Key Patterns**:
    - **Prompt-as-Code**: Store system prompts in version control (e.g., `prompts/`).
    - **Structured Output**: Enforce JSON schemas for LLM responses to ensure reliability.

## Development Workflow
- **Build**: `pip install -r requirements.txt`
- **Run**: `python src/main.py` (Target)
- **Test**: `pytest`

## Coding Conventions
- **Naming**: `snake_case` for Python, `camelCase` for JavaScript/TypeScript.
- **Error Handling**: Graceful degradation if the LLM fails or returns invalid JSON.
- **Comments**: Document the "Why" behind prompt engineering decisions.

## Key Files & Directories
- `prompts/`: Contains the system prompts (e.g., `gitgrade_persona.md`).
- `src/`: Application source code.
- `.github/copilot-instructions.md`: This file.
