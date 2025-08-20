# Kiến Trúc Chatbot Enterprise-Grade - Complete System Design

## Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  React App (CDN/Vercel)                                                    │
│  ├── Context Manager (Page tracking, User session)                         │
│  ├── Chatbot Component (UI/UX, Real-time messaging)                        │
│  └── Analytics Tracker (User behavior, Chat metrics)                       │
└─────────────────┬───────────────────────────────────────────────────────────┘
                  │ HTTPS/WebSocket
┌─────────────────▼───────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Nginx/Cloudflare (Load Balancer, Rate Limiting, SSL)                      │
│  ├── Authentication & Authorization                                         │
│  ├── Request Routing & Load Balancing                                       │
│  └── DDoS Protection & Caching                                             │
└─────────────────┬───────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────────────────┐
│                           CHATBOT API LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Application (Docker Container)                                    │
│  ├── Intent Classification Engine                                          │
│  ├── Document Router & FAISS Manager                                       │
│  ├── Multi-LLM Provider Handler                                            │
│  └── Response Generation & Optimization                                    │
└─────────────────┬───────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────────────────┐
│                           DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  FAISS Collections (Local/Redis)   │   PostgreSQL (Metadata)              │
│  ├── product_a_features.index      │   ├── user_sessions                  │
│  ├── product_b_features.index      │   ├── chat_history                   │
│  ├── pricing_info.index            │   ├── analytics_data                 │
│  ├── warranty_support.index        │   └── document_metadata              │
│  └── company_contact.index         │                                       │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

## Chi Tiết Implementation

### 1. Frontend Architecture (React)

```typescript
// src/types/chatbot.ts
export interface PageContext {
  url: string;
  title: string;
  product?: string;
  section?: string;
  content_preview?: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: number;
  context?: PageContext;
  sources?: string[];
  confidence?: number;
}

export interface ChatSession {
  session_id: string;
  user_id?: string;
  messages: ChatMessage[];
  context: PageContext;
  created_at: number;
}
```

```tsx
// src/components/ChatbotManager.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { PageContext, ChatMessage, ChatSession } from '../types/chatbot';

class ChatbotContextManager {
  private currentContext: PageContext;
  private sessionId: string;
  
  constructor() {
    this.sessionId = this.generateSessionId();
    this.currentContext = this.getCurrentPageContext();
    this.setupContextTracking();
  }
  
  getCurrentPageContext(): PageContext {
    return {
      url: window.location.href,
      title: document.title,
      product: this.extractProductFromURL(),
      section: this.getCurrentSection(),
      content_preview: this.extractPageContent()
    };
  }
  
  extractProductFromURL(): string | undefined {
    const path = window.location.pathname;
    const productMatch = path.match(/\/products\/([^\/]+)/);
    return productMatch ? productMatch[1] : undefined;
  }
  
  getCurrentSection(): string | undefined {
    const hash = window.location.hash;
    if (hash) return hash.substring(1);
    
    // Detect section by scroll position
    const sections = document.querySelectorAll('[id]');
    for (const section of sections) {
      const rect = section.getBoundingClientRect();
      if (rect.top <= 100 && rect.bottom >= 100) {
        return section.id;
      }
    }
    return undefined;
  }
  
  extractPageContent(): string {
    // Extract key content from page (limit to 500 chars)
    const mainContent = document.querySelector('main, .content, #content');
    if (mainContent) {
      return mainContent.textContent?.substring(0, 500) || '';
    }
    return document.body.textContent?.substring(0, 500) || '';
  }
  
  setupContextTracking() {
    // Track navigation changes
    window.addEventListener('popstate', () => {
      this.currentContext = this.getCurrentPageContext();
    });
    
    // Track hash changes  
    window.addEventListener('hashchange', () => {
      this.currentContext = this.getCurrentPageContext();
    });
    
    // Track scroll for section detection
    let scrollTimeout: NodeJS.Timeout;
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const newSection = this.getCurrentSection();
        if (newSection !== this.currentContext.section) {
          this.currentContext = { ...this.currentContext, section: newSection };
        }
      }, 200);
    });
  }
  
  getContext(): PageContext {
    return { ...this.currentContext };
  }
  
  getSessionId(): string {
    return this.sessionId;
  }
  
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const ChatbotManager: React.FC = () => {
  const [contextManager] = useState(() => new ChatbotContextManager());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  const sendMessage = useCallback(async (content: string) => {
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      content,
      sender: 'user',
      timestamp: Date.now(),
      context: contextManager.getContext()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          session_id: contextManager.getSessionId(),
          context: contextManager.getContext(),
          history: messages.slice(-5) // Last 5 messages for context
        })
      });
      
      const data = await response.json();
      
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        content: data.response,
        sender: 'assistant',
        timestamp: Date.now(),
        sources: data.sources,
        confidence: data.confidence
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        content: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.',
        sender: 'assistant',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, [contextManager, messages]);
  
  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 z-50"
      >
        <MessageCircleIcon className="w-6 h-6 mx-auto" />
      </button>
      
      {/* Chat Interface */}
      {isOpen && (
        <div className="fixed bottom-20 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl z-50 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 bg-blue-600 text-white rounded-t-lg flex justify-between items-center">
            <h3 className="font-semibold">AI Assistant</h3>
            <button onClick={() => setIsOpen(false)}>
              <XIcon className="w-5 h-5" />
            </button>
          </div>
          
          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto">
            {messages.map(message => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && <TypingIndicator />}
          </div>
          
          {/* Input */}
          <ChatInput onSendMessage={sendMessage} disabled={isTyping} />
        </div>
      )}
    </>
  );
};
```

### 2. Backend Architecture (FastAPI)

