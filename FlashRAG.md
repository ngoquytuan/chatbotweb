Vâng, bạn hoàn toàn có thể cài đặt **FlashRAG** trong một môi trường ảo của Python. Sử dụng môi trường ảo giúp cô lập các thư viện và tránh xung đột với các dự án khác. Dưới đây là hướng dẫn chi tiết để cài đặt **FlashRAG** trong môi trường ảo trên hệ điều hành Linux, macOS hoặc Windows.

### Hướng dẫn cài đặt FlashRAG trong môi trường ảo

#### 1. **Tạo và kích hoạt môi trường ảo**

Trước tiên, bạn cần tạo một môi trường ảo bằng `venv` (có sẵn trong Python) hoặc các công cụ như `virtualenv`.

##### Tạo môi trường ảo
```bash
# Di chuyển đến thư mục dự án của bạn (nếu cần)
cd /đường/dẫn/đến/thư/mục/dự/án

# Tạo môi trường ảo với tên 'flashrag_env'
python -m venv flashrag_env
```

##### Kích hoạt môi trường ảo
- **Trên Linux/macOS**:
  ```bash
  source flashrag_env/bin/activate
  ```
- **Trên Windows**:
  ```bash
  flashrag_env\Scripts\activate
  ```

Khi môi trường ảo được kích hoạt, bạn sẽ thấy tên môi trường (ví dụ: `(flashrag_env)`) xuất hiện trước dấu nhắc lệnh trong terminal.

#### 2. **Cài đặt FlashRAG**

FlashRAG yêu cầu Python 3.10 trở lên. Hãy đảm bảo bạn đang sử dụng phiên bản Python phù hợp trong môi trường ảo. Bạn có thể kiểm tra phiên bản Python bằng lệnh:
```bash
python --version
```

##### Cài đặt qua pip (khuyến nghị)
Bạn có thể cài đặt FlashRAG trực tiếp từ PyPI:
```bash
pip install flashrag-dev --pre
```

##### Hoặc cài đặt từ mã nguồn
Nếu bạn muốn cài đặt từ mã nguồn trên GitHub:
```bash
# Clone repository
git clone https://github.com/RUC-NLPIR/FlashRAG.git
cd FlashRAG

# Cài đặt FlashRAG trong môi trường ảo
pip install -e .
```

#### 3. **Cài đặt các thư viện bổ sung (tùy chọn)**

FlashRAG hỗ trợ một số thư viện tùy chọn để tăng tốc độ hoặc thêm tính năng. Bạn có thể cài đặt chúng nếu cần:

##### Cài đặt tất cả các phụ thuộc tùy chọn
```bash
pip install flashrag-dev[full]
```

##### Cài đặt từng phụ thuộc riêng lẻ
- **vLLM** (tăng tốc độ suy luận LLM):
  ```bash
  pip install vllm>=0.4.1
  ```
- **sentence-transformers** (hỗ trợ retriever):
  ```bash
  pip install sentence-transformers
  ```
- **Pyserini** (hỗ trợ BM25 retriever):
  ```bash
  pip install pyserini
  ```

#### 4. **Cài đặt Faiss**

Faiss (dùng cho dense retrieval) không thể cài đặt trực tiếp qua `pip` trên một số hệ thống, do đó bạn cần sử dụng `conda` để cài đặt. Nếu bạn chưa cài đặt Conda, bạn có thể tải Miniconda hoặc Anaconda từ trang chính thức.

##### Cài đặt Faiss trong môi trường ảo
- **CPU-only**:
  ```bash
  conda install -c pytorch faiss-cpu=1.8.0
  ```
- **GPU (+CPU)** (chỉ hỗ trợ trên Linux với CUDA 11.4 hoặc 12.1):
  ```bash
  conda install -c pytorch -c nvidia faiss-gpu=1.8.0
  ```

**Lưu ý**: 
- Faiss-cpu hỗ trợ Linux (x86_64, arm64), macOS (arm64), và Windows (x86_64).
- Faiss-gpu chỉ hỗ trợ Linux (x86_64) với CUDA 11.4 hoặc 12.1. Hãy kiểm tra hệ thống của bạn trước khi cài đặt.

Nếu bạn không có Conda trong môi trường ảo, bạn cần kích hoạt Conda trước:
```bash
# Kích hoạt Conda (nếu cần)
source /đường/dẫn/đến/conda/bin/activate
conda activate flashrag_env
```

