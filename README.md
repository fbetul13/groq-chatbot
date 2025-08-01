# AI Chatbot - Groq API ile

Bu proje, Groq API kullanarak ChatGPT benzeri bir chatbot uygulamasıdır. Backend Python Flask ile, frontend ise Streamlit ile geliştirilmiştir.

## 🚀 Özellikler

- **Hızlı Yanıt**: Groq API'nin hızlı LLM modelleri ile anında yanıt
- **Modern UI**: Streamlit ile responsive ve kullanıcı dostu arayüz
- **Kullanıcı Kimlik Doğrulama**: Güvenli giriş/kayıt sistemi
- **Kişisel Sohbet Geçmişi**: Her kullanıcının kendi sohbet geçmişi
- **Gelişmiş Kontroller**: Model seçimi, sıcaklık ve token ayarları
- **Gerçek Zamanlı**: Canlı chat deneyimi
- **Sohbet Geçmişi**: SQLite veritabanı ile kalıcı sohbet saklama
- **Oturum Yönetimi**: Birden fazla sohbet oturumu oluşturma ve yönetme
- **API Durumu**: Backend bağlantı kontrolü
- **Türkçe Destek**: Tam Türkçe arayüz
- **Mesaj Geçmişi**: Tüm mesajları kalıcı olarak saklama
- **Güvenlik**: Şifre hash'leme ve session yönetimi
- **📄 Export Özellikleri**: JSON, CSV, PDF ve TXT formatlarında sohbet indirme
- **🌍 Çoklu Dil Desteği**: 100+ dilde otomatik dil algılama ve yanıt
- **🔍 Kalite Kontrolü**: Yanıt kalitesini kontrol etme
- **📱 Responsive Tasarım**: Mobil ve masaüstü uyumlu

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

### 2. Cursor/VSCode ayarları (opsiyonel)
Proje `.vscode/settings.json` dosyası ile panel boyutları otomatik ayarlanır:
- Sağ panel geniş olarak açılır (800px)
- Sidebar sol tarafta kalır (300px)
- Panel maksimize edilmiş olarak başlar

### 3. Python bağımlılıklarını yükleyin
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
SECRET_KEY=your_secret_key_here_or_leave_empty_for_auto_generation
```

### 4. Backend'i başlatın
```bash
cd backend
python3 app.py
```

Backend `http://localhost:5050` adresinde çalışacaktır.

### 5. Streamlit Frontend'i başlatın
```bash
cd frontend
streamlit run streamlit_app.py
```

Streamlit uygulaması `http://localhost:8501` adresinde açılacaktır.

## 🎯 Kullanım

1. Streamlit uygulamasını başlatın: `streamlit run frontend/streamlit_app.py`
2. Tarayıcınızda `http://localhost:8501` adresini açın
3. **İlk kullanımda kayıt olun** veya mevcut hesabınızla giriş yapın
4. Sidebar'dan model ve parametreleri ayarlayın
5. **Sohbet Oturumları** bölümünden mevcut oturumları görüntüleyin veya yeni oturum oluşturun
6. Chat kutusuna sorunuzu yazın ve Enter'a basın
7. AI'dan yanıtınızı alın!

### 🔐 Kullanıcı Kimlik Doğrulama

- **Kayıt Olma**: İlk kullanımda "📝 Kayıt" sekmesinden hesap oluşturun
  - Kullanıcı adı en az 3 karakter olmalıdır
  - Şifre en az 6 karakter olmalıdır
- **Giriş Yapma**: "🔑 Giriş" sekmesinden mevcut hesabınızla giriş yapın
- **Çıkış Yapma**: Sidebar'daki "🚪 Çıkış Yap" butonunu kullanın
- **Güvenlik**: Şifreler SHA-256 ile hash'lenerek saklanır

### 💬 Sohbet Oturumu Yönetimi

