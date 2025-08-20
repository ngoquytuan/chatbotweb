#engines/intent_classifier.py
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