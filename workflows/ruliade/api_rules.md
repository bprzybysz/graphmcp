# API Development Rules (FastAPI + Pydantic)

## FastAPI Application Architecture

### Dependency Injection
- **Use `Depends()` for reusable dependencies**
  ```python
  from fastapi import Depends, HTTPException
  
  def get_db() -> Session:
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  
  @app.get("/users/{user_id}")
  async def get_user(user_id: int, db: Session = Depends(get_db)):
      return db.query(User).filter(User.id == user_id).first()
  ```

- **Create dependency hierarchies**
  ```python
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      # Validate token and return user
      return user
  
  async def get_admin_user(user: User = Depends(get_current_user)):
      if not user.is_admin:
          raise HTTPException(status_code=403, detail="Admin required")
      return user
  ```

### Route Organization
- **Use `APIRouter` for modular applications**
  ```python
  from fastapi import APIRouter
  
  router = APIRouter(prefix="/api/v1", tags=["users"])
  
  @router.get("/users/")
  async def list_users():
      return {"users": []}
  
  @router.post("/users/")
  async def create_user(user: UserCreate):
      return {"user": user}
  
  # In main app
  app.include_router(router)
  ```

- **Group related endpoints logically**
  ```python
  # users.py
  users_router = APIRouter(prefix="/users", tags=["users"])
  
  # auth.py  
  auth_router = APIRouter(prefix="/auth", tags=["authentication"])
  
  # admin.py
  admin_router = APIRouter(prefix="/admin", tags=["admin"])
  ```

### Request/Response Models

#### Pydantic Model Patterns
- **Use separate models for input/output**
  ```python
  from pydantic import BaseModel, Field
  from typing import Optional
  from datetime import datetime
  
  class UserBase(BaseModel):
      email: str = Field(..., description="User email address")
      name: str = Field(..., min_length=1, max_length=100)
  
  class UserCreate(UserBase):
      password: str = Field(..., min_length=8)
  
  class UserUpdate(BaseModel):
      email: Optional[str] = None
      name: Optional[str] = None
  
  class UserResponse(UserBase):
      id: int
      created_at: datetime
      is_active: bool = True
      
      class Config:
          from_attributes = True
  ```

- **Use model validation methods**
  ```python
  from pydantic import validator, root_validator
  
  class UserModel(BaseModel):
      email: str
      age: int
      
      @validator('email')
      def validate_email(cls, v):
          if '@' not in v:
              raise ValueError('Invalid email format')
          return v.lower()
      
      @root_validator
      def validate_user(cls, values):
          email = values.get('email')
          age = values.get('age')
          if age < 18 and 'student' not in email:
              raise ValueError('Users under 18 must have student email')
          return values
  ```

### Error Handling
- **Use HTTPException for API errors**
  ```python
  from fastapi import HTTPException, status
  
  @app.get("/users/{user_id}")
  async def get_user(user_id: int):
      user = await get_user_by_id(user_id)
      if not user:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="User not found"
          )
      return user
  ```

- **Create custom exception handlers**
  ```python
  from fastapi.responses import JSONResponse
  
  class CustomException(Exception):
      def __init__(self, message: str):
          self.message = message
  
  @app.exception_handler(CustomException)
  async def custom_exception_handler(request, exc):
      return JSONResponse(
          status_code=400,
          content={"detail": exc.message}
      )
  ```

### Async Patterns
- **Use async/await for I/O operations**
  ```python
  import aiohttp
  import asyncpg
  
  @app.get("/external-data")
  async def get_external_data():
      async with aiohttp.ClientSession() as session:
          async with session.get("https://api.example.com/data") as response:
              data = await response.json()
      return data
  
  @app.get("/db-data")
  async def get_db_data():
      conn = await asyncpg.connect("postgresql://...")
      try:
          result = await conn.fetch("SELECT * FROM users")
          return [dict(row) for row in result]
      finally:
          await conn.close()
  ```

