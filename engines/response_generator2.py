#engines/response_generator.py
"""
Contextual Response Generator
Generates responses using RAG with multiple LLM providers
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from .intent_classifier import IntentResult, IntentType
from models.schemas import PageContext, ChatMessage


class ContextualResponseGenerator:
    def __init__(self):
        self.llm_provider = None
        self.faiss_manager = None
        
        # Response templates for different intents
        self.response_templates = {
            IntentType.PRODUCT_INQUIRY: {
                "system_prompt": """Bạn là chuyên gia tư vấn sản phẩm thông minh. Nhiệm vụ của bạn là:
1. Trả lời câu hỏi về tính năng và đặc điểm sản phẩm một cách chính xác
2. Sử dụng thông tin từ tài liệu được cung cấp
3. Giải thích rõ ràng, dễ hiểu cho khách hàng
4. Nếu không có thông tin, hãy thành thật nói rằng cần thêm chi tiết

Trả lời bằng tiếng Việt, giọng điệu chuyên nghiệp nhưng thân thiện.""",
                "max_tokens": 400
            },
            IntentType.PRICING_INQUIRY: {
                "system_prompt": """Bạn là chuyên viên tư vấn giá và gói dịch vụ. Nhiệm vụ của bạn là:
1. Cung cấp thông tin giá cả chính xác từ tài liệu
2. Giải thích các gói dịch vụ và lợi ích
3. So sánh các tùy chọn nếu có
4. Hướng dẫn khách hàng lựa chọn phù hợp

Trả lời bằng tiếng Việt, tập trung vào giá trị mang lại cho khách hàng.""",
                "max_tokens": 350
            },
            IntentType.SUPPORT_REQUEST: {
                "system_prompt": """Bạn là chuyên viên hỗ trợ kỹ thuật. Nhiệm vụ của bạn là:
1. Hướng dẫn khách hàng giải quyết vấn đề từng bước
2. Sử dụng thông tin từ tài liệu hướng dẫn
3. Đưa ra giải pháp cụ thể và dễ thực hiện
4. Nếu vấn đề phức tạp, hướng dẫn liên hệ support trực tiếp

Trả lời bằng tiếng Việt, giọng điệu hỗ trợ và kiên nhẫn.""",
                "max_tokens": 450
            },
            IntentType.WARRANTY_INQUIRY: {
                "system_prompt": """Bạn là chuyên viên tư vấn chính sách bảo hành. Nhiệm vụ của bạn là:
1. Giải thích chính sách bảo hành một cách rõ ràng
2. Hướng dẫn quy trình yêu cầu bảo hành
3. Trả lời về điều kiện và thời hạn bảo hành
4. Cung cấp thông tin liên hệ nếu cần hỗ trợ trực tiếp

Trả lời bằng tiếng Việt, đảm bảo thông tin chính xác.""",
                "max_tokens": 400
            },
            IntentType.CONTACT_REQUEST: {
                "system_prompt": """Bạn là nhân viên hỗ trợ khách hàng. Nhiệm vụ của bạn là:
1. Cung cấp thông tin liên hệ chính xác
2. Hướng dẫn cách liên hệ phù hợp với nhu cầu
3. Đưa ra thông tin về giờ hoạt động
4. Gợi ý kênh liên hệ tốt nhất

Trả lời bằng tiếng Việt, thân thiện và hữu ích.""",
                "max_tokens": 300
            },
            IntentType.COMPANY_INFO: {
                "system_prompt": """Bạn là đại diện công ty. Nhiệm vụ của bạn là:
1. Giới thiệu về công ty một cách tích cực
2. Cung cấp thông tin về lịch sử và giá trị
3. Nêu bật những thành tựu và dịch vụ
4. Tạo ấn tượng tốt về thương hiệu

Trả lời bằng tiếng Việt, giọng điệu tự hào và chuyên nghiệp.""",
                "max_tokens": 350
            },
            IntentType.GENERAL_CHAT: {
                "system_prompt": """Bạn là trợ lý AI thân thiện. Nhiệm vụ của bạn là:
1. Trò chuyện một cách tự nhiên và lịch sự
2. Hướng dẫn khách hàng đến đúng chức năng
3. Giữ cuộc trò chuyện tích cực
4. Đề xuất cách thức hỗ trợ cụ thể

