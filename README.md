# Healf Wellness Profiling Platform

A sophisticated AI-powered wellness profiling platform built with FastAPI, WebSockets, and Large Language Models. This platform provides real-time conversational interfaces for creating personalized wellness profiles through adaptive questioning.

## ✅ **Current Status: Fully Functional & Production Ready**

🎉 **All systems operational!** Complete wellness profiling workflow tested and working:
- ✅ **9/9 Tests Passing** - Complete test suite validated
- ✅ **Docker Integration** - Multi-container setup with MongoDB, Redis, and FastAPI
- ✅ **WebSocket Conversations** - Real-time wellness profiling demonstrated  
- ✅ **Database Persistence** - MongoDB integration with Redis caching
- ✅ **Production Ready** - Environment-specific configurations and Docker deployment

## 🚀 Features

- **Real-time Conversational Interface**: WebSocket-based communication for seamless user interaction
- **AI-Powered Question Generation**: Dynamic, context-aware questions using OpenAI's GPT-4 with intelligent fallbacks
- **Adaptive Profiling**: Intelligent question flow based on user responses
- **RESTful API**: Complete REST endpoints for profile management
- **Robust Architecture**: Clean separation with DAO, Service, and API layers
- **Database Integration**: MongoDB for persistent storage with Redis caching
- **Environment-Specific Configuration**: Separate configs for development, production, and testing
- **Docker Support**: Full containerization with multi-service orchestration
- **Comprehensive Validation**: Pydantic models with robust data validation
- **Health Monitoring**: Built-in health checks and connection monitoring

## 🎯 Quick Start Guide

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd healf

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Choose Your Setup Method

#### Option A: Docker Setup (Recommended for Development & Production)

**⚠️ Important**: Our application requires MongoDB and Redis for full functionality. Docker provides these services automatically.

```bash
# Generate Docker configuration
python scripts/generate_docker_config.py development

# Start all services (API + MongoDB + Redis)
docker-compose -f docker-compose.development.yml up --build
```

#### Option B: Local Development (Testing Only - Limited Functionality)

**⚠️ Note**: This setup is suitable for **testing only** as it lacks database services. The application will use fallback logic and won't persist data.

**Prerequisites**: This requires manually setting up MongoDB and Redis if you want full functionality:

```bash
# Option B1: Manual database setup (if you want full functionality)
# Install and start MongoDB (port 27017)
# Install and start Redis (port 6379)

# Option B2: Testing mode (fallback logic only)
# Start the application (uses development config with fallback logic)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Limitations of Local Setup**:
- ❌ No data persistence (profiles won't be saved)
- ❌ No Redis caching (slower performance)  
- ❌ Limited WebSocket session management
- ✅ API endpoints work with fallback responses
- ✅ LLM integration uses intelligent fallbacks
- ✅ Testing and validation still functional

### Step 4: Verify It's Working

#### For Docker Setup (Full Functionality):
```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response: {"status":"healthy","service":"healf-api","version":"1.0.0"}

# Test profile creation with persistence
curl -X POST http://localhost:8000/api/v1/profile/init/test_user

# Test profile retrieval (should work with data persistence)
curl http://localhost:8000/api/v1/profile/test_user

# View API documentation
open http://localhost:8000/docs
```

#### For Local Setup (Testing Mode):
```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response: {"status":"healthy","service":"healf-api","version":"1.0.0"}

# Test profile creation (will work but won't persist)
curl -X POST http://localhost:8000/api/v1/profile/init/test_user

# Note: Profile retrieval may fail or return fallback data without databases

# View API documentation
open http://localhost:8000/docs
```

### Step 5: Test the Complete Workflow

```bash
# Run the interactive wellness profiling demo
python tests/test_websocket_demo.py

# Run full test suite
pytest tests/ -v

# Expected: 9 tests passing (8 API + 1 WebSocket)
```

**🎉 That's it! Your wellness platform is now running on `http://localhost:8000`**