#### 5. **Kiểm tra cài đặt**

Sau khi cài đặt, bạn có thể kiểm tra xem FlashRAG đã được cài đặt đúng cách bằng cách chạy:
```bash
python -c "import flashrag; print(flashrag.__version__)"
```

Nếu không có lỗi và phiên bản được in ra, bạn đã cài đặt thành công.

#### 6. **Chạy FlashRAG-UI (tùy chọn)**

Nếu bạn muốn sử dụng giao diện người dùng của FlashRAG:
```bash
cd webui
python interface.py
```

Giao diện sẽ chạy trên trình duyệt, cho phép bạn cấu hình và trải nghiệm các phương pháp RAG một cách trực quan.

#### 7. **Thoát môi trường ảo**

Khi hoàn tất, bạn có thể thoát môi trường ảo bằng lệnh:
```bash
deactivate
```

### Lưu ý quan trọng
- **Phiên bản Python**: FlashRAG yêu cầu Python 3.10 trở lên. Nếu môi trường ảo của bạn sử dụng phiên bản thấp hơn, hãy tạo lại môi trường ảo với Python 3.10+:
  ```bash
  python3.10 -m venv flashrag_env
  ```
- **Vấn đề cài đặt Faiss**: Nếu gặp lỗi khi cài đặt Faiss, hãy kiểm tra hệ điều hành và phiên bản CUDA (nếu dùng GPU). Bạn có thể thử cài đặt Faiss bằng `pip` nếu không cần Conda:
  ```bash
  pip install faiss-cpu
  ```
- **Tài nguyên hệ thống**: Một số thành phần (như vLLM hoặc Faiss-GPU) yêu cầu tài nguyên phần cứng đáng kể (RAM, GPU). Hãy đảm bảo máy của bạn đáp ứng yêu cầu.
- **Cập nhật**: FlashRAG vẫn đang được phát triển. Hãy theo dõi GitHub để cập nhật các phiên bản mới hoặc sửa lỗi.

### Xử lý lỗi thường gặp
- **Lỗi không tìm thấy module**: Đảm bảo bạn đã kích hoạt môi trường ảo trước khi chạy lệnh.
- **Lỗi cài đặt Faiss**: Nếu Conda không hoạt động, thử cài đặt Faiss qua pip hoặc kiểm tra xem hệ thống của bạn có tương thích với phiên bản Faiss được yêu cầu không.
- **Lỗi Pyserini**: Pyserini có thể khó cài đặt trên một số hệ thống. Bạn có thể sử dụng `bm25s` thay thế bằng cách đặt `bm25_backend=bm25s` trong cấu hình.

Nếu bạn gặp vấn đề cụ thể trong quá trình cài đặt, hãy cung cấp chi tiết lỗi để mình có thể hỗ trợ thêm!


**FlashRAG** là một bộ công cụ Python mạnh mẽ và toàn diện được thiết kế để hỗ trợ nghiên cứu về **Retrieval-Augmented Generation (RAG)**, và nó có nhiều điểm nổi bật khiến nó trở thành một tài nguyên giá trị cho các nhà nghiên cứu trong lĩnh vực này. Dưới đây là những điểm nổi bật của dự án **FlashRAG** dựa trên tài liệu bạn cung cấp:

### 1. **Khung công tác toàn diện và tùy chỉnh**
- **Cấu trúc linh hoạt**: FlashRAG cung cấp các thành phần cốt lõi cho RAG như **retriever** (mô hình lấy thông tin), **reranker** (sắp xếp lại kết quả), **generator** (mô hình sinh nội dung), và **compressor** (nén ngữ cảnh). Các thành phần này có thể được kết hợp linh hoạt để xây dựng các pipeline RAG phức tạp theo nhu cầu nghiên cứu.
- **Hỗ trợ đa dạng các thành phần**:
  - **Retriever**: Bao gồm cả **dense retriever** (như DPR, BGE, E5) sử dụng Faiss để tìm kiếm vector, và **sparse retriever** (như BM25) dựa trên Lucene.
  - **Reranker**: Hỗ trợ cả **bi-encoder** và **cross-encoder** để tính toán điểm phù hợp.
  - **Refiner**: Bao gồm các phương pháp tinh chỉnh ngữ cảnh như **Extractive Refiner**, **Abstractive Refiner**, **LLMLingua**, **Selective-Context**, và **KG Refiner** (dựa trên đồ thị tri thức).
  - **Generator**: Hỗ trợ các mô hình như **Encoder-Decoder**, **Decoder-only**, và tăng tốc với **FastChat** hoặc **vLLM**.
