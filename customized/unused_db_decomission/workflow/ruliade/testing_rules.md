# Testing Rules (Pytest + Coverage + AsyncIO)

## Test Structure and Organization

### Test File Organization
- **Follow naming conventions**
  ```
  tests/
  ├── conftest.py              # Shared fixtures
  ├── unit/
  │   ├── test_models.py       # Unit tests for models
  │   ├── test_services.py     # Unit tests for business logic
  │   └── test_utils.py        # Unit tests for utilities
  ├── integration/
  │   ├── test_api.py          # API integration tests
  │   ├── test_database.py     # Database integration tests
  │   └── test_external.py     # External service tests
  └── e2e/
      ├── test_workflows.py    # End-to-end workflows
      └── test_user_journeys.py
  ```

- **Use descriptive test names**
  ```python
  def test_user_creation_with_valid_data_should_return_user_object():
      pass
  
  def test_user_creation_with_invalid_email_should_raise_validation_error():
      pass
  
  def test_user_deletion_should_mark_user_as_inactive():
      pass
  ```

### Test Categories and Markers
- **Register custom markers in pytest.ini**
  ```ini
  [tool:pytest]
  markers =
      unit: Unit tests
      integration: Integration tests
      e2e: End-to-end tests
      slow: Slow tests (> 1 second)
      external: Tests that require external services
      database: Tests that require database
  ```

- **Use markers consistently**
  ```python
  import pytest
  
  @pytest.mark.unit
  def test_calculate_total():
      assert calculate_total([1, 2, 3]) == 6
  
  @pytest.mark.integration
  @pytest.mark.database
  def test_user_repository_save():
      user = User(name="Test")
      saved_user = user_repository.save(user)
      assert saved_user.id is not None
  
  @pytest.mark.e2e
  @pytest.mark.slow
  def test_complete_user_workflow():
      # Full workflow test
      pass
  ```

## Fixtures and Setup

### Fixture Patterns
- **Use scope appropriately**
  ```python
  import pytest
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  
  @pytest.fixture(scope="session")
  def engine():
      """Database engine for the entire test session"""
      return create_engine("sqlite:///:memory:")
  
  @pytest.fixture(scope="function")
  def db_session(engine):
      """Fresh database session for each test"""
      Session = sessionmaker(bind=engine)
      session = Session()
      try:
          yield session
      finally:
          session.rollback()
          session.close()
  
  @pytest.fixture
  def sample_user():
      """Sample user data for tests"""
      return User(
          name="Test User",
          email="test@example.com",
          age=25
      )
  ```

- **Create factory fixtures**
  ```python
  @pytest.fixture
  def user_factory():
      """Factory to create users with different attributes"""
      def _create_user(**kwargs):
          defaults = {
              "name": "Test User",
              "email": "test@example.com",
              "age": 25
          }
          defaults.update(kwargs)
          return User(**defaults)
      return _create_user
  
  def test_user_creation(user_factory):
      admin_user = user_factory(name="Admin", is_admin=True)
      regular_user = user_factory(age=30)
      assert admin_user.is_admin
      assert regular_user.age == 30
  ```

### Configuration Fixtures
- **Environment setup**
  ```python
  @pytest.fixture(autouse=True)
  def setup_test_environment(monkeypatch):
      """Automatically set up test environment for all tests"""
      monkeypatch.setenv("ENVIRONMENT", "test")
      monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
      monkeypatch.setenv("DEBUG", "true")
  
  @pytest.fixture
  def mock_external_api(monkeypatch):
      """Mock external API calls"""
      def mock_get_user_data(user_id):
          return {"id": user_id, "name": "Mock User"}
      
      monkeypatch.setattr("services.external_api.get_user_data", mock_get_user_data)
  ```

## Parametrized Testing

### Test Parametrization
- **Test multiple inputs with parametrize**
  ```python
  import pytest
  
  @pytest.mark.parametrize("input_value,expected", [
      (0, 0),
      (1, 1),
      (2, 4),
      (3, 9),
      (-1, 1),
      (-2, 4),
  ])
  def test_square_function(input_value, expected):
      assert square(input_value) == expected
  
  @pytest.mark.parametrize("email", [
      "invalid-email",
      "@example.com",
      "user@",
      "user@.com",
      "",
  ])
  def test_invalid_email_validation(email):
      with pytest.raises(ValidationError):
          validate_email(email)
  ```

- **Parameterize fixtures**
  ```python
  @pytest.fixture(params=["postgresql", "mysql", "sqlite"])
  def database_config(request):
      """Test with different database configurations"""
      configs = {
          "postgresql": {"driver": "postgresql", "host": "localhost"},
          "mysql": {"driver": "mysql", "host": "localhost"},
          "sqlite": {"driver": "sqlite", "host": ":memory:"}
      }
      return configs[request.param]
  
  def test_database_connection(database_config):
      # This test will run 3 times with different configs
      connection = create_connection(database_config)
      assert connection is not None
  ```

