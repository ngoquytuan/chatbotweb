Tôi sẽ phân tích kỹ thuật và đưa ra những khuyến nghị chuyên nghiệp cho chatbot system của bạn.

## Phân Tích Hiện Trạng

### 1. Kiến trúc hiện tại
Từ code bạn đính kèm, tôi thấy bạn đang sử dụng kiến trúc **Monolithic** với Flask serving cả frontend (static files) và backend API. Điều này hoàn toàn có thể tách riêng và nên tách riêng.

### 2. Đánh giá công nghệ hiện tại

**Điểm mạnh:**
- Multi-provider fallback (OpenRouter → Groq → Gemini → OpenAI) - rất tốt cho reliability
- Context-aware với WEBSITE_CONTENT - phù hợp cho use case của bạn
- Error handling cơ bản
- Health check endpoint

**Điểm cần cải thiện:**
- Thiếu caching cho responses
- Không có rate limiting
- Thiếu logging và monitoring
- Security chưa đủ mạnh
- Không có conversation memory
- Thiếu vector database cho large content

## Khuyến Nghị Kiến Trúc Chuyên Nghiệp

### 1. Tách Frontend và Backend

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Chatbot API   │
│   (React/Vue)   │◄──►│   (Optional)    │◄──►│   (FastAPI)     │
│   Static Host   │    │   Rate Limit    │    │   Business      │
│   (CDN)         │    │   Auth          │    │   Logic         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   Vector DB     │
                                               │   (Pinecone/    │
                                               │   Weaviate)     │
                                               └─────────────────┘
```

### 2. Nâng cấp Tech Stack

**Backend Recommendation:**
```python
# Thay Flask bằng FastAPI
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.ratelimit import RateLimitMiddleware
import redis
import asyncio
from typing import List, Optional
import tiktoken
```

**Lý do chọn FastAPI:**
- Performance cao hơn Flask (async support)
- Auto API documentation (Swagger/OpenAPI)
- Built-in validation với Pydantic
- Better typing support
- Production-ready features

### 3. Kiến trúc Production-Ready

```python
# main.py - FastAPI version
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import logging
from typing import List, Optional
import asyncio
import aiohttp
from pydantic import BaseModel

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Chatbot API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis for caching
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float
    sources: List[str] = []

# Vector search for large content
class VectorSearch:
    def __init__(self):
        # Initialize vector database (Pinecone, Weaviate, etc.)
        pass
    
    async def search_relevant_content(self, query: str, top_k: int = 3):
        # Search vector database for relevant content
        pass

# Async LLM calls
class LLMProvider:
    async def call_provider_async(self, provider: str, messages: List[dict]):
        async with aiohttp.ClientSession() as session:
            # Async HTTP calls to LLM providers
            pass

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # Rate limiting
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        # Check cache first
        cache_key = f"chat:{hash(request.message)}"
        cached_response = redis_client.get(cache_key)
        
        if cached_response:
            return ChatResponse.parse_raw(cached_response)
        
        # Vector search for relevant content
        vector_search = VectorSearch()
        relevant_content = await vector_search.search_relevant_content(request.message)
        
        # Generate response
        llm = LLMProvider()
        response = await llm.call_provider_async("openrouter", messages)
        
        # Cache response
        background_tasks.add_task(cache_response, cache_key, response)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id or generate_session_id(),
            confidence=0.95,
            sources=relevant_content
        )
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 4. Các Công Ty Chuyên Nghiệp Làm Gì?Dựa trên nghiên cứu và kinh nghiệm thực tế, các công ty chuyên nghiệp thường sử dụng:

### Enterprise Chatbot Architecture

**1. Microservices Architecture**
```
┌────────────┐  ┌─────────────┐  ┌──────────────┐
│  Frontend  │  │ API Gateway │  │   Auth       │
│  (React)   │◄►│ (Kong/      │◄►│  Service     │
│  CDN       │  │  Ambassador)│  │  (OAuth2)    │
└────────────┘  └─────────────┘  └──────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
┌────────▼──┐ ┌────────▼──┐ ┌────────▼──┐
│ Chatbot   │ │ Knowledge │ │ Analytics │
│ Service   │ │ Service   │ │ Service   │
│ (FastAPI) │ │ (Vector   │ │ (Metrics) │
└───────────┘ │ Database) │ └───────────┘
              └───────────┘
```