```python
# main.py - FastAPI Application
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import asyncio
import logging
import redis
import json
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI
app = FastAPI(
    title="Enterprise Chatbot API",
    description="Advanced RAG-based chatbot with context-aware routing",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "http://localhost:3000"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "api.yourdomain.com", "localhost"]
)

# Redis for caching and session management
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Pydantic models
class PageContext(BaseModel):
    url: str
    title: str
    product: Optional[str] = None
    section: Optional[str] = None
    content_preview: Optional[str] = None

class ChatMessage(BaseModel):
    content: str
    sender: str
    timestamp: int
    context: Optional[PageContext] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: PageContext
    history: List[ChatMessage] = []
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    intent: Optional[str] = None
    target_product: Optional[str] = None
    processing_time: float = 0.0

# Import our custom modules
from .engines.intent_classifier import IntentClassifier
from .engines.faiss_manager import FAISSCollectionManager
from .engines.llm_provider import MultiLLMProvider
from .engines.response_generator import ContextualResponseGenerator
from .utils.analytics import ChatAnalytics
from .utils.cache import CacheManager

# Initialize engines
intent_classifier = IntentClassifier()
faiss_manager = FAISSCollectionManager()
llm_provider = MultiLLMProvider()
response_generator = ContextualResponseGenerator()
analytics = ChatAnalytics()
cache_manager = CacheManager(redis_client)

@app.on_startup
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting up chatbot API...")
    
    # Load FAISS indices
    await faiss_manager.load_all_collections()
    
    # Initialize LLM providers
    await llm_provider.initialize_providers()
    
    logger.info("Chatbot API startup complete")

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # Rate limiting per IP
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    remote_addr: str = Depends(get_remote_address)
):
    """Main chat endpoint with full RAG pipeline"""
    start_time = time.time()
    
    try:
        # Input validation
        if len(request.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(request.message) > 1000:
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")
        
        # Check cache first
        cache_key = cache_manager.generate_cache_key(request.message, request.context)
        cached_response = await cache_manager.get_cached_response(cache_key)
        
        if cached_response:
            logger.info(f"Cache hit for session {request.session_id}")
            return cached_response
        
        # Stage 1: Intent Classification + Context Analysis
        intent_result = await intent_classifier.analyze_query(
            query=request.message,
            context=request.context,
            history=request.history
        )
        
        logger.info(f"Intent classified: {intent_result.intent}, Target: {intent_result.target_product}")
        
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
            intent=intent_result.intent,
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
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat error for session {request.session_id}: {str(e)}")
        
        # Fallback response
        return ChatResponse(
            response="Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng liên hệ support@yourdomain.com để được hỗ trợ.",
            session_id=request.session_id,
            confidence=0.0,
            processing_time=time.time() - start_time
        )

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
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
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
    
    # Check LLM providers
    try:
        provider_status = await llm_provider.health_check()
        health_status["components"]["llm_providers"] = provider_status
    except Exception as e:
        health_status["components"]["llm_providers"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status

@app.get("/api/analytics/dashboard")
async def analytics_dashboard():
    """Analytics endpoint for monitoring"""
    return await analytics.get_dashboard_data()
```

### 3. FAISS Collections Management