- **Yeni Oturum**: "➕ Yeni Oturum" butonuna tıklayarak yeni bir sohbet başlatın
- **Oturum Seçimi**: Sidebar'daki oturum listesinden istediğiniz oturumu seçin
- **Oturum Yeniden Adlandırma**: Aktif oturumun ismini değiştirmek için metin kutusunu kullanın
- **Oturum Silme**: Oturum yanındaki "🗑️" butonuna tıklayarak oturumu silin
- **Oturum Yenileme**: "🔄 Oturumları Yenile" butonu ile listeyi güncelleyin
- **Kişisel Geçmiş**: Her kullanıcı sadece kendi sohbet geçmişini görebilir

## 📁 Proje Yapısı

```
chatbot/
├── backend/
│   ├── app.py              # Flask API server
│   └── chatbot.db          # SQLite veritabanı (otomatik oluşturulur)
├── frontend/
│   └── streamlit_app.py    # Streamlit web arayüzü
├── requirements.txt        # Python bağımlılıkları
├── env_example.txt         # Environment variables örneği
└── README.md              # Bu dosya
```

## 🔧 API Endpoints

### POST /api/register
Kullanıcı kaydı.

**Request:**
```json
{
    "username": "kullanici_adi",
    "password": "sifre123"
}
```

**Response:**
```json
{
    "message": "Registration successful",
    "user_id": 1,
    "username": "kullanici_adi"
}
```

### POST /api/login
Kullanıcı girişi.

**Request:**
```json
{
    "username": "kullanici_adi",
    "password": "sifre123"
}
```

**Response:**
```json
{
    "message": "Login successful",
    "user_id": 1,
    "username": "kullanici_adi"
}
```

### POST /api/logout
Kullanıcı çıkışı.

### GET /api/user
Kullanıcı bilgilerini getir (kimlik doğrulama gerekli).

### POST /api/chat
Chatbot ile konuşmak için kullanılır (kimlik doğrulama gerekli).

**Request:**
```json
{
    "message": "Merhaba, nasılsın?",
    "session_id": "optional-session-id",
    "model": "llama3-8b-8192",
    "temperature": 0.7,
    "max_tokens": 1024
}
```

**Response:**
```json
{
    "response": "Merhaba! Ben iyiyim, teşekkür ederim. Size nasıl yardımcı olabilirim?",
    "session_id": "generated-session-id",
    "model": "llama3-8b-8192",
    "temperature": 0.7,
    "max_tokens": 1024
}
```

### GET /api/sessions
Kullanıcının sohbet oturumlarını listeler (kimlik doğrulama gerekli).

**Response:**
```json
{
    "sessions": [
        {
            "session_id": "uuid",
            "session_name": "Sohbet 01.01.2024 14:30",
            "created_at": "2024-01-01T14:30:00",
            "updated_at": "2024-01-01T15:45:00",
            "message_count": 10
        }
    ]
}
```

### GET /api/sessions/{session_id}
Belirli bir oturumun mesajlarını getir (kimlik doğrulama gerekli).

**Response:**
```json
{
    "messages": [
        {
            "role": "user",
            "content": "Merhaba",
            "timestamp": "2024-01-01T14:30:00",
            "model": "llama3-8b-8192",
            "temperature": 0.7,
            "max_tokens": 1024
        }
    ]
}
```

### DELETE /api/sessions/{session_id}
Sohbet oturumunu sil (kimlik doğrulama gerekli).

### PUT /api/sessions/{session_id}/rename
Sohbet oturumunu yeniden adlandır (kimlik doğrulama gerekli).

**Request:**
```json
{
    "session_name": "Yeni Oturum Adı"
}
```

### GET /api/health
API'nin çalışır durumda olup olmadığını kontrol eder.

## 🎨 Özelleştirme