**2. Technology Stack Enterprise-Grade**

Các công ty lớn như Microsoft khuyến nghị kiến trúc network-secured, highly available, và zone-redundant cho enterprise chat applications, tích hợp với existing databases và CRM systems.

```python
# Production Stack
- API Framework: FastAPI/Express.js
- Database: PostgreSQL + Redis (cache)
- Vector Database: Pinecone/Weaviate/ChromaDB
- Message Queue: RabbitMQ/Apache Kafka
- Container: Docker + Kubernetes
- Monitoring: Prometheus + Grafana
- Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
```

**3. Security & Compliance**

Các best practices bao gồm centralized authentication, multi-factor authentication, data encryption, và real-time PII detection với fine-grained access controls.

```python
# Security Implementation
from fastapi_users import FastAPIUsers
from cryptography.fernet import Fernet
import jwt

class SecurityManager:
    def __init__(self):
        self.fernet = Fernet(os.getenv('ENCRYPTION_KEY'))
    
    def encrypt_sensitive_data(self, data: str):
        return self.fernet.encrypt(data.encode()).decode()
    
    def detect_pii(self, text: str):
        # Implement PII detection logic
        pass
```

### 4. Khuyến Nghị Cụ Thể Cho Bạn

**Phase 1: Tách Frontend/Backend (Immediate)**
```bash
# Frontend deployment
- Host trên CDN (Cloudflare/AWS CloudFront)
- Build time: Environment variables
- API endpoint configuration

# Backend deployment  
- Containerize với Docker
- Deploy trên VPS/Cloud (DigitalOcean/AWS)
- Load balancer (Nginx)
```

**Phase 2: Nâng cấp Architecture (1-2 tháng)**
```python
# Migrate sang FastAPI
# Thêm Redis caching
# Implement rate limiting
# Add logging/monitoring
# Vector database cho large content (4-10 pages A4)
```

**Phase 3: Enterprise Features (3-6 tháng)**
```python
# User authentication
# Conversation memory
# Analytics dashboard
# A/B testing
# Multi-language support
```

### 5. Vector Database cho Large Content

Với nội dung 4-10 trang A4, bạn nên sử dụng RAG (Retrieval Augmented Generation):

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings

class ContentManager:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone.from_existing_index("website-content")
    
    def add_content(self, content: str, metadata: dict):
        chunks = self.text_splitter.split_text(content)
        self.vectorstore.add_texts(chunks, metadatas=[metadata] * len(chunks))
    
    def search_relevant_content(self, query: str, k: int = 3):
        return self.vectorstore.similarity_search(query, k=k)
```

### Kết Luận

Công nghệ hiện tại của bạn đã tốt cho MVP, nhưng cần nâng cấp để đạt enterprise-grade. Việc tách frontend/backend là bước đầu quan trọng và hoàn toàn khả thi. Với nội dung large (4-10 trang), vector database là must-have để tìm kiếm thông tin relevant chính xác.

Bạn đã nêu đúng vấn đề cốt lõi của RAG trong enterprise! Đây gọi là **Contextual RAG with Intent Classification** và **Document Routing**. Tôi sẽ thiết kế một hệ thống multi-stage processing cho bạn.

## Kiến Trúc Multi-Stage RAG System

### 1. Overall Flow Architecture

```
User Query + Page Context
         │
         ▼
┌─────────────────────────────────┐
│    Intent Classification        │
│  + Entity Extraction + Context  │
│       (LLM + Rules)            │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│    Document Routing Engine      │
│   (Route to specific corpus)    │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│    Targeted Vector Search       │
│   (Search in specific domain)   │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│    Response Generation          │
│  (Context-aware LLM response)   │
└─────────────────────────────────┘
```

### 2. Implementation Chi Tiết

```python
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from enum import Enum
import json
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
import re

class DocumentType(Enum):
    PRODUCT_A = "product_a"
    PRODUCT_B = "product_b"
    PRICING = "pricing"
    SUPPORT = "support"
    COMPANY_INFO = "company_info"
    WARRANTY = "warranty"
    CONTACT = "contact"

class QueryContext(BaseModel):
    user_query: str
    current_page_url: str
    current_page_title: str
    current_page_content: Optional[str] = None
    user_session_id: str

class IntentResult(BaseModel):
    intent: str
    entities: Dict[str, str]
    target_product: Optional[str] = None
    document_types: List[DocumentType]
    confidence: float
    refined_queries: List[str]

