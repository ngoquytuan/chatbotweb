### engines/intent_classifier.py

```python
"""
Intent Classification Engine with LLM and keyword fallback
"""
import json
import re
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


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
        self.llm_provider = None
        
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
            IntentType.GENERAL_CHAT: ['contact_company']
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
        
        # Backup with keyword classification if confidence is low
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
        """.strip()
        
        history_info = ""
        if history and len(history) > 0:
            recent_messages = history[-3:]  # Last 3 messages
            history_info = "Recent Conversation:\n"
            for msg in recent_messages:
                history_info += f"{msg.sender}: {msg.content}\n"
        
        system_prompt = f"""You are an expert intent classifier for a Vietnamese/English website chatbot.

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
}}"""
        
        user_prompt = f'User Query: "{query}"'
        
        try:
            if not self.llm_provider:
                raise Exception("LLM provider not initialized")
            
            response = await self.llm_provider.call_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result_data = json.loads(json_str)
            else:
                result_data = json.loads(response)
            
            return IntentResult(
                intent=IntentType(result_data.get('intent', 'general_chat')),
                confidence=float(result_data.get('confidence', 0.5)),
                target_product=result_data.get('target_product'),
                target_collections=[],
                refined_queries=[],
                entities=result_data.get('entities', {}),
                reasoning=result_data.get('reasoning', '')
            )
            
        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")
            return self._keyword_classify_intent(query, context)
    
    def _keyword_classify_intent(self, query: str, context: 'PageContext') -> IntentResult:
        """Fallback keyword-based intent classification"""
        
        query_lower = query.lower()
        best_intent = IntentType.GENERAL_CHAT
        best_score = 0.0
        
        # Score each intent based on keyword matches
        for intent_type, patterns in self.keyword_patterns.items():
            score = 0.0
            
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1.0
            
            # Normalize score
            if patterns:
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
            confidence=min(best_score + 0.3, 1.0) if best_score > 0 else 0.5,
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
            return collection_mapping if isinstance(collection_mapping, list) else [collection_mapping]
    
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
                refined_queries.extend([
                    f"{target_product} tính năng",
                    f"{target_product} chức năng"
                ])
            refined_queries.extend([
                "đặc điểm sản phẩm",
                "tính năng chính",
                "product features"
            ])
            
        elif intent == IntentType.PRICING_INQUIRY:
            if target_product:
                refined_queries.extend([
                    f"{target_product} giá cả",
                    f"{target_product} pricing"
                ])
            refined_queries.extend([
                "bảng giá dịch vụ",
                "gói cước phí",
                "pricing plans"
            ])
            
        elif intent == IntentType.SUPPORT_REQUEST:
            refined_queries.extend([
                "hướng dẫn sử dụng",
                "cách thức hoạt động",
                "hỗ trợ khách hàng",
                "user guide"
            ])
            
        elif intent == IntentType.WARRANTY_INQUIRY:
            refined_queries.extend([
                "chính sách bảo hành",
                "điều khoản đảm bảo",
                "hoàn tiền dịch vụ",
                "warranty policy"
            ])
            
        elif intent == IntentType.CONTACT_REQUEST:
            refined_queries.extend([
                "thông tin liên hệ",
                "địa chỉ công ty",
                "hotline hỗ trợ",
                "contact information"
            ])
        
        # Remove duplicates and limit to 4 queries
        seen = set()
        unique_queries = []
        for query in refined_queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:4]
```

### engines/faiss_manager.py

```python
"""
FAISS Collections Manager for document storage and retrieval
"""
import os
import json
import time
import pickle
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


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
        logger.info(f"FAISS manager initialized with base path: {base_path}")
    
    async def initialize_collections(self):
        """Initialize all FAISS collections"""
        logger.info("Initializing FAISS collections...")
        
        for name, config in self.collection_configs.items():
            await self._create_collection(name, config)
            logger.info(f"Created collection: {name}")
    
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
        logger.info(f"Adding {len(documents)} documents to {collection_name}")
        
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
        logger.info(f"Added {len(documents)} documents to {collection_name}")
        
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
        logger.info(f"Searching collections {collections} with queries: {queries}")
        
        for collection_name in collections:
            if collection_name not in self.collections:
                logger.warning(f"Collection {collection_name} not found, skipping")
                continue
            
            collection = self.collections[collection_name]
            if not collection['loaded']:
                await self._load_collection(collection_name)
            
            for query in queries:
                try:
                    # Generate query embedding
                    query_embedding = await self._generate_embeddings_batch([query])
                    query_vector = query_embedding[0] / np.linalg.norm(query_embedding[0])
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
                        
                except Exception as e:
                    logger.error(f"Error searching {collection_name} with query '{query}': {e}")
                    continue
        
        # Sort by score and remove duplicates
        all_results = self._deduplicate_results(all_results)
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        final_results = all_results[:top_k * len(collections)]
        logger.info(f"Found {len(final_results)} relevant documents")
        
        return final_results
    
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
            # Use first 100 chars as a simple hash for deduplication
            content_hash = hash(result['content'][:100])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    async def _save_collection(self, collection_name: str):
        """Save FAISS collection to disk"""
        collection = self.collections[collection_name]
        
        try:
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
                
            logger.info(f"Saved collection {collection_name} to disk")
            
        except Exception as e:
            logger.error(f"Failed to save collection {collection_name}: {e}")
            raise
    
    async def _load_collection(self, collection_name: str):
        """Load FAISS collection from disk"""
        
        try:
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
            logger.info(f"Loaded collection {collection_name} from disk")
            
        except Exception as e:
            logger.error(f"Failed to load collection {collection_name}: {e}")
            # Initialize empty collection if loading fails
            await self._create_collection(collection_name, self.collection_configs[collection_name])
    
    async def load_all_collections(self):
        """Load all collections from disk"""
        logger.info("Loading all FAISS collections...")
        
        for collection_name in self.collection_configs.keys():
            try:
                await self._load_collection(collection_name)
                doc_count = self.collections[collection_name]['doc_count']
                logger.info(f"Loaded collection: {collection_name} ({doc_count} docs)")
            except Exception as e:
                logger.error(f"Failed to load collection {collection_name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all collections"""
        status = {
            'all_loaded': True,
            'collections': {},
            'total_documents': 0
        }
        
        for name, collection in self.collections.items():
            collection_status = {
                'loaded': collection['loaded'],
                'doc_count': collection['doc_count'],
                'index_size': collection['index'].ntotal if collection['loaded'] else 0,
                'config': collection['config']['description']
            }
            
            if not collection['loaded']:
                status['all_loaded'] = False
            
            status['collections'][name] = collection_status
            status['total_documents'] += collection['doc_count']
        
        return status
```

Je continues avec les fichiers restants dans la prochaine réponse.