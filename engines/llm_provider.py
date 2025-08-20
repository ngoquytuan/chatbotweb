#engines/llm_provider.py
"""
Multi-LLM Provider Handler - Manages multiple LLM providers with automatic failover
"""
import asyncio
import aiohttp
import json
import time
import random
import os
import logging
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OPENROUTER = "openrouter"
    GROQ = "groq"
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass
class ProviderMetrics:
    response_times: List[float]
    success_rate: float
    last_error: Optional[str]
    available: bool
    total_requests: int
    successful_requests: int


class MultiLLMProvider:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.providers: Dict[LLMProvider, Dict[str, Any]] = {}
        
        self.provider_configs = {
            LLMProvider.OPENROUTER: {
                'url': 'https://openrouter.ai/api/v1/chat/completions',
                'model': 'anthropic/claude-3.5-sonnet',
                'api_key_env': 'OPENROUTER_API_KEY',
                'priority': 1,
                'timeout': 30,
                'max_tokens': 2000,
                'headers_extra': {
                    'HTTP-Referer': os.getenv('DOMAIN_URL', 'https://yourdomain.com'),
                    'X-Title': 'Enterprise Chatbot'
                }
            },
            LLMProvider.GROQ: {
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'model': 'llama-3.1-70b-versatile',
                'api_key_env': 'GROQ_API_KEY',
                'priority': 2,
                'timeout': 25,
                'max_tokens': 2000,
                'headers_extra': {}
            },
            LLMProvider.GEMINI: {
                'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent',
                'model': 'gemini-1.5-flash',
                'api_key_env': 'GEMINI_API_KEY',
                'priority': 3,
                'timeout': 30,
                'max_tokens': 2000,
                'headers_extra': {}
            },
            LLMProvider.OPENAI: {
                'url': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-4o-mini',
                'api_key_env': 'OPENAI_API_KEY',
                'priority': 4,
                'timeout': 35,
                'max_tokens': 2000,
                'headers_extra': {}
            }
        }
    
    async def initialize_providers(self):
        """Initialize HTTP session and check provider availability"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        
        for provider in LLMProvider:
            config = self.provider_configs[provider]
            api_key = os.getenv(config['api_key_env'])
            
            self.providers[provider] = {
                'config': config,
                'api_key': api_key,
                'metrics': ProviderMetrics(
                    response_times=[],
                    success_rate=1.0 if api_key else 0.0,
                    last_error=None if api_key else 'API key not found',
                    available=bool(api_key),
                    total_requests=0,
                    successful_requests=0
                )
            }
        
        # Initial health check
        await self._update_provider_health()
        logger.info(f"Initialized {len([p for p in self.providers.values() if p['metrics'].available])} LLM providers")
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        preferred_provider: Optional[LLMProvider] = None,
        max_retries: int = 3,
        temperature: float = 0.7
    ) -> str:
        """Call LLM with automatic failover"""
        
        if not self.session:
            raise Exception("LLM provider not initialized. Call initialize_providers() first.")
        
        # Get available providers sorted by priority and health
        available_providers = self._get_available_providers()
        
        if not available_providers:
            raise Exception("No LLM providers available")
        
        if preferred_provider and preferred_provider in available_providers:
            # Move preferred provider to front
            available_providers.remove(preferred_provider)
            available_providers.insert(0, preferred_provider)
        
        last_error = None
        
        for provider in available_providers:
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    response = await self._call_provider(provider, messages, temperature)
                    
                    # Update metrics
                    response_time = time.time() - start_time
                    self._update_provider_metrics(provider, response_time, success=True)
                    
                    logger.debug(f"LLM call successful: {provider.value} in {response_time:.2f}s")
                    return response
                    
                except Exception as e:
                    last_error = e
                    self._update_provider_metrics(provider, 0, success=False)
                    
                    logger.warning(f"LLM call failed: {provider.value}, attempt {attempt + 1}, error: {str(e)}")
                    
                    # Wait before retry with exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                        await asyncio.sleep(wait_time)
        
        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def _call_provider(
        self, 
        provider: LLMProvider, 
        messages: List[Dict], 
        temperature: float
    ) -> str:
        """Call specific LLM provider"""
        
        provider_data = self.providers[provider]
        config = provider_data['config']
        api_key = provider_data['api_key']
        
        if not api_key:
            raise Exception(f"No API key for {provider.value}")
        
        if provider == LLMProvider.GEMINI:
            return await self._call_gemini(messages, config, api_key, temperature)
        else:
            return await self._call_openai_compatible(messages, config, api_key, provider, temperature)
    
    async def _call_openai_compatible(
        self,
        messages: List[Dict],
        config: Dict,
        api_key: str,
        provider: LLMProvider,
        temperature: float
    ) -> str:
        """Call OpenAI-compatible APIs (OpenRouter, Groq, OpenAI)"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Add provider-specific headers
        headers.update(config.get('headers_extra', {}))
        
        payload = {
            'model': config['model'],
            'messages': messages,
            'max_tokens': config['max_tokens'],
            'temperature': temperature,
            'stream': False
        }
        
        # Add provider-specific parameters
        if provider == LLMProvider.OPENROUTER:
            payload['top_p'] = 0.9
        elif provider == LLMProvider.GROQ:
            payload['top_p'] = 0.9
            payload['stop'] = None
        
        try:
            async with self.session.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=config['timeout'])
            ) as response:
                
                response_text = await response.text()
                
                if response.status != 200:
                    logger.error(f"{provider.value} API error {response.status}: {response_text}")
                    raise Exception(f"{provider.value} API error {response.status}: {response_text[:200]}")
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {provider.value}: {response_text[:200]}")
                    raise Exception(f"Invalid JSON response from {provider.value}")
                
                if 'choices' not in result or len(result['choices']) == 0:
                    logger.error(f"Invalid response structure from {provider.value}: {result}")
                    raise Exception(f"Invalid response structure from {provider.value}")
                
                content = result['choices'][0]['message']['content']
                if not content or not content.strip():
                    raise Exception(f"Empty response from {provider.value}")
                
                return content.strip()
                
        except asyncio.TimeoutError:
            raise Exception(f"Timeout calling {provider.value}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling {provider.value}: {str(e)}")
    
    async def _call_gemini(
        self, 
        messages: List[Dict], 
        config: Dict, 
        api_key: str, 
        temperature: float
    ) -> str:
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
                'temperature': temperature,
                'topP': 0.9,
                'topK': 40
            },
            'safetySettings': [
                {
                    'category': 'HARM_CATEGORY_HARASSMENT',
                    'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                },
                {
                    'category': 'HARM_CATEGORY_HATE_SPEECH',
                    'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                }
            ]
        }
        
        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=config['timeout'])
            ) as response:
                
                response_text = await response.text()
                
                if response.status != 200:
                    logger.error(f"Gemini API error {response.status}: {response_text}")
                    raise Exception(f"Gemini API error {response.status}: {response_text[:200]}")
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from Gemini: {response_text[:200]}")
                    raise Exception("Invalid JSON response from Gemini")
                
                if 'candidates' not in result or len(result['candidates']) == 0:
                    # Check for safety issues
                    if 'promptFeedback' in result:
                        feedback = result['promptFeedback']
                        if feedback.get('blockReason'):
                            raise Exception(f"Gemini blocked request: {feedback['blockReason']}")
                    
                    logger.error(f"Invalid Gemini response: {result}")
                    raise Exception("Invalid response from Gemini")
                
                candidate = result['candidates'][0]
                
                # Check if content was blocked
                if 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
                    raise Exception("Gemini response blocked by safety filters")
                
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    logger.error(f"Missing content in Gemini response: {candidate}")
                    raise Exception("Missing content in Gemini response")
                
                content = candidate['content']['parts'][0]['text']
                if not content or not content.strip():
                    raise Exception("Empty response from Gemini")
                
                return content.strip()
                
        except asyncio.TimeoutError:
            raise Exception("Timeout calling Gemini")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling Gemini: {str(e)}")
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict]) -> str:
        """Convert OpenAI format messages to Gemini prompt"""
        prompt_parts = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                prompt_parts.append(f"System Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers sorted by priority and health"""
        available = []
        
        for provider, data in self.providers.items():
            metrics = data['metrics']
            if metrics.available and metrics.success_rate > 0.1:
                priority = data['config']['priority']
                # Calculate composite score: lower priority number is better, higher success rate is better
                score = priority - (metrics.success_rate * 0.5)  # Adjust success rate impact
                available.append((provider, score, metrics.success_rate))
        
        # Sort by composite score
        available.sort(key=lambda x: x[1])
        
        return [provider for provider, _, _ in available]
    
    def _update_provider_metrics(self, provider: LLMProvider, response_time: float, success: bool):
        """Update provider performance metrics"""
        
        metrics = self.providers[provider]['metrics']
        
        # Update counters
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
            
            # Update response times (keep last 100)
            metrics.response_times.append(response_time)
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
        
        # Update success rate (exponential moving average)
        alpha = 0.1  # Learning rate
        new_point = 1.0 if success else 0.0
        metrics.success_rate = alpha * new_point + (1 - alpha) * metrics.success_rate
        
        # Mark as unavailable if success rate is too low
        if metrics.success_rate < 0.1 and metrics.total_requests > 5:
            metrics.available = False
            metrics.last_error = 'Low success rate'
            logger.warning(f"Marking {provider.value} as unavailable due to low success rate")
        elif success and not metrics.available and metrics.success_rate > 0.5:
            # Re-enable if success rate improves
            metrics.available = True
            metrics.last_error = None
            logger.info(f"Re-enabling {provider.value} due to improved success rate")
    
    async def _update_provider_health(self):
        """Periodic health check for all providers"""
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'OK' if you can respond."}
        ]
        
        health_check_tasks = []
        for provider in self.providers.keys():
            if self.providers[provider]['api_key']:
                task = self._health_check_provider(provider, test_messages)
                health_check_tasks.append(task)
        
        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)
    
    async def _health_check_provider(self, provider: LLMProvider, test_messages: List[Dict]):
        """Health check for individual provider"""
        try:
            await asyncio.wait_for(
                self._call_provider(provider, test_messages, 0.1), 
                timeout=15
            )
            metrics = self.providers[provider]['metrics']
            metrics.available = True
            metrics.last_error = None
        except Exception as e:
            metrics = self.providers[provider]['metrics']
            metrics.available = False
            metrics.last_error = str(e)
            logger.debug(f"Health check failed for {provider.value}: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        await self._update_provider_health()
        
        status = {
            'overall_status': 'healthy',
            'providers': {},
            'summary': {
                'total_providers': len(self.providers),
                'available_providers': 0,
                'degraded_providers': 0
            }
        }
        
        available_count = 0
        degraded_count = 0
        
        for provider, data in self.providers.items():
            metrics = data['metrics']
            
            avg_response_time = 0.0
            if metrics.response_times:
                avg_response_time = sum(metrics.response_times) / len(metrics.response_times)
            
            provider_status = {
                'available': metrics.available,
                'success_rate': round(metrics.success_rate, 3),
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'last_error': metrics.last_error,
                'has_api_key': bool(data['api_key'])
            }
            
            if metrics.available:
                available_count += 1
                if metrics.success_rate < 0.8:
                    degraded_count += 1
            
            status['providers'][provider.value] = provider_status
        
        status['summary']['available_providers'] = available_count
        status['summary']['degraded_providers'] = degraded_count
        
        # Determine overall status
        if available_count == 0:
            status['overall_status'] = 'unhealthy'
        elif available_count < len(self.providers) * 0.5 or degraded_count > 0:
            status['overall_status'] = 'degraded'
        
        return status
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get detailed provider statistics"""
        stats = {}
        
        for provider, data in self.providers.items():
            metrics = data['metrics']
            
            stats[provider.value] = {
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'success_rate': round(metrics.success_rate, 3),
                'avg_response_time': round(
                    sum(metrics.response_times) / len(metrics.response_times), 3
                ) if metrics.response_times else 0,
                'min_response_time': round(min(metrics.response_times), 3) if metrics.response_times else 0,
                'max_response_time': round(max(metrics.response_times), 3) if metrics.response_times else 0,
                'last_error': metrics.last_error,
                'available': metrics.available
            }
        
        return stats
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("LLM provider session closed")