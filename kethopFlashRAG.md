Vấn đề bạn gặp phải là **circular import** trong flashrag_core module. Tôi thấy nguyên nhân và sẽ giúp bạn fix:

## Vấn đề chính:

1. **Files thiếu**: Các file `DenseRetriever`, `SparseRetriever` etc. chưa được copy vào
2. **Circular import**: `flashrag_core/__init__.py` đang import từ modules chưa tồn tại
3. **Import structure sai**: Cấu trúc import không đúng

## Giải pháp:

### 1. Fix flashrag_core/__init__.py

```python
# flashrag_core/__init__.py
"""
FlashRAG Core Integration - Fixed version
"""

# Thay vì import trực tiếp, chỉ expose những gì thực sự có
__version__ = "1.0.0"

# Import conditionally để tránh lỗi khi modules không tồn tại
def safe_import():
    """Safely import available modules"""
    available_modules = {}
    
    try:
        from .retriever.dense_retriever import DenseRetriever
        available_modules['DenseRetriever'] = DenseRetriever
    except ImportError:
        pass
    
    try:
        from .retriever.sparse_retriever import SparseRetriever  
        available_modules['SparseRetriever'] = SparseRetriever
    except ImportError:
        pass
        
    try:
        from .utils.chunkie import Chunkie
        available_modules['Chunkie'] = Chunkie
    except ImportError:
        pass
        
    return available_modules

# Initialize available modules
_modules = safe_import()
globals().update(_modules)

# Define what's available for import
__all__ = list(_modules.keys())
```

### 2. Fix các __init__.py files trong submodules

```python
# flashrag_core/retriever/__init__.py
"""
Retriever modules
"""

# Chỉ import những file thực sự tồn tại
try:
    from .dense_retriever import DenseRetriever
except ImportError:
    DenseRetriever = None

try:
    from .sparse_retriever import SparseRetriever
except ImportError:
    SparseRetriever = None

# Chỉ export những gì available
__all__ = []
if DenseRetriever is not None:
    __all__.append('DenseRetriever')
if SparseRetriever is not None:
    __all__.append('SparseRetriever')
```

### 3. Tạo Mock Classes cho các modules thiếu

```python
# flashrag_core/retriever/dense_retriever.py
"""
Dense Retriever - Mock implementation
"""

class DenseRetriever:
    """Mock Dense Retriever implementation"""
    
    def __init__(self, model_path: str, index_path: str = None, device: str = "cpu"):
        self.model_path = model_path
        self.index_path = index_path
        self.device = device
        print(f"Mock DenseRetriever initialized with model: {model_path}")
    
    def retrieve(self, query: str, k: int = 10):
        """Mock retrieve method"""
        print(f"Mock retrieval for query: {query[:50]}...")
        return [
            {"id": f"doc_{i}", "content": f"Mock document {i}", "score": 0.9 - i*0.1}
            for i in range(k)
        ]
    
    def encode(self, texts):
        """Mock encoding method"""
        print(f"Mock encoding {len(texts)} texts")
        import numpy as np
        return np.random.rand(len(texts), 768)  # Mock embeddings

# flashrag_core/retriever/sparse_retriever.py  
class SparseRetriever:
    """Mock Sparse Retriever implementation"""
    
    def __init__(self, index_path: str = None, config: dict = None):
        self.index_path = index_path
        self.config = config or {}
        print(f"Mock SparseRetriever initialized")
    
    def retrieve(self, query: str, k: int = 10):
        """Mock retrieve method"""
        print(f"Mock sparse retrieval for query: {query[:50]}...")
        return [
            {"id": f"sparse_doc_{i}", "content": f"Mock sparse document {i}", "score": 0.8 - i*0.08}
            for i in range(k)
        ]

# flashrag_core/utils/chunkie.py
class Chunkie:
    """Mock Chunkie implementation"""
    
    def __init__(self, method: str = "semantic", **kwargs):
        self.method = method
        self.config = kwargs
        print(f"Mock Chunkie initialized with method: {method}")
    
    def chunk_text(self, text: str):
        """Mock chunking method"""
        print(f"Mock chunking text of length: {len(text)}")
        # Simple sentence-based chunking
        sentences = text.split('.')
        chunks = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                chunk = type('Chunk', (), {
                    'text': sentence.strip(),
                    'start_pos': i * 100,
                    'end_pos': (i + 1) * 100,
                    'token_count': len(sentence.split())
                })()
                chunks.append(chunk)
        
        return chunks
```

### 4. Fix core/flashrag_processor.py

```python
# core/flashrag_processor.py
"""
FlashRAG Processor với error handling
"""
import sys
import os
import logging

logger = logging.getLogger(__name__)

class FlashRAGProcessor:
    def __init__(self, config):
        self.config = config
        self.components = {}
        self.fallback_mode = False
        
    async def initialize_components(self):
        """Initialize FlashRAG components với fallback"""
        
        try:
            # Try to import FlashRAG components
            from flashrag_core import safe_import
            available_modules = safe_import()
            
            if 'DenseRetriever' in available_modules:
                DenseRetriever = available_modules['DenseRetriever']
                self.components['dense_retriever'] = DenseRetriever(
                    model_path=self.config.get("E5_MODEL_PATH", "intfloat/e5-base-v2")
                )
                logger.info("DenseRetriever initialized")
            
            if 'SparseRetriever' in available_modules:
                SparseRetriever = available_modules['SparseRetriever'] 
                self.components['sparse_retriever'] = SparseRetriever()
                logger.info("SparseRetriever initialized")
            
            if 'Chunkie' in available_modules:
                Chunkie = available_modules['Chunkie']
                self.components['chunker'] = Chunkie(method="semantic")
                logger.info("Chunkie initialized")
                
            logger.info(f"FlashRAG components initialized: {list(self.components.keys())}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize FlashRAG components: {e}")
            await self._fallback_initialization()
    
    async def _fallback_initialization(self):
        """Fallback nếu FlashRAG components fail"""
        logger.info("Using fallback mock components...")
        self.fallback_mode = True
        
        # Simple fallback implementations
        self.components = {
            'dense_retriever': self._mock_dense_retriever(),
            'sparse_retriever': self._mock_sparse_retriever(),  
            'chunker': self._mock_chunker()
        }
    
    def _mock_dense_retriever(self):
        class MockRetriever:
            def retrieve(self, query, k=10):
                return [{"id": f"mock_{i}", "content": f"Mock result {i}"} for i in range(k)]
        return MockRetriever()
    
    def _mock_sparse_retriever(self):
        class MockSparseRetriever:
            def retrieve(self, query, k=10):
                return [{"id": f"sparse_mock_{i}", "content": f"Mock sparse result {i}"} for i in range(k)]
        return MockSparseRetriever()
    
    def _mock_chunker(self):
        class MockChunker:
            def chunk_text(self, text):
                sentences = text.split('.')
                return [type('Chunk', (), {'text': s.strip()})() for s in sentences if s.strip()]
        return MockChunker()
    
    async def process_query(self, query: str, method: str = "dense"):
        """Process query với available components"""
        
        if method == "dense" and "dense_retriever" in self.components:
            return self.components["dense_retriever"].retrieve(query)
        elif method == "sparse" and "sparse_retriever" in self.components:
            return self.components["sparse_retriever"].retrieve(query)
        else:
            logger.warning(f"Method {method} not available, using fallback")
            return [{"id": "fallback", "content": "Fallback response"}]
    
    def get_status(self):
        """Get processor status"""
        return {
            "fallback_mode": self.fallback_mode,
            "available_components": list(self.components.keys()),
            "status": "initialized"
        }
```

### 5. Fix main.py imports

```python
# main.py - Fixed imports
"""
Main CLI interface cho FlashRAG Data Management System
"""
import asyncio
import click
import logging
from pathlib import Path
from typing import List, Optional

# Import với error handling
try:
    from core.collection_manager import EnhancedCollectionManager
except ImportError as e:
    print(f"Warning: Could not import EnhancedCollectionManager: {e}")
    EnhancedCollectionManager = None

try:
    from core.flashrag_processor import FlashRAGProcessor
except ImportError as e:
    print(f"Warning: Could not import FlashRAGProcessor: {e}")
    FlashRAGProcessor = None

try:
    from utils.flashrag_adapter import FlashRAGAdapter
except ImportError as e:
    print(f"Warning: Could not import FlashRAGAdapter: {e}")
    FlashRAGAdapter = None

try:
    from utils.jsonl_handler import JSONLHandler
except ImportError as e:
    print(f"Warning: Could not import JSONLHandler: {e}")
    JSONLHandler = None

try:
    from config.settings import settings
except ImportError as e:
    print(f"Warning: Could not import settings: {e}")
    settings = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@click.group()
def cli():
    """FlashRAG Data Management CLI"""
    pass

@cli.command()
def test():
    """Test basic functionality"""
    print("Testing FlashRAG integration...")
    
    if FlashRAGProcessor:
        processor = FlashRAGProcessor({})
        asyncio.run(processor.initialize_components())
        status = processor.get_status()
        print(f"Processor status: {status}")
    else:
        print("FlashRAGProcessor not available")
    
    print("Test completed!")

@cli.command()
def status():
    """Show system status"""
    components = {
        "EnhancedCollectionManager": EnhancedCollectionManager is not None,
        "FlashRAGProcessor": FlashRAGProcessor is not None,
        "FlashRAGAdapter": FlashRAGAdapter is not None,
        "JSONLHandler": JSONLHandler is not None,
        "Settings": bool(settings)
    }
    
    print("System Component Status:")
    for component, available in components.items():
        status = "✓ Available" if available else "✗ Not Available"
        print(f"  {component}: {status}")

if __name__ == "__main__":
    cli()
```

### 6. Test the fixes:

```bash
# Test basic import
python -c "from flashrag_core import safe_import; print('Import test passed')"

# Test main
python main.py status

# Test processor
python main.py test
```

Những fixes này sẽ:

1. **Tránh circular imports** bằng cách sử dụng safe_import()
2. **Graceful fallback** khi modules không tồn tại
3. **Mock implementations** để system vẫn chạy được
4. **Better error handling** trong tất cả imports

Hãy thử chạy lại và cho tôi biết kết quả!


Tôi vừa có ý tưởng tích hợp FlashRAG https://github.com/RUC-NLPIR/FlashRAG vào hệ thống quản trị dababase chatbot chăm sóc khách hàng của mình. Bạn hãy tạo cho tôi một thiết kế architectManageDB mới ứng dụng FlashRAG cho LLM thực hiện nhé. Các cấu hình database thì giữ nguyên như cũ.

# Kiến Trúc FlashRAG-Enhanced Data Management Tool cho Enterprise Chatbot

## 1. Tổng Quan Kiến Trúc Tích Hợp FlashRAG