## 🏗️ Understanding the Architecture

### Project Structure Overview

```
healf/
├── app/                          # 🧠 Main application code
│   ├── api/                      # 🌐 API routes and WebSocket handlers
│   ├── config/                   # ⚙️ Environment-specific configurations
│   ├── dao/                      # 💾 Data Access Objects (Redis, MongoDB, LLM)
│   ├── models/                   # 📝 Pydantic data models
│   ├── services/                 # 🔧 Business logic services
│   └── utils/                    # 🛠️ Utility functions
├── templates/                    # 🐳 Docker configuration templates
├── scripts/                      # 🔨 Utility scripts (Docker generation)
├── tests/                        # 🧪 Test files (9 tests passing)
└── requirements.txt              # 📦 Python dependencies
```

### Module Explanations

#### 🌐 **API Layer** (`app/api/`)
**Purpose**: Handles external communication (REST + WebSocket)

- **`routes/profile.py`**: REST endpoints for profile CRUD operations
- **`routes/websocket.py`**: Real-time WebSocket handlers for conversational interface
- **Key Features**: 
  - RESTful profile management (init, get, update, delete, completion status)
  - Real-time bidirectional communication via WebSockets
  - Input validation and comprehensive error handling

#### 💾 **DAO Layer** (`app/dao/`)
**Purpose**: Data access abstraction and external service integration

- **`profile_dao.py`**: User profile data operations with MongoDB + Redis caching
- **`websocket_dao.py`**: WebSocket connection and session management via Redis
- **`llm_dao.py`**: Large Language Model integration (OpenAI) with intelligent fallback logic
- **`mongo_dao.py`**: Generic MongoDB operations (CRUD, aggregation, indexing)
- **`redis_dao.py`**: Generic Redis operations (caching, sessions, analytics)
- **Key Features**:
  - Hybrid storage strategy (Redis cache + MongoDB persistence)
  - Service abstraction with connection pooling
  - Intelligent fallbacks when external services fail
  - Automatic timestamping and data consistency

#### 🔧 **Service Layer** (`app/services/`)
**Purpose**: Business logic and orchestration

- **`profile_service.py`**: Profile management business logic and completion tracking
- **`question_service.py`**: Intelligent question generation and natural language answer processing
- **Key Features**:
  - Complex business workflows and profile completion logic
  - Data validation and transformation
  - Service coordination between DAOs

#### 📝 **Models** (`app/models/`)
**Purpose**: Data structure definitions and validation

- **`user_profile.py`**: User profile schema with validation rules and enums
- **`websocket_models.py`**: WebSocket message schemas
- **Key Features**:
  - Type-safe data structures with field validation
  - Automatic completion percentage calculation
  - Clear API contracts and documentation

#### ⚙️ **Configuration** (`app/config/`)
**Purpose**: Environment-specific settings management

- **`base.py`**: Common configuration base class
- **`development.py`**: Development environment (localhost databases, debug mode)
- **`production.py`**: Production environment (secure settings, multiple workers)  
- **`testing.py`**: Testing environment (in-memory storage, fast execution)
- **Key Features**:
  - Environment-specific database URLs and Docker configurations
  - Automatic environment variable reading for Docker deployments
  - Type-safe settings with no environment files needed

## 🧪 Testing Your Setup

### Run Complete Test Suite

```bash
# Run all tests (9 tests should pass)
pytest tests/ -v

# Expected output:
# tests/test_api.py::test_root_endpoint PASSED
# tests/test_api.py::test_health_endpoint PASSED  
# tests/test_api.py::test_profile_init PASSED
# tests/test_api.py::test_get_profile PASSED
# tests/test_api.py::test_get_nonexistent_profile PASSED
# tests/test_api.py::test_update_profile PASSED
# tests/test_api.py::test_profile_completion_status PASSED
# tests/test_api.py::test_delete_profile PASSED
# tests/test_websocket_demo.py::test_websocket_demo PASSED
# ========================= 9 passed in 0.51s =========================
```

