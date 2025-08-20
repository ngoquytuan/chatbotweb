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