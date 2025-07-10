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
            
            # Step 3: Validate and categorize matches (using Repomix output_id)
            output_id = repo_structure.get("pack_result", {}).get("output_id")
            if output_id:
                validated_matches = await self._validate_pattern_matches_repomix(
                    repomix_client, output_id, pattern_matches, database_name
                )
            else:
                # Fallback: basic validation without file content access
                validated_matches = []
                seen_files = set()
                for source_type, matches in pattern_matches.items():
                    for match in matches:
                        if match['path'] not in seen_files:
                            seen_files.add(match['path'])
                            validated_matches.append(match)
            
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
        """Analyze repository structure using repomix (minimal GitHub API usage)."""
        try:
            # Pack repository for analysis - this is the main operation
            pack_result = await repomix_client.pack_remote_repository(repo_url)
            
            # Get basic repository info from GitHub (single API call, not search)
            try:
                repo_info = await github_client.analyze_repo_structure(repo_url)
            except Exception as e:
                logger.debug(f"GitHub repo structure call failed: {e}")
                repo_info = {"error": "github_api_failed"}
            
            return {
                "pack_result": pack_result,
                "repo_info": repo_info,
                "languages": repo_info.get("languages", {}),
                "file_count": repo_info.get("file_count", 0),
                "repomix_success": pack_result is not None
            }
            
        except Exception as e:
            logger.warning(f"Repository structure analysis failed: {e}")
            return {"error": str(e), "repomix_success": False}
    
    async def _search_database_patterns(
        self, 
        repomix_client, 
        github_client, 
        repo_url: str, 
        repo_owner: str, 
        repo_name: str, 
        database_name: str
    ) -> Dict[SourceType, List[Dict[str, Any]]]:
        """Search for database patterns using Repomix only - NO GitHub API calls."""
        pattern_matches = {source_type: [] for source_type in SourceType}
        
        # Step 1: Pack the repository once using Repomix
        logger.info(f"🚀 Packing repository {repo_url} with Repomix...")
        try:
            pack_result = await repomix_client.pack_remote_repository(repo_url)
            output_id = pack_result.get('output_id') if pack_result else None
            
            if not output_id:
                logger.error("Failed to pack repository with Repomix")
                return pattern_matches
                
            logger.info(f"✅ Repository packed successfully: {output_id}")
            
        except Exception as e:
            logger.error(f"Repomix packing failed: {e}")
            return pattern_matches
        
        # Step 2: Search patterns in packed content using grep
        await self._search_direct_database_references_repomix(
            repomix_client, output_id, database_name, pattern_matches
        )
        
        # Step 3: Search file-type specific patterns using grep on packed content
        await self._search_by_file_types_repomix(
            repomix_client, output_id, database_name, pattern_matches
        )
        
        # Step 4: Search content-based patterns using grep
        await self._search_content_patterns_repomix(
            repomix_client, output_id, database_name, pattern_matches
        )
        
        logger.info(f"🔍 Pattern search completed using Repomix only")
        return pattern_matches
    
    async def _search_direct_database_references_repomix(
        self, 
        repomix_client, 
        output_id: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for direct database name references using Repomix grep."""
        try:
            # Search for exact database name with context
            search_patterns = [
                database_name,
                f'"{database_name}"',
                f"'{database_name}'",
                f":{database_name}",
                f"={database_name}",
            ]
            
            for pattern in search_patterns:
                try:
                    result = await repomix_client.grep_repomix_output(
                        output_id=output_id,
                        pattern=re.escape(pattern),
                        context_lines=2,
                        ignore_case=True
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
                                "confidence": classification.confidence,
                                "search_method": "repomix_direct"
                            }
                            
                            pattern_matches[classification.source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"Direct pattern search failed for '{pattern}': {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Direct database reference search failed: {e}")

    async def _search_by_file_types_repomix(
        self, 
        repomix_client, 
        output_id: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for database references by specific file types using Repomix grep."""
        
        # Define file extension patterns for different source types
        file_type_patterns = {
            SourceType.INFRASTRUCTURE: [
                (r"\.tf$", "Terraform files"),
                (r"values\.ya?ml$", "Helm values"),
                (r"Chart\.ya?ml$", "Helm charts"),
                (r"docker-compose\.ya?ml$", "Docker compose"),
                (r"Dockerfile", "Docker files"),
            ],
            SourceType.CONFIG: [
                (r"\.ya?ml$", "YAML config"),
                (r"\.json$", "JSON config"),
                (r"\.env", "Environment files"),
                (r"config\.", "Config files"),
                (r"\.ini$", "INI files"),
                (r"\.toml$", "TOML files"),
            ],
            SourceType.SQL: [
                (r"\.sql$", "SQL files"),
                (r"migration", "Migration files"),
                (r"schema", "Schema files"),
            ],
            SourceType.PYTHON: [
                (r"\.py$", "Python files"),
                (r"models\.py$", "Django/Flask models"),
                (r"settings\.py$", "Django settings"),
                (r"requirements\.txt$", "Python deps"),
            ],
            # Note: JavaScript files would be classified as UNKNOWN since JS is not in SourceType enum
        }
        
        for source_type, file_patterns in file_type_patterns.items():
            for file_regex, description in file_patterns:
                try:
                    # Use grep to find database name in files matching the pattern
                    # Combine file path filtering with content search
                    grep_pattern = f"({re.escape(database_name)})"
                    
                    result = await repomix_client.grep_repomix_output(
                        output_id=output_id,
                        pattern=grep_pattern,
                        context_lines=1,
                        ignore_case=True
                    )
                    
                    if result and result.get('matches'):
                        for match in result['matches']:
                            file_path = match.get('file', '')
                            
                            # Filter by file type using regex
                            if re.search(file_regex, file_path, re.IGNORECASE):
                                match_info = {
                                    "path": file_path,
                                    "type": source_type.value,
                                    "pattern": f"{description}: {grep_pattern}",
                                    "line_number": match.get('line_number', 0),
                                    "context": match.get('context', ''),
                                    "confidence": 0.8,  # High confidence for file type + content match
                                    "search_method": "repomix_filetype"
                                }
                                
                                pattern_matches[source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"File type search failed for '{file_regex}': {e}")
                    continue

    async def _search_content_patterns_repomix(
        self, 
        repomix_client, 
        output_id: str, 
        database_name: str, 
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]]
    ):
        """Search for content-specific patterns using Repomix grep."""
        content_patterns = {
            SourceType.INFRASTRUCTURE: [
                (rf'resource\s+["\'][^"\']*{re.escape(database_name)}[^"\']*["\']', "Terraform resource"),
                (rf'name:\s*[\'\"]{re.escape(database_name)}[\'\"]', "YAML name field"),
                (rf'database:\s*[\'\"]{re.escape(database_name)}[\'\"]', "Database config"),
            ],
            SourceType.CONFIG: [
                (rf'{re.escape(database_name)}[_-]?(host|port|url|connection)', "DB connection config"),
                (rf'(host|port|url|connection)[_-]?{re.escape(database_name)}', "Connection prefix"),
                (rf'{re.escape(database_name)}_DATABASE_URL', "Database URL env var"),
            ],
            SourceType.SQL: [
                (rf'CREATE\s+DATABASE\s+{re.escape(database_name)}', "CREATE DATABASE"),
                (rf'USE\s+{re.escape(database_name)}', "USE statement"),
                (rf'FROM\s+{re.escape(database_name)}\.', "FROM table"),
            ],
            SourceType.PYTHON: [
                (rf'class\s+\w*{re.escape(database_name)}\w*\(', "Python class"),
                (rf'{re.escape(database_name)}[_-]?(model|connection|engine)', "DB model/connection"),
                (rf'DATABASES\s*=.*{re.escape(database_name)}', "Django DATABASES"),
            ]
        }
        
        for source_type, patterns in content_patterns.items():
            for pattern, description in patterns:
                try:
                    result = await repomix_client.grep_repomix_output(
                        output_id=output_id,
                        pattern=pattern,
                        context_lines=1,
                        ignore_case=True
                    )
                    
                    if result and result.get('matches'):
                        for match in result['matches']:
                            file_path = match.get('file', '')
                            
                            # Re-classify file for accuracy
                            classification = self.classifier.classify_file(file_path)
                            
                            match_info = {
                                "path": file_path,
                                "type": classification.source_type.value,
                                "pattern": f"{description}: {pattern}",
                                "line_number": match.get('line_number', 0),
                                "context": match.get('context', ''),
                                "confidence": 0.7,  # Medium confidence for regex patterns
                                "search_method": "repomix_content"
                            }
                            
                            pattern_matches[classification.source_type].append(match_info)
                            
                except Exception as e:
                    logger.debug(f"Content pattern search failed for '{pattern}': {e}")
                    continue
    
    async def _validate_pattern_matches_repomix(
        self, 
        repomix_client,
        output_id: str,
        pattern_matches: Dict[SourceType, List[Dict[str, Any]]], 
        database_name: str
    ) -> List[Dict[str, Any]]:
        """Validate and deduplicate pattern matches from Repomix results."""
        validated_matches = []
        seen_files = set()
        
        for source_type, matches in pattern_matches.items():
            for match in matches:
                file_path = match['path']
                
                # Skip duplicates (same file found by multiple search methods)
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                
                # Since we found it via grep, we know the database name appears in the file
                # Just re-classify for better accuracy and add validation info
                classification = self.classifier.classify_file(file_path)
                
                validated_match = {
                    "path": file_path,
                    "type": classification.source_type.value,
                    "frameworks": classification.detected_frameworks,
                    "confidence": max(classification.confidence, match.get('confidence', 0.5)),
                    "rule_files": classification.rule_files,
                    "patterns_matched": match.get('pattern', ''),
                    "line_number": match.get('line_number', 0),
                    "context": match.get('context', ''),
                    "search_method": match.get('search_method', 'repomix'),
                    "validation": "repomix_confirmed"  # Found via content search, so confirmed
                }
                
                validated_matches.append(validated_match)
        
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