class DocumentRouter:
    def __init__(self):
        self.vector_stores = {}
        self.initialize_vector_stores()
        
    def initialize_vector_stores(self):
        """Initialize separate vector stores for each document type"""
        embeddings = OpenAIEmbeddings()
        
        for doc_type in DocumentType:
            self.vector_stores[doc_type.value] = Pinecone.from_existing_index(
                index_name=f"website-{doc_type.value}",
                embedding=embeddings
            )

class IntentClassifier:
    def __init__(self):
        self.llm = self._initialize_llm()
        
    async def classify_intent(self, context: QueryContext) -> IntentResult:
        """Phân loại intent và extract entities từ query + context"""
        
        # 1. Xác định sản phẩm từ URL hiện tại
        current_product = self._extract_product_from_url(context.current_page_url)
        
        # 2. LLM Intent Classification
        system_prompt = self._build_classification_prompt()
        
        user_prompt = f"""
        User Query: {context.user_query}
        Current Page: {context.current_page_url}
        Page Title: {context.current_page_title}
        Page Content Summary: {self._summarize_page_content(context.current_page_content)}
        
        Based on the context, classify the user's intent and extract relevant information.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages)
        
        # 3. Parse LLM response
        intent_result = self._parse_intent_response(response, current_product)
        
        # 4. Generate refined queries for vector search
        intent_result.refined_queries = await self._generate_refined_queries(
            context.user_query, 
            intent_result
        )
        
        return intent_result

    def _build_classification_prompt(self) -> str:
        return """You are an intent classification system for a website chatbot.
        
        Your job is to analyze user queries in context and return a JSON response with:

        1. INTENT CLASSIFICATION:
        - product_inquiry: Questions about product features, specifications
        - pricing_inquiry: Questions about cost, plans, payments
        - support_request: Technical support, how-to questions
        - warranty_inquiry: Questions about warranty, guarantees
        - contact_request: Want contact information
        - company_info: Questions about the company
        
        2. ENTITY EXTRACTION:
        - Extract specific product names, feature names, technical terms
        - Identify if user is referring to current page content
        
        3. DOCUMENT ROUTING:
        - Determine which document types are most relevant
        
        4. QUERY REFINEMENT:
        - Break down complex queries into specific searchable questions
        
        Return JSON format:
        {
            "intent": "product_inquiry",
            "entities": {"product": "Product A", "feature": "security"},
            "target_product": "product_a",
            "document_types": ["product_a", "support"],
            "confidence": 0.95,
            "reasoning": "User is asking about security features of Product A"
        }
        """

    async def _generate_refined_queries(self, original_query: str, intent: IntentResult) -> List[str]:
        """Generate multiple specific queries for better vector search"""
        
        system_prompt = """Break down the user query into specific, searchable questions.
        Focus on the identified product and intent.
        Generate 2-4 specific queries that would find the most relevant information.
        """
        
        user_prompt = f"""
        Original Query: {original_query}
        Target Product: {intent.target_product}
        Intent: {intent.intent}
        Entities: {intent.entities}
        
        Generate specific search queries:
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages)
        
        # Parse queries from LLM response
        queries = self._extract_queries_from_response(response)
        return queries[:4]  # Limit to 4 queries

