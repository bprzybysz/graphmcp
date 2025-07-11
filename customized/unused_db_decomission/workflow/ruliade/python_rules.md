# Python Rules for Database Decommissioning

## Python Application Code Rules

### ORM Model and Migration Handling
- **Review ORM Models**: Check Django models, SQLAlchemy models, or other ORM definitions
- **Migration Dependencies**: Analyze migration chains and dependencies before removing database references
- **Model Relationships**: Identify foreign key relationships and cascading effects
- **Abstract Base Classes**: Review inheritance hierarchies that might reference the database

### Database Connection Management
- **Connection Strings**: Update or remove database connection configurations
- **Connection Pools**: Review connection pooling configurations and timeouts
- **Database URLs**: Check environment-specific database URL configurations
- **Credential Management**: Remove database credentials from configuration files

### Django-Specific Rules
- **Settings Files**: Review `settings.py` for database configurations and references
- **Model Imports**: Check for model imports across the application
- **Admin Interface**: Remove admin registrations for decommissioned database models
- **Management Commands**: Review custom management commands that access the database
- **Template References**: Check Django templates for model field references
- **URL Patterns**: Review URL patterns that might reference model-based views

### SQLAlchemy-Specific Rules
- **Engine Configuration**: Review SQLAlchemy engine and session configurations
- **Declarative Base**: Check base class definitions and metadata
- **Table Definitions**: Review explicit table definitions and relationships
- **Query Objects**: Identify direct SQL queries and ORM queries
- **Alembic Migrations**: Review Alembic migration history and dependencies

### Database Query Patterns
- **Raw SQL Queries**: Identify and review raw SQL embedded in Python code
- **Query Builders**: Check dynamic query construction and parameterization
- **Stored Procedure Calls**: Review calls to database stored procedures
- **Database Functions**: Check usage of database-specific functions

### Testing and Test Data
- **Test Fixtures**: Remove test fixtures that create database test data
- **Mock Configurations**: Update mocks and patches for database interactions
- **Integration Tests**: Modify tests that depend on database state
- **Test Database Setup**: Review test database configuration and teardown

### Application Configuration
- **Environment Variables**: Check for database-related environment variables
- **Configuration Classes**: Review configuration classes and factory patterns
- **Feature Flags**: Check feature flags that might control database access
- **Logging Configuration**: Update database query logging configurations

### Data Processing and ETL
- **Data Pipeline Code**: Review ETL scripts and data processing workflows
- **Batch Processing**: Check scheduled jobs and batch processing scripts
- **Data Export/Import**: Review data migration and synchronization scripts
- **Analytics Queries**: Check reporting and analytics query definitions

### API and Web Framework Rules
- **Flask Applications**: Review Flask app configurations and database extensions
- **FastAPI Dependencies**: Check dependency injection for database sessions
- **API Serializers**: Review serializer classes that expose database fields
- **WebSocket Handlers**: Check real-time handlers that query the database

### Monitoring and Observability
- **Health Check Endpoints**: Update health checks that test database connectivity
- **Metrics Collection**: Review database-related metrics and monitoring code
- **Error Handling**: Update error handling for database connection failures
- **Alerting Logic**: Review alerting rules based on database metrics

### Security and Access Control
- **Authentication Backends**: Review custom authentication that queries the database
- **Permission Systems**: Check permission decorators and access control logic
- **Session Management**: Review session storage and user state management
- **Audit Logging**: Check audit trails that log database operations

### Documentation and Comments
- **Docstrings**: Update docstrings that reference database schemas or tables
- **Inline Comments**: Review code comments that explain database interactions
- **Type Hints**: Update type annotations for database-related objects
- **API Documentation**: Update API docs that reference database fields

### Dependencies and Requirements
- **Database Drivers**: Remove database driver dependencies from requirements files
- **ORM Dependencies**: Review ORM and database-related package dependencies
- **Migration Tools**: Check migration tool dependencies and configurations
- **Testing Libraries**: Review database testing library dependencies

### Deployment and Infrastructure
- **Database Initialization**: Review database setup scripts and initialization code
- **Container Configurations**: Check Docker configurations for database connections
- **Service Discovery**: Review service discovery configurations for database endpoints
- **Environment Setup**: Check development and staging environment setup scripts

### Quality Gates for Python Code
- **Code Coverage**: Ensure test coverage for modified database interaction code
- **Static Analysis**: Run linting tools to check for unused imports and references
- **Type Checking**: Use mypy or similar tools to validate type consistency
- **Security Scanning**: Check for database credential exposure in code

### Rollback Strategy
- **Code Rollback Plan**: Maintain rollback procedures for Python code changes
- **Database Migration Rollback**: Plan for reversing database schema changes
- **Feature Flag Rollback**: Use feature flags to quickly disable database features
- **Deployment Rollback**: Ensure application can rollback to previous database configurations

### Communication and Coordination
- **Team Notifications**: Inform development teams about database decommissioning timeline
- **Documentation Updates**: Update architectural documentation and runbooks
- **Change Management**: Follow change management processes for database modifications
- **Stakeholder Approval**: Ensure proper approvals for database decommissioning changes 