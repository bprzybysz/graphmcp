"""
Unit tests for Preview MCP Server Main Entry Point

Tests the main entry point functionality for the MCP server:
- Main function execution
- Server startup and configuration
- Error handling scenarios
- Logging setup
"""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Import the main module
import clients.preview_mcp.__main__ as main_module


class TestPreviewMCPMain:
    """Test cases for the preview MCP main entry point."""
    
    @pytest.mark.asyncio
    @patch('clients.preview_mcp.__main__.MCPWorkflowServer')
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    @patch('clients.preview_mcp.__main__.logging.basicConfig')
    async def test_main_function_success(self, mock_logging_config, mock_executor_class, mock_server_class):
        """Test successful main function execution."""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        mock_server = AsyncMock()
        mock_server.run = AsyncMock()
        mock_server_class.return_value = mock_server
        
        # Run main function
        await main_module.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once_with(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Verify executor was created
        mock_executor_class.assert_called_once()
        
        # Verify server was created with correct parameters
        mock_server_class.assert_called_once_with(mock_executor, log_level="INFO")
        
        # Verify server.run was called with stdio
        mock_server.run.assert_called_once_with("stdio")
    
    @pytest.mark.asyncio
    @patch('clients.preview_mcp.__main__.MCPWorkflowServer')
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    @patch('clients.preview_mcp.__main__.logging.basicConfig')
    @patch('clients.preview_mcp.__main__.logger')
    async def test_main_function_keyboard_interrupt(self, mock_logger, mock_logging_config, mock_executor_class, mock_server_class):
        """Test main function handling KeyboardInterrupt."""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        mock_server = AsyncMock()
        mock_server.run = AsyncMock(side_effect=KeyboardInterrupt())
        mock_server_class.return_value = mock_server
        
        # Run main function
        await main_module.main()
        
        # Verify shutdown message was logged
        mock_logger.info.assert_any_call("Server shutdown requested")
    
    @pytest.mark.asyncio
    @patch('clients.preview_mcp.__main__.MCPWorkflowServer')
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    @patch('clients.preview_mcp.__main__.logging.basicConfig')
    @patch('clients.preview_mcp.__main__.logger')
    @patch('clients.preview_mcp.__main__.sys.exit')
    async def test_main_function_general_exception(self, mock_sys_exit, mock_logger, mock_logging_config, mock_executor_class, mock_server_class):
        """Test main function handling general exceptions."""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        test_error = RuntimeError("Test server error")
        mock_server = AsyncMock()
        mock_server.run = AsyncMock(side_effect=test_error)
        mock_server_class.return_value = mock_server
        
        # Run main function
        await main_module.main()
        
        # Verify error was logged
        mock_logger.error.assert_called_once_with(f"Server error: {test_error}")
        
        # Verify sys.exit was called with error code
        mock_sys_exit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    @patch('clients.preview_mcp.__main__.MCPWorkflowServer')
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    @patch('clients.preview_mcp.__main__.logging.basicConfig')
    @patch('clients.preview_mcp.__main__.logger')
    async def test_main_function_logging_messages(self, mock_logger, mock_logging_config, mock_executor_class, mock_server_class):
        """Test that appropriate logging messages are generated."""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        mock_server = AsyncMock()
        mock_server.run = AsyncMock()
        mock_server_class.return_value = mock_server
        
        # Run main function
        await main_module.main()
        
        # Verify startup messages were logged
        expected_calls = [
            ("Starting Preview MCP Server...",),
            ("Preview MCP Server started successfully on stdio",)
        ]
        
        for expected_call in expected_calls:
            mock_logger.info.assert_any_call(*expected_call)
    
    def test_main_module_structure(self):
        """Test that the module has the proper structure for execution."""
        # Verify the module has the required structure for command-line execution
        # This is a safer test that doesn't try to exec the module
        assert hasattr(main_module, 'main')
        assert callable(main_module.main)
        
        # Verify that the main function is a coroutine function
        import inspect
        assert inspect.iscoroutinefunction(main_module.main)
    
    def test_module_imports(self):
        """Test that all required imports are available."""
        # Verify that the main module can import its dependencies
        assert hasattr(main_module, 'MCPWorkflowServer')
        assert hasattr(main_module, 'GraphMCPWorkflowExecutor') 
        assert hasattr(main_module, 'main')
        assert hasattr(main_module, 'logger')
        assert hasattr(main_module, 'asyncio')
        assert hasattr(main_module, 'logging')
        assert hasattr(main_module, 'sys')
    
    @pytest.mark.asyncio 
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    async def test_executor_creation_error(self, mock_executor_class):
        """Test handling of executor creation errors."""
        # Setup executor to raise an exception during creation
        mock_executor_class.side_effect = Exception("Executor creation failed")
        
        with patch('clients.preview_mcp.__main__.logger') as mock_logger, \
             patch('clients.preview_mcp.__main__.sys.exit') as mock_sys_exit:
            
            await main_module.main()
            
            # Verify error was logged and exit was called
            mock_logger.error.assert_called_once()
            mock_sys_exit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    @patch('clients.preview_mcp.__main__.MCPWorkflowServer')
    @patch('clients.preview_mcp.__main__.GraphMCPWorkflowExecutor')
    async def test_server_creation_error(self, mock_executor_class, mock_server_class):
        """Test handling of server creation errors."""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        # Setup server to raise an exception during creation
        mock_server_class.side_effect = Exception("Server creation failed")
        
        with patch('clients.preview_mcp.__main__.logger') as mock_logger, \
             patch('clients.preview_mcp.__main__.sys.exit') as mock_sys_exit:
            
            await main_module.main()
            
            # Verify error was logged and exit was called
            mock_logger.error.assert_called_once()
            mock_sys_exit.assert_called_once_with(1)


class TestModuleLevelExecution:
    """Test cases for module-level execution scenarios."""
    
    @patch('clients.preview_mcp.__main__.asyncio.run')
    def test_if_main_execution_path(self, mock_asyncio_run):
        """Test the if __name__ == '__main__' execution path."""
        # This test verifies the module structure but doesn't actually execute
        # the asyncio.run call since that would start the actual server
        
        # The key is that the module should have the proper structure
        # for command line execution
        assert hasattr(main_module, 'main')
        assert callable(main_module.main)
        
        # Verify that if we were to execute the main block,
        # it would call asyncio.run with the main function
        # (This is more of a structural test)
        import types
        assert isinstance(main_module.main, types.FunctionType) 