```python
# engines/faiss_manager.py
import faiss
import numpy as np
import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import pickle

@dataclass
class DocumentChunk:
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class FAISSCollectionManager:
    def __init__(self, base_path: str = "./data/faiss_indices"):
        self.base_path = base_path
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_dim = 384  # MiniLM dimension
        
        # Collection definitions
        self.collection_configs = {
            'product_a_features': {
                'description': 'Tính năng và đặc điểm của Sản phẩm A',
                'keywords': ['product a', 'sản phẩm a', 'tính năng', 'feature', 'chức năng'],
                'index_type': 'flat',
                'max_docs': 1000
            },
            'product_a_pricing': {
                'description': 'Giá cả và gói dịch vụ Sản phẩm A',
                'keywords': ['product a', 'giá', 'pricing', 'cost', 'gói', 'plan'],
                'index_type': 'flat',
                'max_docs': 200
            },
            'product_b_features': {
                'description': 'Tính năng và đặc điểm của Sản phẩm B',
                'keywords': ['product b', 'sản phẩm b', 'tính năng', 'feature'],
                'index_type': 'flat',
                'max_docs': 1000
            },
            'warranty_support': {
                'description': 'Thông tin bảo hành và hỗ trợ khách hàng',
                'keywords': ['bảo hành', 'warranty', 'support', 'hỗ trợ', 'khách hàng'],
                'index_type': 'flat',
                'max_docs': 500
            },
            'contact_company': {
                'description': 'Thông tin liên hệ và về công ty',
                'keywords': ['liên hệ', 'contact', 'company', 'công ty', 'địa chỉ'],
                'index_type': 'flat',
                'max_docs': 100
            }
        }
        
        self.collections = {}
        os.makedirs(base_path, exist_ok=True)
    
    async def initialize_collections(self):
        """Initialize all FAISS collections"""
        for name, config in self.collection_configs.items():
            await self._create_collection(name, config)
    
    async def _create_collection(self, name: str, config: Dict):
        """Create individual FAISS collection"""
        
        # Create appropriate FAISS index
        if config['index_type'] == 'flat':
            index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        else:
            # For future scaling - IVF index
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, min(100, config['max_docs']//10))
        
        # Wrap with ID mapping
        index = faiss.IndexIDMap2(index)
        
        self.collections[name] = {
            'index': index,
            'metadata_store': {},  # doc_id -> metadata
            'doc_count': 0,
            'config': config,
            'loaded': False
        }
    
    async def add_documents_to_collection(self, collection_name: str, documents: List[DocumentChunk]):
        """Add documents to specific collection with batch processing"""
        
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        collection = self.collections[collection_name]
        
        # Generate embeddings in batches
        texts = [doc.content for doc in documents]
        embeddings = await self._generate_embeddings_batch(texts)
        
        # Prepare data for FAISS
        doc_ids = []
        embedding_matrix = []
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"{collection_name}_{collection['doc_count'] + i}"
            
            # Normalize embedding for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            
            # Store metadata
            collection['metadata_store'][doc_id] = {
                'id': doc_id,
                'content': doc.content,
                'metadata': doc.metadata,
                'collection': collection_name,
                'added_at': time.time()
            }
            
            # Convert doc_id to integer for FAISS
            doc_ids.append(hash(doc_id) % (2**63))
            embedding_matrix.append(embedding)
        
        # Add to FAISS index
        if embedding_matrix:
            embedding_matrix = np.array(embedding_matrix).astype('float32')
            collection['index'].add_with_ids(embedding_matrix, np.array(doc_ids, dtype=np.int64))
            collection['doc_count'] += len(documents)
        
        # Save to disk
        await self._save_collection(collection_name)
        
        return len(documents)
    
    async def search_targeted_collections(
        self,
        queries: List[str],
        collections: List[str],
        context_filter: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search across specified collections with context filtering"""
        
        all_results = []
        
        for collection_name in collections:
            if collection_name not in self.collections:
                continue
            
            collection = self.collections[collection_name]
            if not collection['loaded']:
                await self._load_collection(collection_name)
            
            for query in queries:
                # Generate query embedding
                query_embedding = await self._generate_embeddings_batch([query])
                query_vector = query_embedding[0] / np.linalg.norm(query_embedding[0])  # Normalize
                query_vector = np.array([query_vector]).astype('float32')
                
                # Search FAISS index
                scores, doc_ids = collection['index'].search(query_vector, top_k)
                
                # Convert results and apply filters
                for score, doc_id in zip(scores[0], doc_ids[0]):
                    if doc_id == -1:  # No result found
                        continue
                    
                    # Find metadata by doc_id
                    metadata = self._find_metadata_by_id(collection, doc_id)
                    if not metadata:
                        continue
                    
                    # Apply context filters
                    if context_filter and not self._matches_filter(metadata, context_filter):
                        continue
                    
                    result = {
                        'content': metadata['content'],
                        'metadata': metadata['metadata'],
                        'collection': collection_name,
                        'score': float(score),
                        'query': query,
                        'doc_id': metadata['id']
                    }
                    
                    all_results.append(result)
        
        # Sort by score and remove duplicates
        all_results = self._deduplicate_results(all_results)
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return all_results[:top_k * len(collections)]  # Return proportional results
    
    async def _generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings with batch processing"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(batch, convert_to_numpy=True)
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings)
    
    def _find_metadata_by_id(self, collection: Dict, doc_id: int) -> Optional[Dict]:
        """Find metadata by FAISS doc_id"""
        for stored_id, metadata in collection['metadata_store'].items():
            if hash(stored_id) % (2**63) == doc_id:
                return metadata
        return None
    
    def _matches_filter(self, metadata: Dict, context_filter: Dict) -> bool:
        """Check if metadata matches context filters"""
        for key, value in context_filter.items():
            if value is None:
                continue
            
            metadata_value = metadata.get('metadata', {}).get(key)
            if metadata_value != value:
                return False
        
        return True
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on content similarity"""
        seen_contents = set()
        deduplicated = []
        
        for result in results:
            content_hash = hash(result['content'][:100])  # Use first 100 chars
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    async def _save_collection(self, collection_name: str):
        """Save FAISS collection to disk"""
        collection = self.collections[collection_name]
        
        # Save FAISS index
        index_path = os.path.join(self.base_path, f"{collection_name}.index")
        faiss.write_index(collection['index'], index_path)
        
        # Save metadata
        metadata_path = os.path.join(self.base_path, f"{collection_name}_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(collection['metadata_store'], f)
        
        # Save config
        config_path = os.path.join(self.base_path, f"{collection_name}_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            config_data = {
                'config': collection['config'],
                'doc_count': collection['doc_count'],
                'last_updated': time.time()
            }
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    async def _load_collection(self, collection_name: str):
        """Load FAISS collection from disk"""
        
        # Load FAISS index
        index_path = os.path.join(self.base_path, f"{collection_name}.index")
        if os.path.exists(index_path):
            self.collections[collection_name]['index'] = faiss.read_index(index_path)
        
        # Load metadata
        metadata_path = os.path.join(self.base_path, f"{collection_name}_metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                self.collections[collection_name]['metadata_store'] = pickle.load(f)
        
        # Load config
        config_path = os.path.join(self.base_path, f"{collection_name}_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.collections[collection_name]['doc_count'] = config_data['doc_count']
        
        self.collections[collection_name]['loaded'] = True
    
    async def load_all_collections(self):
        """Load all collections from disk"""
        await self.initialize_collections()
        
        for collection_name in self.collection_configs.keys():
            try:
                await self._load_collection(collection_name)
                print(f"Loaded collection: {collection_name} ({self.collections[collection_name]['doc_count']} docs)")
            except Exception as e:
                print(f"Failed to load collection {collection_name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all collections"""
        status = {
            'all_loaded': True,
            'collections': {}
        }
        
        for name, collection in self.collections.items():
            collection_status = {
                'loaded': collection['loaded'],
                'doc_count': collection['doc_count'],
                'index_size': collection['index'].ntotal if collection['loaded'] else 0
				}
           
            if not collection['loaded']:
                status['all_loaded'] = False
           
            status['collections'][name] = collection_status
       
        return status
```


### 4. Intent Classification Engine