- **Khả năng tùy chỉnh cao**: Người dùng có thể dễ dàng tích hợp các thành phần mới hoặc xây dựng pipeline tùy chỉnh bằng cách kế thừa lớp `BasicPipeline`.

### 2. **Bộ dữ liệu benchmark phong phú**
- **36 bộ dữ liệu RAG**: FlashRAG cung cấp 36 bộ dữ liệu được xử lý sẵn, bao gồm các tác vụ như QA (Natural Questions, TriviaQA), multi-hop QA (HotpotQA, 2WikiMultiHopQA), long-form QA (ASQA, ELI5), fact verification (FEVER), và nhiều tác vụ khác. Các bộ dữ liệu này được chuẩn hóa ở định dạng `jsonl`, giúp dễ dàng sử dụng và tái hiện thí nghiệm.
- **Tập hợp tài liệu (corpus)**: Hỗ trợ các tập tài liệu phổ biến như Wikipedia và MS MARCO, kèm theo các tập hợp được xử lý sẵn (ví dụ: `wiki18_100w_e5_index` trên ModelScope). FlashRAG cũng cung cấp script để xử lý Wikipedia dump thành định dạng có thể lập chỉ mục.

### 3. **17 thuật toán RAG tiên tiến**
- **Hỗ trợ các phương pháp SOTA**: FlashRAG triển khai 17 thuật toán RAG tiên tiến, bao gồm cả các phương pháp tuần tự (Sequential), điều kiện (Conditional), phân nhánh (Branching), và lặp (Loop). Một số phương pháp đáng chú ý:
  - **Standard RAG**: Pipeline RAG cơ bản.
  - **Spring**: Tăng hiệu suất LLM bằng cách thêm một vài token embeddings.
  - **Ret-Robust**: Đạt hiệu suất cao trên nhiều bộ dữ liệu (ví dụ: 42.9 EM trên NQ, 57.2 F1 trên PopQA).
  - **R1-Searcher**: Tăng khả năng tìm kiếm của LLM thông qua học tăng cường.
  - **Reasoning Pipeline**: Kết hợp khả năng suy luận và lấy thông tin, đạt F1 gần 60 trên HotpotQA.
- **Kết quả tái hiện**: Các phương pháp được kiểm tra với cài đặt nhất quán (sử dụng LLAMA3-8B-instruct, retriever E5-base-v2, lấy 5 tài liệu mỗi truy vấn), giúp dễ dàng so sánh hiệu suất. Kết quả được công bố trên các bộ dữ liệu như NQ, TriviaQA, HotpotQA, v.v.

### 4. **Hiệu quả xử lý và tối ưu hóa**
- **Xử lý trước hiệu quả**: FlashRAG cung cấp các script để xử lý corpus, xây dựng chỉ mục tìm kiếm (index) và thực hiện lấy tài liệu trước (pre-retrieval), giúp đơn giản hóa quy trình chuẩn bị dữ liệu.
- **Tăng tốc độ thực thi**:
  - Sử dụng **vLLM** và **FastChat** để tăng tốc suy luận LLM.
  - Sử dụng **Faiss** để quản lý chỉ mục vector hiệu quả.
  - Hỗ trợ **BM25s** như một thay thế nhẹ cho Pyserini, giúp dễ cài đặt và nhanh hơn.
- **Tích hợp Chunkie**: Một thư viện phân đoạn tài liệu linh hoạt, hỗ trợ các phương pháp phân đoạn dựa trên token, câu, hoặc ngữ nghĩa.

### 5. **Giao diện người dùng trực quan (FlashRAG-UI)**
- **Dễ sử dụng**: FlashRAG-UI cho phép cấu hình và trải nghiệm các phương pháp RAG thông qua giao diện trực quan, không cần viết code phức tạp.
- **Tính năng nổi bật của UI**:
  - **Tải cấu hình nhanh**: Cho phép chọn và lưu các tham số của pipeline RAG.
  - **Trải nghiệm phương pháp**: Hỗ trợ tải corpus, chỉ mục, và chuyển đổi giữa các pipeline để so sánh hiệu suất.
  - **Tái hiện benchmark**: Dễ dàng chạy các phương pháp baseline và đánh giá trên các bộ dữ liệu được tích hợp.

