"""
Cache Management for GraphMCP Demo.

This module provides caching functionality for repository pack data and
pattern discovery results to enable fast iteration and mock mode execution.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from concrete.performance_optimization import AsyncCache
from .config import DemoConfig

logger = logging.getLogger(__name__)


class DemoCache:
    """
    Cache manager for demo workflow data.
    
    Provides caching for repository pack data and pattern discovery results
    to enable fast iteration in mock mode.
    
    Args:
        config: Demo configuration
    """
    
    def __init__(self, config: DemoConfig):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AsyncCache for performance optimization
        self.async_cache = AsyncCache(
            strategy="disk",
            cache_dir=str(self.cache_dir),
            ttl_seconds=config.cache_ttl
        )
    
    def _get_cache_key(self, data_type: str) -> str:
        """
        Get cache key for data type.
        
        Args:
            data_type: Type of data ('repo' or 'patterns')
            
        Returns:
            Cache key
        """
        return f"{self.config.target_database}_{data_type}_{self.config.mode}"
    
    def has_repo_cache(self) -> bool:
        """
        Check if repository pack cache exists.
        
        Returns:
            True if cache exists and is valid
        """
        cache_path = self.config.get_repo_cache_path()
        if not cache_path.exists():
            return False
        
        # Check if cache is expired
        if self.config.cache_ttl > 0:
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age > self.config.cache_ttl:
                logger.info(f"Repository cache expired (age: {cache_age:.1f}s)")
                return False
        
        return True
    
    def has_patterns_cache(self) -> bool:
        """
        Check if patterns cache exists.
        
        Returns:
            True if cache exists and is valid
        """
        cache_path = self.config.get_patterns_cache_path()
        if not cache_path.exists():
            return False
        
        # Check if cache is expired
        if self.config.cache_ttl > 0:
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age > self.config.cache_ttl:
                logger.info(f"Patterns cache expired (age: {cache_age:.1f}s)")
                return False
        
        return True
    
    def load_repo_cache(self) -> Optional[str]:
        """
        Load repository pack data from cache.
        
        Returns:
            Cached repository pack data or None if not found
        """
        cache_path = self.config.get_repo_cache_path()
        
        if not self.has_repo_cache():
            logger.warning(f"Repository cache not found or expired: {cache_path}")
            return None
        
        try:
            logger.info(f"Loading repository cache from: {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = f.read()
            
            logger.info(f"Repository cache loaded ({len(data)} characters)")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load repository cache: {e}")
            return None
    
    def save_repo_cache(self, data: str) -> bool:
        """
        Save repository pack data to cache.
        
        Args:
            data: Repository pack data to cache
            
        Returns:
            True if saved successfully
        """
        cache_path = self.config.get_repo_cache_path()
        
        try:
            logger.info(f"Saving repository cache to: {cache_path}")
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(data)
            
            logger.info(f"Repository cache saved ({len(data)} characters)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save repository cache: {e}")
            return False
    
    def load_patterns_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load pattern discovery results from cache.
        
        Returns:
            Cached pattern data or None if not found
        """
        cache_path = self.config.get_patterns_cache_path()
        
        if not self.has_patterns_cache():
            logger.warning(f"Patterns cache not found or expired: {cache_path}")
            return None
        
        try:
            logger.info(f"Loading patterns cache from: {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            patterns_count = len(data.get("patterns", []))
            logger.info(f"Patterns cache loaded ({patterns_count} patterns)")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load patterns cache: {e}")
            return None
    
    def save_patterns_cache(self, data: Dict[str, Any]) -> bool:
        """
        Save pattern discovery results to cache.
        
        Args:
            data: Pattern discovery data to cache
            
        Returns:
            True if saved successfully
        """
        cache_path = self.config.get_patterns_cache_path()
        
        try:
            logger.info(f"Saving patterns cache to: {cache_path}")
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            patterns_count = len(data.get("patterns", []))
            logger.info(f"Patterns cache saved ({patterns_count} patterns)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save patterns cache: {e}")
            return False
    
    def clear_cache(self, cache_type: Optional[str] = None) -> bool:
        """
        Clear cached data.
        
        Args:
            cache_type: Type to clear ('repo', 'patterns', or None for all)
            
        Returns:
            True if cleared successfully
        """
        try:
            if cache_type is None or cache_type == 'repo':
                repo_path = self.config.get_repo_cache_path()
                if repo_path.exists():
                    repo_path.unlink()
                    logger.info(f"Cleared repository cache: {repo_path}")
            
            if cache_type is None or cache_type == 'patterns':
                patterns_path = self.config.get_patterns_cache_path()
                if patterns_path.exists():
                    patterns_path.unlink()
                    logger.info(f"Cleared patterns cache: {patterns_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached data.
        
        Returns:
            Cache information
        """
        repo_path = self.config.get_repo_cache_path()
        patterns_path = self.config.get_patterns_cache_path()
        
        info = {
            "cache_dir": str(self.cache_dir),
            "cache_ttl": self.config.cache_ttl,
            "repo_cache": {
                "exists": repo_path.exists(),
                "path": str(repo_path),
                "size": repo_path.stat().st_size if repo_path.exists() else 0,
                "modified": repo_path.stat().st_mtime if repo_path.exists() else None,
            },
            "patterns_cache": {
                "exists": patterns_path.exists(),
                "path": str(patterns_path),
                "size": patterns_path.stat().st_size if patterns_path.exists() else 0,
                "modified": patterns_path.stat().st_mtime if patterns_path.exists() else None,
            }
        }
        
        return info
    
    async def populate_default_cache(self) -> bool:
        """
        Populate cache with default data for demo purposes.
        
        This creates sample cached data to enable mock mode execution
        even when no real data has been cached yet.
        
        Returns:
            True if populated successfully
        """
        try:
            # Create sample repository pack data
            sample_repo_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<repository url="{self.config.target_repo}">
    <file path="src/config/database.py">
        <content>
# Database configuration
DATABASE_URL = "postgresql://user:pass@localhost/{self.config.target_database}"
        </content>
    </file>
    <file path="sql/queries.sql">
        <content>
-- Sample SQL queries for {self.config.target_database}
SELECT * FROM {self.config.target_database}.users;
        </content>
    </file>
    <file path="docker-compose.yml">
        <content>
version: '3.8'
services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: {self.config.target_database}
        </content>
    </file>
</repository>"""
            
            # Create sample pattern discovery data
            sample_patterns_data = {
                "database": self.config.target_database,
                "patterns": [
                    {
                        "type": "connection_string",
                        "file": "src/config/database.py",
                        "line": 2,
                        "pattern": f"postgresql://user:pass@localhost/{self.config.target_database}",
                        "confidence": 0.95
                    },
                    {
                        "type": "sql_query", 
                        "file": "sql/queries.sql",
                        "line": 2,
                        "pattern": f"SELECT * FROM {self.config.target_database}.users",
                        "confidence": 0.90
                    },
                    {
                        "type": "environment_variable",
                        "file": "docker-compose.yml", 
                        "line": 6,
                        "pattern": f"POSTGRES_DB: {self.config.target_database}",
                        "confidence": 0.85
                    }
                ],
                "total_files_scanned": 3,
                "scan_duration": 1.5,
                "timestamp": time.time(),
            }
            
            # Save the sample data
            repo_saved = self.save_repo_cache(sample_repo_data)
            patterns_saved = self.save_patterns_cache(sample_patterns_data)
            
            if repo_saved and patterns_saved:
                logger.info("Default cache data populated successfully")
                return True
            else:
                logger.error("Failed to populate some cache data")
                return False
                
        except Exception as e:
            logger.error(f"Failed to populate default cache: {e}")
            return False