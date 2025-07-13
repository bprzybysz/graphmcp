"""
Demo Configuration for GraphMCP Workflows.

This module provides configuration management for demo execution modes,
supporting both mock (cached) and real (live service) execution modes.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class DemoConfig:
    """
    Configuration for demo execution.
    
    Supports environment variable loading and mode switching between
    mock (cached data) and real (live services) execution.
    
    Args:
        mode: Execution mode ('mock' or 'real')
        target_repo: Target repository URL for analysis
        target_database: Target database name for decommissioning
        cache_dir: Directory for cached data storage
        cache_ttl: Cache time-to-live in seconds
        log_level: Logging level for demo execution
        quick_mode: Enable quick mode for faster execution
    """
    mode: str
    target_repo: str
    target_database: str
    cache_dir: str = "tests/data"
    cache_ttl: int = 3600  # 1 hour
    log_level: str = "INFO"
    quick_mode: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.mode not in ("mock", "real"):
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'mock' or 'real'")
        
        # Ensure cache directory exists
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> 'DemoConfig':
        """
        Load configuration from environment variables.
        
        Environment variables:
            DEMO_MODE: Execution mode (mock/real) - default: mock
            TARGET_REPO: Target repository URL - default: postgres sample repo
            TARGET_DATABASE: Target database name - default: postgres_air
            CACHE_DIR: Cache directory - default: tests/data
            CACHE_TTL: Cache TTL in seconds - default: 3600
            LOG_LEVEL: Logging level - default: INFO
            QUICK_MODE: Quick mode flag - default: false
            
        Returns:
            DemoConfig instance with environment values
        """
        return cls(
            mode=os.getenv('DEMO_MODE', 'real'),
            target_repo=os.getenv(
                'TARGET_REPO', 
                'https://github.com/bprzybysz/postgres-sample-dbs'
            ),
            target_database=os.getenv('TARGET_DATABASE', 'postgres_air'),
            cache_dir=os.getenv('CACHE_DIR', 'tests/data'),
            cache_ttl=int(os.getenv('CACHE_TTL', '3600')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            quick_mode=os.getenv('QUICK_MODE', 'false').lower() in ('true', '1', 'yes'),
        )

    @classmethod
    def for_mock_mode(cls, database_name: str = 'postgres_air') -> 'DemoConfig':
        """
        Create configuration for mock mode execution.
        
        Args:
            database_name: Database name to use
            
        Returns:
            DemoConfig configured for mock mode
        """
        return cls(
            mode='mock',
            target_repo='https://github.com/bprzybysz/postgres-sample-dbs',
            target_database=database_name,
            cache_dir='tests/data',
            quick_mode=True,
        )

    @classmethod  
    def for_real_mode(cls, database_name: str = 'postgres_air', repo_url: Optional[str] = None) -> 'DemoConfig':
        """
        Create configuration for real mode execution.
        
        Args:
            database_name: Database name to use
            repo_url: Repository URL (uses default if None)
            
        Returns:
            DemoConfig configured for real mode
        """
        return cls(
            mode='real',
            target_repo=repo_url or 'https://github.com/bprzybysz/postgres-sample-dbs',
            target_database=database_name,
            cache_dir='tests/data',
            quick_mode=False,
        )

    @property
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mode == 'mock'

    @property
    def is_real_mode(self) -> bool:
        """Check if running in real mode."""
        return self.mode == 'real'

    @property
    def cache_file_prefix(self) -> str:
        """Get cache file prefix for this configuration."""
        return f"{self.target_database}_{self.mode}"

    def get_repo_cache_path(self) -> Path:
        """Get path for repository pack cache file."""
        return Path(self.cache_dir) / f"{self.cache_file_prefix}_repo_pack.xml"

    def get_patterns_cache_path(self) -> Path:
        """Get path for pattern discovery cache file."""
        return Path(self.cache_dir) / f"{self.cache_file_prefix}_patterns.json"

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'mode': self.mode,
            'target_repo': self.target_repo,
            'target_database': self.target_database,
            'cache_dir': self.cache_dir,
            'cache_ttl': self.cache_ttl,
            'log_level': self.log_level,
            'quick_mode': self.quick_mode,
        }