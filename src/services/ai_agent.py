"""
AI Agent Service (Stage 3: The Mentor/Brain)

Sends repository data to Google Gemini and receives structured evaluation.
Uses structured "Investigation Reports" from 4 specialized agents for better analysis.
Uses Gemini's JSON mode for reliable parsing.
Now supports: Persona-based analysis (recruiter, mentor, bug_hunter, gsoc_admin)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Literal
import google.generativeai as genai

from src.core.schemas import RepoMetadata, GradeReport, RoadmapItem, Metrics
from src.core.personas import get_persona, get_persona_prompt, PERSONAS
from src.services.agents import InvestigationReport


class AIAgent:
    """Manages Gemini LLM interaction for repository grading."""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            }
        )
        self.base_system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Loads the GitGrade base persona from prompts directory."""
        possible_paths = [
            Path("prompts/gitgrade_persona.md"),
            Path(__file__).parent.parent.parent / "prompts" / "gitgrade_persona.md",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.read_text(encoding="utf-8")
        
        raise FileNotFoundError("System prompt file 'prompts/gitgrade_persona.md' not found")
    
    def _build_persona_prompt(self, persona_id: str) -> str:
        """
        Build the system prompt with the selected persona overlay.
        
        The base prompt provides structure/format.
        The persona prompt changes the LENS through which we analyze.
        """
        persona = get_persona(persona_id)
        persona_prompt = persona["prompt"]
        
        return f"""
{self.base_system_prompt}

---

## ACTIVE PERSONA: {persona["name"]} {persona["icon"]}
Focus: {persona["focus"]}
Tone: {persona["tone"]}

{persona_prompt}

Remember: You are NOW acting as {persona["name"]}. 
Your analysis, tone, and recommendations should reflect this persona.
"""
        
        raise FileNotFoundError("System prompt file 'prompts/gitgrade_persona.md' not found")
    
    def _build_user_prompt(self, metadata: RepoMetadata, investigation: Optional[InvestigationReport] = None) -> str:
        """
        Constructs the user prompt using the "Context Injection" pattern.
        
        We DO NOT send raw code to the AI - we send pre-computed FACTS.
        The scripts (agents) did the grunt work. The LLM provides intelligence.
        """
        
        if not investigation:
            # Fallback - should not happen in normal flow
            return self._build_legacy_prompt(metadata)
        
        # Build the EVIDENCE block (hard facts from our agents)
        return f"""
REPOSITORY FACTS (Pre-analyzed by investigation agents - these are 100% accurate):

{investigation.to_llm_context()}

--- IDENTITY ---
- Repository: {metadata.owner}/{metadata.repo_name}
- Homepage: {metadata.homepage_url or 'Not configured'}

YOUR TASK:
Use the FACTS above to evaluate this candidate's project.
Do NOT guess or hallucinate. If tests are missing in the facts, say so.
The numbers (file counts, commit counts, ratios) are EXACT - trust them.
Output your evaluation as JSON matching the required schema.
"""
    
    def _build_legacy_prompt(self, metadata: RepoMetadata) -> str:
        """Legacy prompt format when investigation report is unavailable."""
        return f"""
Here is the repository data for analysis:

--- FILE TREE ---
{metadata.file_tree}

--- README CONTENT ---
{metadata.readme_content}

--- RECENT COMMITS ---
{metadata.commit_log}

--- TECH STACK FILES ---
{metadata.dependency_files}

--- DETECTED INFO ---
- Language: {metadata.detected_language or 'Unknown'}
- Total Files: {metadata.total_files}
- Has Tests: {metadata.has_tests}
- Has README: {metadata.has_readme}
- Has .gitignore: {metadata.has_gitignore}
"""

    def grade(
        self, 
        metadata: RepoMetadata, 
        investigation: Optional[InvestigationReport] = None,
        persona: str = "mentor"
    ) -> GradeReport:
        """
        Sends repository data to Gemini and returns a validated GradeReport.
        
        Args:
            metadata: Repository metadata from the scraper
            investigation: Optional investigation report from 4 specialized agents
            persona: The persona to use for analysis (recruiter, mentor, bug_hunter, gsoc_admin)
            
        Returns:
            GradeReport: Validated Pydantic model with all grading data
        """
        user_prompt = self._build_user_prompt(metadata, investigation)
        
        # Build persona-enhanced system prompt
        system_prompt = self._build_persona_prompt(persona)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            raw_content = response.text
            
            # Parse JSON response
            data = json.loads(raw_content)
            
            # Add identity fields from metadata (LLM doesn't know repo name)
            data["repo_name"] = metadata.repo_name
            data["owner"] = metadata.owner
            
            # Validate and return as Pydantic model
            return GradeReport(**data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini: {e}")


# Convenience function (legacy)
def grade_repository(metadata: RepoMetadata) -> GradeReport:
    """Grades a repository using the AI agent (legacy, no investigation report)."""
    agent = AIAgent()
    return agent.grade(metadata)
