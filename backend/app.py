from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
from groq import Groq
import json
import sqlite3
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets
import csv
import io
import tiktoken
import logging
import traceback
from logging.handlers import RotatingFileHandler
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, gray
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from web_research import WebResearch
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import base64
import mimetypes
from PIL import Image
import cv2
import numpy as np
from werkzeug.utils import secure_filename

# .env dosyasını yükle
load_dotenv()

# Loglama sistemini kur
def setup_logging():
    """Loglama sistemini yapılandır"""
    # Logs klasörünü oluştur
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Ana logger'ı yapılandır
    logger = logging.getLogger('chatbot')
    logger.setLevel(logging.INFO)
    
    # Dosya handler'ı (rotating file handler)
    file_handler = RotatingFileHandler(
        'logs/chatbot.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler'ı
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Loglama sistemini başlat
logger = setup_logging()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Rate Limiter'ı başlat
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["5000 per day", "1000 per hour"],
    storage_uri="memory://"
)

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

# Resim analizi ayarları
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Upload klasörünü oluştur
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Dosya uzantısının izin verilen uzantılardan olup olmadığını kontrol et"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(file):
    """Resim dosyasını doğrula"""
    if not file:
        return False, "Dosya yüklenmedi"
    
    if file.filename == '':
        return False, "Dosya adı boş"
    
    if not allowed_file(file.filename):
        return False, f"Desteklenmeyen dosya formatı. İzin verilen formatlar: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Dosya boyutunu kontrol et
    file.seek(0, 2)  # Dosyanın sonuna git
    file_size = file.tell()
    file.seek(0)  # Dosyanın başına dön
    
    if file_size > MAX_FILE_SIZE:
        return False, f"Dosya boyutu çok büyük. Maksimum boyut: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, "OK"

def save_image_file(file, user_id):
    """Resim dosyasını kaydet ve dosya yolunu döndür"""
    try:
        # Güvenli dosya adı oluştur
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
        
        # Kullanıcı klasörünü oluştur
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Benzersiz dosya adı oluştur
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(user_folder, unique_filename)
        
        # Dosyayı kaydet
        file.save(file_path)
        
        return file_path, unique_filename
        
    except Exception as e:
        logger.error(f"Resim kaydetme hatası: {str(e)}")
        return None, None

def analyze_image_with_groq(image_path, analysis_type="general"):
    """Groq API ile resim analizi yap"""
    try:
        # Resmi base64'e çevir
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analiz türüne göre prompt oluştur
        if analysis_type == "general":
            system_prompt = """Sen bir resim analiz uzmanısın. Resmi detaylı olarak analiz et ve şu bilgileri ver:

1. **Genel Açıklama**: Resimde ne görüyorsun?
2. **Nesneler**: Resimde hangi nesneler var?
3. **Renkler**: Hangi renkler baskın?
4. **Kompozisyon**: Resmin düzeni nasıl?
5. **Duygu/Atmosfer**: Resim nasıl bir duygu veriyor?
6. **Detaylar**: Önemli detaylar neler?

Türkçe olarak, detaylı ve anlaşılır şekilde yanıtla."""
        
        elif analysis_type == "objects":
            system_prompt = """Sen bir nesne tanıma uzmanısın. Resimdeki nesneleri tespit et ve listele:

1. **Ana Nesneler**: Resmin odak noktasındaki nesneler
2. **Arka Plan Nesneleri**: Arka plandaki nesneler
3. **Küçük Detaylar**: Küçük ama önemli nesneler
4. **Nesne İlişkileri**: Nesneler arasındaki ilişkiler

Her nesne için konumunu da belirt."""
        
        elif analysis_type == "text":
            system_prompt = """Sen bir OCR (Optical Character Recognition) uzmanısın. Resimdeki tüm metinleri oku ve çıkar:

1. **Ana Metinler**: Büyük ve net yazılar
2. **Küçük Yazılar**: Küçük etiketler, işaretler
3. **Sayılar**: Tarihler, fiyatlar, kodlar
4. **Semboller**: Logolar, işaretler
5. **Dil**: Metinlerin hangi dilde olduğu

Metinleri olduğu gibi, doğru şekilde yaz."""
        
        elif analysis_type == "emotions":
            system_prompt = """Sen bir duygu analizi uzmanısın. Resimdeki duyguları ve atmosferi analiz et:

1. **Genel Duygu**: Resmin verdiği ana duygu
2. **Yüz İfadeleri**: Varsa insan yüzlerindeki ifadeler
3. **Renk Psikolojisi**: Renklerin duygusal etkisi
4. **Atmosfer**: Resmin genel atmosferi
5. **Mood**: Resmin ruh hali

Duyguları detaylı olarak açıkla."""
        
        else:
            system_prompt = """Resmi detaylı olarak analiz et ve açıkla."""
        
        # Groq API'ye gönder - Vision modeli için doğru format
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Vision destekli model
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Bu resmi analiz et ve {analysis_type} odaklı detaylı bir rapor ver. Resim: data:image/jpeg;base64,{encoded_image}"
                }
            ],
            max_tokens=2048,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Resim analizi hatası: {str(e)}")
        return f"Resim analizi sırasında hata oluştu: {str(e)}"


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
            email TEXT,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin sütunu yoksa ekle (geriye uyumluluk için)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Sütun zaten varsa hata verme
    
    # Email sütunu yoksa ekle (geriye uyumluluk için)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass  # Sütun zaten varsa hata verme
    
    # Şifre sıfırlama token'ları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
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
    
    # Resim analizi tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            image_filename TEXT,
            image_path TEXT,
            analysis_type TEXT,
            analysis_result TEXT,
            file_size INTEGER,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# Şifre hash fonksiyonu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Token oluşturma fonksiyonu
