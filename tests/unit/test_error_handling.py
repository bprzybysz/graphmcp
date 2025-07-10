"""
Unit tests for Error Handling Module

Tests the production-grade error management system:
- Error categorization
- Error severity levels  
- Error context creation
- Error handling and recovery
- Circuit breaker pattern
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from concrete.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorRecoveryStrategy,
    ErrorHandler,
    CircuitBreaker,
    handle_errors,
    get_error_handler
)


class TestErrorCategory:
    """Test cases for ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test all error category values are defined."""
        expected_categories = [
            "NETWORK", "AUTHENTICATION", "CONFIGURATION", "RESOURCE",
            "BUSINESS_LOGIC", "EXTERNAL_SERVICE", "DATA_VALIDATION", "SYSTEM"
        ]
        
        for category in expected_categories:
            assert hasattr(ErrorCategory, category)


class TestErrorSeverity:
    """Test cases for ErrorSeverity enum."""
    
    def test_error_severity_values(self):
        """Test all error severity values are defined."""
        expected_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        for severity in expected_severities:
            assert hasattr(ErrorSeverity, severity)


class TestErrorContext:
    """Test cases for ErrorContext class."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation with all fields."""
        context = ErrorContext(
            error_id="test_001",
            timestamp=datetime.now(),
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            message="Test error",
            exception_type="TestException",
            traceback_str="Mock traceback",
            function_name="test_function",
            module_name="test_module",
            metadata={"key": "value"},
            workflow_id="workflow_123",
            database_name="test_db",
            repository_url="https://github.com/test/repo"
        )
        
        assert context.error_id == "test_001"
        assert context.severity == ErrorSeverity.HIGH
        assert context.category == ErrorCategory.NETWORK
        assert context.message == "Test error"
        assert context.workflow_id == "workflow_123"
        assert context.database_name == "test_db"
        assert context.repository_url == "https://github.com/test/repo"
    
    def test_error_context_to_dict(self):
        """Test ErrorContext serialization to dictionary."""
        context = ErrorContext(
            error_id="test_001",
            timestamp=datetime.now(),
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHENTICATION,
            message="Auth error",
            exception_type="AuthError",
            traceback_str="Mock traceback",
            function_name="auth_func",
            module_name="auth_module",
            metadata={"user": "test_user"}
        )
        
        context_dict = context.to_dict()
        
        assert context_dict["error_id"] == "test_001"
        assert context_dict["severity"] == "medium"
        assert context_dict["category"] == "authentication"
        assert context_dict["message"] == "Auth error"
        assert "timestamp" in context_dict
        assert isinstance(context_dict["timestamp"], str)  # Should be ISO format


