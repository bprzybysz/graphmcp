"""
Contextual Rules Engine for Database Decommissioning.

This module provides intelligent rule application based on source type classification
and detected frameworks, ensuring appropriate rules are applied to each file type.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

from .source_type_classifier import SourceType, ClassificationResult

logger = logging.getLogger(__name__)

@dataclass
class RuleResult:
    """Result of applying a rule to a file."""
    rule_id: str
    rule_description: str
    applied: bool
    changes_made: int
    warnings: List[str]
    errors: List[str]

@dataclass
class FileProcessingResult:
    """Result of processing a single file with rules."""
    file_path: str
    source_type: SourceType
    rules_applied: List[RuleResult]
    total_changes: int
    success: bool
    error_message: Optional[str] = None

class ContextualRulesEngine:
    """Engine for applying contextual rules based on source type and frameworks."""
    
    def __init__(self):
        self.rule_processors = {
            SourceType.INFRASTRUCTURE: self._process_infrastructure_rules,
            SourceType.CONFIG: self._process_config_rules,
            SourceType.SQL: self._process_sql_rules,
            SourceType.PYTHON: self._process_python_rules,
            SourceType.SHELL: self._process_shell_rules,
            SourceType.DOCUMENTATION: self._process_documentation_rules,
        }
        
        # Load rule definitions
        self.rule_definitions = self._load_rule_definitions()
    
    def _load_rule_definitions(self) -> Dict[SourceType, Dict[str, Any]]:
        """Load rule definitions from rule files."""
        rules = {
            SourceType.INFRASTRUCTURE: self._load_infrastructure_rules(),
            SourceType.CONFIG: self._load_config_rules(),
            SourceType.SQL: self._load_sql_rules(),
            SourceType.PYTHON: self._load_python_rules(),
            SourceType.SHELL: self._load_shell_rules(),
            SourceType.DOCUMENTATION: self._load_documentation_rules(),
        }
        return rules
    
    def _load_infrastructure_rules(self) -> Dict[str, Any]:
        """Load infrastructure-specific rules."""
        return {
            "terraform_resource_removal": {
                "id": "R-INFRA-1.1",
                "description": "Remove Terraform database resources",
                "patterns": [
                    r'resource\s+"[^"]*database[^"]*"\s+"{{TARGET_DB}}"',
                    r'resource\s+"[^"]*rds[^"]*"\s+"{{TARGET_DB}}"',
                    r'resource\s+"[^"]*postgresql[^"]*"\s+"{{TARGET_DB}}"',
                ],
                "action": "comment_out",
                "frameworks": ["terraform"]
            },
            "helm_values_cleanup": {
                "id": "R-INFRA-4.1",
                "description": "Remove database entries from values.yaml",
                "patterns": [
                    r'^(\s*){{TARGET_DB}}:\s*$',
                    r'^(\s*)database:\s*{{TARGET_DB}}\s*$',
                    r'^(\s*)name:\s*[\'"]{{TARGET_DB}}[\'"]?\s*$',
                ],
                "action": "comment_out",
                "frameworks": ["helm"]
            },
            "kubernetes_manifest_cleanup": {
                "id": "R-INFRA-6.1",
                "description": "Remove Kubernetes database resources",
                "patterns": [
                    r'name:\s*{{TARGET_DB}}[-_].*',
                    r'{{TARGET_DB}}[-_]database',
                    r'DATABASE_NAME:\s*[\'"]{{TARGET_DB}}[\'"]',
                ],
                "action": "comment_out",
                "frameworks": ["kubernetes"]
            },
            "docker_compose_cleanup": {
                "id": "R-INFRA-2.1",
                "description": "Remove Docker Compose database services",
                "patterns": [
                    r'^\s*{{TARGET_DB}}[-_]?(db|database):\s*$',
                    r'POSTGRES_DB:\s*{{TARGET_DB}}',
                    r'DATABASE_NAME:\s*{{TARGET_DB}}',
                ],
                "action": "comment_out",
                "frameworks": ["docker"]
            }
        }
    
    def _load_config_rules(self) -> Dict[str, Any]:
        """Load configuration-specific rules."""
        return {
            "database_url_removal": {
                "id": "R-CONFIG-1.1",
                "description": "Remove database connection URLs",
                "patterns": [
                    r'{{TARGET_DB}}_DATABASE_URL\s*=.*',
                    r'DATABASE_URL.*{{TARGET_DB}}.*',
                    r'{{TARGET_DB}}_CONNECTION_STRING\s*=.*',
                ],
                "action": "comment_out"
            },
            "database_host_removal": {
                "id": "R-CONFIG-1.2", 
                "description": "Remove database host configurations",
                "patterns": [
                    r'{{TARGET_DB}}_HOST\s*[=:].*',
                    r'{{TARGET_DB}}_PORT\s*[=:].*',
                    r'{{TARGET_DB}}_USER\s*[=:].*',
                    r'{{TARGET_DB}}_PASSWORD\s*[=:].*',
                ],
                "action": "comment_out"
            },
            "yaml_config_cleanup": {
                "id": "R-CONFIG-2.1",
                "description": "Remove YAML database configurations", 
                "patterns": [
                    r'^(\s*){{TARGET_DB}}:\s*$',
                    r'^(\s*)database:\s*{{TARGET_DB}}\s*$',
                    r'^(\s*)host:\s*{{TARGET_DB}}[-_].*',
                ],
                "action": "comment_out"
            },
            "helm_values_deprecation": {
                "id": "R-CONFIG-3.1",
                "description": "Mark Helm values and YAML examples as deprecated",
                "patterns": [
                    r'name:\s*[\'"]{{TARGET_DB}}[\'"]',
                    r'# {{TARGET_DB}}',
                    r'{{TARGET_DB}}[-_].*:',
                    r'# .*{{TARGET_DB}}.*',
                ],
                "action": "add_deprecation_notice"
            }
        }
    
    def _load_sql_rules(self) -> Dict[str, Any]:
        """Load SQL-specific rules."""
        return {
            "create_database_removal": {
                "id": "R-SQL-1.1",
                "description": "Comment out CREATE DATABASE statements",
                "patterns": [
                    r'CREATE\s+DATABASE\s+{{TARGET_DB}}\s*;?',
                    r'CREATE\s+SCHEMA\s+{{TARGET_DB}}\s*;?',
                ],
                "action": "comment_out"
            },
            "use_database_removal": {
                "id": "R-SQL-1.2",
                "description": "Comment out USE database statements",
                "patterns": [
                    r'USE\s+{{TARGET_DB}}\s*;?',
                    r'\\connect\s+{{TARGET_DB}}\s*;?',
                    r'\\c\s+{{TARGET_DB}}\s*;?',
                ],
                "action": "comment_out"
            },
            "table_references_cleanup": {
                "id": "R-SQL-2.1",
                "description": "Comment out table references with database prefix",
                "patterns": [
                    r'FROM\s+{{TARGET_DB}}\.\w+',
                    r'INSERT\s+INTO\s+{{TARGET_DB}}\.\w+',
                    r'UPDATE\s+{{TARGET_DB}}\.\w+',
                    r'DELETE\s+FROM\s+{{TARGET_DB}}\.\w+',
                ],
                "action": "comment_out"
            }
        }
    
    def _load_python_rules(self) -> Dict[str, Any]:
        """Load Python-specific rules."""
        return {
            "django_database_config": {
                "id": "R-PYTHON-1.1",
                "description": "Remove Django database configurations",
                "patterns": [
                    r"'{{TARGET_DB}}':\s*\{[^}]*\}",
                    r'"{{TARGET_DB}}":\s*\{[^}]*\}',
                    r'{{TARGET_DB}}_DATABASE\s*=.*',
                ],
                "action": "comment_out",
                "frameworks": ["django"]
            },
            "sqlalchemy_engine_removal": {
                "id": "R-PYTHON-2.1", 
                "description": "Remove SQLAlchemy engine configurations",
                "patterns": [
                    r'{{TARGET_DB}}_engine\s*=.*create_engine.*',
                    r'{{TARGET_DB}}_SESSION\s*=.*',
                    r'{{TARGET_DB}}_connection\s*=.*',
                ],
                "action": "comment_out",
                "frameworks": ["sqlalchemy"]
            },
            "model_references_cleanup": {
                "id": "R-PYTHON-3.1",
                "description": "Comment out database model references",
                "patterns": [
                    r'class\s+{{TARGET_DB}}\w*\(.*Model.*\):',
                    r'from\s+.*{{TARGET_DB}}.*\s+import',
                    r'import\s+.*{{TARGET_DB}}.*',
                ],
                "action": "comment_out"
            },
            "connection_string_cleanup": {
                "id": "R-PYTHON-4.1",
                "description": "Remove database connection strings",
                "patterns": [
                    r'{{TARGET_DB}}_DATABASE_URL\s*=.*',
                    r'DATABASE_URL.*{{TARGET_DB}}.*',
                    r'postgresql://.*{{TARGET_DB}}.*',
                    r'mysql://.*{{TARGET_DB}}.*',
                ],
                "action": "comment_out"
            },
            "test_data_deprecation": {
                "id": "R-PYTHON-5.1",
                "description": "Mark test data and examples as deprecated",
                "patterns": [
                    r'\(\s*"{{TARGET_DB}}"\s*,.*\)',
                    r'"{{TARGET_DB}}":\s*\(',
                    r'"{{TARGET_DB}}":\s*ScenarioDefinition',
                    r'"{{TARGET_DB}}"[,\s]*$',
                ],
                "action": "add_deprecation_notice"
            }
        }
    
    def _load_shell_rules(self) -> Dict[str, Any]:
        """Load shell script-specific rules."""
        return {
            "database_variable_removal": {
                "id": "R-SHELL-1.1",
                "description": "Remove database variable assignments",
                "patterns": [
                    r'^(\s*){{TARGET_DB}}_[A-Z_]*=.*$',
                    r'^(\s*)export\s+{{TARGET_DB}}_[A-Z_]*=.*$',
                    r'^(\s*)DB_NAME=[\'"]{{TARGET_DB}}[\'"].*$',
                    r'^(\s*)DATABASE=[\'"]{{TARGET_DB}}[\'"].*$',
                ],
                "action": "comment_out"
            },
            "database_command_removal": {
                "id": "R-SHELL-1.2",
                "description": "Remove database-related commands",
                "patterns": [
                    r'psql.*{{TARGET_DB}}.*',
                    r'mysql.*{{TARGET_DB}}.*',
                    r'createdb\s+{{TARGET_DB}}',
                    r'dropdb\s+{{TARGET_DB}}',
                    r'pg_dump.*{{TARGET_DB}}.*',
                    r'mysqldump.*{{TARGET_DB}}.*',
                ],
                "action": "comment_out"
            },
            "deployment_script_cleanup": {
                "id": "R-SHELL-2.1",
                "description": "Remove deployment steps for database",
                "patterns": [
                    r'deploy.*{{TARGET_DB}}.*',
                    r'install.*{{TARGET_DB}}.*',
                    r'setup.*{{TARGET_DB}}.*',
                    r'configure.*{{TARGET_DB}}.*',
                ],
                "action": "comment_out"
            }
        }
    
    def _load_documentation_rules(self) -> Dict[str, Any]:
        """Load documentation-specific rules."""
        return {
            "markdown_references_update": {
                "id": "R-DOC-1.1",
                "description": "Update markdown database references with deprecation notices",
                "patterns": [
                    r'#.*{{TARGET_DB}}.*',
                    r'##.*{{TARGET_DB}}.*',
                    r'`{{TARGET_DB}}`',
                    r'{{TARGET_DB}}',
                ],
                "action": "add_deprecation_notice"
            },
            "code_block_cleanup": {
                "id": "R-DOC-1.2",
                "description": "Update code blocks with database references",
                "patterns": [
                    r'```.*{{TARGET_DB}}.*```',
                    r'```sql.*{{TARGET_DB}}.*```',
                    r'```python.*{{TARGET_DB}}.*```',
                ],
                "action": "add_deprecation_notice"
            },
            "table_references_deprecate": {
                "id": "R-DOC-1.3",
                "description": "Mark table entries containing database references as deprecated",
                "patterns": [
                    r'\|.*{{TARGET_DB}}.*\|',
                    r'^\s*\*.*{{TARGET_DB}}.*',
                    r'^\s*-.*{{TARGET_DB}}.*',
                ],
                "action": "add_deprecation_notice"
            },
            "example_configuration_deprecate": {
                "id": "R-DOC-1.4",
                "description": "Mark example configurations as deprecated",
                "patterns": [
                    r'"{{TARGET_DB}}":\s*\{',
                    r'"{{TARGET_DB}}":\s*\(',
                    r'"{{TARGET_DB}}"[,\s]*$',
                ],
                "action": "add_deprecation_notice"
            }
        }
    
    async def process_file_with_contextual_rules(
        self, 
        file_path: str, 
        file_content: str,
        classification: ClassificationResult,
        database_name: str,
        github_client,
        repo_owner: str,
        repo_name: str
    ) -> FileProcessingResult:
        """Process a file using contextual rules based on its classification."""
        try:
            # Get applicable rules for this file type
            applicable_rules = self._get_applicable_rules(
                classification.source_type, 
                classification.detected_frameworks
            )
            
            # Apply rules to the file content
            modified_content = file_content
            rule_results = []
            total_changes = 0
            
            for rule_id, rule_config in applicable_rules.items():
                rule_result = await self._apply_rule(
                    rule_id, rule_config, modified_content, database_name
                )
                
                rule_results.append(rule_result)
                total_changes += rule_result.changes_made
                
                # Update content if rule was applied successfully
                if rule_result.applied and hasattr(rule_result, 'modified_content'):
                    modified_content = rule_result.modified_content
            
            # If changes were made, update the file
            if total_changes > 0:
                await self._update_file_content(
                    github_client, repo_owner, repo_name, file_path, modified_content
                )
            
            return FileProcessingResult(
                file_path=file_path,
                source_type=classification.source_type,
                rules_applied=rule_results,
                total_changes=total_changes,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path} with contextual rules: {e}")
            return FileProcessingResult(
                file_path=file_path,
                source_type=classification.source_type,
                rules_applied=[],
                total_changes=0,
                success=False,
                error_message=str(e)
            )
    
    def _get_applicable_rules(
        self, 
        source_type: SourceType, 
        detected_frameworks: List[str]
    ) -> Dict[str, Any]:
        """Get rules applicable to the given source type and frameworks."""
        applicable_rules = {}
        
        # Get rules for the source type
        if source_type in self.rule_definitions:
            source_rules = self.rule_definitions[source_type]
            
            for rule_id, rule_config in source_rules.items():
                # Check if rule is framework-specific
                required_frameworks = rule_config.get("frameworks", [])
                
                if not required_frameworks:
                    # General rule for this source type
                    applicable_rules[rule_id] = rule_config
                else:
                    # Framework-specific rule
                    for framework in required_frameworks:
                        if framework in detected_frameworks:
                            applicable_rules[rule_id] = rule_config
                            break
        
        return applicable_rules
    
    async def _apply_rule(
        self, 
        rule_id: str, 
        rule_config: Dict[str, Any], 
        content: str, 
        database_name: str
    ) -> RuleResult:
        """Apply a single rule to file content."""
        try:
            patterns = rule_config.get("patterns", [])
            action = rule_config.get("action", "comment_out")
            description = rule_config.get("description", f"Apply rule {rule_id}")
            
            # Replace template variables in patterns
            processed_patterns = []
            for pattern in patterns:
                processed_pattern = pattern.replace("{{TARGET_DB}}", database_name)
                processed_patterns.append(processed_pattern)
            
            # Apply the rule based on action type
            if action == "comment_out":
                modified_content, changes = self._comment_out_patterns(content, processed_patterns)
            elif action == "add_deprecation_notice":
                modified_content, changes = self._add_deprecation_notice(content, processed_patterns, database_name)
            elif action == "remove_lines":
                modified_content, changes = self._remove_matching_lines(content, processed_patterns)
            else:
                logger.warning(f"Unknown action '{action}' for rule {rule_id}")
                return RuleResult(
                    rule_id=rule_id,
                    rule_description=description,
                    applied=False,
                    changes_made=0,
                    warnings=[f"Unknown action: {action}"],
                    errors=[]
                )
            
            result = RuleResult(
                rule_id=rule_id,
                rule_description=description,
                applied=changes > 0,
                changes_made=changes,
                warnings=[],
                errors=[]
            )
            
            # Store modified content for later use
            result.modified_content = modified_content
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying rule {rule_id}: {e}")
            return RuleResult(
                rule_id=rule_id,
                rule_description=rule_config.get("description", f"Apply rule {rule_id}"),
                applied=False,
                changes_made=0,
                warnings=[],
                errors=[str(e)]
            )
    
    def _comment_out_patterns(self, content: str, patterns: List[str]) -> Tuple[str, int]:
        """Comment out lines matching the given patterns."""
        lines = content.split('\n')
        modified_lines = []
        changes_made = 0
        
        for line in lines:
            line_modified = False
            
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Don't double-comment already commented lines
                    stripped = line.strip()
                    if not (stripped.startswith('#') or stripped.startswith('//') or 
                           stripped.startswith('/*')):
                        # Determine comment style based on file extension
                        comment_prefix = self._get_comment_prefix(pattern)
                        modified_lines.append(f"{comment_prefix} {line}")
                        changes_made += 1
                        line_modified = True
                        break
            
            if not line_modified:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines), changes_made
    
    def _add_deprecation_notice(self, content: str, patterns: List[str], database_name: str) -> Tuple[str, int]:
        """Add deprecation notices for matching patterns."""
        lines = content.split('\n')
        modified_lines = []
        changes_made = 0
        deprecation_added = set()  # Track where we've already added notices
        
        for i, line in enumerate(lines):
            line_matched = False
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Add deprecation notice before the line if not already added
                    notice_key = f"{i}_{pattern}"
                    if notice_key not in deprecation_added:
                        comment_prefix = self._get_comment_prefix_for_line(line)
                        
                        # Create context-aware deprecation notices
                        if any(keyword in line.lower() for keyword in ['test', 'example', 'demo', 'sample']):
                            deprecation_notice = f"{comment_prefix} DEPRECATED: {database_name} database has been decommissioned - update test/example data"
                        elif '|' in line and line.count('|') >= 2:  # Table format
                            deprecation_notice = f"{comment_prefix} DEPRECATED: {database_name} database has been decommissioned"
                        elif line.strip().startswith(('*', '-', '•')):  # List items
                            deprecation_notice = f"{comment_prefix} DEPRECATED: {database_name} database has been decommissioned"
                        elif 'scenario' in line.lower() or 'definition' in line.lower():
                            deprecation_notice = f"{comment_prefix} DEPRECATED: {database_name} database has been decommissioned - remove from scenarios"
                        else:
                            deprecation_notice = f"{comment_prefix} DEPRECATED: {database_name} database has been decommissioned"
                        
                        modified_lines.append(deprecation_notice)
                        deprecation_added.add(notice_key)
                        changes_made += 1
                    
                    modified_lines.append(line)
                    line_matched = True
                    break
            
            if not line_matched:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines), changes_made
    
    def _remove_matching_lines(self, content: str, patterns: List[str]) -> Tuple[str, int]:
        """Remove lines matching the given patterns."""
        lines = content.split('\n')
        modified_lines = []
        changes_made = 0
        
        for line in lines:
            should_remove = False
            
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_remove = True
                    changes_made += 1
                    break
            
            if not should_remove:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines), changes_made
    
    def _get_comment_prefix(self, pattern: str) -> str:
        """Get appropriate comment prefix based on pattern context."""
        # Simple heuristic based on pattern content
        if any(keyword in pattern.lower() for keyword in ['yaml', 'yml', 'docker']):
            return '#'
        elif any(keyword in pattern.lower() for keyword in ['sql', 'database']):
            return '--'
        elif any(keyword in pattern.lower() for keyword in ['python', 'django']):
            return '#'
        elif any(keyword in pattern.lower() for keyword in ['terraform', 'hcl']):
            return '#'
        else:
            return '#'  # Default to hash comment
    
    def _get_comment_prefix_for_line(self, line: str) -> str:
        """Get appropriate comment prefix based on line content."""
        stripped = line.strip()
        
        # Detect based on line characteristics
        if ':' in stripped and any(c in stripped for c in ['{', '}', '[', ']']):
            return '#'  # YAML/JSON-like
        elif stripped.endswith(';'):
            return '--'  # SQL-like
        elif stripped.startswith(('def ', 'class ', 'import ', 'from ')):
            return '#'  # Python-like
        elif stripped.startswith(('resource ', 'variable ', 'output ')):
            return '#'  # Terraform-like
        else:
            return '#'  # Default
    
    async def _update_file_content(
        self, 
        github_client, 
        repo_owner: str, 
        repo_name: str, 
        file_path: str, 
        new_content: str
    ):
        """Update file content using GitHub API."""
        try:
            # This would integrate with the GitHub MCP client
            # For now, log the operation
            logger.info(f"Would update file {file_path} with {len(new_content)} characters")
            
            # In a real implementation, this would call:
            # await github_client.update_file_contents(repo_owner, repo_name, file_path, new_content)
            
        except Exception as e:
            logger.error(f"Failed to update file {file_path}: {e}")
            raise
    
    async def _process_infrastructure_rules(self, file_path: str, content: str, 
                                          classification: ClassificationResult,
                                          database_name: str) -> List[RuleResult]:
        """Process infrastructure-specific rules."""
        # This method can be extended for infrastructure-specific processing
        return []
    
    async def _process_config_rules(self, file_path: str, content: str,
                                   classification: ClassificationResult,
                                   database_name: str) -> List[RuleResult]:
        """Process configuration-specific rules."""
        # This method can be extended for config-specific processing
        return []
    
    async def _process_sql_rules(self, file_path: str, content: str,
                                classification: ClassificationResult,
                                database_name: str) -> List[RuleResult]:
        """Process SQL-specific rules."""
        # This method can be extended for SQL-specific processing
        return []
    
    async def _process_python_rules(self, file_path: str, content: str,
                                   classification: ClassificationResult,
                                   database_name: str) -> List[RuleResult]:
        """Process Python-specific rules."""
        # This method can be extended for Python-specific processing
        return []
    
    async def _process_shell_rules(self, file_path: str, content: str,
                                   classification: ClassificationResult,
                                   database_name: str) -> List[RuleResult]:
        """Process shell script-specific rules."""
        # This method can be extended for shell-specific processing
        return []
    
    async def _process_documentation_rules(self, file_path: str, content: str,
                                          classification: ClassificationResult,
                                          database_name: str) -> List[RuleResult]:
        """Process documentation-specific rules."""
        # This method can be extended for documentation-specific processing
        return []

def create_contextual_rules_engine() -> ContextualRulesEngine:
    """Factory function to create a configured contextual rules engine."""
    return ContextualRulesEngine() 