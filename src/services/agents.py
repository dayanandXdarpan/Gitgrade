"""
GitGrade Investigation Agents

4 Specialized Agents that extract structured data for the LLM:
1. Structure Agent (The Architect) - Maps file tree and categorizes files
2. Context Agent (The Librarian) - Extracts README and dependencies
3. Quality Agent (The Inspector) - Calculates metrics and detects issues
4. History Agent (The Historian) - Analyzes commit patterns

These agents produce a structured "Investigation Report" that the LLM uses
to generate advice, rather than parsing raw code.

Now includes the UniversalParser for handling ANY file type:
- AI/ML: Jupyter Notebooks (.ipynb) → Extracts code cells
- DevOps: Docker, K8s, CI/CD → Security analysis
- Java/C++: Deep folder structures → Flattened tree
"""

import os
import re
import json
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter

# Import the Universal Parser
from .universal_parser import UniversalParser, ParsedRepo, ParsedFile


# ==========================================
# Data Classes for Agent Reports
# ==========================================

@dataclass
class FileCategory:
    """Categorized file information"""
    code_files: List[str] = field(default_factory=list)
    asset_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    doc_files: List[str] = field(default_factory=list)


@dataclass
class StructureReport:
    """Output from the Structure Agent"""
    file_tree: str
    total_files: int
    total_folders: int
    entry_points: List[str]  # Main files like main.py, index.js
    categories: FileCategory
    root_clutter: int  # Files in root (too many = messy)
    max_depth: int
    structure_grade: str  # "Clean", "Moderate", "Messy"
    issues: List[str]


@dataclass
class ContextReport:
    """Output from the Context Agent"""
    readme_exists: bool
    readme_length: int
    readme_quality: str  # "Missing", "Sparse", "Good", "Excellent"
    readme_has_sections: bool  # Has headers like ## Installation
    detected_stack: List[str]  # ["React", "FastAPI", "PostgreSQL"]
    dependency_count: int
    has_lockfile: bool  # package-lock.json, poetry.lock
    license_type: Optional[str]
    issues: List[str]


@dataclass
class QualityReport:
    """Output from the Quality Agent"""
    has_tests: bool
    test_file_count: int
    has_ci_cd: bool  # .github/workflows, .gitlab-ci.yml
    has_linter_config: bool  # .eslintrc, pylint.rc
    has_formatter_config: bool  # .prettierrc, black.toml
    has_gitignore: bool
    gitignore_quality: str  # "Missing", "Basic", "Good"
    complexity_warnings: List[str]
    security_warnings: List[str]
    quality_grade: str  # "Poor", "Fair", "Good", "Excellent"
    issues: List[str]


@dataclass
class CommitPattern:
    """Commit pattern analysis"""
    total_commits: int
    unique_authors: int
    date_range_days: int
    commits_per_day: float
    is_cramming: bool  # All commits in short period
    is_consistent: bool  # Spread over time


@dataclass  
class HistoryReport:
    """Output from the History Agent"""
    commit_count: int
    pattern: CommitPattern
    lazy_commits: int  # "update", "fix", "wip"
    lazy_commit_ratio: float
    conventional_commits: int  # "feat:", "fix:", "docs:"
    conventional_ratio: float
    sample_messages: List[str]
    commit_quality: str  # "Amateur", "Developing", "Professional"
    issues: List[str]


