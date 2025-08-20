# Website với AI Chatbot

Một trang web hiện đại với chatbot AI tích hợp, được xây dựng bằng React và Flask.

## 🚀 Tính Năng

- **Trang web responsive** với giao diện hiện đại
- **AI Chatbot** có thể trả lời câu hỏi dựa trên nội dung trang web
- **Multi-API support** (OpenRouter, Groq, Gemini, OpenAI)
- **Real-time chat interface** với typing indicators
- **Modern UI/UX** sử dụng Tailwind CSS và Shadcn/UI

## 🛠️ Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- Shadcn/UI Components
- Lucide Icons

### Backend
- Flask
- Flask-CORS
- SQLAlchemy
- Requests

## 📁 Cấu Trúc Project

```
├── website-with-chatbot/     # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/           # UI Components
│   │   │   └── Chatbot.jsx   # Chatbot Component
│   │   ├── App.jsx           # Main App
│   │   └── main.jsx          # Entry Point
│   └── dist/                 # Build Output
│
├── chatbot-backend/          # Flask Backend
│   ├── src/
│   │   ├── routes/
│   │   │   ├── chatbot.py    # Chatbot API
│   │   │   └── user.py       # User API
│   │   ├── models/           # Database Models
│   │   ├── static/           # Frontend Build Files
│   │   └── main.py           # Flask App
│   └── venv/                 # Virtual Environment
│
├── HUONG_DAN_SU_DUNG.md     # Hướng dẫn chi tiết
└── README.md                 # File này
```

## 🚀 Quick Start

### 1. Development Mode

#### Frontend:
```bash
cd website-with-chatbot
npm install
npm run dev
```

#### Backend:
```bash
cd chatbot-backend
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### 2. Production Mode

```bash
# Build frontend
cd website-with-chatbot
npm run build

# Copy to Flask static
cp -r dist/* ../chatbot-backend/src/static/

# Run Flask
cd ../chatbot-backend
source venv/bin/activate
python src/main.py
```

## 🔑 API Configuration

Cấu hình environment variables cho chatbot:

```bash
export OPENROUTER_API_KEY="your-key"
export GROQ_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

## 📱 Screenshots

### Trang chủ
- Hero section với call-to-action
- Stats section với số liệu
- Features showcase
- Customer testimonials
- Pricing plans
- Contact information

### Chatbot
- Floating chat button
- Modern chat interface
- AI responses based on website content
- Error handling và fallbacks

## 🎨 Customization

### Thay đổi nội dung trang web:
Chỉnh sửa `website-with-chatbot/src/App.jsx`

### Cập nhật chatbot knowledge:
Chỉnh sửa `WEBSITE_CONTENT` trong `chatbot-backend/src/routes/chatbot.py`

### Styling:
Chỉnh sửa `website-with-chatbot/src/App.css`

## 📖 Documentation

Xem file `HUONG_DAN_SU_DUNG.md` để có hướng dẫn chi tiết về:
- Cách chạy và deploy
- Cấu hình API keys
- Customization
- Troubleshooting

## 🤝 Contributing

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra file `HUONG_DAN_SU_DUNG.md`
2. Xem logs trong browser console
3. Kiểm tra API keys và environment variables

---

**Được tạo bởi Manus AI** 🤖