class TestErrorRecoveryStrategy:
    """Test cases for ErrorRecoveryStrategy class."""
    
    def test_recovery_strategy_creation(self):
        """Test ErrorRecoveryStrategy creation."""
        strategy = ErrorRecoveryStrategy(max_retries=3, backoff_factor=2.0)
        
        assert strategy.max_retries == 3
        assert strategy.backoff_factor == 2.0
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_success(self):
        """Test successful operation execution."""
        strategy = ErrorRecoveryStrategy(max_retries=2)
        
        async def success_operation():
            return "success"
        
        result = await strategy.execute_with_recovery(success_operation)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_retry_and_succeed(self):
        """Test retry mechanism that eventually succeeds."""
        strategy = ErrorRecoveryStrategy(max_retries=2, backoff_factor=1.01)  # Fast backoff for testing
        
        attempt_count = 0
        async def failing_then_success_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary failure")
            return "eventual_success"
        
        result = await strategy.execute_with_recovery(failing_then_success_operation)
        assert result == "eventual_success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_max_retries_exceeded(self):
        """Test when max retries are exceeded."""
        strategy = ErrorRecoveryStrategy(max_retries=1, backoff_factor=1.01)
        
        async def always_failing_operation():
            raise RuntimeError("Persistent failure")
        
        with pytest.raises(RuntimeError, match="Persistent failure"):
            await strategy.execute_with_recovery(always_failing_operation)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""
    
    def test_circuit_breaker_creation(self):
        """Test CircuitBreaker creation."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30.0,
            expected_exception=ConnectionError
        )
        
        assert breaker.failure_threshold == 3
        assert breaker.timeout == 30.0
        assert breaker.expected_exception == ConnectionError
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_call(self):
        """Test successful operation through circuit breaker."""
        breaker = CircuitBreaker()
        
        async def success_operation():
            return "success"
        
        result = await breaker.call(success_operation)
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after threshold."""
        breaker = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        
        async def failing_operation():
            raise ValueError("Service error")
        
        # First failure
        with pytest.raises(ValueError):
            await breaker.call(failing_operation)
        assert breaker.state == "closed"
        assert breaker.failure_count == 1
        
        # Second failure should open circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_operation)
        assert breaker.state == "open"
        assert breaker.failure_count == 2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state."""
        breaker = CircuitBreaker(failure_threshold=1, timeout=1.0)
        
        async def failing_operation():
            raise Exception("Service error")
        
        # Trigger circuit breaker to open
        with pytest.raises(Exception):
            await breaker.call(failing_operation)
        assert breaker.state == "open"
        
        # Subsequent calls should fail immediately
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_operation)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery to half-open state."""
        breaker = CircuitBreaker(failure_threshold=1, timeout=0.1)
        
        async def failing_operation():
            raise Exception("Service error")
        
        async def success_operation():
            return "recovered"
        
        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(failing_operation)
        assert breaker.state == "open"
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Should move to half-open and then closed on success
        result = await breaker.call(success_operation)
        assert result == "recovered"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def test_error_handler_creation(self):
        """Test ErrorHandler creation."""
        handler = ErrorHandler()
        
        assert len(handler.error_history) == 0
        assert len(handler.circuit_breakers) == 0
        assert len(handler.recovery_strategies) > 0  # Has default strategies
    
    def test_error_handler_get_circuit_breaker(self):
        """Test getting circuit breaker for a service."""
        handler = ErrorHandler()
        
        breaker1 = handler.get_circuit_breaker("service_a")
        breaker2 = handler.get_circuit_breaker("service_a")
        breaker3 = handler.get_circuit_breaker("service_b")
        
        # Same service should return same breaker
        assert breaker1 is breaker2
        # Different service should return different breaker
        assert breaker1 is not breaker3
    
    @pytest.mark.asyncio
    async def test_error_handler_handle_error(self):
        """Test error handling and context creation."""
        handler = ErrorHandler()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error_context = await handler.handle_error(
                e,
                context={"test_key": "test_value"},
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATA_VALIDATION,
                workflow_id="test_workflow",
                database_name="test_db"
            )
        
        assert error_context.severity == ErrorSeverity.HIGH
        assert error_context.category == ErrorCategory.DATA_VALIDATION
        assert error_context.message == "Test error"
        assert error_context.workflow_id == "test_workflow"
        assert error_context.database_name == "test_db"
        assert error_context.metadata["test_key"] == "test_value"
        
        # Check error was recorded
        assert len(handler.error_history) == 1
        assert handler.error_history[0] == error_context
    
    @pytest.mark.asyncio
    async def test_error_handler_execute_with_error_handling(self):
        """Test executing operation with error handling."""
        handler = ErrorHandler()
        
        # Test successful operation
        async def success_operation():
            return "success_result"
        
        result = await handler.execute_with_error_handling(
            success_operation,
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            workflow_id="test_workflow"
        )
        
        assert result == "success_result"
        assert len(handler.error_history) == 0  # No errors recorded
    
    @pytest.mark.asyncio
    async def test_error_handler_execute_with_failure(self):
        """Test executing operation that fails."""
        handler = ErrorHandler()
        
        async def failing_operation():
            raise ConnectionError("Network failure")
        
        # Should handle the error and re-raise it
        with pytest.raises(ConnectionError):
            await handler.execute_with_error_handling(
                failing_operation,
                error_category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH
            )
        
        # Error should be recorded
        assert len(handler.error_history) == 1
        assert handler.error_history[0].category == ErrorCategory.NETWORK
        assert handler.error_history[0].severity == ErrorSeverity.HIGH
    
    def test_error_handler_get_error_summary(self):
        """Test getting error summary."""
        handler = ErrorHandler()
        
        # Add some mock errors
        for i in range(3):
            error_context = ErrorContext(
                error_id=f"test_{i}",
                timestamp=datetime.now(),
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.NETWORK,
                message=f"Error {i}",
                exception_type="TestError",
                traceback_str="Mock traceback",
                function_name="test_func",
                module_name="test_module",
                metadata={}
            )
            handler.error_history.append(error_context)
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert len(summary["recent_errors"]) == 3
        assert ErrorCategory.NETWORK.value in summary["error_by_category"]
        assert summary["error_by_category"][ErrorCategory.NETWORK.value] == 3


class TestErrorHandlerHelpers:
    """Test cases for error handler helper functions."""
    
    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Should return the same instance
        assert handler1 is handler2
        assert isinstance(handler1, ErrorHandler)
    
    @pytest.mark.asyncio
    async def test_handle_errors_decorator(self):
        """Test handle_errors decorator."""
        @handle_errors(
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH,
            context={"test": "decorator"}
        )
        async def decorated_function():
            return "decorated_result"
        
        result = await decorated_function()
        assert result == "decorated_result"
    
    @pytest.mark.asyncio
    async def test_handle_errors_decorator_with_failure(self):
        """Test handle_errors decorator with failing function."""
        @handle_errors(
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH
        )
        async def failing_decorated_function():
            raise RuntimeError("Decorated failure")
        
        with pytest.raises(RuntimeError):
            await failing_decorated_function()
        
        # Error should be recorded in global handler
        global_handler = get_error_handler()
        assert len(global_handler.error_history) > 0


class TestErrorHandlerIntegration:
    """Integration tests for error handler."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_error_handling_workflow(self):
        """Test complete error handling workflow."""
        handler = ErrorHandler()
        
        # Test different error scenarios
        scenarios = [
            (ConnectionError("Network timeout"), ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            (ValueError("Invalid data"), ErrorCategory.DATA_VALIDATION, ErrorSeverity.MEDIUM),
            (PermissionError("Access denied"), ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
        ]
        
        for exception, category, severity in scenarios:
            try:
                raise exception
            except Exception as e:
                await handler.handle_error(
                    e,
                    context={"scenario": "integration_test"},
                    severity=severity,
                    category=category,
                    workflow_id="integration_workflow"
                )
        
        # Verify all errors were recorded
        assert len(handler.error_history) == 3
        
        # Check error summary
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 3
        assert len(summary["error_by_category"]) >= 3
        
        # Test circuit breaker integration
        network_breaker = handler.get_circuit_breaker("test_service")
        assert network_breaker.state == "closed"
        assert network_breaker.failure_count == 0 