@dataclass
class InvestigationReport:
    """Complete report from all agents"""
    structure: StructureReport
    context: ContextReport
    quality: QualityReport
    history: HistoryReport
    # Universal Parser results (optional, populated for deep analysis)
    parsed_repo: Optional[ParsedRepo] = None
    
    def to_llm_context(self) -> str:
        """
        Convert to a text format optimized for LLM consumption.
        
        Structured around the 5 KEY AREAS recruiters/mentors evaluate:
        1. The "Storefront" (Documentation)
        2. The "Skeleton" (File Structure)  
        3. The "Work Ethic" (Commit History)
        4. The "Quality Signals" (Code Hygiene)
        5. The "Real-World Value" (Uniqueness & Completeness)
        """
        lines = [
            "=" * 50,
            "RECRUITER'S VIEW: 5 KEY AREAS ANALYSIS",
            "=" * 50,
            "",
            
            # ===== AREA 1: THE STOREFRONT =====
            "## 1. THE STOREFRONT (First Impressions - Documentation)",
            "   What recruiters see in the first 7 seconds:",
            "",
            f"   README.md Quality: {self.context.readme_quality}",
            f"   README Length: {self.context.readme_length} characters {'(Too Short!)' if self.context.readme_length < 200 else '(Good length)' if self.context.readme_length > 500 else ''}",
            f"   Has Setup Instructions: {self.context.readme_has_sections}",
            f"   License: {self.context.license_type or '❌ MISSING (looks unprofessional)'}",
            f"   Project Description: {'Present' if self.context.readme_length > 0 else '❌ MISSING'}",
            "",
            
            # ===== AREA 2: THE SKELETON =====
            "## 2. THE SKELETON (File Structure & Organization)",
            "   Does this look organized or like a messy bedroom?",
            "",
            f"   Organization Grade: {self.structure.structure_grade}",
            f"   Root Clutter: {self.structure.root_clutter} files in root {'❌ (MESSY - dump everything in root)' if self.structure.root_clutter > 10 else '✅ (Clean)' if self.structure.root_clutter <= 5 else '⚠️ (Getting cluttered)'}",
            f"   Has /src or /app folder: {'✅ Yes' if any('src/' in f or 'app/' in f for f in self.structure.categories.code_files[:20]) else '❌ No organized code folder'}",
            f"   Entry Points: {', '.join(self.structure.entry_points[:5]) or 'None detected'}",
            f"   Total Files: {self.structure.total_files} | Folders: {self.structure.total_folders}",
            f"   Looks Like Boilerplate: {'⚠️ Possibly CRA/Vite default' if self.structure.total_files < 15 else 'Custom structure'}",
            "",
            f"   File Breakdown:",
            f"      Code Files: {len(self.structure.categories.code_files)}",
            f"      Test Files: {len(self.structure.categories.test_files)}",
            f"      Config Files: {len(self.structure.categories.config_files)}",
            f"      Asset Files: {len(self.structure.categories.asset_files)}",
            f"      Doc Files: {len(self.structure.categories.doc_files)}",
            "",
            
            # ===== AREA 3: THE WORK ETHIC =====
            "## 3. THE WORK ETHIC (Commit History & Consistency)",
            "   How did they build this? Cramming or consistent effort?",
            "",
            f"   Commit Quality Grade: {self.history.commit_quality}",
            f"   Total Commits: {self.history.commit_count}",
            f"   Work Pattern: {'🚨 CRAMMING DETECTED (all work done last minute)' if self.history.pattern.is_cramming else '✅ Consistent work pattern' if self.history.pattern.is_consistent else '⚠️ Irregular commits'}",
            f"   Lazy Commit Messages: {self.history.lazy_commits} ({self.history.lazy_commit_ratio:.0%}) {'❌ Too many vague commits' if self.history.lazy_commit_ratio > 0.3 else ''}",
            f"   Conventional Commits (feat/fix/docs): {self.history.conventional_commits} ({self.history.conventional_ratio:.0%})",
            f"   Contributors: {self.history.pattern.unique_authors}",
            f"   Days Active: {self.history.pattern.date_range_days}",
            "",
            f"   Sample Commit Messages: {self._format_sample_messages()}",
            "",
            
            # ===== AREA 4: QUALITY SIGNALS =====
            "## 4. THE QUALITY SIGNALS (Code Hygiene & Professionalism)",
            "   Does this developer write maintainable, production-ready code?",
            "",
            f"   Quality Grade: {self.quality.quality_grade}",
            f"   Has Tests: {'✅ YES' if self.quality.has_tests else '❌ NO TESTS (major red flag)'} ({self.quality.test_file_count} test files)",
            f"   Has CI/CD: {'✅ YES (GitHub Actions, etc.)' if self.quality.has_ci_cd else '❌ No automation'}",
            f"   Has Linter: {'✅ Yes' if self.quality.has_linter_config else '❌ No ESLint/Pylint config'}",
            f"   Has Formatter: {'✅ Yes' if self.quality.has_formatter_config else '❌ No Prettier/Black config'}",
            f"   .gitignore Quality: {self.quality.gitignore_quality}",
            f"   Type Safety: {'✅ TypeScript/Type hints' if any('.ts' in f for f in self.structure.categories.code_files[:50]) else '⚠️ No type safety detected'}",
            "",
            
            # ===== AREA 5: REAL-WORLD VALUE =====
            "## 5. THE REAL-WORLD VALUE (Uniqueness & Completeness)",
            "   Is this a tutorial clone or something that solves a real problem?",
            "",
            f"   Tech Stack Detected: {', '.join(self.context.detected_stack) or 'Unknown'}",
            f"   Dependency Count: {self.context.dependency_count} packages {'(Minimal/learning project)' if self.context.dependency_count < 5 else '(Feature-rich project)' if self.context.dependency_count > 20 else ''}",
            f"   Has Lockfile: {'✅ Yes (reproducible builds)' if self.context.has_lockfile else '❌ No (unprofessional)'}",
            f"   Completeness Signals:",
            f"      - Has README: {'✅' if self.context.readme_length > 100 else '❌'}",
            f"      - Has Tests: {'✅' if self.quality.has_tests else '❌'}",
            f"      - Has CI/CD: {'✅' if self.quality.has_ci_cd else '❌'}",
            f"      - Has License: {'✅' if self.context.license_type else '❌'}",
            "",
            
            # ===== CRITICAL ISSUES SUMMARY =====
            "=" * 50,
            "## CRITICAL ISSUES (Red Flags a Recruiter Would Notice)",
            "=" * 50,
        ]
        
        # Collect all issues
        all_issues = (
            self.structure.issues + 
            self.context.issues + 
            self.quality.issues + 
            self.history.issues
        )
        
        if all_issues:
            for issue in all_issues:
                lines.append(f"   🚩 {issue}")
        else:
            lines.append("   ✅ No critical issues detected - this repo is recruiter-ready!")
        
        # ===== UNIVERSAL PARSER INSIGHTS =====
        if self.parsed_repo:
            lines.extend(self._format_parsed_repo_insights())
        
        return "\n".join(lines)
    
    def _format_parsed_repo_insights(self) -> List[str]:
        """Format insights from the Universal Parser."""
        if not self.parsed_repo:
            return []
        
        lines = [
            "",
            "=" * 50,
            "## DEEP ANALYSIS (Universal Parser Insights)",
            "=" * 50,
            "",
        ]
        
        # Tech Stack Summary
        if self.parsed_repo.tech_stack:
            lines.append(f"   🔧 Detected Tech Stack: {', '.join(sorted(self.parsed_repo.tech_stack))}")
        
        # Notebook Count (AI/ML indicator)
        if self.parsed_repo.notebook_count > 0:
            lines.append(f"   📓 Jupyter Notebooks: {self.parsed_repo.notebook_count} (AI/ML project detected)")
        
        # Infrastructure Summary
        if self.parsed_repo.infra_summary and "No infrastructure" not in self.parsed_repo.infra_summary:
            lines.append("")
            lines.append("   📦 Infrastructure Files Found:")
            for line in self.parsed_repo.infra_summary.split("\n"):
                if line.strip():
                    lines.append(f"      {line.strip()}")
        
        # Security Issues from DevOps files
        if self.parsed_repo.security_issues:
            lines.append("")
            lines.append("   🔒 Security Analysis:")
            for issue in self.parsed_repo.security_issues[:10]:  # Limit to 10
                lines.append(f"      {issue}")
        
        return lines
    
    def _format_sample_messages(self) -> str:
        """Helper to format sample commit messages without backslash in f-string"""
        messages = self.history.sample_messages[:5]
        quoted = [f'"{m}"' for m in messages]
        return ', '.join(quoted)