```python
# engines/intent_classifier.py
import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

class IntentType(Enum):
    PRODUCT_INQUIRY = "product_inquiry"
    PRICING_INQUIRY = "pricing_inquiry"
    SUPPORT_REQUEST = "support_request"
    WARRANTY_INQUIRY = "warranty_inquiry"
    CONTACT_REQUEST = "contact_request"
    COMPANY_INFO = "company_info"
    GENERAL_CHAT = "general_chat"

@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    target_product: Optional[str]
    target_collections: List[str]
    refined_queries: List[str]
    entities: Dict[str, str]
    reasoning: str

class IntentClassifier:
    def __init__(self):
        self.llm_provider = None  # Will be injected
        
        # Intent to collection mapping
        self.intent_collection_map = {
            IntentType.PRODUCT_INQUIRY: {
                'product_a': ['product_a_features'],
                'product_b': ['product_b_features'],
                'general': ['product_a_features', 'product_b_features']
            },
            IntentType.PRICING_INQUIRY: {
                'product_a': ['product_a_pricing'],
                'product_b': ['product_b_pricing'],
                'general': ['product_a_pricing', 'product_b_pricing']
            },
            IntentType.SUPPORT_REQUEST: ['warranty_support'],
            IntentType.WARRANTY_INQUIRY: ['warranty_support'],
            IntentType.CONTACT_REQUEST: ['contact_company'],
            IntentType.COMPANY_INFO: ['contact_company'],
            IntentType.GENERAL_CHAT: ['contact_company']  # Fallback
        }
        
        # Keyword patterns for backup classification
        self.keyword_patterns = {
            IntentType.PRODUCT_INQUIRY: [
                r'tính năng|feature|chức năng|hoạt động|làm gì|có thể',
                r'sản phẩm.*gì|product.*what|specifications|đặc điểm'
            ],
            IntentType.PRICING_INQUIRY: [
                r'giá|price|cost|phí|pricing|bao nhiều tiền|plan|gói',
                r'thanh toán|payment|subscription|đăng ký'
            ],
            IntentType.SUPPORT_REQUEST: [
                r'hướng dẫn|guide|how to|làm sao|cách|hỗ trợ|support',
                r'không hoạt động|not working|lỗi|error|bug|problem'
            ],
            IntentType.WARRANTY_INQUIRY: [
                r'bảo hành|warranty|guarantee|đảm bảo|chính sách',
                r'hoàn tiền|refund|return|đổi trả'
            ],
            IntentType.CONTACT_REQUEST: [
                r'liên hệ|contact|gọi|call|email|địa chỉ|address',
                r'hotline|phone|điện thoại|customer service'
            ],
            IntentType.COMPANY_INFO: [
                r'công ty|company|về chúng tôi|about us|giới thiệu',
                r'team|đội ngũ|lịch sử|history'
            ]
        }
    
    def set_llm_provider(self, llm_provider):
        """Inject LLM provider dependency"""
        self.llm_provider = llm_provider
    
    async def analyze_query(
        self,
        query: str,
        context: 'PageContext',
        history: List['ChatMessage'] = None
    ) -> IntentResult:
        """Main intent analysis pipeline"""
        
        # Extract product context from URL/page
        product_context = self._extract_product_context(context)
        
        # Try LLM classification first
        llm_result = await self._llm_classify_intent(query, context, history)
        
        # Backup with keyword classification
        if llm_result.confidence < 0.7:
            keyword_result = self._keyword_classify_intent(query, context)
            if keyword_result.confidence > llm_result.confidence:
                llm_result = keyword_result
        
        # Determine target collections
        target_collections = self._resolve_target_collections(
            llm_result.intent,
            llm_result.target_product or product_context
        )
        
        # Generate refined queries
        refined_queries = await self._generate_refined_queries(
            query, llm_result.intent, llm_result.target_product, context
        )
        
        return IntentResult(
            intent=llm_result.intent,
            confidence=llm_result.confidence,
            target_product=llm_result.target_product or product_context,
            target_collections=target_collections,
            refined_queries=refined_queries,
            entities=llm_result.entities,
            reasoning=llm_result.reasoning
        )
    
    def _extract_product_context(self, context: 'PageContext') -> Optional[str]:
        """Extract product from page context"""
        
        # From URL path
        if context.product:
            return context.product
        
        # From URL patterns
        url_lower = context.url.lower()
        if 'product-a' in url_lower or 'product_a' in url_lower:
            return 'product_a'
        elif 'product-b' in url_lower or 'product_b' in url_lower:
            return 'product_b'
        
        # From page title
        title_lower = context.title.lower()
        if 'product a' in title_lower:
            return 'product_a'
        elif 'product b' in title_lower:
            return 'product_b'
        
        return None
    
    async def _llm_classify_intent(
        self,
        query: str,
        context: 'PageContext',
        history: Optional[List['ChatMessage']] = None
    ) -> IntentResult:
        """Use LLM for intent classification"""
        
        # Build context for LLM
        context_info = f"""
        Current Page: {context.url}
        Page Title: {context.title}
        Product Context: {context.product or 'unknown'}
        Section: {context.section or 'unknown'}
        """
        
        history_info = ""
        if history and len(history) > 0:
            recent_messages = history[-3:]  # Last 3 messages
            history_info = "Recent Conversation:\n"
            for msg in recent_messages:
                history_info += f"{msg.sender}: {msg.content}\n"
        
        system_prompt = f"""You are an expert intent classifier for a website chatbot.
        
        Available Intent Types:
        1. product_inquiry: Questions about product features, capabilities, specifications
        2. pricing_inquiry: Questions about cost, plans, pricing, payments
        3. support_request: Technical support, how-to questions, troubleshooting
        4. warranty_inquiry: Questions about warranty, guarantees, returns, refunds
        5. contact_request: Want contact information, phone, email, address
        6. company_info: Questions about the company, team, history, about us
        7. general_chat: Greetings, small talk, off-topic questions
        
        Context Information:
        {context_info}
        
        {history_info}
        
        Your task: Analyze the user query and return a JSON response with:
        1. Intent classification with confidence score (0.0-1.0)
        2. Target product if mentioned or implied from context
        3. Key entities extracted from the query
        4. Brief reasoning for your decision
        
        Return JSON format:
        {{
            "intent": "product_inquiry",
            "confidence": 0.95,
            "target_product": "product_a",
            "entities": {{"feature": "security", "product": "product_a"}},
            "reasoning": "User is asking about security features while on Product A page"
        }}
        """
        
        user_prompt = f'User Query: "{query}"'
        
        try:
            if not self.llm_provider:
                raise Exception("LLM provider not initialized")
            
            response = await self.llm_provider.call_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            result_data = json.loads(response)
            
            return IntentResult(
                intent=IntentType(result_data.get('intent', 'general_chat')),
                confidence=float(result_data.get('confidence', 0.5)),
                target_product=result_data.get('target_product'),
                target_collections=[],  # Will be resolved later
                refined_queries=[],     # Will be generated later
                entities=result_data.get('entities', {}),
                reasoning=result_data.get('reasoning', '')
            )
            
        except Exception as e:
            print(f"LLM intent classification failed: {e}")
            return self._keyword_classify_intent(query, context)
    
    def _keyword_classify_intent(self, query: str, context: 'PageContext') -> IntentResult:
        """Fallback keyword-based intent classification"""
        
        query_lower = query.lower()
        best_intent = IntentType.GENERAL_CHAT
        best_score = 0.0
        
        # Score each intent based on keyword matches
        for intent_type, patterns in self.keyword_patterns.items():
            score = 0.0
            matches = []
            
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1.0
                    matches.append(pattern)
            
            # Normalize score
            score = score / len(patterns)
            
            if score > best_score:
                best_score = score
                best_intent = intent_type
        
        # Extract entities with simple pattern matching
        entities = {}
        
        # Product extraction
        if 'product a' in query_lower or 'sản phẩm a' in query_lower:
            entities['product'] = 'product_a'
        elif 'product b' in query_lower or 'sản phẩm b' in query_lower:
            entities['product'] = 'product_b'
        elif context.product:
            entities['product'] = context.product
        
        # Feature extraction
        feature_keywords = ['tính năng', 'feature', 'chức năng', 'bảo mật', 'security']
        for keyword in feature_keywords:
            if keyword in query_lower:
                entities['feature'] = keyword
                break
        
        return IntentResult(
            intent=best_intent,
            confidence=min(best_score + 0.3, 1.0),  # Boost confidence slightly
            target_product=entities.get('product'),
            target_collections=[],
            refined_queries=[],
            entities=entities,
            reasoning=f"Keyword matching: {best_score:.2f} confidence"
        )
    
    def _resolve_target_collections(self, intent: IntentType, target_product: Optional[str]) -> List[str]:
        """Resolve which collections to search based on intent and product"""
        
        collection_mapping = self.intent_collection_map.get(intent, ['contact_company'])
        
        if isinstance(collection_mapping, dict):
            # Product-specific mapping
            if target_product and target_product in collection_mapping:
                return collection_mapping[target_product]
            else:
                return collection_mapping.get('general', list(collection_mapping.values())[0])
        else:
            # Simple list mapping
            return collection_mapping
    
    async def _generate_refined_queries(
        self,
        original_query: str,
        intent: IntentType,
        target_product: Optional[str],
        context: 'PageContext'
    ) -> List[str]:
        """Generate refined search queries for better retrieval"""
        
        refined_queries = [original_query]  # Always include original
        
        # Generate variations based on intent
        if intent == IntentType.PRODUCT_INQUIRY:
            if target_product:
                refined_queries.append(f"{target_product} tính năng")
                refined_queries.append(f"{target_product} chức năng")
            refined_queries.append("đặc điểm sản phẩm")
            refined_queries.append("tính năng chính")
            
        elif intent == IntentType.PRICING_INQUIRY:
            if target_product:
                refined_queries.append(f"{target_product} giá cả")
                refined_queries.append(f"{target_product} pricing")
            refined_queries.append("bảng giá dịch vụ")
            refined_queries.append("gói cước phí")
            
        elif intent == IntentType.SUPPORT_REQUEST:
            refined_queries.append("hướng dẫn sử dụng")
            refined_queries.append("cách thức hoạt động")
            refined_queries.append("hỗ trợ khách hàng")
            
        elif intent == IntentType.WARRANTY_INQUIRY:
            refined_queries.append("chính sách bảo hành")
            refined_queries.append("điều khoản đảm bảo")
            refined_queries.append("hoàn tiền dịch vụ")
            
        elif intent == IntentType.CONTACT_REQUEST:
            refined_queries.append("thông tin liên hệ")
            refined_queries.append("địa chỉ công ty")
            refined_queries.append("hotline hỗ trợ")
        
        # Remove duplicates and limit to 4 queries
        refined_queries = list(dict.fromkeys(refined_queries))[:4]
        
        return refined_queries
```

