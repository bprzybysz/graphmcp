"""
Database Decommissioning Pattern Discovery and Processing.

This module contains pattern discovery and file processing functions for the database
decommissioning workflow, including the AgenticFileProcessor for batch processing.
"""

import os
import json
import openai
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Import source type classification
from concrete.source_type_classifier import SourceType, SourceTypeClassifier

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig

# Import data models
from .data_models import FileProcessingResult


class AgenticFileProcessor:
    """
    Processes files in batches using an agentic, category-based approach.
    
    This processor uses OpenAI's API to intelligently process files in batches,
    categorized by source type for more efficient and accurate refactoring.
    """
    
    def __init__(
        self,
        source_classifier: SourceTypeClassifier,
        contextual_rules_engine: Any,
        github_client: Any,
        repo_owner: str,
        repo_name: str
    ):
        """
        Initialize the AgenticFileProcessor.
        
        Args:
            source_classifier: Source type classifier instance
            contextual_rules_engine: Contextual rules engine instance
            github_client: GitHub MCP client instance
            repo_owner: Repository owner name
            repo_name: Repository name
        """
        self.source_classifier = source_classifier
        self.contextual_rules_engine = contextual_rules_engine
        self.github_client = github_client
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.agent = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize structured logger
        config = LoggingConfig.from_env()
        self.logger = get_logger(
            workflow_id=f"agentic_processor_{repo_owner}_{repo_name}",
            config=config
        )
    
    def _build_agent_prompt(
        self,
        batch: List[Dict[str, str]],
        rules: Dict[str, Any],
        source_type: SourceType
    ) -> str:
        """
        Build a detailed prompt for the agent to process a batch of files.
        
        Args:
            batch: List of file dictionaries with path and content
            rules: Applicable rules for the source type
            source_type: Source type being processed
            
        Returns:
            Formatted prompt string for the agent
        """
        database_name = getattr(self.contextual_rules_engine, 'database_name', 'unknown')
        
        prompt = f"""You are an expert code refactoring agent tasked with decommissioning a database named '{database_name}'.
You will be given a batch of files of type '{source_type.value}' and a set of rules to apply.
Your task is to analyze each file and apply the necessary code modifications based on the rules.

**Rules:**
{json.dumps(rules, indent=2)}

**Files to Process:**
"""
        
        for file_info in batch:
            prompt += f"""---

**File Path:** {file_info['file_path']}

**File Content:**
```
{file_info['file_content']}
```
"""
        
        prompt += """---

Please return a JSON object with a key for each file path processed. The value for each key should be an object containing the new file content under the key 'modified_content'.
Example response format:
{
    "path/to/file1.py": {
        "modified_content": "... new content for file1 ..."
    },
    "path/to/file2.js": {
        "modified_content": "... new content for file2 ..."
    }
}
"""
        return prompt
    
    async def _invoke_agent_on_batch(
        self,
        prompt: str,
        batch: List[Dict[str, str]]
    ) -> List[FileProcessingResult]:
        """
        Invoke the OpenAI agent with the prompt and process the response.
        
        Args:
            prompt: Formatted prompt for the agent
            batch: List of file dictionaries being processed
            
        Returns:
            List of FileProcessingResult objects
        """
        try:
            response = await self.agent.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            agent_results = json.loads(response_content)
            
            batch_results = []
            for file_info in batch:
                file_path = file_info['file_path']
                original_content = file_info['file_content']
                
                if file_path in agent_results and 'modified_content' in agent_results[file_path]:
                    modified_content = agent_results[file_path]['modified_content']
                    changes_made = 1 if modified_content != original_content else 0
                    
                    if changes_made > 0:
                        await self.contextual_rules_engine._update_file_content(
                            self.github_client, self.repo_owner, self.repo_name, file_path, modified_content
                        )
                    
                    batch_results.append(FileProcessingResult(
                        file_path=file_path,
                        source_type=self.source_classifier.classify_file(file_path, original_content).source_type,
                        success=True,
                        total_changes=changes_made,
                        rules_applied=[]
                    ))
                else:
                    # Agent did not return modifications for this file
                    batch_results.append(FileProcessingResult(
                        file_path=file_path,
                        source_type=self.source_classifier.classify_file(file_path, original_content).source_type,
                        success=True,
                        total_changes=0,
                        rules_applied=[]
                    ))
            
            return batch_results
            
        except Exception as e:
            self.logger.log_error(f"Error invoking agent or processing response: {e}")
            return [
                FileProcessingResult(
                    file_path=f['file_path'],
                    source_type=self.source_classifier.classify_file(f['file_path'], f.get('file_content', '')).source_type,
                    success=False,
                    total_changes=0,
                    rules_applied=[],
                    error_message=str(e)
                ) for f in batch
            ]
    
    async def process_files(
        self,
        files_to_process: List[Dict[str, str]],
        batch_size: int = 3
    ) -> List[FileProcessingResult]:
        """
        Classify, batch, and process files using an agentic workflow.
        
        Args:
            files_to_process: List of file dictionaries with path and content
            batch_size: Number of files to process in each batch
            
        Returns:
            List of FileProcessingResult objects
        """
        self.logger.log_info(f"Starting agentic processing for {len(files_to_process)} files with batch size {batch_size}")
        
        # 1. Classify and group files by source type
        categorized_files = defaultdict(list)
        for file_info in files_to_process:
            file_path = file_info['file_path']
            
            # Ensure content is available for classification
            if 'file_content' not in file_info or file_info['file_content'] is None:
                self.logger.log_warning(f"Skipping {file_path} due to missing content")
                continue
            
            classification = self.source_classifier.classify_file(file_path, file_info['file_content'])
            categorized_files[classification.source_type].append(file_info)
        
        all_results = []
        
        # 2. Process each category in batches
        for source_type, files in categorized_files.items():
            self.logger.log_info(f"Processing category '{source_type.value}' with {len(files)} files")
            
            # Process files in batches
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                self.logger.log_info(f"Processing batch of {len(batch)} files for category {source_type.value}")
                
                # 1. Get rules for the current source_type
                applicable_rules = self.contextual_rules_engine._get_applicable_rules(source_type, [])
                
                # 2. Construct a prompt for the agent with the batch of files and rules
                prompt = self._build_agent_prompt(batch, applicable_rules, source_type)
                self.logger.log_info(f"Built prompt for batch (category: {source_type.value}), invoking agent...")
                
                # 3. Invoke the agent and process the results
                batch_results = await self._invoke_agent_on_batch(prompt, batch)
                all_results.extend(batch_results)
        
        self.logger.log_info(f"Agentic processing finished. Processed {len(all_results)} files")
        return all_results