## Async Testing

### AsyncIO Test Support
- **Test async functions**
  ```python
  import pytest
  import asyncio
  
  @pytest.mark.asyncio
  async def test_async_function():
      result = await async_function()
      assert result == "expected_value"
  
  @pytest.mark.asyncio
  async def test_async_context_manager():
      async with async_context_manager() as resource:
          result = await resource.process()
          assert result is not None
  ```

- **Async fixtures**
  ```python
  @pytest.fixture
  async def async_client():
      """Async HTTP client for testing"""
      async with httpx.AsyncClient() as client:
          yield client
  
  @pytest.fixture
  async def async_db_session():
      """Async database session"""
      async with async_sessionmaker() as session:
          yield session
          await session.rollback()
  
  @pytest.mark.asyncio
  async def test_async_api_call(async_client):
      response = await async_client.get("/api/users")
      assert response.status_code == 200
  ```

## Mocking and Patching

### Mock External Dependencies
- **Use pytest-mock for mocking**
  ```python
  def test_service_with_external_dependency(mocker):
      # Mock external service
      mock_api = mocker.patch('services.external_api.get_data')
      mock_api.return_value = {"status": "success"}
      
      # Test service that uses external API
      result = my_service.process_data()
      
      # Assertions
      mock_api.assert_called_once()
      assert result["status"] == "success"
  ```

- **Mock with side effects**
  ```python
  def test_retry_mechanism(mocker):
      mock_api = mocker.patch('services.api.call_external')
      
      # First call fails, second succeeds
      mock_api.side_effect = [
          ConnectionError("Network error"),
          {"data": "success"}
      ]
      
      result = service_with_retry.fetch_data()
      
      assert mock_api.call_count == 2
      assert result["data"] == "success"
  ```

### Database Mocking
- **Mock database queries**
  ```python
  def test_user_repository_find_by_email(mocker):
      mock_session = mocker.Mock()
      mock_query = mock_session.query.return_value
      mock_filter = mock_query.filter.return_value
      mock_filter.first.return_value = User(id=1, email="test@example.com")
      
      repo = UserRepository(mock_session)
      user = repo.find_by_email("test@example.com")
      
      assert user.id == 1
      assert user.email == "test@example.com"
      mock_session.query.assert_called_once_with(User)
  ```

## Test Data Management

### Test Data Creation
- **Use factories for complex objects**
  ```python
  import factory
  from factory import Faker
  
  class UserFactory(factory.Factory):
      class Meta:
          model = User
      
      name = Faker('name')
      email = Faker('email')
      age = factory.LazyFunction(lambda: random.randint(18, 80))
      created_at = Faker('date_time')
  
  def test_user_service():
      users = UserFactory.build_batch(5)
      result = user_service.process_users(users)
      assert len(result) == 5
  ```

- **Create realistic test data**
  ```python
  @pytest.fixture
  def realistic_user_data():
      return {
          "name": "John Doe",
          "email": "john.doe@company.com",
          "age": 35,
          "department": "Engineering",
          "join_date": datetime(2020, 1, 15),
          "skills": ["Python", "SQL", "Docker"],
          "address": {
              "street": "123 Main St",
              "city": "San Francisco",
              "state": "CA",
              "zip": "94105"
          }
      }
  ```

## Error Testing

### Exception Testing
- **Test expected exceptions**
  ```python
  def test_divide_by_zero_raises_exception():
      with pytest.raises(ZeroDivisionError):
          divide(10, 0)
  
  def test_invalid_input_raises_specific_error():
      with pytest.raises(ValueError, match="Invalid input format"):
          parse_input("invalid-format")
  
  def test_exception_details():
      with pytest.raises(ValidationError) as exc_info:
          validate_user_data({"age": -1})
      
      assert "age must be positive" in str(exc_info.value)
      assert exc_info.value.error_count == 1
  ```

### Error Recovery Testing
- **Test error handling and recovery**
  ```python
  def test_service_handles_network_errors_gracefully(mocker):
      mock_api = mocker.patch('services.api.fetch_data')
      mock_api.side_effect = ConnectionError("Network unavailable")
      
      result = resilient_service.get_data_with_fallback()
      
      # Should return cached data or default values
      assert result is not None
      assert result["source"] == "cache"
  ```

## Performance Testing

### Performance Benchmarks
- **Use pytest-benchmark for performance tests**
  ```python
  def test_algorithm_performance(benchmark):
      data = list(range(10000))
      result = benchmark(sort_algorithm, data)
      assert len(result) == 10000
  
  def test_database_query_performance(benchmark, db_session):
      def query_users():
          return db_session.query(User).filter(User.active == True).all()
      
      users = benchmark(query_users)
      assert len(users) > 0
  ```

