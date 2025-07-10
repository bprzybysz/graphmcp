"""
Source Type Classification System for Database Decommissioning Workflow.

This module provides comprehensive classification of source types found in repositories
and maps them to appropriate rule sets for database decommissioning workflows.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class SourceType(Enum):
    """Enumeration of supported source types."""
    INFRASTRUCTURE = "infrastructure"
    CONFIG = "config"
    SQL = "sql"
    PYTHON = "python"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    """Result of source type classification."""
    source_type: SourceType
    confidence: float  # 0.0 to 1.0
    matched_patterns: List[str]
    detected_frameworks: List[str]
    rule_files: List[str]

class SourceTypeClassifier:
    """Classifies source types based on file patterns and content analysis."""
    
    def __init__(self):
        self.classification_patterns = self._initialize_patterns()
        self.framework_patterns = self._initialize_framework_patterns()
        
    def _initialize_patterns(self) -> Dict[SourceType, Dict[str, List[str]]]:
        """Initialize file patterns for each source type."""
        return {
            SourceType.INFRASTRUCTURE: {
                "file_extensions": [".tf", ".tfvars", ".hcl", ".nomad"],
                "file_names": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", 
                             "Vagrantfile", "Jenkinsfile", "Makefile"],
                "directory_patterns": ["terraform/", "helm/", "k8s/", "kubernetes/", 
                                     "charts/", "manifests/", "deployment/", "infra/"],
                "content_patterns": [
                    r"resource\s+\"[^\"]+\"\s+\"[^\"]+\"",  # Terraform resources
                    r"apiVersion:\s*v\d+",  # Kubernetes API version
                    r"kind:\s*(Deployment|Service|ConfigMap|Secret)",  # K8s resources
                    r"FROM\s+[\w\-\.\/]+",  # Dockerfile FROM
                    r"helm\s+(install|upgrade|delete)",  # Helm commands
                ]
            },
            SourceType.CONFIG: {
                "file_extensions": [".yml", ".yaml", ".json", ".toml", ".ini", ".conf", 
                                  ".config", ".properties", ".env"],
                "file_names": [".env", ".env.local", ".env.production", "config.yml",
                             "application.yml", "settings.yml", "config.json"],
                "directory_patterns": ["config/", "configs/", "settings/", "env/"],
                "content_patterns": [
                    r"database[_\-]?url[:\s]*",
                    r"db[_\-]?(host|port|name|user)[:\s]*",
                    r"connection[_\-]?string[:\s]*",
                    r"jdbc:[^\"'\s]+",
                    r"postgresql://[^\"'\s]+",
                    r"mysql://[^\"'\s]+",
                ]
            },
            SourceType.SQL: {
                "file_extensions": [".sql", ".ddl", ".dml", ".dump", ".backup"],
                "file_names": ["schema.sql", "dump.sql", "backup.sql", "migration.sql"],
                "directory_patterns": ["sql/", "migrations/", "database/", "db/", 
                                     "schemas/", "dumps/", "backups/"],
                "content_patterns": [
                    r"CREATE\s+(TABLE|DATABASE|SCHEMA|INDEX)",
                    r"DROP\s+(TABLE|DATABASE|SCHEMA|INDEX)",
                    r"ALTER\s+TABLE",
                    r"INSERT\s+INTO",
                    r"SELECT\s+.*\s+FROM",
                    r"UPDATE\s+.*\s+SET",
                    r"DELETE\s+FROM",
                ]
            },
            SourceType.PYTHON: {
                "file_extensions": [".py", ".pyw", ".pyx", ".pyi"],
                "file_names": ["manage.py", "wsgi.py", "asgi.py", "settings.py", 
                             "models.py", "migrations.py"],
                "directory_patterns": ["python/", "src/", "app/", "apps/", "migrations/"],
                "content_patterns": [
                    r"from\s+django",
                    r"import\s+django",
                    r"from\s+sqlalchemy",
                    r"import\s+sqlalchemy",
                    r"class\s+\w+\(models\.Model\)",
                    r"class\s+\w+\(db\.Model\)",
                    r"@app\.route",
                    r"def\s+\w+\(request",
                ]
            },
            SourceType.DOCUMENTATION: {
                "file_extensions": [".md", ".rst", ".txt", ".adoc", ".wiki"],
                "file_names": ["README.md", "CHANGELOG.md", "CONTRIBUTING.md", 
                             "ARCHITECTURE.md", "API.md"],
                "directory_patterns": ["docs/", "documentation/", "wiki/"],
                "content_patterns": [
                    r"#\s+.*[Dd]atabase",
                    r"##\s+.*[Ss]chema",
                    r"```sql",
                    r"```python",
                    r"API\s+documentation",
                ]
            }
        }
    
    def _initialize_framework_patterns(self) -> Dict[str, List[str]]:
        """Initialize framework detection patterns."""
        return {
            "terraform": [r"terraform\s*{", r"provider\s+\"[^\"]+\"", r"resource\s+\"[^\"]+\""],
            "kubernetes": [r"apiVersion:", r"kind:", r"metadata:"],
            "helm": [r"Chart\.yaml", r"values\.yaml", r"templates/"],
            "docker": [r"FROM\s+", r"RUN\s+", r"COPY\s+", r"ADD\s+"],
            "django": [r"from\s+django", r"DJANGO_SETTINGS_MODULE", r"manage\.py"],
            "flask": [r"from\s+flask", r"@app\.route", r"Flask\(__name__\)"],
            "fastapi": [r"from\s+fastapi", r"@app\.(get|post|put|delete)", r"FastAPI\("],
            "sqlalchemy": [r"from\s+sqlalchemy", r"declarative_base", r"Column\("],
            "alembic": [r"from\s+alembic", r"revision\s*=", r"down_revision\s*="],
        }
    
    def classify_file(self, file_path: str, content: Optional[str] = None) -> ClassificationResult:
        """Classify a single file."""
        path = Path(file_path)
        
        # Initialize scores for each source type
        scores = {source_type: 0.0 for source_type in SourceType}
        matched_patterns = []
        detected_frameworks = []
        
        # File extension scoring
        for source_type, patterns in self.classification_patterns.items():
            if path.suffix.lower() in patterns["file_extensions"]:
                scores[source_type] += 0.4
                matched_patterns.append(f"extension:{path.suffix}")
        
        # File name scoring
        for source_type, patterns in self.classification_patterns.items():
            if path.name in patterns["file_names"]:
                scores[source_type] += 0.3
                matched_patterns.append(f"filename:{path.name}")
        
        # Directory pattern scoring
        path_str = str(path).lower()
        for source_type, patterns in self.classification_patterns.items():
            for dir_pattern in patterns["directory_patterns"]:
                if dir_pattern in path_str:
                    scores[source_type] += 0.2
                    matched_patterns.append(f"directory:{dir_pattern}")
        
        # Content analysis if available
        if content:
            content_scores, content_patterns, frameworks = self._analyze_content(content)
            for source_type, score in content_scores.items():
                scores[source_type] += score
            matched_patterns.extend(content_patterns)
            detected_frameworks.extend(frameworks)
        
        # Determine best match
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type], 1.0)
        
        # If confidence is too low, mark as unknown
        if confidence < 0.1:
            best_type = SourceType.UNKNOWN
            confidence = 0.0
        
        # Determine applicable rule files
        rule_files = self._get_rule_files(best_type, detected_frameworks)
        
        return ClassificationResult(
            source_type=best_type,
            confidence=confidence,
            matched_patterns=matched_patterns,
            detected_frameworks=detected_frameworks,
            rule_files=rule_files
        )
    
    def _analyze_content(self, content: str) -> Tuple[Dict[SourceType, float], List[str], List[str]]:
        """Analyze file content for classification."""
        scores = {source_type: 0.0 for source_type in SourceType}
        matched_patterns = []
        detected_frameworks = []
        
        # Check content patterns
        for source_type, patterns in self.classification_patterns.items():
            for pattern in patterns["content_patterns"]:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    scores[source_type] += 0.1 * len(matches)
                    matched_patterns.append(f"content:{pattern}")
        
        # Check framework patterns
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    detected_frameworks.append(framework)
                    break
        
        return scores, matched_patterns, detected_frameworks
    
    def _get_rule_files(self, source_type: SourceType, frameworks: List[str]) -> List[str]:
        """Get applicable rule files for the source type and frameworks."""
        rule_files = ["workflows/ruliade/general_rules.md"]
        
        if source_type == SourceType.INFRASTRUCTURE:
            rule_files.append("workflows/ruliade/infrastructure_rules.md")
        elif source_type == SourceType.CONFIG:
            rule_files.append("workflows/ruliade/config_rules.md")
        elif source_type == SourceType.SQL:
            rule_files.append("workflows/ruliade/sql_rules.md")
        elif source_type == SourceType.PYTHON:
            rule_files.append("workflows/ruliade/python_rules.md")
        
        return rule_files
    
    def classify_repository(self, repo_path: str, file_patterns: List[str] = None) -> Dict[str, ClassificationResult]:
        """Classify all relevant files in a repository."""
        results = {}
        repo = Path(repo_path)
        
        # Default patterns if none provided
        if file_patterns is None:
            file_patterns = ["**/*.py", "**/*.sql", "**/*.tf", "**/*.yml", "**/*.yaml", 
                           "**/*.json", "**/*.md", "**/Dockerfile", "**/docker-compose*"]
        
        for pattern in file_patterns:
            for file_path in repo.glob(pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        result = self.classify_file(str(file_path), content)
                        results[str(file_path)] = result
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error processing {file_path}: {e}")
                        result = self.classify_file(str(file_path))
                        results[str(file_path)] = result
        
        return results
    
    def get_source_type_summary(self, classifications: Dict[str, ClassificationResult]) -> Dict[SourceType, List[str]]:
        """Get a summary of files by source type."""
        summary = {source_type: [] for source_type in SourceType}
        
        for file_path, result in classifications.items():
            summary[result.source_type].append(file_path)
        
        return summary
    
    def get_framework_summary(self, classifications: Dict[str, ClassificationResult]) -> Dict[str, List[str]]:
        """Get a summary of detected frameworks."""
        framework_files = {}
        
        for file_path, result in classifications.items():
            for framework in result.detected_frameworks:
                if framework not in framework_files:
                    framework_files[framework] = []
                framework_files[framework].append(file_path)
        
        return framework_files

def get_database_search_patterns(source_type: SourceType, database_name: str) -> List[str]:
    """Get database-specific search patterns for a source type."""
    base_patterns = [
        database_name,
        database_name.upper(),
        database_name.lower(),
        database_name.replace('_', '-'),
        database_name.replace('-', '_'),
    ]
    
    if source_type == SourceType.INFRASTRUCTURE:
        return [
            f'name.*{database_name}',
            f'database.*{database_name}',
            f'{database_name}.*database',
            f'resource.*{database_name}',
        ] + base_patterns
    
    elif source_type == SourceType.CONFIG:
        return [
            f'database.*{database_name}',
            f'db.*{database_name}',
            f'{database_name}.*url',
            f'{database_name}.*connection',
        ] + base_patterns
    
    elif source_type == SourceType.SQL:
        return [
            f'CREATE.*{database_name}',
            f'USE.*{database_name}',
            f'DATABASE.*{database_name}',
            f'SCHEMA.*{database_name}',
        ] + base_patterns
    
    elif source_type == SourceType.PYTHON:
        return [
            f'database.*{database_name}',
            f'db.*{database_name}',
            f'{database_name}.*model',
            f'class.*{database_name}',
        ] + base_patterns
    
    else:
        return base_patterns 