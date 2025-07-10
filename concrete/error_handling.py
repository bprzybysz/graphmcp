"""
Production Error Handling System for Database Decommissioning Workflow.

This module provides comprehensive error handling, recovery mechanisms,
and error reporting for production deployment.
"""

import asyncio
import traceback
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import json
import uuid # Add this import

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels for classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATA_VALIDATION = "data_validation"
    SYSTEM = "system"

@dataclass
class ErrorContext:
    """Context information for errors."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback_str: str
    function_name: str
    module_name: str
    metadata: Dict[str, Any]
    workflow_id: Optional[str] = None
    database_name: Optional[str] = None
    repository_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['severity'] = self.severity.value
        result['category'] = self.category.value
        return result

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def execute_with_recovery(self,
                                  operation: Callable,
                                  *args,
                                  **kwargs) -> Any:
        """Execute operation with recovery strategy."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    delay = self.backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    
        raise last_error

class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self,
                 failure_threshold: int = 5,
                 timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker."""
        if self.state == "open":
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception("Circuit breaker is OPEN - service unavailable")
            else:
                self.state = "half-open"
                logger.info("Circuit breaker moving to HALF-OPEN state")
        
        try:
            result = await operation(*args, **kwargs)
            
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker moved to CLOSED state")
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker moved to OPEN state after {self.failure_count} failures")
            
            raise e

class ErrorHandler:
    """Comprehensive error handling system."""
    
    def __init__(self, 
                 alert_callback: Optional[Callable] = None,
                 storage_path: str = "logs/errors"):
        self.alert_callback = alert_callback
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.error_history = []
        self.circuit_breakers = {}
        self.recovery_strategies = {}
        
        # Initialize default recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies for different error types."""
        self.recovery_strategies = {
            ErrorCategory.NETWORK: ErrorRecoveryStrategy(max_retries=3, backoff_factor=2.0),
            ErrorCategory.EXTERNAL_SERVICE: ErrorRecoveryStrategy(max_retries=2, backoff_factor=3.0),
            ErrorCategory.RESOURCE: ErrorRecoveryStrategy(max_retries=1, backoff_factor=1.0),
            ErrorCategory.AUTHENTICATION: ErrorRecoveryStrategy(max_retries=1, backoff_factor=1.0)
        }
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    async def handle_error(self,
                          exception: Exception,
                          context: Dict[str, Any] = None,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          category: ErrorCategory = ErrorCategory.SYSTEM,
                          workflow_id: str = None,
                          database_name: str = None,
                          repository_url: str = None) -> ErrorContext:
        """Handle an error with comprehensive logging and reporting."""
        
        # Create error context
        error_context = ErrorContext(
            error_id=f"err_{uuid.uuid4().hex}", # Use uuid for robust unique IDs
            timestamp=datetime.utcnow(),
            severity=severity,
            category=category,
            message=str(exception),
            exception_type=type(exception).__name__,
            traceback_str=traceback.format_exc(),
            function_name=traceback.extract_tb(exception.__traceback__)[-1].name if exception.__traceback__ else "unknown",
            module_name=traceback.extract_tb(exception.__traceback__)[-1].filename if exception.__traceback__ else "unknown",
            metadata=context or {},
            workflow_id=workflow_id,
            database_name=database_name,
            repository_url=repository_url
        )
        
        # Store error
        self.error_history.append(error_context)
        
        # Log error based on severity
        self._log_error(error_context)
        
        # Save error to file
        await self._save_error_to_file(error_context)
        
        # Send alert for high severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and self.alert_callback:
            try:
                await self.alert_callback(error_context)
            except Exception as alert_error:
                logger.error(f"Failed to send error alert: {alert_error}")
        
        return error_context
    
    def _log_error(self, error_context: ErrorContext):
        """Log error based on severity."""
        message = f"[{error_context.error_id}] {error_context.message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(message)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(message)
        else:
            logger.info(message)
        
        # Always log full context at debug level
        logger.debug(f"Error context: {error_context.to_dict()}")
    
    async def _save_error_to_file(self, error_context: ErrorContext):
        """Save error to persistent storage."""
        try:
            timestamp = error_context.timestamp.strftime("%Y%m%d")
            error_file = self.storage_path / f"errors_{timestamp}.json"
            
            # Read existing errors
            errors = []
            if error_file.exists():
                with open(error_file, 'r') as f:
                    errors = json.load(f)
            
            # Add new error
            errors.append(error_context.to_dict())
            
            # Write back to file
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save error to file: {e}")
    
    async def execute_with_error_handling(self,
                                        operation: Callable,
                                        *args,
                                        error_category: ErrorCategory = ErrorCategory.SYSTEM,
                                        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                                        context: Dict[str, Any] = None,
                                        workflow_id: str = None,
                                        database_name: str = None,
                                        repository_url: str = None,
                                        **kwargs) -> Any:
        """Execute operation with comprehensive error handling."""
        
        try:
            # Use recovery strategy if available
            if error_category in self.recovery_strategies:
                strategy = self.recovery_strategies[error_category]
                return await strategy.execute_with_recovery(operation, *args, **kwargs)
            else:
                return await operation(*args, **kwargs)
                
        except Exception as e:
            await self.handle_error(
                exception=e,
                context=context,
                severity=severity,
                category=error_category,
                workflow_id=workflow_id,
                database_name=database_name,
                repository_url=repository_url
            )
            raise
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.error_history:
            return {
                "total_errors": 0,
                "error_by_severity": {},
                "error_by_category": {},
                "recent_errors": [],
                "circuit_breaker_states": {
                    name: breaker.state for name, breaker in self.circuit_breakers.items()
                }
            }
        
        recent_errors = self.error_history[-10:]  # Last 10 errors
        
        severity_count = {}
        category_count = {}
        
        for error in self.error_history:
            severity_count[error.severity.value] = severity_count.get(error.severity.value, 0) + 1
            category_count[error.category.value] = category_count.get(error.category.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_by_severity": severity_count,
            "error_by_category": category_count,
            "recent_errors": [error.to_dict() for error in recent_errors],
            "circuit_breaker_states": {
                name: breaker.state for name, breaker in self.circuit_breakers.items()
            }
        }
    
    async def export_error_report(self, output_path: str):
        """Export comprehensive error report."""
        try:
            report = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "summary": self.get_error_summary(),
                "all_errors": [error.to_dict() for error in self.error_history],
                "recovery_strategies": {
                    category.value: {
                        "max_retries": strategy.max_retries,
                        "backoff_factor": strategy.backoff_factor
                    }
                    for category, strategy in self.recovery_strategies.items()
                },
                "circuit_breakers": {
                    name: {
                        "state": breaker.state,
                        "failure_count": breaker.failure_count,
                        "failure_threshold": breaker.failure_threshold,
                        "timeout": breaker.timeout
                    }
                    for name, breaker in self.circuit_breakers.items()
                }
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Error report exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Dict[str, Any] = None):
    """Decorator for automatic error handling."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            
            return await error_handler.execute_with_error_handling(
                func,
                *args,
                error_category=category,
                severity=severity,
                context=context,
                **kwargs
            )
        return wrapper
    return decorator

# Global error handler instance
_error_handler = None

def get_error_handler(alert_callback: Optional[Callable] = None) -> ErrorHandler:
    """Get or create global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(alert_callback=alert_callback)
    return _error_handler

def reset_error_handler():
    """Reset global error handler (for testing)."""
    global _error_handler
    _error_handler = None 