"""
Pattern Discovery System for Database Decommissioning.

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
    """Pattern discovery engine for database references."""
    
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

    def _search_content_for_patterns(self, content: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search content for database patterns."""
        matches = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                try:
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append({
                            "pattern": pattern,
                            "line_number": line_num,
                            "line_content": line.strip(),
                            "match_confidence": 0.8  # Base confidence
                        })
                except re.error:
                    # Skip invalid regex patterns
                    continue
        
        return matches

    async def analyze_repository_structure(
        self, 
        repomix_client, 
        repo_url: str, 
        repo_owner: str, 
        repo_name: str
    ) -> Dict[str, Any]:
        """Analyze repository structure using Repomix."""
        try:
            logger.info(f"📥 Downloading repository content via Repomix: {repo_owner}/{repo_name}")
            
            # Pack repository using Repomix
            pack_result = await repomix_client.pack_remote_repository(
                repo_url,  # First positional argument
                include_patterns=["**/*.{py,js,ts,yaml,yml,json,sql,md,txt,ini,conf,env}"],
                exclude_patterns=["node_modules/**", "*.log", "*.tmp"]
            )
            
            if not pack_result or 'output_id' not in pack_result:
                logger.warning(f"Failed to pack repository {repo_url}")
                return {"files": [], "structure": {}, "total_size": 0}
            
            output_id = pack_result['output_id']
            
            # Read the packed repository content
            content_result = await repomix_client.read_repomix_output(output_id=output_id)
            
            if not content_result:
                logger.warning(f"Failed to read repository content for {repo_url}")
                return {"files": [], "structure": {}, "total_size": 0}
            
            # Parse repository content
            repository_content = content_result.get('content', '')
            files = self._parse_repomix_content(repository_content)
            
            structure_analysis = {
                "total_files": len(files),
                "file_types": self._analyze_file_types(files),
                "directory_structure": self._analyze_directory_structure(files),
                "estimated_size": len(repository_content)
            }
            
            logger.info(f"✅ Repository analysis complete: {len(files)} files found")
            
            return {
                "files": files,
                "structure": structure_analysis,
                "total_size": len(repository_content),
                "output_id": output_id
            }
            
        except Exception as e:
            logger.error(f"Repository structure analysis failed for {repo_url}: {e}")
            return {"files": [], "structure": {}, "total_size": 0, "error": str(e)}

    def _parse_repomix_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse Repomix output to extract individual files."""
        files = []
        
        # Repomix formats files with XML-like markers
        file_pattern = r'<file path="([^"]+)">\s*\n(.*?)\n</file>'
        matches = re.findall(file_pattern, content, re.DOTALL)
        
        for file_path, file_content in matches:
            files.append({
                "path": file_path,
                "content": file_content,
                "size": len(file_content),
                "type": self._get_file_type(file_path)
            })
        
        return files

    def _get_file_type(self, file_path: str) -> str:
        """Get file type from path."""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.sql': 'sql',
            '.md': 'markdown',
            '.txt': 'text',
            '.ini': 'config',
            '.conf': 'config',
            '.env': 'environment'
        }
        
        return type_mapping.get(extension, 'unknown')

    def _analyze_file_types(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of file types."""
        type_counts = {}
        for file_info in files:
            file_type = file_info.get('type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        return type_counts

    def _analyze_directory_structure(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze directory structure of repository."""
        directories = set()
        depth_analysis = {}
        
        for file_info in files:
            file_path = file_info.get('path', '')
            path_parts = Path(file_path).parts
            
            # Track directories
            for i in range(len(path_parts) - 1):  # Exclude the file itself
                dir_path = '/'.join(path_parts[:i+1])
                directories.add(dir_path)
            
            # Analyze depth
            depth = len(path_parts) - 1
            depth_analysis[depth] = depth_analysis.get(depth, 0) + 1
        
        return {
            "total_directories": len(directories),
            "max_depth": max(depth_analysis.keys()) if depth_analysis else 0,
            "depth_distribution": depth_analysis
        }

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
        Discover database patterns in repository using intelligent analysis.
        """
        try:
            logger.info(f"🔍 Starting pattern discovery for '{database_name}' in {repo_owner}/{repo_name}")
            
            # Step 1: Analyze repository structure
            repo_analysis = await self.analyze_repository_structure(
                repomix_client, repo_url, repo_owner, repo_name
            )
            
            if not repo_analysis.get("files"):
                logger.info(f"ℹ️ No files found in repository {repo_owner}/{repo_name}")
                return {
                    "total_files": 0,
                    "matched_files": [],
                    "files_by_type": {},
                    "confidence_distribution": {},
                    "repository_analysis": repo_analysis
                }
            
            # Step 2: Compile search patterns for this database
            database_patterns = self._compile_database_patterns(database_name)
            
            # Step 3: Search each file for database patterns
            matched_files = []
            files_by_type = {}
            confidence_scores = []
            
            for file_info in repo_analysis["files"]:
                file_path = file_info["path"]
                file_content = file_info["content"]
                
                # Classify file type using the source type classifier
                classification = self.classifier.classify_file(file_path, file_content)
                source_type = classification.source_type
                
                # Get relevant patterns for this source type
                relevant_patterns = database_patterns.get(source_type, [])
                if not relevant_patterns and source_type != SourceType.UNKNOWN:
                    # Fallback to general patterns
                    relevant_patterns = database_patterns.get(SourceType.UNKNOWN, [])
                
                # Search for patterns in file content
                pattern_matches = self._search_content_for_patterns(file_content, relevant_patterns)
                
                if pattern_matches:
                    # Calculate overall confidence for this file
                    file_confidence = min(
                        classification.confidence + 
                        (len(pattern_matches) * 0.1),  # Boost for multiple matches
                        1.0
                    )
                    
                    file_result = {
                        "path": file_path,
                        "content": file_content,
                        "source_type": source_type.value,
                        "classification": classification,
                        "pattern_matches": pattern_matches,
                        "confidence": file_confidence,
                        "match_count": len(pattern_matches)
                    }
                    
                    matched_files.append(file_result)
                    confidence_scores.append(file_confidence)
                    
                    # Group by source type
                    type_key = source_type.value
                    if type_key not in files_by_type:
                        files_by_type[type_key] = []
                    files_by_type[type_key].append(file_result)
            
            # Step 4: Calculate overall discovery metrics
            discovery_result = {
                "database_name": database_name,
                "repository": f"{repo_owner}/{repo_name}",
                "total_files": len(repo_analysis["files"]),
                "matched_files": len(matched_files),
                "files": matched_files,
                "files_by_type": files_by_type,
                "confidence_distribution": {
                    "high_confidence": len([s for s in confidence_scores if s >= 0.8]),
                    "medium_confidence": len([s for s in confidence_scores if 0.5 <= s < 0.8]),
                    "low_confidence": len([s for s in confidence_scores if s < 0.5]),
                    "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
                },
                "discovery_strategy": "intelligent_pattern_matching",
                "repository_analysis": repo_analysis,
                "pattern_types_used": list(database_patterns.keys())
            }
            
            logger.info(f"✅ Pattern discovery complete: {len(matched_files)} files matched with "
                       f"average confidence {discovery_result['confidence_distribution']['average_confidence']:.2f}")
            
            return discovery_result
            
        except Exception as e:
            logger.error(f"Pattern discovery failed for {repo_owner}/{repo_name}: {e}")
            return {
                "total_files": 0,
                "matched_files": [],
                "files_by_type": {},
                "confidence_distribution": {},
                "error": str(e),
                "repository_analysis": {"files": [], "structure": {}, "total_size": 0}
            }

async def discover_patterns_step(
    context, 
    step, 
    database_name: str, 
    repo_owner: str, 
    repo_name: str
) -> Dict[str, Any]:
    """
    Pattern discovery step that replaces the hardcoded discover_helm_patterns_step.
    
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
        
        # Run pattern discovery
        discovery_result = await discovery_engine.discover_patterns_in_repository(
            repomix_client=repomix_client,
            github_client=github_client,
            repo_url=repo_url,
            database_name=database_name,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        
        # Store result in context for downstream steps
        context.set_shared_value("discovery", discovery_result)
        
        # Log summary
        logger.info(f"Pattern discovery completed for {database_name}: "
                   f"{discovery_result['total_files']} files found, "
                   f"{discovery_result.get('matched_files', 0)} matches")
        
        return discovery_result
        
    except Exception as e:
        logger.error(f"Pattern discovery step failed for {database_name}: {e}")
        return {
            "database_name": database_name,
            "total_files": 0,
            "matched_files": 0,
            "files": [],
            "error": str(e)
        } 