# ==========================================
# File Classification Constants
# ==========================================

CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb', 
    '.php', '.c', '.cpp', '.h', '.cs', '.swift', '.kt', '.scala', '.vue',
    '.svelte', '.dart', '.lua', '.r', '.m', '.mm'
}

ASSET_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp',
    '.mp4', '.webm', '.mov', '.mp3', '.wav', '.ogg', '.pdf', '.ttf',
    '.woff', '.woff2', '.eot'
}

CONFIG_EXTENSIONS = {
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.env', '.properties'
}

CONFIG_FILES = {
    'package.json', 'requirements.txt', 'pyproject.toml', 'setup.py',
    'Dockerfile', 'docker-compose.yml', 'Makefile', '.gitignore',
    '.eslintrc', '.eslintrc.js', '.eslintrc.json', '.prettierrc',
    'tsconfig.json', 'webpack.config.js', 'vite.config.js', 'babel.config.js',
    '.env.example', 'jest.config.js', 'pytest.ini', 'setup.cfg',
    'tox.ini', '.flake8', '.black.toml', 'mypy.ini'
}

DOC_EXTENSIONS = {'.md', '.rst', '.txt', '.adoc'}

TEST_PATTERNS = [
    r'test_.*\.py$', r'.*_test\.py$', r'.*\.test\.[jt]sx?$',
    r'.*\.spec\.[jt]sx?$', r'tests?/', r'__tests__/', r'spec/'
]

ENTRY_POINT_FILES = {
    'main.py', 'app.py', 'server.py', 'index.py', 'run.py', 'manage.py',
    'index.js', 'index.ts', 'app.js', 'app.ts', 'server.js', 'server.ts',
    'main.js', 'main.ts', 'index.jsx', 'index.tsx', 'App.jsx', 'App.tsx',
    'main.go', 'main.rs', 'Main.java', 'Application.java', 'index.html'
}

