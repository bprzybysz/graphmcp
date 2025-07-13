"""
Centralized Parameter Service for Enhanced Database Workflow.

This service:
1. Loads environment variables from .env files
2. Overlays secrets from secrets.json (overwriting env vars if defined)
3. Validates secrets using patterns and logs issues
4. Throws exceptions if required secrets are missing
5. Provides secure access to configuration parameters
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SecretLevel(Enum):
    """Security levels for different types of secrets."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEPRECATED = "deprecated"

@dataclass
class SecretPattern:
    """Pattern definition for validating secrets."""
    name: str
    level: SecretLevel
    pattern: str
    description: str
    example: str

class ParameterService:
    """Centralized service for managing environment variables and secrets."""
    
    def __init__(self, env_file: str = ".env", secrets_file: str = "secrets.json"):
        self.env_file = env_file
        self.secrets_file = secrets_file
        self.parameters: Dict[str, Any] = {}
        self.validation_issues: List[str] = []
        self.secret_patterns = self._initialize_secret_patterns()
        
        # Load configuration
        self._load_environment()
        self._load_secrets()
        self._validate_secrets()
        
        logger.info(f"🔐 ParameterService initialized with {len(self.parameters)} parameters")
        if self.validation_issues:
            logger.warning(f"⚠️ Found {len(self.validation_issues)} validation issues")
            for issue in self.validation_issues:
                logger.warning(f"   - {issue}")
    
    def _initialize_secret_patterns(self) -> List[SecretPattern]:
        """Initialize patterns for validating different types of secrets."""
        return [
            # GitHub tokens
            SecretPattern(
                name="GITHUB_PERSONAL_ACCESS_TOKEN",
                level=SecretLevel.REQUIRED,
                pattern=r"^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$",
                description="GitHub Personal Access Token",
                example="ghp_[36_chars]"
            ),
            SecretPattern(
                name="GITHUB_TOKEN", 
                level=SecretLevel.OPTIONAL,
                pattern=r"^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$",
                description="Alternative GitHub Token",
                example="ghp_[36_chars]"
            ),
            
            # Slack tokens
            SecretPattern(
                name="SLACK_BOT_TOKEN",
                level=SecretLevel.REQUIRED,
                pattern=r"^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]{24}$",
                description="Slack Bot Token",
                example="xoxb-[numbers]-[numbers]-[24_chars]"
            ),
            SecretPattern(
                name="SLACK_APP_TOKEN",
                level=SecretLevel.OPTIONAL,
                pattern=r"^xapp-[0-9]+-[A-Z0-9]+-[0-9]+-[a-f0-9]{64}$",
                description="Slack App Token",
                example="xapp-[n]-[A123]-[n]-[64_hex_chars]"
            ),
            
            # Database connection strings
            SecretPattern(
                name="DATABASE_URL",
                level=SecretLevel.OPTIONAL,
                pattern=r"^(postgresql|mysql|sqlite)://.*$",
                description="Database connection URL",
                example="postgresql://user:pass@host:port/db"
            ),
            
            # API Keys
            SecretPattern(
                name="OPENAI_API_KEY",
                level=SecretLevel.OPTIONAL,
                pattern=r"^sk-[a-zA-Z0-9]{48}$",
                description="OpenAI API Key",
                example="sk-[48_chars]"
            ),
            
            # Generic patterns
            SecretPattern(
                name="API_KEY",
                level=SecretLevel.OPTIONAL,
                pattern=r"^[a-zA-Z0-9_\-]{16,}$",
                description="Generic API Key",
                example="api_key_[alphanumeric]"
            ),
        ]
    
    def _load_environment(self):
        """Load environment variables from .env file."""
        # First, load all system environment variables
        for key, value in os.environ.items():
            self.parameters[key] = value
            
        env_path = Path(self.env_file)
        
        if env_path.exists():
            logger.info(f"📁 Loading environment from {self.env_file}")
            try:
                with open(env_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Parse KEY=VALUE format
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            
                            self.parameters[key] = value
                            logger.debug(f"   - Loaded {key} from .env")
                        else:
                            self.validation_issues.append(f"Invalid .env format at line {line_num}: {line}")
                            
            except Exception as e:
                self.validation_issues.append(f"Failed to load .env file: {e}")
                logger.error(f"❌ Failed to load {self.env_file}: {e}")
        else:
            logger.info(f"📁 No .env file found at {self.env_file}")
    
    def _load_secrets(self):
        """Load secrets from secrets.json, overwriting environment variables."""
        secrets_path = Path(self.secrets_file)
        
        if secrets_path.exists():
            logger.info(f"🔐 Loading secrets from {self.secrets_file}")
            try:
                with open(secrets_path, 'r') as f:
                    secrets_data = json.load(f)
                
                # Flatten nested structures for easier access
                flattened = self._flatten_json(secrets_data)
                
                for key, value in flattened.items():
                    if key in self.parameters:
                        logger.debug(f"   - Overwriting {key} from secrets.json")
                    else:
                        logger.debug(f"   - Adding {key} from secrets.json")
                    
                    self.parameters[key] = value
                    
            except json.JSONDecodeError as e:
                self.validation_issues.append(f"Invalid JSON in secrets.json: {e}")
                logger.error(f"❌ Invalid JSON in {self.secrets_file}: {e}")
            except Exception as e:
                self.validation_issues.append(f"Failed to load secrets.json: {e}")
                logger.error(f"❌ Failed to load {self.secrets_file}: {e}")
        else:
            logger.info(f"🔐 No secrets file found at {self.secrets_file}")
    
    def _flatten_json(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested JSON structure for easier parameter access."""
        result = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_json(value, full_key))
            else:
                result[full_key] = value
                # Also add without prefix for common keys
                result[key] = value
        
        return result
    
    def _validate_secrets(self):
        """Validate secrets - simplified to just check for non-empty values."""
        logger.info("🔍 Validating secrets - checking for non-empty values...")
        
        for pattern in self.secret_patterns:
            value = self.get_parameter(pattern.name, required=False)
            
            if value is None:
                if pattern.level == SecretLevel.REQUIRED:
                    self.validation_issues.append(
                        f"Required secret '{pattern.name}' is missing. "
                        f"Expected: {pattern.description}"
                    )
                elif pattern.level == SecretLevel.OPTIONAL:
                    logger.debug(f"   - Optional secret '{pattern.name}' not provided")
                continue
            
            # Simple validation - just check if not empty
            value_str = str(value).strip()
            if not value_str:
                self.validation_issues.append(
                    f"Secret '{pattern.name}' is empty or whitespace only"
                )
                logger.warning(f"⚠️ Empty value for {pattern.name}")
            else:
                logger.info(f"   ✅ {pattern.name} validation passed (non-empty)")
        
        # Debug: List all managed values after being set
        self._list_managed_values()
    
    def _list_managed_values(self):
        """Debug: List all managed parameter values after being set."""
        logger.info("📋 Managed parameter values:")
        
        secret_keywords = ["token", "key", "secret", "password", "pass", "auth", "credential"]
        
        for param_name, param_value in sorted(self.parameters.items()):
            # Check if parameter name suggests it's a secret
            is_secret = any(keyword in param_name.lower() for keyword in secret_keywords)
            
            if is_secret:
                # Show only first/last few characters for secrets
                value_str = str(param_value)
                if len(value_str) > 8:
                    masked_value = f"{value_str[:4]}...{value_str[-4:]}"
                else:
                    masked_value = "***"
                logger.info(f"   🔐 {param_name}: {masked_value} (length: {len(value_str)})")
            else:
                logger.info(f"   📄 {param_name}: {param_value}")
                
        logger.info(f"📊 Total managed parameters: {len(self.parameters)}")
    
    def get_parameter(self, key: str, default: Any = None, required: bool = False) -> Any:
        """Get a parameter value with optional requirement checking."""
        value = self.parameters.get(key, default)
        
        if required and value is None:
            raise ValueError(
                f"Required parameter '{key}' is not defined. "
                f"Add it to {self.env_file} or {self.secrets_file}"
            )
        
        return value
    
    def get_secret(self, key: str, required: bool = True) -> str:
        """Get a secret value with strict requirement checking."""
        value = self.get_parameter(key, required=required)
        
        if value is None:
            if required:
                raise ValueError(f"Required secret '{key}' is not available")
            return None
        
        # Additional validation for secrets
        value_str = str(value)
        if len(value_str) < 8:
            logger.warning(f"⚠️ Secret '{key}' seems too short (length: {len(value_str)})")
        
        return value_str
    
    def get_github_token(self) -> str:
        """Get GitHub token with fallback options."""
        for token_name in ["GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"]:
            token = self.get_parameter(token_name, required=False)
            if token:
                return str(token)
        
        raise ValueError(
            "No GitHub token found. Set one of: GITHUB_PERSONAL_ACCESS_TOKEN, GITHUB_TOKEN, or GH_TOKEN"
        )
    
    def get_slack_token(self) -> str:
        """Get Slack token with validation."""
        return self.get_secret("SLACK_BOT_TOKEN", required=True)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration parameters."""
        return {
            "url": self.get_parameter("DATABASE_URL", required=False),
            "host": self.get_parameter("DB_HOST", default="localhost"),
            "port": self.get_parameter("DB_PORT", default=5432),
            "name": self.get_parameter("DB_NAME", required=False),
            "user": self.get_parameter("DB_USER", required=False),
            "password": self.get_parameter("DB_PASSWORD", required=False),
        }
    
    def has_validation_issues(self) -> bool:
        """Check if there are any validation issues."""
        return len(self.validation_issues) > 0
    
    def get_validation_issues(self) -> List[str]:
        """Get list of validation issues."""
        return self.validation_issues.copy()
    
    def get_all_parameters(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Get all parameters, optionally including secrets."""
        if include_secrets:
            return self.parameters.copy()
        
        # Filter out potential secrets
        secret_keywords = ["token", "key", "secret", "password", "pass", "auth", "credential"]
        safe_params = {}
        
        for key, value in self.parameters.items():
            if any(keyword in key.lower() for keyword in secret_keywords):
                safe_params[key] = "***REDACTED***"
            else:
                safe_params[key] = value
        
        return safe_params
    
    def validate_mcp_configuration(self) -> Dict[str, Any]:
        """Validate configuration for MCP services."""
        validation_result = {
            "github": {"available": False, "issues": []},
            "slack": {"available": False, "issues": []},
            "repomix": {"available": True, "issues": []},  # Repomix doesn't need auth
        }
        
        # Validate GitHub
        try:
            github_token = self.get_github_token()
            if github_token:
                validation_result["github"]["available"] = True
                logger.info("✅ GitHub authentication configured")
            else:
                validation_result["github"]["issues"].append("No GitHub token available")
        except ValueError as e:
            validation_result["github"]["issues"].append(str(e))
        
        # Validate Slack
        try:
            slack_token = self.get_slack_token()
            if slack_token:
                validation_result["slack"]["available"] = True
                logger.info("✅ Slack authentication configured")
            else:
                validation_result["slack"]["issues"].append("No Slack token available")
        except ValueError as e:
            validation_result["slack"]["issues"].append(str(e))
            validation_result["slack"]["available"] = False
        
        return validation_result

# Global parameter service instance
_parameter_service: Optional[ParameterService] = None

def get_parameter_service(env_file: str = ".env", secrets_file: str = "secrets.json") -> ParameterService:
    """Get or create the global parameter service instance."""
    global _parameter_service
    
    if _parameter_service is None:
        _parameter_service = ParameterService(env_file, secrets_file)
    
    return _parameter_service

def reset_parameter_service():
    """Reset the global parameter service (useful for testing)."""
    global _parameter_service
    _parameter_service = None

# Convenience functions
def get_param(key: str, default: Any = None, required: bool = False) -> Any:
    """Convenience function to get a parameter."""
    return get_parameter_service().get_parameter(key, default, required)

def get_secret(key: str, required: bool = True) -> str:
    """Convenience function to get a secret."""
    return get_parameter_service().get_secret(key, required)

def validate_configuration() -> bool:
    """Validate the current configuration and return True if valid."""
    service = get_parameter_service()
    
    if service.has_validation_issues():
        logger.error("❌ Configuration validation failed:")
        for issue in service.get_validation_issues():
            logger.error(f"   - {issue}")
        return False
    
    logger.info("✅ Configuration validation passed")
    return True 