### 6. **Hỗ trợ RAG đa phương thức (Multimodal RAG)**
- FlashRAG đã thêm hỗ trợ cho RAG đa phương thức (từ ngày 24/02/25), bao gồm các mô hình ngôn ngữ lớn đa phương thức (**MLLMs**) như **Llava**, **Qwen**, **InternVL**, và các retriever đa phương thức dựa trên kiến trúc **CLIP**. Điều này mở rộng khả năng xử lý cả văn bản và hình ảnh, phù hợp với các ứng dụng RAG tiên tiến.

### 7. **Cộng đồng và phát triển liên tục**
- **Mã nguồn mở**: FlashRAG được cấp phép dưới **MIT License**, cho phép cộng đồng sử dụng và đóng góp tự do.
- **Cập nhật thường xuyên**: Dự án liên tục được cải tiến với các tính năng mới như hỗ trợ OpenAI models, tích hợp sentence transformers, thêm các chỉ số đánh giá (Unieval, name-entity F1), và hỗ trợ retriever dựa trên API (vLLM server).
- **Đóng góp từ cộng đồng**: FlashRAG khuyến khích đóng góp từ các nhà nghiên cứu, với roadmap rõ ràng để mở rộng thêm các phương pháp và bộ dữ liệu.

### 8. **Ứng dụng thực tiễn và tài liệu chi tiết**
- **Hỗ trợ nghiên cứu**: FlashRAG đã được sử dụng trong các công trình như **R1-Searcher**, **ReSearch**, và **AutoCoA**, chứng minh tính hữu ích trong việc phát triển các phương pháp RAG mới.
- **Tài liệu đầy đủ**: Dự án cung cấp tài liệu chi tiết về cách tái hiện các phương pháp, cấu hình pipeline, và sử dụng các thành phần, giúp cả người mới bắt đầu và nhà nghiên cứu có kinh nghiệm dễ dàng làm quen.
- **Bài báo được công nhận**: FlashRAG đã được chấp nhận tại **WWW 2025 (Resource Track)**, khẳng định chất lượng và giá trị nghiên cứu của nó.

### 9. **Hiệu suất nổi bật**
- FlashRAG cung cấp bảng kết quả chi tiết cho 17 phương pháp RAG trên các bộ dữ liệu phổ biến:
  - **Ret-Robust** đạt **42.9 EM** trên NQ và **57.2 F1** trên PopQA.
  - **R1-Searcher** đạt **59.5 F1** trên HotpotQA, cho thấy khả năng xử lý các truy vấn phức tạp (multi-hop).
  - **Spring** cải thiện đáng kể hiệu suất LLM với **54.8 F1** trên PopQA.

### 10. **Hỗ trợ nền tảng phần cứng Trung Quốc**
- FlashRAG cung cấp các phiên bản dựa trên **Paddle** và **MindSpore**, hỗ trợ các nền tảng phần cứng của Trung Quốc, giúp tăng khả năng tương thích với các hệ thống địa phương.

### Tại sao FlashRAG nổi bật?
- **Toàn diện**: Kết hợp cả dữ liệu, thuật toán, và công cụ trong một bộ công cụ duy nhất.
- **Dễ sử dụng**: Giao diện UI và tài liệu chi tiết giúp giảm rào cản cho người mới.
- **Hiệu quả**: Tối ưu hóa hiệu suất với các công cụ như vLLM, Faiss, và BM25s.
- **Tính linh hoạt**: Hỗ trợ từ RAG truyền thống đến RAG đa phương thức và suy luận (reasoning).
- **Cộng đồng định hướng**: Mã nguồn mở, cập nhật liên tục, và khuyến khích đóng góp.

### Kết luận
FlashRAG là một công cụ lý tưởng cho nghiên cứu RAG nhờ vào bộ dữ liệu phong phú, các thuật toán tiên tiến, giao diện thân thiện, và khả năng tùy chỉnh cao. Nếu bạn đang nghiên cứu RAG, FlashRAG không chỉ giúp tái hiện các phương pháp SOTA mà còn hỗ trợ phát triển các ý tưởng mới với hiệu suất tối ưu. Bạn có muốn mình đi sâu vào một khía cạnh cụ thể của FlashRAG, như cách sử dụng một pipeline cụ thể hoặc một thuật toán nào đó không?