async def process_discovered_files_with_rules(
    context: Any,
    discovery_result: Dict[str, Any],
    database_name: str,
    repo_owner: str,
    repo_name: str,
    contextual_rules_engine: Any,
    source_classifier: SourceTypeClassifier,
    logger: Any
) -> Dict[str, Any]:
    """
    Process discovered files with contextual rules.
    
    Args:
        context: WorkflowContext instance
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        repo_owner: Repository owner name
        repo_name: Repository name
        contextual_rules_engine: Contextual rules engine instance
        source_classifier: Source type classifier instance
        logger: Structured logger instance
        
    Returns:
        Dict containing processing results
    """
    try:
        discovered_files = discovery_result.get("files", [])
        
        # --- Dispatcher to switch between processing strategies ---
        # Set this to True to use the new agentic batch processor
        USE_AGENTIC_PROCESSOR = True
        
        if USE_AGENTIC_PROCESSOR:
            logger.log_info("Using AgenticFileProcessor for file processing")
            
            agentic_processor = AgenticFileProcessor(
                source_classifier=source_classifier,
                contextual_rules_engine=contextual_rules_engine,
                github_client=context.clients.get('ovr_github'),
                repo_owner=repo_owner,
                repo_name=repo_name
            )
            
            results = await agentic_processor.process_files(discovered_files)
            files_processed = len(results)
            files_modified = sum(1 for r in results if r.total_changes > 0)
            
        else:
            logger.log_info("Using original sequential processor for file processing")
            
            files_processed = 0
            files_modified = 0
            
            # Process files sequentially
            for file_info in discovered_files:
                file_path = file_info.get("path", "")
                file_content = file_info.get("content", "")
                
                # Classify file
                classification = source_classifier.classify_file(file_path, file_content)
                
                # Process with contextual rules
                processing_result = await contextual_rules_engine.process_file_with_contextual_rules(
                    file_path, file_content, classification, database_name,
                    github_client=context.clients.get('ovr_github'),
                    repo_owner=repo_owner,
                    repo_name=repo_name
                )
                
                files_processed += 1
                if processing_result.total_changes > 0:
                    files_modified += 1
        
        return {
            "files_processed": files_processed,
            "files_modified": files_modified
        }
        
    except Exception as e:
        logger.log_error("Failed to process discovered files with rules", e)
        return {"files_processed": 0, "files_modified": 0}