LAZY_COMMIT_PATTERNS = [
    r'^update[sd]?\s*$', r'^fix(ed)?\s*$', r'^change[sd]?\s*$',
    r'^wip\s*$', r'^work in progress\s*$', r'^test\s*$',
    r'^asdf+\s*$', r'^[\.]+$', r'^minor\s*(changes?)?\s*$',
    r'^edit\s*$', r'^modify\s*$', r'^stuff\s*$', r'^things\s*$',
    r'^temp\s*$', r'^tmp\s*$', r'^save\s*$', r'^commit\s*$',
    r'^initial commit\s*$', r'^first commit\s*$', r'^init\s*$',
    r'^[a-z]\s*$',  # Single letter commits
]

CONVENTIONAL_PREFIXES = [
    'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore',
    'ci', 'perf', 'build', 'revert'
]

IGNORED_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env',
    'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache',
    '.mypy_cache', '.tox', 'eggs', '*.egg-info', 'target', 'out',
    '.idea', '.vscode', '.vs'
}


# ==========================================
# Repo Investigator (Agent Orchestrator)
# ==========================================

class RepoInvestigator:
    """
    Orchestrates all 4 investigation agents to produce a comprehensive report.
    
    Usage:
        investigator = RepoInvestigator("owner", "repo")
        report = await investigator.investigate()
        llm_context = report.to_llm_context()
    """
    
    BASE_URL = "https://api.github.com"
    RAW_URL = "https://raw.githubusercontent.com"
    
    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitGrade/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        
        # Cache for API responses
        self._tree_cache: Optional[List[Dict]] = None
        self._readme_cache: Optional[str] = None
        self._commits_cache: Optional[List[Dict]] = None
        self._default_branch: str = "main"
    
    async def investigate(self) -> InvestigationReport:
        """Run all 4 agents and compile the investigation report."""
        # First, fetch the repo info to get default branch
        await self._fetch_repo_info()
        
        # Run all agents (they share cached data)
        structure = await self._structure_agent()
        context = await self._context_agent()
        quality = await self._quality_agent(structure)
        history = await self._history_agent()
        
        # Optional: Deep file parsing with UniversalParser
        parsed_repo = await self._deep_parse_files(structure)
        
        return InvestigationReport(
            structure=structure,
            context=context,
            quality=quality,
            history=history,
            parsed_repo=parsed_repo
        )
    
    async def _deep_parse_files(self, structure: StructureReport) -> Optional[ParsedRepo]:
        """
        Fetch and parse key files using the UniversalParser.
        
        This enables handling of:
        - Jupyter Notebooks (.ipynb) → Extracts only code cells
        - Dockerfiles → Security analysis
        - K8s manifests → Security checks
        - CI/CD workflows → Secret handling validation
        """
        try:
            tree = await self._fetch_tree()
            
            # Identify important files to parse (limit to avoid rate limiting)
            important_files = []
            for item in tree:
                path = item.get("path", "")
                item_type = item.get("type", "")
                
                if item_type != "blob":
                    continue
                
                # Skip ignored directories
                if any(ignored in path for ignored in IGNORED_DIRS):
                    continue
                
                # Priority files for deep parsing
                filename = os.path.basename(path)
                ext = os.path.splitext(filename)[1].lower()
                
                # Always parse: notebooks, dockerfiles, CI/CD, K8s
                if ext == ".ipynb":
                    important_files.append(path)
                elif filename in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]:
                    important_files.append(path)
                elif ".github/workflows" in path:
                    important_files.append(path)
                elif "k8s" in path.lower() or "kubernetes" in path.lower():
                    important_files.append(path)
                # Limit code files (sample for tech detection)
                elif ext in [".py", ".js", ".ts", ".java", ".go", ".rs"] and len(important_files) < 20:
                    important_files.append(path)
            
            # Limit total files to parse
            important_files = important_files[:30]
            
            if not important_files:
                return None
            
            # Fetch file contents in parallel (with rate limiting)
            files_content: Dict[str, str] = {}
            
            async def fetch_file(path: str) -> Tuple[str, Optional[str]]:
                content = await self._fetch_file_content(path)
                return path, content
            
            # Fetch in batches of 5 to avoid rate limiting
            for i in range(0, len(important_files), 5):
                batch = important_files[i:i+5]
                tasks = [fetch_file(path) for path in batch]
                results = await asyncio.gather(*tasks)
                for path, content in results:
                    if content:
                        files_content[path] = content
                
                # Small delay between batches
                if i + 5 < len(important_files):
                    await asyncio.sleep(0.1)
            
            # Parse with UniversalParser
            file_tree_list = [item.get("path", "") for item in tree if item.get("type") == "blob"]
            parser = UniversalParser()
            parsed_repo = parser.parse_repo(files_content, file_tree_list)
            
            return parsed_repo
            
        except Exception as e:
            # Don't fail the whole investigation if parsing fails
            print(f"Warning: Deep file parsing failed: {e}")
            return None
    
    async def _fetch_repo_info(self):
        """Fetch basic repo info including default branch."""
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                self._default_branch = data.get("default_branch", "main")
    
    async def _fetch_tree(self) -> List[Dict]:
        """Fetch the full file tree (cached)."""
        if self._tree_cache is not None:
            return self._tree_cache
        
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/git/trees/{self._default_branch}?recursive=1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                self._tree_cache = data.get("tree", [])
            else:
                self._tree_cache = []
        
        return self._tree_cache or []
    
    async def _fetch_file_content(self, path: str) -> Optional[str]:
        """Fetch raw content of a file."""
        url = f"{self.RAW_URL}/{self.owner}/{self.repo}/{self._default_branch}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            if response.status_code == 200:
                return response.text
        return None
    
    async def _fetch_commits(self, limit: int = 30) -> List[Dict]:
        """Fetch recent commits (cached)."""
        if self._commits_cache is not None:
            return self._commits_cache
        
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/commits"
        params = {"per_page": limit}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            if response.status_code == 200:
                self._commits_cache = response.json()
            else:
                self._commits_cache = []
        
        return self._commits_cache or []
    
    # ==========================================
    # Agent 1: Structure Agent (The Architect)
    # ==========================================
    
    async def _structure_agent(self) -> StructureReport:
        """
        Analyzes the project structure and organization.
        - Maps file tree
        - Identifies entry points
        - Categorizes files
        - Detects structural issues
        """
        tree = await self._fetch_tree()
        issues = []
        
        # Filter and categorize files
        categories = FileCategory()
        entry_points = []
        root_files = []
        max_depth = 0
        total_folders = 0
        
        for item in tree:
            path = item.get("path", "")
            item_type = item.get("type", "")
            
            # Skip ignored directories
            if any(ignored in path for ignored in IGNORED_DIRS):
                continue
            
            # Calculate depth
            depth = path.count("/")
            max_depth = max(max_depth, depth)
            
            if item_type == "tree":  # folder
                total_folders += 1
                continue
            
            if item_type != "blob":  # file
                continue
            
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1].lower()
            
            # Check for entry points
            if filename in ENTRY_POINT_FILES:
                entry_points.append(path)
            
            # Track root clutter
            if "/" not in path:
                root_files.append(filename)
            
            # Categorize by type
            if any(re.search(pattern, path, re.I) for pattern in TEST_PATTERNS):
                categories.test_files.append(path)
            elif ext in CODE_EXTENSIONS:
                categories.code_files.append(path)
            elif ext in ASSET_EXTENSIONS:
                categories.asset_files.append(path)
            elif ext in CONFIG_EXTENSIONS or filename in CONFIG_FILES:
                categories.config_files.append(path)
            elif ext in DOC_EXTENSIONS:
                categories.doc_files.append(path)
        
        # Calculate totals
        total_files = (
            len(categories.code_files) + 
            len(categories.asset_files) + 
            len(categories.config_files) +
            len(categories.doc_files) +
            len(categories.test_files)
        )
        
        root_clutter = len(root_files)
        
        # Determine structure grade
        if root_clutter > 15 or total_folders < 2:
            structure_grade = "Messy"
            issues.append("Too many files in root directory - use folders to organize")
        elif root_clutter > 8:
            structure_grade = "Moderate"
            issues.append("Consider organizing some root files into folders")
        else:
            structure_grade = "Clean"
        
        if not entry_points:
            issues.append("No clear entry point file found (main.py, index.js, etc.)")
        
        if total_folders == 0 and total_files > 5:
            issues.append("Flat structure with no folders - add organization")
        
        # Build tree string
        tree_str = self._build_tree_string(tree)
        
        return StructureReport(
            file_tree=tree_str,
            total_files=total_files,
            total_folders=total_folders,
            entry_points=entry_points[:5],  # Top 5
            categories=categories,
            root_clutter=root_clutter,
            max_depth=max_depth,
            structure_grade=structure_grade,
            issues=issues
        )
    
    def _build_tree_string(self, tree: List[Dict], max_items: int = 100) -> str:
        """Build a human-readable tree string."""
        lines = []
        count = 0
        
        for item in sorted(tree, key=lambda x: x.get("path", "")):
            if count >= max_items:
                lines.append(f"... and {len(tree) - count} more files")
                break
            
            path = item.get("path", "")
            item_type = item.get("type", "")
            
            # Skip ignored
            if any(ignored in path for ignored in IGNORED_DIRS):
                continue
            
            depth = path.count("/")
            indent = "  " * depth
            name = os.path.basename(path)
            
            if item_type == "tree":
                lines.append(f"{indent}📁 {name}/")
            else:
                lines.append(f"{indent}📄 {name}")
            
            count += 1
        
        return "\n".join(lines) if lines else "[Empty repository]"
    
    # ==========================================
    # Agent 2: Context Agent (The Librarian)
    # ==========================================
    
    async def _context_agent(self) -> ContextReport:
        """
        Extracts project context and technology stack.
        - Reads and analyzes README
        - Parses dependency files
        - Detects tech stack
        """
        issues = []
        
        # Fetch README
        readme_content = await self._fetch_readme()
        readme_exists = readme_content is not None and len(readme_content) > 10
        readme_length = len(readme_content) if readme_content else 0
        
        # Analyze README quality
        if not readme_exists:
            readme_quality = "Missing"
            issues.append("CRITICAL: No README.md found - every project needs documentation")
        elif readme_length < 100:
            readme_quality = "Sparse"
            issues.append("README is too short - add project description, setup instructions")
        elif readme_length < 500:
            readme_quality = "Good"
        else:
            readme_quality = "Excellent"
        
        # Check for structured README (has headers)
        readme_has_sections = bool(
            readme_content and 
            (re.search(r'^#+\s+', readme_content, re.M) or 
             re.search(r'^[A-Z][^:]+:', readme_content, re.M))
        )
        
        if readme_exists and not readme_has_sections:
            issues.append("README lacks structure - add sections like Installation, Usage, etc.")
        
        # Parse dependencies
        detected_stack, dependency_count = await self._parse_dependencies()
        
        if not detected_stack:
            issues.append("Could not detect technology stack - add package.json or requirements.txt")
        
        # Check for lockfile
        tree = await self._fetch_tree()
        tree_paths = {item.get("path", "") for item in tree}
        
        lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
                     "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum"]
        has_lockfile = any(lf in tree_paths for lf in lockfiles)
        
        if not has_lockfile and dependency_count > 0:
            issues.append("No lockfile found - commit your lockfile for reproducible builds")
        
        # Check for license
        license_type = None
        license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        for lf in license_files:
            if lf in tree_paths:
                license_content = await self._fetch_file_content(lf)
                if license_content:
                    license_type = self._detect_license(license_content)
                break
        
        if not license_type:
            issues.append("No LICENSE file found - add one to clarify usage rights")
        
        return ContextReport(
            readme_exists=readme_exists,
            readme_length=readme_length,
            readme_quality=readme_quality,
            readme_has_sections=readme_has_sections,
            detected_stack=detected_stack,
            dependency_count=dependency_count,
            has_lockfile=has_lockfile,
            license_type=license_type,
            issues=issues
        )
    
    async def _fetch_readme(self) -> Optional[str]:
        """Fetch README content."""
        readme_names = ["README.md", "readme.md", "README", "README.rst", "README.txt"]
        for name in readme_names:
            content = await self._fetch_file_content(name)
            if content:
                return content[:5000]  # Limit size
        return None
    
    async def _parse_dependencies(self) -> Tuple[List[str], int]:
        """Parse dependency files and extract tech stack."""
        stack = []
        total_deps = 0
        
        # Try package.json (JavaScript/TypeScript)
        pkg_json = await self._fetch_file_content("package.json")
        if pkg_json:
            try:
                import json
                data = json.loads(pkg_json)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                total_deps = len(deps)
                
                # Detect major frameworks
                framework_map = {
                    "react": "React", "next": "Next.js", "vue": "Vue.js",
                    "angular": "Angular", "svelte": "Svelte", "express": "Express",
                    "fastify": "Fastify", "nestjs": "NestJS", "tailwindcss": "Tailwind CSS",
                    "typescript": "TypeScript", "jest": "Jest", "mocha": "Mocha",
                    "prisma": "Prisma", "mongoose": "MongoDB", "sequelize": "Sequelize"
                }
                
                for dep in deps:
                    dep_lower = dep.lower().replace("@", "").replace("/", "")
                    for key, name in framework_map.items():
                        if key in dep_lower and name not in stack:
                            stack.append(name)
                
                if not stack:
                    stack.append("JavaScript")
                    
            except Exception:
                pass
        
        # Try requirements.txt (Python)
        requirements = await self._fetch_file_content("requirements.txt")
        if requirements:
            lines = [l.strip() for l in requirements.split("\n") if l.strip() and not l.startswith("#")]
            total_deps = max(total_deps, len(lines))
            
            framework_map = {
                "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
                "pytest": "Pytest", "numpy": "NumPy", "pandas": "Pandas",
                "tensorflow": "TensorFlow", "pytorch": "PyTorch", "sqlalchemy": "SQLAlchemy",
                "celery": "Celery", "redis": "Redis", "requests": "Requests"
            }
            
            for line in lines:
                pkg = re.split(r'[>=<\[\]]', line)[0].lower()
                for key, name in framework_map.items():
                    if key in pkg and name not in stack:
                        stack.append(name)
            
            if "Python" not in stack:
                stack.insert(0, "Python")
        
        # Try pyproject.toml
        pyproject = await self._fetch_file_content("pyproject.toml")
        if pyproject and "Python" not in stack:
            stack.insert(0, "Python")
        
        return stack[:10], total_deps  # Limit to top 10
    
    def _detect_license(self, content: str) -> Optional[str]:
        """Detect license type from content."""
        content_lower = content.lower()
        if "mit license" in content_lower or "permission is hereby granted, free of charge" in content_lower:
            return "MIT"
        elif "apache license" in content_lower:
            return "Apache 2.0"
        elif "gnu general public license" in content_lower:
            return "GPL"
        elif "bsd" in content_lower:
            return "BSD"
        elif "unlicense" in content_lower:
            return "Unlicense"
        return "Unknown"
    
    # ==========================================
    # Agent 3: Quality Agent (The Inspector)
    # ==========================================
    
    async def _quality_agent(self, structure: StructureReport) -> QualityReport:
        """
        Analyzes code quality indicators.
        - Test detection
        - CI/CD configuration
        - Linter/formatter setup
        - Security checks
        """
        issues = []
        tree = await self._fetch_tree()
        tree_paths = {item.get("path", "").lower() for item in tree}
        
        # Test detection
        has_tests = len(structure.categories.test_files) > 0
        test_file_count = len(structure.categories.test_files)
        
        if not has_tests:
            issues.append("CRITICAL: No tests found - add unit tests for reliability")
        elif test_file_count < 3:
            issues.append("Very few test files - aim for better test coverage")
        
        # CI/CD detection
        ci_paths = [
            ".github/workflows", "github/workflows", ".gitlab-ci.yml",
            "azure-pipelines.yml", ".circleci", "Jenkinsfile", ".travis.yml"
        ]
        has_ci_cd = any(
            any(ci.lower() in path for path in tree_paths) 
            for ci in ci_paths
        )
        
        if not has_ci_cd:
            issues.append("No CI/CD configuration found - add GitHub Actions for automated testing")
        
        # Linter config
        linter_files = [
            ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
            ".pylintrc", "pylint.rc", ".flake8", "mypy.ini", ".rubocop.yml",
            "tslint.json"
        ]
        has_linter_config = any(lf.lower() in tree_paths for lf in linter_files)
        
        # Formatter config
        formatter_files = [
            ".prettierrc", ".prettierrc.js", ".prettierrc.json",
            "pyproject.toml", ".black.toml", ".editorconfig", ".clang-format"
        ]
        has_formatter_config = any(ff.lower() in tree_paths for ff in formatter_files)
        
        if not has_linter_config and not has_formatter_config:
            issues.append("No linter or formatter config - add ESLint/Prettier or Pylint/Black")
        
        # Gitignore check
        gitignore_content = await self._fetch_file_content(".gitignore")
        if not gitignore_content:
            has_gitignore = False
            gitignore_quality = "Missing"
            issues.append("No .gitignore file - add one to exclude build artifacts")
        else:
            has_gitignore = True
            lines = [l for l in gitignore_content.split("\n") if l.strip() and not l.startswith("#")]
            if len(lines) < 5:
                gitignore_quality = "Basic"
            else:
                gitignore_quality = "Good"
        
        # Security warnings
        security_warnings = []
        sensitive_files = [".env", "secrets.json", "credentials.json", "config/secrets.yml", "id_rsa"]
        for sf in sensitive_files:
            if sf.lower() in tree_paths:
                security_warnings.append(f"SECURITY: {sf} should not be committed")
                issues.append(f"SECURITY: Found {sf} in repository - remove sensitive files")
        
        # Complexity warnings (heuristic based on file count)
        complexity_warnings = []
        large_code_files = len([f for f in structure.categories.code_files])
        if large_code_files > 50:
            complexity_warnings.append("Large codebase - ensure good documentation")
        
        # Calculate quality grade
        score = 0
        if has_tests:
            score += 3
        if test_file_count >= 3:
            score += 1
        if has_ci_cd:
            score += 2
        if has_linter_config:
            score += 1
        if has_formatter_config:
            score += 1
        if gitignore_quality == "Good":
            score += 1
        if not security_warnings:
            score += 1
        
        if score >= 8:
            quality_grade = "Excellent"
        elif score >= 5:
            quality_grade = "Good"
        elif score >= 3:
            quality_grade = "Fair"
        else:
            quality_grade = "Poor"
        
        return QualityReport(
            has_tests=has_tests,
            test_file_count=test_file_count,
            has_ci_cd=has_ci_cd,
            has_linter_config=has_linter_config,
            has_formatter_config=has_formatter_config,
            has_gitignore=has_gitignore,
            gitignore_quality=gitignore_quality,
            complexity_warnings=complexity_warnings,
            security_warnings=security_warnings,
            quality_grade=quality_grade,
            issues=issues
        )
    
    # ==========================================
    # Agent 4: History Agent (The Historian)
    # ==========================================
    
    async def _history_agent(self) -> HistoryReport:
        """
        Analyzes commit history and contribution patterns.
        - Detects lazy commit messages
        - Checks for conventional commits
        - Identifies cramming vs consistent work
        """
        issues = []
        commits = await self._fetch_commits(30)
        
        if not commits:
            return HistoryReport(
                commit_count=0,
                pattern=CommitPattern(0, 0, 0, 0.0, False, False),
                lazy_commits=0,
                lazy_commit_ratio=0.0,
                conventional_commits=0,
                conventional_ratio=0.0,
                sample_messages=[],
                commit_quality="Unknown",
                issues=["Could not fetch commit history"]
            )
        
        commit_count = len(commits)
        messages = []
        authors = set()
        dates = []
        
        lazy_count = 0
        conventional_count = 0
        
        for commit in commits:
            # Extract message
            message = commit.get("commit", {}).get("message", "").split("\n")[0].strip()
            messages.append(message)
            
            # Extract author
            author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
            authors.add(author)
            
            # Extract date
            date_str = commit.get("commit", {}).get("author", {}).get("date", "")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    dates.append(dt)
                except Exception:
                    pass
            
            # Check for lazy commits
            msg_lower = message.lower()
            if any(re.match(pattern, msg_lower) for pattern in LAZY_COMMIT_PATTERNS):
                lazy_count += 1
            
            # Check for conventional commits
            if any(msg_lower.startswith(f"{prefix}:") or msg_lower.startswith(f"{prefix}(") 
                   for prefix in CONVENTIONAL_PREFIXES):
                conventional_count += 1
        
        # Calculate ratios
        lazy_ratio = lazy_count / commit_count if commit_count > 0 else 0
        conventional_ratio = conventional_count / commit_count if commit_count > 0 else 0
        
        # Analyze work pattern
        if len(dates) >= 2:
            dates.sort()
            date_range = (dates[-1] - dates[0]).days
            commits_per_day = commit_count / max(date_range, 1)
            
            # Cramming: more than 10 commits per day average, or all in 1-2 days
            is_cramming = date_range <= 2 and commit_count > 5
            is_consistent = date_range >= 7 and commits_per_day <= 5
        else:
            date_range = 0
            commits_per_day = float(commit_count)
            is_cramming = commit_count > 5
            is_consistent = False
        
        pattern = CommitPattern(
            total_commits=commit_count,
            unique_authors=len(authors),
            date_range_days=date_range,
            commits_per_day=commits_per_day,
            is_cramming=is_cramming,
            is_consistent=is_consistent
        )
        
        # Determine commit quality
        if lazy_ratio > 0.5:
            commit_quality = "Amateur"
            issues.append("Over 50% lazy commit messages like 'update', 'fix' - write descriptive commits")
        elif lazy_ratio > 0.3:
            commit_quality = "Developing"
            issues.append("Many lazy commits - try Conventional Commits format (feat:, fix:, docs:)")
        elif conventional_ratio > 0.5:
            commit_quality = "Professional"
        else:
            commit_quality = "Developing"
        
        if is_cramming:
            issues.append("CRAMMING DETECTED: All commits in short period - work consistently over time")
        
        if commit_count < 5:
            issues.append("Very few commits - break work into smaller, atomic commits")
        
        return HistoryReport(
            commit_count=commit_count,
            pattern=pattern,
            lazy_commits=lazy_count,
            lazy_commit_ratio=lazy_ratio,
            conventional_commits=conventional_count,
            conventional_ratio=conventional_ratio,
            sample_messages=messages[:5],
            commit_quality=commit_quality,
            issues=issues
        )


# ==========================================
# Convenience Function
# ==========================================

async def investigate_repository(owner: str, repo: str) -> InvestigationReport:
    """
    Convenience function to investigate a repository.
    
    Usage:
        report = await investigate_repository("facebook", "react")
        print(report.to_llm_context())
    """
    investigator = RepoInvestigator(owner, repo)
    return await investigator.investigate()