### 1.1 Mục Tiêu Chính
- Tích hợp 17+ thuật toán RAG từ FlashRAG để nâng cao khả năng retrieval
- Sử dụng Chunkie cho phân đoạn tài liệu thông minh
- Áp dụng Refiner (LongLLMLingua, Selective-Context) để tối ưu context
- Kết hợp Dense/Sparse retrieval với FAISS và BM25s
- Hỗ trợ multi-hop reasoning và fact verification
- Tương thích với hệ thống database hiện tại (PostgreSQL, Redis)

### 1.2 Kiến Trúc High-Level với FlashRAG Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 FLASHRAG-ENHANCED DATA MANAGEMENT TOOL                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI Interface                FlashRAG-UI Integration                        │
│  ├─ RAG Pipeline Control     ├─ Visual Pipeline Builder                      │
│  ├─ Algorithm Selection      ├─ Real-time Evaluation                         │
│  ├─ Quality Metrics          ├─ Performance Dashboard                        │
│  └─ Batch Processing         └─ Configuration Manager                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                        FLASHRAG PROCESSING ENGINE                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Document Parser  │  │ Chunkie Processor│  │ FlashRAG Refiner │           │
│  │ - PDF/DOCX/MD    │  │ - Semantic Split │  │ - LongLLMLingua  │           │
│  │ - Structure Det  │  │ - Token-based    │  │ - Selective-Ctx  │           │
│  │ - FlashRAG JSONL │  │ - Sentence-based │  │ - Trace Refiner  │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Multi-Retriever  │  │ RAG Pipeline Mgr │  │ Quality Engine   │           │
│  │ - Dense (E5/BGE) │  │ - 17 Algorithms  │  │ - FlashRAG Eval  │           │
│  │ - Sparse (BM25s) │  │ - Sequential     │  │ - Custom Metrics │           │
│  │ - Hybrid Fusion  │  │ - Iterative      │  │ - Coherence Score│           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
├─────────────────────────────────────────────────────────────────────────────┤
│                        ENHANCED STORAGE LAYER                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ FAISS + BM25s    │  │ PostgreSQL Meta  │  │ Redis + Pipeline │           │
│  │ - Dense Indices  │  │ - FlashRAG Data  │  │ - RAG Cache      │           │
│  │ - Sparse Indices │  │ - Eval Results   │  │ - Pipeline State │           │
│  │ - Hybrid Search  │  │ - Quality Scores │  │ - Model Cache    │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Cấu Trúc Project Tích Hợp FlashRAG

```
flashrag_data_manager/
├── main.py                      # CLI với FlashRAG commands
├── config/
│   ├── __init__.py
│   ├── settings.py              # Load từ .env + FlashRAG configs
│   ├── collections.yaml         # Collection + RAG algorithm mapping
│   └── flashrag_configs/        # FlashRAG algorithm configs
│       ├── standard_rag.yaml
│       ├── ret_robust.yaml
│       └── r1_searcher.yaml
├── core/
│   ├── __init__.py
│   ├── flashrag_processor.py    # FlashRAG integration layer
│   ├── chunkie_processor.py     # Chunkie-based chunking
│   ├── multi_retriever.py       # Dense + Sparse retrieval
│   ├── rag_pipeline_manager.py  # 17 RAG algorithms
│   ├── refiner_engine.py        # LongLLMLingua, Selective-Context
│   └── collection_manager.py    # Enhanced FAISS + BM25s
├── models/
│   ├── __init__.py
│   ├── flashrag_document.py     # FlashRAG JSONL format
│   ├── rag_evaluation.py        # Evaluation metrics
│   └── pipeline_results.py      # RAG pipeline outputs
├── utils/
│   ├── __init__.py
│   ├── jsonl_handler.py         # JSONL I/O operations
│   ├── flashrag_adapter.py      # PostgreSQL ↔ JSONL converter
│   ├── evaluation_metrics.py    # Custom + FlashRAG metrics
│   └── pipeline_tracker.py      # Pipeline execution tracking
├── web/
│   ├── __init__.py
│   ├── flashrag_ui_integration.py # FlashRAG-UI wrapper
│   ├── app.py                   # FastAPI với RAG endpoints
│   └── templates/               # Enhanced UI templates
├── algorithms/                  # Custom RAG implementations
│   ├── __init__.py
│   ├── custom_sequential.py
│   ├── enhanced_ret_robust.py
│   └── domain_specific_rag.py
├── tests/
│   ├── __init__.py
│   ├── test_flashrag_integration.py
│   ├── test_rag_algorithms.py
│   └── sample_datasets/
├── requirements.txt             # Thêm FlashRAG dependencies
└── README.md
```

## 2. Chi Tiết Components Tích Hợp FlashRAG

### 2.1 FlashRAG Document Schema & Metadata Mapping

```python
# FlashRAG JSONL Format với Custom Extensions
{
    "id": "PA_FEAT_001_v1",           # Tương thích với schema cũ
    "contents": "Sản phẩm A cung cấp...", # FlashRAG standard field
    "title": "Product A Security Features",
    "metadata": {
        "collection": "product_a_features",
        "category": "security", 
        "product": "product_a",
        "keywords": ["security", "authentication"],
        "auto_keywords": ["bảo mật", "xác thực"],
        "source_file": "product_a_security.pdf",
        "page_numbers": [1, 2, 3],
        "chunk_index": 0,
        "chunk_total": 5,
        "quality_score": 0.85,
        "flashrag_score": 0.92,         # FlashRAG quality metric
        "coherence_score": 0.88,        # Refiner output
        "compression_ratio": 0.75,      # LongLLMLingua output
        "created_at": "2025-01-20T10:30:00Z",
        "rag_algorithms": ["standard_rag", "ret_robust"] # Supported algorithms
    }
}
```

### 2.2 Multi-Retriever Architecture

```python
# core/multi_retriever.py
from flashrag.retriever import DenseRetriever, SparseRetriever
from flashrag.utils import pooling

class MultiRetriever:
    def __init__(self, config):
        # Dense retrievers
        self.e5_retriever = DenseRetriever(
            model_path=config.e5_model_path,
            index_path=config.faiss_index_path,
            pooling_method="mean"
        )
        
        self.bge_retriever = DenseRetriever(
            model_path=config.bge_model_path, 
            index_path=config.faiss_index_path,
            pooling_method="cls"
        )
        
        # Sparse retriever
        self.bm25_retriever = SparseRetriever(
            index_path=config.bm25_index_path,
            config=config.bm25_config
        )
        
    async def hybrid_search(self, query: str, k: int = 10) -> List[Document]:
        """Kết hợp Dense + Sparse retrieval"""
        # Dense results
        dense_results_e5 = await self.e5_retriever.retrieve(query, k=k//2)
        dense_results_bge = await self.bge_retriever.retrieve(query, k=k//2)
        
        # Sparse results  
        sparse_results = await self.bm25_retriever.retrieve(query, k=k)
        
        # Fusion strategy (RRF - Reciprocal Rank Fusion)
        fused_results = self.reciprocal_rank_fusion([
            dense_results_e5, dense_results_bge, sparse_results
        ], k=k)
        
        return fused_results
```

### 2.3 RAG Pipeline Manager với 17 Thuật Toán

```python
# core/rag_pipeline_manager.py
from flashrag.pipeline import SequentialPipeline, IterativePipeline
from flashrag.config import Config

class RAGPipelineManager:
    def __init__(self, config):
        self.config = config
        self.available_algorithms = {
            'standard_rag': self._setup_standard_rag,
            'ret_robust': self._setup_ret_robust,
            'r1_searcher': self._setup_r1_searcher,
            'flare': self._setup_flare,
            'spring': self._setup_spring,
            # ... thêm 12 algorithms khác
        }
    
    async def run_algorithm(self, algorithm: str, query: str, 
                          context: PageContext) -> RAGResult:
        """Chạy thuật toán RAG cụ thể"""
        
        if algorithm not in self.available_algorithms:
            raise ValueError(f"Algorithm {algorithm} not supported")
        
        pipeline = self.available_algorithms[algorithm]()
        
        # Tạo FlashRAG dataset format
        dataset_item = {
            "id": f"query_{uuid.uuid4().hex[:8]}",
            "question": query,
            "golden_answers": [],  # Sẽ được fill sau evaluation
            "metadata": {
                "collection": context.product or "general",
                "url": context.url,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Chạy pipeline
        result = pipeline.run([dataset_item], do_eval=False)
        
        return self._format_result(result, context)
    
    def _setup_standard_rag(self):
        """Standard RAG: Retrieve → Generate"""
        config_dict = {
            "retrieval_method": "e5",
            "generator_model": "llama3-8b-instruct", 
            "retrieval_topk": 5,
            "max_input_len": 2048,
            "dataset_name": "custom",
            "save_intermediate_data": True
        }
        return SequentialPipeline(Config(config_dict=config_dict))
    
    def _setup_ret_robust(self):
        """Ret-Robust: Multiple retrieval với robust ranking"""
        config_dict = {
            "retrieval_method": ["e5", "bge", "bm25"],
            "rerank_model": "bge-reranker-large",
            "fusion_method": "rrf",
            "robust_threshold": 0.7,
            "generator_model": "llama3-8b-instruct"
        }
        return SequentialPipeline(Config(config_dict=config_dict))
    
    def _setup_r1_searcher(self):
        """R1-Searcher: Multi-hop reasoning với graph search"""
        config_dict = {
            "retrieval_method": "e5",
            "reasoning_method": "graph_search",
            "max_hops": 3,
            "search_strategy": "beam_search",
            "beam_width": 5,
            "generator_model": "llama3-8b-instruct"
        }
        return IterativePipeline(Config(config_dict=config_dict))
```

### 2.4 Chunkie Integration

```python
# core/chunkie_processor.py
from flashrag.utils.chunkie import Chunkie

class ChunkieProcessor:
    def __init__(self, config):
        self.semantic_chunker = Chunkie(
            method="semantic",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=512,
            overlap_tokens=50
        )
        
        self.token_chunker = Chunkie(
            method="token",
            max_tokens=300,
            overlap_tokens=30
        )
        
        self.sentence_chunker = Chunkie(
            method="sentence",
            max_sentences=5,
            overlap_sentences=1
        )
    
    async def chunk_document(self, content: str, method: str = "semantic",
                           **kwargs) -> List[DocumentChunk]:
        """Phân đoạn document bằng Chunkie"""
        
        chunker = getattr(self, f"{method}_chunker")
        
        # Update chunker config nếu có
        if kwargs:
            chunker.update_config(**kwargs)
        
        # Chunking
        chunks = chunker.chunk_text(content)
        
        # Convert to DocumentChunk format
        document_chunks = []
        for i, chunk in enumerate(chunks):
            doc_chunk = DocumentChunk(
                content=chunk.text,
                metadata={
                    "chunk_index": i,
                    "chunk_total": len(chunks),
                    "chunk_method": method,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    "tokens": chunk.token_count,
                    "sentences": chunk.sentence_count if hasattr(chunk, 'sentence_count') else None
                }
            )
            document_chunks.append(doc_chunk)
        
        return document_chunks
```

