from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq
import json
import sqlite3
from datetime import datetime
import uuid
import hashlib
import secrets
import csv
import io
import tiktoken
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, gray
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from web_research import WebResearch

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
# Render'da CORS ayarlarını genişlet
CORS(app, 
     supports_credentials=True,
     origins=['http://localhost:8501', 'https://chatbot-frontend-u380.onrender.com'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Groq API anahtarını al
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

# Groq client'ını başlat
client = Groq(api_key=GROQ_API_KEY)

# Web araştırma modülünü başlat
web_research = WebResearch()

# Veritabanı başlatma
def init_db():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sohbet oturumları tablosu (kullanıcı ID'si eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            session_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Silinen sohbet oturumları tablosu (geri alma için)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            session_name TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Mesajlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model TEXT,
            temperature REAL,
            max_tokens INTEGER,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    # Silinen mesajlar tablosu (geri alma için)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            model TEXT,
            temperature REAL,
            max_tokens INTEGER,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# Şifre hash fonksiyonu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# PDF oluşturma fonksiyonu
def create_pdf_from_session(session_data, messages):
    """Sohbet oturumunu PDF formatında oluştur"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Stil tanımlamaları
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Ortalanmış
    )
    
    user_style = ParagraphStyle(
        'UserMessage',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        leftIndent=20,
        borderWidth=1,
        borderColor=blue,
        borderPadding=8,
        backColor=gray
    )
    
    bot_style = ParagraphStyle(
        'BotMessage',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        leftIndent=20,
        borderWidth=1,
        borderColor=black,
        borderPadding=8
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=6,
        textColor=gray
    )
    
    # PDF içeriği
    story = []
    
    # Başlık
    story.append(Paragraph(f"🤖 AI Chatbot - Sohbet Raporu", title_style))
    story.append(Spacer(1, 20))
    
    # Oturum bilgileri
    story.append(Paragraph(f"<b>Oturum Adı:</b> {session_data['session_name']}", styles['Normal']))
    story.append(Paragraph(f"<b>Oluşturulma:</b> {session_data['created_at']}", styles['Normal']))
    story.append(Paragraph(f"<b>Son Güncelleme:</b> {session_data['updated_at']}", styles['Normal']))
    story.append(Paragraph(f"<b>Toplam Mesaj:</b> {len(messages)}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Mesajlar
    for i, msg in enumerate(messages):
        role = "👤 Kullanıcı" if msg['role'] == 'user' else "🤖 AI Asistan"
        content = msg['content'].replace('\n', '<br/>')
        timestamp = msg['timestamp']
        
        # Mesaj başlığı
        story.append(Paragraph(f"<b>{role}</b> - {timestamp}", info_style))
        
        # Mesaj içeriği
        if msg['role'] == 'user':
            story.append(Paragraph(content, user_style))
        else:
            story.append(Paragraph(content, bot_style))
        
        story.append(Spacer(1, 10))
    
    # PDF oluştur
    doc.build(story)
    buffer.seek(0)
    return buffer

# TXT oluşturma fonksiyonu
def create_txt_from_session(session_data, messages):
    """Sohbet oturumunu TXT formatında oluştur"""
    buffer = io.StringIO()
    
    # Başlık
    buffer.write("🤖 AI Chatbot - Sohbet Raporu\n")
    buffer.write("=" * 50 + "\n\n")
    
    # Oturum bilgileri
    buffer.write(f"Oturum Adı: {session_data['session_name']}\n")
    buffer.write(f"Oluşturulma: {session_data['created_at']}\n")
    buffer.write(f"Son Güncelleme: {session_data['updated_at']}\n")
    buffer.write(f"Toplam Mesaj: {len(messages)}\n")
    buffer.write("-" * 50 + "\n\n")
    
    # Mesajlar
    for i, msg in enumerate(messages):
        role = "👤 Kullanıcı" if msg['role'] == 'user' else "🤖 AI Asistan"
        content = msg['content']
        timestamp = msg['timestamp']
        
        buffer.write(f"[{timestamp}] {role}:\n")
        buffer.write(f"{content}\n")
        buffer.write("-" * 30 + "\n\n")
    
    buffer.seek(0)
    return buffer

# Token sayımı fonksiyonları
def get_token_count(text, model="llama3-8b-8192"):
    """Metindeki token sayısını hesapla"""
    try:
        # Model için uygun encoding'i seç
        if "llama" in model.lower():
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding (Llama için de kullanılır)
        elif "gpt" in model.lower():
            encoding = tiktoken.get_encoding("cl100k_base")
        else:
            encoding = tiktoken.get_encoding("cl100k_base")  # Varsayılan
        
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Token sayımı hatası: {e}")
        # Hata durumunda yaklaşık hesaplama (1 token ≈ 4 karakter)
        return len(text) // 4

def check_token_limit(messages, max_tokens, model="llama3-8b-8192"):
    """Token limitini kontrol et ve uyarı ver"""
    try:
        # Tüm mesajları birleştir
        full_text = ""
        for msg in messages:
            full_text += msg.get('content', '') + "\n"
        
        # Mevcut token sayısını hesapla
        current_tokens = get_token_count(full_text, model)
        
        # Model limitlerini tanımla (yaklaşık değerler)
        model_limits = {
            "llama3-8b-8192": 8192,
            "llama3.1-70b-8192": 8192,
            "llama3.1-405b-8192": 8192,
            "mixtral-8x7b-32768": 32768,
            "gemma-7b-it": 8192,
            "llama-3.1-8b-instant": 131072,
            "llama-3.3-70b-versatile": 131072,
            "qwen/qwen3-32b": 32768,
            "moonshotai/kimi-k2-instruct": 32768,
            "gemma2-9b-it": 8192
        }
        
        # Model limitini al (varsayılan: 8192)
        model_limit = model_limits.get(model, 8192)
        
        # Kullanılabilir token sayısı
        available_tokens = model_limit - current_tokens
        
        # Uyarı seviyeleri
        warning_level = "safe"
        warning_message = ""
        
        if available_tokens < max_tokens:
            warning_level = "critical"
            warning_message = f"⚠️ Token limiti aşıldı! Mevcut: {current_tokens}, Limit: {model_limit}, İstenen: {max_tokens}"
        elif available_tokens < max_tokens * 1.5:
            warning_level = "warning"
            warning_message = f"⚠️ Token limiti yaklaşıyor! Kalan: {available_tokens}, İstenen: {max_tokens}"
        elif available_tokens < max_tokens * 2:
            warning_level = "info"
            warning_message = f"ℹ️ Token durumu: {available_tokens} kullanılabilir"
        
        return {
            "current_tokens": current_tokens,
            "model_limit": model_limit,
            "available_tokens": available_tokens,
            "warning_level": warning_level,
            "warning_message": warning_message,
            "can_proceed": available_tokens >= max_tokens
        }
        
    except Exception as e:
        print(f"Token limit kontrolü hatası: {e}")
        return {
            "current_tokens": 0,
            "model_limit": 8192,
            "available_tokens": 8192,
            "warning_level": "error",
            "warning_message": f"Token hesaplama hatası: {str(e)}",
            "can_proceed": True  # Hata durumunda devam et
        }

# Kullanıcı kimlik doğrulama decorator'ı
def require_auth(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/register', methods=['POST'])
def register():
    """Kullanıcı kaydı"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            
            # Kullanıcı ID'sini al
            user_id = cursor.lastrowid
            
            conn.close()
            
            # Session'a kullanıcı bilgilerini kaydet
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                'message': 'Registration successful',
                'user_id': user_id,
                'username': username
            })
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username already exists'}), 409
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        user = cursor.fetchone()
        
        if user:
            user_id, username = user
            
            # Son giriş zamanını güncelle
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            # Session'a kullanıcı bilgilerini kaydet
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                'message': 'Login successful',
                'user_id': user_id,
                'username': username
            })
        else:
            conn.close()
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Kullanıcı çıkışı"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/user', methods=['GET'])
@require_auth
def get_user_info():
    """Kullanıcı bilgilerini getir"""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    })

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    try:
        print("DEBUG: Chat endpoint çağrıldı")
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = session['user_id']
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Yeni session oluştur (eğer session_id yoksa)
        if not session_id:
            session_id = str(uuid.uuid4())
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_sessions (session_id, user_id, session_name) VALUES (?, ?, ?)',
                (session_id, user_id, f"Sohbet {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            )
            conn.commit()
            conn.close()
        else:
            # Session'ın bu kullanıcıya ait olduğunu kontrol et
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_id FROM chat_sessions WHERE session_id = ?',
                (session_id,)
            )
            session_user = cursor.fetchone()
            conn.close()
            
            if not session_user or session_user[0] != user_id:
                return jsonify({'error': 'Access denied to this session'}), 403
        
        # Streamlit'ten gelen parametreleri al (varsayılan değerlerle)
        model = data.get('model', 'llama3-8b-8192')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        system_message = data.get('system_message', '')  # Sistem mesajı
        
        # Sohbet geçmişini al (son 20 mesaj ile sınırla)
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT 20',
            (session_id,)
        )
        chat_history = cursor.fetchall()
        
        # Groq API için mesaj formatını hazırla
        messages = []
        
        # Sistem mesajını ekle (eğer varsa)
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Chat geçmişini ekle
        for role, content in chat_history:
            messages.append({"role": role, "content": content})
        
        # Debug için mesaj sayısını logla
        print(f"Session {session_id}: {len(messages)} messages in history")
        for i, msg in enumerate(messages):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
        
        # Dil algılama sistemi (güvenilir)
        def detect_language_advanced(text):
            text = text.lower().strip()
            
            # Önce kesin eşleşmeleri kontrol et
            exact_matches = {
                'merhaba': 'tr', 'selam': 'tr', 'nasılsın': 'tr', 'naber': 'tr', 'iyiyim': 'tr', 'iyi': 'tr', 'güzel': 'tr', 'teşekkür': 'tr', 'ediyorum': 'tr', 'ediyor': 'tr', 'var': 'tr', 'yok': 'tr', 'evet': 'tr', 'hayır': 'tr', 'tamam': 'tr', 'olur': 'tr', 'güzel': 'tr', 'kötü': 'tr', 'fena': 'tr', 'değil': 'tr', 'çok': 'tr', 'az': 'tr', 'biraz': 'tr', 'şey': 'tr', 'bu': 'tr', 'şu': 'tr', 'o': 'tr', 'ben': 'tr', 'sen': 'tr', 'biz': 'tr', 'siz': 'tr', 'onlar': 'tr', 'anlamadım': 'tr', 'diyorsun': 'tr', 'ne': 'tr', 'diyor': 'tr',
                'hallo': 'de', 'guten': 'de', 'tag': 'de', 'danke': 'de', 'bitte': 'de', 'kannst': 'de', 'du': 'de', 'mir': 'de', 'die': 'de', 'aber': 'de', 'original': 'de',
                'hola': 'es', 'buenos': 'es', 'días': 'es', 'gracias': 'es', 'por': 'es',
                'hello': 'en', 'hi': 'en', 'how': 'en', 'are': 'en', 'you': 'en',
                'bonjour': 'fr', 'salut': 'fr', 'comment': 'fr', 'ça': 'fr', 'va': 'fr',
                'ciao': 'it', 'come': 'it', 'stai': 'it', 'bene': 'it', 'grazie': 'it',
                'olá': 'pt', 'como': 'pt', 'está': 'pt', 'obrigado': 'pt', 'por': 'pt',
                'привет': 'ru', 'как': 'ru', 'дела': 'ru', 'хорошо': 'ru', 'спасибо': 'ru',
                'こんにちは': 'ja', 'おはよう': 'ja', 'ありがとう': 'ja', 'はい': 'ja', 'いいえ': 'ja',
                '안녕하세요': 'ko', '안녕': 'ko', '감사합니다': 'ko', '네': 'ko', '아니요': 'ko',
                '你好': 'zh', '谢谢': 'zh', '是的': 'zh', '不是': 'zh', '再见': 'zh',
                'مرحبا': 'ar', 'شكرا': 'ar', 'نعم': 'ar', 'لا': 'ar', 'كيف': 'ar'
            }
            
            # Kelime bazında kontrol
            words = text.split()
            for word in words:
                if word in exact_matches:
                    detected_lang = exact_matches[word]
                    print(f"Exact match found: '{word}' -> {detected_lang}")
                    return detected_lang
            
            # Karakter bazında kontrol
            turkish_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']
            german_chars = ['ä', 'ö', 'ü', 'ß']
            
            turkish_char_count = sum(1 for char in text if char in turkish_chars)
            german_char_count = sum(1 for char in text if char in german_chars)
            
            if turkish_char_count > 0:
                print(f"Turkish characters found: {turkish_char_count}")
                return 'tr'
            elif german_char_count > 0:
                print(f"German characters found: {german_char_count}")
                return 'de'
            
            # LangDetect'i son çare olarak kullan
            try:
                import langdetect
                from langdetect import detect, DetectorFactory
                DetectorFactory.seed = 0
                detected_lang = detect(text)
                print(f"LangDetect result: {detected_lang}")
                return detected_lang
            except Exception as e:
                print(f"LangDetect error: {e}")
                return 'en'  # Varsayılan İngilizce
        
        # Son kullanıcı mesajının dilini algıla
        detected_lang = detect_language_advanced(user_message)
        print(f"Detected language: {detected_lang} for message: {user_message[:50]}...")
        
        # Kullanıcı mesajını veritabanına kaydet
        cursor.execute(
            'INSERT INTO messages (session_id, role, content, model, temperature, max_tokens) VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, 'user', user_message, model, temperature, max_tokens)
        )
        conn.commit()
        
        # Dil algılamasına göre kullanıcı mesajını güncelle
        if detected_lang == 'tr':
            enhanced_user_message = f"""[Sen Türkçe konuşan bir AI asistanısın. Basit ve doğal Türkçe ile yanıt ver.

Kullanıcının mesajı: {user_message}

Türkçe olarak yanıtla:]"""
        elif detected_lang == 'de':
            enhanced_user_message = f"""[Du bist ein KI-Assistent, der Deutsch spricht. Befolge diese Regeln strikt:

1. KORREKTES DEUTSCH: Verwende korrekte deutsche Grammatik und Rechtschreibung
2. DEUTSCHE ZEICHEN: Verwende ä, ö, ü, ß korrekt
3. SINNVOLLE ANTWORTEN: Gib logische, konsistente und verständliche Antworten
4. NATÜRLICHE SPRACHE: Verwende natürliches, alltägliches Deutsch
5. FOKUSSIERT: Antworte NUR auf die gestellte Frage, nicht auf frühere Themen
6. KEINE WIEDERHOLUNGEN: Wiederhole nicht unnötig dieselben Dinge
7. FLÜSSIGE SÄTZE: Verwende kurze, klare Sätze statt zu langer, komplexer Sätze
8. THEMA FOKUS: Sprich nur über das aktuelle Thema, nicht über vorherige Gespräche
9. KEINE FEHLERHAFTEN WÖRTER: Verwende keine sinnlosen oder falschen Wörter

Benutzer-Nachricht: {user_message}

Antworte auf Deutsch:]"""
        elif detected_lang == 'es':
            enhanced_user_message = f"""[Eres un asistente de IA que habla español. Sigue estas reglas estrictamente:

1. ESPAÑOL CORRECTO: Usa gramática y ortografía española correcta
2. CARACTERES ESPAÑOLES: Usa ñ, á, é, í, ó, ú, ü correctamente
3. RESPUESTAS SIGNIFICATIVAS: Da respuestas lógicas, consistentes y comprensibles
4. LENGUAJE NATURAL: Usa español natural y cotidiano
5. ENFOQUE: Responde directamente y con precisión a la pregunta
6. SIN REPETICIONES: No repitas innecesariamente las mismas cosas
7. ORACIONES FLUIDAS: Usa oraciones cortas y claras en lugar de oraciones largas y complejas

Mensaje del usuario: {user_message}

Responde en español:]"""
        elif detected_lang == 'fr':
            enhanced_user_message = f"""[Tu es un assistant IA qui parle français. Suis ces règles strictement:

1. FRANÇAIS CORRECT: Utilise une grammaire et une orthographe françaises correctes
2. CARACTÈRES FRANÇAIS: Utilise é, è, ê, ë, à, â, ï, î, ô, û, ù, ü, ç correctement
3. RÉPONSES SIGNIFICATIVES: Donne des réponses logiques, cohérentes et compréhensibles
4. LANGAGE NATUREL: Utilise un français naturel et quotidien
5. FOCUS: Réponds directement et précisément à la question
6. SANS RÉPÉTITIONS: Ne répète pas inutilement les mêmes choses
7. PHRASES FLUIDES: Utilise des phrases courtes et claires au lieu de phrases longues et complexes

Message de l'utilisateur: {user_message}

Réponds en français:]"""
        elif detected_lang == 'it':
            enhanced_user_message = f"""[Sei un assistente IA che parla italiano. Segui queste regole rigorosamente:

1. ITALIANO CORRETTO: Usa grammatica e ortografia italiana corretta
2. CARATTERI ITALIANI: Usa à, è, é, ì, ò, ù correttamente
3. RISPOSTE SIGNIFICATIVE: Dai risposte logiche, coerenti e comprensibili
4. LINGUAGGIO NATURALE: Usa italiano naturale e quotidiano
5. FOCUS: Rispondi direttamente e precisamente alla domanda
6. SENZA RIPETIZIONI: Non ripetere inutilmente le stesse cose
7. FRASI FLUIDE: Usa frasi brevi e chiare invece di frasi lunghe e complesse

Messaggio dell'utente: {user_message}

Rispondi in italiano:]"""
        elif detected_lang == 'pt':
            enhanced_user_message = f"""[Você é um assistente de IA que fala português. Siga estas regras estritamente:

1. PORTUGUÊS CORRETO: Use gramática e ortografia portuguesa correta
2. CARACTERES PORTUGUESES: Use ã, õ, ç, á, é, í, ó, ú corretamente
3. RESPOSTAS SIGNIFICATIVAS: Dê respostas lógicas, consistentes e compreensíveis
4. LINGUAGEM NATURAL: Use português natural e cotidiano
5. FOCO: Responda diretamente e precisamente à pergunta
6. SEM REPETIÇÕES: Não repita desnecessariamente as mesmas coisas
7. FRASES FLUIDAS: Use frases curtas e claras em vez de frases longas e complexas

Mensagem do usuário: {user_message}

Responda em português:]"""
        elif detected_lang == 'ru':
            enhanced_user_message = f"""[Вы - ИИ-ассистент, который говорит по-русски. Следуйте этим правилам строго:

1. ПРАВИЛЬНЫЙ РУССКИЙ: Используйте правильную русскую грамматику и орфографию
2. РУССКИЕ БУКВЫ: Используйте ё, й, ъ, ь, э, ю, я правильно
3. ОСМЫСЛЕННЫЕ ОТВЕТЫ: Давайте логичные, последовательные и понятные ответы
4. ЕСТЕСТВЕННЫЙ ЯЗЫК: Используйте естественный, повседневный русский
5. ФОКУС: Отвечайте прямо и точно на вопрос
6. БЕЗ ПОВТОРЕНИЙ: Не повторяйте ненужно одни и те же вещи
7. ПЛАВНЫЕ ПРЕДЛОЖЕНИЯ: Используйте короткие, ясные предложения вместо длинных и сложных

Сообщение пользователя: {user_message}

Отвечайте на русском языке:]"""
        elif detected_lang == 'ja':
            enhanced_user_message = f"""[あなたは日本語を話すAIアシスタントです。以下のルールを厳守してください：

1. 正しい日本語: 正しい日本語の文法と表記を使用する
2. 日本語文字: ひらがな、カタカナ、漢字を適切に使用する
3. 意味のある回答: 論理的で一貫性があり理解しやすい回答を提供する
4. 自然な言語: 自然で日常的な日本語を使用する
5. 焦点: 質問に直接的に正確に答える
6. 繰り返しなし: 同じことを不必要に繰り返さない
7. 流暢な文章: 長く複雑な文章ではなく、短く明確な文章を使用する

ユーザーのメッセージ: {user_message}

日本語で答えてください:]"""
        elif detected_lang == 'ko':
            enhanced_user_message = f"""[당신은 한국어를 구사하는 AI 어시스턴트입니다. 다음 규칙을 엄격히 따르세요:

1. 올바른 한국어: 올바른 한국어 문법과 맞춤법을 사용하세요
2. 한국어 문자: 한글, 한자를 적절히 사용하세요
3. 의미 있는 답변: 논리적이고 일관성 있으며 이해하기 쉬운 답변을 제공하세요
4. 자연스러운 언어: 자연스럽고 일상적인 한국어를 사용하세요
5. 집중: 질문에 직접적이고 정확하게 답변하세요
6. 반복 없음: 같은 것을 불필요하게 반복하지 마세요
7. 유창한 문장: 길고 복잡한 문장보다는 짧고 명확한 문장을 사용하세요

사용자 메시지: {user_message}

한국어로 답변하세요:]"""
        elif detected_lang == 'zh':
            enhanced_user_message = f"""[你是一个会说中文的AI助手。请严格遵守以下规则：

1. 正确的中文：使用正确的中文语法和书写
2. 中文字符：正确使用简体字或繁体字
3. 有意义的回答：提供逻辑性、一致性和易懂的回答
4. 自然语言：使用自然、日常的中文
5. 重点：直接准确地回答问题
6. 无重复：不要不必要地重复相同的内容
7. 流畅句子：使用简短清晰的句子而不是长而复杂的句子

用户消息：{user_message}

请用中文回答:]"""
        elif detected_lang == 'ar':
            enhanced_user_message = f"""[أنت مساعد ذكاء اصطناعي يتحدث العربية. اتبع هذه القواعد بدقة:

1. العربية الصحيحة: استخدم قواعد النحو والإملاء العربية الصحيحة
2. الحروف العربية: استخدم الحروف العربية بشكل صحيح
3. إجابات ذات معنى: قدم إجابات منطقية ومتسقة ومفهومة
4. لغة طبيعية: استخدم العربية الطبيعية واليومية
5. التركيز: أجب مباشرة وبشكل دقيق على السؤال
6. بدون تكرار: لا تكرر نفس الأشياء بشكل غير ضروري
7. جمل سلسة: استخدم جمل قصيرة وواضحة بدلاً من جمل طويلة ومعقدة

رسالة المستخدم: {user_message}

أجب باللغة العربية:]"""
        elif detected_lang == 'hi':
            enhanced_user_message = f"[आप एक AI सहायक हैं जो हिंदी बोलते हैं। उपयोगकर्ता के संदेश का जवाब हिंदी में दें।] {user_message}"
        elif detected_lang == 'nl':
            enhanced_user_message = f"[Je bent een AI-assistent die Nederlands spreekt. Antwoord op het bericht van de gebruiker in het Nederlands.] {user_message}"
        elif detected_lang == 'pl':
            enhanced_user_message = f"[Jesteś asystentem AI, który mówi po polsku. Odpowiedz na wiadomość użytkownika po polsku.] {user_message}"
        elif detected_lang == 'sv':
            enhanced_user_message = f"[Du är en AI-assistent som talar svenska. Svara på användarens meddelande på svenska.] {user_message}"
        elif detected_lang == 'da':
            enhanced_user_message = f"[Du er en AI-assistent, der taler dansk. Svar på brugerens besked på dansk.] {user_message}"
        elif detected_lang == 'no':
            enhanced_user_message = f"[Du er en AI-assistent som snakker norsk. Svar på brukerens melding på norsk.] {user_message}"
        elif detected_lang == 'fi':
            enhanced_user_message = f"[Olet AI-avustaja, joka puhuu suomea. Vastaa käyttäjän viestiin suomeksi.] {user_message}"
        elif detected_lang == 'hu':
            enhanced_user_message = f"[Te egy AI asszisztens vagy, aki magyarul beszél. Válaszolj a felhasználó üzenetére magyarul.] {user_message}"
        elif detected_lang == 'cs':
            enhanced_user_message = f"[Jste AI asistent, který mluví česky. Odpovězte na zprávu uživatele česky.] {user_message}"
        elif detected_lang == 'ro':
            enhanced_user_message = f"[Ești un asistent AI care vorbește română. Răspunde la mesajul utilizatorului în română.] {user_message}"
        elif detected_lang == 'bg':
            enhanced_user_message = f"[Вие сте AI асистент, който говори български. Отговорете на съобщението на потребителя на български.] {user_message}"
        elif detected_lang == 'hr':
            enhanced_user_message = f"[Vi ste AI asistent koji govori hrvatski. Odgovorite na korisnikovu poruku na hrvatskom.] {user_message}"
        elif detected_lang == 'sk':
            enhanced_user_message = f"[Ste AI asistent, ktorý hovorí slovensky. Odpovedzte na správu používateľa po slovensky.] {user_message}"
        elif detected_lang == 'sl':
            enhanced_user_message = f"[Vi ste AI asistent, ki govori slovensko. Odgovorite na sporočilo uporabnika v slovenščini.] {user_message}"
        elif detected_lang == 'et':
            enhanced_user_message = f"[Oled AI assistent, kes räägib eesti keelt. Vasta kasutaja sõnumile eesti keeles.] {user_message}"
        elif detected_lang == 'lv':
            enhanced_user_message = f"[Jūs esat AI asistents, kurš runā latviešu valodā. Atbildiet uz lietotāja ziņojumu latviešu valodā.] {user_message}"
        elif detected_lang == 'lt':
            enhanced_user_message = f"[Jūs esate AI asistentas, kuris kalba lietuvių kalba. Atsakykite į vartotojo žinutę lietuvių kalba.] {user_message}"
        elif detected_lang == 'mt':
            enhanced_user_message = f"[Inti assistent AI li jitkellem bil-Malti. Irrispondi lill-messaġġ tal-utent bil-Malti.] {user_message}"
        elif detected_lang == 'ga':
            enhanced_user_message = f"[Is cúntóir AI tú a labhraíonn Gaeilge. Freagair teachtaireacht an úsáideora as Gaeilge.] {user_message}"
        elif detected_lang == 'cy':
            enhanced_user_message = f"[Rydych chi'n cynorthwyydd AI sy'n siarad Cymraeg. Atebwch neges y defnyddiwr yn Gymraeg.] {user_message}"
        elif detected_lang == 'eu':
            enhanced_user_message = f"[Euskara hitz egiten duen AI laguntzailea zara. Erantzun erabiltzailearen mezua euskaraz.] {user_message}"
        elif detected_lang == 'ca':
            enhanced_user_message = f"[Ets un assistent d'IA que parla català. Respon al missatge de l'usuari en català.] {user_message}"
        elif detected_lang == 'gl':
            enhanced_user_message = f"[Es un asistente de IA que fala galego. Responde á mensaxe do usuario en galego.] {user_message}"
        elif detected_lang == 'is':
            enhanced_user_message = f"[Þú ert AI aðstoðarmaður sem talar íslensku. Svaraðu skilaboðum notandans á íslensku.] {user_message}"
        elif detected_lang == 'mk':
            enhanced_user_message = f"[Вие сте AI асистент кој зборува македонски. Одговорете на пораката на корисникот на македонски.] {user_message}"
        elif detected_lang == 'sq':
            enhanced_user_message = f"[Ju jeni një asistent AI që flet shqip. Përgjigjuni mesazhit të përdoruesit në shqip.] {user_message}"
        elif detected_lang == 'sr':
            enhanced_user_message = f"[Ви сте AI асистент који говори српски. Одговорите на поруку корисника на српском.] {user_message}"
        elif detected_lang == 'bs':
            enhanced_user_message = f"[Vi ste AI asistent koji govori bosanski. Odgovorite na poruku korisnika na bosanskom.] {user_message}"
        elif detected_lang == 'me':
            enhanced_user_message = f"[Vi ste AI asistent koji govori crnogorski. Odgovorite na poruku korisnika na crnogorskom.] {user_message}"
        elif detected_lang == 'uk':
            enhanced_user_message = f"[Ви - ІІ-асистент, який говорить українською. Відповідайте на повідомлення користувача українською мовою.] {user_message}"
        elif detected_lang == 'be':
            enhanced_user_message = f"[Вы - ІІ-асістэнт, які размаўляе па-беларуску. Адкажыце на паведамленне карыстальніка па-беларуску.] {user_message}"
        elif detected_lang == 'kk':
            enhanced_user_message = f"[Сіз қазақ тілінде сөйлейтін AI көмекшісісіз. Пайдаланушының хабарламасына қазақ тілінде жауап беріңіз.] {user_message}"
        elif detected_lang == 'ky':
            enhanced_user_message = f"[Сиз кыргыз тилинде сүйлөгөн AI жардамчысысыз. Колдонуучунун билдирүүсүнө кыргыз тилинде жооп бериңиз.] {user_message}"
        elif detected_lang == 'uz':
            enhanced_user_message = f"[Siz o'zbek tilida gapiruvchi AI yordamchisisiz. Foydalanuvchining xabariga o'zbek tilida javob bering.] {user_message}"
        elif detected_lang == 'tg':
            enhanced_user_message = f"[Шумо AI ёрдамчи ҳастед, ки тоҷикӣ гап мезанед. Ба пайғоми корбар ба тоҷикӣ ҷавоб диҳед.] {user_message}"
        elif detected_lang == 'mn':
            enhanced_user_message = f"[Та бол Монгол хэлээр ярьдагч AI туслах юм. Хэрэглэгчийн мессежид Монгол хэлээр хариулна уу.] {user_message}"
        elif detected_lang == 'ka':
            enhanced_user_message = f"[თქვენ ხართ AI ასისტენტი, რომელიც ქართულად საუბრობს. უპასუხეთ მომხმარებლის შეტყობინებას ქართულად.] {user_message}"
        elif detected_lang == 'hy':
            enhanced_user_message = f"[Դուք AI օգնական եք, ով խոսում է հայերեն: Պատասխանեք օգտագործողի հաղորդագրությանը հայերենով:] {user_message}"
        elif detected_lang == 'az':
            enhanced_user_message = f"[Siz Azərbaycan dilində danışan AI köməkçisisiniz. İstifadəçinin mesajına Azərbaycan dilində cavab verin.] {user_message}"
        elif detected_lang == 'fa':
            enhanced_user_message = f"[شما یک دستیار هوش مصنوعی هستید که فارسی صحبت می‌کند. به پیام کاربر به فارسی پاسخ دهید.] {user_message}"
        elif detected_lang == 'ur':
            enhanced_user_message = f"[آپ ایک AI اسسٹنٹ ہیں جو اردو بولتے ہیں۔ صارف کے پیغام کا جواب اردو میں دیں۔] {user_message}"
        elif detected_lang == 'bn':
            enhanced_user_message = f"[আপনি একজন AI সহকারী যিনি বাংলা বলেন। ব্যবহারকারীর বার্তার উত্তর বাংলায় দিন।] {user_message}"
        elif detected_lang == 'ta':
            enhanced_user_message = f"[நீங்கள் தமிழில் பேசும் AI உதவியாளர். பயனரின் செய்திக்கு தமிழில் பதிலளிக்கவும்.] {user_message}"
        elif detected_lang == 'te':
            enhanced_user_message = f"[మీరు తెలుగులో మాట్లాడే AI సహాయకుడు. వినియోగదారు సందేశానికి తెలుగులో సమాధానం ఇవ్వండి.] {user_message}"
        elif detected_lang == 'kn':
            enhanced_user_message = f"[ನೀವು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುವ AI ಸಹಾಯಕ. ಬಳಕೆದಾರರ ಸಂದೇಶಕ್ಕೆ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.] {user_message}"
        elif detected_lang == 'ml':
            enhanced_user_message = f"[നിങ്ങൾ മലയാളത്തിൽ സംസാരിക്കുന്ന AI സഹായിയാണ്. ഉപയോക്താവിന്റെ സന്ദേശത്തിന് മലയാളത്തിൽ മറുപടി നൽകുക.] {user_message}"
        elif detected_lang == 'gu':
            enhanced_user_message = f"[તમે ગુજરાતીમાં બોલતા AI સહાયક છો. વપરાશકર્તાના સંદેશનો જવાબ ગુજરાતીમાં આપો.] {user_message}"
        elif detected_lang == 'pa':
            enhanced_user_message = f"[ਤੁਸੀਂ ਪੰਜਾਬੀ ਵਿੱਚ ਬੋਲਣ ਵਾਲੇ AI ਸਹਾਇਕ ਹੋ। ਉਪਭੋਗਤਾ ਦੇ ਸੁਨੇਹੇ ਦਾ ਜਵਾਬ ਪੰਜਾਬੀ ਵਿੱਚ ਦਿਓ।] {user_message}"
        elif detected_lang == 'or':
            enhanced_user_message = f"[ଆପଣ ଓଡ଼ିଆରେ କଥା ହେଉଥିବା AI ସହାୟକ। ବ୍ୟବହାରକାରୀର ବାର୍ତ୍ତାର ଉତ୍ତର ଓଡ଼ିଆରେ ଦିଅନ୍ତୁ।] {user_message}"
        elif detected_lang == 'as':
            enhanced_user_message = f"[আপুনি অসমীয়াত কথা কোৱা AI সহায়ক। ব্যৱহাৰকাৰীৰ বাৰ্তাৰ উত্তৰ অসমীয়াত দিয়ক।] {user_message}"
        elif detected_lang == 'ne':
            enhanced_user_message = f"[तपाईं नेपाली बोल्ने AI सहायक हुनुहुन्छ। प्रयोगकर्ताको सन्देशको जवाफ नेपालीमा दिनुहोस्।] {user_message}"
        elif detected_lang == 'si':
            enhanced_user_message = f"[ඔබ සිංහලෙන් කතා කරන AI සහායකයෙකි. පරිශීලකයාගේ පණිවිඩයට සිංහලෙන් පිළිතුරු දෙන්න.] {user_message}"
        elif detected_lang == 'my':
            enhanced_user_message = f"[သင်သည် မြန်မာဘာသာဖြင့် ပြောဆိုသော AI လက်ထောက်ဖြစ်သည်။ အသုံးပြုသူ၏ မက်ဆေ့ခ်ျကို မြန်မာဘာသာဖြင့် ဖြေကြားပါ။] {user_message}"
        elif detected_lang == 'km':
            enhanced_user_message = f"[អ្នកគឺជា AI ជំនួយការដែលនិយាយភាសាខ្មែរ។ ឆ្លើយតបទៅកាន់សាររបស់អ្នកប្រើប្រាស់ជាភាសាខ្មែរ។] {user_message}"
        elif detected_lang == 'lo':
            enhanced_user_message = f"[ທ່ານເປັນ AI ຜູ້ຊ່ວຍທີ່ເວົ້າພາສາລາວ. ຕອບກັບຂໍ້ຄວາມຂອງຜູ້ໃຊ້ເປັນພາສາລາວ.] {user_message}"
        elif detected_lang == 'th':
            enhanced_user_message = f"[คุณเป็น AI ผู้ช่วยที่พูดภาษาไทย ตอบข้อความของผู้ใช้เป็นภาษาไทย] {user_message}"
        elif detected_lang == 'vi':
            enhanced_user_message = f"[Bạn là trợ lý AI nói tiếng Việt. Trả lời tin nhắn của người dùng bằng tiếng Việt.] {user_message}"
        elif detected_lang == 'id':
            enhanced_user_message = f"[Anda adalah asisten AI yang berbicara bahasa Indonesia. Jawab pesan pengguna dalam bahasa Indonesia.] {user_message}"
        elif detected_lang == 'ms':
            enhanced_user_message = f"[Anda adalah pembantu AI yang bercakap bahasa Melayu. Jawab mesej pengguna dalam bahasa Melayu.] {user_message}"
        elif detected_lang == 'tl':
            enhanced_user_message = f"[Ikaw ay isang AI assistant na nagsasalita ng Tagalog. Sagutin ang mensahe ng user sa Tagalog.] {user_message}"
        elif detected_lang == 'ceb':
            enhanced_user_message = f"[Ikaw usa ka AI assistant nga nagsulti og Cebuano. Tubaga ang mensahe sa user sa Cebuano.] {user_message}"
        elif detected_lang == 'jv':
            enhanced_user_message = f"[Sampeyan kuwi asisten AI sing ngomong basa Jawa. Jawab pesen pangguna nganggo basa Jawa.] {user_message}"
        elif detected_lang == 'su':
            enhanced_user_message = f"[Anjeun mangrupikeun asisten AI anu nyarios basa Sunda. Waeh pesen pangguna dina basa Sunda.] {user_message}"
        elif detected_lang == 'sw':
            enhanced_user_message = f"[Wewe ni msaidizi wa AI anayezungumza Kiswahili. Jibu ujumbe wa mtumiaji kwa Kiswahili.] {user_message}"
        elif detected_lang == 'am':
            enhanced_user_message = f"[እርስዎ አማርኛ የሚናገር AI አገልግሎት ነዎት። የተጠቃሚውን መልእክት በአማርኛ ይመልሱ።] {user_message}"
        elif detected_lang == 'ha':
            enhanced_user_message = f"[Kai ne AI mataimaki wanda ke magana da Hausa. Amsa sakon mai amfani da Hausa.] {user_message}"
        elif detected_lang == 'yo':
            enhanced_user_message = f"[O jẹ́ olùrànlọ́wọ́ AI tí ó ń sọ èdè Yorùbá. Dáhùn ìfiranṣẹ́ olùlo èdè Yorùbá.] {user_message}"
        elif detected_lang == 'ig':
            enhanced_user_message = f"[Ị bụ onye enyemaka AI na-asụ Igbo. Zaa ozi onye ọrụ na Igbo.] {user_message}"
        elif detected_lang == 'zu':
            enhanced_user_message = f"[Ungumxhashe we-AI okhuluma isiZulu. Phendula umyalezo womsebenzisi ngesiZulu.] {user_message}"
        elif detected_lang == 'xh':
            enhanced_user_message = f"[Ungumxhasi we-AI okhuluma isiXhosa. Phendula umyalezo womsebenzisi ngesiXhosa.] {user_message}"
        elif detected_lang == 'af':
            enhanced_user_message = f"[Jy is 'n AI-assistent wat Afrikaans praat. Antwoord op die gebruiker se boodskap in Afrikaans.] {user_message}"
        elif detected_lang == 'st':
            enhanced_user_message = f"[U mokhanni wa AI ya buang le Sesotho. Araba molaetsa wa mosebedisi ka Sesotho.] {user_message}"
        elif detected_lang == 'tn':
            enhanced_user_message = f"[O le mothusi wa AI yo buang Setswana. Araba molaetsa wa mosebedisi ka Setswana.] {user_message}"
        elif detected_lang == 'ss':
            enhanced_user_message = f"[Ungumxhashe we-AI okhuluma siSwati. Phendula umyalezo womsebenzisi ngesiSwati.] {user_message}"
        elif detected_lang == 've':
            enhanced_user_message = f"[Ndi muthu u thusaho wa AI u amba Tshivenda. Fhindula ndaela ya muthu u shumisa nga Tshivenda.] {user_message}"
        elif detected_lang == 'ts':
            enhanced_user_message = f"[U muthu u thusaho wa AI u amba Xitsonga. Fhindula ndaela ya muthu u shumisa nga Xitsonga.] {user_message}"
        elif detected_lang == 'nd':
            enhanced_user_message = f"[Ungumxhashe we-AI okhuluma isiNdebele. Phendula umyalezo womsebenzisi ngesiNdebele.] {user_message}"
        elif detected_lang == 'sn':
            enhanced_user_message = f"[Uri mubatsiri weAI unotaura chiShona. Pindura meseji yemushandisi nechiShona.] {user_message}"
        elif detected_lang == 'rw':
            enhanced_user_message = f"[Uri umufasha wa AI uvuga Ikinyarwanda. Subiza ubutumwa bw'umukoresha mu Kinyarwanda.] {user_message}"
        elif detected_lang == 'ak':
            enhanced_user_message = f"[Wo yɛ AI boafo a ɔka Akan. Fa Akan hyɛ asɛm a ɔde ma no so.] {user_message}"
        elif detected_lang == 'tw':
            enhanced_user_message = f"[Wo yɛ AI boafo a ɔka Twi. Fa Twi hyɛ asɛm a ɔde ma no so.] {user_message}"
        elif detected_lang == 'ee':
            enhanced_user_message = f"[Wò nyɛ AI kpekpeɖeŋutsu si gblɔ Eʋegbe. Ɖe Eʋegbe ɖe gbeɖeɖe si wòɖe ɖe wò ŋutsu la ta.] {user_message}"
        elif detected_lang == 'lg':
            enhanced_user_message = f"[Oli mukozi wa AI eyogera Oluganda. Ddamu obubaka bw'omukozesa mu Luganda.] {user_message}"
        elif detected_lang == 'ny':
            enhanced_user_message = f"[Iwe ndi AI wothandizira amene amalankhula Chichewa. Yankhulani uthenga wa wogwiritsa ntchito mu Chichewa.] {user_message}"
        elif detected_lang == 'mg':
            enhanced_user_message = f"[Hianao no mpanampy AI miteny Malagasy. Valio ny hafatra an'ny mpampiasa amin'ny teny Malagasy.] {user_message}"
        elif detected_lang == 'so':
            enhanced_user_message = f"[Waxaad tahay caawiyaha AI ee ku hadla Soomaali. Ka jawaab fariinta isticmaalaha afka Soomaaliga.] {user_message}"
        elif detected_lang == 'om':
            enhanced_user_message = f"[Ati gargaara AI kan afaan Oromoo dubbatu. Deebii barruu fayyadamaa afaan Oromootiin kenni.] {user_message}"
        elif detected_lang == 'ti':
            enhanced_user_message = f"[ንስኻ ብትግርኛ ዘዛረብ AI ሓጋዚ ኢኻ። መልእክቲ ተጠቃሚ ብትግርኛ ምላሽ ሃብ።] {user_message}"
        elif detected_lang == 'he':
            enhanced_user_message = f"[אתה עוזר AI שמדבר עברית. ענה להודעת המשתמש בעברית.] {user_message}"
        elif detected_lang == 'yi':
            enhanced_user_message = f"[איר זענט אַן AI אַסיסטאַנט וואָס רעדט יידיש. ענטפערט צו דער באַניצער ס אָנזאָג אין יידיש.] {user_message}"
        elif detected_lang == 'lb':
            enhanced_user_message = f"[Dir sidd en AI Assistent deen Lëtzebuergesch schwätzt. Äntwert op d'Benotzer seng Noriicht op Lëtzebuergesch.] {user_message}"
        elif detected_lang == 'fo':
            enhanced_user_message = f"[Tú ert ein AI hjálpar, ið talar føroyskt. Svara brúkarans boðskapi á føroyskum.] {user_message}"
        elif detected_lang == 'kl':
            enhanced_user_message = f"[Illit AI-iliuinnarpoq kalaallisut oqaluttuarpoq. Aqaguutit atuakkia kalaallisut.] {user_message}"
        elif detected_lang == 'sm':
            enhanced_user_message = f"[O oe o se fesoasoani AI e tautala le gagana Samoa. Tali atu i le fe'au a le tagata fa'aoga i le gagana Samoa.] {user_message}"
        elif detected_lang == 'to':
            enhanced_user_message = f"[Ko koe ko e tokoni AI 'oku lea faka-Tonga. Tali ki he fe'au 'a e 'etita 'i he lea faka-Tonga.] {user_message}"
        elif detected_lang == 'fj':
            enhanced_user_message = f"[O iko e dau veivuke ni AI e vosa vakaviti. Vakasaurarataka na itukutuku ni dau vakayagataka ena vosa vakaviti.] {user_message}"
        elif detected_lang == 'haw':
            enhanced_user_message = f"[ʻO ʻoe he kōkua AI e ʻōlelo Hawaiʻi. E pane i ka leka uila a ka mea hoʻohana ma ka ʻōlelo Hawaiʻi.] {user_message}"
        elif detected_lang == 'mi':
            enhanced_user_message = f"[Ko koe he kaiāwhina AI e kōrero Māori. Whakahoki ki te karere a te kaiwhakamahi i te reo Māori.] {user_message}"
        elif detected_lang == 'co':
            enhanced_user_message = f"[Tù sì un assistente AI chì parla corsu. Rispondi à u messaghju di l'utilizatore in corsu.] {user_message}"
        elif detected_lang == 'oc':
            enhanced_user_message = f"[Sètz un assistent AI que parla occitan. Respondètz al messatge de l'utilizaire en occitan.] {user_message}"
        elif detected_lang == 'sc':
            enhanced_user_message = f"[Ses un assistente AI chi faeddat sardu. Responde a su messazu de s'utente in sardu.] {user_message}"
        elif detected_lang == 'rm':
            enhanced_user_message = f"[Ti es in assistent AI che discuorra rumantsch. Respunda al messadi da l'utilisader en rumantsch.] {user_message}"
        elif detected_lang == 'fur':
            enhanced_user_message = f"[Tu sês un assistent AI che fevele furlan. Respuint al messaç dal utent in furlan.] {user_message}"
        elif detected_lang == 'lld':
            enhanced_user_message = f"[Tu es un assistent AI che discuor ladin. Respunde al messaç de l'utent en ladin.] {user_message}"
        elif detected_lang == 'vec':
            enhanced_user_message = f"[Ti xe un assistente AI che parla vèneto. Rispondi al messajo de l'utente in vèneto.] {user_message}"
        elif detected_lang == 'lmo':
            enhanced_user_message = f"[Ti te see un assistent AI che parla lumbard. Respoond al messagg de l'utent in lumbard.] {user_message}"
        elif detected_lang == 'pms':
            enhanced_user_message = f"[Ti it ses n'assistent AI ch'a parla piemontèis. Arspond al mëssagi dl'utent an piemontèis.] {user_message}"
        elif detected_lang == 'nap':
            enhanced_user_message = f"[Tu si n'assistente AI ca parla napulitano. Responn' ô messaggio d' 'o utente 'n napulitano.] {user_message}"
        elif detected_lang == 'scn':
            enhanced_user_message = f"[Tu si n'assistenti AI ca parra sicilianu. Risponni ô missaggiu di l'utenti 'n sicilianu.] {user_message}"
        elif detected_lang == 'lij':
            enhanced_user_message = f"[Ti ti ê un assistente AI ch'o parla lìgure. Arspondi a-o messaggio de l'utente in lìgure.] {user_message}"
        elif detected_lang == 'pdc':
            enhanced_user_message = f"[Du bischt en AI Assistent wu Pennsilfaanisch Deitsch schwetzt. Antwatt uff die Benutzer sei Nochricht in Pennsilfaanisch Deitsch.] {user_message}"
        elif detected_lang == 'bar':
            enhanced_user_message = f"[Du bist a AI Assistent der Boarisch redt. Antwort auf de Benutza sei Nochricht in Boarisch.] {user_message}"
        elif detected_lang == 'ksh':
            enhanced_user_message = f"[Do bes en AI Assistent dä Kölsch kütt. Antwoot op de Benutzer sing Nohreesch en Kölsch.] {user_message}"
        elif detected_lang == 'swg':
            enhanced_user_message = f"[Du bisch a AI Assistent wo Schwäbisch redt. Antwort auf de Benutzer sei Nochricht in Schwäbisch.] {user_message}"
        elif detected_lang == 'gsw':
            enhanced_user_message = f"[Du bisch en AI Assistent wo Schwiizerdütsch redt. Antwort uf de Benutzer si Nochricht in Schwiizerdütsch.] {user_message}"
        elif detected_lang == 'als':
            enhanced_user_message = f"[Du bisch en AI Assistent wo Elsässisch redt. Antwort uf de Benutzer si Nochricht in Elsässisch.] {user_message}"
        elif detected_lang == 'wae':
            enhanced_user_message = f"[Du bisch en AI Assistent wo Walserdütsch redt. Antwort uf de Benutzer si Nochricht in Walserdütsch.] {user_message}"
        elif detected_lang == 'sli':
            enhanced_user_message = f"[Ty jes AI asystynt kery godo po ślůnsku. Uodpowjej na wiadůmość użytkowńika po ślůnsku.] {user_message}"
        elif detected_lang == 'hrx':
            enhanced_user_message = f"[Du bischt en AI Assistent wu Hunsrik redt. Antwatt uff die Benutzer sei Nochricht in Hunsrik.] {user_message}"
        elif detected_lang == 'cim':
            enhanced_user_message = f"[Tü pist en AI Assistent che parla zimbrisch. Antworte a la messazia de l'utent in zimbrisch.] {user_message}"
        elif detected_lang == 'mhn':
            enhanced_user_message = f"[Du pist en AI Assistent che parla mòchen. Antworte a la messazia de l'utent in mòchen.] {user_message}"
        elif detected_lang == 'yue':
            enhanced_user_message = f"[你係一個講廣東話嘅AI助手。請用廣東話回覆用戶嘅訊息。] {user_message}"
        elif detected_lang == 'nan':
            enhanced_user_message = f"[你是一个讲闽南语的AI助手。请用闽南语回复用户的消息。] {user_message}"
        elif detected_lang == 'hak':
            enhanced_user_message = f"[你係一個講客家話嘅AI助手。請用客家話回覆用戶嘅訊息。] {user_message}"
        elif detected_lang == 'gan':
            enhanced_user_message = f"[你是一个讲赣语的AI助手。请用赣语回复用户的消息。] {user_message}"
        elif detected_lang == 'wuu':
            enhanced_user_message = f"[你是一个讲吴语的AI助手。请用吴语回复用户的消息。] {user_message}"
        elif detected_lang == 'hsn':
            enhanced_user_message = f"[你是一个讲湘语的AI助手。请用湘语回复用户的消息。] {user_message}"
        elif detected_lang == 'cjy':
            enhanced_user_message = f"[你是一个讲晋语的AI助手。请用晋语回复用户的消息。] {user_message}"
        elif detected_lang == 'cmn':
            enhanced_user_message = f"[你是一个讲普通话的AI助手。请用普通话回复用户的消息。] {user_message}"
        elif detected_lang == 'dng':
            enhanced_user_message = f"[Син AI ярдәмчесе, Дунган телендә сөйләшә. Кулланучының хәбәрене Дунган телендә җаваплагыз.] {user_message}"
        elif detected_lang == 'ug':
            enhanced_user_message = f"[سىز ئۇيغۇر تىلىدا سۆزلىگۈچى AI ياردەمچىسىز. ئىشلەتكۈچىنىڭ ئۇچۇرىغا ئۇيغۇر تىلىدا جاۋاب بېرىڭ.] {user_message}"
        elif detected_lang == 'bo':
            enhanced_user_message = f"[ཁྱེད་རྣམ་པ་ནི་བོད་སྐད་ཤོད་མཁན་གྱི་AI རོགས་རམ་པ་ཞིག་ཡིན། སྤྱོད་མཁན་གྱི་སྐད་ཆ་ལ་བོད་སྐད་ནས་ལན་འདེབས་གནང་།] {user_message}"
        elif detected_lang == 'dz':
            enhanced_user_message = f"[ཁྱེད་རྣམ་པ་ནི་རྫོང་ཁ་ཤོད་མཁན་གྱི་AI རོགས་རམ་པ་ཞིག་ཡིན། སྤྱོད་མཁན་གྱི་སྐད་ཆ་ལ་རྫོང་ཁ་ནས་ལན་འདེབས་གནང་།] {user_message}"
        else:
            enhanced_user_message = f"[You are an AI assistant who can speak English. Respond to the user's message in English.] {user_message}"
        
        # Geliştirilmiş kullanıcı mesajını ekle
        messages.append({"role": "user", "content": enhanced_user_message})
        
        # Token limitini kontrol et
        token_check = check_token_limit(messages, max_tokens, model)
        print(f"Token kontrolü: {token_check}")
        
        # Eğer kritik seviyede ise uyarı ver ama devam et
        if token_check["warning_level"] == "critical":
            print(f"⚠️ KRİTİK: {token_check['warning_message']}")
        
        # Groq API'ye istek gönder
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Yanıtı al
        assistant_response = chat_completion.choices[0].message.content
        
        # Bot yanıtını veritabanına kaydet
        cursor.execute(
            'INSERT INTO messages (session_id, role, content, model, temperature, max_tokens) VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, 'assistant', assistant_response, model, temperature, max_tokens)
        )
        
        # Session'ın güncellenme zamanını güncelle
        cursor.execute(
            'UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?',
            (session_id,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'response': assistant_response,
            'session_id': session_id,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'token_info': token_check
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Kullanıcının sohbet oturumlarını getir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, session_name, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE messages.session_id = chat_sessions.session_id) as message_count
            FROM chat_sessions 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        sessions = cursor.fetchall()
        conn.close()
        
        session_list = []
        for session_data in sessions:
            session_list.append({
                'session_id': session_data[0],
                'session_name': session_data[1],
                'created_at': session_data[2],
                'updated_at': session_data[3],
                'message_count': session_data[4]
            })
        
        return jsonify({'sessions': session_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
@require_auth
def get_session_messages(session_id):
    """Belirli bir oturumun mesajlarını getir (kullanıcı kontrolü ile)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        cursor.execute('''
            SELECT id, role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg[0],
                'role': msg[1],
                'content': msg[2],
                'timestamp': msg[3],
                'model': msg[4],
                'temperature': msg[5],
                'max_tokens': msg[6]
            })
        
        return jsonify({'messages': message_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@require_auth
def delete_session(session_id):
    """Sohbet oturumunu sil (geri alma için silinen tablosuna taşı)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name, created_at, updated_at FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        created_at = session_data[2]
        updated_at = session_data[3]
        
        # Mesajları silinen mesajlar tablosuna taşı
        cursor.execute('''
            INSERT INTO deleted_messages (session_id, role, content, timestamp, model, temperature, max_tokens)
            SELECT session_id, role, content, timestamp, model, temperature, max_tokens
            FROM messages WHERE session_id = ?
        ''', (session_id,))
        
        # Orijinal mesajları sil
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        
        # Session'ı silinen oturumlar tablosuna taşı
        cursor.execute('''
            INSERT INTO deleted_chat_sessions (session_id, user_id, session_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, session_name, created_at, updated_at))
        
        # Orijinal session'ı sil
        cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session moved to trash successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/rename', methods=['PUT'])
@require_auth
def rename_session(session_id):
    """Sohbet oturumunu yeniden adlandır (kullanıcı kontrolü ile)"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        new_name = data.get('session_name', '')
        
        if not new_name:
            return jsonify({'error': 'Session name is required'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        cursor.execute(
            'UPDATE chat_sessions SET session_name = ? WHERE session_id = ?',
            (new_name, session_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session renamed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download', methods=['GET'])
@require_auth
def download_session(session_id):
    """Sohbet oturumunu JSON formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # JSON formatında hazırla
        session_data = {
            'session_id': session_id,
            'session_name': session_name,
            'user_id': user_id,
            'username': session['username'],
            'export_date': datetime.now().isoformat(),
            'messages': []
        }
        
        for msg in messages:
            session_data['messages'].append({
                'role': msg[0],
                'content': msg[1],
                'timestamp': msg[2],
                'model': msg[3],
                'temperature': msg[4],
                'max_tokens': msg[5]
            })
        
        # JSON dosyası oluştur
        json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        json_buffer.seek(0)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            json_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download-csv', methods=['GET'])
@require_auth
def download_session_csv(session_id):
    """Sohbet oturumunu CSV formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # CSV formatında hazırla
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Başlık satırı
        csv_writer.writerow(['Rol', 'İçerik', 'Zaman', 'Model', 'Sıcaklık', 'Maksimum Token'])
        
        # Mesajları yaz
        for msg in messages:
            csv_writer.writerow([
                'Kullanıcı' if msg[0] == 'user' else 'AI',
                msg[1],
                msg[2],
                msg[3],
                msg[4],
                msg[5]
            ])
        
        csv_buffer.seek(0)
        csv_data = csv_buffer.getvalue().encode('utf-8')
        csv_buffer = io.BytesIO(csv_data)
        csv_buffer.seek(0)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download-pdf', methods=['GET'])
@require_auth
def download_session_pdf(session_id):
    """Sohbet oturumunu PDF formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name, created_at, updated_at FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        created_at = session_data[2]
        updated_at = session_data[3]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # Mesajları formatla
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'role': msg[0],
                'content': msg[1],
                'timestamp': msg[2],
                'model': msg[3],
                'temperature': msg[4],
                'max_tokens': msg[5]
            })
        
        # Session verilerini hazırla
        session_info = {
            'session_name': session_name,
            'created_at': created_at,
            'updated_at': updated_at
        }
        
        # PDF oluştur
        pdf_buffer = create_pdf_from_session(session_info, formatted_messages)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download-txt', methods=['GET'])
@require_auth
def download_session_txt(session_id):
    """Sohbet oturumunu TXT formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name, created_at, updated_at FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        created_at = session_data[2]
        updated_at = session_data[3]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # Mesajları formatla
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'role': msg[0],
                'content': msg[1],
                'timestamp': msg[2],
                'model': msg[3],
                'temperature': msg[4],
                'max_tokens': msg[5]
            })
        
        # Session verilerini hazırla
        session_info = {
            'session_name': session_name,
            'created_at': created_at,
            'updated_at': updated_at
        }
        
        # TXT oluştur
        txt_buffer = create_txt_from_session(session_info, formatted_messages)
        txt_content = txt_buffer.getvalue()
        
        # BytesIO'ya çevir
        txt_bytes = io.BytesIO(txt_content.encode('utf-8'))
        txt_bytes.seek(0)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return send_file(
            txt_bytes,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/clear', methods=['DELETE'])
@require_auth
def clear_session_messages(session_id):
    """Sohbet oturumundaki tüm mesajları sil (oturumu silme)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        # Sadece mesajları sil, oturumu silme
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session messages cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/messages/<int:message_id>/update', methods=['PUT'])
@require_auth
def update_message(session_id, message_id):
    """Belirli bir mesajı güncelle ve chatbot yanıtını yeniden oluştur"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        new_content = data.get('content', '')
        
        if not new_content:
            return jsonify({'error': 'Content is required'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        # Mesajın var olduğunu ve kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT role, content FROM messages WHERE id = ? AND session_id = ?',
            (message_id, session_id)
        )
        message = cursor.fetchone()
        
        if not message:
            conn.close()
            return jsonify({'error': 'Message not found'}), 404
        
        if message[0] != 'user':
            conn.close()
            return jsonify({'error': 'Only user messages can be updated'}), 400
        
        # Mesajı güncelle
        cursor.execute(
            'UPDATE messages SET content = ? WHERE id = ?',
            (new_content, message_id)
        )
        
        # Bu mesajdan sonraki tüm mesajları sil (chatbot yanıtları)
        cursor.execute(
            'DELETE FROM messages WHERE session_id = ? AND id > ?',
            (session_id, message_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Message updated successfully',
            'message_id': message_id,
            'new_content': new_content
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deleted-sessions', methods=['GET'])
@require_auth
def get_deleted_sessions():
    """Kullanıcının silinen sohbet oturumlarını getir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, session_name, created_at, updated_at, deleted_at,
                   (SELECT COUNT(*) FROM deleted_messages WHERE deleted_messages.session_id = deleted_chat_sessions.session_id) as message_count
            FROM deleted_chat_sessions 
            WHERE user_id = ?
            ORDER BY deleted_at DESC
        ''', (user_id,))
        sessions = cursor.fetchall()
        conn.close()
        
        session_list = []
        for session_data in sessions:
            session_list.append({
                'session_id': session_data[0],
                'session_name': session_data[1],
                'created_at': session_data[2],
                'updated_at': session_data[3],
                'deleted_at': session_data[4],
                'message_count': session_data[5]
            })
        
        return jsonify({'deleted_sessions': session_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deleted-sessions/<session_id>/restore', methods=['POST'])
@require_auth
def restore_deleted_session(session_id):
    """Silinen sohbet oturumunu geri yükle"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Silinen session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name, created_at, updated_at FROM deleted_chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        created_at = session_data[2]
        updated_at = session_data[3]
        
        # Session'ı aktif oturumlar tablosuna geri taşı
        cursor.execute('''
            INSERT INTO chat_sessions (session_id, user_id, session_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, session_name, created_at, updated_at))
        
        # Mesajları aktif mesajlar tablosuna geri taşı
        cursor.execute('''
            INSERT INTO messages (session_id, role, content, timestamp, model, temperature, max_tokens)
            SELECT session_id, role, content, timestamp, model, temperature, max_tokens
            FROM deleted_messages WHERE session_id = ?
        ''', (session_id,))
        
        # Silinen mesajları temizle
        cursor.execute('DELETE FROM deleted_messages WHERE session_id = ?', (session_id,))
        
        # Silinen session'ı temizle
        cursor.execute('DELETE FROM deleted_chat_sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session restored successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deleted-sessions/<session_id>/permanent-delete', methods=['DELETE'])
@require_auth
def permanent_delete_session(session_id):
    """Silinen sohbet oturumunu kalıcı olarak sil"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Silinen session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM deleted_chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        # Silinen mesajları kalıcı olarak sil
        cursor.execute('DELETE FROM deleted_messages WHERE session_id = ?', (session_id,))
        
        # Silinen session'ı kalıcı olarak sil
        cursor.execute('DELETE FROM deleted_chat_sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session permanently deleted'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deleted-sessions/empty-trash', methods=['DELETE'])
@require_auth
def empty_trash():
    """Tüm silinen oturumları kalıcı olarak sil"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Kullanıcının tüm silinen mesajlarını sil
        cursor.execute('''
            DELETE FROM deleted_messages 
            WHERE session_id IN (
                SELECT session_id FROM deleted_chat_sessions WHERE user_id = ?
            )
        ''', (user_id,))
        
        # Kullanıcının tüm silinen oturumlarını sil
        cursor.execute('DELETE FROM deleted_chat_sessions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Trash emptied successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/research', methods=['POST'])
@require_auth
def web_research():
    """Web araştırma endpoint'i"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Web araştırması yap
        research_result = web_research.research_query(query)
        
        return jsonify({
            'success': True,
            'research_result': research_result,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Web araştırması yapılamadı.'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Chatbot API is running'})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - redirect to health check or return API info"""
    return jsonify({
        'message': 'AI Chatbot Backend API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'chat': '/api/chat',
            'login': '/api/login',
            'register': '/api/register',
            'sessions': '/api/sessions'
        },
        'status': 'running'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': {
            'root': '/',
            'health': '/api/health',
            'chat': '/api/chat',
            'login': '/api/login',
            'register': '/api/register',
            'sessions': '/api/sessions'
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    # Render'da debug modunu kapat
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 