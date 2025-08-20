#utils/cache.py
"""
Cache Manager - Redis-based caching for responses and session management
"""
import json
import hashlib
import time
from typing import Optional, Dict, Any
import redis
import logging
from models.schemas import ChatResponse, PageContext

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.cache_prefix = "chatbot:cache:"
        self.session_prefix = "chatbot:session:"
        self.stats_prefix = "chatbot:stats:"
        
        # Cache TTL settings (seconds)
        self.default_ttl = 3600  # 1 hour
        self.session_ttl = 24 * 3600  # 24 hours
        self.stats_ttl = 7 * 24 * 3600  # 7 days
    
    def generate_cache_key(self, message: str, context: PageContext) -> str:
        """Generate cache key for message and context"""
        
        # Create a hash from message and relevant context
        cache_input = {
            'message': message.lower().strip(),
            'product': context.product,
            'section': context.section,
            'url_path': self._extract_path(context.url)
        }
        
        cache_string = json.dumps(cache_input, sort_keys=True, ensure_ascii=False)
        cache_hash = hashlib.md5(cache_string.encode('utf-8')).hexdigest()
        
        return f"{self.cache_prefix}response:{cache_hash}"
    
    def _extract_path(self, url: str) -> str:
        """Extract relevant path from URL for caching"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.path
        except:
            return ""
    
    async def get_cached_response(self, cache_key: str) -> Optional[ChatResponse]:
        """Get cached response if available"""
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Update cache hit stats
                self._update_cache_stats("hits")
                
                # Convert back to ChatResponse
                return ChatResponse(**data)
            
            # Update cache miss stats
            self._update_cache_stats("misses")
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            self._update_cache_stats("errors")
            return None
    
    async def cache_response(
        self,
        cache_key: str,
        response: ChatResponse,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache response with TTL"""
        
        try:
            # Convert ChatResponse to dict for JSON serialization
            response_data = response.dict()
            
            # Set cache with TTL
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response_data, ensure_ascii=False)
            )
            
            # Update cache set stats
            self._update_cache_stats("sets")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            self._update_cache_stats("errors")
            return False
    
    async def store_session_data(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Store session data"""
        
        try:
            session_key = f"{self.session_prefix}{session_id}"
            
            # Add timestamp
            data['last_updated'] = time.time()
            
            self.redis_client.setex(
                session_key,
                self.session_ttl,
                json.dumps(data, ensure_ascii=False)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Session storage error: {e}")
            return False
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Session retrieval error: {e}")
            return None
    
    def _update_cache_stats(self, stat_type: str):
        """Update cache statistics"""
        
        try:
            today = time.strftime('%Y-%m-%d')
            stat_key = f"{self.stats_prefix}{stat_type}:{today}"
            
            pipeline = self.redis_client.pipeline()
            pipeline.incr(stat_key)
            pipeline.expire(stat_key, self.stats_ttl)
            pipeline.execute()
            
        except Exception as e:
            logger.error(f"Stats update error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        try:
            today = time.strftime('%Y-%m-%d')
            
            stats = {}
            for stat_type in ['hits', 'misses', 'sets', 'errors']:
                stat_key = f"{self.stats_prefix}{stat_type}:{today}"
                value = self.redis_client.get(stat_key)
                stats[stat_type] = int(value) if value else 0
            
            # Calculate hit rate
            total_requests = stats['hits'] + stats['misses']
            stats['hit_rate'] = (stats['hits'] / total_requests) if total_requests > 0 else 0.0
            
            # Get Redis info
            redis_info = self.redis_client.info('memory')
            stats['redis_memory_used'] = redis_info.get('used_memory', 0)
            stats['redis_memory_peak'] = redis_info.get('used_memory_peak', 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'errors': 1,
                'hit_rate': 0.0,
                'redis_memory_used': 0,
                'redis_memory_peak': 0
            }
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        
        try:
            if pattern:
                keys = self.redis_client.keys(f"{self.cache_prefix}*{pattern}*")
            else:
                keys = self.redis_client.keys(f"{self.cache_prefix}*")
            
            if keys:
                return self.redis_client.delete(*keys)
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_cache_size(self) -> int:
        """Get total number of cached items"""
        
        try:
            return len(self.redis_client.keys(f"{self.cache_prefix}*"))
        except Exception as e:
            logger.error(f"Cache size error: {e}")
            return 0