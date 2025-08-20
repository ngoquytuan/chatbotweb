Tôi sẽ tạo các file source code cho backend theo kiến trúc trong tài liệu. Đây là cấu trúc project và các file chính:

## Cấu trúc Project

```
backend/
├── main.py
├── requirements.txt
├── Dockerfile
├── engines/
│   ├── __init__.py
│   ├── intent_classifier.py
│   ├── faiss_manager.py
│   ├── llm_provider.py
│   └── response_generator.py
├── utils/
│   ├── __init__.py
│   ├── analytics.py
│   ├── cache.py
│   └── monitoring.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── db/
│   └── init.sql
├── data/
│   └── faiss_indices/
└── logs/
```

## File chính

### requirements.txt

```txt
# Web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
slowapi==0.1.9

# Database
psycopg2-binary==2.9.9
redis==5.0.1

# Machine Learning & RAG
faiss-cpu==1.7.4
sentence-transformers==2.2.2
numpy==1.24.4

# HTTP clients
aiohttp==3.9.1
requests==2.31.0

# Data processing
pydantic==2.5.0
python-multipart==0.0.6

# System monitoring
psutil==5.9.6

# Environment
python-dotenv==1.0.0

# Utilities
python-json-logger==2.0.7
```

### main.py

```python
"""
Enterprise Chatbot API - Main FastAPI Application
"""
import os
import time
import logging
import asyncio
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import models and schemas
from models.schemas import ChatRequest, ChatResponse, PageContext
from engines.intent_classifier import IntentClassifier
from engines.faiss_manager import FAISSCollectionManager
from engines.llm_provider import MultiLLMProvider
from engines.response_generator import ContextualResponseGenerator
from utils.analytics import ChatAnalytics
from utils.cache import CacheManager
from utils.monitoring import PerformanceMonitor

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI
app = FastAPI(
    title="Enterprise Chatbot API",
    description="Advanced RAG-based chatbot with context-aware routing",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
    redoc_url="/api/redoc" if os.getenv('ENVIRONMENT') != 'production' else None
)

# Store startup time
app.state.start_time = time.time()

# Middleware setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted hosts
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["yourdomain.com", "api.yourdomain.com", "www.yourdomain.com"]
    )

# Redis setup
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

# Initialize components
intent_classifier = IntentClassifier()
faiss_manager = FAISSCollectionManager()
llm_provider = MultiLLMProvider()
response_generator = ContextualResponseGenerator()
analytics = ChatAnalytics(
    postgres_url=os.getenv('DATABASE_URL'),
    redis_client=redis_client
)
cache_manager = CacheManager(redis_client)
performance_monitor = PerformanceMonitor()


@app.on_startup
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting up Enterprise Chatbot API...")
    
    try:
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise
    
    try:
        # Load FAISS indices
        await faiss_manager.initialize_collections()
        await faiss_manager.load_all_collections()
        logger.info("FAISS collections initialized")
    except Exception as e:
        logger.error(f"FAISS initialization failed: {e}")
        raise
    
    try:
        # Initialize LLM providers
        await llm_provider.initialize_providers()
        intent_classifier.set_llm_provider(llm_provider)
        response_generator.set_llm_provider(llm_provider)
        response_generator.set_faiss_manager(faiss_manager)
        logger.info("LLM providers initialized")
    except Exception as e:
        logger.error(f"LLM provider initialization failed: {e}")
        raise
    
    logger.info("Enterprise Chatbot API startup complete")


@app.on_shutdown
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Enterprise Chatbot API...")
    
    try:
        await llm_provider.cleanup()
        redis_client.close()
        logger.info("Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def get_remote_address(request: Request) -> str:
    """Get client IP address with proxy support"""
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",")[0].strip()
    elif real_ip := request.headers.get("x-real-ip"):
        return real_ip
    else:
        return request.client.host if request.client else "unknown"


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """Main chat endpoint with full RAG pipeline"""
    start_time = time.time()
    remote_addr = get_remote_address(http_request)
    
    try:
        # Input validation
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(request.message) > 1000:
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")
        
        logger.info(f"Processing chat request from session {request.session_id}")
        
        # Check cache first
        cache_key = cache_manager.generate_cache_key(request.message, request.context)
        cached_response = await cache_manager.get_cached_response(cache_key)
        
        if cached_response:
            logger.info(f"Cache hit for session {request.session_id}")
            # Still track for analytics
            background_tasks.add_task(
                analytics.track_conversation,
                request.session_id,
                request.message,
                cached_response,
                remote_addr
            )
            return cached_response
        
        # Stage 1: Intent Classification + Context Analysis
        intent_result = await intent_classifier.analyze_query(
            query=request.message,
            context=request.context,
            history=request.history
        )
        
        logger.info(f"Intent classified: {intent_result.intent.value}, Target: {intent_result.target_product}")
        
        # Stage 2: Document Routing + Vector Search
        relevant_docs = await faiss_manager.search_targeted_collections(
            queries=intent_result.refined_queries,
            collections=intent_result.target_collections,
            context_filter={
                "product": intent_result.target_product,
                "section": request.context.section
            },
            top_k=8
        )
        
        logger.info(f"Found {len(relevant_docs)} relevant documents")
        
        # Stage 3: Response Generation
        response_data = await response_generator.generate_response(
            user_query=request.message,
            intent=intent_result,
            context=request.context,
            relevant_docs=relevant_docs,
            history=request.history
        )
        
        # Build final response
        chat_response = ChatResponse(
            response=response_data["content"],
            session_id=request.session_id,
            sources=response_data["sources"],
            confidence=response_data["confidence"],
            intent=intent_result.intent.value,
            target_product=intent_result.target_product,
            processing_time=time.time() - start_time
        )
        
        # Background tasks
        background_tasks.add_task(
            cache_manager.cache_response,
            cache_key,
            chat_response,
            ttl=3600  # 1 hour cache
        )
        
        background_tasks.add_task(
            analytics.track_conversation,
            request.session_id,
            request.message,
            chat_response,
            remote_addr
        )
        
        logger.info(f"Chat response generated in {chat_response.processing_time:.2f}s")
        return chat_response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chat error for session {request.session_id}: {error_msg}")
        
        # Return fallback response
        return ChatResponse(
            response="Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng liên hệ support@yourdomain.com để được hỗ trợ.",
            session_id=request.session_id,
            confidence=0.0,
            processing_time=time.time() - start_time,
            intent="error",
            sources=[]
        )


@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - app.state.start_time,
        "components": {}
    }
    
    # Check FAISS collections
    try:
        collections_status = await faiss_manager.health_check()
        health_status["components"]["faiss"] = {
            "status": "healthy" if collections_status["all_loaded"] else "degraded",
            "details": collections_status
        }
    except Exception as e:
        health_status["components"]["faiss"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check LLM providers
    try:
        provider_status = await llm_provider.health_check()
        health_status["components"]["llm_providers"] = provider_status
        
        if provider_status["overall_status"] != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["llm_providers"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/api/analytics/dashboard")
async def analytics_dashboard():
    """Analytics endpoint for monitoring"""
    try:
        dashboard_data = await analytics.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Analytics temporarily unavailable")


@app.get("/api/monitoring/metrics")
async def get_monitoring_metrics():
    """Get system monitoring metrics"""
    try:
        system_metrics = await performance_monitor.get_system_metrics()
        
        # Get application metrics
        faiss_status = await faiss_manager.health_check()
        llm_status = await llm_provider.health_check()
        cache_stats = cache_manager.get_stats()
        
        return {
            'system': system_metrics,
            'application': {
                'uptime': time.time() - app.state.start_time,
                'faiss_status': faiss_status,
                'llm_providers': llm_status,
                'cache_stats': cache_stats
            }
        }
    except Exception as e:
        logger.error(f"Monitoring metrics error: {e}")
        raise HTTPException(status_code=500, detail="Monitoring temporarily unavailable")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") != "production",
        workers=1 if os.getenv("ENVIRONMENT") != "production" else 4
    )
```

### models/schemas.py

```python
"""
Pydantic models for request/response schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime


class PageContext(BaseModel):
    url: str
    title: str
    product: Optional[str] = None
    section: Optional[str] = None
    content_preview: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL format')
        return v


class ChatMessage(BaseModel):
    content: str
    sender: str
    timestamp: int
    context: Optional[PageContext] = None
    
    @validator('sender')
    def validate_sender(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError('Sender must be user or assistant')
        return v


class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: PageContext
    history: List[ChatMessage] = []
    user_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        return v.strip()
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid session ID')
        return v


class SourceReference(BaseModel):
    content: str
    collection: str
    score: float
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[SourceReference] = []
    confidence: float = 0.0
    intent: Optional[str] = None
    target_product: Optional[str] = None
    processing_time: float = 0.0
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, v))


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float
    components: Dict[str, Any]


class AnalyticsSummary(BaseModel):
    total_conversations: int
    avg_confidence: float
    avg_processing_time: float
    top_intents: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]


class SystemMetrics(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_stats: Dict[str, int]
```

Tôi sẽ tiếp tục với các file engine trong comment tiếp theo để tránh response quá dài.