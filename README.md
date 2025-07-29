# AI Chatbot - Groq API ile

Bu proje, Groq API kullanarak ChatGPT benzeri bir chatbot uygulamasıdır. Backend Python Flask ile, frontend ise modern HTML/CSS/JavaScript ile geliştirilmiştir.

## 🚀 Özellikler

- **Hızlı Yanıt**: Groq API'nin hızlı LLM modelleri ile anında yanıt
- **Modern UI**: Streamlit ile responsive ve kullanıcı dostu arayüz
- **Gelişmiş Kontroller**: Model seçimi, sıcaklık ve token ayarları
- **Gerçek Zamanlı**: Canlı chat deneyimi
- **API Durumu**: Backend bağlantı kontrolü
- **Türkçe Destek**: Tam Türkçe arayüz
- **Sohbet Geçmişi**: Mesaj geçmişini saklama

## 📋 Gereksinimler

- Python 3.8+
- Groq API hesabı ve API anahtarı
- Modern web tarayıcısı

## 🛠️ Kurulum

### 1. Projeyi klonlayın
```bash
git clone <repository-url>
cd chatbot
```

### 2. Python bağımlılıklarını yükleyin
```bash
pip3 install -r requirements.txt
```

### 3. Environment variables ayarlayın
```bash
# .env dosyası oluşturun
cp env_example.txt .env
```

`.env` dosyasını düzenleyerek Groq API anahtarınızı ekleyin:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 4. Backend'i başlatın
```bash
cd backend
python3 app.py
```

Backend `http://localhost:5000` adresinde çalışacaktır.

### 5. Streamlit Frontend'i başlatın
```bash
cd frontend
streamlit run streamlit_app.py
```

Streamlit uygulaması `http://localhost:8501` adresinde açılacaktır.

## 🎯 Kullanım

1. Streamlit uygulamasını başlatın: `streamlit run frontend/streamlit_app.py`
2. Tarayıcınızda `http://localhost:8501` adresini açın
3. Sidebar'dan model ve parametreleri ayarlayın
4. Chat kutusuna sorunuzu yazın ve Enter'a basın
5. AI'dan yanıtınızı alın!

## 📁 Proje Yapısı

```
chatbot/
├── backend/
│   └── app.py              # Flask API server
├── frontend/
│   └── streamlit_app.py    # Streamlit web arayüzü
├── requirements.txt        # Python bağımlılıkları
├── env_example.txt         # Environment variables örneği
└── README.md              # Bu dosya
```

## 🔧 API Endpoints

### POST /api/chat
Chatbot ile konuşmak için kullanılır.

**Request:**
```json
{
    "message": "Merhaba, nasılsın?"
}
```

**Response:**
```json
{
    "response": "Merhaba! Ben iyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?",
    "model": "llama3-8b-8192"
}
```

### GET /api/health
API'nin çalışır durumda olup olmadığını kontrol eder.

## 🎨 Özelleştirme

### Model ve Parametre Ayarları
Streamlit arayüzünden sidebar'da şu ayarları yapabilirsiniz:
- **Model Seçimi**: llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it
- **Sıcaklık**: 0.0-2.0 arası yaratıcılık seviyesi
- **Maksimum Token**: 100-4096 arası yanıt uzunluğu

### UI Özelleştirme
`frontend/streamlit_app.py` dosyasındaki CSS stillerini düzenleyerek görünümü özelleştirebilirsiniz.

## 🔒 Güvenlik

- API anahtarınızı asla kod içinde saklamayın
- `.env` dosyasını `.gitignore`'a ekleyin
- Production ortamında HTTPS kullanın

## 🐛 Sorun Giderme

### Backend başlatılamıyor
- Python sürümünüzün 3.8+ olduğundan emin olun (`python3 --version`)
- Tüm bağımlılıkların yüklendiğini kontrol edin (`pip3 install -r requirements.txt`)
- `.env` dosyasında API anahtarının doğru olduğunu kontrol edin
- macOS'ta `python3` komutunu kullandığınızdan emin olun

### Frontend bağlantı hatası
- Backend'in çalıştığından emin olun
- Tarayıcı konsolunda hata mesajlarını kontrol edin
- CORS ayarlarının doğru olduğunu kontrol edin

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📞 Destek

Herhangi bir sorun yaşarsanız, lütfen issue açın veya iletişime geçin. 