class ContextualRAGEngine:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.document_router = DocumentRouter()
        
    async def process_query(self, context: QueryContext) -> Dict:
        """Main processing pipeline"""
        
        # Stage 1: Intent Classification + Entity Extraction
        intent_result = await self.intent_classifier.classify_intent(context)
        
        # Stage 2: Document Routing - Search in specific vector stores
        relevant_docs = await self._search_targeted_documents(
            intent_result.refined_queries,
            intent_result.document_types,
            intent_result.target_product
        )
        
        # Stage 3: Context Assembly
        search_context = self._assemble_search_context(relevant_docs, intent_result)
        
        # Stage 4: Response Generation
        response = await self._generate_contextual_response(
            context.user_query,
            search_context,
            intent_result
        )
        
        return {
            "response": response,
            "intent": intent_result.intent,
            "target_product": intent_result.target_product,
            "sources": [doc.metadata for doc in relevant_docs],
            "confidence": intent_result.confidence
        }
        
    async def _search_targeted_documents(
        self, 
        queries: List[str], 
        doc_types: List[DocumentType],
        target_product: Optional[str]
    ) -> List[Dict]:
        """Search in specific document collections"""
        
        all_results = []
        
        for doc_type in doc_types:
            vector_store = self.document_router.vector_stores[doc_type.value]
            
            for query in queries:
                # Add product filter if available
                filter_dict = {}
                if target_product:
                    filter_dict["product"] = target_product
                
                results = vector_store.similarity_search(
                    query=query,
                    k=3,
                    filter=filter_dict
                )
                
                # Add metadata about search context
                for result in results:
                    result.metadata["search_query"] = query
                    result.metadata["document_type"] = doc_type.value
                    result.metadata["relevance_score"] = result.metadata.get("score", 0.8)
                
                all_results.extend(results)
        
        # Deduplicate and rank results
        deduplicated_results = self._deduplicate_and_rank(all_results)
        
        return deduplicated_results[:10]  # Return top 10 most relevant

    def _assemble_search_context(self, docs: List[Dict], intent: IntentResult) -> str:
        """Assemble context from search results"""
        
        context_parts = []
        
        # Group by document type
        grouped_docs = {}
        for doc in docs:
            doc_type = doc.metadata.get("document_type", "general")
            if doc_type not in grouped_docs:
                grouped_docs[doc_type] = []
            grouped_docs[doc_type].append(doc)
        
        # Build structured context
        for doc_type, doc_list in grouped_docs.items():
            context_parts.append(f"\n--- {doc_type.upper()} INFORMATION ---")
            for doc in doc_list[:3]:  # Top 3 per category
                context_parts.append(f"Content: {doc.page_content}")
                if doc.metadata.get("title"):
                    context_parts.append(f"Source: {doc.metadata['title']}")
                context_parts.append("---")
        
        return "\n".join(context_parts)

    async def _generate_contextual_response(
        self, 
        user_query: str, 
        search_context: str, 
        intent: IntentResult
    ) -> str:
        """Generate final response using assembled context"""
        
        system_prompt = f"""You are a helpful customer service assistant for this website.
        
        User Intent: {intent.intent}
        Target Product: {intent.target_product or "General"}
        
        Guidelines:
        1. Answer based ONLY on the provided context
        2. If information isn't available, say so clearly
        3. Be specific about the product/service being discussed
        4. Provide actionable information when possible
        5. If asking for contact info, provide exact details from context
        
        Context Information:
        {search_context}
        """
        
        user_prompt = f"User Question: {user_query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages)
        return response

# Usage Example
async def handle_chatbot_request():
    engine = ContextualRAGEngine()
    
    context = QueryContext(
        user_query="sản phẩm này có tính năng bảo mật không?",
        current_page_url="https://example.com/products/product-a",
        current_page_title="Product A - Security Features",
        current_page_content="Product A overview content...",
        user_session_id="session_123"
    )
    
    result = await engine.process_query(context)
    
    return result
```

### 3. Document Organization Strategy

```python
# Document metadata structure for proper routing
document_metadata = {
    "product_a": {
        "metadata": {
            "product": "product_a",
            "document_type": "product_specs",
            "category": "features",
            "title": "Product A Security Features",
            "url": "/products/product-a/security",
            "last_updated": "2024-01-15"
        }
    },
    "product_b": {
        "metadata": {
            "product": "product_b", 
            "document_type": "product_specs",
            "category": "pricing",
            "title": "Product B Pricing Plans",
            "url": "/products/product-b/pricing"
        }
    }
}

# Vector store initialization với proper indexing
class DocumentIndexer:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200
        )
    
    def index_document(self, content: str, metadata: Dict, doc_type: DocumentType):
        """Index document vào vector store phù hợp"""
        
        chunks = self.text_splitter.split_text(content)
        
        # Enrich metadata for each chunk
        enriched_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_id": f"{metadata.get('title', 'doc')}_{i}",
                "chunk_content_preview": chunk[:100],
                "document_type": doc_type.value
            })
            enriched_metadata.append(chunk_metadata)
        
        # Add to appropriate vector store
        vector_store = self.document_router.vector_stores[doc_type.value]
        vector_store.add_texts(chunks, metadatas=enriched_metadata)
```

### 4. Frontend Integration

```javascript
// Frontend context capture
class ChatbotManager {
    constructor() {
        this.currentPageContext = this.getCurrentPageContext();
    }
    