### Test WebSocket Functionality (Interactive Demo)

```bash
# Run the interactive wellness profiling demo
python tests/test_websocket_demo.py

# Expected: Complete conversational flow demonstrating:
# 🤖 Assistant: To get started, could you tell me your age?
# 👤 You: I'm 28 years old
# [... conversation continues through all profile fields ...]
# 🎉 Congratulations! Your wellness profile is complete.
# 📊 Completion: 100.0%
```

### Validate Database Integration

```bash
# Test profile creation and retrieval
curl -X POST http://localhost:8000/api/v1/profile/init/test_user

# Test data persistence  
curl http://localhost:8000/api/v1/profile/test_user

# Check WebSocket statistics
curl http://localhost:8000/ws/stats
```

## 🐳 Docker Setup (Production-Ready)

### Full Multi-Service Deployment

```bash
# Generate Docker configuration for development
python scripts/generate_docker_config.py development

# Start complete stack (API + MongoDB + Redis)
docker-compose -f docker-compose.development.yml up --build

# Verify all services are running
docker-compose -f docker-compose.development.yml ps
```

### Multi-Environment Support

```bash
# Generate configuration for all environments
python scripts/generate_docker_config.py development
python scripts/generate_docker_config.py production  
python scripts/generate_docker_config.py testing

# Production deployment
docker-compose -f docker-compose.production.yml up --build

# Clean shutdown
docker-compose -f docker-compose.development.yml down -v
```

### Docker Service Architecture

**Services Deployed**:
- **`api`**: FastAPI application with hot reload (development) or multiple workers (production)
- **`mongo`**: MongoDB 7.x for persistent data storage with volume mounting
- **`redis`**: Redis 7.x for caching and session management
- **`healf-network`**: Isolated Docker network for service communication

**Features**:
- **Persistent Storage**: MongoDB and Redis data persisted in Docker volumes
- **Environment Variables**: Automatic service discovery via Docker networking
- **Health Checks**: Built-in container health monitoring
- **Resource Limits**: Memory and CPU limits configured per environment

## 📖 API Usage Examples

### REST API Workflow

```python
import requests

# 1. Initialize a new profile
response = requests.post("http://localhost:8000/api/v1/profile/init/user123")
print(response.json())
# {"status":"success","profile":{"user_id":"user123","completion_percentage":0.0,...}}

# 2. Update profile with structured data
update_data = {"age": 28, "activity_level": "active", "dietary_preference": "vegetarian"}
updated = requests.put("http://localhost:8000/api/v1/profile/user123", json=update_data)
print(updated.json())

# 3. Check completion status
completion = requests.get("http://localhost:8000/api/v1/profile/user123/completion")
print(completion.json())
# {"completion_percentage":42.86,"missing_fields":["gender","sleep_quality","stress_level","health_goals"],...}

# 4. Get complete profile
profile = requests.get("http://localhost:8000/api/v1/profile/user123")
print(f"Profile completion: {profile.json()['completion_percentage']}%")
```

### WebSocket Communication (Real-time Conversation)

```python
import asyncio
import websockets
import json

async def wellness_conversation():
    uri = "ws://localhost:8000/ws/user123"
    
    async with websockets.connect(uri) as websocket:
        # Receive initial question
        response = await websocket.recv()
        message = json.loads(response)
        print(f"🤖 Assistant: {message['data']['question']}")
        
        # Send natural language answer
        answer = {
            "type": "USER_ANSWER", 
            "data": {
                "answer": "I'm 28 years old and exercise regularly",
                "context": {"current_field": "age"}
            }
        }
        await websocket.send(json.dumps(answer))
        
        # Receive next question or completion
        response = await websocket.recv()
        next_message = json.loads(response)
        
        if next_message["type"] == "PROFILE_COMPLETE":
            print("🎉 Profile complete!")
        else:
            print(f"🤖 Next: {next_message['data']['question']}")

# Run the conversation
asyncio.run(wellness_conversation())
```