### 2.5 Refiner Engine với LongLLMLingua & Selective-Context

```python
# core/refiner_engine.py
from flashrag.refiner import LongLLMLinguaRefiner, SelectiveContextRefiner

class RefinerEngine:
    def __init__(self, config):
        self.longllm_refiner = LongLLMLinguaRefiner(
            model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
            compress_ratio=0.5,
            instruction_str="",
            question_str="",
            reorder_context="sort"
        )
        
        self.selective_refiner = SelectiveContextRefiner(
            model_name="microsoft/deberta-v3-base",
            reduce_ratio=0.35,
            reduce_level="sent"
        )
    
    async def refine_context(self, contexts: List[str], query: str,
                           method: str = "longllm") -> RefinerResult:
        """Tinh chỉnh context để tối ưu LLM input"""
        
        if method == "longllm":
            result = self.longllm_refiner.refine(
                contexts=contexts,
                question=query
            )
        elif method == "selective":
            result = self.selective_refiner.refine(
                contexts=contexts,
                question=query
            )
        else:
            raise ValueError(f"Unknown refiner method: {method}")
        
        return RefinerResult(
            refined_contexts=result["compressed_contexts"],
            compression_ratio=result["compress_ratio"],
            coherence_score=result.get("coherence_score", 0.0),
            relevance_score=result.get("relevance_score", 0.0),
            processing_time=result.get("processing_time", 0.0)
        )
```

## 3. Database Schema Extensions cho FlashRAG

### 3.1 PostgreSQL Schema Updates

```sql
-- Extend existing tables for FlashRAG integration
ALTER TABLE conversations ADD COLUMN rag_algorithm VARCHAR(50);
ALTER TABLE conversations ADD COLUMN flashrag_score DECIMAL(4,3);
ALTER TABLE conversations ADD COLUMN compression_ratio DECIMAL(4,3);
ALTER TABLE conversations ADD COLUMN reasoning_steps JSONB;

-- New tables for FlashRAG-specific data
CREATE TABLE rag_evaluations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    query_text TEXT NOT NULL,
    retrieved_docs JSONB NOT NULL,
    refined_contexts JSONB,
    generated_response TEXT NOT NULL,
    evaluation_metrics JSONB NOT NULL, -- precision, recall, f1, etc.
    processing_stages JSONB NOT NULL,  -- timing for each stage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE algorithm_performance (
    id SERIAL PRIMARY KEY,
    algorithm VARCHAR(50) NOT NULL,
    collection VARCHAR(100),
    avg_precision DECIMAL(4,3),
    avg_recall DECIMAL(4,3), 
    avg_f1_score DECIMAL(4,3),
    avg_response_time DECIMAL(8,3),
    total_queries INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pipeline_cache (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL UNIQUE,
    algorithm VARCHAR(50) NOT NULL,
    collection VARCHAR(100),
    cached_result JSONB NOT NULL,
    retrieval_results JSONB,
    expiry_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Redis Cache Structure for FlashRAG

```python
# Redis keys for FlashRAG caching
REDIS_KEYS = {
    # Pipeline caching
    "pipeline_result": "flashrag:pipeline:{algorithm}:{query_hash}",
    "retrieval_cache": "flashrag:retrieval:{method}:{query_hash}",
    "refiner_cache": "flashrag:refiner:{method}:{content_hash}",
    
    # Real-time metrics
    "algorithm_metrics": "flashrag:metrics:{algorithm}:daily:{date}",
    "retrieval_stats": "flashrag:retrieval:{method}:stats",
    "pipeline_queue": "flashrag:pipeline:processing_queue",
    
    # Model caching
    "model_cache": "flashrag:model:{model_name}:cache",
    "index_metadata": "flashrag:index:{collection}:metadata"
}
```

## 4. CLI Commands với FlashRAG Integration

```bash
# FlashRAG algorithm management
python main.py list-algorithms
python main.py algorithm-info --name standard_rag
python main.py benchmark-algorithm --name ret_robust --collection product_a_features

# Index building với FlashRAG
python main.py build-index --collection product_a_features --method e5 --faiss_type HNSW
python main.py build-sparse-index --collection product_a_features --method bm25s

# RAG pipeline operations  
python main.py run-pipeline --algorithm standard_rag --query "Sản phẩm A có tính năng gì?"
python main.py run-evaluation --algorithm ret_robust --dataset test_queries.jsonl

# Chunkie operations
python main.py chunk-document --file document.pdf --method semantic --max_tokens 512
python main.py optimize-chunks --collection product_a_features --method token

# Refiner operations
python main.py refine-context --algorithm longllm --compress_ratio 0.5
python main.py selective-context --reduce_ratio 0.35 --collection all

# Performance monitoring
python main.py algorithm-stats --timerange 7d
python main.py retrieval-benchmark --methods e5,bge,bm25
python main.py pipeline-health-check
```

## 5. API Endpoints với FlashRAG

```python
# web/app.py - Enhanced endpoints
@app.post("/api/chat/flashrag")
async def chat_with_flashrag(request: FlashRAGChatRequest):
    """Chat endpoint sử dụng FlashRAG algorithms"""
    
    # Algorithm selection based on query complexity
    algorithm = select_optimal_algorithm(
        query=request.message,
        context=request.context,
        history=request.history
    )
    
    # Run RAG pipeline
    result = await rag_pipeline_manager.run_algorithm(
        algorithm=algorithm,
        query=request.message,
        context=request.context
    )
    
    # Save to database
    await save_flashrag_conversation(request, result)
    
    return FlashRAGChatResponse(
        response=result.response,
        algorithm=algorithm,
        confidence=result.confidence,
        sources=result.sources,
        processing_stages=result.stages,
        evaluation_metrics=result.metrics
    )

@app.post("/api/algorithms/{algorithm}/evaluate")
async def evaluate_algorithm(algorithm: str, dataset: UploadFile):
    """Đánh giá performance của thuật toán RAG"""
    
    evaluation_results = await rag_evaluator.evaluate_algorithm(
        algorithm=algorithm,
        dataset=dataset,
        metrics=["precision", "recall", "f1", "response_time"]
    )
    
    return evaluation_results

@app.get("/api/algorithms/performance")
async def get_algorithm_performance():
    """Lấy performance statistics của các algorithms"""
    
    stats = await db_manager.get_algorithm_performance_stats()
    return stats
```

## 6. Quality Control với FlashRAG Metrics

```python
# utils/evaluation_metrics.py
from flashrag.evaluator import Evaluator

class EnhancedQualityControl:
    def __init__(self, config):
        self.flashrag_evaluator = Evaluator(config.evaluation_config)
        self.custom_metrics = CustomMetrics()
    
    async def evaluate_document_quality(self, document: FlashRAGDocument) -> QualityReport:
        """Đánh giá chất lượng document với FlashRAG metrics"""
        
        # FlashRAG built-in evaluation
        flashrag_scores = await self.flashrag_evaluator.evaluate_document(
            document.contents,
            metrics=["coherence", "relevance", "factuality"]
        )
        
        # Custom evaluation
        custom_scores = {
            "word_count": len(document.contents.split()),
            "sentence_count": len(document.contents.split('.')),
            "readability_score": self.custom_metrics.readability(document.contents),
            "keyword_density": self.custom_metrics.keyword_density(document),
            "language_confidence": self.custom_metrics.language_detection(document.contents)
        }
        
        # Combined quality score
        quality_score = self._calculate_combined_score(flashrag_scores, custom_scores)
        
        return QualityReport(
            flashrag_scores=flashrag_scores,
            custom_scores=custom_scores,
            overall_quality=quality_score,
            recommendations=self._generate_recommendations(flashrag_scores, custom_scores)
        )
```

## 7. Monitoring và Analytics Dashboard

```python
# web/flashrag_ui_integration.py
from flashrag.ui import FlashRAGUI

class EnhancedDashboard:
    def __init__(self, config):
        self.flashrag_ui = FlashRAGUI(config.flashrag_ui_config)
        
    async def get_dashboard_data(self):
        """Tạo dashboard data kết hợp FlashRAG metrics"""
        
        return {
            "algorithm_performance": await self.get_algorithm_metrics(),
            "retrieval_analytics": await self.get_retrieval_analytics(),
            "quality_trends": await self.get_quality_trends(),
            "pipeline_health": await self.get_pipeline_health(),
            "flashrag_insights": await self.flashrag_ui.get_insights()
        }
    
    async def get_algorithm_metrics(self):
        """Metrics cho từng RAG algorithm"""
        algorithms = ["standard_rag", "ret_robust", "r1_searcher", "flare"]
        
        metrics = {}
        for algorithm in algorithms:
            metrics[algorithm] = {
                "avg_precision": await self.db.get_avg_precision(algorithm),
                "avg_recall": await self.db.get_avg_recall(algorithm), 
                "avg_f1": await self.db.get_avg_f1(algorithm),
                "avg_response_time": await self.db.get_avg_response_time(algorithm),
                "usage_count": await self.db.get_usage_count(algorithm),
                "success_rate": await self.db.get_success_rate(algorithm)
            }
        
        return metrics