**FlashRAG** cung cấp 17 thuật toán **Retrieval-Augmented Generation (RAG)** tiên tiến, được triển khai trong khuôn khổ của mình để hỗ trợ nghiên cứu và tái hiện các phương pháp RAG hiện đại. Các thuật toán này **không chạy cùng lúc** mà do **người dùng quyết định** chọn và cấu hình thông qua pipeline hoặc giao diện FlashRAG-UI. Dưới đây, mình sẽ đi sâu vào chi tiết về 17 thuật toán này, cách chúng hoạt động, và cách người dùng chọn chúng để sử dụng.

---

### **Tổng quan về 17 thuật toán RAG**
FlashRAG phân loại các phương pháp RAG thành bốn loại dựa trên cách chúng thực thi trong quá trình suy luận:
1. **Sequential (Tuần tự)**: Thực hiện theo quy trình tuyến tính (truy vấn → lấy tài liệu → xử lý sau lấy tài liệu → sinh câu trả lời).
2. **Conditional (Điều kiện)**: Chọn đường thực thi khác nhau dựa trên loại truy vấn.
3. **Branching (Phân nhánh)**: Thực hiện nhiều đường thực thi song song và tổng hợp kết quả.
4. **Loop (Lặp)**: Lặp lại quá trình lấy tài liệu và sinh nội dung cho đến khi đạt được kết quả mong muốn.
5. **Reasoning (Suy luận)**: Kết hợp khả năng suy luận với lấy tài liệu.

Dưới đây là danh sách 17 thuật toán RAG được triển khai trong FlashRAG, kèm theo mô tả ngắn gọn và hiệu suất trên một số bộ dữ liệu (dựa trên tài liệu):

| **Phương pháp**         | **Loại**        | **Mô tả**                                                                 | **Hiệu suất nổi bật** (NQ EM / HotpotQA F1 / PopQA F1) | **Cài đặt cụ thể** |
|-------------------------|-----------------|---------------------------------------------------------------------------|-------------------------------------------------------|---------------------|
| **Naive Generation**    | Sequential      | Sinh câu trả lời trực tiếp từ LLM mà không lấy tài liệu.                  | 22.6 / 28.4 / 21.7                                   | Không có            |
| **Standard RAG**        | Sequential      | Pipeline RAG cơ bản: lấy tài liệu → sinh câu trả lời.                     | 35.1 / 35.3 / 36.7                                   | Không có            |
| **AAR-contriever-kilt** | Sequential      | Sử dụng Contriever để cải thiện lấy tài liệu trong các tác vụ KILT.       | 30.1 / 33.4 / 36.1                                   | Không có            |
| **LongLLMLingua**       | Sequential      | Nén ngữ cảnh bằng LLMLingua để cải thiện hiệu quả đầu vào.                | 32.2 / 37.5 / 38.7                                   | Tỷ lệ nén = 0.5    |
| **RECOMP-abstractive**  | Sequential      | Tinh chỉnh ngữ cảnh bằng mô hình seq2seq trước khi sinh câu trả lời.      | 33.1 / 37.5 / 39.9                                   | Không có            |
| **Selective-Context**   | Sequential      | Nén ngữ cảnh bằng Selective-Context để giữ lại thông tin quan trọng.      | 30.5 / 34.4 / 33.5                                   | Tỷ lệ nén = 0.5    |
| **Trace**               | Sequential      | Tinh chỉnh ngữ cảnh bằng cách xây dựng đồ thị tri thức (knowledge graph). | 30.7 / 34.0 / 37.4                                   | Không có            |
| **Spring**              | Sequential      | Tăng hiệu suất LLM bằng cách thêm một vài token embeddings.               | 37.9 / 42.6 / 54.8                                   | Dùng Llama2-7B-chat với bảng embedding được huấn luyện |
| **SuRe**                | Branching       | Xếp hạng và tổng hợp kết quả từ nhiều tài liệu được lấy.                  | 37.1 / 33.4 / 48.1                                   | Dùng prompt được cung cấp |
| **REPLUG**              | Branching       | Tích hợp xác suất từ nhiều đường sinh để tạo câu trả lời.                 | 28.9 / 31.2 / 27.8                                   | Không có            |
| **SKR**                 | Conditional     | Đánh giá xem có cần lấy tài liệu dựa trên phương pháp SKR.                | 33.2 / 32.4 / 31.7                                   | Dùng dữ liệu huấn luyện tại thời điểm suy luận |
| **Adaptive-RAG**        | Conditional     | Tự động chọn quy trình RAG dựa trên loại truy vấn.                        | 35.1 / 39.1 / 40.4                                   | Không có            |
| **Ret-Robust**          | Loop            | Lặp lại lấy tài liệu và sinh câu trả lời để cải thiện độ chính xác.       | 42.9 / 35.8 / 57.2                                   | Dùng Llama2-13B với LoRA được huấn luyện |
| **Self-RAG**            | Loop            | Tự động lấy tài liệu, đánh giá, và sinh câu trả lời thích nghi.           | 36.4 / 29.6 / 32.7                                   | Dùng SelfRAG-Llama2-7B được huấn luyện |
| **FLARE**               | Loop            | Lấy tài liệu động trong quá trình sinh câu trả lời.                       | 22.5 / 28.0 / 20.7                                   | Không có            |
| **Iter-Retgen (ITRG)**  | Loop            | Lặp lại quá trình lấy tài liệu và sinh nội dung.                          | 36.8 / 38.3 / 37.9                                   | Không có            |
| **IRCoT**               | Loop            | Tích hợp lấy tài liệu với Chuỗi Suy nghĩ (Chain-of-Thought).              | 33.3 / 41.5 / 45.6                                   | Không có            |
| **RQRAG**               | Loop            | Tinh chỉnh truy vấn và lấy tài liệu lặp lại để cải thiện kết quả.         | 32.6 / 33.5 / 46.4                                   | Dùng RQ-RAG-Llama2-7B được huấn luyện |
| **R1-Searcher**         | Reasoning       | Tăng khả năng tìm kiếm của LLM thông qua học tăng cường.                  | 37.3 / 59.5 / 43.9                                   | Dùng Qwen2.5-7B được huấn luyện |