    getCurrentPageContext() {
        return {
            url: window.location.href,
            title: document.title,
            content: this.extractPageContent(),
            product: this.extractProductFromURL(),
            section: this.getCurrentSection()
        };
    }
    
    async sendMessage(userMessage) {
        const payload = {
            message: userMessage,
            context: this.currentPageContext,
            session_id: this.getSessionId()
        };
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        return response.json();
    }
    
    extractProductFromURL() {
        const path = window.location.pathname;
        const productMatch = path.match(/\/products\/([^\/]+)/);
        return productMatch ? productMatch[1] : null;
    }
}
```

### 5. Monitoring và Optimization

```python
class RAGAnalytics:
    def __init__(self):
        self.metrics = {}
    
    def track_query_performance(self, query_id: str, metrics: Dict):
        """Track performance metrics"""
        self.metrics[query_id] = {
            "intent_classification_time": metrics.get("intent_time"),
            "vector_search_time": metrics.get("search_time"), 
            "response_generation_time": metrics.get("generation_time"),
            "documents_retrieved": metrics.get("doc_count"),
            "user_satisfaction": None,  # To be updated via feedback
            "timestamp": time.time()
        }
    
    def analyze_routing_accuracy(self):
        """Analyze if documents are being routed correctly"""
        # Implementation for analyzing routing success rate
        pass
```

Hệ thống này sẽ giải quyết chính xác vấn đề bạn đề cập - phân loại tài liệu theo chủ đề, context-aware routing, và tránh lộn xộn thông tin giữa các sản phẩm khác nhau. Bạn có muốn tôi detail thêm phần nào không?

Rất tốt! Bạn hỏi đúng những câu hỏi cốt lõi. Tôi sẽ giải thích chi tiết từng phần và so sánh FAISS vs các giải pháp khác.

## 1. LLM Routing Decision - Cách LLM Biết Truy Xuất Tài Liệu Nào

### Approach 1: Router Model + Metadata Filtering (Recommended)

```python
import faiss
import numpy as np
from typing import Dict, List, Tuple
import json
from dataclasses import dataclass
from enum import Enum

@dataclass
class DocumentCollection:
    name: str
    description: str
    keywords: List[str]
    vector_index: faiss.Index
    metadata_store: Dict[str, Dict]
    doc_count: int

