"""
Linter Service (Stage 2: The Quantifier/Calculator)

Performs static analysis on repository metadata to calculate hard metrics.
Uses heuristics instead of running actual linters (for speed and simplicity).
"""

import re
from typing import List, Tuple
from src.core.schemas import RepoMetadata, HardMetrics


class Linter:
    """Analyzes repository metadata to calculate quality metrics."""
    
    # Conventional commit prefixes (good practice)
    GOOD_COMMIT_PREFIXES = ["feat", "fix", "docs", "style", "refactor", "test", "chore", "ci", "perf", "build"]
    
    # Bad commit patterns (lazy commits)
    BAD_COMMIT_PATTERNS = [
        r"^(update|fix|change|edit|modify|test)\s*$",  # Single word lazy commits
        r"^(wip|tmp|temp|asdf|aaa|xxx)",  # Work in progress / garbage
        r"^(initial commit|first commit|init)$",  # Default commits (only bad if it's the only pattern)
        r"^\.+$",  # Just dots
    ]
    
    # Good structure indicators
    GOOD_STRUCTURE = ["src/", "lib/", "app/", "tests/", "test/", "docs/", "config/"]
    
    # Bad structure indicators (files that shouldn't be committed)
    BAD_STRUCTURE = ["node_modules/", ".venv/", "venv/", "__pycache__/", ".env", "*.pyc"]
    
    def analyze(self, metadata: RepoMetadata) -> HardMetrics:
        """
        Analyzes repository metadata and returns calculated metrics.
        """
        issues = []
        
        # Calculate individual scores
        structure_score, structure_issues = self._score_structure(metadata)
        docs_score, docs_issues = self._score_documentation(metadata)
        test_score, test_issues = self._score_tests(metadata)
        commit_score, commit_issues = self._score_commits(metadata)
        
        issues.extend(structure_issues)
        issues.extend(docs_issues)
        issues.extend(test_issues)
        issues.extend(commit_issues)
        
        return HardMetrics(
            structure_score=structure_score,
            docs_score=docs_score,
            test_score=test_score,
            commit_quality_score=commit_score,
            issues=issues
        )
    
    def _score_structure(self, metadata: RepoMetadata) -> Tuple[int, List[str]]:
        """Scores project organization (0-100)."""
        score = 50  # Base score
        issues = []
        
        file_tree = metadata.file_tree.lower()
        
        # Good structure bonuses
        for pattern in self.GOOD_STRUCTURE:
            if pattern.lower() in file_tree:
                score += 10
        
        # Bad structure penalties
        for pattern in self.BAD_STRUCTURE:
            if pattern.lower().replace("*", "") in file_tree:
                score -= 20
                issues.append(f"❌ '{pattern}' should not be committed - add to .gitignore")
        
        # .gitignore bonus
        if metadata.has_gitignore:
            score += 10
        else:
            issues.append("⚠️ Missing .gitignore file")
        
        # Penalty for too few files (likely incomplete)
        if metadata.total_files < 5:
            score -= 20
            issues.append("⚠️ Very few files - project may be incomplete")
        
        return max(0, min(100, score)), issues
    
    def _score_documentation(self, metadata: RepoMetadata) -> Tuple[int, List[str]]:
        """Scores documentation quality (0-100)."""
        score = 0
        issues = []
        
        readme = metadata.readme_content
        
        if not metadata.has_readme or readme == "[No README found]":
            issues.append("❌ No README.md found - critical for any project")
            return 0, issues
        
        # Base points for having README
        score += 30
        
        # Length bonus
        if len(readme) > 500:
            score += 20
        elif len(readme) > 200:
            score += 10
        else:
            issues.append("⚠️ README is too short - add more details")
        
        # Check for key sections
        readme_lower = readme.lower()
        
        if "install" in readme_lower or "setup" in readme_lower or "getting started" in readme_lower:
            score += 15
        else:
            issues.append("⚠️ README missing installation/setup instructions")
        
        if "usage" in readme_lower or "example" in readme_lower or "how to" in readme_lower:
            score += 15
        else:
            issues.append("⚠️ README missing usage examples")
        
        if "```" in readme:  # Code blocks
            score += 10
        
        if "license" in readme_lower or "mit" in readme_lower or "apache" in readme_lower:
            score += 10
        
        return min(100, score), issues
    
    def _score_tests(self, metadata: RepoMetadata) -> Tuple[int, List[str]]:
        """Scores test coverage indicators (0-100)."""
        score = 0
        issues = []
        
        file_tree = metadata.file_tree.lower()
        deps = metadata.dependency_files.lower()
        
        # Check for test directories
        if metadata.has_tests:
            score += 40
        else:
            issues.append("❌ No test directory found (tests/, test/, __tests__/, spec/)")
        
        # Check for test files
        test_file_patterns = [".test.", "_test.", ".spec.", "_spec."]
        has_test_files = any(p in file_tree for p in test_file_patterns)
        
        if has_test_files:
            score += 30
        elif metadata.has_tests:
            issues.append("⚠️ Test directory exists but no test files found")
        
        # Check for testing frameworks in dependencies
        testing_frameworks = ["pytest", "jest", "mocha", "junit", "rspec", "unittest", "vitest"]
        has_framework = any(f in deps for f in testing_frameworks)
        
        if has_framework:
            score += 20
        else:
            issues.append("⚠️ No testing framework found in dependencies")
        
        # CI/CD bonus
        if ".github/workflows" in metadata.file_tree or "ci" in metadata.dependency_files.lower():
            score += 10
        
        return min(100, score), issues
    
    def _score_commits(self, metadata: RepoMetadata) -> Tuple[int, List[str]]:
        """Scores commit message quality (0-100)."""
        commits = metadata.commit_log.strip()
        
        if not commits or commits.startswith("["):
            return 50, ["⚠️ Could not analyze commit history"]
        
        lines = commits.split("\n")
        if not lines:
            return 50, ["⚠️ No commits found"]
        
        good_count = 0
        bad_count = 0
        issues = []
        
        for line in lines:
            # Extract just the message part (after the hash and dash)
            parts = line.split(" - ", 1)
            if len(parts) < 2:
                continue
            
            message = parts[1].split("(")[0].strip().lower()
            
            # Check for conventional commit format
            is_conventional = any(message.startswith(f"{prefix}:") or message.startswith(f"{prefix}(") 
                                 for prefix in self.GOOD_COMMIT_PREFIXES)
            
            # Check for bad patterns
            is_bad = any(re.match(pattern, message, re.IGNORECASE) for pattern in self.BAD_COMMIT_PATTERNS)
            
            if is_conventional:
                good_count += 1
            elif is_bad:
                bad_count += 1
        
        total = good_count + bad_count
        if total == 0:
            return 60, []
        
        # Score based on ratio
        good_ratio = good_count / len(lines)
        bad_ratio = bad_count / len(lines)
        
        score = int(50 + (good_ratio * 50) - (bad_ratio * 30))
        
        if bad_ratio > 0.3:
            issues.append("⚠️ Many commits have lazy messages (e.g., 'update', 'fix'). Use conventional commits.")
        
        if good_ratio > 0.5:
            issues.append("✅ Good use of conventional commit format!")
        
        return max(0, min(100, score)), issues


def analyze_repository(metadata: RepoMetadata) -> HardMetrics:
    """Convenience function to analyze a repository."""
    linter = Linter()
    return linter.analyze(metadata)