- **Handle background tasks**
  ```python
  from fastapi import BackgroundTasks
  
  def send_email(email: str, message: str):
      # Send email logic
      pass
  
  @app.post("/send-notification/")
  async def send_notification(
      email: str, 
      background_tasks: BackgroundTasks
  ):
      background_tasks.add_task(send_email, email, "Welcome!")
      return {"message": "Notification will be sent"}
  ```

## WebSocket Support

### WebSocket Endpoints
- **Implement WebSocket connections**
  ```python
  from fastapi import WebSocket, WebSocketDisconnect
  
  class ConnectionManager:
      def __init__(self):
          self.active_connections: List[WebSocket] = []
      
      async def connect(self, websocket: WebSocket):
          await websocket.accept()
          self.active_connections.append(websocket)
      
      def disconnect(self, websocket: WebSocket):
          self.active_connections.remove(websocket)
      
      async def broadcast(self, message: str):
          for connection in self.active_connections:
              await connection.send_text(message)
  
  manager = ConnectionManager()
  
  @app.websocket("/ws/{client_id}")
  async def websocket_endpoint(websocket: WebSocket, client_id: int):
      await manager.connect(websocket)
      try:
          while True:
              data = await websocket.receive_text()
              await manager.broadcast(f"Client {client_id}: {data}")
      except WebSocketDisconnect:
          manager.disconnect(websocket)
  ```

## Authentication and Security

### OAuth2 Implementation
- **Implement JWT authentication**
  ```python
  from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
  from jose import JWTError, jwt
  from passlib.context import CryptContext
  
  SECRET_KEY = "your-secret-key"
  ALGORITHM = "HS256"
  
  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  
  def create_access_token(data: dict):
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
      to_encode.update({"exp": expire})
      return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          username: str = payload.get("sub")
          if username is None:
              raise HTTPException(status_code=401, detail="Invalid token")
      except JWTError:
          raise HTTPException(status_code=401, detail="Invalid token")
      return username
  ```

### Input Validation and Security
- **Validate and sanitize inputs**
  ```python
  from pydantic import validator, constr
  
  class UserInput(BaseModel):
      username: constr(regex=r'^[a-zA-Z0-9_]+$', min_length=3, max_length=20)
      email: EmailStr
      
      @validator('username')
      def username_alphanumeric(cls, v):
          assert v.isalnum() or '_' in v, 'Username must be alphanumeric'
          return v
  ```

## Middleware and CORS

### Custom Middleware
- **Implement request logging middleware**
  ```python
  import time
  from fastapi import Request
  
  @app.middleware("http")
  async def add_process_time_header(request: Request, call_next):
      start_time = time.time()
      response = await call_next(request)
      process_time = time.time() - start_time
      response.headers["X-Process-Time"] = str(process_time)
      return response
  ```