## 🔧 Advanced Configuration

### Environment Management

```bash
# Development mode (default) - localhost databases, debug logging
uvicorn app.main:app --reload

# Production mode - Docker service URLs, optimized performance
ENVIRONMENT=production uvicorn app.main:app --workers 4

# Testing mode - in-memory storage, fast execution
ENVIRONMENT=testing uvicorn app.main:app
```

### Database Configuration

**Development**:
- **MongoDB**: `mongodb://localhost:27017/healf_development` (or `mongodb://mongo:27017/healf_development` in Docker)
- **Redis**: `redis://localhost:6379` (or `redis://redis:6379` in Docker)

**Production**:
- **MongoDB**: `mongodb://mongo:27017/healf_production` with authentication
- **Redis**: `redis://redis:6379` with persistence enabled

**Features**:
- **Automatic Service Discovery**: Environment variables override localhost URLs in Docker
- **Connection Pooling**: Configured for production workloads
- **Data Persistence**: Docker volumes maintain data between container restarts

### Docker Template System

Advanced template-based Docker configuration:

```bash
# Generate specific configurations
python scripts/generate_docker_config.py development --clean
python scripts/generate_docker_config.py production --compose-only
python scripts/generate_docker_config.py testing --dockerfile-only

# Templates auto-configure:
# - Multi-stage builds (production)
# - Volume mounting (development) 
# - Resource limits (all environments)
# - Health checks and monitoring
```

## 🛠️ Development Commands

### Testing and Quality

```bash
# Run specific test suites
pytest tests/test_api.py -v                    # API tests only
pytest tests/test_websocket_demo.py -v         # WebSocket tests only

# Test with coverage
pytest tests/ --cov=app --cov-report=html
```

### Database Operations

```bash
# MongoDB operations (in Docker)
docker exec -it healf-mongo-1 mongosh
> show dbs
> use healf_development
> db.profiles.find()

# Redis operations (in Docker)  
docker exec -it healf-redis-1 redis-cli
> keys *
> get profile:user123
```

### Monitoring and Stats

```bash
# WebSocket connection statistics
curl http://localhost:8000/ws/stats
# {"active_connections":0,"total_sessions":5,"peak_connections":2,"last_updated":"2025-06-08T02:24:21Z"}

# Health check with detailed status
curl http://localhost:8000/health
# {"status":"healthy","service":"healf-api","version":"1.0.0"}

# API documentation
curl http://localhost:8000/docs
```

## 🚀 Deployment

### Local Production Testing

```bash
# Generate production Docker configuration
python scripts/generate_docker_config.py production

# Deploy with production settings
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
curl http://localhost:8000/health
docker-compose -f docker-compose.production.yml ps
```

### Production Features

- **Multi-stage Docker builds** for optimized image sizes
- **Non-root user** for enhanced container security
- **Multiple workers** for concurrent request handling
- **Resource limits** (memory: 512MB, CPU: 0.5 cores per service)
- **Health checks** with automatic restart policies
- **Persistent volumes** for data durability
- **Network isolation** for service security

## 📊 Performance & Scalability

### Current Capabilities

- **Concurrent Users**: Supports multiple simultaneous WebSocket connections
- **Database Performance**: MongoDB with indexing on user_id, completion_percentage, and compound fields
- **Caching Strategy**: Redis-first with MongoDB fallback reduces database load
- **Response Times**: Sub-100ms API responses for cached data

### Tested Scenarios

✅ **Stress Tested**: Multiple concurrent WebSocket conversations  
✅ **Data Persistence**: Profile data survives container restarts  
✅ **Error Recovery**: Graceful handling of database connection failures  
✅ **Cache Performance**: Significant speedup with Redis caching layer

## 🔒 Security Features