```

## Đánh Giá Thiết Kế FlashRAG-Enhanced

**Ưu điểm của thiết kế tích hợp**:

1. **Khả năng RAG mạnh mẽ**: 17 thuật toán RAG tiên tiến từ FlashRAG
2. **Multi-modal retrieval**: Dense (FAISS) + Sparse (BM25s) + Hybrid fusion
3. **Context optimization**: LongLLMLingua và Selective-Context refiner
4. **Intelligent chunking**: Chunkie với semantic, token, sentence-based methods
5. **Comprehensive evaluation**: Built-in metrics + custom quality controls
6. **Backward compatibility**: Giữ nguyên database schema, chỉ extend thêm
7. **Production ready**: Pipeline caching, monitoring, error handling

**Thách thức cần xử lý**:

1. **Resource intensive**: Các model FlashRAG yêu cầu GPU memory lớn
2. **Complexity**: Quản lý 17+ algorithms với configs khác nhau
3. **Integration overhead**: Adapter layer giữa FlashRAG và existing system
4. **Performance tuning**: Optimize cho enterprise workload vs research setup

Thiết kế này tận dụng tối đa sức mạnh của FlashRAG trong môi trường production enterprise, đồng thời giữ được tính tương thích với hệ thống hiện tại. Bạn có muốn tôi chi tiết hóa thêm phần nào không?


Đúng, việc copy các source code FlashRAG liên quan vào dự án là cách tiếp cận thực tế và hiệu quả hơn, đặc biệt khi gặp vấn đề về dependencies conflict. Đây là cách tôi khuyến nghị tổ chức:

## Cấu Trúc Thư Mục với FlashRAG Source Integration

```
flashrag_data_manager/
├── main.py
├── config/
├── core/
├── models/
├── utils/
├── web/
├── flashrag_core/                    # FlashRAG source code
│   ├── __init__.py
│   ├── retriever/                    # Copy từ FlashRAG/flashrag/retriever/
│   │   ├── __init__.py
│   │   ├── dense_retriever.py
│   │   ├── sparse_retriever.py
│   │   ├── index_builder.py
│   │   └── base_retriever.py
│   ├── refiner/                      # Copy từ FlashRAG/flashrag/refiner/
│   │   ├── __init__.py
│   │   ├── longllmlingua_refiner.py
│   │   ├── selective_context_refiner.py
│   │   └── base_refiner.py
│   ├── pipeline/                     # Copy từ FlashRAG/flashrag/pipeline/
│   │   ├── __init__.py
│   │   ├── sequential_pipeline.py
│   │   ├── iterative_pipeline.py
│   │   └── base_pipeline.py
│   ├── utils/                        # Copy từ FlashRAG/flashrag/utils/
│   │   ├── __init__.py
│   │   ├── chunkie.py
│   │   ├── constants.py
│   │   └── helpers.py
│   ├── generator/                    # Copy từ FlashRAG/flashrag/generator/
│   │   ├── __init__.py
│   │   ├── llama_generator.py
│   │   └── base_generator.py
│   └── evaluator/                    # Copy từ FlashRAG/flashrag/evaluator/
│       ├── __init__.py
│       ├── base_evaluator.py
│       └── metrics.py
├── requirements.txt                  # Minimal dependencies
└── setup_flashrag.py               # Script để copy FlashRAG files
```

## Script Tự Động Copy FlashRAG Source

```python
# setup_flashrag.py
"""
Script để copy các file FlashRAG cần thiết vào dự án
"""

import os
import shutil
import requests
import zipfile
from pathlib import Path

