"""
Orchestrator (Stage 4: The Aggregator)

The main pipeline that connects all services:
1. Investigation Agents -> Structured Report (Structure, Context, Quality, History)
2. Scraper (GitHub) -> RepoMetadata + Assets
3. Hybrid AI Engine -> GradeReport (Groq for fast, Gemini for deep)
4. Deployment Verification -> Live status

This is the single entry point for grading a repository.

Hybrid AI Strategy:
- Fast Mode: Groq (Llama-3-70b) for ~1 second responses
- Deep Mode: Gemini (1.5-Pro) for 2M token context analysis
"""

import asyncio
import httpx
import re
from typing import Optional, Literal, Tuple

from src.core.schemas import RepoMetadata, HardMetrics, GradeReport, FileNode, Asset
from src.core.personas import get_persona, get_persona_prompt, PersonaType, ModeType
from src.services.github import scrape_github_repo, GitHubScraper
from src.services.linter import analyze_repository as run_linter
from src.services.ai_engine import HybridAIEngine, AIEngineError
from src.services.agents import RepoInvestigator, InvestigationReport


class Orchestrator:
    """
    Coordinates the entire grading pipeline.
    
    Pipeline Flow:
        URL -> [Investigation Agents] -> InvestigationReport
            -> [Scraper] -> RepoMetadata (for assets/files)
            -> [AI Agent + Investigation Context + Persona] -> GradeReport
            -> [Deployment Check] -> Live Status
    
    Supports:
        - mode: "fast" (30s, metadata only) or "deep" (2-5min, full code analysis)
        - persona: "recruiter", "mentor", "bug_hunter", "gsoc_admin"
    """
    
    async def grade(
        self, 
        repo_url: str, 
        deployed_link: Optional[str] = None,
        mode: ModeType = "fast",
        persona: PersonaType = "mentor"
    ) -> GradeReport:
        """
        Main entry point: grades a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
            deployed_link: Optional deployment URL to verify
            mode: Analysis depth - "fast" or "deep"
            persona: Viewer persona - changes analysis focus and tone
            
        Returns:
            GradeReport: Complete grading result with score, summary, and roadmap
        """
        # Parse owner/repo from URL
        owner, repo_name = self._parse_url(repo_url)
        
        # Stage 1: Run Investigation Agents (4 specialized agents)
        # Deep mode enables full file parsing with UniversalParser
        investigation_report = await self._investigate(owner, repo_name, deep=mode == "deep")
        
        # Stage 2: Scrape repository data (for assets, file nodes, etc.)
        metadata = await self._scrape(repo_url)
        
        # Stage 3: Calculate hard metrics  
        hard_metrics = self._analyze(metadata)
        file_nodes = self._update_file_health(metadata.file_nodes, hard_metrics)
        
        # Update file health based on linter findings
        file_nodes = self._update_file_health(metadata.file_nodes, hard_metrics)
        
        # Stage 4: Get AI evaluation using Hybrid Engine (Groq for fast, Gemini for deep)
        persona_info = get_persona(persona)
        ai_engine = HybridAIEngine()
        
        try:
            report = ai_engine.analyze(
                metadata=metadata, 
                investigation=investigation_report, 
                mode=mode,
                persona=persona
            )
        except AIEngineError as e:
            # Graceful degradation: Return a minimal report with error info
            print(f"⚠️ AI Engine failed: {e}")
            raise RuntimeError(f"Analysis failed: {e}")
        
        # Add persona info to report for frontend display
        report.persona_used = persona_info["name"]
        report.analysis_mode = mode
        
        # Stage 5: Verify deployment
        final_link = deployed_link or metadata.homepage_url
        deployment_status = await self._verify_deployment(final_link)
        
        # Merge in the new fields
        report.deployed_link = final_link if deployment_status != "unknown" else None
        report.deployment_status = deployment_status
        report.file_diagram = file_nodes
        report.assets = metadata.assets
        
        return report
    
    def _parse_url(self, repo_url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        pattern = r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.search(pattern, repo_url)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    async def _investigate(self, owner: str, repo_name: str, deep: bool = False) -> InvestigationReport:
        """
        Stage 1: Run 4 specialized investigation agents.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            deep: If True, enables full file parsing with UniversalParser
        """
        investigator = RepoInvestigator(owner, repo_name)
        # The investigator now automatically does deep parsing via UniversalParser
        return await investigator.investigate()
    
    async def _scrape(self, repo_url: str) -> RepoMetadata:
        """Stage 2: Fetch repository data from GitHub API."""
        return await scrape_github_repo(repo_url)
    
    def _analyze(self, metadata: RepoMetadata) -> HardMetrics:
        """Stage 3: Run static analysis on repository data."""
        return run_linter(metadata)
    
    def _update_file_health(self, file_nodes: list, hard_metrics: HardMetrics) -> list:
        """Update file node health status based on linter issues."""
        updated_nodes = []
        
        # Build issue patterns from hard metrics
        issue_keywords = set()
        for issue in hard_metrics.issues:
            issue_lower = issue.lower()
            if "readme" in issue_lower:
                issue_keywords.add("readme")
            if ".gitignore" in issue_lower:
                issue_keywords.add(".gitignore")
            if "test" in issue_lower:
                issue_keywords.add("test")
        
        for node in file_nodes:
            node_copy = FileNode(
                name=node.name,
                path=node.path,
                type=node.type,
                health=node.health,
                issues=list(node.issues)
            )
            
            # Apply health checks
            name_lower = node.name.lower()
            
            # Critical issues (red)
            if name_lower in [".env", "secrets.json", "credentials.json"]:
                node_copy.health = "critical"
                node_copy.issues.append("Sensitive file should not be committed")
            elif name_lower == "readme.md" and "readme" in issue_keywords:
                node_copy.health = "warning"
                node_copy.issues.append("README needs improvement")
            elif node.type == "folder" and name_lower in ["test", "tests", "__tests__", "spec"]:
                if hard_metrics.test_score < 50:
                    node_copy.health = "warning"
                    node_copy.issues.append("Tests may be insufficient")
            
            updated_nodes.append(node_copy)
        
        return updated_nodes
    
    async def _verify_deployment(self, url: Optional[str]) -> Literal["live", "broken", "unknown"]:
        """Stage 4: Check if deployment link is working."""
        if not url:
            return "unknown"
        
        # Ensure URL has scheme
        if not url.startswith("http"):
            url = f"https://{url}"
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.head(url)
                
                if 200 <= response.status_code < 400:
                    return "live"
                else:
                    return "broken"
        except Exception:
            return "broken"


async def grade_repository(
    repo_url: str, 
    deployed_link: Optional[str] = None,
    mode: ModeType = "fast",
    persona: PersonaType = "mentor"
) -> GradeReport:
    """
    Convenience function to grade a repository.
    
    Args:
        repo_url: GitHub repository URL
        deployed_link: Optional deployment URL to verify
        mode: "fast" (Groq ~1s) or "deep" (Gemini ~20s)
        persona: Analysis persona (recruiter, mentor, bug_hunter, gsoc_admin)
    
    Usage:
        report = await grade_repository("https://github.com/user/repo")
        print(report.score)  # 85
        print(report.summary)  # "Well-structured project..."
    """
    orchestrator = Orchestrator()
    return await orchestrator.grade(repo_url, deployed_link, mode=mode, persona=persona)


def grade_repository_sync(
    repo_url: str,
    mode: ModeType = "fast",
    persona: PersonaType = "mentor"  
) -> GradeReport:
    """
    Synchronous wrapper for environments that can't use async.
    
    Usage:
        report = grade_repository_sync("https://github.com/user/repo")
    """
    return asyncio.run(grade_repository(repo_url, mode=mode, persona=persona))
