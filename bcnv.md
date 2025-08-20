Chắc chắn rồi. Dưới đây là tài liệu hoàn chỉnh, kết hợp báo cáo chiến lược đã soạn thảo trước đó với các yêu cầu nhiệm vụ chi tiết bạn vừa cung cấp, tạo thành một bộ hồ sơ Thuyết minh Nhiệm vụ Khoa học và Công nghệ (KH\&CN) hoàn chỉnh và chuyên nghiệp.

-----

**THUYẾT MINH NHIỆM VỤ KHOA HỌC VÀ CÔNG NGHỆ CẤP CÔNG TY NĂM 2026**

### **ĐỀ TÀI: Nghiên cứu, thiết kế, chế tạo chatbot sử dụng mô hình ngôn ngữ lớn LLM xử lý tài liệu nội bộ của Công ty.**

-----

#### **PHẦN I: TỔNG QUAN VỀ NHIỆM VỤ KH\&CN**

**1.1. Tên nhiệm vụ KH\&CN**

Nghiên cứu, thiết kế, chế tạo chatbot sử dụng mô hình ngôn ngữ lớn LLM xử lý tài liệu nội bộ của Công ty.

**1.2. Tiêu chuẩn**

Đảm bảo phát triển phần mềm an toàn và tin cậy, đảm bảo bảo mật và quyền riêng tư.

**1.3. Mục tiêu của nhiệm vụ**

Mục tiêu của nhiệm vụ là cung cấp một giải pháp xử lý tài liệu nội bộ của Công ty ứng dụng mô hình ngôn ngữ lớn LLM để nâng cao hiệu quả, cải thiện khả năng tiếp cận kiến thức, ứng dụng các công nghệ tiên tiến trong lĩnh vực trí tuệ nhân tạo vào quản lý tri thức nội bộ của Công ty.

Mô hình LLM sẽ hoạt động hoàn toàn trong môi trường mạng nội bộ, đảm bảo tính riêng tư tuyệt đối của dữ liệu. Để kiểm tra và xác minh công nghệ, trong phạm vi nhiệm vụ này, chatbot sẽ được nghiên cứu và huấn luyện chuyên biệt với bộ dữ liệu liên quan đến các **quy trình Khoa học và Công nghệ** của Công ty.

-----

#### **PHẦN II: PHÂN TÍCH BỐI CẢNH VÀ SỰ CẦN THIẾT**

**2.1. Bối cảnh và Nhu cầu Nghiệp vụ**

Ngành kỹ thuật quản lý bay là một lĩnh vực đặc thù với yêu cầu cực kỳ cao về độ chính xác, an toàn và tuân thủ quy trình. Tri thức và dữ liệu—từ tài liệu kỹ thuật của nhà sản xuất, quy trình bay hiệu chuẩn, tiêu chuẩn ICAO, đến các quy định nội bộ—là tài sản cốt lõi nhưng đang phân tán. Việc truy xuất thông tin chậm trễ hoặc sai lệch có thể dẫn đến rủi ro trong vận hành.

Nhiệm vụ KH\&CN này ra đời nhằm giải quyết trực tiếp bài toán trên, cải thiện triệt để hiệu quả và độ chính xác trong việc truy xuất thông tin chuyên ngành, tự động hóa việc giải đáp các câu hỏi lặp đi lặp lại và giải phóng các chuyên gia khỏi các tác vụ hỗ trợ thông tin cơ bản.

**2.2. Lợi ích chiến lược**

  * **An toàn và Bảo mật Dữ liệu Tuyệt đối:** Hệ thống hoạt động trong một môi trường mạng LAN khép kín ("air-gapped"), loại bỏ hoàn toàn nguy cơ rò rỉ dữ liệu nhạy cảm của ngành hàng không ra bên ngoài.
  * **Câu trả lời Chính xác và Phù hợp Cao:** Cung cấp thông tin được cá nhân hóa bằng cách hiểu rõ vai trò của người dùng (ví dụ: câu trả lời cho kỹ sư bảo trì sẽ khác với chuyên viên tư vấn dự án).
  * **Kho tri thức có khả năng Mở rộng:** Kiến trúc được thiết kế để bắt đầu với một bộ tài liệu lõi và có thể mở rộng lên hàng nghìn tài liệu phức tạp mà không cần thay đổi cấu trúc.
  * **Dễ bảo trì và Sẵn sàng cho Tương lai:** Thiết kế module hóa cho phép dễ dàng cập nhật, bảo trì và tích hợp các công nghệ mới trong tương lai.

-----

#### **PHẦN III: GIẢI PHÁP CÔNG NGHỆ VÀ CÁC TÍNH NĂNG ĐỔI MỚI**

