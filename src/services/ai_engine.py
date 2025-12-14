"""
GitGrade Hybrid AI Engine (The Dual-Brain)

A cost-optimized, performance-focused architecture:
- GROQ (Llama-3-70b): Ultra-fast inference (~1s) for "fast" mode
- GEMINI (1.5-Pro): Massive context (2M tokens) for "deep" mode

This is the ULTIMATE hackathon architecture:
1. Speed: Groq gives instant gratification
2. Power: Gemini reads entire codebases
3. Cost: Both have generous free tiers

Error Handling:
- Graceful fallback if one engine fails
- Detailed error messages for debugging
- JSON validation before returning
"""

import os
import json
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum

# AI SDKs
import google.generativeai as genai
from groq import Groq

# Local imports
from src.core.schemas import RepoMetadata, GradeReport, RoadmapItem, Metrics
from src.core.personas import get_persona, get_persona_prompt, PERSONAS, PersonaType, ModeType
from src.services.agents import InvestigationReport


# ==========================================
# Error Types
# ==========================================

class AIEngineError(Exception):
    """Base exception for AI Engine errors."""
    pass


class GroqError(AIEngineError):
    """Error from Groq API."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"🚀 Groq Error: {message}")
        self.original_error = original_error


class GeminiError(AIEngineError):
    """Error from Gemini API."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"🧠 Gemini Error: {message}")
        self.original_error = original_error


class JSONParseError(AIEngineError):
    """LLM returned invalid JSON."""
    def __init__(self, raw_response: str, parse_error: str):
        super().__init__(f"Invalid JSON from LLM: {parse_error}")
        self.raw_response = raw_response


# ==========================================
# Response Schema
# ==========================================

GRADE_REPORT_SCHEMA = """
You MUST respond with valid JSON matching this EXACT schema. Follow it PRECISELY:

{
    "score": <integer 0-100, employability score>,
    "level": "<MUST be one of: 'Beginner', 'Intermediate', 'Advanced'>",
    "headline": "<5-7 word catchy headline about this repo>",
    "summary": "<2-3 sentence executive summary like a recruiter's notes>",
    "critique_tone": "<witty one-liner roast or praise>",
    "recruiter_verdict": "<one of: 'Strong Hire', 'Hire', 'Lean Hire', 'Lean No Hire', 'No Hire' with 1-sentence justification>",
    "resume_bullets": [
        "<bullet point 1 for CV>",
        "<bullet point 2 for CV>",
        "<bullet point 3 for CV>"
    ],
    "interview_question": "<technical interview question based on THEIR specific code>",
    "red_flags": [
        "<issue that makes recruiters hesitate>",
        "<another issue if applicable>"
    ],
    "green_flags": [
        "<positive signal that impresses recruiters>",
        "<another positive if applicable>"
    ],
    "metrics": {
        "structure_rating": "<MUST be one of: 'A', 'B', 'C', 'D', 'F'>",
        "docs_rating": "<MUST be one of: 'A', 'B', 'C', 'D', 'F'>",
        "test_rating": "<MUST be one of: 'A', 'B', 'C', 'D', 'F'>",
        "commit_rating": "<MUST be one of: 'A', 'B', 'C', 'D', 'F'>",
        "employability_score": <integer 0-100>
    },
    "roadmap": [
        {
            "step": "<short action title like 'Add Unit Tests'>",
            "description": "<SPECIFIC commands and files to create/modify>",
            "priority": "<MUST be one of: 'Critical', 'High', 'Medium', 'Low'>",
            "impact": "<what this fixes for employability>"
        }
    ],
    "deployment_status": "<one of: 'live', 'broken', 'unknown'>"
}

CRITICAL RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no explanations
2. All 'level' values MUST be exactly: 'Beginner', 'Intermediate', or 'Advanced'
3. All 'priority' values MUST use Title Case: 'Critical', 'High', 'Medium', 'Low'
4. All rating fields MUST be single letters: 'A', 'B', 'C', 'D', or 'F'
5. Include at least 3 resume_bullets and 3 roadmap items
"""


