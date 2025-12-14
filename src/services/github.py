"""
GitHub Scraper Service (Stage 1: The Eyes)

Fetches repository data from GitHub API:
- File tree (recursive)
- README content
- Dependency files (package.json, requirements.txt, etc.)
- Commit history
- Assets (images, videos)
- Homepage/deployment URL
"""

import os
import re
import httpx
from typing import Optional, Tuple, List
from src.core.schemas import RepoMetadata, Asset, FileNode


# Asset file extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}


class GitHubScraper:
    """Fetches repository data from GitHub REST API"""
    
    BASE_URL = "https://api.github.com"
    RAW_URL = "https://raw.githubusercontent.com"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitGrade/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        
        # Collectors for assets and file nodes
        self._assets: List[Asset] = []
        self._file_nodes: List[FileNode] = []
        self._default_branch: str = "main"
    
    def parse_repo_url(self, url: str) -> Tuple[str, str]:
        """
        Extracts owner and repo name from GitHub URL.
        Supports: https://github.com/owner/repo, github.com/owner/repo
        """
        # Remove trailing slashes and .git suffix
        url = url.rstrip("/").removesuffix(".git")
        
        # Match github.com/owner/repo pattern
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        return match.group(1), match.group(2)
    
    async def fetch_repo_info(self, owner: str, repo: str) -> Tuple[Optional[str], str]:
        """Fetches repository info including homepage URL and default branch."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            
            if response.status_code != 200:
                return None, "main"
            
            data = response.json()
            homepage = data.get("homepage")
            default_branch = data.get("default_branch", "main")
            
            # homepage might be empty string
            if homepage and homepage.strip():
                return homepage.strip(), default_branch
            
            return None, default_branch
    
    def _get_asset_type(self, filename: str) -> Optional[str]:
        """Determine if file is an asset and its type."""
        ext = os.path.splitext(filename.lower())[1]
        if ext in IMAGE_EXTENSIONS:
            return "image"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        return None
    
    def _build_raw_url(self, owner: str, repo: str, path: str) -> str:
        """Build raw.githubusercontent.com URL for direct access."""
        return f"{self.RAW_URL}/{owner}/{repo}/{self._default_branch}/{path}"
    
    async def fetch_file_tree(self, owner: str, repo: str, path: str = "", depth: int = 0, max_depth: int = 3) -> str:
        """
        Recursively fetches the file tree from GitHub API.
        Also collects assets and file nodes for diagram.
        Limits depth to avoid excessive API calls.
        """
        if depth >= max_depth:
            return ""
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)
            
            if response.status_code == 404:
                return "[Repository not found or private]"
            elif response.status_code == 403:
                return "[Rate limit exceeded - add GITHUB_TOKEN to .env]"
            elif response.status_code != 200:
                return f"[Error fetching contents: {response.status_code}]"
            
            contents = response.json()
        
        tree_str = ""
        indent = "    " * depth
        
        # Sort: directories first, then files
        contents = sorted(contents, key=lambda x: (x["type"] != "dir", x["name"]))
        
        for item in contents:
            name = item["name"]
            item_type = item["type"]
            item_path = f"{path}/{name}".lstrip("/") if path else name
            
            # Skip common unneeded directories
            if name in ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"]:
                tree_str += f"{indent}{name}/ [SKIPPED]\n"
                continue
            
            if item_type == "dir":
                tree_str += f"{indent}{name}/\n"
                
                # Add folder to file nodes
                self._file_nodes.append(FileNode(
                    name=name,
                    path=item_path,
                    type="folder",
                    health="healthy",
                    issues=[]
                ))
                
                # Recurse into subdirectory
                sub_tree = await self.fetch_file_tree(owner, repo, item_path, depth + 1, max_depth)
                tree_str += sub_tree
            else:
                tree_str += f"{indent}{name}\n"
                
                # Check if it's an asset
                asset_type = self._get_asset_type(name)
                if asset_type:
                    self._assets.append(Asset(
                        name=name,
                        url=self._build_raw_url(owner, repo, item_path),
                        type=asset_type,
                        path=item_path
                    ))
                
                # Add file to file nodes
                self._file_nodes.append(FileNode(
                    name=name,
                    path=item_path,
                    type="file",
                    health="healthy",  # Will be updated by linter
                    issues=[]
                ))
        
        return tree_str
    
    async def fetch_readme(self, owner: str, repo: str) -> str:
        """Fetches README content from the repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers={**self.headers, "Accept": "application/vnd.github.v3.raw"},
                timeout=30.0
            )
            
            if response.status_code == 404:
                return "[No README found]"
            elif response.status_code != 200:
                return f"[Error fetching README: {response.status_code}]"
            
            return response.text[:3000]  # Truncate to save tokens
    
    async def fetch_commits(self, owner: str, repo: str, limit: int = 10) -> str:
        """Fetches recent commit messages."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            
            if response.status_code != 200:
                return "[Error fetching commits]"
            
            commits = response.json()
        
        commit_log = ""
        for commit in commits:
            sha = commit["sha"][:7]
            message = commit["commit"]["message"].split("\n")[0]  # First line only
            author = commit["commit"]["author"]["name"]
            commit_log += f"{sha} - {message} ({author})\n"
        
        return commit_log
    
    async def fetch_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetches raw content of a specific file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={**self.headers, "Accept": "application/vnd.github.v3.raw"},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return None
            
            return response.text
    
    async def fetch_dependency_files(self, owner: str, repo: str) -> str:
        """Fetches common dependency/config files."""
        dependency_files = [
            "package.json", "requirements.txt", "pyproject.toml",
            "pom.xml", "build.gradle", "Gemfile", "go.mod", "Cargo.toml",
            ".gitignore", "Dockerfile"
        ]
        
        content = ""
        for filename in dependency_files:
            file_content = await self.fetch_file_content(owner, repo, filename)
            if file_content:
                content += f"--- {filename} ---\n{file_content[:1500]}\n\n"
        
        return content if content else "[No standard dependency files found]"
    
    async def analyze_repository(self, repo_url: str) -> RepoMetadata:
        """
        Main entry point: Fetches all repository data and returns RepoMetadata.
        """
        owner, repo_name = self.parse_repo_url(repo_url)
        
        # Reset collectors
        self._assets = []
        self._file_nodes = []
        
        # Fetch repo info first to get homepage and default branch
        homepage_url, self._default_branch = await self.fetch_repo_info(owner, repo_name)
        
        # Fetch all data
        file_tree = await self.fetch_file_tree(owner, repo_name)
        readme_content = await self.fetch_readme(owner, repo_name)
        dependency_files = await self.fetch_dependency_files(owner, repo_name)
        commit_log = await self.fetch_commits(owner, repo_name)
        
        # Detect basic indicators from file tree
        has_tests = any(term in file_tree.lower() for term in ["test", "tests", "spec", "__tests__"])
        has_readme = "[No README found]" not in readme_content
        has_gitignore = ".gitignore" in dependency_files
        
        # Count files (rough estimate from tree)
        total_files = file_tree.count("\n") - file_tree.count("/\n")
        
        # Detect primary language from dependency files
        detected_language = None
        if "package.json" in dependency_files:
            detected_language = "JavaScript/TypeScript"
        elif "requirements.txt" in dependency_files or "pyproject.toml" in dependency_files:
            detected_language = "Python"
        elif "pom.xml" in dependency_files or "build.gradle" in dependency_files:
            detected_language = "Java"
        elif "go.mod" in dependency_files:
            detected_language = "Go"
        elif "Cargo.toml" in dependency_files:
            detected_language = "Rust"
        
        return RepoMetadata(
            owner=owner,
            repo_name=repo_name,
            file_tree=file_tree,
            readme_content=readme_content,
            dependency_files=dependency_files,
            commit_log=commit_log,
            detected_language=detected_language,
            total_files=total_files,
            has_tests=has_tests,
            has_readme=has_readme,
            has_gitignore=has_gitignore,
            homepage_url=homepage_url,
            assets=self._assets.copy(),
            file_nodes=self._file_nodes.copy(),
            default_branch=self._default_branch
        )


# Convenience function for simple usage
async def scrape_github_repo(repo_url: str) -> RepoMetadata:
    """Scrapes a GitHub repository and returns metadata."""
    scraper = GitHubScraper()
    return await scraper.analyze_repository(repo_url)