---

### **Các thuật toán có chạy cùng lúc không?**
- **Không chạy cùng lúc**: FlashRAG không tự động chạy đồng thời 17 thuật toán này. Thay vào đó, **người dùng quyết định** chọn thuật toán nào để sử dụng thông qua:
  - **Cấu hình pipeline**: Người dùng có thể chọn một pipeline cụ thể (Sequential, Conditional, Branching, Loop, hoặc Reasoning) và chỉ định phương pháp RAG tương ứng trong file cấu hình (`yaml`) hoặc thông qua biến `config_dict`.
  - **FlashRAG-UI**: Giao diện người dùng cho phép chọn và cấu hình một phương pháp RAG cụ thể để chạy, giúp dễ dàng so sánh hiệu suất hoặc thử nghiệm trên các bộ dữ liệu.
- **Tính linh hoạt**: Người dùng có thể chạy nhiều thuật toán tuần tự để so sánh kết quả, nhưng mỗi lần chạy chỉ thực thi một pipeline với một phương pháp được chọn. FlashRAG hỗ trợ lưu trữ kết quả trung gian và đánh giá để so sánh hiệu quả.

---

### **Chi tiết về cách chọn và sử dụng thuật toán**
1. **Sử dụng pipeline có sẵn**:
   - FlashRAG cung cấp các lớp pipeline tương ứng với từng loại phương pháp (ví dụ: `SequentialPipeline`, `ConditionalPipeline`, `REPLUGPipeline`, `IterativePipeline`, v.v.).
   - Để sử dụng một thuật toán cụ thể, bạn cần:
     - **Cấu hình**: Chỉ định pipeline và các tham số (retriever, generator, refiner, v.v.) trong file `yaml` hoặc biến `config_dict`.
     - **Tải pipeline**: Sử dụng `SequentialPipeline(my_config)` hoặc các lớp pipeline khác, sau đó gọi `pipeline.run(dataset)` để thực thi.
     - Ví dụ mã để chạy **Standard RAG**:
       ```python
       from flashrag.config import Config
       from flashrag.pipeline import SequentialPipeline
       from flashrag.utils import get_dataset

       config_dict = {'data_dir': 'dataset/', 'pipeline': 'sequential', 'method': 'standard_rag'}
       my_config = Config(config_file_path='my_config.yaml', config_dict=config_dict)
       dataset = get_dataset(my_config)['test']
       pipeline = SequentialPipeline(my_config)
       output = pipeline.run(dataset, do_eval=True)
       ```