class DocumentRouter:
    def __init__(self):
        # Định nghĩa các collection documents
        self.collections = {
            'product_a_features': DocumentCollection(
                name='product_a_features',
                description='Tính năng và đặc điểm của Sản phẩm A',
                keywords=['tính năng', 'feature', 'chức năng', 'product a', 'sản phẩm a'],
                vector_index=None,  # Sẽ load sau
                metadata_store={},
                doc_count=0
            ),
            'product_a_pricing': DocumentCollection(
                name='product_a_pricing',
                description='Giá cả và gói dịch vụ Sản phẩm A',
                keywords=['giá', 'pricing', 'cost', 'gói', 'plan', 'product a'],
                vector_index=None,
                metadata_store={},
                doc_count=0
            ),
            'product_b_features': DocumentCollection(
                name='product_b_features', 
                description='Tính năng và đặc điểm của Sản phẩm B',
                keywords=['tính năng', 'feature', 'chức năng', 'product b', 'sản phẩm b'],
                vector_index=None,
                metadata_store={},
                doc_count=0
            ),
            'warranty_support': DocumentCollection(
                name='warranty_support',
                description='Thông tin bảo hành và hỗ trợ khách hàng',
                keywords=['bảo hành', 'warranty', 'support', 'hỗ trợ', 'khách hàng'],
                vector_index=None,
                metadata_store={},
                doc_count=0
            ),
            'contact_info': DocumentCollection(
                name='contact_info',
                description='Thông tin liên hệ và địa chỉ công ty',
                keywords=['liên hệ', 'contact', 'địa chỉ', 'phone', 'email'],
                vector_index=None,
                metadata_store={},
                doc_count=0
            )
        }
        
        self.router_llm = self._initialize_router_llm()
        self.embedding_model = self._initialize_embeddings()
        
    async def route_query(self, query: str, page_context: Dict) -> List[str]:
        """
        Quyết định collection nào cần search dựa trên:
        1. LLM analysis của query
        2. Page context (URL, title)  
        3. Keyword matching
        """
        
        # Step 1: LLM-based routing decision
        llm_routing = await self._llm_route_decision(query, page_context)
        
        # Step 2: Keyword-based backup routing
        keyword_routing = self._keyword_route_decision(query, page_context)
        
        # Step 3: Combine và rank collections
        final_collections = self._combine_routing_decisions(llm_routing, keyword_routing)
        
        return final_collections

    async def _llm_route_decision(self, query: str, page_context: Dict) -> Dict[str, float]:
        """LLM quyết định collection nào relevant nhất"""
        
        # Build routing prompt
        collections_info = ""
        for name, collection in self.collections.items():
            collections_info += f"""
            Collection: {name}
            Description: {collection.description}
            Keywords: {', '.join(collection.keywords)}
            Document Count: {collection.doc_count}
            ---
            """
        
        system_prompt = f"""You are a document router for a RAG system.
        
        Available Document Collections:
        {collections_info}
        
        Your task: Analyze the user query and page context, then return a JSON with relevance scores (0.0-1.0) for each collection.
        
        Consider:
        1. Query intent and entities
        2. Current page context (URL, title)
        3. Semantic similarity to collection descriptions
        
        Return format:
        {{
            "product_a_features": 0.9,
            "product_a_pricing": 0.1,
            "product_b_features": 0.0,
            "warranty_support": 0.3,
            "contact_info": 0.1,
            "reasoning": "User is asking about Product A features while on Product A page"
        }}
        """
        
        user_prompt = f"""
        User Query: "{query}"
        Current Page URL: {page_context.get('url', 'unknown')}
        Page Title: {page_context.get('title', 'unknown')}
        Page Product: {page_context.get('product', 'unknown')}
        
        Determine relevance scores for each document collection.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages)
        
        try:
            routing_result = json.loads(response)
            return {k: v for k, v in routing_result.items() if k != 'reasoning' and isinstance(v, (int, float))}
        except:
            # Fallback to keyword routing
            return {}

    def _keyword_route_decision(self, query: str, page_context: Dict) -> Dict[str, float]:
        """Backup routing dựa trên keyword matching"""
        
        query_lower = query.lower()
        page_url = page_context.get('url', '').lower()
        page_title = page_context.get('title', '').lower()
        
        scores = {}
        
        for name, collection in self.collections.items():
            score = 0.0
            
            # Query keyword matching
            for keyword in collection.keywords:
                if keyword.lower() in query_lower:
                    score += 0.3
            
            # Page context matching
            for keyword in collection.keywords:
                if keyword.lower() in page_url or keyword.lower() in page_title:
                    score += 0.2
            
            scores[name] = min(score, 1.0)  # Cap at 1.0
        
        return scores

    def _combine_routing_decisions(self, llm_scores: Dict[str, float], keyword_scores: Dict[str, float]) -> List[str]:
        """Combine LLM và keyword routing, return ordered list"""
        
        combined_scores = {}
        
        for collection_name in self.collections.keys():
            llm_score = llm_scores.get(collection_name, 0.0)
            keyword_score = keyword_scores.get(collection_name, 0.0)
            
            # Weighted combination: LLM 70%, Keywords 30%
            combined_score = (llm_score * 0.7) + (keyword_score * 0.3)
            combined_scores[collection_name] = combined_score
        
        # Sort by score, return top collections with score > threshold
        sorted_collections = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return collections với score >= 0.3
        relevant_collections = [name for name, score in sorted_collections if score >= 0.3]
        
        # Ensure at least 1 collection (fallback)
        if not relevant_collections:
            relevant_collections = [sorted_collections[0][0]]
        
        return relevant_collections[:3]  # Max 3 collections
```

## 2. Database Architecture: Single vs Multiple

### Recommended: Hybrid Approach với FAISS

```python
class FAISSCollectionManager:
    def __init__(self, base_path: str = "./faiss_indices"):
        self.base_path = base_path
        self.collections = {}
        self.embedding_dim = 1536  # OpenAI ada-002 dimension
        
        # Initialize collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize separate FAISS indices for each collection"""
        
        collection_configs = {
            'product_a_features': {'index_type': 'flat', 'nlist': 100},
            'product_a_pricing': {'index_type': 'flat', 'nlist': 50},  
            'product_b_features': {'index_type': 'flat', 'nlist': 100},
            'warranty_support': {'index_type': 'flat', 'nlist': 50},
            'contact_info': {'index_type': 'flat', 'nlist': 20}
        }
        
        for collection_name, config in collection_configs.items():
            # Create FAISS index based on expected size
            if config['index_type'] == 'flat':
                # For smaller collections (< 10k docs) - exact search
                index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
            else:
                # For larger collections - approximate search  
                quantizer = faiss.IndexFlatIP(self.embedding_dim)
                index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, config['nlist'])
            
            # Wrap với ID mapping để track metadata
            index = faiss.IndexIDMap2(index)
            
            self.collections[collection_name] = {
                'index': index,
                'metadata': {},  # document_id -> metadata mapping
                'embeddings': {},  # document_id -> embedding mapping  
                'doc_count': 0,
                'config': config
            }

    def add_documents(self, collection_name: str, documents: List[Dict]):
        """Add documents to specific collection"""
        
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        collection = self.collections[collection_name]
        
        # Generate embeddings
        texts = [doc['content'] for doc in documents]
        embeddings = self._generate_embeddings(texts)
        
        # Prepare data for FAISS
        doc_ids = []
        embedding_matrix = []
        
        for i, doc in enumerate(documents):
            doc_id = doc.get('id') or f"{collection_name}_{collection['doc_count'] + i}"
            
            # Store metadata
            collection['metadata'][doc_id] = {
                'id': doc_id,
                'content': doc['content'],
                'title': doc.get('title', ''),
                'url': doc.get('url', ''),
                'product': doc.get('product', ''),
                'category': doc.get('category', ''),
                'last_updated': doc.get('last_updated', ''),
                'collection': collection_name
            }
            
            doc_ids.append(hash(doc_id) % (2**63))  # Convert to int64 for FAISS
            embedding_matrix.append(embeddings[i])
        
        # Add to FAISS index
        embedding_matrix = np.array(embedding_matrix).astype('float32')
        collection['index'].add_with_ids(embedding_matrix, np.array(doc_ids))
        collection['doc_count'] += len(documents)
        
        # Save index to disk
        self._save_collection(collection_name)
        
    def search_collections(self, query: str, collection_names: List[str], top_k: int = 5) -> List[Dict]:
        """Search across specified collections"""
        
        query_embedding = self._generate_embeddings([query])[0]
        query_vector = np.array([query_embedding]).astype('float32')
        
        all_results = []
        
        for collection_name in collection_names:
            if collection_name not in self.collections:
                continue
                
            collection = self.collections[collection_name]
            
            # Search in FAISS index
            scores, doc_ids = collection['index'].search(query_vector, top_k)
            
            # Convert results to readable format
            for i, (score, doc_id) in enumerate(zip(scores[0], doc_ids[0])):
                if doc_id == -1:  # FAISS returns -1 for no result
                    continue
                
                # Find metadata by doc_id
                metadata = None
                for stored_id, meta in collection['metadata'].items():
                    if hash(stored_id) % (2**63) == doc_id:
                        metadata = meta.copy()
                        break
                
                if metadata:
                    metadata['score'] = float(score)
                    metadata['collection'] = collection_name
                    metadata['search_query'] = query
                    all_results.append(metadata)
        
        # Sort all results by score and return top results
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:top_k * 2]  # Return more results for diversity

    def _save_collection(self, collection_name: str):
        """Save FAISS index to disk"""
        collection = self.collections[collection_name]
        index_path = f"{self.base_path}/{collection_name}.index"
        metadata_path = f"{self.base_path}/{collection_name}_metadata.json"
        
        # Save FAISS index
        faiss.write_index(collection['index'], index_path)
        
        # Save metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(collection['metadata'], f, ensure_ascii=False, indent=2)

    def load_collections(self):
        """Load existing indices from disk"""
        import os
        
        for collection_name in self.collections.keys():
            index_path = f"{self.base_path}/{collection_name}.index" 
            metadata_path = f"{self.base_path}/{collection_name}_metadata.json"
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.collections[collection_name]['index'] = faiss.read_index(index_path)
                
                # Load metadata
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.collections[collection_name]['metadata'] = json.load(f)
                    
                self.collections[collection_name]['doc_count'] = len(
                    self.collections[collection_name]['metadata']
                )
