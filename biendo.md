Biểu đồ luồng công việc với các "vòng lặp" (feedback loops) để xử lý khi có lỗi. Quy trình làm việc sẽ linh hoạt, lường trước rủi ro và tập trung vào chất lượng.


### **Biểu đồ Luồng công việc & Xử lý Rủi ro**

Biểu đồ dưới đây mô tả luồng công việc chi tiết của dự án, bao gồm các "chốt chặn chất lượng" (Quality Gates) và các vòng lặp xử lý khi một công đoạn không đạt yêu cầu.

```mermaid
graph TD
    subgraph Giai_Đoạn_1_Nền_Tảng_Thiết_Kế
        A1[1.1 Lựa chọn Embedding Model] --> A2{1.2 Test Model OK?}
        A2 -- Yes --> B1
        A2 -- No --> A1
        
        B1[1.3 Thiết Kế CSDL] --> B2[1.4 Xây đựng hệ quản trị CSDL]
    end

    subgraph Giai_Đoạn_2_Phát_triển_Tool_và_Dữ_Liệu
        C1[2.1 Xây dựng Tool RawToClean] --> C2[2.2 Phòng ban chuẩn bị dữ liệu]
        C2 --> D1[2.3 Xây dựng Tool đánh giá]
        D1 --> D2{2.4 Dữ liệu đạt yêu cầu?}
        D2 -- No --> C2
        D2 -- Yes --> E1[2.5 Module nạp dữ liệu vào CSDL]
    end

    subgraph Giai_Đoạn_3_Xây_Dựng_Tối_Ưu_CoreRAG
        F1[3.1 Xây dựng core RAG v1] --> F2[3.2 Test core RAG trên máy chủ chatbotAI]
        F2 --> F3{3.3 Kết quả Test OK?}
        F3 -- No --> G1{Xác định nguyên nhân}
        F3 -- Yes --> H1
        G1 -- Truy xuất kém, sai ngữ cảnh --> A1
        G1 -- "Câu trả lời bịa, không bám ngữ cảnh" --> F1
        G1 -- Lỗi phân quyền CSDL --> B1
    end

    subgraph Giai_Đoạn_4_Tích_Hợp_Vận_Hành
        H1[4.1 Xây dựng và tích hợp UI] --> H2[4.2 Thử nghiệm người dùng cuối]
        H2 --> H3{4.3 Người dùng chấp nhận?}
        H3 -- No --> H4{Xác định vấn đề}
        H3 -- Yes --> I1[✅ Vận hành chính thức]
        H4 -- Lỗi giao diện, trải nghiệm --> H1
        H4 -- Lỗi Logic/độ chính xác --> F2
    end
    
    B2 --> C1
    E1 --> F1


```

#### **Diễn giải Biểu đồ và các Vòng lặp Xử lý:**

Biểu đồ này thể hiện một quy trình kiểm soát chất lượng liên tục. Nếu một bước thất bại, thay vì đi tiếp, luồng công việc sẽ quay lại bước phù hợp để khắc phục.

1.  **Vòng lặp tại Giai đoạn 1 (Lựa chọn Model):**

      * **Nếu `[A2] Test Model OK?` trả về "No"**: Điều này có nghĩa là các embedding model được chọn không hiệu quả với dữ liệu đặc thù của công ty.
      * **Hành động:** Quay lại bước `[A1]`, chúng ta phải tìm kiếm, thử nghiệm các model khác hoặc xem xét phương án tinh chỉnh (fine-tuning) model. Đây là vòng lặp nền tảng để đảm bảo "trái tim" của việc tìm kiếm hoạt động tốt.

2.  **Vòng lặp tại Giai đoạn 2 (Chuẩn bị Dữ liệu):**

      * **Nếu `[D2] Dữ liệu đạt chuẩn?` trả về "No"**: Đây là vòng lặp phổ biến nhất. Tool đánh giá phát hiện dữ liệu do phòng ban cung cấp bị trùng lặp, mâu thuẫn hoặc sai định dạng.
      * **Hành động:** Hệ thống sẽ gửi trả lại tài liệu lỗi cho `[C2] Phòng ban`, yêu cầu họ sử dụng `[C1] Tool Raw-->Clean` để chỉnh sửa lại. Vòng lặp này đảm bảo chỉ "dữ liệu vàng" mới được đưa vào hệ thống.

3.  **Vòng lặp tại Giai đoạn 3 (Tối ưu Lõi AI):**

      * **Đây là vòng lặp phức tạp và quan trọng nhất.** Nếu `[F3] Kết quả Test Lõi RAG OK?` trả về "No", chúng ta phải xác định rõ nguyên nhân gốc rễ:
          * **Nếu "Truy xuất kém/Sai ngữ cảnh"**: Vấn đề nằm ở khả năng "tìm" của hệ thống.
              * **Hành động:** Quay lại tận bước `[A1] Lựa chọn Embedding Model`. Đây là một thay đổi lớn, cho thấy model ban đầu không phù hợp như chúng ta nghĩ.
          * **Nếu "Câu trả lời 'bịa', không bám ngữ cảnh"**: Vấn đề nằm ở khả năng "tổng hợp" của LLM.
              * **Hành động:** Quay lại bước `[F1] Xây dựng Lõi RAG` để tinh chỉnh lại Prompt Engineering (cách chúng ta "ra lệnh" cho LLM).
          * **Nếu "Lỗi phân quyền/Tốc độ CSDL"**: Vấn đề nằm ở nền tảng dữ liệu.
              * **Hành động:** Quay lại bước `[B1] Thiết kế CSDL` để tối ưu lại cấu trúc, chỉ mục (index) và API truy vấn.

4.  **Vòng lặp tại Giai đoạn 4 (Phản hồi từ Người dùng):**

      * **Nếu `[H3] Người dùng chấp nhận?` trả về "No"**: Đây là vòng lặp cuối cùng dựa trên phản hồi thực tế.
      * **Hành động:**
          * Nếu vấn đề là **"Lỗi Giao diện/Trải nghiệm"**: Quay lại `[H1]` để đội frontend chỉnh sửa UI.
          * Nếu vấn đề là **"Lỗi Logic/Độ chính xác"**: Vấn đề nghiêm trọng hơn, cần quay lại `[F2]` để thực hiện lại quy trình test và tối ưu Lõi RAG.