2. **Sử dụng FlashRAG-UI**:
   - Giao diện UI cho phép chọn pipeline và phương pháp RAG thông qua các nút bấm hoặc menu. Bạn có thể:
     - Tải cấu hình có sẵn cho một phương pháp (ví dụ: **Ret-Robust**, **Spring**).
     - Chọn bộ dữ liệu và corpus để chạy thử nghiệm.
     - Xem kết quả và đánh giá trực quan trên giao diện.
   - Để chạy UI:
     ```bash
     cd webui
     python interface.py
     ```

3. **Xây dựng pipeline tùy chỉnh**:
   - Nếu bạn muốn thử nghiệm một phương pháp mới hoặc kết hợp các thuật toán, bạn có thể kế thừa lớp `BasicPipeline` và tự định nghĩa logic trong hàm `run`. Điều này cho phép bạn tích hợp các thành phần từ 17 phương pháp trên hoặc tạo ra phương pháp mới.

---

### **Điểm nổi bật của các thuật toán**
- **Hiệu suất cao**:
  - **Ret-Robust** và **R1-Searcher** nổi bật với hiệu suất cao trên các bộ dữ liệu phức tạp (ví dụ: 59.5 F1 trên HotpotQA cho R1-Searcher).
  - **Spring** cải thiện đáng kể hiệu suất LLM chỉ bằng cách thêm một vài token embeddings (54.8 F1 trên PopQA).
- **Đa dạng cách tiếp cận**:
  - **Sequential**: Phù hợp cho các tác vụ đơn giản, dễ triển khai (Standard RAG, LongLLMLingua).
  - **Conditional**: Linh hoạt với các truy vấn khác nhau (Adaptive-RAG, SKR).
  - **Branching**: Tăng độ chính xác bằng cách tổng hợp nhiều đường sinh (SuRe, REPLUG).
  - **Loop**: Xử lý các truy vấn phức tạp bằng cách lặp lại (Ret-Robust, Self-RAG, IRCoT).
  - **Reasoning**: Kết hợp suy luận, đặc biệt mạnh trong các tác vụ multi-hop (R1-Searcher).
- **Tái hiện dễ dàng**: Mỗi phương pháp được triển khai với cài đặt nhất quán (LLAMA3-8B-instruct, E5-base-v2 retriever, 5 tài liệu), giúp so sánh công bằng. Tài liệu chi tiết và hướng dẫn tái hiện được cung cấp.

---

### **Lưu ý khi chọn thuật toán**
- **Tùy thuộc vào tác vụ**:
  - Các tác vụ QA đơn giản (như NQ, TriviaQA) có thể sử dụng **Standard RAG** hoặc **Spring** để đạt hiệu quả cao với chi phí thấp.
  - Các tác vụ multi-hop (như HotpotQA) nên dùng **R1-Searcher** hoặc **IRCoT** để tận dụng khả năng suy luận.
  - Nếu cần xử lý ngữ cảnh dài, **LongLLMLingua** hoặc **Selective-Context** giúp nén hiệu quả.
- **Yêu cầu tài nguyên**:
  - Một số phương pháp như **Ret-Robust** hoặc **R1-Searcher** yêu cầu mô hình được huấn luyện trước (như Llama2-13B với LoRA hoặc Qwen2.5-7B), có thể cần GPU mạnh.
  - Các phương pháp như **Naive Generation** hoặc **Standard RAG** nhẹ hơn, phù hợp với tài nguyên hạn chế.
- **Cấu hình cụ thể**: Một số phương pháp (như Spring, Ret-Robust, RQRAG) yêu cầu các tham số hoặc mô hình được huấn luyện trước, cần tham khảo tài liệu chi tiết hoặc cài đặt bổ sung.

---

### **Kết luận**
17 thuật toán RAG trong FlashRAG cung cấp một bộ công cụ đa dạng, từ các phương pháp cơ bản đến tiên tiến, phù hợp với nhiều loại tác vụ và nhu cầu nghiên cứu. Chúng không chạy cùng lúc mà được người dùng chọn thông qua cấu hình hoặc giao diện UI. FlashRAG-UI và các pipeline có sẵn giúp việc chọn và thử nghiệm các thuật toán này trở nên dễ dàng, trong khi khả năng tùy chỉnh cho phép bạn kết hợp hoặc phát triển các phương pháp mới.

Nếu bạn muốn đi sâu hơn vào một thuật toán cụ thể (ví dụ: **R1-Searcher** hoặc **Ret-Robust**) hoặc cần hướng dẫn chi tiết về cách cấu hình một phương pháp, hãy cho mình biết nhé!