async def log_pattern_discovery_visual(
    workflow_id: Optional[str],
    discovery_result: Dict[str, Any],
    repo_owner: str,
    repo_name: str,
    logger: Any
) -> None:
    """
    Log pattern discovery results with structured visualization.
    
    Args:
        workflow_id: Unique workflow identifier
        discovery_result: Results from pattern discovery
        repo_owner: Repository owner name
        repo_name: Repository name
        logger: Structured logger instance
    """
    try:
        files_by_type = discovery_result.get("files_by_type", {})
        
        # Create table of discovered files by type
        if files_by_type:
            table_data = []
            for file_type, files in files_by_type.items():
                table_data.append({
                    "file_type": file_type.title(),
                    "count": len(files),
                    "status": "✅"
                })
            
            logger.log_table(
                f"Pattern Discovery Results: {repo_owner}/{repo_name}",
                table_data
            )
            
            # Create file type distribution tree
            distribution_tree = {
                file_type.title(): len(files)
                for file_type, files in files_by_type.items()
            }
            
            logger.log_tree(
                f"File Type Distribution: {repo_owner}/{repo_name}",
                distribution_tree
            )
            
            # Log additional metrics
            total_files = sum(len(files) for files in files_by_type.values())
            logger.log_info(
                f"Pattern Discovery Summary: {len(files_by_type)} file types, {total_files} total files"
            )
            
    except Exception as e:
        logger.log_warning(f"Failed to create visual logs for pattern discovery: {e}")


def categorize_files_by_source_type(
    files: List[Dict[str, Any]],
    source_classifier: SourceTypeClassifier
) -> Dict[SourceType, List[Dict[str, Any]]]:
    """
    Categorize files by their source type for batch processing.
    
    Args:
        files: List of file dictionaries with path and content
        source_classifier: Source type classifier instance
        
    Returns:
        Dict mapping source types to lists of files
    """
    categorized_files = defaultdict(list)
    
    for file_info in files:
        file_path = file_info.get("path", "")
        file_content = file_info.get("content", "")
        
        if file_path and file_content:
            classification = source_classifier.classify_file(file_path, file_content)
            categorized_files[classification.source_type].append(file_info)
    
    return dict(categorized_files)


def calculate_processing_metrics(
    results: List[FileProcessingResult]
) -> Dict[str, Any]:
    """
    Calculate processing metrics from file processing results.
    
    Args:
        results: List of FileProcessingResult objects
        
    Returns:
        Dict containing processing metrics
    """
    total_files = len(results)
    successful_files = sum(1 for r in results if r.success)
    failed_files = total_files - successful_files
    total_changes = sum(r.total_changes for r in results)
    
    # Group by source type
    by_source_type = defaultdict(list)
    for result in results:
        by_source_type[result.source_type].append(result)
    
    source_type_metrics = {}
    for source_type, type_results in by_source_type.items():
        source_type_metrics[source_type.value] = {
            "total_files": len(type_results),
            "successful_files": sum(1 for r in type_results if r.success),
            "total_changes": sum(r.total_changes for r in type_results)
        }
    
    return {
        "total_files": total_files,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "total_changes": total_changes,
        "success_rate": (successful_files / total_files * 100) if total_files > 0 else 0,
        "by_source_type": source_type_metrics
    }


def extract_high_confidence_patterns(
    discovery_result: Dict[str, Any],
    confidence_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """
    Extract high-confidence patterns from discovery results.
    
    Args:
        discovery_result: Results from pattern discovery
        confidence_threshold: Minimum confidence threshold for patterns
        
    Returns:
        List of high-confidence pattern matches
    """
    files = discovery_result.get("files", [])
    high_confidence_files = []
    
    for file_info in files:
        confidence = file_info.get("confidence", 0)
        if confidence >= confidence_threshold:
            high_confidence_files.append(file_info)
    
    return high_confidence_files


def generate_pattern_discovery_summary(
    discovery_result: Dict[str, Any],
    database_name: str
) -> Dict[str, Any]:
    """
    Generate a comprehensive summary of pattern discovery results.
    
    Args:
        discovery_result: Results from pattern discovery
        database_name: Name of the database being decommissioned
        
    Returns:
        Dict containing pattern discovery summary
    """
    files = discovery_result.get("files", [])
    files_by_type = discovery_result.get("files_by_type", {})
    confidence_dist = discovery_result.get("confidence_distribution", {})
    
    total_files = discovery_result.get("total_files", 0)
    matched_files = discovery_result.get("matched_files", 0)
    
    high_confidence_files = extract_high_confidence_patterns(discovery_result)
    
    summary = {
        "database_name": database_name,
        "total_files_scanned": total_files,
        "matched_files": matched_files,
        "match_rate": (matched_files / total_files * 100) if total_files > 0 else 0,
        "high_confidence_matches": len(high_confidence_files),
        "file_types_found": len(files_by_type),
        "confidence_distribution": confidence_dist,
        "files_by_type": {
            file_type: len(files)
            for file_type, files in files_by_type.items()
        }
    }
    
    return summary