```

## 3. FAISS vs Alternatives - Analysis Chi Tiết

### FAISS Strengths cho Use Case Của Bạn:

```python
# FAISS Performance Comparison
class FAISSBenchmark:
    def __init__(self):
        self.results = {}
    
    def benchmark_search_performance(self):
        """So sánh FAISS với alternatives"""
        
        # FAISS advantages for your use case:
        advantages = {
            "speed": "Cực nhanh cho < 100K documents per collection",
            "memory": "Efficient memory usage, có thể load/unload collections",
            "flexibility": "Multiple index types (Flat, IVF, HNSW)", 
            "cost": "Completely free, no API costs",
            "control": "Full control over data, no external dependencies",
            "offline": "Works completely offline",
            "customization": "Easy to customize distance metrics"
        }
        
        # Disadvantages:
        disadvantages = {
            "complexity": "More complex setup vs managed solutions",
            "maintenance": "Need to handle index updates, backups",
            "scaling": "Manual scaling vs auto-scaling of cloud solutions"
        }
        
        return advantages, disadvantages
```

### Recommended Architecture cho Your Use Case:

```python
class OptimalRAGArchitecture:
    """
    Kiến trúc tối ưu cho 4-10 pages content với multiple topics
    """
    
    def __init__(self):
        # Multiple FAISS collections approach
        self.faiss_manager = FAISSCollectionManager()
        self.router = DocumentRouter()
        
        # Collection strategy cho bạn:
        self.collection_strategy = {
            "approach": "topic-based_separation",
            "reasoning": """
            1. 4-10 trang content = ~20-50K tokens = ~1000-3000 chunks
            2. Multiple topics cần tách biệt để avoid confusion
            3. FAISS IndexFlatIP perfect cho size này (exact search)
            4. Separate collections = better precision, less noise
            """,
            
            "collections": {
                "product_a": "Tất cả content về sản phẩm A",
                "product_b": "Tất cả content về sản phẩm B", 
                "pricing": "Pricing cho tất cả products",
                "support": "Support, warranty, technical docs",
                "company": "Company info, contact, about us"
            }
        }

    def get_architecture_recommendation(self):
        return """
        RECOMMENDED SETUP:
        
        1. DATABASE STRATEGY: Multiple FAISS Collections
           ✅ Separate FAISS index per topic/product
           ✅ Shared embedding model (OpenAI ada-002 or sentence-transformers)
           ✅ Local storage with periodic backups
        
        2. ROUTING STRATEGY: LLM + Keyword Hybrid
           ✅ LLM analyzes query intent + page context
           ✅ Keyword backup for reliability  
           ✅ Search top 2-3 most relevant collections
        
        3. FAISS CONFIGURATION:
           ✅ IndexFlatIP for exact search (your data size < 10K per collection)
           ✅ IndexIDMap2 for metadata tracking
           ✅ Normalize embeddings for cosine similarity
        
        4. SCALABILITY PATH:
           - Start: FAISS local files
           - Growth: Redis + FAISS for caching
           - Scale: Migrate to Pinecone/Weaviate if needed
        """
