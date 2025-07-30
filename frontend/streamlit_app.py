import streamlit as st
import requests
import json
from datetime import datetime
import time
import base64
import re
import emoji
import random

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Avatar fonksiyonları
def get_user_avatar():
    """Kullanıcı avatarı döndür"""
    user_avatars = [
        "👤", "👨‍💼", "👩‍💼", "👨‍🎓", "👩‍🎓", "👨‍💻", "👩‍💻", 
        "👨‍🔬", "👩‍🔬", "👨‍🎨", "👩‍🎨", "👨‍⚕️", "👩‍⚕️", "👨‍🏫", "👩‍🏫"
    ]
    return random.choice(user_avatars)

def get_bot_avatar():
    """Bot avatarı döndür"""
    bot_avatars = [
        "🤖", "🦾", "🧠", "💻", "🔮", "🎯", "⚡", "🚀", "🌟", "💎"
    ]
    return random.choice(bot_avatars)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
        margin-left: 2rem;
    }
    
    .bot-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
        margin-right: 2rem;
    }
    
    .message-time {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
    }
    
    /* Avatar buton stilleri */
    .avatar-button {
        font-size: 1.5rem;
        padding: 0.5rem;
        border-radius: 50%;
        border: 2px solid transparent;
        background: transparent;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .avatar-button:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.1);
        transform: scale(1.1);
    }
    
    .avatar-button.active {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.2);
    }
    
    /* Seçili avatar vurgulama */
    .stButton > button[data-testid*="user_avatar"]:has-text("${st.session_state.user_avatar}") {
        background-color: #667eea !important;
        color: white !important;
        border: 2px solid #667eea !important;
    }
    
    .stButton > button[data-testid*="bot_avatar"]:has-text("${st.session_state.bot_avatar}") {
        background-color: #667eea !important;
        color: white !important;
        border: 2px solid #667eea !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .session-item {
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .session-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .session-item.active {
        background-color: rgba(255, 255, 255, 0.2);
        border-left: 3px solid #fff;
    }
    
    .auth-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 300px;
        margin: 0 auto;
    }
    
    .auth-container h2 {
        color: #333 !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .auth-container {
        margin-bottom: 1rem;
    }
    
    .user-info {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    /* Form etiketleri için daha koyu renk */
    .stForm label {
        color: #333 !important;
        font-weight: 600;
    }
    
    /* Tab başlıkları için daha koyu renk */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f9fa;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #333 !important;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        color: #667eea !important;
        font-weight: bold;
    }
    
    /* İndirme butonları için özel stiller */
    .download-btn {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    
    .clear-btn {
        background: linear-gradient(90deg, #dc3545 0%, #fd7e14 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    
    /* Markdown stilleri */
    .chat-message h1 {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 10px 0;
        color: #333;
    }
    
    .chat-message h2 {
        font-size: 1.3rem;
        font-weight: bold;
        margin: 8px 0;
        color: #333;
    }
    
    .chat-message h3 {
        font-size: 1.1rem;
        font-weight: bold;
        margin: 6px 0;
        color: #333;
    }
    
    .chat-message strong {
        font-weight: bold;
        color: #333;
    }
    
    .chat-message em {
        font-style: italic;
        color: #666;
    }
    
    .chat-message li {
        margin: 2px 0;
        padding-left: 10px;
    }
    
    .chat-message a {
        color: #007bff;
        text-decoration: none;
    }
    
    .chat-message a:hover {
        text-decoration: underline;
    }
    
    .chat-message code {
        background-color: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    .chat-message pre {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #007bff;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        margin: 10px 0;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# Session state başlatma
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:5050/api"

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" veya "register"

# Avatar'ları session state'e ekle
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = get_user_avatar()

if "bot_avatar" not in st.session_state:
    st.session_state.bot_avatar = get_bot_avatar()

# API fonksiyonları
def check_auth_status():
    """Kullanıcı kimlik doğrulama durumunu kontrol et"""
    try:
        response = requests.get(f"{st.session_state.api_url}/user", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_id = data['user_id']
            st.session_state.username = data['username']
            return True
        else:
            st.session_state.user_id = None
            st.session_state.username = None
            return False
    except:
        st.session_state.user_id = None
        st.session_state.username = None
        return False

def login_user(username, password):
    """Kullanıcı girişi"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/login",
            json={"username": username, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_id = data['user_id']
            st.session_state.username = data['username']
            # Cookie'leri kaydet
            if 'Set-Cookie' in response.headers:
                st.session_state.cookies = response.cookies.get_dict()
            st.success("Giriş başarılı!")
            return True
        else:
            error_data = response.json()
            st.error(f"Giriş hatası: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return False

def register_user(username, password):
    """Kullanıcı kaydı"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/register",
            json={"username": username, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_id = data['user_id']
            st.session_state.username = data['username']
            # Cookie'leri kaydet
            if 'Set-Cookie' in response.headers:
                st.session_state.cookies = response.cookies.get_dict()
            st.success("Kayıt başarılı!")
            return True
        else:
            error_data = response.json()
            st.error(f"Kayıt hatası: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return False

def logout_user():
    """Kullanıcı çıkışı"""
    try:
        response = requests.post(f"{st.session_state.api_url}/logout", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.session_state.sessions = []
            st.session_state.cookies = {}
            st.success("Çıkış başarılı!")
            st.rerun()
        else:
            st.error("Çıkış hatası")
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")

def load_sessions():
    """Kullanıcının sohbet oturumlarını yükle"""
    try:
        response = requests.get(f"{st.session_state.api_url}/sessions", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            st.session_state.sessions = data.get('sessions', [])
        else:
            st.error("Oturumlar yüklenemedi")
    except Exception as e:
        st.error(f"Oturum yükleme hatası: {str(e)}")

def load_session_messages(session_id):
    """Belirli bir oturumun mesajlarını yükle"""
    try:
        response = requests.get(f"{st.session_state.api_url}/sessions/{session_id}", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            
            # Mesajları Streamlit formatına çevir
            st.session_state.messages = []
            for msg in messages:
                st.session_state.messages.append({
                    "role": msg['role'],
                    "content": msg['content'],
                    "time": datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')).strftime("%H:%M")
                })
        else:
            st.error("Mesajlar yüklenemedi")
    except Exception as e:
        st.error(f"Mesaj yükleme hatası: {str(e)}")

def delete_session(session_id):
    """Sohbet oturumunu sil"""
    try:
        response = requests.delete(f"{st.session_state.api_url}/sessions/{session_id}", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            st.success("Oturum silindi!")
            load_sessions()
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            st.rerun()
        else:
            st.error("Oturum silinemedi")
    except Exception as e:
        st.error(f"Silme hatası: {str(e)}")

def rename_session(session_id, new_name):
    """Sohbet oturumunu yeniden adlandır"""
    try:
        response = requests.put(
            f"{st.session_state.api_url}/sessions/{session_id}/rename",
            json={"session_name": new_name},
            timeout=5,
            cookies=st.session_state.get('cookies', {})
        )
        if response.status_code == 200:
            st.success("Oturum yeniden adlandırıldı!")
            load_sessions()
            st.rerun()
        else:
            st.error("Oturum yeniden adlandırılamadı")
    except Exception as e:
        st.error(f"Yeniden adlandırma hatası: {str(e)}")

def download_session_json(session_id):
    """Sohbet oturumunu JSON formatında indir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/sessions/{session_id}/download",
            cookies=st.session_state.get('cookies', {}),
            stream=True
        )
        if response.status_code == 200:
            # Dosya adını al
            content_disposition = response.headers.get('content-disposition', '')
            filename = 'sohbet.json'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Dosyayı indir
            st.download_button(
                label="📄 JSON İndir",
                data=response.content,
                file_name=filename,
                mime="application/json",
                key=f"download_json_{session_id}"
            )
            return True
        else:
            st.error("İndirme hatası")
            return False
    except Exception as e:
        st.error(f"İndirme hatası: {str(e)}")
        return False

def download_session_csv(session_id):
    """Sohbet oturumunu CSV formatında indir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/sessions/{session_id}/download-csv",
            cookies=st.session_state.get('cookies', {}),
            stream=True
        )
        if response.status_code == 200:
            # Dosya adını al
            content_disposition = response.headers.get('content-disposition', '')
            filename = 'sohbet.csv'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Dosyayı indir
            st.download_button(
                label="📊 CSV İndir",
                data=response.content,
                file_name=filename,
                mime="text/csv",
                key=f"download_csv_{session_id}"
            )
            return True
        else:
            st.error("İndirme hatası")
            return False
    except Exception as e:
        st.error(f"İndirme hatası: {str(e)}")
        return False

def clear_session_messages(session_id):
    """Sohbet oturumundaki tüm mesajları sil"""
    try:
        response = requests.delete(
            f"{st.session_state.api_url}/sessions/{session_id}/clear",
            cookies=st.session_state.get('cookies', {})
        )
        if response.status_code == 200:
            st.success("Sohbet geçmişi temizlendi!")
            load_sessions()
            if st.session_state.current_session_id == session_id:
                st.session_state.messages = []
            st.rerun()
        else:
            st.error("Temizleme hatası")
    except Exception as e:
        st.error(f"Temizleme hatası: {str(e)}")

def process_markdown_and_emoji(text):
    """Markdown ve emoji işleme"""
    if not text:
        return text
    
    # Emoji'leri işle
    text = emoji.emojize(text, language='alias')
    
    # Markdown kod bloklarını koru
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    # Kod bloklarını geçici olarak sakla
    text = re.sub(r'```[\s\S]*?```', save_code_block, text)
    
    # Satır içi kod bloklarını da sakla
    text = re.sub(r'`[^`]+`', save_code_block, text)
    
    # Markdown formatlaması
    # Başlıklar
    text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Kalın ve italik
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Liste
    text = re.sub(r'^\* (.*$)', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.*$)', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Linkler
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # Satır sonları
    text = text.replace('\n', '<br>')
    
    # Kod bloklarını geri yükle
    for i, code_block in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", code_block)
    
    return text

def render_message_content(content):
    """Mesaj içeriğini render et"""
    if not content:
        return ""
    
    # Markdown ve emoji işle
    processed_content = process_markdown_and_emoji(content)
    
    # Kod bloklarını özel olarak işle
    def format_code_block(match):
        code = match.group(1)
        return f'<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff; font-family: monospace; white-space: pre-wrap; margin: 10px 0;">{code}</div>'
    
    # Satır içi kod bloklarını işle
    def format_inline_code(match):
        code = match.group(1)
        return f'<code style="background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; font-family: monospace;">{code}</code>'
    
    # Kod bloklarını formatla
    processed_content = re.sub(r'```(\w+)?\n([\s\S]*?)```', format_code_block, processed_content)
    processed_content = re.sub(r'`([^`]+)`', format_inline_code, processed_content)
    
    return processed_content

# Ana başlık
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Chatbot</h1>
    <p>Groq API ile güçlendirilmiş yapay zeka asistanı</p>
</div>
""", unsafe_allow_html=True)

# Kullanıcı kimlik doğrulama durumunu kontrol et
is_authenticated = check_auth_status()

# Kullanıcı giriş yapmamışsa giriş/ kayıt formunu göster
if not is_authenticated:
    st.markdown("""
    <div class="auth-container">
        <h2>🔐 Giriş Yapın</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Giriş/Kayıt seçimi
    auth_tab1, auth_tab2 = st.tabs(["🔑 Giriş", "📝 Kayıt"])
    
    with auth_tab1:
        with st.form("login_form"):
            login_username = st.text_input("Kullanıcı Adı", key="login_username")
            login_password = st.text_input("Şifre", type="password", key="login_password")
            login_submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if login_submitted:
                if login_username and login_password:
                    if login_user(login_username, login_password):
                        st.rerun()
                else:
                    st.error("Kullanıcı adı ve şifre gerekli!")
    
    with auth_tab2:
        with st.form("register_form"):
            register_username = st.text_input("Kullanıcı Adı", key="register_username")
            register_password = st.text_input("Şifre", type="password", key="register_password")
            register_password_confirm = st.text_input("Şifre Tekrar", type="password", key="register_password_confirm")
            register_submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            if register_submitted:
                if register_username and register_password:
                    if register_password == register_password_confirm:
                        if len(register_username) >= 3:
                            if len(register_password) >= 6:
                                if register_user(register_username, register_password):
                                    st.rerun()
                            else:
                                st.error("Şifre en az 6 karakter olmalıdır!")
                        else:
                            st.error("Kullanıcı adı en az 3 karakter olmalıdır!")
                    else:
                        st.error("Şifreler eşleşmiyor!")
                else:
                    st.error("Kullanıcı adı ve şifre gerekli!")
    
    # API durumu kontrolü
    st.markdown("---")
    st.markdown("## 📊 API Durumu")
    
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API Bağlantısı Aktif")
        else:
            st.error("❌ API Bağlantısı Hatası")
    except:
        st.error("❌ API Bağlantısı Yok")
        st.info("Backend'i başlatmayı unutmayın!")
    
    st.stop()

# Kullanıcı giriş yapmışsa ana uygulamayı göster
else:
    # Kullanıcı bilgileri
    st.markdown(f"""
    <div class="user-info">
        👤 <strong>{st.session_state.username}</strong> olarak giriş yaptınız
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Ayarlar")
        
        # Kullanıcı çıkış butonu
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            logout_user()
        
        st.markdown("---")
        
        # API URL ayarı
        api_url = st.text_input(
            "API URL",
            value=st.session_state.api_url,
            help="Backend API'nin URL'si"
        )
        
        if api_url != st.session_state.api_url:
            st.session_state.api_url = api_url
            st.success("API URL güncellendi!")
        
        # Model seçimi
        model = st.selectbox(
            "Model",
            ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"],
            help="Kullanılacak AI modeli"
        )
        
        # Sıcaklık ayarı
        temperature = st.slider(
            "Sıcaklık",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Yaratıcılık seviyesi (0=deterministik, 2=çok yaratıcı)"
        )
        
        # Maksimum token
        max_tokens = st.slider(
            "Maksimum Token",
            min_value=100,
            max_value=4096,
            value=1024,
            step=100,
            help="Maksimum yanıt uzunluğu"
        )
        
        st.markdown("---")
        
        # Avatar Ayarları
        st.markdown("## 🎭 Avatar Ayarları")
        
        # Mevcut avatar'ları göster
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Kullanıcı Avatarı:** {st.session_state.user_avatar}")
        with col2:
            st.markdown(f"**🤖 Bot Avatarı:** {st.session_state.bot_avatar}")
        
        # Kullanıcı avatarı seçimi
        user_avatars = ["👤", "👨‍💼", "👩‍💼", "👨‍🎓", "👩‍🎓", "👨‍💻", "👩‍💻", "👨‍🔬", "👩‍🔬", "👨‍🎨", "👩‍🎨", "👨‍⚕️", "👩‍⚕️", "👨‍🏫", "👩‍🏫"]
        
        st.markdown("**👤 Kullanıcı Avatarı Seçin:**")
        user_avatar_cols = st.columns(5)
        for i, avatar in enumerate(user_avatars):
            with user_avatar_cols[i % 5]:
                # Seçili avatar'ı vurgula
                button_style = "background-color: #667eea; color: white;" if avatar == st.session_state.user_avatar else ""
                if st.button(avatar, key=f"user_avatar_{i}", help=f"Kullanıcı avatarı: {avatar}"):
                    st.session_state.user_avatar = avatar
                    st.success(f"✅ Kullanıcı avatarı değiştirildi: {avatar}")
                    st.rerun()
        
        # Bot avatarı seçimi
        bot_avatars = ["🤖", "🦾", "🧠", "💻", "🔮", "🎯", "⚡", "🚀", "🌟", "💎"]
        
        st.markdown("**🤖 Bot Avatarı Seçin:**")
        bot_avatar_cols = st.columns(5)
        for i, avatar in enumerate(bot_avatars):
            with bot_avatar_cols[i % 5]:
                # Seçili avatar'ı vurgula
                button_style = "background-color: #667eea; color: white;" if avatar == st.session_state.bot_avatar else ""
                if st.button(avatar, key=f"bot_avatar_{i}", help=f"Bot avatarı: {avatar}"):
                    st.session_state.bot_avatar = avatar
                    st.success(f"✅ Bot avatarı değiştirildi: {avatar}")
                    st.rerun()
        
        # Avatar sıfırlama
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Rastgele Avatar'lar", use_container_width=True):
                st.session_state.user_avatar = get_user_avatar()
                st.session_state.bot_avatar = get_bot_avatar()
                st.success("🎲 Avatar'lar rastgele değiştirildi!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Sohbeti Yenile", use_container_width=True):
                st.success("🔄 Sohbet yenilendi! Yeni avatar'ları görebilirsiniz.")
                st.rerun()
        
        # Avatar test mesajı
        if st.button("🧪 Avatar Test Mesajı Gönder", use_container_width=True):
            # Test mesajları ekle
            test_user_message = {
                "role": "user",
                "content": "Bu bir test mesajıdır! Avatar'ımı görebiliyor musun? 👋",
                "time": datetime.now().strftime("%H:%M")
            }
            test_bot_message = {
                "role": "assistant", 
                "content": "Evet! Senin avatar'ın: {st.session_state.user_avatar} ve benim avatar'ım: {st.session_state.bot_avatar} 🎭",
                "time": datetime.now().strftime("%H:%M")
            }
            
            st.session_state.messages.append(test_user_message)
            st.session_state.messages.append(test_bot_message)
            st.success("🧪 Test mesajları eklendi! Avatar'ları kontrol edin.")
            st.rerun()
        
        st.markdown("---")
        
        # Sohbet Oturumları
        st.markdown("## 💬 Sohbet Oturumları")
        
        # Oturumları yenile butonu
        if st.button("🔄 Oturumları Yenile", use_container_width=True):
            load_sessions()
        
        # Oturumları yükle
        if not st.session_state.sessions:
            load_sessions()
        
        # Yeni oturum oluştur
        if st.button("➕ Yeni Oturum", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.messages = []
            st.rerun()
        
        # Mevcut oturumları listele
        if st.session_state.sessions:
            st.markdown("### Mevcut Oturumlar:")
            
            for session in st.session_state.sessions:
                session_id = session['session_id']
                session_name = session['session_name']
                message_count = session['message_count']
                updated_at = session['updated_at']
                
                # Oturum bilgilerini göster
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Aktif oturum kontrolü
                    is_active = st.session_state.current_session_id == session_id
                    if is_active:
                        st.markdown(f"**📁 {session_name}**")
                    else:
                        if st.button(f"📁 {session_name}", key=f"session_{session_id}", use_container_width=True):
                            st.session_state.current_session_id = session_id
                            load_session_messages(session_id)
                            st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"delete_{session_id}", help="Oturumu sil"):
                        delete_session(session_id)
                
                # Oturum detayları
                st.caption(f"💬 {message_count} mesaj • {updated_at[:10]}")
                
                # İndirme ve temizleme butonları (sadece aktif oturum için)
                if is_active and message_count > 0:
                    st.markdown("**📥 İndirme Seçenekleri:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📄 JSON", key=f"download_json_{session_id}", help="JSON formatında indir"):
                            download_session_json(session_id)
                    
                    with col2:
                        if st.button("📊 CSV", key=f"download_csv_{session_id}", help="CSV formatında indir"):
                            download_session_csv(session_id)
                    
                    with col3:
                        if st.button("🧹 Temizle", key=f"clear_{session_id}", help="Sohbet geçmişini temizle"):
                            clear_session_messages(session_id)
                
                # Yeniden adlandırma
                if is_active:
                    new_name = st.text_input(
                        "Yeni isim:",
                        value=session_name,
                        key=f"rename_{session_id}",
                        label_visibility="collapsed"
                    )
                    if new_name != session_name:
                        rename_session(session_id, new_name)
        
        st.markdown("---")
        
        # Sohbeti temizle
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # API durumu kontrolü
        st.markdown("---")
        st.markdown("## 📊 API Durumu")
        
        try:
            response = requests.get(f"{st.session_state.api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API Bağlantısı Aktif")
            else:
                st.error("❌ API Bağlantısı Hatası")
        except:
            st.error("❌ API Bağlantısı Yok")
            st.info("Backend'i başlatmayı unutmayın!")

    # Mevcut oturum bilgisi
    if st.session_state.current_session_id:
        current_session = next((s for s in st.session_state.sessions if s['session_id'] == st.session_state.current_session_id), None)
        if current_session:
            st.info(f"📁 Aktif Oturum: {current_session['session_name']} ({current_session['message_count']} mesaj)")
    else:
        st.info("🆕 Yeni oturum başlatıldı")

    # Chat container
    chat_container = st.container()

    # Mesajları göster
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            # Avatar seç
            if message["role"] == "user":
                avatar = st.session_state.user_avatar
            else:
                avatar = st.session_state.bot_avatar
            
            with st.chat_message(message["role"], avatar=avatar):
                # Markdown ve emoji desteği ile mesajı render et
                rendered_content = render_message_content(message["content"])
                st.markdown(rendered_content, unsafe_allow_html=True)
                st.caption(message["time"])

    # Kullanıcı girişi
    if prompt := st.chat_input("Mesajınızı yazın..."):
        # Kullanıcı mesajını ekle
        user_message = {
            "role": "user",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M")
        }
        st.session_state.messages.append(user_message)
        
        # Kullanıcı mesajını göster
        with st.chat_message("user", avatar=st.session_state.user_avatar):
            # Markdown ve emoji desteği ile kullanıcı mesajını render et
            rendered_prompt = render_message_content(prompt)
            st.markdown(rendered_prompt, unsafe_allow_html=True)
            st.caption(user_message["time"])
        
        # Bot yanıtını al
        with st.chat_message("assistant", avatar=st.session_state.bot_avatar):
            with st.spinner("🤔 Düşünüyor..."):
                try:
                    # API'ye istek gönder
                    request_data = {
                        "message": prompt,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    
                    # Eğer aktif oturum varsa session_id ekle
                    if st.session_state.current_session_id:
                        request_data["session_id"] = st.session_state.current_session_id
                    
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json=request_data,
                        timeout=30,
                        cookies=st.session_state.get('cookies', {})
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        bot_response = data["response"]
                        
                        # Session ID'yi kaydet (yeni oturum oluşturulmuşsa)
                        if "session_id" in data and not st.session_state.current_session_id:
                            st.session_state.current_session_id = data["session_id"]
                            load_sessions()  # Oturum listesini güncelle
                        
                        # Bot mesajını ekle
                        bot_message = {
                            "role": "assistant",
                            "content": bot_response,
                            "time": datetime.now().strftime("%H:%M")
                        }
                        st.session_state.messages.append(bot_message)
                        
                        # Bot yanıtını göster (avatar zaten chat_message'da ayarlandı)
                        rendered_response = render_message_content(bot_response)
                        st.markdown(rendered_response, unsafe_allow_html=True)
                        st.caption(bot_message["time"])
                        
                    else:
                        error_msg = f"API Hatası: {response.status_code}"
                        st.error(error_msg)
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Yanıt zaman aşımına uğradı")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 API bağlantısı kurulamadı. Backend'in çalıştığından emin olun.")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")

    # Alt bilgi
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔧 Teknolojiler:**")
        st.markdown("- Python Flask")
        st.markdown("- Streamlit")
        st.markdown("- Groq API")
        st.markdown("- SQLite DB")

    with col2:
        st.markdown("**🚀 Özellikler:**")
        st.markdown("- Kullanıcı kimlik doğrulama")
        st.markdown("- Kişisel sohbet geçmişi")
        st.markdown("- Oturum yönetimi")
        st.markdown("- Sohbet indirme")

    with col3:
        st.markdown("**📞 Destek:**")
        st.markdown("- API durumu kontrolü")
        st.markdown("- Hata yönetimi")
        st.markdown("- Responsive tasarım")
        st.markdown("- Güvenli veri saklama")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🤖 AI Chatbot - Groq API ile güçlendirilmiş"
        "</div>",
        unsafe_allow_html=True
    ) 