### Model ve Parametre Ayarları
Streamlit arayüzünden sidebar'da şu ayarları yapabilirsiniz:
- **Model Seçimi**: llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it, llama-3.1-8b-instant, llama-3.3-70b-versatile, qwen/qwen3-32b, moonshotai/kimi-k2-instruct
- **Sıcaklık**: 0.0-2.0 arası yaratıcılık seviyesi
- **Maksimum Token**: 100-4096 arası yanıt uzunluğu

### Veritabanı Yönetimi
- Veritabanı dosyası (`chatbot.db`) otomatik olarak oluşturulur
- Kullanıcı bilgileri ve sohbet geçmişi kalıcı olarak saklanır
- Oturumlar ve mesajlar SQLite veritabanında tutulur
- Her kullanıcının verileri ayrı ayrı saklanır

### UI Özelleştirme
`frontend/streamlit_app.py` dosyasındaki CSS stillerini düzenleyerek görünümü özelleştirebilirsiniz.

## 🔒 Güvenlik

- API anahtarınızı asla kod içinde saklamayın
- `.env` dosyasını `.gitignore`'a ekleyin
- Production ortamında HTTPS kullanın
- Veritabanı dosyasını güvenli bir yerde saklayın
- Şifreler SHA-256 ile hash'lenerek saklanır
- Session yönetimi ile güvenli oturum kontrolü
- Kullanıcılar sadece kendi verilerine erişebilir

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

### Veritabanı sorunları
- `chatbot.db` dosyasının yazma izinlerini kontrol edin
- Veritabanı dosyası bozuksa silip yeniden oluşturabilirsiniz
- SQLite sürümünüzün güncel olduğundan emin olun

### Kimlik doğrulama sorunları
- Kullanıcı adı ve şifrenin doğru olduğundan emin olun
- Kayıt olurken şifre gereksinimlerini kontrol edin
- Session çerezlerinin tarayıcıda etkin olduğundan emin olun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 🚀 Deployment (Canlıya Alma)

### Render ile Deployment (Önerilen)

1. **Render hesabı oluşturun**: [render.com](https://render.com) adresinden ücretsiz hesap oluşturun

2. **GitHub repository'nizi bağlayın**:
   - Render Dashboard'da "New +" > "Blueprint" seçin
   - GitHub repository'nizi seçin
   - `render.yaml` dosyası otomatik olarak algılanacak

3. **Environment Variables ayarlayın**:
   - `GROQ_API_KEY`: Groq API anahtarınız
   - `SECRET_KEY`: Güvenlik için rastgele bir anahtar (otomatik oluşturulabilir)

4. **Deploy edin**:
   - Render otomatik olarak backend ve frontend servislerini oluşturacak
   - Backend: `https://your-app-name.onrender.com`
   - Frontend: `https://your-app-name-frontend.onrender.com`

### Heroku ile Deployment

1. **Heroku CLI kurulumu**:
```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Heroku CLI'ı resmi siteden indirin
```

2. **Heroku uygulaması oluşturun**:
```bash
heroku create your-app-name
```

3. **Environment variables ayarlayın**:
```bash
heroku config:set GROQ_API_KEY=your_groq_api_key
heroku config:set SECRET_KEY=your_secret_key
```

4. **Deploy edin**:
```bash
git push heroku main
```

### Railway ile Deployment

1. **Railway hesabı oluşturun**: [railway.app](https://railway.app)

2. **GitHub repository'nizi bağlayın**

3. **Environment variables ayarlayın**:
   - `GROQ_API_KEY`
   - `SECRET_KEY`

4. **Otomatik deployment** başlayacak

### AWS/DigitalOcean ile Deployment

Daha gelişmiş deployment için:

1. **VPS/EC2 instance oluşturun**
2. **Docker kullanın** (Dockerfile eklenebilir)
3. **Nginx reverse proxy** kurun
4. **SSL sertifikası** ekleyin (Let's Encrypt)

## 📞 Destek

Herhangi bir sorun yaşarsanız, lütfen issue açın veya iletişime geçin. 