```

### Implementation Example:

```python
# Complete working example
async def main():
    # Initialize system
    faiss_manager = FAISSCollectionManager()
    router = DocumentRouter()
    
    # Add documents to collections
    product_a_docs = [
        {
            "content": "Sản phẩm A có tính năng bảo mật cao với mã hóa AES-256...",
            "title": "Tính năng bảo mật Product A",
            "product": "product_a",
            "category": "security"
        }
        # ... more docs
    ]
    
    faiss_manager.add_documents("product_a_features", product_a_docs)
    
    # Process user query  
    user_query = "sản phẩm này có tính năng bảo mật không?"
    page_context = {
        "url": "https://example.com/products/product-a",
        "title": "Product A Features",
        "product": "product_a"
    }
    
    # Route query to collections
    target_collections = await router.route_query(user_query, page_context)
    print(f"Routing to: {target_collections}")
    
    # Search in targeted collections
    results = faiss_manager.search_collections(user_query, target_collections, top_k=5)
    
    # Generate response with context
    context = "\n".join([doc['content'] for doc in results[:3]])
    response = await generate_response(user_query, context)
    
    return response
```

**Kết luận**: FAISS rất phù hợp cho use case của bạn. Với 4-10 trang content và multiple topics, multiple FAISS collections + LLM routing sẽ cho kết quả chính xác nhất và cost-effective nhất.