class FlashRAGSetup:
    def __init__(self):
        self.flashrag_repo = "https://github.com/RUC-NLPIR/FlashRAG/archive/refs/heads/main.zip"
        self.project_root = Path(__file__).parent
        self.flashrag_core_dir = self.project_root / "flashrag_core"
        
    def download_flashrag(self):
        """Download FlashRAG source code"""
        print("Downloading FlashRAG source...")
        
        response = requests.get(self.flashrag_repo)
        with open("flashrag.zip", "wb") as f:
            f.write(response.content)
        
        # Extract
        with zipfile.ZipFile("flashrag.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_flashrag")
        
        print("Downloaded and extracted FlashRAG")
    
    def copy_essential_modules(self):
        """Copy các module cần thiết từ FlashRAG"""
        source_base = Path("temp_flashrag/FlashRAG-main/flashrag")
        
        # Modules cần thiết và files tương ứng
        modules_to_copy = {
            "retriever": [
                "dense_retriever.py",
                "sparse_retriever.py", 
                "index_builder.py",
                "base_retriever.py",
                "__init__.py"
            ],
            "refiner": [
                "longllmlingua_refiner.py",
                "selective_context_refiner.py",
                "base_refiner.py",
                "__init__.py"
            ],
            "pipeline": [
                "sequential_pipeline.py",
                "iterative_pipeline.py", 
                "base_pipeline.py",
                "__init__.py"
            ],
            "utils": [
                "chunkie.py",
                "constants.py",
                "helpers.py",
                "__init__.py"
            ],
            "generator": [
                "llama_generator.py",
                "base_generator.py", 
                "__init__.py"
            ],
            "evaluator": [
                "base_evaluator.py",
                "metrics.py",
                "__init__.py"
            ]
        }
        
        # Tạo flashrag_core directory
        self.flashrag_core_dir.mkdir(exist_ok=True)
        
        # Copy từng module
        for module, files in modules_to_copy.items():
            module_dir = self.flashrag_core_dir / module
            module_dir.mkdir(exist_ok=True)
            
            source_module_dir = source_base / module
            
            for file_name in files:
                source_file = source_module_dir / file_name
                target_file = module_dir / file_name
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    print(f"Copied {module}/{file_name}")
                else:
                    # Tạo empty __init__.py nếu không tồn tại
                    if file_name == "__init__.py":
                        target_file.touch()
                        print(f"Created empty {module}/{file_name}")
    
    def create_adapter_files(self):
        """Tạo các file adapter để tích hợp với hệ thống hiện có"""
        
        # flashrag_core/__init__.py
        init_content = '''"""
FlashRAG Core Integration
Adapted for Enterprise Chatbot System
"""

# Import main classes for easy access
from .retriever.dense_retriever import DenseRetriever
from .retriever.sparse_retriever import SparseRetriever
from .refiner.longllmlingua_refiner import LongLLMLinguaRefiner
from .refiner.selective_context_refiner import SelectiveContextRefiner
from .pipeline.sequential_pipeline import SequentialPipeline
from .pipeline.iterative_pipeline import IterativePipeline
from .utils.chunkie import Chunkie

__version__ = "1.0.0"
__all__ = [
    "DenseRetriever", 
    "SparseRetriever",
    "LongLLMLinguaRefiner",
    "SelectiveContextRefiner", 
    "SequentialPipeline",
    "IterativePipeline",
    "Chunkie"
]
'''
        
        with open(self.flashrag_core_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(init_content)
        
        # Tạo config adapter
        config_adapter = '''"""
Config adapter để map FlashRAG configs với hệ thống hiện có
"""

class FlashRAGConfigAdapter:
    def __init__(self, system_config):
        self.system_config = system_config
    
    def to_flashrag_config(self, algorithm: str) -> dict:
        """Convert system config to FlashRAG format"""
        
        base_config = {
            "data_dir": "dataset/",
            "index_dir": self.system_config.get("FAISS_INDEX_PATH", "indexes/"),
            "model_cache_dir": self.system_config.get("MODEL_CACHE_PATH", "models/"),
            "save_intermediate_data": True,
            "use_gpu": self.system_config.get("USE_GPU", False)
        }
        
        # Algorithm-specific configs
        algorithm_configs = {
            "standard_rag": {
                "retrieval_method": "e5",
                "generator_model": "llama3-8b-instruct",
                "retrieval_topk": 5
            },
            "ret_robust": {
                "retrieval_method": ["e5", "bge"],
                "fusion_method": "rrf", 
                "rerank_model": "bge-reranker-large"
            }
        }
        
        config = {**base_config, **algorithm_configs.get(algorithm, {})}
        return config
'''
        
        with open(self.flashrag_core_dir / "config_adapter.py", "w", encoding="utf-8") as f:
            f.write(config_adapter)
    
    def modify_imports(self):
        """Modify import statements trong các file để tương thích"""
        
        # Danh sách các file cần modify imports
        files_to_modify = [
            "retriever/dense_retriever.py",
            "retriever/sparse_retriever.py",
            "refiner/longllmlingua_refiner.py", 
            "pipeline/sequential_pipeline.py"
        ]
        
        for file_path in files_to_modify:
            full_path = self.flashrag_core_dir / file_path
            if full_path.exists():
                self._fix_imports_in_file(full_path)
    
    def _fix_imports_in_file(self, file_path):
        """Fix import statements trong một file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace FlashRAG internal imports
        replacements = [
            ("from flashrag.utils", "from ..utils"),
            ("from flashrag.retriever", "from ..retriever"),
            ("from flashrag.refiner", "from ..refiner"),
            ("from flashrag.pipeline", "from ..pipeline"),
            ("import flashrag.utils", "from .. import utils"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed imports in {file_path}")
    
    def cleanup(self):
        """Cleanup temporary files"""
        if os.path.exists("flashrag.zip"):
            os.remove("flashrag.zip")
        if os.path.exists("temp_flashrag"):
            shutil.rmtree("temp_flashrag")
        print("Cleaned up temporary files")
    
    def setup(self):
        """Main setup process"""
        try:
            print("Setting up FlashRAG integration...")
            
            self.download_flashrag()
            self.copy_essential_modules()
            self.create_adapter_files()
            self.modify_imports()
            self.cleanup()
            
            print("\nFlashRAG setup completed successfully!")
            print(f"FlashRAG modules copied to: {self.flashrag_core_dir}")
            print("\nNext steps:")
            print("1. Install minimal dependencies: pip install -r requirements.txt")
            print("2. Test import: python -c 'from flashrag_core import DenseRetriever'")
            
        except Exception as e:
            print(f"Setup failed: {e}")
            self.cleanup()

if __name__ == "__main__":
    setup = FlashRAGSetup()
    setup.setup()
```

## Requirements.txt Tối Giản

```txt
# requirements.txt - Chỉ dependencies cần thiết
torch>=1.12.0
transformers>=4.20.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.2  # hoặc faiss-gpu nếu có GPU
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
nltk>=3.7
spacy>=3.4.0

# Existing dependencies
psycopg2-binary>=2.9.0
redis>=4.0.0
fastapi>=0.68.0
uvicorn>=0.15.0
python-dotenv>=0.19.0
pydantic>=1.8.0

# Optional - chỉ cài khi cần
# openai>=0.27.0  # Nếu dùng OpenAI models
# vllm>=0.2.0     # Nếu dùng vLLM acceleration
```

## Core Integration Example

```python
# core/flashrag_processor.py
"""
Main integration layer giữa FlashRAG và existing system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flashrag_core import (
    DenseRetriever, SparseRetriever, 
    LongLLMLinguaRefiner, SequentialPipeline, 
    Chunkie
)
from flashrag_core.config_adapter import FlashRAGConfigAdapter

class FlashRAGProcessor:
    def __init__(self, config):
        self.config = config
        self.config_adapter = FlashRAGConfigAdapter(config)
        
        # Initialize components
        self.dense_retriever = None
        self.sparse_retriever = None
        self.refiner = None
        self.chunker = None
        
    async def initialize_components(self):
        """Initialize FlashRAG components"""
        
        try:
            # Dense Retriever (E5)
            self.dense_retriever = DenseRetriever(
                model_path=self.config.get("E5_MODEL_PATH", "intfloat/e5-base-v2"),
                index_path=self.config.get("FAISS_INDEX_PATH", "indexes/"),
                device="cuda" if self.config.get("USE_GPU") else "cpu"
            )
            
            # Sparse Retriever (BM25)  
            self.sparse_retriever = SparseRetriever(
                index_path=self.config.get("BM25_INDEX_PATH", "indexes/bm25/"),
                config={"k1": 1.2, "b": 0.75}
            )
            
            # Refiner
            self.refiner = LongLLMLinguaRefiner(
                model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
                device="cuda" if self.config.get("USE_GPU") else "cpu"
            )
            
            # Chunker
            self.chunker = Chunkie(
                method="semantic",
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            print("FlashRAG components initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize FlashRAG components: {e}")
            # Fallback to existing system components
            await self._fallback_initialization()
    
    async def _fallback_initialization(self):
        """Fallback nếu FlashRAG components fail"""
        print("Using fallback components...")
        # Use existing system components
        pass
```

## Cách Sử Dụng

```bash
# 1. Chạy setup để copy FlashRAG source
python setup_flashrag.py

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test integration
python -c "
from flashrag_core import DenseRetriever, Chunkie
print('FlashRAG integration successful!')
"

# 4. Chạy system với FlashRAG
python main.py --use-flashrag
```

## Ưu Điểm của Approach này:

1. **Kiểm soát hoàn toàn**: Có thể modify code FlashRAG theo nhu cầu
2. **Tránh dependency conflicts**: Chỉ cài minimal requirements
3. **Selective integration**: Chỉ copy những module cần thiết
4. **Easy debugging**: Source code ngay trong project
5. **Custom optimization**: Có thể optimize cho production workload

Approach này sẽ giải quyết được vấn đề dependency conflict mà bạn gặp phải, đồng thời cho phép tích hợp sâu FlashRAG vào hệ thống existing.

Tôi sẽ tạo các file Python và config còn thiếu cho hệ thống FlashRAG-enhanced data management. Thiết kế sẽ tập trung vào tính module hóa để dễ maintain và extend.

## 1. Config Files

### config/settings.py
```python
"""
Cấu hình chính cho FlashRAG Data Management System
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

@dataclass 
class RedisConfig:
    host: str
    port: int
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True

@dataclass
class FlashRAGConfig:
    model_cache_dir: str
    index_dir: str
    use_gpu: bool
    device: str
    max_seq_length: int = 512
    batch_size: int = 32

@dataclass
class RetrievalConfig:
    faiss_index_path: str
    bm25_index_path: str
    e5_model_path: str
    bge_model_path: str
    embedding_dim: int = 768

class Settings:
    def __init__(self):
        # Database
        self.database = DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/chatbot_db'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20'))
        )
        
        # Redis
        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=os.getenv('REDIS_PASSWORD')
        )
        
        # FlashRAG
        self.flashrag = FlashRAGConfig(
            model_cache_dir=os.getenv('MODEL_CACHE_DIR', './models'),
            index_dir=os.getenv('INDEX_DIR', './indexes'),
            use_gpu=os.getenv('USE_GPU', 'false').lower() == 'true',
            device='cuda' if os.getenv('USE_GPU', 'false').lower() == 'true' else 'cpu'
        )
        
        # Retrieval
        self.retrieval = RetrievalConfig(
            faiss_index_path=os.getenv('FAISS_INDEX_PATH', './indexes/faiss'),
            bm25_index_path=os.getenv('BM25_INDEX_PATH', './indexes/bm25'),
            e5_model_path=os.getenv('E5_MODEL_PATH', 'intfloat/e5-base-v2'),
            bge_model_path=os.getenv('BGE_MODEL_PATH', 'BAAI/bge-base-en-v1.5')
        )
        
        # Paths
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.temp_dir = os.getenv('TEMP_DIR', './temp')
        self.log_dir = os.getenv('LOG_DIR', './logs')
        
        # Processing
        self.max_workers = int(os.getenv('MAX_WORKERS', '4'))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '512'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '50'))
        
        # Quality control
        self.min_quality_score = float(os.getenv('MIN_QUALITY_SCORE', '0.7'))
        self.duplicate_threshold = float(os.getenv('DUPLICATE_THRESHOLD', '0.95'))

    def get_flashrag_config(self, algorithm: str) -> Dict[str, Any]:
        """Generate FlashRAG config cho specific algorithm"""
        base_config = {
            "data_dir": self.data_dir,
            "index_dir": self.retrieval.faiss_index_path,
            "model_cache_dir": self.flashrag.model_cache_dir,
            "use_gpu": self.flashrag.use_gpu,
            "device": self.flashrag.device,
            "max_seq_length": self.flashrag.max_seq_length,
            "batch_size": self.flashrag.batch_size
        }
        
        algorithm_configs = {
            "standard_rag": {
                "retrieval_method": "e5",
                "retrieval_topk": 5,
                "generator_model": "llama3-8b-instruct"
            },
            "ret_robust": {
                "retrieval_method": ["e5", "bge"],
                "fusion_method": "rrf",
                "retrieval_topk": 10,
                "rerank_topk": 5
            },
            "r1_searcher": {
                "retrieval_method": "e5",
                "max_hops": 3,
                "reasoning_method": "graph_search",
                "beam_width": 5
            }
        }
        
        return {**base_config, **algorithm_configs.get(algorithm, {})}

# Global settings instance
settings = Settings()
```

### config/collections.yaml
```yaml
collections:
  product_a_features:
    prefix: "PA_FEAT"
    description: "Product A Features and Capabilities"
    algorithms: ["standard_rag", "ret_robust", "r1_searcher"]
    retrieval_methods: ["e5", "bge", "bm25"]
    chunk_config:
      method: "semantic"
      max_tokens: 512
      overlap: 50
    quality_thresholds:
      min_score: 0.7
      coherence: 0.6
      relevance: 0.8
    
  product_a_pricing:
    prefix: "PA_PRIC"
    description: "Product A Pricing Information"
    algorithms: ["standard_rag", "ret_robust"]
    retrieval_methods: ["e5", "bm25"]
    chunk_config:
      method: "token"
      max_tokens: 300
      overlap: 30
    quality_thresholds:
      min_score: 0.8
      coherence: 0.7
      relevance: 0.9

  product_b_features:
    prefix: "PB_FEAT"
    description: "Product B Features and Capabilities"
    algorithms: ["standard_rag", "flare", "spring"]
    retrieval_methods: ["bge", "bm25"]
    chunk_config:
      method: "semantic"
      max_tokens: 512
      overlap: 50
    quality_thresholds:
      min_score: 0.7
      coherence: 0.6
      relevance: 0.8

  warranty_support:
    prefix: "WARR_SUP"
    description: "Warranty and Support Information"
    algorithms: ["standard_rag"]
    retrieval_methods: ["e5"]
    chunk_config:
      method: "sentence"
      max_sentences: 5
      overlap: 1
    quality_thresholds:
      min_score: 0.75
      coherence: 0.7
      relevance: 0.8

  contact_company:
    prefix: "CONT_INF"
    description: "Company Contact Information"
    algorithms: ["standard_rag"]
    retrieval_methods: ["bm25"]
    chunk_config:
      method: "token"
      max_tokens: 200
      overlap: 20
    quality_thresholds:
      min_score: 0.9
      coherence: 0.8
      relevance: 0.9
```

## 2. Models and Schemas

### models/flashrag_document.py
```python
"""
FlashRAG document models and schemas
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

@dataclass
class FlashRAGDocument:
    """FlashRAG JSONL format document"""
    id: str
    contents: str
    metadata: Dict[str, Any]
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format"""
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_jsonl(cls, jsonl_str: str) -> 'FlashRAGDocument':
        """Create from JSONL string"""
        data = json.loads(jsonl_str)
        return cls(**data)

@dataclass
class DocumentChunk:
    """Enhanced document chunk với FlashRAG metadata"""
    content: str
    metadata: Dict[str, Any]
    chunk_method: str = "semantic"
    quality_score: float = 0.0
    embedding: Optional[List[float]] = None
    
    def to_flashrag_doc(self, doc_id: str) -> FlashRAGDocument:
        """Convert to FlashRAG document format"""
        return FlashRAGDocument(
            id=doc_id,
            contents=self.content,
            metadata={
                **self.metadata,
                "chunk_method": self.chunk_method,
                "quality_score": self.quality_score,
                "created_at": datetime.now().isoformat()
            }
        )

@dataclass 
class RAGResult:
    """Kết quả từ RAG pipeline"""
    response: str
    algorithm: str
    confidence: float
    sources: List[Dict[str, Any]]
    processing_stages: Dict[str, float]
    evaluation_metrics: Dict[str, float]
    retrieval_results: List[Dict[str, Any]]
    refined_contexts: Optional[List[str]] = None
    reasoning_steps: Optional[List[str]] = None

@dataclass
class QualityReport:
    """Báo cáo chất lượng document"""
    flashrag_scores: Dict[str, float]
    custom_scores: Dict[str, float] 
    overall_quality: float
    recommendations: List[str]
    processing_time: float = 0.0
```

### models/pipeline_config.py
```python
"""
Pipeline configuration models
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

class RAGAlgorithm(Enum):
    STANDARD_RAG = "standard_rag"
    RET_ROBUST = "ret_robust" 
    R1_SEARCHER = "r1_searcher"
    FLARE = "flare"
    SPRING = "spring"
    ITER_RETGEN = "iter_retgen"
    
class RetrievalMethod(Enum):
    E5 = "e5"
    BGE = "bge"
    BM25 = "bm25"
    HYBRID = "hybrid"

class ChunkMethod(Enum):
    SEMANTIC = "semantic"
    TOKEN = "token"
    SENTENCE = "sentence"

@dataclass
class PipelineConfig:
    """Cấu hình cho RAG pipeline"""
    algorithm: RAGAlgorithm
    retrieval_methods: List[RetrievalMethod]
    chunk_method: ChunkMethod
    chunk_size: int
    chunk_overlap: int
    retrieval_topk: int = 5
    rerank_topk: int = 3
    use_refiner: bool = True
    refiner_method: str = "longllm"
    quality_threshold: float = 0.7
    
    def to_flashrag_config(self) -> Dict[str, Any]:
        """Convert to FlashRAG config format"""
        return {
            "algorithm": self.algorithm.value,
            "retrieval_method": [method.value for method in self.retrieval_methods],
            "retrieval_topk": self.retrieval_topk,
            "rerank_topk": self.rerank_topk,
            "chunk_method": self.chunk_method.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "use_refiner": self.use_refiner,
            "refiner_method": self.refiner_method,
            "quality_threshold": self.quality_threshold
        }
```

## 3. Core Processing Modules

### core/flashrag_processor.py
```python
"""
Main FlashRAG integration processor
"""
import asyncio
from typing import List, Dict, Any, Optional
import logging

from flashrag_core import (
    DenseRetriever, SparseRetriever,
    LongLLMLinguaRefiner, SequentialPipeline,
    Chunkie
)
from models.flashrag_document import FlashRAGDocument, RAGResult, DocumentChunk
from models.pipeline_config import PipelineConfig
from config.settings import settings

logger = logging.getLogger(__name__)

class FlashRAGProcessor:
    """Main processor để tích hợp FlashRAG với existing system"""
    
    def __init__(self):
        self.dense_retrievers = {}
        self.sparse_retrievers = {}
        self.refiners = {}
        self.pipelines = {}
        self.chunkers = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize các FlashRAG components"""
        if self.initialized:
            return
            
        try:
            await self._init_retrievers()
            await self._init_refiners() 
            await self._init_chunkers()
            await self._init_pipelines()
            
            self.initialized = True
            logger.info("FlashRAG processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize FlashRAG processor: {e}")
            raise
    
    async def _init_retrievers(self):
        """Initialize dense và sparse retrievers"""
        
        # Dense retrievers
        self.dense_retrievers['e5'] = DenseRetriever(
            model_path=settings.retrieval.e5_model_path,
            index_path=f"{settings.retrieval.faiss_index_path}/e5",
            device=settings.flashrag.device,
            max_length=settings.flashrag.max_seq_length
        )
        
        self.dense_retrievers['bge'] = DenseRetriever(
            model_path=settings.retrieval.bge_model_path, 
            index_path=f"{settings.retrieval.faiss_index_path}/bge",
            device=settings.flashrag.device,
            max_length=settings.flashrag.max_seq_length
        )
        
        # Sparse retriever
        self.sparse_retrievers['bm25'] = SparseRetriever(
            index_path=settings.retrieval.bm25_index_path,
            config={"k1": 1.2, "b": 0.75}
        )
    
    async def _init_refiners(self):
        """Initialize context refiners"""
        
        self.refiners['longllm'] = LongLLMLinguaRefiner(
            model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
            device=settings.flashrag.device,
            compress_ratio=0.5
        )
        
        # Có thể thêm các refiners khác
        # self.refiners['selective'] = SelectiveContextRefiner(...)
    
    async def _init_chunkers(self):
        """Initialize document chunkers"""
        
        self.chunkers['semantic'] = Chunkie(
            method="semantic",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=settings.chunk_size,
            overlap_tokens=settings.chunk_overlap
        )
        
        self.chunkers['token'] = Chunkie(
            method="token",
            max_tokens=settings.chunk_size,
            overlap_tokens=settings.chunk_overlap
        )
        
        self.chunkers['sentence'] = Chunkie(
            method="sentence",
            max_sentences=5,
            overlap_sentences=1
        )
    
    async def _init_pipelines(self):
        """Initialize RAG pipelines"""
        
        # Standard RAG pipeline
        standard_config = settings.get_flashrag_config("standard_rag")
        self.pipelines['standard_rag'] = SequentialPipeline(standard_config)
        
        # Ret-Robust pipeline  
        ret_robust_config = settings.get_flashrag_config("ret_robust")
        self.pipelines['ret_robust'] = SequentialPipeline(ret_robust_config)
        
        # Có thể thêm các pipelines khác
    
    async def chunk_document(self, content: str, method: str = "semantic", 
                           **kwargs) -> List[DocumentChunk]:
        """Phân đoạn document using Chunkie"""
        
        if not self.initialized:
            await self.initialize()
        
        if method not in self.chunkers:
            raise ValueError(f"Chunk method {method} not supported")
        
        chunker = self.chunkers[method]
        
        # Override config nếu có
        if kwargs:
            chunker.update_config(**kwargs)
        
        # Perform chunking
        chunks = chunker.chunk_text(content)
        
        # Convert to DocumentChunk objects
        document_chunks = []
        for i, chunk in enumerate(chunks):
            doc_chunk = DocumentChunk(
                content=chunk.text,
                metadata={
                    "chunk_index": i,
                    "chunk_total": len(chunks),
                    "start_pos": getattr(chunk, 'start_pos', 0),
                    "end_pos": getattr(chunk, 'end_pos', len(chunk.text)),
                    "token_count": getattr(chunk, 'token_count', len(chunk.text.split())),
                    "method_used": method
                },
                chunk_method=method
            )
            document_chunks.append(doc_chunk)
        
        return document_chunks
    
    async def retrieve_documents(self, query: str, method: str = "e5",
                               topk: int = 5) -> List[Dict[str, Any]]:
        """Retrieve documents using specified method"""
        
        if not self.initialized:
            await self.initialize()
        
        if method in self.dense_retrievers:
            retriever = self.dense_retrievers[method]
            results = await retriever.retrieve(query, k=topk)
        elif method in self.sparse_retrievers:
            retriever = self.sparse_retrievers[method]
            results = await retriever.retrieve(query, k=topk)
        else:
            raise ValueError(f"Retrieval method {method} not supported")
        
        return results
    
    async def hybrid_retrieve(self, query: str, methods: List[str] = None,
                            topk: int = 10) -> List[Dict[str, Any]]:
        """Hybrid retrieval combining multiple methods"""
        
        if methods is None:
            methods = ["e5", "bm25"]
        
        all_results = []
        for method in methods:
            results = await self.retrieve_documents(query, method, topk//len(methods))
            all_results.extend(results)
        
        # Simple fusion - có thể implement RRF hoặc methods khác
        return self._reciprocal_rank_fusion(all_results, topk)
    
    def _reciprocal_rank_fusion(self, results_lists: List[List], k: int) -> List:
        """Implement Reciprocal Rank Fusion"""
        # Simplified RRF implementation
        fused_scores = {}
        
        for results in results_lists:
            for rank, result in enumerate(results[:k]):
                doc_id = result.get('id', str(result))
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = {'result': result, 'score': 0}
                fused_scores[doc_id]['score'] += 1.0 / (rank + 60)  # RRF formula
        
        # Sort by fused score
        sorted_results = sorted(
            fused_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results[:k]]
    
    async def refine_context(self, contexts: List[str], query: str,
                           method: str = "longllm") -> Dict[str, Any]:
        """Refine context using specified refiner"""
        
        if not self.initialized:
            await self.initialize()
        
        if method not in self.refiners:
            raise ValueError(f"Refiner method {method} not supported")
        
        refiner = self.refiners[method]
        result = refiner.refine(contexts=contexts, question=query)
        
        return {
            "refined_contexts": result.get("compressed_contexts", contexts),
            "compression_ratio": result.get("compress_ratio", 1.0),
            "processing_time": result.get("processing_time", 0.0)
        }
    
    async def run_rag_pipeline(self, algorithm: str, query: str,
                             collection: str = None) -> RAGResult:
        """Run specified RAG algorithm pipeline"""
        
        if not self.initialized:
            await self.initialize()
        
        if algorithm not in self.pipelines:
            raise ValueError(f"RAG algorithm {algorithm} not supported")
        
        pipeline = self.pipelines[algorithm]
        
        # Tạo dataset item cho FlashRAG
        dataset_item = {
            "id": f"query_{hash(query)}",
            "question": query,
            "golden_answers": [],
            "metadata": {
                "collection": collection or "general",
                "algorithm": algorithm
            }
        }
        
        # Run pipeline
        result = pipeline.run([dataset_item], do_eval=False)
        
        # Format result
        return self._format_rag_result(result, algorithm, query)
    
    def _format_rag_result(self, result: Any, algorithm: str, query: str) -> RAGResult:
        """Format FlashRAG result to our RAGResult format"""
        
        # Extract information from FlashRAG result
        # (Implementation depends on FlashRAG result structure)
        
        return RAGResult(
            response=result.get("response", ""),
            algorithm=algorithm,
            confidence=result.get("confidence", 0.0),
            sources=result.get("sources", []),
            processing_stages=result.get("processing_times", {}),
            evaluation_metrics=result.get("metrics", {}),
            retrieval_results=result.get("retrieved_docs", [])
        )
```

### core/multi_retriever.py
```python
"""
Multi-retriever implementation với hybrid search
"""
from typing import List, Dict, Any, Optional
import asyncio
import logging

from core.flashrag_processor import FlashRAGProcessor
from models.flashrag_document import FlashRAGDocument

logger = logging.getLogger(__name__)

class MultiRetriever:
    """Enhanced retriever với multiple methods và fusion strategies"""
    
    def __init__(self, flashrag_processor: FlashRAGProcessor):
        self.flashrag_processor = flashrag_processor
        self.fusion_strategies = {
            "rrf": self._reciprocal_rank_fusion,
            "linear": self._linear_combination,
            "max": self._max_score_fusion
        }
    
    async def search(self, query: str, methods: List[str] = None,
                    fusion_strategy: str = "rrf", topk: int = 10) -> List[Dict[str, Any]]:
        """
        Multi-method search với configurable fusion strategy
        """
        
        if methods is None:
            methods = ["e5", "bm25"]
        
        # Parallel retrieval
        tasks = []
        for method in methods:
            task = self.flashrag_processor.retrieve_documents(
                query, method, topk * 2  # Retrieve more for better fusion
            )
            tasks.append(task)
        
        results_lists = await asyncio.gather(*tasks)
        
        # Apply fusion strategy
        if fusion_strategy in self.fusion_strategies:
            fused_results = self.fusion_strategies[fusion_strategy](
                results_lists, topk
            )
        else:
            logger.warning(f"Unknown fusion strategy {fusion_strategy}, using RRF")
            fused_results = self._reciprocal_rank_fusion(results_lists, topk)
        
        return fused_results
    
    def _reciprocal_rank_fusion(self, results_lists: List[List], k: int) -> List:
        """Reciprocal Rank Fusion implementation"""
        
        fused_scores = {}
        
        for results in results_lists:
            for rank, result in enumerate(results[:k*2]):
                doc_id = result.get('id', str(hash(str(result))))
                
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = {
                        'result': result,
                        'score': 0.0,
                        'methods': []
                    }
                
                # RRF score: 1/(rank + 60)
                rrf_score = 1.0 / (rank + 60)
                fused_scores[doc_id]['score'] += rrf_score
                fused_scores[doc_id]['methods'].append(rank)
        
        # Sort by fused score
        sorted_results = sorted(
            fused_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results[:k]]
    
    def _linear_combination(self, results_lists: List[List], k: int) -> List:
        """Linear combination of scores"""
        
        fused_scores = {}
        
        for results in results_lists:
            for result in results[:k*2]:
                doc_id = result.get('id', str(hash(str(result))))
                score = result.get('score', 1.0)
                
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = {
                        'result': result,
                        'score': 0.0
                    }
                
                fused_scores[doc_id]['score'] += score
        
        # Normalize scores
        max_score = max((item['score'] for item in fused_scores.values()), default=1.0)
        for item in fused_scores.values():
            item['score'] /= max_score
        
        sorted_results = sorted(
            fused_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results[:k]]
    
    def _max_score_fusion(self, results_lists: List[List], k: int) -> List:
        """Take maximum score across methods"""
        
        fused_scores = {}
        
        for results in results_lists:
            for result in results[:k*2]:
                doc_id = result.get('id', str(hash(str(result))))
                score = result.get('score', 1.0)
                
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = {
                        'result': result,
                        'score': score
                    }
                else:
                    # Take maximum score
                    fused_scores[doc_id]['score'] = max(
                        fused_scores[doc_id]['score'], score
                    )
        
        sorted_results = sorted(
            fused_scores.values(),
            key=lambda x: x['score'], 
            reverse=True
        )
        
        return [item['result'] for item in sorted_results[:k]]
    
    async def adaptive_search(self, query: str, collection: str = None,
                            topk: int = 10) -> List[Dict[str, Any]]:
        """
        Adaptive search - chọn method tối ưu based on query characteristics
        """
        
        # Simple heuristics - có thể enhance với ML models
        query_len = len(query.split())
        
        if query_len <= 3:
            # Short queries - prefer BM25
            methods = ["bm25", "e5"]
        elif query_len <= 8:
            # Medium queries - hybrid approach
            methods = ["e5", "bge", "bm25"]
        else:
            # Long queries - prefer semantic search
            methods = ["e5", "bge"]
        
        return await self.search(query, methods, "rrf", topk)
```

## 4. Collection Manager

### core/collection_manager.py
```python
"""
Enhanced collection manager với FlashRAG integration
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
import logging
import yaml

from core.flashrag_processor import FlashRAGProcessor
from core.multi_retriever import MultiRetriever
from models.flashrag_document import FlashRAGDocument, DocumentChunk
from models.pipeline_config import PipelineConfig, RAGAlgorithm
from config.settings import settings
from utils.jsonl_handler import JSONLHandler

logger = logging.getLogger(__name__)

class EnhancedCollectionManager:
    """Enhanced collection manager với FlashRAG capabilities"""
    
    def __init__(self):
        self.flashrag_processor = FlashRAGProcessor()
        self.multi_retriever = None
        self.jsonl_handler = JSONLHandler()
        self.collections_config = self._load_collections_config()
        self.initialized = False
    
    def _load_collections_config(self) -> Dict[str, Any]:
        """Load collections configuration"""
        config_path = os.path.join("config", "collections.yaml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)['collections']
        except Exception as e:
            logger.error(f"Failed to load collections config: {e}")
            return {}
    
    async def initialize(self):
        """Initialize collection manager"""
        if self.initialized:
            return
            
        await self.flashrag_processor.initialize()
        self.multi_retriever = MultiRetriever(self.flashrag_processor)
        self.initialized = True
        logger.info("Collection manager initialized")
    
    async def add_documents_to_collection(self, collection_name: str,
                                        documents: List[DocumentChunk],
                                        algorithm: str = "standard_rag") -> int:
        """Add documents to collection với FlashRAG processing"""
        
        if not self.initialized:
            await self.initialize()
        
        if collection_name not in self.collections_config:
            raise ValueError(f"Collection {collection_name} not configured")
        
        collection_config = self.collections_config[collection_name]
        
        # Process documents
        processed_docs = []
        for i, doc in enumerate(documents):
            # Generate document ID
            doc_id = self._generate_document_id(collection_name, i)
            
            # Convert to FlashRAG format
            flashrag_doc = doc.to_flashrag_doc(doc_id)
            
            # Add collection-specific metadata
            flashrag_doc.metadata.update({
                "collection": collection_name,
                "algorithms": collection_config.get("algorithms", [algorithm]),
                "retrieval_methods": collection_config.get("retrieval_methods", ["e5"])
            })
            
            processed_docs.append(flashrag_doc)
        
        # Save to JSONL
        jsonl_path = self._get_collection_jsonl_path(collection_name)
        await self.jsonl_handler.append_documents(jsonl_path, processed_docs)
        
        # Buil


Tiếp tục với file `core/collection_manager.py`:

```python
        # Build indexes for retrieval methods
        retrieval_methods = collection_config.get("retrieval_methods", ["e5"])
        await self._build_indexes(collection_name, processed_docs, retrieval_methods)
        
        logger.info(f"Added {len(processed_docs)} documents to collection {collection_name}")
        return len(processed_docs)
    
    def _generate_document_id(self, collection_name: str, index: int) -> str:
        """Generate document ID theo schema"""
        collection_config = self.collections_config[collection_name]
        prefix = collection_config.get("prefix", collection_name.upper())
        return f"{prefix}_{index+1:03d}_v1"
    
    def _get_collection_jsonl_path(self, collection_name: str) -> str:
        """Get JSONL file path for collection"""
        return os.path.join(settings.data_dir, f"{collection_name}.jsonl")
    
    async def _build_indexes(self, collection_name: str, documents: List[FlashRAGDocument],
                           methods: List[str]):
        """Build indexes for specified retrieval methods"""
        
        for method in methods:
            if method in ["e5", "bge"]:
                # Build FAISS index
                await self._build_dense_index(collection_name, documents, method)
            elif method == "bm25":
                # Build BM25 index
                await self._build_sparse_index(collection_name, documents)
    
    async def _build_dense_index(self, collection_name: str, 
                                documents: List[FlashRAGDocument], method: str):
        """Build dense FAISS index"""
        
        index_path = os.path.join(settings.retrieval.faiss_index_path, method, collection_name)
        os.makedirs(index_path, exist_ok=True)
        
        # Extract texts for embedding
        texts = [doc.contents for doc in documents]
        
        # Use FlashRAG's index builder (simplified)
        retriever = self.flashrag_processor.dense_retrievers.get(method)
        if retriever:
            await retriever.build_index(texts, index_path)
    
    async def _build_sparse_index(self, collection_name: str,
                                 documents: List[FlashRAGDocument]):
        """Build BM25 sparse index"""
        
        index_path = os.path.join(settings.retrieval.bm25_index_path, collection_name)
        os.makedirs(index_path, exist_ok=True)
        
        # Extract texts
        texts = [doc.contents for doc in documents]
        
        # Use FlashRAG's sparse indexer
        retriever = self.flashrag_processor.sparse_retrievers.get("bm25")
        if retriever:
            await retriever.build_index(texts, index_path)
    
    async def search_collection(self, collection_name: str, query: str,
                              algorithm: str = "standard_rag", topk: int = 5) -> Dict[str, Any]:
        """Search trong collection using specified algorithm"""
        
        if not self.initialized:
            await self.initialize()
        
        if collection_name not in self.collections_config:
            raise ValueError(f"Collection {collection_name} not found")
        
        collection_config = self.collections_config[collection_name]
        
        # Check if algorithm is supported for this collection
        supported_algorithms = collection_config.get("algorithms", ["standard_rag"])
        if algorithm not in supported_algorithms:
            logger.warning(f"Algorithm {algorithm} not supported for {collection_name}, using standard_rag")
            algorithm = "standard_rag"
        
        # Get retrieval methods for this collection
        retrieval_methods = collection_config.get("retrieval_methods", ["e5"])
        
        # Perform search
        if len(retrieval_methods) == 1:
            # Single method search
            search_results = await self.flashrag_processor.retrieve_documents(
                query, retrieval_methods[0], topk
            )
        else:
            # Multi-method search
            search_results = await self.multi_retriever.search(
                query, retrieval_methods, "rrf", topk
            )
        
        # Run RAG pipeline if requested
        rag_result = None
        if algorithm != "retrieval_only":
            rag_result = await self.flashrag_processor.run_rag_pipeline(
                algorithm, query, collection_name
            )
        
        return {
            "collection": collection_name,
            "algorithm": algorithm,
            "search_results": search_results,
            "rag_result": rag_result,
            "retrieval_methods": retrieval_methods
        }
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for collection"""
        
        if collection_name not in self.collections_config:
            raise ValueError(f"Collection {collection_name} not found")
        
        jsonl_path = self._get_collection_jsonl_path(collection_name)
        
        if not os.path.exists(jsonl_path):
            return {"document_count": 0, "size_bytes": 0}
        
        # Count documents
        doc_count = await self.jsonl_handler.count_documents(jsonl_path)
        
        # Get file size
        file_size = os.path.getsize(jsonl_path)
        
        return {
            "document_count": doc_count,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "config": self.collections_config[collection_name]
        }
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with stats"""
        
        collections = []
        for name in self.collections_config.keys():
            stats = await self.get_collection_stats(name)
            collections.append({
                "name": name,
                **stats
            })
        
        return collections
```

## 5. Utility Modules

### utils/jsonl_handler.py
```python
"""
JSONL file handler for FlashRAG documents
"""
import asyncio
import aiofiles
import json
from typing import List, AsyncGenerator, Optional
import logging

from models.flashrag_document import FlashRAGDocument

logger = logging.getLogger(__name__)

class JSONLHandler:
    """Handler for JSONL file operations"""
    
    async def write_documents(self, file_path: str, documents: List[FlashRAGDocument]):
        """Write documents to JSONL file"""
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                for doc in documents:
                    await f.write(doc.to_jsonl() + '\n')
            
            logger.info(f"Written {len(documents)} documents to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write JSONL file {file_path}: {e}")
            raise
    
    async def append_documents(self, file_path: str, documents: List[FlashRAGDocument]):
        """Append documents to JSONL file"""
        
        try:
            async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
                for doc in documents:
                    await f.write(doc.to_jsonl() + '\n')
            
            logger.info(f"Appended {len(documents)} documents to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to append to JSONL file {file_path}: {e}")
            raise
    
    async def read_documents(self, file_path: str, limit: Optional[int] = None) -> List[FlashRAGDocument]:
        """Read documents from JSONL file"""
        
        documents = []
        count = 0
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    if limit and count >= limit:
                        break
                    
                    line = line.strip()
                    if line:
                        doc = FlashRAGDocument.from_jsonl(line)
                        documents.append(doc)
                        count += 1
            
            logger.info(f"Read {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to read JSONL file {file_path}: {e}")
            raise
    
    async def stream_documents(self, file_path: str) -> AsyncGenerator[FlashRAGDocument, None]:
        """Stream documents from JSONL file"""
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        yield FlashRAGDocument.from_jsonl(line)
                        
        except Exception as e:
            logger.error(f"Failed to stream JSONL file {file_path}: {e}")
            raise
    
    async def count_documents(self, file_path: str) -> int:
        """Count documents in JSONL file"""
        
        count = 0
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    if line.strip():
                        count += 1
            return count
            
        except Exception as e:
            logger.error(f"Failed to count documents in {file_path}: {e}")
            return 0
    
    async def filter_documents(self, file_path: str, filter_func,
                             output_path: str) -> int:
        """Filter documents and save to new file"""
        
        filtered_docs = []
        
        async for doc in self.stream_documents(file_path):
            if filter_func(doc):
                filtered_docs.append(doc)
        
        await self.write_documents(output_path, filtered_docs)
        return len(filtered_docs)
```

### utils/flashrag_adapter.py
```python
"""
Adapter để convert giữa PostgreSQL và FlashRAG JSONL formats
"""
import asyncio
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

import asyncpg
from models.flashrag_document import FlashRAGDocument, RAGResult
from config.settings import settings

logger = logging.getLogger(__name__)

class FlashRAGAdapter:
    """Adapter giữa PostgreSQL database và FlashRAG JSONL"""
    
    def __init__(self):
        self.db_pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        if self.db_pool is None:
            self.db_pool = await asyncpg.create_pool(
                settings.database.url,
                min_size=5,
                max_size=settings.database.pool_size
            )
    
    async def save_flashrag_document(self, document: FlashRAGDocument,
                                   collection: str) -> bool:
        """Save FlashRAG document to PostgreSQL"""
        
        if not self.db_pool:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Insert vào documents table (existing schema)
                await conn.execute("""
                    INSERT INTO documents (doc_id, title, content, collection, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (doc_id) DO UPDATE SET
                        content = $3, metadata = $5, updated_at = CURRENT_TIMESTAMP
                """, 
                    document.id,
                    document.metadata.get('title', 'Untitled'),
                    document.contents,
                    collection,
                    json.dumps(document.metadata),
                    datetime.now()
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save FlashRAG document {document.id}: {e}")
            return False
    
    async def save_rag_result(self, result: RAGResult, session_id: str,
                            user_message: str) -> bool:
        """Save RAG result to conversations table"""
        
        if not self.db_pool:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversations (
                        session_id, user_message, bot_response, intent, target_product,
                        confidence, processing_time, sources_count, rag_algorithm,
                        flashrag_score, reasoning_steps, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                    session_id,
                    user_message,
                    result.response,
                    result.evaluation_metrics.get('intent', 'unknown'),
                    result.evaluation_metrics.get('target_product'),
                    result.confidence,
                    result.processing_stages.get('total_time', 0.0),
                    len(result.sources),
                    result.algorithm,
                    result.evaluation_metrics.get('flashrag_score', 0.0),
                    json.dumps(result.reasoning_steps) if result.reasoning_steps else None,
                    datetime.now()
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save RAG result: {e}")
            return False
    
    async def save_evaluation_result(self, evaluation: Dict[str, Any],
                                   session_id: str) -> bool:
        """Save evaluation result to rag_evaluations table"""
        
        if not self.db_pool:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO rag_evaluations (
                        session_id, algorithm, query_text, retrieved_docs,
                        refined_contexts, generated_response, evaluation_metrics,
                        processing_stages, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    session_id,
                    evaluation.get('algorithm'),
                    evaluation.get('query'),
                    json.dumps(evaluation.get('retrieved_docs', [])),
                    json.dumps(evaluation.get('refined_contexts', [])),
                    evaluation.get('response'),
                    json.dumps(evaluation.get('metrics', {})),
                    json.dumps(evaluation.get('processing_stages', {})),
                    datetime.now()
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save evaluation result: {e}")
            return False
    
    async def get_documents_for_collection(self, collection: str,
                                         limit: int = None) -> List[FlashRAGDocument]:
        """Get documents from PostgreSQL và convert to FlashRAG format"""
        
        if not self.db_pool:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT doc_id, title, content, metadata FROM documents WHERE collection = $1"
                if limit:
                    query += f" LIMIT {limit}"
                
                rows = await conn.fetch(query, collection)
                
                documents = []
                for row in rows:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                    metadata['title'] = row['title']
                    
                    doc = FlashRAGDocument(
                        id=row['doc_id'],
                        contents=row['content'],
                        metadata=metadata
                    )
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to get documents for collection {collection}: {e}")
            return []
    
    async def get_algorithm_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics cho các RAG algorithms"""
        
        if not self.db_pool:
            await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get basic stats
                stats = await conn.fetch("""
                    SELECT 
                        rag_algorithm,
                        COUNT(*) as total_queries,
                        AVG(confidence) as avg_confidence,
                        AVG(processing_time) as avg_processing_time,
                        AVG(flashrag_score) as avg_flashrag_score
                    FROM conversations 
                    WHERE rag_algorithm IS NOT NULL
                    GROUP BY rag_algorithm
                """)
                
                return {row['rag_algorithm']: dict(row) for row in stats}
                
        except Exception as e:
            logger.error(f"Failed to get algorithm performance stats: {e}")
            return {}
```

## 6. Main CLI Interface

### main.py
```python
"""
Main CLI interface cho FlashRAG Data Management System
"""
import asyncio
import click
import logging
from pathlib import Path
from typing import List, Optional

from core.collection_manager import EnhancedCollectionManager
from core.flashrag_processor import FlashRAGProcessor
from utils.flashrag_adapter import FlashRAGAdapter
from utils.jsonl_handler import JSONLHandler
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """FlashRAG-Enhanced Data Management CLI"""
    pass

@cli.group()
def collection():
    """Collection management commands"""
    pass

@collection.command()
@click.option('--name', required=True, help='Collection name')
async def stats(name: str):
    """Get collection statistics"""
    
    manager = EnhancedCollectionManager()
    await manager.initialize()
    
    try:
        stats = await manager.get_collection_stats(name)
        
        click.echo(f"\nCollection: {name}")
        click.echo("=" * 40)
        click.echo(f"Documents: {stats['document_count']}")
        click.echo(f"Size: {stats['size_mb']} MB")
        click.echo(f"Algorithms: {stats['config'].get('algorithms', [])}")
        click.echo(f"Retrieval methods: {stats['config'].get('retrieval_methods', [])}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@collection.command()
async def list():
    """List all collections"""
    
    manager = EnhancedCollectionManager()
    await manager.initialize()
    
    try:
        collections = await manager.list_collections()
        
        click.echo("\nAvailable Collections:")
        click.echo("=" * 50)
        
        for col in collections:
            click.echo(f"{col['name']:<20} {col['document_count']:<8} docs {col['size_mb']:<6} MB")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def algorithm():
    """RAG algorithm management commands"""
    pass

@algorithm.command()
async def list():
    """List available RAG algorithms"""
    
    algorithms = [
        "standard_rag - Standard Retrieve → Generate",
        "ret_robust - Multi-retrieval với robust ranking", 
        "r1_searcher - Multi-hop reasoning với graph search",
        "flare - Forward-looking active retrieval",
        "spring - Self-prompting iterative generation"
    ]
    
    click.echo("\nAvailable RAG Algorithms:")
    click.echo("=" * 50)
    
    for algo in algorithms:
        click.echo(f"• {algo}")

@algorithm.command()
@click.option('--name', required=True, help='Algorithm name')
@click.option('--query', required=True, help='Test query')
@click.option('--collection', help='Target collection')
async def test(name: str, query: str, collection: str):
    """Test RAG algorithm với query"""
    
    processor = FlashRAGProcessor()
    await processor.initialize()
    
    try:
        result = await processor.run_rag_pipeline(name, query, collection)
        
        click.echo(f"\nAlgorithm: {result.algorithm}")
        click.echo(f"Query: {query}")
        click.echo("=" * 50)
        click.echo(f"Response: {result.response}")
        click.echo(f"Confidence: {result.confidence:.3f}")
        click.echo(f"Processing time: {result.processing_stages.get('total_time', 0):.2f}s")
        click.echo(f"Sources: {len(result.sources)}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def document():
    """Document processing commands"""
    pass

@document.command()
@click.option('--file', required=True, type=click.Path(exists=True), help='Document file')
@click.option('--collection', required=True, help='Target collection')
@click.option('--method', default='semantic', help='Chunking method')
@click.option('--max-tokens', default=512, help='Max tokens per chunk')
async def ingest(file: str, collection: str, method: str, max_tokens: int):
    """Ingest document into collection"""
    
    manager = EnhancedCollectionManager()
    await manager.initialize()
    
    try:
        # Process document
        file_path = Path(file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chunk document
        chunks = await manager.flashrag_processor.chunk_document(
            content, method=method, max_tokens=max_tokens
        )
        
        # Add to collection
        added = await manager.add_documents_to_collection(collection, chunks)
        
        click.echo(f"Successfully ingested {added} chunks from {file_path.name} into {collection}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def search():
    """Search and retrieval commands"""
    pass

@search.command()
@click.option('--query', required=True, help='Search query')
@click.option('--collection', required=True, help='Collection to search')
@click.option('--algorithm', default='standard_rag', help='RAG algorithm')
@click.option('--topk', default=5, help='Number of results')
async def run(query: str, collection: str, algorithm: str, topk: int):
    """Run search với RAG algorithm"""
    
    manager = EnhancedCollectionManager()
    await manager.initialize()
    
    try:
        result = await manager.search_collection(collection, query, algorithm, topk)
        
        click.echo(f"\nQuery: {query}")
        click.echo(f"Collection: {collection}")
        click.echo(f"Algorithm: {algorithm}")
        click.echo("=" * 50)
        
        if result.get('rag_result'):
            rag = result['rag_result']
            click.echo(f"Response: {rag.response}")
            click.echo(f"Confidence: {rag.confidence:.3f}")
        
        click.echo(f"\nSearch Results ({len(result['search_results'])}):")
        for i, doc in enumerate(result['search_results'][:3]):
            click.echo(f"{i+1}. {doc.get('title', 'Untitled')[:60]}...")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
async def health():
    """Check system health"""
    
    try:
        # Test FlashRAG processor
        processor = FlashRAGProcessor()
        await processor.initialize()
        click.echo("✓ FlashRAG processor: OK")
        
        # Test database
        adapter = FlashRAGAdapter()
        await adapter.initialize()
        click.echo("✓ Database connection: OK")
        
        # Test collections config
        manager = EnhancedCollectionManager()
        collections = manager.collections_config
        click.echo(f"✓ Collections configured: {len(collections)}")
        
        click.echo("\n✅ System health: All components operational")
        
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)

def run_async_command(coro):
    """Helper để run async commands"""
    asyncio.run(coro)

# Make async commands work với click
for command in [stats, list, test, ingest, run, health]:
    command.callback = lambda func: lambda *args, **kwargs: run_async_command(func(*args, **kwargs))

if __name__ == '__main__':
    cli()
```

## 7. Enhanced Requirements

### requirements.txt
```txt
# Core dependencies
torch>=1.12.0
transformers>=4.20.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.2
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0

# Database
asyncpg>=0.27.0
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0

# Redis
redis>=4.0.0
aioredis>=2.0.0

# Web framework
fastapi>=0.68.0
uvicorn>=0.15.0
aiofiles>=0.8.0

# Configuration
python-dotenv>=0.19.0
pydantic>=1.8.0
PyYAML>=6.0

# CLI
click>=8.0.0

# Text processing
nltk>=3.7
spacy>=3.4.0

# Utilities
tqdm>=4.62.0
python-multipart>=0.0.5
```

Hệ thống này được thiết kế với tính module hóa cao, cho phép:

1. **Dễ dàng thay thế components**: Mỗi module có interface rõ ràng
2. **Configurable algorithms**: Có thể thêm/bớt RAG algorithms
3. **Flexible retrieval**: Support nhiều retrieval methods
4. **Database compatibility**: Tương thích với existing schema
5. **CLI-friendly**: Commands intuitive và comprehensive
6. **Error handling**: Robust error handling và logging
7. **Async support**: Performance tối ưu với async/await


Bạn có muốn tôi tiếp tục với các file còn lại như web interface hoặc test files không?