- **Configure CORS properly**
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "https://yourapp.com"],
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE"],
      allow_headers=["*"],
  )
  ```

## Data Serialization and Validation

### Advanced Pydantic Usage
- **Use custom validators and serializers**
  ```python
  from pydantic import BaseModel, validator, Field
  from typing import List, Dict, Any
  
  class DataModel(BaseModel):
      items: List[Dict[str, Any]]
      metadata: Dict[str, str] = Field(default_factory=dict)
      
      @validator('items', pre=True)
      def parse_items(cls, v):
          if isinstance(v, str):
              import json
              return json.loads(v)
          return v
      
      def dict(self, **kwargs):
          # Custom serialization
          d = super().dict(**kwargs)
          d['processed_at'] = datetime.utcnow().isoformat()
          return d
  ```

- **Handle complex data types**
  ```python
  from pydantic import BaseModel, Json
  from typing import Union, Literal
  from datetime import datetime
  from uuid import UUID
  
  class EventModel(BaseModel):
      id: UUID
      event_type: Literal["create", "update", "delete"]
      timestamp: datetime
      payload: Json[Dict[str, Any]]
      
      class Config:
          json_encoders = {
              datetime: lambda v: v.isoformat(),
              UUID: lambda v: str(v)
          }
  ```

## Testing API Endpoints

### Test Client Usage
- **Use TestClient for endpoint testing**
  ```python
  from fastapi.testclient import TestClient
  import pytest
  
  client = TestClient(app)
  
  def test_create_user():
      response = client.post(
          "/users/",
          json={"email": "test@example.com", "name": "Test User"}
      )
      assert response.status_code == 201
      assert response.json()["email"] == "test@example.com"
  
  def test_get_user_not_found():
      response = client.get("/users/999")
      assert response.status_code == 404
  ```

- **Test with authentication**
  ```python
  def test_protected_endpoint():
      # Get token
      response = client.post("/token", data={"username": "test", "password": "test"})
      token = response.json()["access_token"]
      
      # Use token
      response = client.get(
          "/protected",
          headers={"Authorization": f"Bearer {token}"}
      )
      assert response.status_code == 200
  ```

### Mock Dependencies
- **Override dependencies for testing**
  ```python
  def override_get_db():
      try:
          db = TestingSessionLocal()
          yield db
      finally:
          db.close()
  
  app.dependency_overrides[get_db] = override_get_db
  
  def test_with_db():
      response = client.get("/users/")
      assert response.status_code == 200
  ```

## Performance Optimization

### Caching Strategies
- **Implement response caching**
  ```python
  from functools import lru_cache
  import redis
  
  redis_client = redis.Redis(host='localhost', port=6379, db=0)
  
  @lru_cache(maxsize=100)
  def get_expensive_data(param: str):
      # Expensive computation
      return result
  
  @app.get("/cached-data/{param}")
  async def cached_endpoint(param: str):
      cache_key = f"data:{param}"
      cached = redis_client.get(cache_key)
      if cached:
          return json.loads(cached)
      
      result = get_expensive_data(param)
      redis_client.setex(cache_key, 300, json.dumps(result))  # 5 min cache
      return result
  ```

### Database Optimization
- **Use connection pooling**
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.pool import QueuePool
  
  engine = create_engine(
      DATABASE_URL,
      poolclass=QueuePool,
      pool_size=10,
      max_overflow=20,
      pool_pre_ping=True
  )
  ```

## Documentation and OpenAPI

### API Documentation
- **Customize OpenAPI schema**
  ```python
  app = FastAPI(
      title="My API",
      description="A sample API with comprehensive documentation",
      version="1.0.0",
      docs_url="/docs",
      redoc_url="/redoc"
  )
  
  @app.get("/items/", tags=["items"], summary="List all items")
  async def list_items(
      skip: int = Query(0, description="Number of items to skip"),
      limit: int = Query(100, le=100, description="Maximum number of items to return")
  ):
      """
      Retrieve a list of items with pagination.
      
      - **skip**: Number of items to skip for pagination
      - **limit**: Maximum number of items to return (max 100)
      """
      return {"items": []}
  ```

## Configuration Management

### Environment-based Configuration
- **Use Pydantic for settings**
  ```python
  from pydantic import BaseSettings
  
  class Settings(BaseSettings):
      database_url: str
      secret_key: str
      debug: bool = False
      redis_host: str = "localhost"
      redis_port: int = 6379
      
      class Config:
          env_file = ".env"
  
  settings = Settings()
  ```

### Feature Flags
- **Implement feature toggles**
  ```python
  class FeatureFlags(BaseSettings):
      enable_new_feature: bool = False
      enable_beta_endpoint: bool = False
      
      class Config:
          env_prefix = "FEATURE_"
  
  flags = FeatureFlags()
  
  @app.get("/beta-feature")
  async def beta_feature():
      if not flags.enable_beta_endpoint:
          raise HTTPException(status_code=404, detail="Not found")
      return {"message": "Beta feature enabled"}
  ``` 