**3.1. Tổng quan giải pháp**

Dự án tập trung vào việc nghiên cứu và phát triển một hệ thống chatbot trợ lý nội bộ thông minh, an toàn, và được thiết kế để hoạt động hoàn toàn trong môi trường mạng LAN nội bộ của Công ty ATTECH. Hệ thống sẽ cung cấp cho đội ngũ cán bộ nhân viên, chuyên gia kỹ thuật những câu trả lời nhanh chóng, chính xác và phù hợp với ngữ cảnh, dựa trên kho tri thức chuyên ngành đã được kiểm duyệt.

**3.2. Các tính năng vượt trội và đổi mới**

1.  **Tạo sinh Tăng cường Truy xuất (RAG) Chống "Ảo giác":** Công nghệ RAG đảm bảo chatbot **chỉ trả lời dựa trên thông tin có trong kho tài liệu của ATTECH**. Điều này loại bỏ hoàn toàn rủi ro chatbot "sáng tạo" ra thông tin sai lệch (hallucination) – một yếu tố sống còn đối với ngành đòi hỏi độ chính xác tuyệt đối như quản lý bay.
2.  **Định tuyến Thông minh đến Kho tri thức Chuyên ngành:** Hệ thống tự động phân tích câu hỏi của người dùng và định tuyến đến đúng bộ sưu tập tri thức phù hợp.
3.  **Trợ lý Thông minh theo Ngữ cảnh:** Chatbot nhận biết được người dùng đang xem tài liệu hay dự án nào để đưa ra câu trả lời liên quan nhất, hoạt động như một trợ lý ảo thực thụ.
4.  **Tự chủ Công nghệ và Tối ưu Chi phí (Multi-LLM):** Khả năng chuyển đổi linh hoạt giữa các LLM (cả mã nguồn mở và thương mại) giúp ATTECH không bị phụ thuộc vào bất kỳ nhà cung cấp nào, đồng thời tối ưu được chi phí vận hành lâu dài.
5.  **Cá nhân hóa theo Vai trò và Phân quyền:** Tích hợp với hệ thống quản lý người dùng nội bộ để cung cấp thông tin phù hợp với vai trò và cấp bậc, đảm bảo tính bảo mật và liên quan của dữ liệu.

**3.3. Phạm vi Tri thức và Định hướng Mở rộng**

Trong khuôn khổ của Nhiệm vụ KH\&CN năm 2026, hệ thống sẽ được nghiên cứu và thử nghiệm với bộ dữ liệu chuyên biệt về các **quy trình Khoa học Công nghệ** theo đúng yêu cầu.

Sau khi nền tảng công nghệ đã được xác minh thành công, hệ thống có khả năng mở rộng để quản lý các bộ sưu tập tri thức chuyên ngành khác, bao gồm:

| Collection | Mô tả | Keywords chính |
| :--- | :--- | :--- |
| **flight\_services** | Dịch vụ dẫn đường hàng không, bay kiểm tra hiệu chuẩn | dẫn đường, navigation, calibration, flight check |
| **equipment\_tech** | Thiết bị thông tin, dẫn đường, giám sát hàng không | equipment, maintenance, installation, radar |
| **training\_services** | Đào tạo, huấn luyện nhân lực hàng không | training, certification, course, aviation |
| **consulting\_design** | Tư vấn, thiết kế, thi công công trình hàng không | consulting, design, construction, airport |
| **company\_info**| Lịch sử, tổ chức, liên hệ công ty | company, history, contact, organization |

-----

#### **PHẦN IV: YÊU CẦU KỸ THUẬT CHI TIẾT**

**4.1. Yêu cầu chung**

  * **Mục tiêu:** Xây dựng giải pháp chatbot tiếng Việt nội bộ có khả năng hiểu, truy vấn và trả lời câu hỏi dựa trên bộ tài liệu nội bộ của Công ty có dung lượng khoảng 200-500 trang A4, định dạng text. Mô hình LLM chạy trong máy tính nội bộ của Công ty.
  * **Phạm vi xử lý dữ liệu:**
      * **Định dạng:** Tài liệu đầu vào là các tệp .txt.
      * **Dung lượng:** Tương đương 200-500 trang A4. Tổng dung lượng bộ dữ liệu từ 200 MB đến 500 MB.
      * **Nội dung:** Các loại tài liệu nội bộ liên quan đến các hoạt động Khoa học Công nghệ của Công ty (quy trình, hướng dẫn, chính sách, báo cáo, v.v.).
  * **Yêu cầu về Hệ thống:**
      * Hoạt động nội bộ, đảm bảo tính riêng tư và bảo mật dữ liệu.
      * Triển khai trên hạ tầng máy tính cấu hình tiêu chuẩn.
      * Giao diện tương tác thân thiện, dễ sử dụng.

