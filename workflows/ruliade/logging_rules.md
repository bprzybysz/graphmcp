# Logging Rules (Structlog + Rich + Python Logging)

## Structured Logging Setup

### Structlog Configuration
- **Configure structlog at application startup**
  ```python
  import structlog
  import logging
  from rich.logging import RichHandler
  
  def configure_logging():
      """Configure structured logging for the application"""
      # Configure standard library logging
      logging.basicConfig(
          level=logging.INFO,
          format="%(message)s",
          handlers=[RichHandler(rich_tracebacks=True)]
      )
      
      # Configure structlog
      structlog.configure(
          processors=[
              structlog.stdlib.filter_by_level,
              structlog.stdlib.add_logger_name,
              structlog.stdlib.add_log_level,
              structlog.stdlib.PositionalArgumentsFormatter(),
              structlog.processors.TimeStamper(fmt="iso"),
              structlog.processors.StackInfoRenderer(),
              structlog.processors.format_exc_info,
              structlog.processors.UnicodeDecoder(),
              structlog.processors.JSONRenderer()
          ],
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          wrapper_class=structlog.stdlib.BoundLogger,
          cache_logger_on_first_use=True,
      )
  
  # Call during application initialization
  configure_logging()
  logger = structlog.get_logger()
  ```

### Environment-Specific Configuration
- **Different configs for development vs production**
  ```python
  import os
  from structlog.dev import ConsoleRenderer
  
  def configure_logging():
      """Configure logging based on environment"""
      is_development = os.getenv("ENVIRONMENT") == "development"
      
      processors = [
          structlog.stdlib.filter_by_level,
          structlog.stdlib.add_logger_name,
          structlog.stdlib.add_log_level,
          structlog.stdlib.PositionalArgumentsFormatter(),
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.StackInfoRenderer(),
          structlog.processors.format_exc_info,
          structlog.processors.UnicodeDecoder(),
      ]
      
      if is_development:
          # Human-readable console output for development
          processors.append(ConsoleRenderer(colors=True))
      else:
          # JSON output for production (log aggregation)
          processors.append(structlog.processors.JSONRenderer())
      
      structlog.configure(
          processors=processors,
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          wrapper_class=structlog.stdlib.BoundLogger,
          cache_logger_on_first_use=True,
      )
  ```

## Logging Patterns

### Structured Context Logging
- **Use structured context throughout application**
  ```python
  import structlog
  
  logger = structlog.get_logger()
  
  def process_user_data(user_id: int, data: dict):
      # Bind context to logger
      log = logger.bind(user_id=user_id, operation="process_user_data")
      
      log.info("Starting user data processing", data_size=len(data))
      
      try:
          # Process data
          result = validate_data(data)
          log.info("Data validation completed", 
                  validation_result=result.is_valid,
                  error_count=len(result.errors))
          
          if result.is_valid:
              saved_data = save_user_data(user_id, data)
              log.info("User data saved successfully", 
                      record_id=saved_data.id,
                      fields_updated=len(data))
              return saved_data
          else:
              log.warning("Data validation failed", 
                         errors=result.errors)
              raise ValidationError("Invalid data")
              
      except Exception as e:
          log.error("Failed to process user data", 
                   error=str(e), 
                   error_type=type(e).__name__)
          raise
  ```

### Request Tracing
- **Add request context to all logs**
  ```python
  import uuid
  from contextvars import ContextVar
  
  request_id_var: ContextVar[str] = ContextVar("request_id")
  
  class RequestContextMiddleware:
      def __init__(self, app):
          self.app = app
      
      async def __call__(self, scope, receive, send):
          if scope["type"] == "http":
              request_id = str(uuid.uuid4())
              request_id_var.set(request_id)
              
              # Add to response headers
              async def send_wrapper(message):
                  if message["type"] == "http.response.start":
                      headers = list(message.get("headers", []))
                      headers.append((b"x-request-id", request_id.encode()))
                      message["headers"] = headers
                  await send(message)
              
              await self.app(scope, receive, send_wrapper)
          else:
              await self.app(scope, receive, send)
  
  # Custom processor to add request ID
  def add_request_id(logger, method_name, event_dict):
      try:
          request_id = request_id_var.get()
          event_dict["request_id"] = request_id
      except LookupError:
          pass
      return event_dict
  
  # Add to structlog processors
  processors = [..., add_request_id, ...]
  ```