- **API Key Management**: Secure OpenAI key handling through environment configs
- **CORS Policies**: Environment-specific CORS configurations
- **Input Validation**: Comprehensive Pydantic model validation
- **Error Handling**: Secure error responses without sensitive data leakage
- **Container Security**: Non-root user execution in production containers
- **Network Isolation**: Docker network segmentation between services
- **Data Encryption**: HTTPS support ready for production deployment

## 🛣️ Roadmap

### Completed ✅
- [x] **Core API**: Complete REST endpoints for profile management
- [x] **WebSocket Integration**: Real-time conversational interface
- [x] **Database Layer**: MongoDB persistence with Redis caching
- [x] **Docker Support**: Multi-container orchestration
- [x] **Testing Suite**: Comprehensive test coverage (9/9 passing)
- [x] **Environment Management**: Development, production, testing configs
- [x] **LLM Integration**: OpenAI GPT-4 with intelligent fallbacks

### Planned 🚀
- [ ] **Authentication System**: User auth and session management
- [ ] **Multiple LLM Providers**: Anthropic Claude, Azure OpenAI support
- [ ] **Advanced Analytics**: Profile insights, completion trends, user behavior
- [ ] **Frontend Application**: React/Vue.js web interface
- [ ] **Mobile Integration**: React Native or Flutter app
- [ ] **Data Export**: PDF reports, CSV exports
- [ ] **Admin Dashboard**: User management and analytics interface

## 📄 Architecture Deep Dive

### Message Flow Architecture

```
1. WebSocket Connection → User connects to /ws/{user_id}
2. Profile Initialization → System creates/loads profile via ProfileDAO
3. Question Generation → LLM DAO generates contextual questions with fallbacks
4. Answer Processing → QuestionService extracts structured data from natural language
5. Profile Updates → ProfileDAO updates MongoDB + invalidates Redis cache
6. Completion Check → System calculates completion percentage
7. Next Question/Completion → Cycle continues until 100% complete
```

### Data Flow Diagram

```
Frontend Client
       ↕ WebSocket/HTTP
   API Layer (FastAPI)
       ↕
  Service Layer (Business Logic)
       ↕
   DAO Layer (Data Access)
    ↙        ↓        ↘
Redis     MongoDB    OpenAI
(Cache)   (Storage)   (LLM)
```

### Database Schema

**MongoDB Collection: `profiles`**
```json
{
  "_id": "ObjectId",
  "user_id": "string (unique)",
  "age": "int (13-120) | null",
  "gender": "string | null",
  "activity_level": "enum: sedentary|moderate|active | null", 
  "dietary_preference": "enum: vegan|vegetarian|no_preference | null",
  "sleep_quality": "enum: poor|average|good | null",
  "stress_level": "enum: low|medium|high | null",
  "health_goals": "string | null",
  "completion_percentage": "float (0.0-100.0)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Redis Cache Structure**:
- `profile:{user_id}` → Cached profile data (1 hour TTL)
- `session:{user_id}` → WebSocket session data
- `context:{user_id}` → Conversation context
- `websocket_stats` → Global connection statistics

## 🤝 Contributing

1. **Fork the repository** and create a feature branch
2. **Follow existing patterns**: Use the DAO/Service/API layer architecture
3. **Add comprehensive tests**: Maintain 100% test coverage for new features
4. **Update documentation**: Keep README and docstrings current
5. **Test Docker integration**: Ensure changes work in containerized environment
6. **Submit pull request** with clear description of changes

### Development Setup

```bash
# Setup for contribution
git clone https://github.com/your-fork/healf.git
cd healf
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run tests before making changes
pytest tests/ -v

# Make your changes...

# Test your changes
pytest tests/ -v
python tests/test_websocket_demo.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions and support:
- **Issues**: Open an issue in the GitHub repository
- **API Documentation**: Visit `/docs` endpoint when server is running
- **Docker Templates**: Check `templates/README.md` for Docker configuration details
- **Architecture Questions**: Review this README's architecture section

---

**Built with ❤️ for better wellness experiences**  
*Fully tested and production-ready wellness profiling platform*
