"""
Universal Parser - The Polyglot File Handler

Handles ANY tech stack by intelligently parsing:
- AI/ML: Jupyter Notebooks (.ipynb) → Extract only code cells
- DevOps: Docker, K8s, CI/CD → Security-focused analysis
- Java/C++: Deep folder structures → Flattened tree view
- Web: Standard code files → Truncated for token efficiency
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


# ==========================================
# Tech Stack Detection Patterns
# ==========================================

TECH_STACK_PATTERNS = {
    # Languages
    "Python": [".py"],
    "JavaScript": [".js", ".mjs", ".cjs"],
    "TypeScript": [".ts", ".tsx"],
    "Java": [".java"],
    "C/C++": [".c", ".cpp", ".cc", ".h", ".hpp"],
    "Go": [".go"],
    "Rust": [".rs"],
    "Ruby": [".rb"],
    "PHP": [".php"],
    "C#": [".cs"],
    "Swift": [".swift"],
    "Kotlin": [".kt", ".kts"],
    
    # Frameworks (detected from file content)
    "React": ["react", "jsx", "tsx", "next"],
    "Vue": [".vue", "vue"],
    "Angular": ["angular.json", "@angular"],
    "Django": ["django", "wsgi.py", "asgi.py"],
    "Flask": ["flask", "from flask"],
    "FastAPI": ["fastapi", "from fastapi"],
    "Spring Boot": ["spring", "@SpringBootApplication"],
    "Express": ["express", "app.listen"],
    "NestJS": ["@nestjs", "nest-cli.json"],
    
    # AI/ML/DL
    "PyTorch": ["torch", "pytorch"],
    "TensorFlow": ["tensorflow", "tf."],
    "Keras": ["keras"],
    "Scikit-learn": ["sklearn", "scikit-learn"],
    "Hugging Face": ["transformers", "huggingface"],
    "LangChain": ["langchain"],
    "OpenAI": ["openai"],
    "Jupyter": [".ipynb"],
    
    # DevOps/Infrastructure
    "Docker": ["Dockerfile", "docker-compose"],
    "Kubernetes": ["k8s", "kubernetes", "kubectl", ".yaml"],
    "CI/CD": [".github/workflows", ".gitlab-ci", "jenkins", ".circleci"],
    "Terraform": [".tf", "terraform"],
    "Ansible": ["ansible", "playbook"],
    
    # Databases
    "PostgreSQL": ["psycopg2", "pg_", "postgres"],
    "MongoDB": ["mongodb", "mongoose", "pymongo"],
    "Redis": ["redis", "ioredis"],
    "SQLite": ["sqlite", ".db"],
    "MySQL": ["mysql", "mysqlclient"],
    
    # Cloud
    "AWS": ["boto3", "aws-sdk", "s3", "lambda"],
    "Azure": ["azure", "@azure"],
    "GCP": ["google-cloud", "gcloud"],
}

# Files to skip (auto-generated, binary, etc.)
SKIP_PATTERNS = [
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.pyc",
    "*.pyo",
    "__pycache__/*",
    "node_modules/*",
    ".git/*",
    "dist/*",
    "build/*",
    "*.whl",
    "*.egg-info/*",
]

# Infrastructure files that need security analysis
INFRA_FILES = {
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
    ".dockerignore": "docker",
    "Makefile": "build",
    "Jenkinsfile": "ci",
    "azure-pipelines.yml": "ci",
    ".travis.yml": "ci",
    ".circleci/config.yml": "ci",
}


@dataclass
class ParsedFile:
    """Result of parsing a file"""
    path: str
    content: str
    file_type: str  # "code", "notebook", "config", "infra", "docs", "skipped"
    tech_hints: List[str] = field(default_factory=list)
    security_notes: List[str] = field(default_factory=list)
    original_size: int = 0
    truncated: bool = False


@dataclass  
class ParsedRepo:
    """Complete parsed repository"""
    files: Dict[str, ParsedFile]
    tech_stack: Set[str]
    file_tree: str  # Flattened/simplified tree
    infra_summary: str
    notebook_count: int = 0
    security_issues: List[str] = field(default_factory=list)


class UniversalParser:
    """
    The Polyglot Parser - Handles ANY file type intelligently.
    
    Features:
    1. Notebook Cleaner: Extracts code from .ipynb JSON blobs
    2. Config Detector: Identifies and flags infra files for security review
    3. Tree Flattener: Collapses empty Java/C++ folder hierarchies
    4. Smart Truncation: Keeps files under token limits
    """
    
    MAX_CODE_SIZE = 5000      # Max chars for code files
    MAX_CONFIG_SIZE = 3000    # Max chars for config files
    MAX_NOTEBOOK_SIZE = 8000  # Max chars for notebook code extraction
    
    def __init__(self):
        self.tech_stack: Set[str] = set()
        self.security_issues: List[str] = []
    
    def parse_file(self, path: str, content: str) -> ParsedFile:
        """
        Intelligently parse a single file based on its type.
        """
        original_size = len(content)
        extension = self._get_extension(path)
        filename = path.split("/")[-1]
        
        # Check if should skip
        if self._should_skip(path):
            return ParsedFile(
                path=path,
                content="[SKIPPED: Auto-generated/binary file]",
                file_type="skipped",
                original_size=original_size
            )
        
        # 1. AI/ML: Jupyter Notebooks
        if extension == "ipynb":
            return self._parse_notebook(path, content, original_size)
        
        # 2. DevOps: Infrastructure files
        if self._is_infra_file(path, filename):
            return self._parse_infra(path, content, original_size)
        
        # 3. CI/CD Workflows
        if ".github/workflows" in path or ".gitlab-ci" in path:
            return self._parse_ci_cd(path, content, original_size)
        
        # 4. Kubernetes manifests
        if self._is_k8s_file(path, content):
            return self._parse_k8s(path, content, original_size)
        
        # 5. Config files (JSON, YAML, TOML)
        if extension in ["json", "yaml", "yml", "toml", "ini", "cfg"]:
            return self._parse_config(path, content, original_size)
        
        # 6. Documentation
        if extension in ["md", "rst", "txt"] or filename in ["README", "CHANGELOG", "LICENSE"]:
            return self._parse_docs(path, content, original_size)
        
        # 7. Standard code files
        if extension in ["py", "js", "ts", "tsx", "jsx", "java", "go", "rs", 
                         "rb", "php", "c", "cpp", "cc", "h", "hpp", "cs", 
                         "swift", "kt", "scala", "vue", "svelte"]:
            return self._parse_code(path, content, original_size)
        
        # Default: Treat as generic text
        return self._parse_generic(path, content, original_size)
    
    def parse_repo(self, files: Dict[str, str], file_tree: List[str]) -> ParsedRepo:
        """
        Parse an entire repository, detecting tech stack and organizing files.
        """
        parsed_files = {}
        notebook_count = 0
        
        for path, content in files.items():
            parsed = self.parse_file(path, content)
            parsed_files[path] = parsed
            
            # Collect tech hints
            for hint in parsed.tech_hints:
                self.tech_stack.add(hint)
            
            # Collect security issues
            self.security_issues.extend(parsed.security_notes)
            
            if parsed.file_type == "notebook":
                notebook_count += 1
        
        # Detect tech stack from content patterns
        self._detect_tech_stack_from_content(files)
        
        # Generate flattened tree
        flattened_tree = self._flatten_tree(file_tree)
        
        # Generate infra summary
        infra_summary = self._generate_infra_summary(parsed_files)
        
        return ParsedRepo(
            files=parsed_files,
            tech_stack=self.tech_stack,
            file_tree=flattened_tree,
            infra_summary=infra_summary,
            notebook_count=notebook_count,
            security_issues=self.security_issues
        )
    
    # ==========================================
    # File Type Parsers
    # ==========================================
    
    def _parse_notebook(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Extract ONLY code cells from Jupyter Notebook JSON.
        Removes metadata, outputs, and cell IDs that waste tokens.
        """
        try:
            notebook = json.loads(content)
            code_cells = []
            markdown_summary = []
            
            for i, cell in enumerate(notebook.get("cells", []), 1):
                cell_type = cell.get("cell_type", "")
                source = "".join(cell.get("source", []))
                
                if cell_type == "code":
                    # Skip empty cells
                    if source.strip():
                        # Remove excessive comments but keep docstrings
                        cleaned = self._clean_notebook_code(source)
                        code_cells.append(f"# === Cell {i} ===\n{cleaned}")
                        
                elif cell_type == "markdown" and len(markdown_summary) < 3:
                    # Keep first few markdown cells as context
                    first_line = source.split("\n")[0][:100]
                    if first_line.strip():
                        markdown_summary.append(first_line)
            
            # Build output
            output_parts = []
            if markdown_summary:
                output_parts.append("# Notebook Overview:\n# " + "\n# ".join(markdown_summary))
            
            output_parts.extend(code_cells)
            extracted = "\n\n".join(output_parts)
            
            # Truncate if too long
            truncated = len(extracted) > self.MAX_NOTEBOOK_SIZE
            if truncated:
                extracted = extracted[:self.MAX_NOTEBOOK_SIZE] + "\n# ... [TRUNCATED]"
            
            # Detect ML frameworks
            tech_hints = []
            if "torch" in content.lower():
                tech_hints.append("PyTorch")
            if "tensorflow" in content.lower() or "tf." in content:
                tech_hints.append("TensorFlow")
            if "sklearn" in content.lower():
                tech_hints.append("Scikit-learn")
            if "pandas" in content.lower():
                tech_hints.append("Pandas")
            if "matplotlib" in content.lower() or "plt." in content:
                tech_hints.append("Matplotlib")
            
            tech_hints.append("Jupyter")
            
            return ParsedFile(
                path=path,
                content=extracted,
                file_type="notebook",
                tech_hints=tech_hints,
                original_size=original_size,
                truncated=truncated
            )
            
        except json.JSONDecodeError:
            return ParsedFile(
                path=path,
                content="[ERROR: Invalid Jupyter Notebook JSON]",
                file_type="notebook",
                tech_hints=["Jupyter"],
                original_size=original_size
            )
    
    def _parse_infra(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse infrastructure files with security analysis.
        """
        security_notes = []
        filename = path.split("/")[-1]
        
        # Dockerfile security checks
        if "Dockerfile" in path or filename == "Dockerfile":
            security_notes.extend(self._check_dockerfile_security(content))
            tech_hints = ["Docker"]
        
        # docker-compose checks
        elif "docker-compose" in filename:
            security_notes.extend(self._check_compose_security(content))
            tech_hints = ["Docker", "Docker Compose"]
        
        else:
            tech_hints = ["Infrastructure"]
        
        truncated = len(content) > self.MAX_CONFIG_SIZE
        clean_content = content[:self.MAX_CONFIG_SIZE]
        if truncated:
            clean_content += "\n# ... [TRUNCATED]"
        
        return ParsedFile(
            path=path,
            content=clean_content,
            file_type="infra",
            tech_hints=tech_hints,
            security_notes=security_notes,
            original_size=original_size,
            truncated=truncated
        )
    
    def _parse_ci_cd(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse CI/CD workflow files.
        """
        security_notes = []
        
        # Check for hardcoded secrets
        if re.search(r'(password|secret|api_key|token)\s*[:=]\s*["\'][^"\']+["\']', content, re.I):
            security_notes.append(f"⚠️ Possible hardcoded secret in {path}")
        
        # Check for proper secret usage
        if "${{ secrets." in content:
            security_notes.append(f"✅ Uses GitHub secrets properly in {path}")
        
        tech_hints = ["CI/CD", "GitHub Actions" if ".github" in path else "GitLab CI"]
        
        return ParsedFile(
            path=path,
            content=content[:self.MAX_CONFIG_SIZE],
            file_type="infra",
            tech_hints=tech_hints,
            security_notes=security_notes,
            original_size=original_size,
            truncated=len(content) > self.MAX_CONFIG_SIZE
        )
    
    def _parse_k8s(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse Kubernetes manifests with security checks.
        """
        security_notes = []
        
        # Check for privileged containers
        if "privileged: true" in content:
            security_notes.append(f"🚨 CRITICAL: Privileged container in {path}")
        
        # Check for running as root
        if "runAsRoot: true" in content or ("runAsUser" not in content and "securityContext" in content):
            security_notes.append(f"⚠️ May be running as root in {path}")
        
        # Check for resource limits
        if "limits:" not in content and ("kind: Deployment" in content or "kind: Pod" in content):
            security_notes.append(f"⚠️ No resource limits defined in {path}")
        
        # Check for latest tag
        if ":latest" in content:
            security_notes.append(f"⚠️ Using :latest tag (unpinned version) in {path}")
        
        tech_hints = ["Kubernetes"]
        
        return ParsedFile(
            path=path,
            content=content[:self.MAX_CONFIG_SIZE],
            file_type="infra",
            tech_hints=tech_hints,
            security_notes=security_notes,
            original_size=original_size,
            truncated=len(content) > self.MAX_CONFIG_SIZE
        )
    
    def _parse_config(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse configuration files.
        """
        tech_hints = []
        filename = path.split("/")[-1]
        
        # Detect specific configs
        if filename == "package.json":
            tech_hints.extend(self._detect_npm_stack(content))
        elif filename in ["requirements.txt", "pyproject.toml", "setup.py"]:
            tech_hints.extend(self._detect_python_stack(content))
        elif filename == "Cargo.toml":
            tech_hints.append("Rust")
        elif filename == "go.mod":
            tech_hints.append("Go")
        elif filename == "pom.xml" or filename == "build.gradle":
            tech_hints.append("Java")
        
        return ParsedFile(
            path=path,
            content=content[:self.MAX_CONFIG_SIZE],
            file_type="config",
            tech_hints=tech_hints,
            original_size=original_size,
            truncated=len(content) > self.MAX_CONFIG_SIZE
        )
    
    def _parse_docs(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse documentation files.
        """
        # Keep more of docs since they're important for grading
        max_size = 4000
        truncated = len(content) > max_size
        
        return ParsedFile(
            path=path,
            content=content[:max_size] + ("\n... [TRUNCATED]" if truncated else ""),
            file_type="docs",
            original_size=original_size,
            truncated=truncated
        )
    
    def _parse_code(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse standard code files.
        """
        tech_hints = []
        extension = self._get_extension(path)
        
        # Basic language detection
        lang_map = {
            "py": "Python", "js": "JavaScript", "ts": "TypeScript",
            "tsx": "TypeScript", "jsx": "React", "java": "Java",
            "go": "Go", "rs": "Rust", "rb": "Ruby", "php": "PHP",
            "c": "C", "cpp": "C++", "h": "C/C++", "cs": "C#",
            "swift": "Swift", "kt": "Kotlin", "vue": "Vue", "svelte": "Svelte"
        }
        if extension in lang_map:
            tech_hints.append(lang_map[extension])
        
        truncated = len(content) > self.MAX_CODE_SIZE
        clean_content = content[:self.MAX_CODE_SIZE]
        if truncated:
            clean_content += "\n# ... [TRUNCATED]"
        
        return ParsedFile(
            path=path,
            content=clean_content,
            file_type="code",
            tech_hints=tech_hints,
            original_size=original_size,
            truncated=truncated
        )
    
    def _parse_generic(self, path: str, content: str, original_size: int) -> ParsedFile:
        """
        Parse unknown file types conservatively.
        """
        return ParsedFile(
            path=path,
            content=content[:1000],
            file_type="unknown",
            original_size=original_size,
            truncated=len(content) > 1000
        )
    
    # ==========================================
    # Security Checkers
    # ==========================================
    
    def _check_dockerfile_security(self, content: str) -> List[str]:
        """
        Check Dockerfile for security issues.
        """
        issues = []
        
        # Running as root
        if "USER root" in content or ("USER" not in content and "FROM" in content):
            issues.append("🚨 Dockerfile: Running as root (add USER directive)")
        
        # Using latest tag
        if re.search(r'FROM\s+\w+:latest', content):
            issues.append("⚠️ Dockerfile: Using :latest tag (pin to specific version)")
        
        # Hardcoded secrets
        if re.search(r'(PASSWORD|SECRET|API_KEY|TOKEN)\s*=', content, re.I):
            issues.append("🚨 Dockerfile: Possible hardcoded secret (use build args or secrets)")
        
        # No .dockerignore check (can't verify from content alone)
        
        # Good practices
        if "HEALTHCHECK" in content:
            issues.append("✅ Dockerfile: Has HEALTHCHECK")
        
        if "COPY --chown" in content or "RUN chown" in content:
            issues.append("✅ Dockerfile: Sets proper file ownership")
        
        return issues
    
    def _check_compose_security(self, content: str) -> List[str]:
        """
        Check docker-compose for security issues.
        """
        issues = []
        
        if "privileged: true" in content:
            issues.append("🚨 docker-compose: Privileged container detected")
        
        if "network_mode: host" in content:
            issues.append("⚠️ docker-compose: Using host network mode")
        
        if re.search(r'ports:\s*\n\s*-\s*"?0\.0\.0\.0:', content):
            issues.append("⚠️ docker-compose: Binding to 0.0.0.0 (consider localhost)")
        
        return issues
    
    # ==========================================
    # Tech Stack Detection
    # ==========================================
    
    def _detect_npm_stack(self, content: str) -> List[str]:
        """
        Detect tech stack from package.json.
        """
        hints = ["Node.js"]
        content_lower = content.lower()
        
        if '"react"' in content_lower:
            hints.append("React")
        if '"next"' in content_lower:
            hints.append("Next.js")
        if '"vue"' in content_lower:
            hints.append("Vue")
        if '"angular"' in content_lower:
            hints.append("Angular")
        if '"express"' in content_lower:
            hints.append("Express")
        if '"typescript"' in content_lower:
            hints.append("TypeScript")
        if '"jest"' in content_lower or '"mocha"' in content_lower:
            hints.append("Testing")
        if '"eslint"' in content_lower:
            hints.append("ESLint")
        if '"prettier"' in content_lower:
            hints.append("Prettier")
        
        return hints
    
    def _detect_python_stack(self, content: str) -> List[str]:
        """
        Detect tech stack from Python dependency files.
        """
        hints = ["Python"]
        content_lower = content.lower()
        
        if "django" in content_lower:
            hints.append("Django")
        if "flask" in content_lower:
            hints.append("Flask")
        if "fastapi" in content_lower:
            hints.append("FastAPI")
        if "torch" in content_lower or "pytorch" in content_lower:
            hints.append("PyTorch")
        if "tensorflow" in content_lower:
            hints.append("TensorFlow")
        if "pandas" in content_lower:
            hints.append("Pandas")
        if "numpy" in content_lower:
            hints.append("NumPy")
        if "pytest" in content_lower:
            hints.append("Testing")
        if "black" in content_lower or "ruff" in content_lower:
            hints.append("Code Formatter")
        
        return hints
    
    def _detect_tech_stack_from_content(self, files: Dict[str, str]):
        """
        Scan all file contents for tech stack patterns.
        """
        all_content = " ".join(files.values()).lower()
        
        for tech, patterns in TECH_STACK_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in all_content:
                    self.tech_stack.add(tech)
                    break
    
    # ==========================================
    # Tree Flattening
    # ==========================================
    
    def _flatten_tree(self, file_tree: List[str]) -> str:
        """
        Collapse empty intermediate directories (common in Java/C++ projects).
        
        Before: src/main/java/com/example/app/Main.java
        After:  src/.../Main.java (or keep if meaningful)
        """
        if not file_tree:
            return "No files found"
        
        # Group files by their simplified paths
        simplified = []
        
        for path in file_tree:
            parts = path.split("/")
            
            # Collapse long Java-style paths
            if len(parts) > 5:
                # Keep first 2 and last 2 parts
                simplified_path = "/".join(parts[:2]) + "/.../" + "/".join(parts[-2:])
                simplified.append(simplified_path)
            else:
                simplified.append(path)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for path in simplified:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        
        return "\n".join(unique[:100])  # Limit to 100 entries
    
    def _generate_infra_summary(self, parsed_files: Dict[str, ParsedFile]) -> str:
        """
        Generate a summary of infrastructure files and security findings.
        """
        infra_files = [f for f in parsed_files.values() if f.file_type == "infra"]
        
        if not infra_files:
            return "No infrastructure files detected."
        
        lines = [
            f"Found {len(infra_files)} infrastructure file(s):",
            ""
        ]
        
        for f in infra_files:
            lines.append(f"  📦 {f.path}")
            for tech in f.tech_hints:
                lines.append(f"     └─ {tech}")
            for note in f.security_notes:
                lines.append(f"     └─ {note}")
        
        return "\n".join(lines)
    
    # ==========================================
    # Helpers
    # ==========================================
    
    def _get_extension(self, path: str) -> str:
        """Get file extension without the dot."""
        if "." in path:
            return path.rsplit(".", 1)[-1].lower()
        return ""
    
    def _should_skip(self, path: str) -> bool:
        """Check if file should be skipped."""
        path_lower = path.lower()
        
        for pattern in SKIP_PATTERNS:
            if pattern.startswith("*"):
                # Extension match
                if path_lower.endswith(pattern[1:]):
                    return True
            elif "*" in pattern:
                # Directory match
                import fnmatch
                if fnmatch.fnmatch(path_lower, pattern.lower()):
                    return True
            else:
                # Exact match
                if pattern.lower() in path_lower:
                    return True
        
        return False
    
    def _is_infra_file(self, path: str, filename: str) -> bool:
        """Check if file is infrastructure-related."""
        return filename in INFRA_FILES or filename == "Dockerfile"
    
    def _is_k8s_file(self, path: str, content: str) -> bool:
        """Check if file is a Kubernetes manifest."""
        if "k8s" in path.lower() or "kubernetes" in path.lower():
            return True
        
        # Check YAML content for K8s markers
        if path.endswith((".yaml", ".yml")):
            if "apiVersion:" in content and "kind:" in content:
                return True
        
        return False
    
    def _clean_notebook_code(self, source: str) -> str:
        """
        Clean notebook code cell - remove excessive blank lines and simple comments.
        """
        lines = source.split("\n")
        cleaned = []
        blank_count = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip excessive blank lines
            if not stripped:
                blank_count += 1
                if blank_count <= 1:
                    cleaned.append("")
                continue
            
            blank_count = 0
            
            # Keep the line
            cleaned.append(line)
        
        return "\n".join(cleaned)


# ==========================================
# Convenience Function
# ==========================================

def analyze_repo_files(files: Dict[str, str], file_tree: List[str]) -> ParsedRepo:
    """
    Convenience function to parse a repository.
    
    Args:
        files: Dict mapping file paths to their content
        file_tree: List of all file paths in the repo
    
    Returns:
        ParsedRepo with cleaned files, tech stack, and analysis
    """
    parser = UniversalParser()
    return parser.parse_repo(files, file_tree)