### 5. Multi-LLM Provider Handler

```python
# engines/llm_provider.py
import asyncio
import aiohttp
import json
import time
import random
from typing import List, Dict, Optional, Any
from enum import Enum
import os

class LLMProvider(Enum):
    OPENROUTER = "openrouter"
    GROQ = "groq"
    GEMINI = "gemini"
    OPENAI = "openai"

class MultiLLMProvider:
    def __init__(self):
        self.providers = {}
        self.provider_configs = {
            LLMProvider.OPENROUTER: {
                'url': 'https://openrouter.ai/api/v1/chat/completions',
                'model': 'anthropic/claude-3.5-sonnet',
                'api_key_env': 'OPENROUTER_API_KEY',
                'priority': 1,
                'timeout': 30,
                'max_tokens': 2000
            },
            LLMProvider.GROQ: {
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'model': 'llama-3.1-70b-versatile',
                'api_key_env': 'GROQ_API_KEY',
                'priority': 2,
                'timeout': 25,
                'max_tokens': 2000
            },
            LLMProvider.GEMINI: {
                'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent',
                'model': 'gemini-1.5-flash',
                'api_key_env': 'GEMINI_API_KEY',
                'priority': 3,
                'timeout': 30,
                'max_tokens': 2000
            },
            LLMProvider.OPENAI: {
                'url': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-4o-mini',
                'api_key_env': 'OPENAI_API_KEY',
                'priority': 4,
                'timeout': 35,
                'max_tokens': 2000
            }
        }
        
        self.provider_status = {}
        self.session = None
    
    async def initialize_providers(self):
        """Initialize HTTP session and check provider availability"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=100)
        )
        
        for provider in LLMProvider:
            config = self.provider_configs[provider]
            api_key = os.getenv(config['api_key_env'])
            
            if api_key:
                self.providers[provider] = {
                    'config': config,
                    'api_key': api_key,
                    'available': True,
                    'last_error': None,
                    'response_times': [],
                    'success_rate': 1.0
                }
            else:
                self.providers[provider] = {
                    'config': config,
                    'api_key': None,
                    'available': False,
                    'last_error': 'API key not found',
                    'response_times': [],
                    'success_rate': 0.0
                }
        
        # Initial health check
        await self._update_provider_health()
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        preferred_provider: Optional[LLMProvider] = None,
        max_retries: int = 3
    ) -> str:
        """Call LLM with automatic failover"""
        
        # Get available providers sorted by priority and health
        available_providers = self._get_available_providers()
        
        if preferred_provider and preferred_provider in available_providers:
            # Move preferred provider to front
            available_providers.remove(preferred_provider)
            available_providers.insert(0, preferred_provider)
        
        last_error = None
        
        for provider in available_providers:
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    response = await self._call_provider(provider, messages)
                    
                    # Update metrics
                    response_time = time.time() - start_time
                    self._update_provider_metrics(provider, response_time, success=True)
                    
                    return response
                    
                except Exception as e:
                    last_error = e
                    self._update_provider_metrics(provider, 0, success=False)
                    
                    # Wait before retry
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All providers failed
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    async def _call_provider(self, provider: LLMProvider, messages: List[Dict]) -> str:
        """Call specific LLM provider"""
        
        provider_data = self.providers[provider]
        config = provider_data['config']
        api_key = provider_data['api_key']
        
        if not api_key:
            raise Exception(f"No API key for {provider.value}")
        
        if provider == LLMProvider.GEMINI:
            return await self._call_gemini(messages, config, api_key)
        else:
            return await self._call_openai_compatible(messages, config, api_key, provider)
    
    async def _call_openai_compatible(
        self,
        messages: List[Dict],
        config: Dict,
        api_key: str,
        provider: LLMProvider
    ) -> str:
        """Call OpenAI-compatible APIs (OpenRouter, Groq, OpenAI)"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Add provider-specific headers
        if provider == LLMProvider.OPENROUTER:
            headers['HTTP-Referer'] = 'https://yourdomain.com'
            headers['X-Title'] = 'Your Chatbot'
        
        payload = {
            'model': config['model'],
            'messages': messages,
            'max_tokens': config['max_tokens'],
            'temperature': 0.7,
            'stream': False
        }
        
        async with self.session.post(
            config['url'],
            headers=headers,
            json=payload,
            timeout=config['timeout']
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"{provider.value} API error {response.status}: {error_text}")
            
            result = await response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Invalid response from {provider.value}")
            
            return result['choices'][0]['message']['content']
    
    async def _call_gemini(self, messages: List[Dict], config: Dict, api_key: str) -> str:
        """Call Google Gemini API"""
        
        # Convert messages to Gemini format
        prompt = self._convert_messages_to_gemini_format(messages)
        
        url = f"{config['url']}?key={api_key}"
        
        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'maxOutputTokens': config['max_tokens'],
                'temperature': 0.7
            }
        }
        
        async with self.session.post(
            url,
            json=payload,
            timeout=config['timeout']
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API error {response.status}: {error_text}")
            
            result = await response.json()
            
            if 'candidates' not in result or len(result['candidates']) == 0:
                raise Exception("Invalid response from Gemini")
            
            return result['candidates'][0]['content']['parts'][0]['text']
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict]) -> str:
        """Convert OpenAI format messages to Gemini prompt"""
        prompt_parts = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                prompt_parts.append(f"Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers sorted by priority and health"""
        available = []
        
        for provider, data in self.providers.items():
            if data['available'] and data['success_rate'] > 0.1:
                available.append((provider, data['config']['priority'], data['success_rate']))
        
        # Sort by priority (lower is better) and success rate (higher is better)
        available.sort(key=lambda x: (x[1], -x[2]))
        
        return [provider for provider, _, _ in available]
    
    def _update_provider_metrics(self, provider: LLMProvider, response_time: float, success: bool):
        """Update provider performance metrics"""
        
        provider_data = self.providers[provider]
        
        # Update response times
        provider_data['response_times'].append(response_time)
        if len(provider_data['response_times']) > 100:
            provider_data['response_times'] = provider_data['response_times'][-100:]
        
        # Update success rate (exponential moving average)
        alpha = 0.1
        current_rate = provider_data['success_rate']
        new_point = 1.0 if success else 0.0
        provider_data['success_rate'] = alpha * new_point + (1 - alpha) * current_rate
        
        # Mark as unavailable if success rate is too low
        if provider_data['success_rate'] < 0.1:
            provider_data['available'] = False
            provider_data['last_error'] = 'Low success rate'
    
    async def _update_provider_health(self):
        """Periodic health check for all providers"""
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        for provider in self.providers.keys():
            if self.providers[provider]['api_key']:
                try:
                    await self._call_provider(provider, test_messages)
                    self.providers[provider]['available'] = True
                    self.providers[provider]['last_error'] = None
                except Exception as e:
                    self.providers[provider]['available'] = False
                    self.providers[provider]['last_error'] = str(e)
    
    async def health_check(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        await self._update_provider_health()
        
        status = {
            'overall_status': 'healthy',
            'providers': {}
        }
        
        healthy_providers = 0
        
        for provider, data in self.providers.items():
            provider_status = {
                'available': data['available'],
                'success_rate': round(data['success_rate'], 2),
                'avg_response_time': round(
                    sum(data['response_times']) / len(data['response_times']), 2
                ) if data['response_times'] else 0,
                'last_error': data['last_error']
            }
            
            status['providers'][provider.value] = provider_status
            
            if data['available']:
                healthy_providers += 1
        
        if healthy_providers == 0:
            status['overall_status'] = 'unhealthy'
        elif healthy_providers < len(self.providers) / 2:
            status['overall_status'] = 'degraded'
        
        return status
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
```

