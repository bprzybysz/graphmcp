"""
Enhanced Pattern Discovery System for Database Decommissioning.

This module provides intelligent pattern discovery to replace the hardcoded
file discovery in the discover_helm_patterns_step function.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from concrete.source_type_classifier import SourceTypeClassifier, SourceType, get_database_search_patterns

logger = logging.getLogger(__name__)

class PatternDiscoveryEngine:
    """Enhanced pattern discovery engine for database references."""
    
    def __init__(self):
        self.classifier = SourceTypeClassifier()
        self.database_patterns = {}
        
    def _compile_database_patterns(self, database_name: str) -> Dict[SourceType, List[str]]:
        """Compile regex patterns for database name detection."""
        patterns = {}
        
        for source_type in SourceType:
            if source_type == SourceType.UNKNOWN:
                continue
            
            base_patterns = get_database_search_patterns(source_type, database_name)
            
            # Compile regex patterns with various case combinations
            regex_patterns = []
            for pattern in base_patterns:
                # Exact match patterns
                regex_patterns.extend([
                    rf'\b{re.escape(pattern)}\b',
                    rf'"{re.escape(pattern)}"',
                    rf"'{re.escape(pattern)}'",
                    rf':{re.escape(pattern)}(?:\s|$)',
                    rf'={re.escape(pattern)}(?:\s|$)',
                ])
            
            patterns[source_type] = regex_patterns
        
        return patterns
    
    async def discover_patterns_in_repository(
        self, 
        repomix_client, 
        github_client, 
        repo_url: str, 
        database_name: str,
        repo_owner: str,
        repo_name: str
    ) -> Dict[str, Any]:
        """
        Discover database patterns in a repository using multiple search strategies.
        
        This replaces the hardcoded discover_helm_patterns_step function.
        """
        try:
            logger.info(f"Starting pattern discovery for database '{database_name}' in {repo_url}")
            
            # Compile database-specific patterns
            self.database_patterns = self._compile_database_patterns(database_name)
            
            # Step 1: Get repository structure and classify files
            repo_structure = await self._analyze_repository_structure(
                repomix_client, github_client, repo_url, repo_owner, repo_name
            )
            
            # Step 2: Search for database patterns across different source types
            pattern_matches = await self._search_database_patterns(
                repomix_client, github_client, repo_url, repo_owner, repo_name, database_name
            )
            
            # Step 3: Validate and categorize matches
            validated_matches = await self._validate_pattern_matches(
                github_client, repo_owner, repo_name, pattern_matches, database_name
            )
            
            # Step 4: Generate discovery result
            discovery_result = self._compile_discovery_result(
                validated_matches, database_name, repo_structure
            )
            
            logger.info(f"Pattern discovery completed: {discovery_result['total_files']} files found")
            return discovery_result
            
        except Exception as e:
            logger.error(f"Pattern discovery failed for {repo_url}: {e}")
            return {
                "error": f"Pattern discovery failed: {e}",
                "total_files": 0,
                "matching_files": [],
                "database_name": database_name,
                "patterns_used": []
            }
    
    async def _analyze_repository_structure(
        self, 
        repomix_client, 
        github_client, 
        repo_url: str, 
        repo_owner: str, 
        repo_name: str
    ) -> Dict[str, Any]:
        """Analyze repository structure using repomix and GitHub APIs."""
        try:
            # Pack repository for analysis
            pack_result = await repomix_client.pack_remote_repository(repo_url)
            
            # Get repository structure from GitHub
            repo_info = await github_client.analyze_repo_structure(repo_url)
            
            return {
                "pack_result": pack_result,
                "repo_info": repo_info,
                "languages": repo_info.get("languages", {}),
                "file_count": repo_info.get("file_count", 0)
            }
            
        except Exception as e:
            logger.warning(f"Repository structure analysis failed: {e}")
            return {"error": str(e)}
    
    async def _search_database_patterns(
        self, 
        repomix_client, 
        github_client, 
        repo_url: str, 
        repo_owner: str, 
        repo_name: str, 
        database_name: str
    ) -> Dict[SourceType, List[Dict[str, Any]]]:
        """Search for database patterns using multiple search strategies."""
        pattern_matches = {source_type: [] for source_type in SourceType}
        
        # Strategy 1: Direct database name search
        await self._search_direct_database_references(
            repomix_client, repo_url, database_name, pattern_matches
        )
        
        # Strategy 2: File-type specific searches
        await self._search_by_file_types(
            github_client, repo_owner, repo_name, database_name, pattern_matches
        )
        
        # Strategy 3: Content-based pattern matching
        await self._search_content_patterns(
            repomix_client, repo_url, database_name, pattern_matches
        )
        
        return pattern_matches
    
    async def _search_direct_database_references(
        self, 
        repomix_client, 
        repo_url: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for direct database name references."""
        try:
            # Search for exact database name
            search_patterns = [
                database_name,
                database_name.upper(),
                database_name.lower(),
                f'"{database_name}"',
                f"'{database_name}'",
            ]
            
            for pattern in search_patterns:
                try:
                    result = await repomix_client.grep_repomix_output(
                        repo_url, pattern, context_lines=2, ignore_case=True
                    )
                    
                    if result and result.get('matches'):
                        for match in result['matches']:
                            file_path = match.get('file', '')
                            
                            # Classify file and add to appropriate source type
                            classification = self.classifier.classify_file(file_path)
                            
                            match_info = {
                                "path": file_path,
                                "type": classification.source_type.value,
                                "pattern": pattern,
                                "line_number": match.get('line_number', 0),
                                "context": match.get('context', ''),
                                "confidence": classification.confidence
                            }
                            
                            pattern_matches[classification.source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"Pattern search failed for '{pattern}': {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Direct database reference search failed: {e}")
    
    async def _search_by_file_types(
        self, 
        github_client, 
        repo_owner: str, 
        repo_name: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for database references by specific file types."""
        file_type_searches = {
            SourceType.INFRASTRUCTURE: [
                f"filename:*.tf {database_name}",
                f"filename:values.yaml {database_name}",
                f"filename:Chart.yaml {database_name}",
                f"filename:docker-compose.yml {database_name}",
            ],
            SourceType.CONFIG: [
                f"filename:*.yaml {database_name}",
                f"filename:*.json {database_name}",
                f"filename:.env {database_name}",
                f"filename:config.* {database_name}",
            ],
            SourceType.SQL: [
                f"filename:*.sql {database_name}",
                f"path:migrations {database_name}",
                f"path:schemas {database_name}",
            ],
            SourceType.PYTHON: [
                f"filename:*.py {database_name}",
                f"filename:models.py {database_name}",
                f"filename:settings.py {database_name}",
            ]
        }
        
        for source_type, queries in file_type_searches.items():
            for query in queries:
                try:
                    search_query = f"repo:{repo_owner}/{repo_name} {query}"
                    result = await github_client.search_code(search_query, per_page=50)
                    
                    if result and result.get('items'):
                        for item in result['items']:
                            match_info = {
                                "path": item.get('path', ''),
                                "type": source_type.value,
                                "pattern": query,
                                "score": item.get('score', 0),
                                "url": item.get('html_url', ''),
                                "confidence": 0.8  # High confidence for GitHub search results
                            }
                            
                            pattern_matches[source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"GitHub file type search failed for '{query}': {e}")
                    continue
    
    async def _search_content_patterns(
        self, 
        repomix_client, 
        repo_url: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for content-specific patterns."""
        content_patterns = {
            SourceType.INFRASTRUCTURE: [
                rf'resource\s+\"[^\"]*{database_name}[^\"]*\"',
                rf'name:\s*[\'\"]{database_name}[\'\"]',
                rf'database:\s*[\'\"]{database_name}[\'\"]',
            ],
            SourceType.CONFIG: [
                rf'{database_name}[_-]?(host|port|url|connection)',
                rf'(host|port|url|connection)[_-]?{database_name}',
                rf'{database_name}_DATABASE_URL',
            ],
            SourceType.SQL: [
                rf'CREATE\s+DATABASE\s+{database_name}',
                rf'USE\s+{database_name}',
                rf'FROM\s+{database_name}\.',
            ],
            SourceType.PYTHON: [
                rf'class\s+\w*{database_name}\w*\(',
                rf'{database_name}[_-]?(model|connection|engine)',
                rf'DATABASES\s*=.*{database_name}',
            ]
        }
        
        for source_type, patterns in content_patterns.items():
            for pattern in patterns:
                try:
                    result = await repomix_client.grep_repomix_output(
                        repo_url, pattern, context_lines=1, ignore_case=True
                    )
                    
                    if result and result.get('matches'):
                        for match in result['matches']:
                            match_info = {
                                "path": match.get('file', ''),
                                "type": source_type.value,
                                "pattern": pattern,
                                "line_number": match.get('line_number', 0),
                                "context": match.get('context', ''),
                                "confidence": 0.7  # Medium confidence for regex patterns
                            }
                            
                            pattern_matches[source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"Content pattern search failed for '{pattern}': {e}")
                    continue
    
    async def _validate_pattern_matches(
        self, 
        github_client, 
        repo_owner: str, 
        repo_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]], 
        database_name: str
    ) -> List[Dict[str, Any]]:
        """Validate pattern matches by examining file content."""
        validated_matches = []
        seen_files = set()
        
        for source_type, matches in pattern_matches.items():
            for match in matches:
                file_path = match['path']
                
                # Skip duplicates
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                
                try:
                    # Get file content for validation
                    file_content = await github_client.get_file_contents(
                        repo_owner, repo_name, file_path
                    )
                    
                    # Validate that database name actually appears in content
                    if self._validate_database_reference(file_content, database_name):
                        # Re-classify file with content for better accuracy
                        classification = self.classifier.classify_file(file_path, file_content)
                        
                        validated_match = {
                            "path": file_path,
                            "type": classification.source_type.value,
                            "frameworks": classification.detected_frameworks,
                            "confidence": classification.confidence,
                            "rule_files": classification.rule_files,
                            "patterns_matched": match.get('pattern', ''),
                            "line_number": match.get('line_number', 0),
                            "validation": "confirmed"
                        }
                        
                        validated_matches.append(validated_match)
                        
                except Exception as e:
                    logger.debug(f"File validation failed for {file_path}: {e}")
                    # Include unvalidated match with lower confidence
                    unvalidated_match = match.copy()
                    unvalidated_match['confidence'] = 0.3
                    unvalidated_match['validation'] = "unvalidated"
                    validated_matches.append(unvalidated_match)
        
        return validated_matches
    
    def _validate_database_reference(self, content: str, database_name: str) -> bool:
        """Validate that content actually contains meaningful database references."""
        # Check for various forms of the database name
        patterns = [
            database_name,
            database_name.upper(),
            database_name.lower(),
            database_name.replace('_', '-'),
            database_name.replace('-', '_'),
        ]
        
        content_lower = content.lower()
        
        for pattern in patterns:
            if pattern.lower() in content_lower:
                # Additional validation: check it's not just in a comment
                lines_with_pattern = [
                    line for line in content.split('\n') 
                    if pattern.lower() in line.lower()
                ]
                
                # At least one line should not be a comment
                for line in lines_with_pattern:
                    stripped = line.strip()
                    if not (stripped.startswith('#') or stripped.startswith('//') or 
                           stripped.startswith('/*') or stripped.startswith('*')):
                        return True
        
        return False
    
    def _compile_discovery_result(
        self, 
        validated_matches: List[Dict[str, Any]], 
        database_name: str, 
        repo_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile the final discovery result."""
        # Group matches by source type
        matches_by_type = {}
        for match in validated_matches:
            source_type = match['type']
            if source_type not in matches_by_type:
                matches_by_type[source_type] = []
            matches_by_type[source_type].append(match)
        
        # Calculate statistics
        total_files = len(validated_matches)
        high_confidence_files = len([m for m in validated_matches if m['confidence'] > 0.7])
        
        # Get unique patterns used
        patterns_used = list(set([m.get('patterns_matched', '') for m in validated_matches]))
        
        # Get unique frameworks detected
        frameworks_detected = []
        for match in validated_matches:
            frameworks_detected.extend(match.get('frameworks', []))
        frameworks_detected = list(set(frameworks_detected))
        
        return {
            "total_files": total_files,
            "high_confidence_files": high_confidence_files,
            "matching_files": validated_matches,
            "matches_by_type": matches_by_type,
            "database_name": database_name,
            "patterns_used": patterns_used,
            "frameworks_detected": frameworks_detected,
            "repository_structure": repo_structure,
            "discovery_method": "enhanced_pattern_discovery",
            "validation_status": "validated"
        }

async def enhanced_discover_patterns_step(
    context, 
    step, 
    database_name: str, 
    repo_owner: str, 
    repo_name: str
) -> Dict[str, Any]:
    """
    Enhanced pattern discovery step that replaces the hardcoded discover_helm_patterns_step.
    
    This function provides intelligent pattern discovery instead of returning hardcoded files.
    """
    try:
        # Get required clients
        repomix_client = context._clients.get('ovr_repomix')
        github_client = context._clients.get('ovr_github')
        
        if not repomix_client:
            from clients import RepomixMCPClient
            repomix_client = RepomixMCPClient(context.config.config_path)
            context._clients['ovr_repomix'] = repomix_client
            
        if not github_client:
            from clients import GitHubMCPClient
            github_client = GitHubMCPClient(context.config.config_path)
            context._clients['ovr_github'] = github_client
        
        # Create discovery engine
        discovery_engine = PatternDiscoveryEngine()
        
        # Construct repository URL
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        
        # Run enhanced pattern discovery
        discovery_result = await discovery_engine.discover_patterns_in_repository(
            repomix_client=repomix_client,
            github_client=github_client,
            repo_url=repo_url,
            database_name=database_name,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        
        # Store result in context for downstream steps
        context.set_shared_value("enhanced_discovery", discovery_result)
        
        # Log summary
        logger.info(f"Enhanced pattern discovery completed for {database_name}: "
                   f"{discovery_result['total_files']} files found, "
                   f"{discovery_result.get('high_confidence_files', 0)} high confidence")
        
        return discovery_result
        
    except Exception as e:
        logger.error(f"Enhanced pattern discovery failed: {e}")
        return {
            "error": f"Enhanced pattern discovery failed: {e}",
            "total_files": 0,
            "matching_files": [],
            "database_name": database_name,
            "patterns_used": [],
            "discovery_method": "enhanced_pattern_discovery",
            "validation_status": "failed"
        } 