### Error Logging with Context
- **Log errors with comprehensive context**
  ```python
  def handle_database_error(operation: str, **context):
      """Handle database errors with structured logging"""
      log = logger.bind(operation=operation, **context)
      
      try:
          # Database operation
          yield
      except sqlalchemy.exc.IntegrityError as e:
          log.error("Database integrity constraint violated",
                   error_code=e.code,
                   error_detail=str(e.orig),
                   constraint=getattr(e.orig, 'constraint', None))
          raise
      except sqlalchemy.exc.OperationalError as e:
          log.error("Database operational error",
                   error_code=e.code,
                   error_detail=str(e.orig),
                   database_url=e.connection_invalidated)
          raise
      except Exception as e:
          log.error("Unexpected database error",
                   error_type=type(e).__name__,
                   error_detail=str(e))
          raise
  
  # Usage
  with handle_database_error("user_creation", user_id=123):
      create_user_in_db(user_data)
  ```

## Performance and Monitoring

### Performance Logging
- **Log performance metrics**
  ```python
  import time
  from functools import wraps
  
  def log_performance(operation_name: str = None):
      """Decorator to log function performance"""
      def decorator(func):
          @wraps(func)
          def wrapper(*args, **kwargs):
              log = logger.bind(
                  function=func.__name__,
                  operation=operation_name or func.__name__
              )
              
              start_time = time.time()
              log.debug("Operation started")
              
              try:
                  result = func(*args, **kwargs)
                  duration = time.time() - start_time
                  
                  log.info("Operation completed successfully",
                          duration_seconds=round(duration, 3),
                          result_type=type(result).__name__)
                  return result
                  
              except Exception as e:
                  duration = time.time() - start_time
                  log.error("Operation failed",
                           duration_seconds=round(duration, 3),
                           error=str(e),
                           error_type=type(e).__name__)
                  raise
          return wrapper
      return decorator
  
  # Usage
  @log_performance("data_processing")
  def process_large_dataset(data):
      # Processing logic
      return processed_data
  ```

### Resource Usage Logging
- **Monitor resource consumption**
  ```python
  import psutil
  import os
  
  def log_resource_usage(logger, method_name, event_dict):
      """Add resource usage to log events"""
      process = psutil.Process(os.getpid())
      
      event_dict["resource_usage"] = {
          "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
          "cpu_percent": process.cpu_percent(),
          "open_files": len(process.open_files()),
          "connections": len(process.connections())
      }
      return event_dict
  
  # Add to critical operations
  @log_performance("memory_intensive_operation")
  def process_large_file(file_path):
      log = logger.bind(file_path=file_path)
      # Add resource usage processor temporarily
      with structlog.configure(processors=[..., log_resource_usage, ...]):
          log.info("Starting large file processing")
          # Process file
          log.info("File processing completed")
  ```

## Security and Sensitive Data

### Sensitive Data Filtering
- **Filter sensitive information from logs**
  ```python
  import re
  
  def filter_sensitive_data(logger, method_name, event_dict):
      """Remove sensitive data from log events"""
      sensitive_fields = {
          "password", "secret", "token", "api_key", 
          "credit_card", "ssn", "social_security"
      }
      
      def sanitize_value(key, value):
          if isinstance(key, str) and any(field in key.lower() for field in sensitive_fields):
              return "***REDACTED***"
          
          if isinstance(value, str):
              # Redact credit card numbers
              value = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                           '****-****-****-****', value)
              # Redact emails (partial)
              value = re.sub(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
                           r'\1***@\2', value)
          
          return value
      
      def sanitize_dict(d):
          if isinstance(d, dict):
              return {k: sanitize_value(k, sanitize_dict(v)) for k, v in d.items()}
          elif isinstance(d, list):
              return [sanitize_dict(item) for item in d]
          else:
              return d
      
      return sanitize_dict(event_dict)
  
  # Add to processor chain
  processors = [..., filter_sensitive_data, ...]
  ```