**4.2. Yêu cầu chức năng**

  * **Thu thập và Tiền xử lý Tài liệu:**
      * Chuẩn hoá tài liệu: Thu thập và chuẩn hoá tài liệu liên quan công tác Khoa học Công nghệ của Công ty để làm dữ liệu đầu vào.
  * **Xử lý Truy vấn Người dùng:**
      * **Đối tượng người dùng:** Nhóm người dùng hay phải làm việc với các nhiệm vụ khoa học công nghệ của Công ty.
      * **Nhận đầu vào:** Hệ thống phải nhận câu hỏi của người dùng bằng ngôn ngữ tự nhiên (tiếng Việt).
      * **Truy xuất Ngữ cảnh Liên quan:** Tìm kiếm trong cơ sở dữ liệu vector để xác định các đoạn tài liệu liên quan nhất đến truy vấn của người dùng.
      * **Tạo câu trả lời bằng LLM:** Sử dụng các đoạn tài liệu liên quan và câu hỏi của người dùng để tạo câu trả lời thông qua mô hình LLM nội bộ, tuân thủ quy tắc không suy diễn ngoài tài liệu.
      * **Tham chiếu nguồn:** Hệ thống chỉ ra các tài liệu/đoạn văn bản nào đã được sử dụng để tạo ra câu trả lời.
  * **Giao diện Người dùng (UI):**
      * **Nhập câu hỏi:** Cung cấp một ô nhập liệu để người dùng gõ câu hỏi.
      * **Hiển thị câu trả lời:** Hiển thị rõ ràng câu trả lời từ chatbot.
      * **Lịch sử hội thoại:** Lưu trữ và hiển thị lịch sử các câu hỏi và câu trả lời trước đó trong phiên làm việc.
      * **Tương thích trình duyệt:** Giao diện web có thể truy cập bằng các trình duyệt phổ biến (Chrome, Firefox, Edge).

**4.3. Yêu cầu phi chức năng**

  * **Hiệu năng:**
      * **Thời gian xử lý truy vấn:** Dưới **30 giây** cho các truy vấn thông thường.
      * **Khả năng xử lý tài liệu:** Hệ thống phải có khả năng xử lý hiệu quả việc thêm, bớt dữ liệu.
      * **Khả năng chịu tải:** Phục vụ đồng thời ít nhất **5 người dùng** mà không làm giảm hiệu năng đáng kể.
  * **Độ chính xác:**
      * **Độ chính xác truy xuất:** Tỷ lệ các đoạn tài liệu liên quan được truy xuất cho các truy vấn mẫu phải đạt tối thiểu **85%**.
      * **Độ chính xác câu trả lời:** Tỷ lệ câu trả lời đúng và có liên quan đến ngữ cảnh được cung cấp phải đạt tối thiểu **80%**. Hạn chế tối đa hiện tượng “ảo giác”.
  * **Bảo mật và quyền riêng tư:**
      * **Triển khai nội bộ:** Toàn bộ hệ thống phải được triển khai và vận hành trên hạ tầng mạng nội bộ của Công ty.
      * **Kiểm soát truy cập:** Có cơ chế xác thực người dùng để đảm bảo chỉ người dùng được ủy quyền mới có thể truy cập hệ thống.
      * **Bảo vệ dữ liệu:** Đảm bảo dữ liệu tài liệu nội bộ không bị lộ ra bên ngoài hệ thống.
  * **Khả năng sử dụng:**
      * Giao diện đơn giản, trực quan, dễ hiểu đối với người dùng không chuyên về kỹ thuật.
      * Thông báo lỗi rõ ràng, dễ hiểu.
  * **Khả năng bảo trì và mở rộng:**
      * Mã nguồn được tổ chức tốt, có chú thích rõ ràng, dễ dàng sửa đổi và bảo trì.
      * Có khả năng mở rộng để xử lý lượng tài liệu lớn hơn hoặc tích hợp các mô hình LLM/embedding khác trong tương lai.