Trả lời bằng tiếng Việt, giọng điệu thân thiện và hữu ích.""",
                "max_tokens": 250
            }
        }
    
    def set_llm_provider(self, llm_provider):
        """Set LLM provider dependency"""
        self.llm_provider = llm_provider
    
    def set_faiss_manager(self, faiss_manager):
        """Set FAISS manager dependency"""
        self.faiss_manager = faiss_manager
    
    async def generate_response(
        self,
        user_query: str,
        intent: IntentResult,
        context: PageContext,
        relevant_docs: List[Dict[str, Any]],
        history: List[ChatMessage] = None
    ) -> Dict[str, Any]:
        """Generate contextual response using RAG"""
        
        # Get template for intent
        template = self.response_templates.get(
            intent.intent, 
            self.response_templates[IntentType.GENERAL_CHAT]
        )
        
        # Build context from documents
        document_context = self._build_document_context(relevant_docs)
        
        # Build conversation history
        conversation_context = self._build_conversation_context(history)
        
        # Build page context
        page_context = self._build_page_context(context, intent.target_product)
        
        # Create system prompt
        system_prompt = self._create_system_prompt(
            template["system_prompt"],
            document_context,
            page_context,
            conversation_context
        )
        
        # Create user prompt
        user_prompt = self._create_user_prompt(user_query, intent)
        
        # Generate response using LLM
        try:
            response_content = await self.llm_provider.call_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
        except Exception as e:
            print(f"LLM call failed: {e}")
            response_content = self._get_fallback_response(intent.intent, intent.target_product)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(relevant_docs, intent.confidence)
        
        # Prepare sources
        sources = self._prepare_sources(relevant_docs)
        
        return {
            "content": response_content,
            "confidence": confidence,
            "sources": sources
        }
    
    def _build_document_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Build context from relevant documents"""
        if not relevant_docs:
            return "Không có tài liệu liên quan được tìm thấy."
        
        context_parts = ["=== THÔNG TIN TÀI LIỆU ==="]
        
        # Group by collection for better organization
        collections = {}
        for doc in relevant_docs[:6]:  # Limit to top 6 docs
            collection = doc.get('collection', 'unknown')
            if collection not in collections:
                collections[collection] = []
            collections[collection].append(doc)
        
        for collection, docs in collections.items():
            context_parts.append(f"\n--- {collection.replace('_', ' ').title()} ---")
            for i, doc in enumerate(docs[:3], 1):  # Max 3 docs per collection
                content = doc['content'][:500]  # Limit content length
                context_parts.append(f"{i}. {content}...")
        
        return "\n".join(context_parts)
    
    def _build_conversation_context(self, history: Optional[List[ChatMessage]]) -> str:
        """Build conversation history context"""
        if not history or len(history) == 0:
            return ""
        
        context_parts = ["=== LỊCH SỬ HỘI THOẠI ==="]
        
        # Get last 3 exchanges
        recent_history = history[-6:] if len(history) > 6 else history
        
        for msg in recent_history:
            role = "Khách hàng" if msg.sender == "user" else "Trợ lý"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _build_page_context(self, context: PageContext, target_product: Optional[str]) -> str:
        """Build page context information"""
        context_parts = ["=== NGỮ CẢNH TRANG WEB ==="]
        
        context_parts.append(f"URL hiện tại: {context.url}")
        context_parts.append(f"Tiêu đề trang: {context.title}")
        
        if context.product:
            context_parts.append(f"Sản phẩm: {context.product}")
        elif target_product:
            context_parts.append(f"Sản phẩm được nhắc đến: {target_product}")
        
        if context.section:
            context_parts.append(f"Phần trang: {context.section}")
        
        if context.content_preview:
            preview = context.content_preview[:200]
            context_parts.append(f"Nội dung trang: {preview}...")
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(
        self,
        base_prompt: str,
        document_context: str,
        page_context: str,
        conversation_context: str
    ) -> str:
        """Create comprehensive system prompt"""
        
        prompt_parts = [base_prompt]
        
        if document_context:
            prompt_parts.append(f"\n{document_context}")
        
        if page_context:
            prompt_parts.append(f"\n{page_context}")
        
        if conversation_context:
            prompt_parts.append(f"\n{conversation_context}")
        
        prompt_parts.append("""
=== HƯỚNG DẪN TRẢ LỜI ===
1. Sử dụng thông tin từ tài liệu để trả lời chính xác
2. Tham khảo ngữ cảnh trang web và hội thoại
3. Trả lời ngắn gọn, rõ ràng (2-4 câu)
4. Nếu không chắc chắn, hãy thành thật nói cần thêm thông tin
5. Luôn giữ giọng điệu chuyên nghiệp và thân thiện
""")
        
        return "\n".join(prompt_parts)
    
    def _create_user_prompt(self, user_query: str, intent: IntentResult) -> str:
        """Create user prompt with intent context"""
        
        prompt_parts = [f'Câu hỏi của khách hàng: "{user_query}"']
        
        if intent.entities:
            entities_str = ", ".join([f"{k}: {v}" for k, v in intent.entities.items()])
            prompt_parts.append(f"Thông tin được nhận diện: {entities_str}")
        
        if intent.target_product:
            prompt_parts.append(f"Sản phẩm liên quan: {intent.target_product}")
        
        prompt_parts.append("Vui lòng trả lời câu hỏi dựa trên thông tin đã cung cấp.")
        
        return "\n".join(prompt_parts)
    
    def _calculate_confidence(self, relevant_docs: List[Dict], intent_confidence: float) -> float:
        """Calculate overall confidence score"""
        if not relevant_docs:
            return max(0.1, intent_confidence * 0.3)
        
        # Average document scores
        doc_scores = [doc.get('score', 0.0) for doc in relevant_docs[:3]]
        avg_doc_score = sum(doc_scores) / len(doc_scores) if doc_scores else 0.0
        
        # Combine intent confidence and document relevance
        combined_confidence = (intent_confidence * 0.4) + (avg_doc_score * 0.6)
        
        # Boost confidence if we have multiple relevant documents
        if len(relevant_docs) >= 3:
            combined_confidence *= 1.1
        
        return min(1.0, max(0.1, combined_confidence))
    
    def _prepare_sources(self, relevant_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare source references for response"""
        sources = []
        
        for doc in relevant_docs[:5]:  # Limit to top 5 sources
            source = {
                "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                "collection": doc['collection'].replace('_', ' ').title(),
                "score": round(doc.get('score', 0.0), 3),
                "metadata": doc.get('metadata', {})
            }
            sources.append(source)
        
        return sources
    
    def _get_fallback_response(self, intent: IntentType, target_product: Optional[str]) -> str:
        """Get fallback response when LLM fails"""
        
        fallback_responses = {
            IntentType.PRODUCT_INQUIRY: f"Tôi hiểu bạn muốn tìm hiểu về {target_product if target_product else 'sản phẩm'}. Vui lòng liên hệ team support để được tư vấn chi tiết hơn.",
            
            IntentType.PRICING_INQUIRY: "Để biết thông tin giá cả chính xác nhất, vui lòng liên hệ trực tiếp với team sales qua hotline hoặc email.",
            
            IntentType.SUPPORT_REQUEST: "Tôi sẽ chuyển yêu cầu hỗ trợ của bạn đến team kỹ thuật. Vui lòng cung cấp thêm chi tiết về vấn đề bạn gặp phải.",
            
            IntentType.WARRANTY_INQUIRY: "Để biết chi tiết về chính sách bảo hành, vui lòng tham khảo tài liệu bảo hành hoặc liên hệ customer service.",
            
            IntentType.CONTACT_REQUEST: "Bạn có thể liên hệ với chúng tôi qua email: support@yourdomain.com hoặc hotline trong giờ hành chính.",
            
            IntentType.COMPANY_INFO: "Cảm ơn bạn quan tâm đến công ty chúng tôi. Vui lòng truy cập trang About Us để biết thêm chi tiết.",
            
            IntentType.GENERAL_CHAT: "Xin chào! Tôi có thể giúp bạn tìm hiểu về sản phẩm, giá cả, hỗ trợ kỹ thuật. Bạn cần hỗ trợ gì?"
        }
        
        return fallback_responses.get(intent, "Xin lỗi, tôi cần thêm thông tin để có thể hỗ trợ bạn tốt hơn. Vui lòng liên hệ support@yourdomain.com.")