### Audit Logging
- **Create audit trails for sensitive operations**
  ```python
  def audit_log(action: str, resource_type: str, resource_id: str = None):
      """Create audit log entries"""
      def decorator(func):
          @wraps(func)
          def wrapper(*args, **kwargs):
              audit_logger = structlog.get_logger("audit")
              
              log_context = {
                  "action": action,
                  "resource_type": resource_type,
                  "resource_id": resource_id,
                  "function": func.__name__,
                  "timestamp": time.time()
              }
              
              # Add user context if available
              try:
                  user_id = get_current_user_id()
                  log_context["user_id"] = user_id
              except:
                  pass
              
              audit_logger.info("Audit event", **log_context)
              
              try:
                  result = func(*args, **kwargs)
                  audit_logger.info("Audit event completed", 
                                   success=True, **log_context)
                  return result
              except Exception as e:
                  audit_logger.error("Audit event failed",
                                    success=False,
                                    error=str(e),
                                    **log_context)
                  raise
          return wrapper
      return decorator
  
  # Usage
  @audit_log("delete", "user")
  def delete_user(user_id: int):
      # Deletion logic
      pass
  ```

## Application-Specific Logging

### Database Operation Logging
- **Log database operations with details**
  ```python
  class DatabaseLogger:
      def __init__(self):
          self.logger = structlog.get_logger("database")
      
      def log_query(self, query: str, params: dict = None, execution_time: float = None):
          """Log database query execution"""
          log_data = {
              "query_type": self._extract_query_type(query),
              "table": self._extract_table_name(query),
              "execution_time_ms": round(execution_time * 1000, 2) if execution_time else None
          }
          
          if params:
              log_data["param_count"] = len(params)
          
          self.logger.debug("Database query executed", **log_data)
      
      def log_transaction(self, operation: str, affected_rows: int = None):
          """Log database transaction"""
          self.logger.info("Database transaction",
                          operation=operation,
                          affected_rows=affected_rows)
      
      def _extract_query_type(self, query: str) -> str:
          return query.strip().split()[0].upper()
      
      def _extract_table_name(self, query: str) -> str:
          # Simple table name extraction
          words = query.strip().split()
          if len(words) > 2:
              return words[2].strip('`"[]')
          return "unknown"
  
  # Usage in SQLAlchemy
  db_logger = DatabaseLogger()
  
  @event.listens_for(Engine, "before_cursor_execute")
  def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
      conn.info.setdefault('query_start_time', []).append(time.time())
  
  @event.listens_for(Engine, "after_cursor_execute")
  def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
      total = time.time() - conn.info['query_start_time'].pop(-1)
      db_logger.log_query(statement, parameters, total)
  ```

### API Request/Response Logging
- **Log API interactions**
  ```python
  import json
  from fastapi import Request, Response
  
  async def log_requests(request: Request, call_next):
      """Middleware to log API requests and responses"""
      log = logger.bind(
          method=request.method,
          url=str(request.url),
          path=request.url.path,
          client_ip=request.client.host
      )
      
      # Log request
      log.info("API request received",
              headers=dict(request.headers),
              query_params=dict(request.query_params))
      
      # Capture request body if needed
      if request.method in ["POST", "PUT", "PATCH"]:
          body = await request.body()
          if body and len(body) < 10000:  # Log small bodies only
              try:
                  body_json = json.loads(body)
                  log.debug("Request body", body=body_json)
              except:
                  log.debug("Request body (non-JSON)", body_size=len(body))
      
      start_time = time.time()
      
      # Process request
      response = await call_next(request)
      
      # Log response
      duration = time.time() - start_time
      log.info("API request completed",
              status_code=response.status_code,
              duration_seconds=round(duration, 3),
              response_size=response.headers.get("content-length"))
      
      return response
  ```

## Error Handling and Debugging

### Exception Logging
- **Comprehensive exception logging**
  ```python
  def log_exception(logger_name: str = None):
      """Decorator for comprehensive exception logging"""
      def decorator(func):
          @wraps(func)
          def wrapper(*args, **kwargs):
              log = structlog.get_logger(logger_name or func.__module__)
              log = log.bind(function=func.__name__)
              
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  # Log with full context
                  log.error("Exception occurred",
                           error_type=type(e).__name__,
                           error_message=str(e),
                           function_args=args[:5],  # Limit arg logging
                           function_kwargs=list(kwargs.keys()),
                           traceback=traceback.format_exc())
                  raise
          return wrapper
      return decorator
  ```

### Debug Logging
- **Conditional debug logging**
  ```python
  def debug_log_enabled():
      """Check if debug logging is enabled"""
      return os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
  
  def conditional_debug(func):
      """Only log debug info if debug is enabled"""
      @wraps(func)
      def wrapper(*args, **kwargs):
          if debug_log_enabled():
              log = logger.bind(function=func.__name__)
              log.debug("Function called",
                       args_count=len(args),
                       kwargs_keys=list(kwargs.keys()))
          
          result = func(*args, **kwargs)
          
          if debug_log_enabled():
              log.debug("Function returned",
                       result_type=type(result).__name__)
          
          return result
      return wrapper
  ```

## Configuration and Best Practices

### Log Level Management
- **Dynamic log level configuration**
  ```python
  def set_log_level(level: str):
      """Dynamically set log level"""
      numeric_level = getattr(logging, level.upper(), None)
      if not isinstance(numeric_level, int):
          raise ValueError(f'Invalid log level: {level}')
      
      # Update standard library logging
      logging.getLogger().setLevel(numeric_level)
      
      # Update structlog filter
      structlog.configure(
          processors=[
              structlog.stdlib.filter_by_level,
              # ... other processors
          ]
      )
  
  # Environment-based configuration
  log_level = os.getenv("LOG_LEVEL", "INFO")
  set_log_level(log_level)
  ```

### Log Rotation and Management
- **Configure log rotation**
  ```python
  import logging.handlers
  
  def setup_file_logging(log_file: str, max_bytes: int = 10*1024*1024, backup_count: int = 5):
      """Set up rotating file logging"""
      file_handler = logging.handlers.RotatingFileHandler(
          log_file,
          maxBytes=max_bytes,
          backupCount=backup_count
      )
      
      formatter = logging.Formatter(
          '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )
      file_handler.setFormatter(formatter)
      
      # Add to root logger
      logging.getLogger().addHandler(file_handler)
  
  # Usage
  if os.getenv("ENVIRONMENT") == "production":
      setup_file_logging("/var/log/app/application.log")
  ```

### Logging Testing
- **Test logging behavior**
  ```python
  import pytest
  from structlog.testing import LogCapture
  
  def test_user_creation_logging():
      with LogCapture() as cap:
          create_user("test@example.com")
      
      # Check that expected log entries were created
      assert len(cap.entries) == 2
      assert cap.entries[0]["event"] == "Creating new user"
      assert cap.entries[0]["email"] == "test@example.com"
      assert cap.entries[1]["event"] == "User created successfully"
  
  def test_error_logging():
      with LogCapture() as cap:
          with pytest.raises(ValidationError):
              create_user("invalid-email")
      
      # Check error was logged
      error_logs = [entry for entry in cap.entries if entry["log_level"] == "error"]
      assert len(error_logs) == 1
      assert "validation" in error_logs[0]["event"].lower()
  ```

## Integration with Monitoring Systems

### Metrics Integration
- **Expose logs as metrics**
  ```python
  from prometheus_client import Counter, Histogram
  
  # Define metrics
  log_counter = Counter('application_logs_total', 'Total log entries', ['level', 'module'])
  error_counter = Counter('application_errors_total', 'Total errors', ['error_type'])
  
  def metrics_processor(logger, method_name, event_dict):
      """Add metrics to log processing"""
      level = event_dict.get('level', 'unknown')
      module = event_dict.get('logger', 'unknown')
      
      # Increment log counter
      log_counter.labels(level=level, module=module).inc()
      
      # Count errors by type
      if level == 'error' and 'error_type' in event_dict:
          error_counter.labels(error_type=event_dict['error_type']).inc()
      
      return event_dict
  
  # Add to processor chain
  processors = [..., metrics_processor, ...]
  ``` 