## Todo List - Enterprise Chatbot Development

### Phase 1: Backend Core Infrastructure
- [ ] **FastAPI Application Setup**
  - [ ] Install FastAPI, uvicorn, và các dependencies cần thiết
  - [ ] Tạo project structure với proper modules
  - [ ] Setup environment variables và configuration
  - [ ] Implement CORS và security middleware
  - [ ] Add rate limiting với slowapi
  - [ ] Setup logging và error handling

- [ ] **FAISS Collections Management**
  - [ ] Install FAISS và sentence-transformers
  - [ ] Implement FAISSCollectionManager class
  - [ ] Tạo 5 collections: product_a_features, product_a_pricing, product_b_features, warranty_support, contact_company
  - [ ] Test embedding generation và vector storage
  - [ ] Implement collection save/load functionality
  - [ ] Add health check cho tất cả collections

- [ ] **Multi-LLM Provider Setup**
  - [ ] Implement MultiLLMProvider class
  - [ ] Configure OpenRouter, Groq, Gemini, OpenAI APIs
  - [ ] Add automatic failover logic
  - [ ] Implement provider health monitoring
  - [ ] Test all provider integrations
  - [ ] Add response caching với Redis

### Phase 2: RAG Intelligence Layer
- [ ] **Intent Classification Engine**
  - [ ] Implement IntentClassifier với 7 intent types
  - [ ] Build LLM-based classification system
  - [ ] Add keyword-based fallback classification
  - [ ] Test intent accuracy với sample queries
  - [ ] Implement entity extraction
  - [ ] Add context-aware product detection