**4.4. Yêu cầu về phần cứng và tài liệu đi kèm**

  * **Hệ thống Máy tính:** 01 hệ thống máy tính với cấu hình tối thiểu như sau:
      * **CPU:** Intel Core i7 (thế hệ 10 trở lên) hoặc tương đương.
      * **RAM:** Tối thiểu 64 GB.
      * **Ổ cứng:** SSD dung lượng tối thiểu 512 GB và ổ cứng HDD 10TB để lưu trữ dữ liệu.
      * **GPU:** NVIDIA GeForce RTX 3060 24GB VRAM trở lên, hoặc tương đương.
  * **Yêu cầu về tài liệu đi kèm:**
      * Thuyết minh thiết kế chi tiết.
      * Hồ sơ bản vẽ thiết kế (sơ đồ kiến trúc, luồng dữ liệu).
      * Quy trình kiểm tra thử nghiệm và báo cáo kết quả.
      * Hướng dẫn cài đặt và vận hành hệ thống.
      * Hướng dẫn sử dụng sản phẩm.

-----

#### **PHẦN V: SẢN PHẨM VÀ KẾT QUẢ BÀN GIAO CỦA NHIỆM VỤ**

**5.1. Bộ hồ sơ thiết kế sản phẩm**

1.  **Thuyết minh thiết kế:** Thể hiện các yêu cầu thiết kế, yêu cầu đối với sản phẩm mẫu; phương pháp, thuật toán tính toán lựa chọn công nghệ và linh kiện, các giải pháp thiết kế.
2.  **Hồ sơ bản vẽ thiết kế:** Bao gồm bản vẽ thiết kế tổng thể hệ thống, sơ đồ nguyên lý, thiết kế triển khai lắp đặt sản phẩm mẫu.
3.  **Dự toán sản xuất:** Đảm bảo đầy đủ chi phí cho quá trình nghiên cứu, chế tạo sản phẩm mẫu, kiểm tra thử nghiệm.
4.  **Quy trình kiểm tra thử nghiệm:** Đưa ra các phương pháp, cách thức để kiểm tra, thử nghiệm đầy đủ các thông số kỹ thuật, tính năng của sản phẩm.
5.  **Qui trình sản xuất và hướng dẫn công nghệ chế tạo:** Thể hiện cách thức tổ chức sản xuất, các bước thực hiện và các lưu ý trong quá trình sản xuất.

**5.2. Sản phẩm mẫu nhiệm vụ**

| STT | Tên sản phẩm | Mô tả | Ghi chú |
| :-- | :--- | :--- | :--- |
| 1 | **Phần cứng** | 01 hệ thống máy tính (đáp ứng cấu hình yêu cầu) | |
| 2 | **Phần mềm** | 01 hệ thống phần mềm chatbot hoàn chỉnh. \<br\> 01 USB chứa file mềm bộ hồ sơ thiết kế và các phần mềm liên quan. | |

-----

#### **PHẦN VI: LỘ TRÌNH TRIỂN KHAI DỰ KIẾN**

  * **Giai đoạn 1 (Tuần 1-2): Hoạch định & Thiết lập** – Hoàn thiện các yêu cầu kỹ thuật, cơ chế xác thực và yêu cầu phần cứng. Thiết lập công cụ quản lý dự án và mã nguồn.
  * **Giai đoạn 2 (Tuần 3-6): Phát triển các Module Lõi** – Xây dựng và kiểm thử đơn vị các module riêng lẻ, tập trung vào quy trình nạp dữ liệu và lõi xử lý RAG.
  * **Giai đoạn 3 (Tuần 7-8): Tích hợp & Triển khai** – Tích hợp toàn bộ hệ thống, triển khai bằng Docker lên máy chủ nội bộ. Thực hiện kiểm thử end-to-end và triển khai chiến lược sao lưu.
  * **Giai đoạn 4 (Tuần 9-10): Vận hành Thử nghiệm & Cải tiến** – Mời các nhóm người dùng thí điểm, thu thập phản hồi qua giao diện, phân tích và thực hiện các cải tiến lặp lại.

-----

#### **PHẦN VII: KẾT LUẬN VÀ KIẾN NGHỊ**

Nhiệm vụ KH\&CN "Nghiên cứu, thiết kế, chế tạo chatbot sử dụng mô hình ngôn ngữ lớn LLM xử lý tài liệu nội bộ" là một bước đi chiến lược, phù hợp với định hướng chuyển đổi số và nâng cao năng lực công nghệ của Công ty. Dự án không chỉ giải quyết bài toán cấp thiết về quản lý tri thức mà còn đặt nền móng cho việc ứng dụng AI vào các hoạt động nghiệp vụ khác trong tương lai.

Với kế hoạch chi tiết, mục tiêu rõ ràng và giải pháp công nghệ tiên tiến, chúng tôi tin tưởng nhiệm vụ sẽ hoàn thành đúng tiến độ và đạt được các sản phẩm đề ra. Kính đề nghị Hội đồng Khoa học và Công nghệ xem xét, phê duyệt để nhiệm vụ được chính thức triển khai.

**Xin trân trọng cảm ơn.**
