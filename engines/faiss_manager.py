#engines/faiss_manager.py
"""
FAISS Collections Manager - Vector database management for document retrieval
"""
import os
import json
import pickle
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import faiss
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
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device='cpu'  # Use CPU for better stability in production
        )
        self.embedding_dim = 384  # MiniLM dimension
        
        # Collection definitions with Vietnamese content structure
        self.collection_configs = {
            'product_a_features': {
                'description': 'Tính năng và đặc điểm của Sản phẩm A',
                'keywords': ['product a', 'sản phẩm a', 'tính năng', 'feature', 'chức năng'],
                'index_type': 'flat',
                'max_docs': 1000,
                'similarity_threshold': 0.7
            },
            'product_a_pricing': {
                'description': 'Giá cả và gói dịch vụ Sản phẩm A',
                'keywords': ['product a', 'giá', 'pricing', 'cost', 'gói', 'plan', 'phí'],
                'index_type': 'flat',
                'max_docs': 200,
                'similarity_threshold': 0.75
            },
            'product_b_features': {
                'description': 'Tính năng và đặc điểm của Sản phẩm B',
                'keywords': ['product b', 'sản phẩm b', 'tính năng', 'feature', 'chức năng'],
                'index_type': 'flat',
                'max_docs': 1000,
                'similarity_threshold': 0.7
            },
            'product_b_pricing': {
                'description': 'Giá cả và gói dịch vụ Sản phẩm B',
                'keywords': ['product b', 'giá', 'pricing', 'cost', 'gói', 'plan', 'phí'],
                'index_type': 'flat',
                'max_docs': 200,
                'similarity_threshold': 0.75
            },
            'warranty_support': {
                'description': 'Thông tin bảo hành và hỗ trợ khách hàng',
                'keywords': ['bảo hành', 'warranty', 'support', 'hỗ trợ', 'khách hàng', 'service'],
                'index_type': 'flat',
                'max_docs': 500,
                'similarity_threshold': 0.7
            },
            'contact_company': {
                'description': 'Thông tin liên hệ và về công ty',
                'keywords': ['liên hệ', 'contact', 'company', 'công ty', 'địa chỉ', 'about'],
                'index_type': 'flat',
                'max_docs': 100,
                'similarity_threshold': 0.8
            }
        }
        
        self.collections = {}
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    async def initialize_collections(self):
        """Initialize all FAISS collections"""
        logger.info("Initializing FAISS collections...")
        
        for name, config in self.collection_configs.items():
            try:
                await self._create_collection(name, config)
                logger.info(f"Initialized collection: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize collection {name}: {e}")
                raise
        
        logger.info(f"Initialized {len(self.collections)} collections")
    
    async def _create_collection(self, name: str, config: Dict):
        """Create individual FAISS collection"""
        
        try:
            # Create appropriate FAISS index
            if config['index_type'] == 'flat':
                # Use Inner Product for cosine similarity (normalized vectors)
                index = faiss.IndexFlatIP(self.embedding_dim)
            elif config['index_type'] == 'ivf':
                # For larger datasets - IVF (Inverted File) index
                quantizer = faiss.IndexFlatIP(self.embedding_dim)
                n_centroids = min(100, max(10, config['max_docs'] // 10))
                index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, n_centroids)
            else:
                raise ValueError(f"Unknown index type: {config['index_type']}")
            
            # Wrap with ID mapping for document tracking
            index_with_ids = faiss.IndexIDMap2(index)
            
            self.collections[name] = {
                'index': index_with_ids,
                'base_index': index,  # Keep reference to base index
                'metadata_store': {},  # doc_id -> metadata mapping
                'doc_count': 0,
                'config': config,
                'loaded': False,
                'last_updated': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            raise
    
    async def add_documents_to_collection(
        self, 
        collection_name: str, 
        documents: List[DocumentChunk]
    ) -> int:
        """Add documents to specific collection with batch processing"""
        
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        if not documents:
            logger.warning(f"No documents provided for collection {collection_name}")
            return 0
        
        collection = self.collections[collection_name]
        logger.info(f"Adding {len(documents)} documents to collection {collection_name}")
        
        try:
            # Generate embeddings in batches for efficiency
            texts = [doc.content for doc in documents]
            embeddings = await self._generate_embeddings_batch(texts, batch_size=32)
            
            # Prepare data for FAISS
            doc_ids = []
            embedding_matrix = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                doc_id = f"{collection_name}_{collection['doc_count'] + i}_{int(time.time())}"
                
                # Normalize embedding for cosine similarity
                embedding_norm = np.linalg.norm(embedding)
                if embedding_norm > 0:
                    normalized_embedding = embedding / embedding_norm
                else:
                    logger.warning(f"Zero embedding for document in {collection_name}")
                    continue
                
                # Store metadata with additional information
                collection['metadata_store'][doc_id] = {
                    'id': doc_id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'collection': collection_name,
                    'added_at': time.time(),
                    'content_length': len(doc.content),
                    'content_hash': hash(doc.content) % (2**32)  # For deduplication
                }
                
                # Convert doc_id to integer for FAISS (use hash)
                doc_id_int = abs(hash(doc_id)) % (2**63)  # Ensure positive int64
                doc_ids.append(doc_id_int)
                embedding_matrix.append(normalized_embedding)
            
            # Add to FAISS index
            if embedding_matrix:
                embedding_matrix = np.array(embedding_matrix, dtype=np.float32)
                doc_ids_array = np.array(doc_ids, dtype=np.int64)
                
                # Train index if necessary (for IVF)
                if hasattr(collection['base_index'], 'is_trained') and not collection['base_index'].is_trained:
                    if embedding_matrix.shape[0] >= collection['base_index'].nlist:
                        collection['base_index'].train(embedding_matrix)
                        logger.info(f"Trained IVF index for collection {collection_name}")
                    else:
                        logger.warning(f"Not enough data to train IVF index for {collection_name}")
                
                collection['index'].add_with_ids(embedding_matrix, doc_ids_array)
                collection['doc_count'] += len(embedding_matrix)
                collection['last_updated'] = time.time()
                
                logger.info(f"Added {len(embedding_matrix)} documents to {collection_name}")
            
            # Save to disk
            await self._save_collection(collection_name)
            
            return len(embedding_matrix)
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            raise
    
    async def search_targeted_collections(
        self,
        queries: List[str],
        collections: List[str],
        context_filter: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search across specified collections with context filtering"""
        
        if not queries or not collections:
            logger.warning("Empty queries or collections provided")
            return []
        
        all_results = []
        
        for collection_name in collections:
            if collection_name not in self.collections:
                logger.warning(f"Collection {collection_name} not found")
                continue
            
            collection = self.collections[collection_name]
            if not collection['loaded']:
                logger.info(f"Loading collection {collection_name}")
                await self._load_collection(collection_name)
            
            if collection['index'].ntotal == 0:
                logger.warning(f"Collection {collection_name} is empty")
                continue
            
            similarity_threshold = collection['config'].get('similarity_threshold', 0.7)
            
            for query in queries:
                try:
                    results = await self._search_single_collection(
                        collection_name=collection_name,
                        query=query,
                        context_filter=context_filter,
                        top_k=top_k,
                        similarity_threshold=similarity_threshold
                    )
                    all_results.extend(results)
                    
                except Exception as e:
                    logger.error(f"Error searching collection {collection_name} with query '{query}': {e}")
                    continue
        
        # Post-process results
        if all_results:
            all_results = self._deduplicate_results(all_results)
            all_results = self._rerank_results(all_results)
            all_results = all_results[:top_k * len(collections)]  # Limit results
        
        logger.info(f"Found {len(all_results)} total results across {len(collections)} collections")
        return all_results
    
    async def _search_single_collection(
        self,
        collection_name: str,
        query: str,
        context_filter: Optional[Dict],
        top_k: int,
        similarity_threshold: float
    ) -> List[Dict]:
        """Search a single collection"""
        
        collection = self.collections[collection_name]
        
        # Generate query embedding
        query_embeddings = await self._generate_embeddings_batch([query])
        query_vector = query_embeddings[0]
        
        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm
        else:
            logger.warning(f"Zero query embedding for: {query}")
            return []
        
        query_matrix = np.array([query_vector], dtype=np.float32)
        
        # Search FAISS index
        scores, doc_ids = collection['index'].search(query_matrix, min(top_k * 2, collection['index'].ntotal))
        
        results = []
        for score, doc_id in zip(scores[0], doc_ids[0]):
            if doc_id == -1:  # No result found
                continue
            
            if score < similarity_threshold:
                continue
            
            # Find metadata by doc_id
            metadata = self._find_metadata_by_id(collection, doc_id)
            if not metadata:
                logger.warning(f"Metadata not found for doc_id {doc_id} in {collection_name}")
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
                'doc_id': metadata['id'],
                'content_length': metadata.get('content_length', len(metadata['content'])),
                'added_at': metadata.get('added_at', 0)
            }
            
            results.append(result)
        
        return results[:top_k]
    
    async def _generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> np.ndarray:
        """Generate embeddings with batch processing"""
        
        if not texts:
            return np.array([])
        
        try:
            # Clean texts
            cleaned_texts = [text.strip() for text in texts if text.strip()]
            
            if not cleaned_texts:
                logger.warning("No valid texts after cleaning")
                return np.array([])
            
            all_embeddings = []
            
            for i in range(0, len(cleaned_texts), batch_size):
                batch = cleaned_texts[i:i + batch_size]
                
                # Generate embeddings for batch
                batch_embeddings = self.embedding_model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=len(batch)
                )
                
                all_embeddings.append(batch_embeddings)
            
            # Combine all embeddings
            result = np.vstack(all_embeddings) if all_embeddings else np.array([])
            logger.debug(f"Generated embeddings for {len(cleaned_texts)} texts")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def _find_metadata_by_id(self, collection: Dict, doc_id: int) -> Optional[Dict]:
        """Find metadata by FAISS doc_id"""
        
        # Search through metadata store to find matching hash
        for stored_id, metadata in collection['metadata_store'].items():
            if abs(hash(stored_id)) % (2**63) == doc_id:
                return metadata
        
        return None
    
    def _matches_filter(self, metadata: Dict, context_filter: Dict) -> bool:
        """Check if metadata matches context filters"""
        
        if not context_filter:
            return True
        
        for key, value in context_filter.items():
            if value is None:
                continue
            
            # Check in both metadata and top-level fields
            metadata_value = metadata.get('metadata', {}).get(key)
            if metadata_value is None:
                metadata_value = metadata.get(key)
            
            # Flexible matching for string values
            if isinstance(value, str) and isinstance(metadata_value, str):
                if value.lower() not in metadata_value.lower():
                    return False
            elif metadata_value != value:
                return False
        
        return True
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on content similarity"""
        
        if len(results) <= 1:
            return results
        
        seen_hashes = set()
        deduplicated = []
        
        # Sort by score first (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        for result in results:
            # Create content hash for deduplication
            content = result['content']
            content_hash = hash(content[:200])  # Use first 200 chars for hash
            
            # Also check for very similar content lengths (potential duplicates)
            similar_found = False
            for existing_hash in seen_hashes:
                if abs(existing_hash - content_hash) < 100:  # Threshold for similarity
                    similar_found = True
                    break
            
            if not similar_found:
                seen_hashes.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    def _rerank_results(self, results: List[Dict]) -> List[Dict]:
        """Re-rank results based on multiple factors"""
        
        if len(results) <= 1:
            return results
        
        # Calculate composite score
        for result in results:
            base_score = result['score']
            
            # Boost factor based on content length (prefer substantial content)
            content_length = result.get('content_length', len(result['content']))
            length_factor = min(1.2, 1.0 + (content_length - 100) / 1000)  # Boost longer content
            
            # Recency factor (newer content gets slight boost)
            added_at = result.get('added_at', 0)
            if added_at > 0:
                age_days = (time.time() - added_at) / (24 * 3600)
                recency_factor = max(0.9, 1.0 - age_days / 365)  # Decay over year
            else:
                recency_factor = 1.0
            
            # Collection priority (some collections might be more important)
            collection_priority = self._get_collection_priority(result['collection'])
            
            # Calculate final score
            result['composite_score'] = base_score * length_factor * recency_factor * collection_priority
        
        # Sort by composite score
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return results
    
    def _get_collection_priority(self, collection_name: str) -> float:
        """Get priority multiplier for collection"""
        
        priority_map = {
            'product_a_features': 1.0,
            'product_b_features': 1.0,
            'product_a_pricing': 1.1,  # Pricing info slightly prioritized
            'product_b_pricing': 1.1,
            'warranty_support': 0.9,
            'contact_company': 0.8
        }
        
        return priority_map.get(collection_name, 1.0)
    
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
            
            # Save config and stats
            config_path = os.path.join(self.base_path, f"{collection_name}_config.json")
            config_data = {
                'config': collection['config'],
                'doc_count': collection['doc_count'],
                'last_updated': collection['last_updated'],
                'index_type': collection['config']['index_type'],
                'total_size': collection['index'].ntotal
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved collection {collection_name} to disk")
            
        except Exception as e:
            logger.error(f"Error saving collection {collection_name}: {e}")
            raise
    
    async def _load_collection(self, collection_name: str):
        """Load FAISS collection from disk"""
        
        try:
            # Load FAISS index
            index_path = os.path.join(self.base_path, f"{collection_name}.index")
            if os.path.exists(index_path):
                self.collections[collection_name]['index'] = faiss.read_index(index_path)
                logger.debug(f"Loaded FAISS index for {collection_name}")
            else:
                logger.warning(f"FAISS index file not found for {collection_name}")
            
            # Load metadata
            metadata_path = os.path.join(self.base_path, f"{collection_name}_metadata.pkl")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    self.collections[collection_name]['metadata_store'] = pickle.load(f)
                logger.debug(f"Loaded metadata for {collection_name}")
            else:
                logger.warning(f"Metadata file not found for {collection_name}")
            
            # Load config
            config_path = os.path.join(self.base_path, f"{collection_name}_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.collections[collection_name]['doc_count'] = config_data.get('doc_count', 0)
                    self.collections[collection_name]['last_updated'] = config_data.get('last_updated', time.time())
            
            self.collections[collection_name]['loaded'] = True
            
        except Exception as e:
            logger.error(f"Error loading collection {collection_name}: {e}")
            # Mark as loaded even if some files missing (for new collections)
            self.collections[collection_name]['loaded'] = True
    
    async def load_all_collections(self):
        """Load all collections from disk"""
        
        logger.info("Loading all FAISS collections...")
        
        if not self.collections:
            await self.initialize_collections()
        
        for collection_name in self.collection_configs.keys():
            try:
                await self._load_collection(collection_name)
                doc_count = self.collections[collection_name]['doc_count']
                index_size = self.collections[collection_name]['index'].ntotal
                logger.info(f"Loaded collection: {collection_name} ({doc_count} docs, {index_size} indexed)")
            except Exception as e:
                logger.error(f"Failed to load collection {collection_name}: {e}")
                # Continue loading other collections
                continue
        
        logger.info("Finished loading all collections")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all collections"""
        
        status = {
            'all_loaded': True,
            'total_collections': len(self.collection_configs),
            'collections': {},
            'embedding_model': {
                'model_name': self.embedding_model.get_sentence_embedding_dimension() is not None,
                'dimension': self.embedding_dim
            }
        }
        
        for name, collection in self.collections.items():
            collection_status = {
                'loaded': collection['loaded'],
                'doc_count': collection['doc_count'],
                'index_size': collection['index'].ntotal if collection['loaded'] else 0,
                'last_updated': collection.get('last_updated', 0),
                'config': {
                    'index_type': collection['config']['index_type'],
                    'max_docs': collection['config']['max_docs']
                }
            }
            
            if not collection['loaded']:
                status['all_loaded'] = False
                collection_status['error'] = 'Not loaded'
            
            status['collections'][name] = collection_status
        
        return status
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific collection"""
        
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        collection = self.collections[collection_name]
        
        stats = {
            'name': collection_name,
            'loaded': collection['loaded'],
            'doc_count': collection['doc_count'],
            'index_size': collection['index'].ntotal if collection['loaded'] else 0,
            'last_updated': collection.get('last_updated', 0),
            'config': collection['config'],
            'metadata_count': len(collection['metadata_store'])
        }
        
        # Calculate content statistics
        if collection['metadata_store']:
            content_lengths = [
                len(meta['content']) 
                for meta in collection['metadata_store'].values()
            ]
            
            stats['content_stats'] = {
                'avg_length': sum(content_lengths) / len(content_lengths),
                'min_length': min(content_lengths),
                'max_length': max(content_lengths),
                'total_characters': sum(content_lengths)
            }
        
        return stats