- [ ] **Document Routing System**
  - [ ] Implement query routing logic
  - [ ] Build collection selection algorithm
  - [ ] Add context filtering capabilities
  - [ ] Test routing accuracy với different scenarios
  - [ ] Optimize search performance
  - [ ] Add result deduplication

- [ ] **Response Generation**
  - [ ] Implement ContextualResponseGenerator
  - [ ] Build context assembly từ multiple sources
  - [ ] Add source citation trong responses
  - [ ] Implement confidence scoring
  - [ ] Test response quality và relevance
  - [ ] Add response length optimization

### Phase 3: Frontend Integration
- [ ] **React Chatbot Component**
  - [ ] Create ChatbotManager với context tracking
  - [ ] Implement PageContext detection
  - [ ] Build modern chat UI với TypeScript
  - [ ] Add typing indicators và loading states
  - [ ] Implement message history management
  - [ ] Add mobile-responsive design

- [ ] **Context Management System**
  - [ ] Implement URL/page tracking
  - [ ] Add product detection từ page context
  - [ ] Track user navigation và section changes
  - [ ] Build session management
  - [ ] Add conversation persistence
  - [ ] Implement analytics tracking

### Phase 4: Data Management & Content
- [ ] **Document Preparation**
  - [ ] Prepare content cho 4-10 trang A4
  - [ ] Structure documents theo collections
  - [ ] Add proper metadata cho mỗi document
  - [ ] Test document chunking strategy
  - [ ] Validate embedding quality
  - [ ] Setup content update workflow

- [ ] **Database & Caching**
  - [ ] Setup Redis cho caching và sessions
  - [ ] Configure PostgreSQL cho metadata
  - [ ] Implement cache invalidation strategy
  - [ ] Add database migrations
  - [ ] Setup backup procedures
  - [ ] Test performance under load

### Phase 5: Production Deployment
- [ ] **Containerization & Deployment**
  - [ ] Create Docker containers cho backend
  - [ ] Setup Docker Compose để development
  - [ ] Configure production environment
  - [ ] Add health checks và monitoring
  - [ ] Setup CI/CD pipeline
  - [ ] Deploy to cloud provider

- [ ] **Security & Performance**
  - [ ] Implement authentication nếu cần
  - [ ] Add input sanitization và validation
  - [ ] Configure rate limiting cho production
  - [ ] Setup SSL certificates
  - [ ] Add DDoS protection
  - [ ] Implement monitoring và alerting

### Phase 6: Testing & Quality Assurance
- [ ] **Testing Suite**
  - [ ] Write unit tests cho core components
  - [ ] Add integration tests cho API endpoints
  - [ ] Test RAG accuracy với sample queries
  - [ ] Performance testing với concurrent users
  - [ ] Test failover scenarios
  - [ ] Cross-browser testing cho frontend

- [ ] **Analytics & Monitoring**
  - [ ] Implement conversation analytics
  - [ ] Add performance monitoring
  - [ ] Track user satisfaction metrics
  - [ ] Monitor API usage và costs
  - [ ] Setup error alerting
  - [ ] Create admin dashboard

### Phase 7: Optimization & Maintenance
- [ ] **Performance Optimization**
  - [ ] Optimize FAISS search performance
  - [ ] Implement intelligent caching strategies
  - [ ] Fine-tune embedding models
  - [ ] Optimize response times
  - [ ] Add CDN cho static assets
  - [ ] Database query optimization

- [ ] **Content Management**
  - [ ] Build content update workflow
  - [ ] Add version control cho documents
  - [ ] Implement A/B testing cho responses
  - [ ] Monitor và improve response quality
  - [ ] Add multilingual support nếu cần
  - [ ] Regular content auditing

### Key Milestones:
- **Week 1-2**: Backend infrastructure + FAISS setup
- **Week 3-4**: RAG intelligence layer + intent classification
- **Week 5-6**: Frontend integration + context management
- **Week 7-8**: Key Milestones (continued):
- **Week 7-8**: Data preparation + production deployment
- **Week 9-10**: Testing, optimization, và monitoring setup
- **Week 11-12**: Final polish, documentation, và go-live