# ==========================================
# The Hybrid AI Engine
# ==========================================

class HybridAIEngine:
    """
    Dual-brain AI engine for optimal cost/performance.
    
    Routing Logic:
    - "fast" mode → Groq (Llama-3-70b) for sub-second responses
    - "deep" mode → Gemini (1.5-Pro) for massive context analysis
    
    Both support persona overlays for customized analysis.
    """
    
    def __init__(self):
        """Initialize both AI engines with API keys from environment."""
        # ===== GROQ SETUP (The Sprinter) =====
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.groq_client: Optional[Groq] = None
        
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                print("✅ Groq client initialized (llama-3.3-70b-versatile)")
            except Exception as e:
                print(f"⚠️ Groq initialization failed: {e}")
        else:
            print("⚠️ GROQ_API_KEY not set - fast mode will fallback to Gemini")
        
        # ===== GEMINI SETUP (The Professor) =====
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.gemini_model = None
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "max_output_tokens": 4096,
                        "response_mime_type": "application/json",
                    }
                )
                print("✅ Gemini client initialized (gemini-2.0-flash)")
            except Exception as e:
                print(f"⚠️ Gemini initialization failed: {e}")
        else:
            print("⚠️ GEMINI_API_KEY not set - deep mode unavailable")
        
        # Validate at least one engine is available
        if not self.groq_client and not self.gemini_model:
            raise AIEngineError(
                "No AI engines available! Set GROQ_API_KEY or GEMINI_API_KEY in .env"
            )
    
    def _build_persona_system_prompt(self, persona_id: str) -> str:
        """Build system prompt with persona overlay."""
        persona = get_persona(persona_id)
        
        return f"""You are analyzing a GitHub repository.

## YOUR PERSONA: {persona["name"]} {persona["icon"]}
Focus: {persona["focus"]}
Tone: {persona["tone"]}

{persona["prompt"]}

{GRADE_REPORT_SCHEMA}
"""
    
    def _build_repo_context(
        self, 
        metadata: RepoMetadata, 
        investigation: Optional[InvestigationReport],
        mode: ModeType
    ) -> str:
        """Build repository context based on analysis mode."""
        
        context_parts = []
        
        # Always include identity
        context_parts.append(f"""
=== REPOSITORY IDENTITY ===
Name: {metadata.owner}/{metadata.repo_name}
Homepage: {metadata.homepage_url or 'Not configured'}
Language: {metadata.detected_language or 'Unknown'}
Total Files: {metadata.total_files}
""")
        
        # Include investigation report if available
        if investigation:
            context_parts.append(f"""
=== INVESTIGATION REPORT (Pre-analyzed by specialized agents) ===
{investigation.to_llm_context()}
""")
        
        # Mode-specific context
        if mode == "fast":
            # Fast mode: Just metadata and structure
            context_parts.append(f"""
=== FILE STRUCTURE (Summary) ===
{metadata.file_tree[:5000]}

=== README (First 3000 chars) ===
{metadata.readme_content[:3000] if metadata.readme_content else 'No README found'}

=== DEPENDENCIES ===
{metadata.dependency_files[:2000] if metadata.dependency_files else 'No dependency files found'}

=== RECENT COMMITS (Last 30) ===
{metadata.commit_log[:2000] if metadata.commit_log else 'No commits found'}
""")
        
        elif mode == "deep":
            # Deep mode: Full code dump (Gemini can handle 2M tokens)
            context_parts.append(f"""
=== FULL FILE STRUCTURE ===
{metadata.file_tree}

=== COMPLETE README ===
{metadata.readme_content if metadata.readme_content else 'No README found'}

=== ALL DEPENDENCIES ===
{metadata.dependency_files if metadata.dependency_files else 'No dependency files found'}

=== FULL COMMIT HISTORY ===
{metadata.commit_log if metadata.commit_log else 'No commits found'}
""")
        
        return "\n".join(context_parts)
    
    def _normalize_response(self, data: dict) -> dict:
        """
        Fix common LLM response variations to match our strict Pydantic schema.
        
        This makes the system robust against LLM inconsistencies like:
        - Lowercase priorities ('high' → 'High')
        - Wrong field names ('title' → 'step')
        - Missing required fields (add defaults)
        """
        
        # Priority mapping (LLMs often return lowercase)
        priority_map = {
            'critical': 'Critical', 'high': 'High', 
            'medium': 'Medium', 'low': 'Low',
            'CRITICAL': 'Critical', 'HIGH': 'High',
            'MEDIUM': 'Medium', 'LOW': 'Low'
        }
        
        # Level mapping
        level_map = {
            'beginner': 'Beginner', 'intermediate': 'Intermediate', 
            'advanced': 'Advanced', 'BEGINNER': 'Beginner',
            'INTERMEDIATE': 'Intermediate', 'ADVANCED': 'Advanced'
        }
        
        # Rating letter mapping (ensure uppercase single letters)
        rating_map = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'f': 'F'}
        
        # === Fix 'level' field ===
        if 'level' not in data:
            score = data.get('score', 50)
            if score >= 75:
                data['level'] = 'Advanced'
            elif score >= 40:
                data['level'] = 'Intermediate'
            else:
                data['level'] = 'Beginner'
        else:
            data['level'] = level_map.get(data['level'], data['level'])
        
        # === Fix missing required fields ===
        if 'headline' not in data:
            data['headline'] = f"Repository Analysis: {data.get('score', 50)}/100"
        
        if 'critique_tone' not in data:
            data['critique_tone'] = data.get('summary', 'No critique provided')[:100]
        
        if 'recruiter_verdict' not in data:
            score = data.get('score', 50)
            if score >= 80:
                data['recruiter_verdict'] = 'Strong Hire - Shows professional quality work'
            elif score >= 60:
                data['recruiter_verdict'] = 'Hire - Demonstrates solid fundamentals'
            elif score >= 40:
                data['recruiter_verdict'] = 'Lean Hire - Has potential with some gaps'
            else:
                data['recruiter_verdict'] = 'Lean No Hire - Needs significant improvement'
        
        if 'resume_bullets' not in data:
            data['resume_bullets'] = [
                'Developed and maintained open source project',
                'Implemented key features using modern practices',
                'Contributed to project documentation'
            ]
        
        if 'interview_question' not in data:
            data['interview_question'] = 'Can you walk me through the architecture decisions you made in this project?'
        
        if 'red_flags' not in data:
            data['red_flags'] = []
        
        if 'green_flags' not in data:
            data['green_flags'] = []
        
        # === Fix metrics ===
        if 'metrics' not in data:
            data['metrics'] = {}
        
        metrics = data['metrics']
        
        # Map old field names to new ones
        old_to_new_metrics = {
            'complexity': 'structure_rating',
            'maintainability': 'structure_rating', 
            'documentation': 'docs_rating',
            'testing': 'test_rating'
        }
        
        for old_name, new_name in old_to_new_metrics.items():
            if old_name in metrics and new_name not in metrics:
                # Convert 1-5 scale to letter grade
                val = metrics[old_name]
                if isinstance(val, int):
                    if val >= 5:
                        metrics[new_name] = 'A'
                    elif val >= 4:
                        metrics[new_name] = 'B'
                    elif val >= 3:
                        metrics[new_name] = 'C'
                    elif val >= 2:
                        metrics[new_name] = 'D'
                    else:
                        metrics[new_name] = 'F'
        
        # Ensure required metric fields exist with defaults
        for field in ['structure_rating', 'docs_rating', 'test_rating']:
            if field not in metrics:
                metrics[field] = 'C'  # Default to average
            elif metrics[field] in rating_map:
                metrics[field] = rating_map[metrics[field]]
        
        if 'commit_rating' not in metrics:
            metrics['commit_rating'] = 'C'
        elif metrics.get('commit_rating') in rating_map:
            metrics['commit_rating'] = rating_map[metrics['commit_rating']]
            
        if 'employability_score' not in metrics:
            metrics['employability_score'] = data.get('score', 50)
        
        data['metrics'] = metrics
        
        # === Fix roadmap ===
        if 'roadmap' not in data:
            data['roadmap'] = [
                {'step': 'Add comprehensive README', 'description': 'Include project overview, installation, and usage', 'priority': 'High', 'impact': 'First impression for recruiters'},
                {'step': 'Add unit tests', 'description': 'Implement test coverage for core functionality', 'priority': 'High', 'impact': 'Demonstrates quality mindset'},
                {'step': 'Setup CI/CD', 'description': 'Add GitHub Actions for automated testing', 'priority': 'Medium', 'impact': 'Shows DevOps awareness'}
            ]
        else:
            # Fix each roadmap item
            fixed_roadmap = []
            for item in data['roadmap']:
                fixed_item = {}
                
                # Map 'title' to 'step' (common LLM mistake)
                fixed_item['step'] = item.get('step') or item.get('title', 'Improve codebase')
                fixed_item['description'] = item.get('description', 'See step title for details')
                
                # Fix priority case
                priority = item.get('priority', 'Medium')
                fixed_item['priority'] = priority_map.get(priority, priority)
                if fixed_item['priority'] not in ['Critical', 'High', 'Medium', 'Low']:
                    fixed_item['priority'] = 'Medium'  # Default fallback
                
                fixed_item['impact'] = item.get('impact', 'Improves overall code quality')
                
                fixed_roadmap.append(fixed_item)
            
            data['roadmap'] = fixed_roadmap if fixed_roadmap else [
                {'step': 'Add tests', 'description': 'Implement unit tests', 'priority': 'High', 'impact': 'Quality signal'}
            ]
        
        # === Fix deployment status ===
        if 'deployment_status' not in data:
            data['deployment_status'] = 'unknown'
        
        # === Fix file_diagram and assets (not from LLM) ===
        if 'file_diagram' not in data:
            data['file_diagram'] = []
        if 'assets' not in data:
            data['assets'] = []
        
        return data
    
    def _parse_and_validate_response(
        self, 
        raw_response: str, 
        metadata: RepoMetadata
    ) -> GradeReport:
        """Parse LLM response and validate as GradeReport."""
        
        # Clean up response (remove markdown code blocks if present)
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise JSONParseError(raw_response, str(e))
        
        # Inject identity fields (LLM doesn't know these)
        data["repo_name"] = metadata.repo_name
        data["owner"] = metadata.owner
        
        # === RESPONSE NORMALIZER ===
        # Fix common LLM output variations to match our strict schema
        data = self._normalize_response(data)

        # === Deterministic scoring enhancement ===
        # Compute a deterministic employability score from repository artifacts
        try:
            computed = self._compute_employability_score(metadata)
        except Exception:
            computed = data.get('metrics', {}).get('employability_score', data.get('score', 50))

        # Blend LLM score with deterministic score: prefer deterministic (80%) but allow LLM nuance (20%)
        llm_score = data.get('score', computed)
        try:
            final_score = int(round(0.8 * float(computed) + 0.2 * float(llm_score)))
        except Exception:
            final_score = int(computed)

        data['score'] = max(0, min(100, final_score))
        # Ensure metrics.employability_score reflects final score
        if 'metrics' not in data:
            data['metrics'] = {}
        data['metrics']['employability_score'] = data['score']
        
        # Validate and create GradeReport
        try:
            return GradeReport(**data)
        except Exception as e:
            raise AIEngineError(f"Response validation failed: {e}")

    def _compute_employability_score(self, metadata: RepoMetadata) -> int:
        """
        Deterministic scoring algorithm based on repository artifacts.

        Categories (100 total):
        - Code Quality: 25
        - Documentation: 20
        - Testing & CI/CD: 15
        - Git Hygiene: 15
        - Project Health: 10
        - Community Engagement: 10
        - Professional Setup: 5
        """
        # Safely extract hard metrics if present
        hm = getattr(metadata, 'hard_metrics', None)

        def score_from_percent(pct, max_points):
            return round(max_points * (max(0, min(100, pct)) / 100.0))

        # Code Quality (25): use structure_score and commit_quality_score
        structure = hm.structure_score if hm else 50
        commit_q = hm.commit_quality_score if hm else 50
        code_quality_pct = (0.6 * structure + 0.4 * commit_q)
        code_quality = score_from_percent(code_quality_pct, 25)

        # Documentation (20): use docs_score and README flag
        docs = hm.docs_score if hm else 40
        readme_bonus = 10 if getattr(metadata, 'has_readme', False) else 0
        docs_pct = min(100, docs + readme_bonus)
        docs_score = score_from_percent(docs_pct, 20)

        # Testing & CI/CD (15): test_score and presence of CI config in files
        tests = hm.test_score if hm else 0
        has_ci = 1 if '.github' in getattr(metadata, 'file_tree', '') or 'github/workflows' in getattr(metadata, 'file_tree', '') else 0
        tests_pct = min(100, tests + (20 if has_ci else 0))
        tests_score = score_from_percent(tests_pct, 15)

        # Git Hygiene (15): commit quality and commit history presence
        commit_pct = commit_q
        recent_activity = 20 if getattr(metadata, 'commit_log', '').strip() else 0
        git_hygiene_pct = min(100, 0.7 * commit_pct + 0.3 * recent_activity)
        git_hygiene = score_from_percent(git_hygiene_pct, 15)

        # Project Health (10): recent activity, dependencies present
        recent = 100 if getattr(metadata, 'commit_log', '').strip() else 0
        deps = 20 if getattr(metadata, 'dependency_files', '').strip() else 0
        project_health_pct = min(100, 0.7 * recent + 0.3 * deps)
        project_health = score_from_percent(project_health_pct, 10)

        # Community Engagement (10): stars/forks/watchers/contributors
        stars = getattr(metadata, 'stars', 0) or 0
        forks = getattr(metadata, 'forks', 0) or 0
        watchers = getattr(metadata, 'watchers', 0) or 0
        contributors = getattr(metadata, 'contributors', 0) or 0

        # Simple normalized engagement score (cap influence)
        eng_score_raw = min(100, (min(stars, 100) * 0.4) + (min(forks, 100) * 0.2) + (min(watchers, 100) * 0.2) + (min(contributors, 50) * 0.2))
        engagement = score_from_percent(eng_score_raw, 10)

        # Professional Setup (5): license, gitignore, SECURITY, CODE_OF_CONDUCT presence
        prof = 0
        prof += 2 if getattr(metadata, 'has_readme', False) else 0
        prof += 2 if getattr(metadata, 'has_gitignore', False) else 0
        # Note: License detection often via investigation; try to read issues
        license_present = any('license' in (issue.lower()) for issue in (hm.issues if hm else [])) if hm else False
        prof += 1 if license_present else 0
        prof = min(5, prof)

        total = code_quality + docs_score + tests_score + git_hygiene + project_health + engagement + prof

        # Ensure within bounds
        total = max(0, min(100, int(total)))
        return total
    
    # ==========================================
    # GROQ ENGINE (Fast Mode)
    # ==========================================
    
    def _analyze_with_groq(
        self,
        metadata: RepoMetadata,
        investigation: Optional[InvestigationReport],
        persona: PersonaType
    ) -> GradeReport:
        """
        Fast analysis using Groq's Llama-3-70b.
        
        Optimized for:
        - Sub-second inference
        - 8k token context limit
        - JSON mode output
        """
        if not self.groq_client:
            raise GroqError("Groq client not initialized")
        
        print("🚀 Speed Mode: Using Groq (Llama-3-70b)...")
        
        system_prompt = self._build_persona_system_prompt(persona)
        user_content = self._build_repo_context(metadata, investigation, mode="fast")
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2048
            )
            
            raw_content = response.choices[0].message.content or ""
            if not raw_content:
                raise GroqError("Empty response from Groq")
            return self._parse_and_validate_response(raw_content, metadata)
            
        except JSONParseError:
            raise
        except GroqError:
            raise
        except Exception as e:
            raise GroqError(str(e), e)
    
    # ==========================================
    # GEMINI ENGINE (Deep Mode)
    # ==========================================
    
    def _analyze_with_gemini(
        self,
        metadata: RepoMetadata,
        investigation: Optional[InvestigationReport],
        persona: PersonaType
    ) -> GradeReport:
        """
        Deep analysis using Gemini 1.5 Pro.
        
        Optimized for:
        - 2M token context window
        - Full codebase analysis
        - Security vulnerability detection
        """
        if not self.gemini_model:
            raise GeminiError("Gemini client not initialized")
        
        print("🧠 Deep Mode: Using Gemini 1.5 Pro...")
        
        system_prompt = self._build_persona_system_prompt(persona)
        user_content = self._build_repo_context(metadata, investigation, mode="deep")
        
        full_prompt = f"{system_prompt}\n\n{user_content}"
        
        try:
            response = self.gemini_model.generate_content(full_prompt)
            raw_content = response.text or ""
            if not raw_content:
                raise GeminiError("Empty response from Gemini")
            return self._parse_and_validate_response(raw_content, metadata)
            
        except JSONParseError:
            raise
        except GeminiError:
            raise
        except Exception as e:
            raise GeminiError(str(e), e)
    
    # ==========================================
    # MAIN ROUTING METHOD
    # ==========================================
    
    def analyze(
        self,
        metadata: RepoMetadata,
        investigation: Optional[InvestigationReport] = None,
        mode: ModeType = "fast",
        persona: PersonaType = "mentor"
    ) -> GradeReport:
        """
        Main entry point: Routes to the appropriate AI engine.
        
        Args:
            metadata: Repository metadata from scraper
            investigation: Structured investigation report from agents
            mode: "fast" (Groq) or "deep" (Gemini)
            persona: Analysis persona (recruiter, mentor, bug_hunter, gsoc_admin)
        
        Returns:
            GradeReport: Validated grading report
        
        Raises:
            AIEngineError: If analysis fails with no fallback available
        """
        
        # ===== FAST MODE: Try Groq first =====
        if mode == "fast":
            if self.groq_client:
                try:
                    return self._analyze_with_groq(metadata, investigation, persona)
                except GroqError as e:
                    print(f"⚠️ Groq failed: {e}, falling back to Gemini...")
                    if self.gemini_model:
                        return self._analyze_with_gemini(metadata, investigation, persona)
                    raise
            elif self.gemini_model:
                # No Groq available, use Gemini for fast mode too
                print("⚠️ Groq unavailable, using Gemini for fast mode...")
                return self._analyze_with_gemini(metadata, investigation, persona)
            else:
                raise AIEngineError("No AI engine available for fast mode")
        
        # ===== DEEP MODE: Use Gemini =====
        elif mode == "deep":
            if self.gemini_model:
                try:
                    return self._analyze_with_gemini(metadata, investigation, persona)
                except GeminiError as e:
                    print(f"⚠️ Gemini failed: {e}, no fallback for deep mode")
                    raise
            else:
                raise AIEngineError(
                    "Deep mode requires Gemini. Set GEMINI_API_KEY in .env"
                )
        
        else:
            raise AIEngineError(f"Unknown mode: {mode}")


# ==========================================
# Legacy Compatibility
# ==========================================

class AIAgent:
    """
    Legacy wrapper for backward compatibility.
    
    Use HybridAIEngine directly for new code.
    """
    
    def __init__(self):
        self.engine = HybridAIEngine()
    
    def grade(
        self,
        metadata: RepoMetadata,
        investigation: Optional[InvestigationReport] = None,
        persona: str = "mentor",
        mode: str = "fast"
    ) -> GradeReport:
        """Grade a repository using the hybrid engine."""
        # Cast to proper types
        mode_typed: ModeType = "deep" if mode == "deep" else "fast"
        persona_typed: PersonaType = persona if persona in ["recruiter", "mentor", "bug_hunter", "gsoc_admin"] else "mentor"  # type: ignore
        
        return self.engine.analyze(
            metadata=metadata,
            investigation=investigation,
            mode=mode_typed,
            persona=persona_typed
        )
