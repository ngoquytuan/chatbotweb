#engines/response_generator.py
"""
Contextual Response Generator - Generates responses using RAG with multiple LLM providers
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from models.schemas import PageContext, ChatMessage, SourceReference

logger = logging.getLogger(__name__)

@dataclass
class ResponseContext:
   user_query: str
   intent: Any  # IntentResult from intent_classifier
   page_context: PageContext
   relevant_docs: List[Dict]
   conversation_history: List[ChatMessage]

class ContextualResponseGenerator:
   def __init__(self):
       self.llm_provider = None
       self.faiss_manager = None
       
       # Response templates for different intents
       self.response_templates = {
           'product_inquiry': {
               'system_prompt': """Bạn là một chuyên gia tư vấn sản phẩm thông minh. Nhiệm vụ của bạn là:
1. Trả lời câu hỏi về tính năng và đặc điểm sản phẩm một cách chính xác
2. Sử dụng thông tin từ tài liệu được cung cấp làm nguồn chính
3. Trả lời bằng tiếng Việt tự nhiên, thân thiện
4. Nếu không có thông tin đủ, hãy thừa nhận và đề xuất liên hệ hỗ trợ
5. Luôn trích dẫn nguồn thông tin khi có thể""",
               'fallback': "Tôi cần thêm thông tin để trả lời chính xác về tính năng sản phẩm này. Vui lòng liên hệ team hỗ trợ để được tư vấn chi tiết."
           },
           'pricing_inquiry': {
               'system_prompt': """Bạn là chuyên gia tư vấn giá cả và gói dịch vụ. Hãy:
1. Cung cấp thông tin giá cả chính xác từ tài liệu
2. Giải thích các gói dịch vụ một cách rõ ràng
3. So sánh các gói nếu được hỏi
4. Đề xuất gói phù hợp dựa trên nhu cầu
5. Hướng dẫn quy trình thanh toán nếu cần""",
               'fallback': "Để có thông tin giá cả chính xác và cập nhật nhất, vui lòng liên hệ team sales qua hotline hoặc email."
           },
           'support_request': {
               'system_prompt': """Bạn là chuyên viên hỗ trợ kỹ thuật chuyên nghiệp. Hãy:
1. Cung cấp hướng dẫn rõ ràng, từng bước
2. Ưu tiên giải pháp đơn giản trước
3. Yêu cầu thông tin cần thiết để chẩn đoán
4. Đề xuất escalate nếu vấn đề phức tạp
5. Luôn kiên nhẫn và hữu ích""",
               'fallback': "Vấn đề này cần được xem xét kỹ hơn. Vui lòng tạo ticket hỗ trợ hoặc liên hệ hotline để được hỗ trợ trực tiếp."
           },
           'warranty_inquiry': {
               'system_prompt': """Bạn là chuyên viên tư vấn chính sách bảo hành. Hãy:
1. Giải thích chính sách bảo hành một cách rõ ràng
2. Hướng dẫn quy trình bảo hành/hoàn tiền
3. Nêu rõ điều kiện và thời hạn
4. Hỗ trợ xử lý khiếu nại nếu có
5. Luôn thấu hiểu và hỗ trợ khách hàng""",
               'fallback': "Để xử lý chính xác vấn đề bảo hành của bạn, vui lòng liên hệ bộ phận chăm sóc khách hàng với thông tin chi tiết sản phẩm."
           },
           'contact_request': {
               'system_prompt': """Bạn là chuyên viên hỗ trợ khách hàng. Hãy:
1. Cung cấp thông tin liên hệ chính xác
2. Hướng dẫn kênh liên hệ phù hợp cho từng vấn đề
3. Cung cấp giờ làm việc và thời gian phản hồi
4. Đề xuất kênh liên hệ nhanh nhất
5. Luôn nhiệt tình và hỗ trợ""",
               'fallback': "Bạn có thể liên hệ chúng tôi qua email support@yourdomain.com hoặc hotline trong giờ hành chính."
           },
           'company_info': {
               'system_prompt': """Bạn là người đại diện chính thức của công ty. Hãy:
1. Chia sẻ thông tin công ty một cách tự hào
2. Nêu bật các giá trị và thành tựu chính
3. Thể hiện tầm nhìn và sứ mệnh
4. Kết nối với khách hàng một cách chân thành
5. Luôn chuyên nghiệp và thân thiện""",
               'fallback': "Chúng tôi là công ty công nghệ chuyên cung cấp giải pháp chất lượng cao. Bạn có thể tìm hiểu thêm tại website chính thức."
           },
           'general_chat': {
               'system_prompt': """Bạn là trợ lý AI thân thiện của công ty. Hãy:
1. Trả lời một cách tự nhiên và thân thiện
2. Hướng dẫn khách hàng đến đúng thông tin cần thiết
3. Duy trì cuộc trò chuyện tích cực
4. Đề xuất cách chúng tôi có thể hỗ trợ
5. Luôn lịch sự và hữu ích""",
               'fallback': "Xin chào! Tôi là trợ lý AI của công ty. Tôi có thể giúp bạn tìm hiểu về sản phẩm, dịch vụ, hoặc kết nối với team hỗ trợ. Bạn cần hỗ trợ gì?"
           }
       }
   
   def set_llm_provider(self, llm_provider):
       """Inject LLM provider dependency"""
       self.llm_provider = llm_provider
   
   def set_faiss_manager(self, faiss_manager):
       """Inject FAISS manager dependency"""
       self.faiss_manager = faiss_manager
   
   async def generate_response(
       self,
       user_query: str,
       intent: Any,
       context: PageContext,
       relevant_docs: List[Dict],
       history: List[ChatMessage] = None
   ) -> Dict[str, Any]:
       """Generate contextual response using RAG pipeline"""
       
       response_context = ResponseContext(
           user_query=user_query,
           intent=intent,
           page_context=context,
           relevant_docs=relevant_docs,
           conversation_history=history or []
       )
       
       # Build context for LLM
       context_prompt = self._build_context_prompt(response_context)
       
       # Get response template
       template = self.response_templates.get(
           intent.intent.value, 
           self.response_templates['general_chat']
       )
       
       # Generate response
       try:
           response_content = await self._generate_llm_response(
               template['system_prompt'],
               context_prompt,
               user_query
           )
           
           # Extract sources
           sources = self._extract_sources(relevant_docs)
           
           # Calculate confidence
           confidence = self._calculate_confidence(intent, relevant_docs, response_content)
           
           return {
               'content': response_content,
               'sources': sources,
               'confidence': confidence,
               'intent': intent.intent.value,
               'reasoning': intent.reasoning
           }
           
       except Exception as e:
           logger.error(f"Response generation failed: {e}")
           # Return fallback response
           return {
               'content': template['fallback'],
               'sources': [],
               'confidence': 0.1,
               'intent': intent.intent.value,
               'reasoning': f"Fallback due to error: {str(e)}"
           }
   
   def _build_context_prompt(self, ctx: ResponseContext) -> str:
       """Build comprehensive context prompt for LLM"""
       
       prompt_parts = []
       
       # Page context
       prompt_parts.append("=== NGỮ CẢNH TRANG WEB ===")
       prompt_parts.append(f"URL: {ctx.page_context.url}")
       prompt_parts.append(f"Tiêu đề: {ctx.page_context.title}")
       if ctx.page_context.product:
           prompt_parts.append(f"Sản phẩm: {ctx.page_context.product}")
       if ctx.page_context.section:
           prompt_parts.append(f"Phần: {ctx.page_context.section}")
       
       # Intent analysis
       prompt_parts.append("\n=== PHÂN TÍCH Ý ĐỊNH ===")
       prompt_parts.append(f"Loại câu hỏi: {ctx.intent.intent.value}")
       prompt_parts.append(f"Sản phẩm mục tiêu: {ctx.intent.target_product or 'Không xác định'}")
       prompt_parts.append(f"Độ tin cậy: {ctx.intent.confidence:.2f}")
       if ctx.intent.entities:
           entities_str = ", ".join([f"{k}: {v}" for k, v in ctx.intent.entities.items()])
           prompt_parts.append(f"Thực thể: {entities_str}")
       
       # Relevant documents
       if ctx.relevant_docs:
           prompt_parts.append("\n=== TÀI LIỆU LIÊN QUAN ===")
           for i, doc in enumerate(ctx.relevant_docs[:5], 1):  # Top 5 docs
               prompt_parts.append(f"\nTài liệu {i} (Điểm: {doc['score']:.3f}):")
               prompt_parts.append(f"Bộ sưu tập: {doc['collection']}")
               prompt_parts.append(f"Nội dung: {doc['content'][:300]}...")
               
               if 'metadata' in doc and doc['metadata']:
                   metadata_str = ", ".join([f"{k}: {v}" for k, v in doc['metadata'].items() if v])
                   prompt_parts.append(f"Metadata: {metadata_str}")
       else:
           prompt_parts.append("\n=== TÀI LIỆU LIÊN QUAN ===")
           prompt_parts.append("Không tìm thấy tài liệu liên quan trực tiếp.")
       
       # Conversation history
       if ctx.conversation_history:
           prompt_parts.append("\n=== LỊCH SỬ HỘI THOẠI ===")
           recent_history = ctx.conversation_history[-3:]  # Last 3 messages
           for msg in recent_history:
               role = "Khách hàng" if msg.sender == "user" else "Trợ lý"
               prompt_parts.append(f"{role}: {msg.content}")
       
       # User query
       prompt_parts.append(f"\n=== CÂU HỎI HIỆN TẠI ===")
       prompt_parts.append(f"Khách hàng hỏi: {ctx.user_query}")
       
       return "\n".join(prompt_parts)
   
   async def _generate_llm_response(
       self,
       system_prompt: str,
       context_prompt: str,
       user_query: str
   ) -> str:
       """Generate response using LLM"""
       
       messages = [
           {
               "role": "system",
               "content": system_prompt
           },
           {
               "role": "user",
               "content": f"{context_prompt}\n\nDựa vào ngữ cảnh trên, hãy trả lời câu hỏi của khách hàng một cách chính xác, hữu ích và thân thiện. Nếu thông tin không đủ để trả lời chính xác, hãy thừa nhận và đề xuất cách thức hỗ trợ khác."
           }
       ]
       
       response = await self.llm_provider.call_llm(messages)
       
       # Post-process response
       response = self._post_process_response(response, user_query)
       
       return response
   
   def _post_process_response(self, response: str, user_query: str) -> str:
       """Post-process LLM response for quality and safety"""
       
       # Remove potential hallucinations
       response = response.strip()
       
       # Ensure Vietnamese politeness
       if not any(greeting in response.lower() for greeting in ['xin chào', 'cảm ơn', 'vui lòng']):
           # Add polite elements if missing
           if not response.startswith(('Xin chào', 'Cảm ơn')):
               response = f"Cảm ơn bạn đã liên hệ. {response}"
       
       # Ensure helpful ending
       helpful_endings = [
           'cần hỗ trợ', 'liên hệ', 'giúp đỡ', 'thắc mắc', 
           'hỗ trợ thêm', 'tư vấn', 'support'
       ]
       
       if not any(ending in response.lower() for ending in helpful_endings):
           response += "\n\nNếu bạn có thắc mắc thêm, vui lòng cho tôi biết!"
       
       # Length check
       if len(response) < 50:
           response += " Tôi luôn sẵn sàng hỗ trợ bạn với thông tin chi tiết hơn."
       elif len(response) > 1000:
           # Truncate if too long
           response = response[:900] + "... Bạn có muốn tôi giải thích chi tiết thêm phần nào không?"
       
       return response
   
   def _extract_sources(self, relevant_docs: List[Dict]) -> List[SourceReference]:
       """Extract source references from relevant documents"""
       
       sources = []
       seen_content = set()
       
       for doc in relevant_docs[:3]:  # Top 3 sources
           # Avoid duplicate content
           content_hash = hash(doc['content'][:100])
           if content_hash in seen_content:
               continue
           seen_content.add(content_hash)
           
           source = SourceReference(
               content=doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
               collection=doc['collection'],
               score=float(doc['score']),
               metadata=doc.get('metadata', {})
           )
           sources.append(source)
       
       return sources
   
   def _calculate_confidence(
       self,
       intent: Any,
       relevant_docs: List[Dict],
       response_content: str
   ) -> float:
       """Calculate response confidence score"""
       
       confidence_factors = []
       
       # Intent confidence
       confidence_factors.append(intent.confidence * 0.3)
       
       # Document relevance
       if relevant_docs:
           avg_score = sum(doc['score'] for doc in relevant_docs) / len(relevant_docs)
           doc_confidence = min(avg_score / 0.8, 1.0)  # Normalize to max 0.8 score
           confidence_factors.append(doc_confidence * 0.4)
       else:
           confidence_factors.append(0.1)  # Low confidence without docs
       
       # Response quality (simple heuristics)
       response_quality = 0.5  # Baseline
       
       # Check for specific indicators
       if len(response_content) > 100:  # Substantial response
           response_quality += 0.2
       
       if any(indicator in response_content.lower() for indicator in [
           'cụ thể', 'chi tiết', 'chính xác', 'theo tài liệu'
       ]):
           response_quality += 0.2
       
       if 'xin lỗi' in response_content.lower() or 'không biết' in response_content.lower():
           response_quality -= 0.2
       
       confidence_factors.append(min(response_quality, 1.0) * 0.3)
       
       # Calculate final confidence
       final_confidence = sum(confidence_factors)
       return max(0.0, min(1.0, final_confidence))
   
   async def generate_followup_suggestions(
       self,
       context: ResponseContext,
       generated_response: str
   ) -> List[str]:
       """Generate follow-up question suggestions"""
       
       suggestions = []
       intent_value = context.intent.intent.value
       
       # Intent-specific suggestions
       if intent_value == 'product_inquiry':
           suggestions.extend([
               "Giá cả của sản phẩm này như thế nào?",
               "Tôi có thể dùng thử sản phẩm không?",
               "Sản phẩm có bảo hành không?"
           ])
       
       elif intent_value == 'pricing_inquiry':
           suggestions.extend([
               "Có khuyến mãi nào hiện tại không?",
               "Tôi có thể thanh toán theo tháng không?",
               "Gói nào phù hợp với doanh nghiệp nhỏ?"
           ])
       
       elif intent_value == 'support_request':
           suggestions.extend([
               "Có tài liệu hướng dẫn chi tiết không?",
               "Tôi có thể liên hệ hỗ trợ trực tiếp không?",
               "Vấn đề này thường mất bao lâu để giải quyết?"
           ])
       
       # Generic helpful suggestions
       suggestions.extend([
           "Tôi có thể liên hệ ai để được tư vấn thêm?",
           "Có thông tin nào khác tôi cần biết không?"
       ])
       
       # Return top 3 suggestions
       return suggestions[:3]