## 6. Production Deployment Configuration

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  chatbot-api:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data/faiss_indices:/app/data/faiss_indices
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=chatbot
      - POSTGRES_USER=chatbot_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - chatbot-api
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/faiss_indices logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream chatbot_backend {
        server chatbot-api:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=20r/m;
    limit_req_zone $binary_remote_addr zone=chat:10m rate=10r/m;
    
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        
        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://chatbot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Chat endpoint với stricter rate limiting
        location /api/chat {
            limit_req zone=chat burst=20 nodelay;
            
            proxy_pass http://chatbot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Longer timeout for AI processing
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
```

### Environment Configuration

```bash
# .env.production
# Database
POSTGRES_PASSWORD=your_secure_postgres_password
DATABASE_URL=postgresql://chatbot_user:${POSTGRES_PASSWORD}@postgres:5432/chatbot

# Redis
REDIS_URL=redis://redis:6379

# LLM API Keys
OPENROUTER_API_KEY=your_openrouter_api_key
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECRET_KEY=your_super_secure_secret_key_here
```

## 7. Monitoring & Analytics Setup

### Analytics Implementation

```python
# utils/analytics.py
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

class ChatAnalytics:
    def __init__(self, postgres_url: str, redis_client: redis.Redis):
        self.postgres_url = postgres_url
        self.redis_client = redis_client
        
    async def track_conversation(
        self,
        session_id: str,
        user_message: str,
        bot_response: 'ChatResponse',
        user_ip: str
    ):
        """Track conversation metrics"""
        
        conversation_data = {
            'session_id': session_id,
            'user_message': user_message,
            'bot_response': bot_response.response,
            'intent': bot_response.intent,
            'target_product': bot_response.target_product,
            'confidence': bot_response.confidence,
            'processing_time': bot_response.processing_time,
            'sources_count': len(bot_response.sources),
            'user_ip': self._anonymize_ip(user_ip),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in database
        await self._store_conversation(conversation_data)
        
        # Update real-time metrics in Redis
        await self._update_realtime_metrics(conversation_data)
    
    async def _store_conversation(self, data: Dict[str, Any]):
        """Store conversation in PostgreSQL"""
        
        query = """
        INSERT INTO conversations 
        (session_id, user_message, bot_response, intent, target_product, 
         confidence, processing_time, sources_count, user_ip, created_at)
        VALUES (%(session_id)s, %(user_message)s, %(bot_response)s, %(intent)s, 
                %(target_product)s, %(confidence)s, %(processing_time)s, 
                %(sources_count)s, %(user_ip)s, %(timestamp)s)
        """
        
        try:
            with psycopg2.connect(self.postgres_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, data)
                    conn.commit()
        except Exception as e:
            print(f"Failed to store conversation: {e}")
    
    async def _update_realtime_metrics(self, data: Dict[str, Any]):
        """Update real-time metrics in Redis"""
        
        # Daily conversation count
        today = datetime.now().strftime('%Y-%m-%d')
        self.redis_client.incr(f"conversations:daily:{today}")
        
        # Intent distribution
        if data['intent']:
            self.redis_client.incr(f"intents:daily:{today}:{data['intent']}")
        
        # Product distribution
        if data['target_product']:
            self.redis_client.incr(f"products:daily:{today}:{data['target_product']}")
        
        # Average processing time
        pipeline = self.redis_client.pipeline()
        pipeline.lpush(f"processing_times:{today}", data['processing_time'])
        pipeline.ltrim(f"processing_times:{today}", 0, 999)  # Keep last 1000
        pipeline.execute()
        
        # Set expiration for daily keys (30 days)
        expire_time = 30 * 24 * 3600
        for key_pattern in ['conversations:daily:', 'intents:daily:', 'products:daily:', 'processing_times:']:
            self.redis_client.expire(f"{key_pattern}{today}", expire_time)
    
    async def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics dashboard data"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get data from PostgreSQL
        query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as conversations,
            AVG(confidence) as avg_confidence,
            AVG(processing_time) as avg_processing_time,
            intent,
            target_product
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s
        GROUP BY DATE(created_at), intent, target_product
        ORDER BY date DESC
        """
        
        dashboard_data = {
            'summary': await self._get_summary_stats(start_date, end_date),
            'daily_conversations': await self._get_daily_conversations(start_date, end_date),
            'intent_distribution': await self._get_intent_distribution(start_date, end_date),
            'product_distribution': await self._get_product_distribution(start_date, end_date),
            'performance_metrics': await self._get_performance_metrics(start_date, end_date)
        }
        
        return dashboard_data
    
    def _anonymize_ip(self, ip: str) -> str:
        """Anonymize IP address for privacy"""
        if ':' in ip:  # IPv6
            parts = ip.split(':')
            return ':'.join(parts[:4] + ['xxxx'] * 4)
        else:  # IPv4
            parts = ip.split('.')
            return '.'.join(parts[:3] + ['xxx'])
```

### Performance Monitoring

```python
# utils/monitoring.py
import time
import psutil
import asyncio
from typing import Dict, Any
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': self._get_network_stats(),
            'processes': len(psutil.pids())
        }
    
    def _get_network_stats(self) -> Dict[str, int]:
        """Get network I/O statistics"""
        stats = psutil.net_io_counters()
        return {
            'bytes_sent': stats.bytes_sent,
            'bytes_recv': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_recv': stats.packets_recv
        }

# Add monitoring endpoint to FastAPI
@app.get("/api/monitoring/metrics")
async def get_monitoring_metrics():
    """Get system monitoring metrics"""
    monitor = PerformanceMonitor()
    
    return {
        'system': await monitor.get_system_metrics(),
        'application': {
            'uptime': time.time() - app.state.start_time,
            'faiss_status': await faiss_manager.health_check(),
            'llm_providers': await llm_provider.health_check(),
            'cache_stats': cache_manager.get_stats()
        }
    }
```

## 8. Final Production Checklist

### Security Checklist
- [ ] **API Security**
  - [ ] Rate limiting implemented và tested
  - [ ] Input validation cho tất cả endpoints
  - [ ] SQL injection protection
  - [ ] XSS protection headers
  - [ ] CORS properly configured
  - [ ] API keys stored securely

- [ ] **Data Privacy**
  - [ ] IP address anonymization
  - [ ] No logging of sensitive user data
  - [ ] GDPR compliance measures
  - [ ] Data retention policies
  - [ ] Secure data transmission (HTTPS)

### Performance Checklist
- [ ] **Backend Performance**
  - [ ] Database queries optimized
  - [ ] FAISS indices properly sized
  - [ ] Caching strategy implemented
  - [ ] Connection pooling configured
  - [ ] Memory usage monitored
  - [ ] CPU utilization optimized

- [ ] **Frontend Performance**
  - [ ] Code splitting implemented
  - [ ] Lazy loading cho components
  - [ ] Image optimization
  - [ ] CDN configured
  - [ ] Bundle size optimized
  - [ ] Performance metrics tracked

### Reliability Checklist
- [ ] **Error Handling**
  - [ ] Graceful degradation implemented
  - [ ] Fallback responses available
  - [ ] Error logging comprehensive
  - [ ] User-friendly error messages
  - [ ] Circuit breaker pattern
  - [ ] Retry mechanisms

- [ ] **Monitoring & Alerting**
  - [ ] Health checks comprehensive
  - [ ] Performance monitoring active
  - [ ] Error rate monitoring
  - [ ] Capacity planning metrics
  - [ ] Alert thresholds configured
  - [ ] On-call procedures documented

### Deployment Checklist
- [ ] **Infrastructure**
  - [ ] Production environment configured
  - [ ] SSL certificates installed
  - [ ] Database backups automated
  - [ ] Logging centralized
  - [ ] Monitoring dashboards setup
  - [ ] Disaster recovery plan

- [ ] **Documentation**
  - [ ] API documentation complete
  - [ ] Deployment procedures documented
  - [ ] Troubleshooting guides written
  - [ ] Code comments comprehensive
  - [ ] README files updated
  - [ ] User guides created

Kiến trúc này sẽ cho bạn một chatbot enterprise-grade với khả năng scale, performance cao, và reliability tốt. Hệ thống có thể handle thousands of concurrent users và maintain accuracy cao với RAG system được optimize cho use case cụ thể của bạn.