### Memory Usage Testing
- **Test memory consumption**
  ```python
  import psutil
  import os
  
  def test_memory_usage_within_limits():
      process = psutil.Process(os.getpid())
      initial_memory = process.memory_info().rss
      
      # Perform memory-intensive operation
      large_data = process_large_dataset()
      
      final_memory = process.memory_info().rss
      memory_increase = final_memory - initial_memory
      
      # Assert memory increase is reasonable (e.g., < 100MB)
      assert memory_increase < 100 * 1024 * 1024
  ```

## Integration Testing

### API Integration Tests
- **Test API endpoints with real HTTP calls**
  ```python
  from fastapi.testclient import TestClient
  
  def test_user_crud_workflow():
      client = TestClient(app)
      
      # Create user
      create_response = client.post("/users", json={
          "name": "Test User",
          "email": "test@example.com"
      })
      assert create_response.status_code == 201
      user_id = create_response.json()["id"]
      
      # Get user
      get_response = client.get(f"/users/{user_id}")
      assert get_response.status_code == 200
      assert get_response.json()["name"] == "Test User"
      
      # Update user
      update_response = client.put(f"/users/{user_id}", json={
          "name": "Updated User"
      })
      assert update_response.status_code == 200
      
      # Delete user
      delete_response = client.delete(f"/users/{user_id}")
      assert delete_response.status_code == 204
  ```

### Database Integration Tests
- **Test with real database transactions**
  ```python
  @pytest.mark.integration
  def test_user_repository_transaction(db_session):
      repo = UserRepository(db_session)
      
      # Create user
      user = User(name="Test User", email="test@example.com")
      saved_user = repo.save(user)
      db_session.commit()
      
      # Verify user exists
      found_user = repo.find_by_id(saved_user.id)
      assert found_user is not None
      assert found_user.name == "Test User"
      
      # Update user
      found_user.name = "Updated User"
      repo.save(found_user)
      db_session.commit()
      
      # Verify update
      updated_user = repo.find_by_id(saved_user.id)
      assert updated_user.name == "Updated User"
  ```

## Test Configuration

### Pytest Configuration
- **Configure pytest.ini**
  ```ini
  [tool:pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = 
      --strict-markers
      --strict-config
      --verbose
      --tb=short
      --cov=src
      --cov-report=term-missing
      --cov-report=html
      --cov-fail-under=80
  markers =
      unit: Unit tests
      integration: Integration tests
      e2e: End-to-end tests
      slow: Slow tests
      external: Tests requiring external services
  ```

### Test Environment Variables
- **Set up test-specific configuration**
  ```python
  # conftest.py
  import os
  import pytest
  
  @pytest.fixture(scope="session", autouse=True)
  def setup_test_environment():
      """Set up test environment variables"""
      os.environ.update({
          "ENVIRONMENT": "test",
          "DATABASE_URL": "sqlite:///:memory:",
          "REDIS_URL": "redis://localhost:6379/1",
          "LOG_LEVEL": "DEBUG",
          "TESTING": "true"
      })
  ```

## Coverage and Quality

### Coverage Configuration
- **Configure coverage in .coveragerc**
  ```ini
  [run]
  source = src
  omit = 
      */tests/*
      */venv/*
      */migrations/*
      */settings/*
      */manage.py
  
  [report]
  exclude_lines =
      pragma: no cover
      def __repr__
      raise AssertionError
      raise NotImplementedError
      if __name__ == .__main__.:
  
  [html]
  directory = htmlcov
  ```

### Quality Checks
- **Ensure high-quality tests**
  ```python
  # Test naming should be descriptive
  def test_user_creation_with_duplicate_email_should_raise_integrity_error():
      pass
  
  # Tests should be independent
  def test_user_creation():
      # Don't depend on other test state
      user = create_fresh_user()
      assert user.id is not None
  
  # Tests should be fast
  @pytest.mark.slow
  def test_complex_workflow():
      # Mark slow tests appropriately
      pass
  
  # Tests should have clear assertions
  def test_user_validation():
      result = validate_user(user_data)
      assert result.is_valid is True
      assert len(result.errors) == 0
      assert result.user.email == "test@example.com"
  ```

## Continuous Integration

### CI/CD Integration
- **Run different test suites**
  ```bash
  # Fast tests for pull requests
  pytest -m "unit and not slow"
  
  # Full test suite for main branch
  pytest
  
  # Integration tests only
  pytest -m integration
  
  # With coverage reporting
  pytest --cov=src --cov-report=xml
  ```

### Test Reporting
- **Generate test reports**
  ```bash
  # JUnit XML for CI systems
  pytest --junitxml=test-results.xml
  
  # HTML coverage report
  pytest --cov=src --cov-report=html
  
  # JSON report for analysis
  pytest --json-report --json-report-file=test-report.json
  ``` 