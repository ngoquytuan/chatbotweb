#utils/analytics.py
"""
Chat Analytics System - Track conversations and performance metrics
"""
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import logging

logger = logging.getLogger(__name__)


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
            'user_message': user_message[:500],  # Truncate for storage
            'bot_response': bot_response.response[:1000],  # Truncate for storage
            'intent': bot_response.intent,
            'target_product': bot_response.target_product,
            'confidence': bot_response.confidence,
            'processing_time': bot_response.processing_time,
            'sources_count': len(bot_response.sources),
            'user_ip': self._anonymize_ip(user_ip),
            'timestamp': datetime.now()
        }
        
        try:
            # Store in database (async)
            await self._store_conversation(conversation_data)
            
            # Update real-time metrics in Redis
            await self._update_realtime_metrics(conversation_data)
            
        except Exception as e:
            logger.error(f"Failed to track conversation: {e}")
    
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
            # Run database operation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._execute_db_query, query, data)
        except Exception as e:
            logger.error(f"Database store error: {e}")
    
    def _execute_db_query(self, query: str, data: Dict[str, Any]):
        """Execute database query synchronously"""
        try:
            with psycopg2.connect(self.postgres_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, data)
                    conn.commit()
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise
    
    async def _update_realtime_metrics(self, data: Dict[str, Any]):
        """Update real-time metrics in Redis"""
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Use pipeline for atomic operations
            pipeline = self.redis_client.pipeline()
            
            # Daily conversation count
            pipeline.incr(f"conversations:daily:{today}")
            
            # Intent distribution
            if data['intent']:
                pipeline.incr(f"intents:daily:{today}:{data['intent']}")
            
            # Product distribution
            if data['target_product']:
                pipeline.incr(f"products:daily:{today}:{data['target_product']}")
            
            # Processing time tracking
            pipeline.lpush(f"processing_times:{today}", data['processing_time'])
            pipeline.ltrim(f"processing_times:{today}", 0, 999)  # Keep last 1000
            
            # Confidence score tracking
            pipeline.lpush(f"confidence_scores:{today}", data['confidence'])
            pipeline.ltrim(f"confidence_scores:{today}", 0, 999)
            
            # Set expiration for daily keys (30 days)
            expire_time = 30 * 24 * 3600
            pipeline.expire(f"conversations:daily:{today}", expire_time)
            pipeline.expire(f"intents:daily:{today}:{data['intent']}", expire_time)
            pipeline.expire(f"products:daily:{today}:{data['target_product']}", expire_time)
            pipeline.expire(f"processing_times:{today}", expire_time)
            pipeline.expire(f"confidence_scores:{today}", expire_time)
            
            # Execute all operations
            pipeline.execute()
            
        except Exception as e:
            logger.error(f"Redis metrics update error: {e}")
    
    async def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics dashboard data"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Run database queries in thread pool
            loop = asyncio.get_event_loop()
            
            summary_task = loop.run_in_executor(None, self._get_summary_stats, start_date, end_date)
            daily_task = loop.run_in_executor(None, self._get_daily_conversations, start_date, end_date)
            intent_task = loop.run_in_executor(None, self._get_intent_distribution, start_date, end_date)
            product_task = loop.run_in_executor(None, self._get_product_distribution, start_date, end_date)
            performance_task = loop.run_in_executor(None, self._get_performance_metrics, start_date, end_date)
            
            # Wait for all tasks to complete
            summary, daily_convs, intents, products, performance = await asyncio.gather(
                summary_task, daily_task, intent_task, product_task, performance_task
            )
            
            return {
                'summary': summary,
                'daily_conversations': daily_convs,
                'intent_distribution': intents,
                'product_distribution': products,
                'performance_metrics': performance,
                'realtime_metrics': await self._get_realtime_metrics()
            }
            
        except Exception as e:
            logger.error(f"Dashboard data error: {e}")
            return {
                'error': 'Analytics temporarily unavailable',
                'summary': {'total_conversations': 0, 'avg_confidence': 0, 'avg_processing_time': 0},
                'daily_conversations': [],
                'intent_distribution': [],
                'product_distribution': [],
                'performance_metrics': {},
                'realtime_metrics': {}
            }
    
    def _get_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get summary statistics from database"""
        query = """
        SELECT 
            COUNT(*) as total_conversations,
            AVG(confidence) as avg_confidence,
            AVG(processing_time) as avg_processing_time,
            MIN(created_at) as earliest_conversation,
            MAX(created_at) as latest_conversation
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s
        """
        
        with psycopg2.connect(self.postgres_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (start_date, end_date))
                result = cursor.fetchone()
                
                return {
                    'total_conversations': result['total_conversations'] or 0,
                    'avg_confidence': float(result['avg_confidence'] or 0),
                    'avg_processing_time': float(result['avg_processing_time'] or 0),
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
    
    def _get_daily_conversations(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily conversation counts"""
        query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence,
            AVG(processing_time) as avg_processing_time
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
        """
        
        with psycopg2.connect(self.postgres_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()
                
                return [
                    {
                        'date': row['date'].isoformat(),
                        'conversations': row['count'],
                        'avg_confidence': float(row['avg_confidence'] or 0),
                        'avg_processing_time': float(row['avg_processing_time'] or 0)
                    }
                    for row in results
                ]
    
    def _get_intent_distribution(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get intent distribution"""
        query = """
        SELECT 
            intent,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s AND intent IS NOT NULL
        GROUP BY intent
        ORDER BY count DESC
        """
        
        with psycopg2.connect(self.postgres_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()
                
                return [
                    {
                        'intent': row['intent'],
                        'count': row['count'],
                        'avg_confidence': float(row['avg_confidence'] or 0)
                    }
                    for row in results
                ]
    
    def _get_product_distribution(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get product distribution"""
        query = """
        SELECT 
            target_product,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s AND target_product IS NOT NULL
        GROUP BY target_product
        ORDER BY count DESC
        """
        
        with psycopg2.connect(self.postgres_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()
                
                return [
                    {
                        'product': row['target_product'],
                        'count': row['count'],
                        'avg_confidence': float(row['avg_confidence'] or 0)
                    }
                    for row in results
                ]
    
    def _get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics"""
        query = """
        SELECT 
            AVG(processing_time) as avg_processing_time,
            MIN(processing_time) as min_processing_time,
            MAX(processing_time) as max_processing_time,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_time) as median_processing_time,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time) as p95_processing_time,
            AVG(sources_count) as avg_sources_count
        FROM conversations 
        WHERE created_at >= %s AND created_at <= %s
        """
        
        with psycopg2.connect(self.postgres_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (start_date, end_date))
                result = cursor.fetchone()
                
                return {
                    'processing_time': {
                        'avg': float(result['avg_processing_time'] or 0),
                        'min': float(result['min_processing_time'] or 0),
                        'max': float(result['max_processing_time'] or 0),
                        'median': float(result['median_processing_time'] or 0),
                        'p95': float(result['p95_processing_time'] or 0)
                    },
                    'avg_sources_per_response': float(result['avg_sources_count'] or 0)
                }
    
    async def _get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics from Redis"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get today's conversation count
            conversations_today = self.redis_client.get(f"conversations:daily:{today}") or 0
            
            # Get processing times for today
            processing_times = self.redis_client.lrange(f"processing_times:{today}", 0, -1)
            avg_processing_time = 0
            if processing_times:
                times = [float(t) for t in processing_times]
                avg_processing_time = sum(times) / len(times)
            
            # Get confidence scores for today
            confidence_scores = self.redis_client.lrange(f"confidence_scores:{today}", 0, -1)
            avg_confidence = 0
            if confidence_scores:
                scores = [float(s) for s in confidence_scores]
                avg_confidence = sum(scores) / len(scores)
            
            return {
                'conversations_today': int(conversations_today),
                'avg_processing_time_today': round(avg_processing_time, 3),
                'avg_confidence_today': round(avg_confidence, 3),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Realtime metrics error: {e}")
            return {}
    
    def _anonymize_ip(self, ip: str) -> str:
        """Anonymize IP address for privacy compliance"""
        if not ip or ip == "unknown":
            return "unknown"
        
        # Hash IP address for anonymization while preserving uniqueness
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        return ip_hash[:16]  # Use first 16 characters of hash