def generate_reset_token():
    """Şifre sıfırlama token'ı oluştur"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

# Email gönderme fonksiyonu
def send_reset_email(email, username, reset_token):
    """Şifre sıfırlama email'i gönder"""
    try:
        # Email ayarları (örnek - gerçek uygulamada .env'den alınır)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME', 'your-email@gmail.com')
        smtp_password = os.getenv('SMTP_PASSWORD', 'your-app-password')
        
        # Email içeriği
        reset_url = f"http://localhost:8501/?token={reset_token}"
        
        subject = "🔐 Şifre Sıfırlama - AI Chatbot"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h1>🤖 AI Chatbot</h1>
                <h2>Şifre Sıfırlama</h2>
            </div>
            
            <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <p>Merhaba <strong>{username}</strong>,</p>
                
                <p>Şifrenizi sıfırlamak için aşağıdaki butona tıklayın:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; font-weight: bold;">
                        🔐 Şifremi Sıfırla
                    </a>
                </div>
                
                <p><strong>Veya bu linki kopyalayın:</strong></p>
                <p style="background: #e9ecef; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <p><strong>Bu link 1 saat sonra geçersiz olacaktır.</strong></p>
                
                <p>Eğer bu isteği siz yapmadıysanız, bu email'i görmezden gelebilirsiniz.</p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Bu email AI Chatbot sistemi tarafından gönderilmiştir.</p>
            </div>
        </body>
        </html>
        """
        
        # Email oluştur
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = email
        
        # HTML içeriği ekle
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Email gönder
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent: email={email}, username={username}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending error: {str(e)} - email={email}, username={username}")
        return False

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

def require_admin(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Admin kontrolü
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user[0]:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/register', methods=['POST'])
@limiter.limit("3 per minute")  # Dakikada 3 kayıt denemesi
def register():
    """Kullanıcı kaydı"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip().lower()
        
        logger.info(f"Registration attempt: username={username}, email={email} - IP: {request.remote_addr}")
        
        if not username or not password:
            logger.warning(f"Registration failed - missing credentials: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            logger.warning(f"Registration failed - username too short: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            logger.warning(f"Registration failed - password too short: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Email formatını kontrol et (opsiyonel)
        if email and ('@' not in email or '.' not in email):
            logger.warning(f"Registration failed - invalid email format: email={email} - IP: {request.remote_addr}")
            return jsonify({'error': 'Geçerli bir email adresi girin'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, password_hash, email)
            )
            conn.commit()
            
            # Kullanıcı ID'sini al
            user_id = cursor.lastrowid
            
            conn.close()
            
            # Session'a kullanıcı bilgilerini kaydet
            session['user_id'] = user_id
            session['username'] = username
            
            logger.info(f"Registration successful: user_id={user_id}, username={username}, email={email} - IP: {request.remote_addr}")
            
            return jsonify({
                'message': 'Registration successful',
                'user_id': user_id,
                'username': username,
                'email': email
            })
            
        except sqlite3.IntegrityError:
            conn.close()
            logger.warning(f"Registration failed - username already exists: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Username already exists'}), 409
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")  # Dakikada 5 giriş denemesi
def login():
    """Kullanıcı girişi (kullanıcı adı veya email ile)"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        logger.info(f"Login attempt: username={username} - IP: {request.remote_addr}")
        
        if not username or not password:
            logger.warning(f"Login failed - missing credentials: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Kullanıcı adı/email ve şifre gerekli'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Kullanıcı adı veya email ile giriş yapabilir
        cursor.execute(
            'SELECT id, username FROM users WHERE (username = ? OR email = ?) AND password_hash = ?',
            (username, username, password_hash)
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
            
            logger.info(f"Login successful: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            
            return jsonify({
                'message': 'Login successful',
                'user_id': user_id,
                'username': username
            })
        else:
            conn.close()
            logger.warning(f"Login failed - invalid credentials: username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Geçersiz kullanıcı adı/email veya şifre'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Kullanıcı çıkışı"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")  # Saatte 3 şifre sıfırlama isteği
def forgot_password():
    """Şifre sıfırlama isteği"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        logger.info(f"Password reset request: email={email} - IP: {request.remote_addr}")
        
        if not email:
            logger.warning(f"Password reset failed - missing email: IP: {request.remote_addr}")
            return jsonify({'error': 'Email adresi gerekli'}), 400
        
        # Email formatını kontrol et
        if '@' not in email or '.' not in email:
            logger.warning(f"Password reset failed - invalid email format: email={email} - IP: {request.remote_addr}")
            return jsonify({'error': 'Geçerli bir email adresi girin'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Kullanıcıyı email ile bul
        cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            # Güvenlik için kullanıcı bulunamasa da başarılı mesajı döndür
            logger.warning(f"Password reset failed - user not found: email={email} - IP: {request.remote_addr}")
            conn.close()
            return jsonify({
                'message': 'Şifre sıfırlama linki email adresinize gönderildi (eğer bu email adresi sistemde kayıtlıysa)'
            })
        
        user_id, username = user
        
        # Eski token'ları temizle
        cursor.execute('DELETE FROM password_reset_tokens WHERE user_id = ?', (user_id,))
        
        # Yeni token oluştur
        reset_token = generate_reset_token()
        expires_at = datetime.now().replace(microsecond=0) + timedelta(hours=1)
        
        # Token'ı veritabanına kaydet
        cursor.execute(
            'INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, reset_token, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        # Email gönder
        if send_reset_email(email, username, reset_token):
            logger.info(f"Password reset email sent successfully: user_id={user_id}, username={username}, email={email} - IP: {request.remote_addr}")
            return jsonify({
                'message': 'Şifre sıfırlama linki email adresinize gönderildi'
            })
        else:
            logger.error(f"Password reset email sending failed: user_id={user_id}, username={username}, email={email} - IP: {request.remote_addr}")
            return jsonify({
                'error': 'Email gönderilemedi. Lütfen daha sonra tekrar deneyin.'
            }), 500
            
    except Exception as e:
        logger.error(f"Password reset error: {str(e)} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
@limiter.limit("5 per hour")  # Saatte 5 şifre sıfırlama denemesi
def reset_password():
    """Şifre sıfırlama"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        
        logger.info(f"Password reset attempt: token={token[:8]}... - IP: {request.remote_addr}")
        
        if not token or not new_password:
            logger.warning(f"Password reset failed - missing token or password: IP: {request.remote_addr}")
            return jsonify({'error': 'Token ve yeni şifre gerekli'}), 400
        
        if len(new_password) < 6:
            logger.warning(f"Password reset failed - password too short: IP: {request.remote_addr}")
            return jsonify({'error': 'Şifre en az 6 karakter olmalıdır'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Token'ı kontrol et
        cursor.execute('''
            SELECT prt.user_id, prt.used, prt.expires_at, u.username 
            FROM password_reset_tokens prt 
            JOIN users u ON prt.user_id = u.id 
            WHERE prt.token = ?
        ''', (token,))
        
        token_data = cursor.fetchone()
        
        if not token_data:
            logger.warning(f"Password reset failed - invalid token: token={token[:8]}... - IP: {request.remote_addr}")
            conn.close()
            return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 400
        
        user_id, used, expires_at, username = token_data
        
        # Token kullanılmış mı kontrol et
        if used:
            logger.warning(f"Password reset failed - token already used: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            conn.close()
            return jsonify({'error': 'Bu token zaten kullanılmış'}), 400
        
        # Token süresi dolmuş mu kontrol et
        if datetime.now() > datetime.fromisoformat(expires_at):
            logger.warning(f"Password reset failed - token expired: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            conn.close()
            return jsonify({'error': 'Token süresi dolmuş'}), 400
        
        # Şifreyi güncelle
        new_password_hash = hash_password(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, user_id))
        
        # Token'ı kullanıldı olarak işaretle
        cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Password reset successful: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        return jsonify({
            'message': 'Şifreniz başarıyla güncellendi'
        })
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """Reset token'ını doğrula"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Token gerekli'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Token'ı kontrol et
        cursor.execute('''
            SELECT prt.user_id, prt.used, prt.expires_at, u.username 
            FROM password_reset_tokens prt 
            JOIN users u ON prt.user_id = u.id 
            WHERE prt.token = ?
        ''', (token,))
        
        token_data = cursor.fetchone()
        conn.close()
        
        if not token_data:
            return jsonify({'valid': False, 'error': 'Geçersiz token'})
        
        user_id, used, expires_at, username = token_data
        
        if used:
            return jsonify({'valid': False, 'error': 'Token zaten kullanılmış'})
        
        if datetime.now() > datetime.fromisoformat(expires_at):
            return jsonify({'valid': False, 'error': 'Token süresi dolmuş'})
        
        return jsonify({
            'valid': True,
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
@require_auth
def get_user_info():
    """Kullanıcı bilgilerini getir"""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    })

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")  # Dakikada 10 istek
@require_auth
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        logger.info(f"Chat request: user_id={user_id}, username={username}, session_id={session_id}, message_length={len(user_message)} - IP: {request.remote_addr}")
        
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
        
        logger.info(f"Chat response successful: user_id={user_id}, username={username}, session_id={session_id}, model={model}, response_length={len(assistant_response)} - IP: {request.remote_addr}")
        
        return jsonify({
            'response': assistant_response,
            'session_id': session_id,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'token_info': token_check
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)} - user_id={user_id}, username={username}, session_id={session_id} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
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

@app.route('/api/search', methods=['POST'])
@require_auth
def search_messages():
    """Mesajlarda arama yap"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        print(f"DEBUG: Search request data: {data}")  # Debug için
        
        # Arama parametreleri
        query = data.get('query', '').strip()
        session_id = data.get('session_id', None)  # Belirli oturumda arama
        role_filter = data.get('role', None)  # 'user' veya 'assistant'
        date_from = data.get('date_from', None)  # Başlangıç tarihi
        date_to = data.get('date_to', None)  # Bitiş tarihi
        limit = data.get('limit', 50)  # Sonuç limiti
        offset = data.get('offset', 0)  # Sayfalama
        
        print(f"DEBUG: Parsed parameters - query: '{query}', session_id: {session_id}, role: {role_filter}, date_from: {date_from}, date_to: {date_to}")  # Debug için
        
        # En az bir arama kriteri gerekli (boş arama yapılamaz)
        has_criteria = False
        if query and len(query) > 0:
            has_criteria = True
            print(f"DEBUG: Query criteria found: '{query}'")
        if session_id:
            has_criteria = True
            print(f"DEBUG: Session criteria found: {session_id}")
        if role_filter:
            has_criteria = True
            print(f"DEBUG: Role criteria found: {role_filter}")
        if date_from:
            has_criteria = True
            print(f"DEBUG: Date from criteria found: {date_from}")
        if date_to:
            has_criteria = True
            print(f"DEBUG: Date to criteria found: {date_to}")
            
        print(f"DEBUG: Has criteria: {has_criteria}")
        
        if not has_criteria:
            return jsonify({'error': 'At least one search criteria is required'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Temel SQL sorgusu
        sql = '''
            SELECT m.id, m.session_id, m.role, m.content, m.timestamp, m.model, m.temperature, m.max_tokens,
                   cs.session_name
            FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ?
        '''
        params = [user_id]
        
        # Arama kriterlerini ekle
        conditions = []
        
        if query:
            conditions.append("(m.content LIKE ? OR cs.session_name LIKE ?)")
            params.extend([f'%{query}%', f'%{query}%'])
        
        if session_id:
            conditions.append("m.session_id = ?")
            params.append(session_id)
        
        if role_filter:
            conditions.append("m.role = ?")
            params.append(role_filter)
        
        if date_from:
            conditions.append("DATE(m.timestamp) >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("DATE(m.timestamp) <= ?")
            params.append(date_to)
        
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        
        # Sıralama ve limit
        sql += " ORDER BY m.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Debug için SQL sorgusunu yazdır
        print(f"DEBUG: SQL Query: {sql}")
        print(f"DEBUG: SQL Params: {params}")
        
        # Sorguyu çalıştır
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        print(f"DEBUG: Found {len(results)} results")
        
        # Toplam sonuç sayısını al (sayfalama için)
        count_sql = '''
            SELECT COUNT(*)
            FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ?
        '''
        count_params = [user_id]
        
        if conditions:
            count_sql += " AND " + " AND ".join(conditions)
            # Count için de aynı parametreleri ekle (sırayla)
            for condition in conditions:
                if "m.content LIKE ?" in condition or "cs.session_name LIKE ?" in condition:
                    count_params.extend([f'%{query}%', f'%{query}%'])
                elif "m.session_id = ?" in condition:
                    count_params.append(session_id)
                elif "m.role = ?" in condition:
                    count_params.append(role_filter)
                elif "DATE(m.timestamp) >= ?" in condition:
                    count_params.append(date_from)
                elif "DATE(m.timestamp) <= ?" in condition:
                    count_params.append(date_to)
        
        print(f"DEBUG: Count SQL: {count_sql}")
        print(f"DEBUG: Count Params: {count_params}")
        
        cursor.execute(count_sql, count_params)
        total_count = cursor.fetchone()[0]
        
        print(f"DEBUG: Total count: {total_count}")
        
        conn.close()
        
        # Sonuçları formatla
        messages = []
        for result in results:
            messages.append({
                'id': result[0],
                'session_id': result[1],
                'role': result[2],
                'content': result[3],
                'timestamp': result[4],
                'model': result[5],
                'temperature': result[6],
                'max_tokens': result[7],
                'session_name': result[8]
            })
        
        return jsonify({
            'messages': messages,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        print(f"ERROR in search_messages: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/sessions', methods=['GET'])
@require_auth
def search_sessions():
    """Oturum adlarında arama yap"""
    try:
        user_id = session['user_id']
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, session_name, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE messages.session_id = chat_sessions.session_id) as message_count
            FROM chat_sessions 
            WHERE user_id = ? AND session_name LIKE ?
            ORDER BY updated_at DESC
        ''', (user_id, f'%{query}%'))
        
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

@app.route('/api/search/stats', methods=['GET'])
@require_auth
def get_search_stats():
    """Arama istatistiklerini getir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Toplam mesaj sayısı
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ?
        ''', (user_id,))
        total_messages = cursor.fetchone()[0]
        
        # Toplam oturum sayısı
        cursor.execute('SELECT COUNT(*) FROM chat_sessions WHERE user_id = ?', (user_id,))
        total_sessions = cursor.fetchone()[0]
        
        # Kullanıcı mesajları sayısı
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ? AND m.role = 'user'
        ''', (user_id,))
        user_messages = cursor.fetchone()[0]
        
        # Bot mesajları sayısı
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ? AND m.role = 'assistant'
        ''', (user_id,))
        bot_messages = cursor.fetchone()[0]
        
        # En son mesaj tarihi
        cursor.execute('''
            SELECT MAX(timestamp) FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ?
        ''', (user_id,))
        last_message_date = cursor.fetchone()[0]
        
        # En aktif gün (en çok mesaj gönderilen gün)
        cursor.execute('''
            SELECT DATE(timestamp) as message_date, COUNT(*) as message_count
            FROM messages m
            JOIN chat_sessions cs ON m.session_id = cs.session_id
            WHERE cs.user_id = ?
            GROUP BY DATE(timestamp)
            ORDER BY message_count DESC
            LIMIT 1
        ''', (user_id,))
        most_active_day = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'total_messages': total_messages,
            'total_sessions': total_sessions,
            'user_messages': user_messages,
            'bot_messages': bot_messages,
            'last_message_date': last_message_date,
            'most_active_day': {
                'date': most_active_day[0] if most_active_day else None,
                'message_count': most_active_day[1] if most_active_day else 0
            }
        })
        
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
@limiter.exempt
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
    logger.warning(f"404 Not Found: {request.url} - IP: {request.remote_addr} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
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
    logger.error(f"500 Internal Server Error: {str(error)} - IP: {request.remote_addr} - URL: {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    logger.warning(f"429 Rate Limit Exceeded: IP: {request.remote_addr} - URL: {request.url} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Çok fazla istek gönderdiniz. Lütfen birkaç dakika bekleyin.',
        'retry_after': e.retry_after if hasattr(e, 'retry_after') else 60
    }), 429

# Admin Endpoint'leri
@app.route('/api/admin/dashboard', methods=['GET'])
@require_admin
def admin_dashboard():
    """Admin dashboard istatistikleri"""
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'unknown')
        logger.info(f"Admin dashboard accessed: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Toplam kullanıcı sayısı
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Bugün aktif kullanıcılar
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM chat_sessions 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_active_users = cursor.fetchone()[0]
        
        # Toplam mesaj sayısı
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        
        # Bugün gönderilen mesajlar
        cursor.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE DATE(timestamp) = DATE('now')
        ''')
        today_messages = cursor.fetchone()[0]
        
        # Toplam oturum sayısı
        cursor.execute('SELECT COUNT(*) FROM chat_sessions')
        total_sessions = cursor.fetchone()[0]
        
        # En popüler AI modelleri
        cursor.execute('''
            SELECT model, COUNT(*) as count 
            FROM messages 
            WHERE model IS NOT NULL 
            GROUP BY model 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_models = [{'model': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Son 7 günlük aktivite
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM messages 
            WHERE timestamp >= DATE('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''')
        weekly_activity = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'today_active_users': today_active_users,
            'total_messages': total_messages,
            'today_messages': today_messages,
            'total_sessions': total_sessions,
            'popular_models': popular_models,
            'weekly_activity': weekly_activity
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_users():
    """Tüm kullanıcıları listele"""
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, is_admin, created_at, last_login,
                   (SELECT COUNT(*) FROM chat_sessions WHERE user_id = users.id) as session_count,
                   (SELECT COUNT(*) FROM messages WHERE session_id IN 
                    (SELECT session_id FROM chat_sessions WHERE user_id = users.id)) as message_count
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'is_admin': bool(row[2]),
                'created_at': row[3],
                'last_login': row[4],
                'session_count': row[5],
                'message_count': row[6]
            })
        
        conn.close()
        return jsonify({'users': users})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def admin_user_detail(user_id):
    """Kullanıcı detaylarını getir"""
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Kullanıcı bilgileri
        cursor.execute('''
            SELECT id, username, is_admin, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Kullanıcının oturumları
        cursor.execute('''
            SELECT session_id, session_name, created_at, updated_at
            FROM chat_sessions 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
        ''', (user_id,))
        sessions = [{'session_id': row[0], 'session_name': row[1], 
                    'created_at': row[2], 'updated_at': row[3]} 
                   for row in cursor.fetchall()]
        
        # Kullanıcının mesaj istatistikleri
        cursor.execute('''
            SELECT COUNT(*) as total_messages,
                   COUNT(DISTINCT DATE(timestamp)) as active_days,
                   MIN(timestamp) as first_message,
                   MAX(timestamp) as last_message
            FROM messages 
            WHERE session_id IN (SELECT session_id FROM chat_sessions WHERE user_id = ?)
        ''', (user_id,))
        stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'user': {
                'id': user[0],
                'username': user[1],
                'is_admin': bool(user[2]),
                'created_at': user[3],
                'last_login': user[4]
            },
            'sessions': sessions,
            'stats': {
                'total_messages': stats[0],
                'active_days': stats[1],
                'first_message': stats[2],
                'last_message': stats[3]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@require_admin
def admin_toggle_user_admin(user_id):
    """Kullanıcının admin durumunu değiştir"""
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Mevcut admin durumunu kontrol et
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Kendini admin'den çıkarma
        if user_id == session.get('user_id'):
            conn.close()
            return jsonify({'error': 'Cannot remove yourself from admin'}), 400
        
        # Admin durumunu değiştir
        new_admin_status = not user[0]
        cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_admin_status, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'User admin status updated to {new_admin_status}',
            'is_admin': new_admin_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/delete', methods=['DELETE'])
@require_auth
@limiter.limit("3 per hour")  # Saatte 3 hesap silme denemesi
def delete_own_account():
    """Kullanıcının kendi hesabını kalıcı olarak silmesi"""
    try:
        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        logger.info(f"Account deletion request: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        data = request.get_json()
        password = data.get('password', '')
        confirmation = data.get('confirmation', '')
        
        if not password:
            logger.warning(f"Account deletion failed - missing password: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Şifre gerekli'}), 400
        
        if confirmation != 'HESABIMI SİL':
            logger.warning(f"Account deletion failed - wrong confirmation: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Onay metni yanlış. Lütfen "HESABIMI SİL" yazın.'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Şifreyi doğrula
        password_hash = hash_password(password)
        cursor.execute(
            'SELECT id FROM users WHERE id = ? AND password_hash = ?',
            (user_id, password_hash)
        )
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            logger.warning(f"Account deletion failed - wrong password: user_id={user_id}, username={username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Şifre yanlış'}), 401
        
        # Kullanıcının tüm verilerini sil
        # 1. Şifre sıfırlama token'larını sil
        cursor.execute('DELETE FROM password_reset_tokens WHERE user_id = ?', (user_id,))
        
        # 2. Silinen mesajları sil
        cursor.execute('''
            DELETE FROM deleted_messages 
            WHERE session_id IN (
                SELECT session_id FROM deleted_chat_sessions WHERE user_id = ?
            )
        ''', (user_id,))
        
        # 3. Silinen oturumları sil
        cursor.execute('DELETE FROM deleted_chat_sessions WHERE user_id = ?', (user_id,))
        
        # 4. Mesajları sil
        cursor.execute('DELETE FROM messages WHERE session_id IN (SELECT session_id FROM chat_sessions WHERE user_id = ?)', (user_id,))
        
        # 5. Oturumları sil
        cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (user_id,))
        
        # 6. Kullanıcıyı sil
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Session'ı temizle
        session.clear()
        
        logger.info(f"Account deleted successfully: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        return jsonify({
            'message': 'Hesabınız başarıyla silindi. Tüm verileriniz kalıcı olarak kaldırıldı.',
            'deleted': True
        })
        
    except Exception as e:
        logger.error(f"Account deletion error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/delete', methods=['DELETE'])
@require_admin
def admin_delete_user(user_id):
    """Admin tarafından kullanıcıyı sil"""
    try:
        admin_user_id = session.get('user_id')
        admin_username = session.get('username', 'unknown')
        
        logger.info(f"Admin user deletion: admin_id={admin_user_id}, admin_username={admin_username}, target_user_id={user_id} - IP: {request.remote_addr}")
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Kendini silme
        if user_id == admin_user_id:
            conn.close()
            logger.warning(f"Admin tried to delete themselves: admin_id={admin_user_id}, admin_username={admin_username} - IP: {request.remote_addr}")
            return jsonify({'error': 'Kendinizi silemezsiniz'}), 400
        
        # Kullanıcının var olup olmadığını kontrol et
        cursor.execute('SELECT username, is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        username, is_admin = user
        
        # Admin kullanıcıyı silme uyarısı
        if is_admin:
            logger.warning(f"Admin user deletion attempted: target_user_id={user_id}, target_username={username}, admin_id={admin_user_id}, admin_username={admin_username} - IP: {request.remote_addr}")
        
        # Kullanıcının tüm verilerini sil
        # 1. Şifre sıfırlama token'larını sil
        cursor.execute('DELETE FROM password_reset_tokens WHERE user_id = ?', (user_id,))
        
        # 2. Silinen mesajları sil
        cursor.execute('''
            DELETE FROM deleted_messages 
            WHERE session_id IN (
                SELECT session_id FROM deleted_chat_sessions WHERE user_id = ?
            )
        ''', (user_id,))
        
        # 3. Silinen oturumları sil
        cursor.execute('DELETE FROM deleted_chat_sessions WHERE user_id = ?', (user_id,))
        
        # 4. Mesajları sil
        cursor.execute('DELETE FROM messages WHERE session_id IN (SELECT session_id FROM chat_sessions WHERE user_id = ?)', (user_id,))
        
        # 5. Oturumları sil
        cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (user_id,))
        
        # 6. Kullanıcıyı sil
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User deleted by admin: target_user_id={user_id}, target_username={username}, admin_id={admin_user_id}, admin_username={admin_username} - IP: {request.remote_addr}")
        
        return jsonify({
            'message': f'Kullanıcı {username} başarıyla silindi. Tüm verileri kalıcı olarak kaldırıldı.',
            'deleted_user': username,
            'deleted': True
        })
        
    except Exception as e:
        logger.error(f"Admin user deletion error: {str(e)} - admin_id={admin_user_id}, admin_username={admin_username}, target_user_id={user_id} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-stats', methods=['GET'])
@require_admin
def admin_system_stats():
    """Sistem performans istatistikleri"""
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'unknown')
        logger.info(f"Admin system stats accessed: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Veritabanı boyutu
        cursor.execute('PRAGMA page_count')
        page_count = cursor.fetchone()[0]
        cursor.execute('PRAGMA page_size')
        page_size = cursor.fetchone()[0]
        db_size_mb = (page_count * page_size) / (1024 * 1024)
        
        # En aktif kullanıcılar
        cursor.execute('''
            SELECT u.username, COUNT(m.id) as message_count
            FROM users u
            JOIN chat_sessions cs ON u.id = cs.user_id
            JOIN messages m ON cs.session_id = m.session_id
            WHERE m.timestamp >= DATE('now', '-7 days')
            GROUP BY u.id, u.username
            ORDER BY message_count DESC
            LIMIT 10
        ''')
        top_users = [{'username': row[0], 'message_count': row[1]} for row in cursor.fetchall()]
        
        # Model kullanım istatistikleri
        cursor.execute('''
            SELECT model, COUNT(*) as count, 
                   COUNT(*) * 100.0 / (SELECT COUNT(*) FROM messages WHERE model IS NOT NULL) as percentage
            FROM messages 
            WHERE model IS NOT NULL 
            GROUP BY model 
            ORDER BY count DESC
        ''')
        model_stats = [{'model': row[0], 'count': row[1], 'percentage': round(row[2], 2)} 
                      for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'database_size_mb': round(db_size_mb, 2),
            'top_users': top_users,
            'model_stats': model_stats
        })
        
    except Exception as e:
        logger.error(f"Admin system stats error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs', methods=['GET'])
@require_admin
def admin_logs():
    """Sistem loglarını getir"""
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'unknown')
        logger.info(f"Admin logs accessed: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        # Log dosyasını oku
        log_file_path = 'logs/chatbot.log'
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            
            # Son 1000 log satırını al
            logs = logs[-1000:]
            
            return jsonify({
                'logs': logs,
                'total_lines': len(logs),
                'file_size_mb': round(os.path.getsize(log_file_path) / (1024 * 1024), 2)
            })
        else:
            return jsonify({
                'logs': [],
                'total_lines': 0,
                'file_size_mb': 0,
                'message': 'Log dosyası bulunamadı'
            })
            
    except Exception as e:
        logger.error(f"Admin logs error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

# Resim Analizi Endpoint'leri
@app.route('/api/upload-image', methods=['POST'])
@require_auth
@limiter.limit("10 per hour")  # Saatte 10 resim yükleme
def upload_image():
    """Resim yükle ve analiz et"""
    try:
        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        logger.info(f"Image upload request: user_id={user_id}, username={username} - IP: {request.remote_addr}")
        
        # Dosya kontrolü
        if 'image' not in request.files:
            return jsonify({'error': 'Resim dosyası bulunamadı'}), 400
        
        file = request.files['image']
        
        # Dosya doğrulama
        is_valid, message = validate_image_file(file)
        if not is_valid:
            logger.warning(f"Image validation failed: {message} - user_id={user_id}, username={username} - IP: {request.remote_addr}")
            return jsonify({'error': message}), 400
        
        # Analiz türü
        analysis_type = request.form.get('analysis_type', 'general')
        session_id = request.form.get('session_id', None)
        
        # Dosyayı kaydet
        file_path, filename = save_image_file(file, user_id)
        if not file_path:
            return jsonify({'error': 'Dosya kaydedilemedi'}), 500
        
        # Dosya boyutunu al
        file_size = os.path.getsize(file_path)
        
        # Resmi analiz et
        analysis_result = analyze_image_with_groq(file_path, analysis_type)
        
        # Veritabanına kaydet
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO image_analysis (user_id, session_id, image_filename, image_path, analysis_type, analysis_result, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session_id, filename, file_path, analysis_type, analysis_result, file_size))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Image analysis completed: user_id={user_id}, username={username}, analysis_id={analysis_id} - IP: {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'filename': filename,
            'analysis_type': analysis_type,
            'analysis_result': analysis_result,
            'file_size': file_size,
            'upload_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Image upload error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr} - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-image', methods=['POST'])
@require_auth
@limiter.limit("20 per hour")  # Saatte 20 analiz
def analyze_image():
    """Mevcut resmi yeniden analiz et"""
    try:
        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        analysis_type = data.get('analysis_type', 'general')
        
        if not analysis_id:
            return jsonify({'error': 'Analiz ID gerekli'}), 400
        
        # Veritabanından resim bilgilerini al
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT image_path, image_filename FROM image_analysis 
            WHERE id = ? AND user_id = ?
        ''', (analysis_id, user_id))
        
        image_data = cursor.fetchone()
        if not image_data:
            conn.close()
            return jsonify({'error': 'Resim bulunamadı'}), 404
        
        image_path, filename = image_data
        
        # Dosyanın hala var olduğunu kontrol et
        if not os.path.exists(image_path):
            conn.close()
            return jsonify({'error': 'Resim dosyası bulunamadı'}), 404
        
        # Yeni analiz yap
        new_analysis_result = analyze_image_with_groq(image_path, analysis_type)
        
        # Veritabanını güncelle
        cursor.execute('''
            UPDATE image_analysis 
            SET analysis_type = ?, analysis_result = ?
            WHERE id = ?
        ''', (analysis_type, new_analysis_result, analysis_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Image re-analysis completed: user_id={user_id}, username={username}, analysis_id={analysis_id} - IP: {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'filename': filename,
            'analysis_type': analysis_type,
            'analysis_result': new_analysis_result
        })
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/image-history', methods=['GET'])
@require_auth
def get_image_history():
    """Kullanıcının resim analiz geçmişini getir"""
    try:
        user_id = session['user_id']
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, image_filename, analysis_type, analysis_result, file_size, upload_time
            FROM image_analysis 
            WHERE user_id = ?
            ORDER BY upload_time DESC
            LIMIT 50
        ''', (user_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        history_list = []
        for row in history:
            history_list.append({
                'id': row[0],
                'filename': row[1],
                'analysis_type': row[2],
                'analysis_result': row[3],
                'file_size': row[4],
                'upload_time': row[5]
            })
        
        return jsonify({'history': history_list})
        
    except Exception as e:
        logger.error(f"Image history error: {str(e)} - user_id={user_id} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/image/<int:analysis_id>', methods=['DELETE'])
@require_auth
def delete_image_analysis(analysis_id):
    """Resim analizini sil"""
    try:
        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Resim bilgilerini al
        cursor.execute('''
            SELECT image_path, image_filename FROM image_analysis 
            WHERE id = ? AND user_id = ?
        ''', (analysis_id, user_id))
        
        image_data = cursor.fetchone()
        if not image_data:
            conn.close()
            return jsonify({'error': 'Resim bulunamadı'}), 404
        
        image_path, filename = image_data
        
        # Dosyayı sil
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Veritabanından sil
        cursor.execute('DELETE FROM image_analysis WHERE id = ?', (analysis_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Image analysis deleted: user_id={user_id}, username={username}, analysis_id={analysis_id} - IP: {request.remote_addr}")
        
        return jsonify({'success': True, 'message': 'Resim analizi silindi'})
        
    except Exception as e:
        logger.error(f"Image deletion error: {str(e)} - user_id={user_id}, username={username} - IP: {request.remote_addr}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    # Render'da debug modunu kapat
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 