"""
Unit tests for the Error Handling System.

Tests the error handling system functionality including:
- ErrorSeverity and ErrorCategory Enums
- ErrorContext Dataclass
- ErrorRecoveryStrategy
- CircuitBreaker
- ErrorHandler class methods
- handle_errors decorator
- Global error handler functions
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock, call
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Import the module under test
from concrete.error_handling import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    ErrorRecoveryStrategy,
    CircuitBreaker,
    ErrorHandler,
    handle_errors,
    get_error_handler,
    reset_error_handler,
    logger as error_handling_logger # Import the module's logger
)

# Use a custom logger name to avoid conflicts with other tests
TEST_LOGGER_NAME = "test_error_handling_logger"

@pytest.fixture
def mock_time():
    """Mock time.time(), datetime.utcnow(), and datetime.now() in the module under test."""
    # Patch datetime.datetime directly as it's used as a class (not a module) in concrete.error_handling
    with patch('concrete.error_handling.time.time') as mock_time_time, \
         patch('concrete.error_handling.datetime.datetime', autospec=True) as mock_datetime_datetime_class, \
         patch('concrete.error_handling.asyncio.sleep', new_callable=AsyncMock) as mock_async_sleep:
        
        mock_fixed_datetime = datetime(2023, 3, 15, 0, 0, 0)

        # Configure the mocked datetime.datetime class methods
        mock_datetime_datetime_class.utcnow.return_value = mock_fixed_datetime
        mock_datetime_datetime_class.now.return_value = mock_fixed_datetime
        
        # Ensure the mocked datetime.datetime can still be called as a constructor
        mock_datetime_datetime_class.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        # Mock time.time()
        mock_time_time.return_value = 1678886400.0  # March 15, 2023 00:00:00 GMT
        
        yield { # Return a dictionary of mocks if you need to interact with them in tests
            "time_time": mock_time_time,
            "datetime_datetime": mock_datetime_datetime_class, # Use this to interact with the mocked class
            "async_sleep": mock_async_sleep
        }

@pytest.fixture
def mock_logger():
    """Fixture to mock the logger used in error_handling.py."""
    with patch('concrete.error_handling.logger') as mock_log_instance:
        # Reset mocks for each test
        mock_log_instance.reset_mock()
        # Set up a side_effect for debug to inspect calls if needed
        # mock_log_instance.debug.side_effect = lambda *args, **kwargs: print(f"DEBUG LOG: {args}, {kwargs}")
        yield mock_log_instance

@pytest.fixture
def error_handler(tmp_path):
    """Fixture for a clean ErrorHandler instance for each test."""
    reset_error_handler() # Ensure a clean slate for the global handler
    return ErrorHandler(storage_path=tmp_path / "test_errors")

class TestEnums:
    def test_error_severity_enum(self):
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_category_enum(self):
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.BUSINESS_LOGIC.value == "business_logic"
        assert ErrorCategory.EXTERNAL_SERVICE.value == "external_service"
        assert ErrorCategory.DATA_VALIDATION.value == "data_validation"
        assert ErrorCategory.SYSTEM.value == "system"

class TestErrorContext:
    @pytest.mark.asyncio
    @patch('concrete.error_handling.traceback.format_exc', return_value="mock_traceback")
    @patch('concrete.error_handling.traceback.extract_tb')
    @patch('concrete.error_handling.uuid.uuid4')
    async def test_error_context_creation(self, mock_uuid_func, mock_extract_tb, mock_format_exc, mock_time):
        mock_uuid_instance = MagicMock()
        mock_uuid_instance.hex = "test_uuid"
        mock_uuid_func.return_value = mock_uuid_instance

        mock_frame = MagicMock()
        mock_frame.name = "test_function_name"
        mock_frame.filename = "test_module.py"
        mock_extract_tb.return_value = [mock_frame]

        exception = ValueError("Test message")
        context_data = {"key": "value"}

        # Simulate the call to handle_error which creates ErrorContext
        error_context = ErrorContext(
            error_id=f"err_{mock_uuid_instance.hex}",
            timestamp=datetime.utcnow(),  # This will use the mocked datetime.utcnow
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.BUSINESS_LOGIC,
            message=str(exception),
            exception_type=type(exception).__name__,
            traceback_str=mock_format_exc.return_value,
            function_name=mock_frame.name,
            module_name=mock_frame.filename,
            metadata=context_data,
            workflow_id="wf_123",
            database_name="db_abc",
            repository_url="http://repo.com"
        )
        
        assert error_context.error_id == f"err_test_uuid"
        assert error_context.timestamp == datetime(2023, 3, 15, 0, 0, 0)
        assert error_context.severity == ErrorSeverity.HIGH
        assert error_context.category == ErrorCategory.BUSINESS_LOGIC
        assert error_context.message == "Test message"
        assert error_context.exception_type == "ValueError"
        assert error_context.traceback_str == "mock_traceback"
        assert error_context.function_name == "test_function_name"
        assert error_context.module_name == "test_module.py"
        assert error_context.metadata == context_data
        assert error_context.workflow_id == "wf_123"
        assert error_context.database_name == "db_abc"
        assert error_context.repository_url == "http://repo.com"
        mock_uuid_func.assert_called_once()
        mock_format_exc.assert_called_once()
        mock_extract_tb.assert_called_once()

    @pytest.mark.asyncio
    @patch('concrete.error_handling.uuid.uuid4')
    @patch('concrete.error_handling.traceback.format_exc', return_value="mock_traceback_str")
    @patch('concrete.error_handling.traceback.extract_tb')
    async def test_error_context_to_dict(self, mock_extract_tb, mock_format_exc, mock_uuid_func, mock_time):
        mock_uuid_instance = MagicMock()
        mock_uuid_instance.hex = "dict_uuid"
        mock_uuid_func.return_value = mock_uuid_instance

        mock_frame = MagicMock()
        mock_frame.name = "dict_function"
        mock_frame.filename = "dict_module.py"
        mock_extract_tb.return_value = [mock_frame]

        error_context = ErrorContext(
            error_id=f"err_{mock_uuid_instance.hex}",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RESOURCE,
            message="Resource not found",
            exception_type="FileNotFoundError",
            traceback_str="mock_traceback_str",
            function_name="dict_function",
            module_name="dict_module.py",
            metadata={"file": "/path/to/file"},
            workflow_id="wf_dict",
            database_name="db_dict",
            repository_url="http://dict_repo.com"
        )
        
        result_dict = error_context.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['error_id'] == "err_dict_uuid"
        assert result_dict['timestamp'] == "2023-03-15T00:00:00"
        assert result_dict['severity'] == "medium"
        assert result_dict['category'] == "resource"
        assert result_dict['message'] == "Resource not found"
        assert result_dict['exception_type'] == "FileNotFoundError"
        assert result_dict['traceback_str'] == "mock_traceback_str"
        assert result_dict['function_name'] == "dict_function"
        assert result_dict['module_name'] == "dict_module.py"
        assert result_dict['metadata'] == {"file": "/path/to/file"}
        assert result_dict['workflow_id'] == "wf_dict"
        assert result_dict['database_name'] == "db_dict"
        assert result_dict['repository_url'] == "http://dict_repo.com"

class TestErrorRecoveryStrategy:
    @pytest.mark.asyncio
    async def test_execute_with_recovery_success(self, mock_time, mock_logger):
        strategy = ErrorRecoveryStrategy(max_retries=3)
        mock_operation = AsyncMock(return_value="Success")

        result = await strategy.execute_with_recovery(mock_operation, 1, 2, kwarg="test")
        
        assert result == "Success"
        mock_operation.assert_called_once_with(1, 2, kwarg="test")
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_recovery_failure_then_success(self, mock_time, mock_logger):
        strategy = ErrorRecoveryStrategy(max_retries=2, backoff_factor=1.0)
        mock_operation = AsyncMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "Success"])

        result = await strategy.execute_with_recovery(mock_operation, "data")
        
        assert result == "Success"
        assert mock_operation.call_count == 3
        expected_warning_calls = [
            call("Attempt 1 failed, retrying in 1.0s: Fail 1"),
            call("Attempt 2 failed, retrying in 1.0s: Fail 2")
        ]
        mock_logger.warning.assert_has_calls(expected_warning_calls, any_order=True)
        mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_recovery_all_attempts_fail(self, mock_time, mock_logger):
        strategy = ErrorRecoveryStrategy(max_retries=2, backoff_factor=1.0)
        mock_operation = AsyncMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), ValueError("Fail 3")])

        with pytest.raises(ValueError, match="Fail 3"):
            await strategy.execute_with_recovery(mock_operation)
        
        assert mock_operation.call_count == 3
        expected_warning_calls = [
            call("Attempt 1 failed, retrying in 1.0s: Fail 1"),
            call("Attempt 2 failed, retrying in 1.0s: Fail 2")
        ]
        mock_logger.warning.assert_has_calls(expected_warning_calls, any_order=True)
        mock_logger.error.assert_called_once_with("All 3 attempts failed") # Max retries + 1

class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, mock_time, mock_logger):
        cb = CircuitBreaker(failure_threshold=2, timeout=5)
        mock_operation = AsyncMock(return_value="Operation Success")

        result = await cb.call(mock_operation)
        assert result == "Operation Success"
        assert cb.state == "closed"
        assert cb.failure_count == 0
        mock_operation.assert_called_once()
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self, mock_time, mock_logger):
        cb = CircuitBreaker(failure_threshold=1, timeout=5)
        mock_operation = AsyncMock(side_effect=[ValueError("Failure"), "Success"])

        with pytest.raises(ValueError):
            await cb.call(mock_operation) # First call fails, opens circuit

        assert cb.state == "open"
        assert cb.failure_count == 1
        mock_logger.error.assert_called_once_with("Circuit breaker moved to OPEN state after 1 failures")

        # Attempt call while open and within timeout
        with pytest.raises(Exception, match="Circuit breaker is OPEN - service unavailable"):
            await cb.call(mock_operation)
        
        # Advance time to after timeout for half-open transition
        mock_time["time_time"].return_value += 6  # Advance by 6 seconds
        mock_logger.reset_mock() # Reset logger for next assertion

        # Attempt call in half-open state (will move to half-open, then fail again)
        with pytest.raises(ValueError):
            await cb.call(mock_operation)
        
        assert cb.state == "open" # Should revert to open because the call failed
        assert mock_logger.info.called # Should have logged transition to half-open
        mock_logger.error.assert_called_once_with("Circuit breaker moved to OPEN state after 2 failures") # Should increment failure count and log open again

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state_success(self, mock_time, mock_logger):
        cb = CircuitBreaker(failure_threshold=1, timeout=5)
        mock_operation = AsyncMock(side_effect=[ValueError("Failure"), "Success"])

        with pytest.raises(ValueError):
            await cb.call(mock_operation) # Fail once to open circuit
        
        # Advance time to move to half-open
        mock_time["time_time"].return_value += 6
        mock_logger.reset_mock() # Reset logger for next assertion

        result = await cb.call(mock_operation) # Succeed in half-open
        assert result == "Success"
        assert cb.state == "closed"
        assert cb.failure_count == 0
        mock_logger.info.assert_has_calls([
            call("Circuit breaker moving to HALF-OPEN state"),
            call("Circuit breaker moved to CLOSED state")
        ], any_order=True)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state_failure(self, mock_time, mock_logger):
        cb = CircuitBreaker(failure_threshold=1, timeout=5)
        mock_operation = AsyncMock(side_effect=[ValueError("Failure"), ValueError("Another Failure")])

        with pytest.raises(ValueError):
            await cb.call(mock_operation) # Fail once to open circuit
        
        # Advance time to move to half-open
        mock_time["time_time"].return_value += 6
        mock_logger.reset_mock()

        with pytest.raises(ValueError):
            await cb.call(mock_operation) # Fail in half-open
        
        assert cb.state == "open"
        assert cb.failure_count == 2 # Failure count should increment
        mock_logger.info.assert_called_once_with("Circuit breaker moving to HALF-OPEN state")
        mock_logger.error.assert_called_once_with("Circuit breaker moved to OPEN state after 2 failures")

class TestErrorHandler:
    def test_error_handler_initialization(self, tmp_path):
        handler = ErrorHandler(storage_path=tmp_path / "errors")
        assert handler.alert_callback is None
        assert handler.storage_path == Path(tmp_path / "errors")
        assert handler.storage_path.exists()
        assert handler.error_history == []
        assert isinstance(handler.recovery_strategies[ErrorCategory.NETWORK], ErrorRecoveryStrategy)

    def test_get_circuit_breaker(self, error_handler):
        cb1 = error_handler.get_circuit_breaker("service_a")
        cb2 = error_handler.get_circuit_breaker("service_a")
        cb3 = error_handler.get_circuit_breaker("service_b")
        
        assert isinstance(cb1, CircuitBreaker)
        assert cb1 is cb2 # Same instance for same service name
        assert cb1 is not cb3 # Different instance for different service name

    @pytest.mark.asyncio
    @patch('concrete.error_handling.get_error_handler') # Patch the global getter
    @patch('concrete.error_handling.traceback.format_exc', return_value="mock_traceback")
    @patch('concrete.error_handling.traceback.extract_tb')
    @patch('concrete.error_handling.uuid.uuid4') # Patch uuid.uuid4 itself
    async def test_handle_error(self, mock_uuid_func, mock_extract_tb, mock_format_exc, mock_get_error_handler, error_handler, mock_time, mock_logger, tmp_path):
        # Ensure the decorator gets our fixture's error_handler instance
        mock_get_error_handler.return_value = error_handler

        # Configure mock_uuid_func to return a mock object with a hex attribute
        mock_uuid_instance = MagicMock()
        mock_uuid_instance.hex = "mock_uuid_value"
        mock_uuid_func.return_value = mock_uuid_instance

        # Configure mock_extract_tb to return a mock frame with correct function_name and filename
        mock_frame = MagicMock()
        mock_frame.name = "test_function"
        mock_frame.filename = "mock_module.py" # Ensure this matches module_name below
        mock_extract_tb.return_value = [mock_frame]
        
        exception = ValueError("Something went wrong")
        context = {"data": 123}
        
        error_context = await error_handler.handle_error(
            exception,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.BUSINESS_LOGIC,
            workflow_id="wf_test",
            database_name="db_prod",
            repository_url="http://repo.git"
        )
        
        assert isinstance(error_context, ErrorContext)
        # Use the mocked uuid value directly
        assert error_context.error_id == f"err_{mock_uuid_instance.hex}"
        # Compare against the explicitly mocked utcnow, not the real one
        assert error_context.timestamp == datetime(2023, 3, 15, 0, 0, 0)
        assert error_context.severity == ErrorSeverity.HIGH
        assert error_context.category == ErrorCategory.BUSINESS_LOGIC
        assert error_context.message == str(exception)
        assert error_context.exception_type == "ValueError"
        assert error_context.traceback_str == "mock_traceback"
        assert error_context.function_name == "test_function" # Updated to match mock_frame.name
        assert error_context.module_name == "mock_module.py" # Updated to match mock_frame.filename
        assert error_context.metadata == context
        assert error_context.workflow_id == "wf_test"
        assert error_context.database_name == "db_prod"
        assert error_context.repository_url == "http://repo.git"
        
        assert len(error_handler.error_history) == 1
        assert error_handler.error_history[0] is error_context
        
        # Verify logging based on severity
        mock_logger.error.assert_called_once_with(f"[{error_context.error_id}] Something went wrong")
        mock_logger.debug.assert_called_once() # Always log full context at debug level
        
        # Verify file storage (simplified check)
        timestamp_str = datetime(2023, 3, 15, 0, 0, 0).strftime("%Y%m%d") # Use mocked timestamp for path
        error_file_path = tmp_path / "test_errors" / f"errors_{timestamp_str}.json"
        assert error_file_path.exists()
        with open(error_file_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]['error_id'] == error_context.error_id

    @pytest.mark.asyncio
    async def test_handle_error_alert_callback(self, error_handler, mock_logger, mock_time):
        mock_alert_callback = AsyncMock()
        error_handler.alert_callback = mock_alert_callback
        
        exception = ConnectionError("Network Down")
        error_context_obj = await error_handler.handle_error(
            exception,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.NETWORK
        )
        
        mock_alert_callback.assert_called_once_with(error_context_obj)
        mock_logger.critical.assert_any_call(f"[{error_context_obj.error_id}] Network Down") # Use assert_any_call for flexibility
        
    @pytest.mark.asyncio
    async def test_handle_error_alert_callback_failure(self, error_handler, mock_logger, mock_time):
        mock_alert_callback = AsyncMock(side_effect=Exception("Alert failed to send"))
        error_handler.alert_callback = mock_alert_callback
        
        exception = ConnectionRefusedError("Cannot connect")
        error_context_obj = await error_handler.handle_error(
            exception,
            severity=ErrorSeverity.CRITICAL
        )
        
        mock_alert_callback.assert_called_once_with(error_context_obj)
        # Expect critical for the error itself, and an error for the alert failure
        mock_logger.critical.assert_any_call(f"[{error_context_obj.error_id}] Cannot connect") # Use assert_any_call for flexibility
        mock_logger.error.assert_called_once_with(f"Failed to send error alert: Alert failed to send")

    @pytest.mark.asyncio
    async def test_execute_with_error_handling_no_strategy(self, error_handler):
        mock_operation = AsyncMock(return_value="Operation Result")
        
        result = await error_handler.execute_with_error_handling(
            mock_operation,
            "arg1", kwarg="value"
        )
        
        assert result == "Operation Result"
        mock_operation.assert_called_once_with("arg1", kwarg="value")
        assert len(error_handler.error_history) == 0

    @pytest.mark.asyncio
    async def test_execute_with_error_handling_with_strategy_success(self, error_handler, mock_logger, mock_time):
        mock_operation = AsyncMock(side_effect=[ConnectionError("First try failed"), "Recovered!"])
        
        result = await error_handler.execute_with_error_handling(
            mock_operation,
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH
        )
        
        assert result == "Recovered!"
        assert mock_operation.call_count == 2
        assert len(error_handler.error_history) == 0 # Should be empty as error was recovered
        
        # Expected warning calls from retries (adjusted to match actual backoff factor of 2.0)
        expected_warning_calls = [
            call(f"Attempt 1 failed, retrying in 1.0s: First try failed")
        ]
        mock_logger.warning.assert_has_calls(expected_warning_calls, any_order=True) # Check logging from the recovery strategy
        mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_error_handling_with_strategy_failure(self, error_handler, mock_logger, mock_time):
        mock_operation = AsyncMock(side_effect=[ConnectionError("Fail 1"), ConnectionError("Fail 2"), ConnectionError("Fail 3")])
        
        # Explicitly set the strategy for this test case if needed, or rely on default
        # strategy = ErrorRecoveryStrategy(max_retries=2, backoff_factor=1.0)
        # error_handler.recovery_strategies[ErrorCategory.NETWORK] = strategy

        with pytest.raises(ConnectionError):
            await error_handler.execute_with_error_handling(
                mock_operation,
                error_category=ErrorCategory.NETWORK, # This category has a default strategy
                severity=ErrorSeverity.CRITICAL
            )
        
        assert mock_operation.call_count == 3
        assert len(error_handler.error_history) == 1 # Error should be in history after all retries fail
        error_context = error_handler.error_history[0]
        assert error_context.message == "Fail 3" # The last error that caused the final failure
        
        expected_warning_calls = [
            call("Attempt 1 failed, retrying in 1.0s: Fail 1"),
            call("Attempt 2 failed, retrying in 2.0s: Fail 2") # Default backoff is 2.0
        ]
        mock_logger.warning.assert_has_calls(expected_warning_calls, any_order=True)
        mock_logger.error.assert_called_once_with(f"[{error_context.error_id}] Fail 3") # Final error logged

    def test_get_error_summary_empty(self, error_handler):
        summary = error_handler.get_error_summary()
        assert summary == {
            "total_errors": 0,
            "severity_counts": {},
            "category_counts": {},
            "recent_errors": []
        }

    @pytest.mark.asyncio
    @patch('concrete.error_handling.uuid.uuid4')
    @patch('concrete.error_handling.traceback.format_exc', return_value="mock_traceback")
    @patch('concrete.error_handling.traceback.extract_tb')
    async def test_get_error_summary_with_errors(self, mock_extract_tb, mock_format_exc, mock_uuid_func, error_handler, mock_time):
        # Setup mock uuid for multiple errors
        mock_uuid_instances = [MagicMock(), MagicMock(), MagicMock()]
        mock_uuid_instances[0].hex = "err1"
        mock_uuid_instances[1].hex = "err2"
        mock_uuid_instances[2].hex = "err3"
        mock_uuid_func.side_effect = mock_uuid_instances

        mock_frame = MagicMock()
        mock_frame.name = "summary_func"
        mock_frame.filename = "summary_module.py"
        mock_extract_tb.return_value = [mock_frame]

        # Simulate adding errors
        await error_handler.handle_error(ValueError("Error 1"), severity=ErrorSeverity.HIGH, category=ErrorCategory.BUSINESS_LOGIC)
        await error_handler.handle_error(ConnectionError("Error 2"), severity=ErrorSeverity.MEDIUM, category=ErrorCategory.NETWORK)
        await error_handler.handle_error(KeyError("Error 3"), severity=ErrorSeverity.HIGH, category=ErrorCategory.NETWORK)

        summary = error_handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["severity_counts"] == {
            "high": 2,
            "medium": 1
        }
        assert summary["category_counts"] == {
            "business_logic": 1,
            "network": 2
        }
        assert len(summary["recent_errors"]) == 3
        assert summary["recent_errors"][0]["error_id"] == "err_err3"
        assert summary["recent_errors"][1]["error_id"] == "err_err2"
        assert summary["recent_errors"][2]["error_id"] == "err_err1"

    @pytest.mark.asyncio
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump', new_callable=MagicMock)
    async def test_export_error_report_success(self, mock_json_dump, mock_open, error_handler, mock_time, tmp_path):
        # Simulate adding an error
        await error_handler.handle_error(ValueError("Test export"))
        
        output_file = tmp_path / "report.json"
        await error_handler.export_error_report(str(output_file))
        
        mock_open.assert_called_once_with(output_file, 'w')
        mock_json_dump.assert_called_once()
        assert len(error_handler.error_history) == 0 # History should be cleared after export

    @pytest.mark.asyncio
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    async def test_export_error_report_failure(self, mock_open, error_handler, mock_logger, mock_time):
        await error_handler.handle_error(ValueError("Test export failure"))
        
        with pytest.raises(IOError): # Expect the error to be re-raised
            await error_handler.export_error_report("/no/such/path/report.json")
        
        mock_logger.error.assert_called_once_with(f"Failed to export error report: Permission denied")
        assert len(error_handler.error_history) == 1 # History should not be cleared on failure

class TestGlobalFunctions:
    def test_get_error_handler(self):
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        assert handler1 is handler2 # Should return the same instance

    def test_get_error_handler_with_alert_callback(self):
        mock_callback = MagicMock()
        handler = get_error_handler(alert_callback=mock_callback)
        assert handler.alert_callback is mock_callback

    def test_reset_error_handler(self):
        handler1 = get_error_handler()
        reset_error_handler()
        handler2 = get_error_handler()
        assert handler1 is not handler2 # Should be a new instance after reset

class TestHandleErrorsDecorator:
    @pytest.mark.asyncio
    @patch('concrete.error_handling.get_error_handler')
    async def test_handle_errors_decorator_success(self, mock_get_error_handler, error_handler):
        mock_get_error_handler.return_value = error_handler

        @handle_errors(category=ErrorCategory.BUSINESS_LOGIC)
        async def successful_function():
            return "Success"

        result = await successful_function()
        assert result == "Success"
        assert len(error_handler.error_history) == 0 # No errors, so history should be empty

    @pytest.mark.asyncio
    @patch('concrete.error_handling.get_error_handler') # Patch the global getter
    async def test_handle_errors_decorator_failure(self, mock_get_error_handler, error_handler, mock_logger, mock_time):
        # Ensure the decorator uses our fixture's error_handler instance
        mock_get_error_handler.return_value = error_handler

        @handle_errors(category=ErrorCategory.NETWORK, severity=ErrorSeverity.CRITICAL)
        async def failing_function_with_retry():
            raise ConnectionError("Failed to connect")

        strategy = ErrorRecoveryStrategy(max_retries=1, backoff_factor=1.0) # Set max_retries to 1 to ensure one retry attempt
        error_handler.recovery_strategies[ErrorCategory.NETWORK] = strategy # Ensure the handler uses this strategy

        with pytest.raises(ConnectionError):
            await failing_function_with_retry()

        # After all retries, the error should be handled and stored
        assert len(error_handler.error_history) == 1 
        error_context = error_handler.error_history[0]

        mock_logger.error.assert_any_call(f"[{error_context.error_id}] Failed to connect") # Initial error
        # Expected warning from retry
        mock_logger.warning.assert_called_once_with(f"Attempt 1 failed, retrying in 1.0s: Failed to connect")
        mock_logger.debug.assert_called_once() # Debug log for full context

    @pytest.mark.asyncio
    @patch('concrete.error_handling.get_error_handler') # Patch the global getter
    async def test_handle_errors_decorator_with_recovery_strategy(self, mock_get_error_handler, error_handler, mock_logger, mock_time):
        mock_get_error_handler.return_value = error_handler # Ensure decorator uses this instance

        # Register a recovery strategy for NETWORK errors
        error_handler.recovery_strategies[ErrorCategory.NETWORK] = ErrorRecoveryStrategy(max_retries=1, backoff_factor=1.0)

        mock_operation = AsyncMock(side_effect=[ConnectionError("First try failed"), "Recovered!"])

        @handle_errors(category=ErrorCategory.NETWORK, severity=ErrorSeverity.HIGH)
        async def operation_with_recovery():
            return await mock_operation()

        result = await operation_with_recovery()
        assert result == "Recovered!"
        assert mock_operation.call_count == 2
        
        # No error should be in history as it was recovered
        assert len(error_handler.error_history) == 0
        
        # Check logging from the recovery strategy (warning for retry)
        expected_warning_calls = [
            call(f"Attempt 1 failed, retrying in 1.0s: First try failed")
        ]
        mock_logger.warning.assert_has_calls(expected_warning_calls, any_order=True) # Check logging from the recovery strategy
        mock_logger.error.assert_not_called() 