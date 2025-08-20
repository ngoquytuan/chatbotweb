# Hướng Dẫn Sử Dụng Website với AI Chatbot

## Tổng Quan

Tôi đã tạo thành công một trang web hiện đại với chatbot AI tích hợp. Trang web bao gồm:

- **Frontend**: React application với giao diện responsive, hiện đại
- **Backend**: Flask API server với chatbot AI tích hợp
- **Chatbot**: AI Assistant có thể trả lời câu hỏi dựa trên nội dung trang web

## Cấu Trúc Project

### Frontend (React)
```
website-with-chatbot/
├── src/
│   ├── components/
│   │   ├── ui/           # Shadcn/UI components
│   │   └── Chatbot.jsx   # Component chatbot chính
│   ├── App.jsx           # Component chính của trang web
│   ├── App.css           # Styles chính
│   └── main.jsx          # Entry point
├── dist/                 # Build files (sau khi chạy npm run build)
└── package.json          # Dependencies
```

### Backend (Flask)
```
chatbot-backend/
├── src/
│   ├── routes/
│   │   ├── user.py       # User routes (mẫu)
│   │   └── chatbot.py    # Chatbot API routes
│   ├── models/           # Database models
│   ├── static/           # Frontend build files
│   └── main.py           # Flask app chính
├── venv/                 # Virtual environment
└── requirements.txt      # Python dependencies
```

## Cách Chạy Trang Web

### 1. Chạy Development Mode

#### Frontend (React):
```bash
cd website-with-chatbot
npm install
npm run dev
```
Trang web sẽ chạy tại: http://localhost:5173

#### Backend (Flask):
```bash
cd chatbot-backend
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```
API server sẽ chạy tại: http://localhost:5001

### 2. Chạy Production Mode

#### Build Frontend:
```bash
cd website-with-chatbot
npm run build
```

#### Copy build files vào Flask static:
```bash
cp -r website-with-chatbot/dist/* chatbot-backend/src/static/
```

#### Chạy Flask server:
```bash
cd chatbot-backend
source venv/bin/activate
python src/main.py
```

Trang web full-stack sẽ chạy tại: http://localhost:5001

## Cấu Hình API Keys

Để chatbot hoạt động đầy đủ, bạn cần cấu hình API keys cho các dịch vụ AI:

### 1. OpenRouter API
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### 2. Groq API
```bash
export GROQ_API_KEY="your-groq-api-key"
```

### 3. Gemini API
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 4. OpenAI API (fallback)
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**Lưu ý**: Chatbot sẽ thử các API theo thứ tự: OpenRouter → Groq → Gemini → OpenAI. Nếu không có API key nào, chatbot sẽ hiển thị thông báo lỗi và hướng dẫn liên hệ.

## Tính Năng Chính

### 1. Trang Web
- **Responsive Design**: Tương thích với desktop và mobile
- **Modern UI**: Sử dụng Tailwind CSS và Shadcn/UI components
- **Sections**: Hero, Stats, Features, Testimonials, Pricing, Contact
- **Navigation**: Smooth scrolling và mobile menu

### 2. Chatbot AI
- **Floating Button**: Ở góc dưới bên phải
- **Chat Interface**: Giao diện chat hiện đại với typing indicator
- **Context Aware**: Trả lời dựa trên nội dung trang web
- **Multi-API Support**: Tích hợp nhiều dịch vụ AI
- **Error Handling**: Xử lý lỗi và fallback gracefully

### 3. Backend API
- **RESTful API**: `/api/chat` endpoint cho chatbot
- **CORS Support**: Cho phép frontend kết nối
- **Health Check**: `/api/health` endpoint
- **Static Serving**: Serve frontend từ Flask

## Tùy Chỉnh Nội Dung

### 1. Cập Nhật Nội Dung Trang Web
Chỉnh sửa file `website-with-chatbot/src/App.jsx`:
- Thay đổi tên brand, logo
- Cập nhật hero section, features, testimonials
- Thay đổi pricing plans
- Cập nhật thông tin liên hệ

### 2. Cập Nhật Nội Dung Chatbot
Chỉnh sửa file `chatbot-backend/src/routes/chatbot.py`:
- Cập nhật biến `WEBSITE_CONTENT` với thông tin mới
- Thay đổi system prompt
- Thêm/bớt thông tin sản phẩm/dịch vụ

### 3. Styling
Chỉnh sửa file `website-with-chatbot/src/App.css`:
- Thay đổi color scheme
- Cập nhật typography
- Tùy chỉnh animations

## Deployment

### 1. Shared Hosting
- Build frontend: `npm run build`
- Upload build files và Flask backend
- Cấu hình Python environment
- Set environment variables cho API keys

### 2. VPS/Cloud
- Clone repository
- Setup Python virtual environment
- Install dependencies
- Configure reverse proxy (Nginx)
- Setup SSL certificate
- Configure environment variables

### 3. Docker (Optional)
Tạo Dockerfile cho containerization:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY chatbot-backend/ .
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["python", "src/main.py"]
```

## Troubleshooting

### 1. Chatbot Không Hoạt Động
- Kiểm tra API keys đã được set chưa
- Kiểm tra backend server đang chạy
- Kiểm tra CORS configuration
- Xem logs trong browser console

### 2. Frontend Không Load
- Kiểm tra build files trong static folder
- Kiểm tra Flask static folder configuration
- Verify file paths

### 3. Styling Issues
- Kiểm tra Tailwind CSS import
- Verify component imports
- Check responsive breakpoints

## Bảo Mật

### 1. API Keys
- Không commit API keys vào git
- Sử dụng environment variables
- Rotate keys định kỳ

### 2. CORS
- Cấu hình CORS cho production domain
- Không allow all origins trong production

### 3. Rate Limiting
- Implement rate limiting cho API endpoints
- Monitor API usage

## Hỗ Trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Dependencies đã được install đầy đủ
2. Environment variables đã được set
3. Ports không bị conflict
4. File permissions đúng

Chúc bạn sử dụng thành công!

