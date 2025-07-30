import streamlit as st
import requests
import json
from datetime import datetime
import time
import base64
import re
import emoji
import random
import langdetect
from langdetect import detect, DetectorFactory

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema fonksiyonları
def get_theme_css(theme="light"):
    """Tema CSS'ini döndür"""
    if theme == "dark":
        return """
        /* Karanlık tema */
        .stApp {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        
        .main .block-container {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        
        .stMarkdown {
            color: #ffffff !important;
        }
        
        .stTextInput > div > div > input {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #444444 !important;
        }
        
        .stSelectbox > div > div > div {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
        }
        
        .stSlider > div > div > div > div {
            background-color: #2d2d2d !important;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        .chat-message {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #444444 !important;
        }
        
        .user-message {
            background-color: #1e3a5f !important;
            border-left-color: #2196f3 !important;
        }
        
        .bot-message {
            background-color: #2d1b3d !important;
            border-left-color: #9c27b0 !important;
        }
        
        .sidebar .sidebar-content {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background-color: #2d2d2d !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #ffffff !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: white !important;
        }
        
        .auth-container {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #444444 !important;
        }
        
        .auth-container h2 {
            color: #ffffff !important;
        }
        
        .user-info {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #444444 !important;
        }
        """
    else:
        return """
        /* Aydınlık tema */
        .stApp {
            background-color: #ffffff !important;
            color: #333333 !important;
        }
        
        .main .block-container {
            background-color: #ffffff !important;
            color: #333333 !important;
        }
        
        .stMarkdown {
            color: #333333 !important;
        }
        
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #333333 !important;
            border-color: #cccccc !important;
        }
        
        .stSelectbox > div > div > div {
            background-color: #ffffff !important;
            color: #333333 !important;
        }
        
        .stSlider > div > div > div > div {
            background-color: #ffffff !important;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        .chat-message {
            background-color: #ffffff !important;
            color: #333333 !important;
            border-color: #cccccc !important;
        }
        
        .user-message {
            background-color: #e3f2fd !important;
            border-left-color: #2196f3 !important;
        }
        
        .bot-message {
            background-color: #f3e5f5 !important;
            border-left-color: #9c27b0 !important;
        }
        
        .sidebar .sidebar-content {
            background-color: #f8f9fa !important;
            color: #333333 !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background-color: #ffffff !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #333333 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: white !important;
        }
        
        .auth-container {
            background-color: #ffffff !important;
            color: #333333 !important;
            border-color: #cccccc !important;
        }
        
        .auth-container h2 {
            color: #333333 !important;
        }
        
        .user-info {
            background-color: #f8f9fa !important;
            color: #333333 !important;
            border-color: #cccccc !important;
        }
        """

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

# Dil algılama ve çeviri fonksiyonları
def detect_language(text):
    """Metnin dilini algıla - Tüm diller"""
    try:
        # LangDetect kullanarak tüm dilleri algıla
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
        detected_lang = detect(text)
        return detected_lang
    except:
        # Fallback: Basit kelime tabanlı algılama
        text = text.lower().strip()
        
        # Türkçe karakterler ve kelimeler
        turkish_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']
        turkish_words = ['merhaba', 'selam', 'nasılsın', 'iyi', 'güzel', 'teşekkür', 'evet', 'hayır']
        
        # Almanca karakterler ve kelimeler
        german_chars = ['ä', 'ö', 'ü', 'ß']
        german_words = ['hallo', 'guten', 'tag', 'danke', 'bitte', 'ja', 'nein']
        
        # İngilizce kelimeler
        english_words = ['hello', 'hi', 'how', 'are', 'you', 'good', 'bad', 'yes', 'no', 'thank', 'please']
        
        # Basit kelime sayımı
        turkish_score = 0
        german_score = 0
        english_score = 0
        
        # Türkçe karakter kontrolü
        for char in turkish_chars:
            if char in text:
                turkish_score += 2
        
        # Almanca karakter kontrolü
        for char in german_chars:
            if char in text:
                german_score += 2
        
        # Kelime kontrolü
        words = text.split()
        for word in words:
            if word in turkish_words:
                turkish_score += 1
            if word in german_words:
                german_score += 1
            if word in english_words:
                english_score += 1
        
        # En yüksek skoru döndür
        scores = {'tr': turkish_score, 'de': german_score, 'en': english_score}
        best_lang = max(scores, key=scores.get)
        
        return best_lang

def get_language_name(lang_code):
    """Dil kodunu dil adına çevir"""
    language_names = {
        'tr': 'Türkçe', 'en': 'İngilizce', 'es': 'İspanyolca', 'fr': 'Fransızca', 'de': 'Almanca',
        'it': 'İtalyanca', 'pt': 'Portekizce', 'ru': 'Rusça', 'ja': 'Japonca', 'ko': 'Korece',
        'zh': 'Çince', 'ar': 'Arapça', 'hi': 'Hintçe', 'nl': 'Hollandaca', 'pl': 'Lehçe',
        'sv': 'İsveççe', 'da': 'Danca', 'no': 'Norveççe', 'fi': 'Fince', 'hu': 'Macarca',
        'cs': 'Çekçe', 'ro': 'Romence', 'bg': 'Bulgarca', 'hr': 'Hırvatça', 'sk': 'Slovakça',
        'sl': 'Slovence', 'et': 'Estonca', 'lv': 'Letonca', 'lt': 'Litvanca', 'mt': 'Maltaca',
        'ga': 'İrlandaca', 'cy': 'Galce', 'eu': 'Baskça', 'ca': 'Katalanca', 'gl': 'Galiçyaca',
        'is': 'İzlandaca', 'mk': 'Makedonca', 'sq': 'Arnavutça', 'sr': 'Sırpça', 'bs': 'Boşnakça',
        'me': 'Karadağca', 'uk': 'Ukraynaca', 'be': 'Belarusça', 'kk': 'Kazakça', 'ky': 'Kırgızca',
        'uz': 'Özbekçe', 'tg': 'Tacikçe', 'mn': 'Moğolca', 'ka': 'Gürcüce', 'hy': 'Ermenice',
        'az': 'Azerbaycanca', 'fa': 'Farsça', 'ur': 'Urduca', 'bn': 'Bengalce', 'ta': 'Tamilce',
        'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam', 'gu': 'Gujarati', 'pa': 'Pencapça',
        'or': 'Odiya', 'as': 'Assamca', 'ne': 'Nepalce', 'si': 'Seylanca', 'my': 'Myanmar',
        'km': 'Kamboçyaca', 'lo': 'Laoca', 'th': 'Tayca', 'vi': 'Vietnamca', 'id': 'Endonezce',
        'ms': 'Malayca', 'tl': 'Tagalog', 'ceb': 'Cebuano', 'jv': 'Cavaca', 'su': 'Sundaca',
        'sw': 'Svahili', 'am': 'Amharca', 'ha': 'Hausa', 'yo': 'Yoruba', 'ig': 'İgbo',
        'zu': 'Zulu', 'xh': 'Xhosa', 'af': 'Afrikaanca', 'st': 'Sotho', 'tn': 'Tswana',
        'ss': 'Swati', 've': 'Venda', 'ts': 'Tsonga', 'nd': 'Ndebele', 'sn': 'Shona',
        'rw': 'Kinyarwanda', 'ak': 'Akan', 'tw': 'Twi', 'ee': 'Ewe', 'lg': 'Luganda',
        'ny': 'Chichewa', 'mg': 'Malgaşça', 'so': 'Somalice', 'om': 'Oromoca', 'ti': 'Tigrinya',
        'he': 'İbranice', 'yi': 'Yidiş', 'lb': 'Lüksemburgca', 'fo': 'Faroece', 'kl': 'Grönlandca',
        'sm': 'Samoaca', 'to': 'Tongaca', 'fj': 'Fijice', 'haw': 'Hawaiice', 'mi': 'Maori',
        'co': 'Korsikaca', 'oc': 'Oksitanca', 'sc': 'Sardunyaca', 'rm': 'Romanşça',
        'fur': 'Friulanca', 'lld': 'Ladin', 'vec': 'Venedikçe', 'lmo': 'Lombardca',
        'pms': 'Piyemontece', 'nap': 'Napolice', 'scn': 'Sicilyaca', 'lij': 'Liguryaca',
        'pdc': 'Pennsylvania Almancası', 'bar': 'Bavyera Almancası', 'ksh': 'Kölnce',
        'swg': 'Svabyaca', 'gsw': 'İsviçre Almancası', 'als': 'Alsasça', 'wae': 'Walser',
        'sli': 'Silezyaca', 'hrx': 'Hunsrik', 'cim': 'Cimbri', 'mhn': 'Mocheno',
        'yue': 'Kantonca', 'nan': 'Min Nan', 'hak': 'Hakka', 'gan': 'Gan', 'wuu': 'Wu',
        'hsn': 'Xiang', 'cjy': 'Jin', 'cmn': 'Mandarin', 'dng': 'Dungan', 'ug': 'Uygurca',
        'bo': 'Tibetçe', 'dz': 'Dzongkha'
    }
    
    return language_names.get(lang_code, lang_code)

def get_language_icon(lang_code):
    """Dil kodu için ikon döndür"""
    language_icons = {
        'tr': '🇹🇷',
        'en': '🇺🇸',
        'es': '🇪🇸',
        'fr': '🇫🇷',
        'de': '🇩🇪',
        'it': '🇮🇹',
        'pt': '🇵🇹',
        'ru': '🇷🇺',
        'ja': '🇯🇵',
        'ko': '🇰🇷',
        'zh': '🇨🇳',
        'ar': '🇸🇦',
        'hi': '🇮🇳',
        'nl': '🇳🇱',
        'pl': '🇵🇱',
        'sv': '🇸🇪',
        'da': '🇩🇰',
        'no': '🇳🇴',
        'fi': '🇫🇮',
        'hu': '🇭🇺',
        'cs': '🇨🇿',
        'ro': '🇷🇴',
        'bg': '🇧🇬',
        'hr': '🇭🇷',
        'sk': '🇸🇰',
        'sl': '🇸🇮',
        'et': '🇪🇪',
        'lv': '🇱🇻',
        'lt': '🇱🇹',
        'mt': '🇲🇹',
        'ga': '🇮🇪',
        'cy': '🇬🇧',
        'eu': '🇪🇸',
        'ca': '🇪🇸',
        'gl': '🇪🇸',
        'is': '🇮🇸',
        'mk': '🇲🇰',
        'sq': '🇦🇱',
        'sr': '🇷🇸',
        'bs': '🇧🇦',
        'me': '🇲🇪',
        'uk': '🇺🇦',
        'be': '🇧🇾',
        'kk': '🇰🇿',
        'ky': '🇰🇬',
        'uz': '🇺🇿',
        'tg': '🇹🇯',
        'mn': '🇲🇳',
        'ka': '🇬🇪',
        'hy': '🇦🇲',
        'az': '🇦🇿',
        'fa': '🇮🇷',
        'ur': '🇵🇰',
        'bn': '🇧🇩',
        'ta': '🇮🇳',
        'te': '🇮🇳',
        'kn': '🇮🇳',
        'ml': '🇮🇳',
        'gu': '🇮🇳',
        'pa': '🇮🇳',
        'or': '🇮🇳',
        'as': '🇮🇳',
        'ne': '🇳🇵',
        'si': '🇱🇰',
        'my': '🇲🇲',
        'km': '🇰🇭',
        'lo': '🇱🇦',
        'th': '🇹🇭',
        'vi': '🇻🇳',
        'id': '🇮🇩',
        'ms': '🇲🇾',
        'tl': '🇵🇭',
        'ceb': '🇵🇭',
        'jv': '🇮🇩',
        'su': '🇮🇩',
        'sw': '🇹🇿',
        'am': '🇪🇹',
        'ha': '🇳🇬',
        'yo': '🇳🇬',
        'ig': '🇳🇬',
        'zu': '🇿🇦',
        'xh': '🇿🇦',
        'af': '🇿🇦',
        'st': '🇿🇦',
        'tn': '🇧🇼',
        'ss': '🇸🇿',
        've': '🇿🇦',
        'ts': '🇿🇦',
        'nd': '🇿🇼',
        'sn': '🇿🇼',
        'rw': '🇷🇼',
        'ak': '🇬🇭',
        'tw': '🇬🇭',
        'ee': '🇬🇭',
        'lg': '🇺🇬',
        'ny': '🇲🇼',
        'mg': '🇲🇬',
        'so': '🇸🇴',
        'om': '🇪🇹',
        'ti': '🇪🇷',
        'he': '🇮🇱',
        'yi': '🇮🇱',
        'lb': '🇱🇺',
        'fo': '🇫🇴',
        'kl': '🇬🇱',
        'sm': '🇼🇸',
        'to': '🇹🇴',
        'fj': '🇫🇯',
        'haw': '🇺🇸',
        'mi': '🇳🇿',
        'co': '🇫🇷',
        'oc': '🇫🇷',
        'sc': '🇮🇹',
        'rm': '🇨🇭',
        'fur': '🇮🇹',
        'lld': '🇮🇹',
        'vec': '🇮🇹',
        'lmo': '🇮🇹',
        'pms': '🇮🇹',
        'nap': '🇮🇹',
        'scn': '🇮🇹',
        'lij': '🇮🇹',
        'pdc': '🇺🇸',
        'bar': '🇩🇪',
        'ksh': '🇩🇪',
        'swg': '🇩🇪',
        'gsw': '🇨🇭',
        'als': '🇫🇷',
        'wae': '🇨🇭',
        'sli': '🇵🇱',
        'hrx': '🇧🇷',
        'cim': '🇮🇹',
        'mhn': '🇮🇹',
        'yue': '🇭🇰',
        'nan': '🇹🇼',
        'hak': '🇹🇼',
        'gan': '🇨🇳',
        'wuu': '🇨🇳',
        'hsn': '🇨🇳',
        'cjy': '🇨🇳',
        'cmn': '🇨🇳',
        'dng': '🇰🇿',
        'ug': '🇨🇳',
        'bo': '🇨🇳',
        'dz': '🇧🇹'
    }
    return language_icons.get(lang_code, '🌐')

def create_language_prompt(user_message, detected_lang):
    """Dil algılamasına göre prompt oluştur"""
    if detected_lang == 'tr':
        return f"""Sen Türkçe konuşan bir AI asistanısın. Kullanıcının mesajını Türkçe olarak yanıtla. 
        Eğer kullanıcı başka bir dilde yazarsa, o dilde de yanıt verebilirsin.
        
        Kullanıcı mesajı: {user_message}
        
        Lütfen Türkçe olarak yanıtla:"""
    
    elif detected_lang == 'en':
        return f"""You are an AI assistant who can speak English. Respond to the user's message in English.
        If the user writes in another language, you can also respond in that language.
        
        User message: {user_message}
        
        Please respond in English:"""
    
    else:
        lang_name = get_language_name(detected_lang)
        return f"""You are a multilingual AI assistant. The user's message appears to be in {lang_name} ({detected_lang}).
        Please respond in the same language as the user's message.
        
        User message: {user_message}
        
        Please respond in {lang_name}:"""

# CSS stilleri - Dinamik tema
base_css = """
    /* Sidebar genişliği - sadece açıkken geniş, kapanabilir */
    section[data-testid="stSidebar"] {
        width: 400px;
    }
    
    /* Sidebar kapalıyken normal genişlik */
    section[data-testid="stSidebar"][data-collapsed="true"] {
        width: auto;
    }
    
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
    
    .message-time {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
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
"""

# Session state başlatma
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
            st.session_state.api_url = "http://localhost:4000/api"

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

# Tema ayarını session state'e ekle
if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # "light" veya "dark" - varsayılan dark mode

# Sistem mesajı ayarını session state'e ekle
if "system_message" not in st.session_state:
    st.session_state.system_message = ""

# CSS stillerini uygula (session state başlatıldıktan sonra)
theme_css = get_theme_css(st.session_state.theme)
full_css = base_css + theme_css

st.markdown(f"""
<style>
{full_css}
</style>
""", unsafe_allow_html=True)

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
        
        # Model seçimi - daha açıklayıcı
        st.markdown("## 🤖 AI Model Seçimi")
        
        # Model bilgileri
        model_info = {
            "llama3-8b-8192": {
                "name": "Llama 3.1 8B",
                "description": "Meta'nın en yeni açık kaynak modeli",
                "strengths": "Genel bilgi, kodlama, yaratıcılık",
                "speed": "Hızlı",
                "context": "8K token",
                "icon": "🦙"
            },
            "mixtral-8x7b-32768": {
                "name": "Mixtral 8x7B",
                "description": "Mistral AI'nin güçlü karışım uzmanı modeli",
                "strengths": "Karmaşık görevler, analiz, çok dilli",
                "speed": "Orta",
                "context": "32K token",
                "icon": "🌪️"
            },
            "gemma2-9b-it": {
                "name": "Gemma 2 9B",
                "description": "Google'ın eğitim odaklı modeli",
                "strengths": "Eğitim, açıklama, öğretim",
                "speed": "Hızlı",
                "context": "8K token",
                "icon": "💎"
            }
        }
        
        # Model seçimi
        model = st.selectbox(
            "🤖 AI Model Seçin:",
            ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"],
            format_func=lambda x: f"{model_info[x]['icon']} {model_info[x]['name']}",
            help="Kullanılacak AI modelini seçin"
        )
        
        # Seçili model hakkında detaylı bilgi
        selected_model = model_info[model]
        
        st.markdown(f"""
        ### 📋 {selected_model['icon']} {selected_model['name']}
        
        **📝 Açıklama:** {selected_model['description']}
        
        **💪 Güçlü Yanları:** {selected_model['strengths']}
        
        **⚡ Hız:** {selected_model['speed']}
        
        **🧠 Bağlam:** {selected_model['context']}
        """)
        
        # Model önerisi
        if model == "llama3-8b-8192":
            st.info("💡 **Öneri:** Genel sohbet ve kodlama için ideal")
        elif model == "mixtral-8x7b-32768":
            st.info("💡 **Öneri:** Karmaşık analiz ve uzun metinler için ideal")
        elif model == "gemma2-9b-it":
            st.info("💡 **Öneri:** Eğitim ve öğretim için ideal")
        
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
        
        # Tema Ayarları
        st.markdown("## 🌙 Tema Ayarları")
        
        # Mevcut temayı göster
        current_theme = st.session_state.theme
        theme_icon = "🌙" if current_theme == "dark" else "☀️"
        st.markdown(f"**{theme_icon} Mevcut Tema:** {current_theme.title()}")
        
        # Tema seçimi
        col1, col2 = st.columns(2)
        with col1:
            if st.button("☀️ Aydınlık Tema", use_container_width=True):
                st.session_state.theme = "light"
                st.success("☀️ Aydınlık tema aktif!")
                st.rerun()
        
        with col2:
            if st.button("🌙 Karanlık Tema", use_container_width=True):
                st.session_state.theme = "dark"
                st.success("🌙 Karanlık tema aktif!")
                st.rerun()
        
        # Otomatik tema (sistem ayarına göre)
        if st.button("🔄 Sistem Teması", use_container_width=True):
            # Basit sistem teması algılama (geliştirilebilir)
            import datetime
            current_hour = datetime.datetime.now().hour
            if 6 <= current_hour <= 18:  # 06:00-18:00 arası aydınlık
                st.session_state.theme = "light"
                st.success("☀️ Sistem teması: Aydınlık")
            else:
                st.session_state.theme = "dark"
                st.success("🌙 Sistem teması: Karanlık")
            st.rerun()
        
        st.markdown("---")
        
        # Dil Ayarları
        st.markdown("## 🌍 Dil Ayarları")
        
        # Dil algılama ayarları
        if 'auto_detect_language' not in st.session_state:
            st.session_state.auto_detect_language = True
        
        if 'preferred_language' not in st.session_state:
            st.session_state.preferred_language = 'tr'
        
        # Otomatik dil algılama
        auto_detect = st.checkbox(
            "🔍 Otomatik Dil Algılama",
            value=st.session_state.auto_detect_language,
            help="Kullanıcının mesajının dilini otomatik olarak algıla"
        )
        
        if auto_detect != st.session_state.auto_detect_language:
            st.session_state.auto_detect_language = auto_detect
            st.success("✅ Dil algılama ayarı güncellendi!")
        
        # Tercih edilen dil seçimi
        if not st.session_state.auto_detect_language:
            # Tüm desteklenen diller
            all_languages = [
                "tr", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "nl", "pl", "sv", 
                "da", "no", "fi", "hu", "cs", "ro", "bg", "hr", "sk", "sl", "et", "lv", "lt", "mt", "ga", "cy", 
                "eu", "ca", "gl", "is", "mk", "sq", "sr", "bs", "me", "uk", "be", "kk", "ky", "uz", "tg", "mn", 
                "ka", "hy", "az", "fa", "ur", "bn", "ta", "te", "kn", "ml", "gu", "pa", "or", "as", "ne", "si", 
                "my", "km", "lo", "th", "vi", "id", "ms", "tl", "ceb", "jv", "su", "sw", "am", "ha", "yo", "ig",
                "zu", "xh", "af", "st", "tn", "ss", "ve", "ts", "nd", "sn", "rw", "ak", "tw", "ee", "lg", "ny", 
                "mg", "so", "om", "ti", "he", "yi", "lb", "fo", "kl", "sm", "to", "fj", "haw", "mi", "co", "oc", 
                "sc", "rm", "fur", "lld", "vec", "lmo", "pms", "nap", "scn", "lij", "pdc", "bar", "ksh", "swg", 
                "gsw", "als", "wae", "sli", "hrx", "cim", "mhn", "yue", "nan", "hak", "gan", "wuu", "hsn", "cjy", 
                "cmn", "dng", "ug", "bo", "dz"
            ]
            
            preferred_lang = st.selectbox(
                "🎯 Tercih Edilen Dil:",
                all_languages,
                format_func=lambda x: f"{get_language_icon(x)} {get_language_name(x)}",
                index=all_languages.index(st.session_state.preferred_language) if st.session_state.preferred_language in all_languages else 0,
                help="Bot'un yanıt vereceği tercih edilen dil"
            )
            
            if preferred_lang != st.session_state.preferred_language:
                st.session_state.preferred_language = preferred_lang
                st.success(f"✅ Tercih edilen dil: {get_language_icon(preferred_lang)} {get_language_name(preferred_lang)}")
        
        # Dil test mesajı
        if st.button("🧪 Dil Test Mesajı Gönder", use_container_width=True):
            # Farklı dillerde test mesajları
            test_messages = [
                ("Merhaba! Nasılsın? Bugün hava çok güzel.", "Türkçe"),
                ("Hello! How are you? The weather is beautiful today.", "İngilizce"),
                ("Hola! ¿Cómo estás? El tiempo está muy hermoso hoy.", "İspanyolca"),
                ("Bonjour! Comment allez-vous? Le temps est très beau aujourd'hui.", "Fransızca"),
                ("Hallo! Wie geht es dir? Das Wetter ist heute sehr schön.", "Almanca"),
                ("Ciao! Come stai? Il tempo è molto bello oggi.", "İtalyanca"),
                ("Olá! Como você está? O tempo está muito bonito hoje.", "Portekizce"),
                ("Привет! Как дела? Сегодня очень красивая погода.", "Rusça"),
                ("こんにちは！お元気ですか？今日はとても美しい天気です。", "Japonca"),
                ("안녕하세요! 어떻게 지내세요? 오늘 날씨가 정말 아름답습니다.", "Korece"),
                ("你好！你好吗？今天天气很美丽。", "Çince"),
                ("مرحبا! كيف حالك؟ الطقس جميل جدا اليوم.", "Arapça")
            ]
            
            st.markdown("### 🧪 Dil Algılama Test Sonuçları:")
            
            for test_message, expected_lang in test_messages:
                detected_lang = detect_language(test_message)
                lang_name = get_language_name(detected_lang)
                lang_icon = get_language_icon(detected_lang)
                
                # Doğru algılanan diller için ✅, yanlış için ❌
                expected_codes = {
                    "Türkçe": "tr", "İngilizce": "en", "İspanyolca": "es", "Fransızca": "fr",
                    "Almanca": "de", "İtalyanca": "it", "Portekizce": "pt", "Rusça": "ru",
                    "Japonca": "ja", "Korece": "ko", "Çince": "zh", "Arapça": "ar"
                }
                expected_code = expected_codes.get(expected_lang, "")
                expected_icon = "✅" if detected_lang == expected_code else "❌"
                
                st.info(f"{expected_icon} **{expected_lang}:** {lang_icon} {lang_name} ({detected_lang})")
                st.caption(f"📝 Test: {test_message}")
                st.markdown("---")
        
        # Desteklenen diller
        with st.expander("🌐 Desteklenen Diller (150+ Dil)"):
            # Tüm dilleri kategorilere ayır
            european_languages = [
                ("tr", "Türkçe"), ("en", "İngilizce"), ("es", "İspanyolca"), ("fr", "Fransızca"),
                ("de", "Almanca"), ("it", "İtalyanca"), ("pt", "Portekizce"), ("ru", "Rusça"),
                ("nl", "Hollandaca"), ("pl", "Lehçe"), ("sv", "İsveççe"), ("da", "Danca"),
                ("no", "Norveççe"), ("fi", "Fince"), ("hu", "Macarca"), ("cs", "Çekçe"),
                ("ro", "Romence"), ("bg", "Bulgarca"), ("hr", "Hırvatça"), ("sk", "Slovakça"),
                ("sl", "Slovence"), ("et", "Estonca"), ("lv", "Letonca"), ("lt", "Litvanca"),
                ("mt", "Maltaca"), ("ga", "İrlandaca"), ("cy", "Galce"), ("eu", "Baskça"),
                ("ca", "Katalanca"), ("gl", "Galiçyaca"), ("is", "İzlandaca"), ("mk", "Makedonca"),
                ("sq", "Arnavutça"), ("sr", "Sırpça"), ("bs", "Boşnakça"), ("me", "Karadağca"),
                ("uk", "Ukraynaca"), ("be", "Belarusça"), ("kk", "Kazakça"), ("ky", "Kırgızca"),
                ("uz", "Özbekçe"), ("tg", "Tacikçe"), ("mn", "Moğolca"), ("ka", "Gürcüce"),
                ("hy", "Ermenice"), ("az", "Azerbaycanca")
            ]
            
            asian_languages = [
                ("ja", "Japonca"), ("ko", "Korece"), ("zh", "Çince"), ("ar", "Arapça"),
                ("hi", "Hintçe"), ("fa", "Farsça"), ("ur", "Urduca"), ("bn", "Bengalce"),
                ("ta", "Tamilce"), ("te", "Telugu"), ("kn", "Kannada"), ("ml", "Malayalam"),
                ("gu", "Gujarati"), ("pa", "Pencapça"), ("or", "Odiya"), ("as", "Assamca"),
                ("ne", "Nepalce"), ("si", "Seylanca"), ("my", "Myanmar"), ("km", "Kamboçyaca"),
                ("lo", "Laoca"), ("th", "Tayca"), ("vi", "Vietnamca"), ("id", "Endonezce"),
                ("ms", "Malayca"), ("tl", "Tagalog"), ("ceb", "Cebuano"), ("jv", "Cavaca"),
                ("su", "Sundaca"), ("yue", "Kantonca"), ("nan", "Min Nan"), ("hak", "Hakka"),
                ("gan", "Gan"), ("wuu", "Wu"), ("hsn", "Xiang"), ("cjy", "Jin"), ("cmn", "Mandarin"),
                ("dng", "Dungan"), ("ug", "Uygurca"), ("bo", "Tibetçe"), ("dz", "Dzongkha")
            ]
            
            african_languages = [
                ("sw", "Svahili"), ("am", "Amharca"), ("ha", "Hausa"), ("yo", "Yoruba"),
                ("ig", "İgbo"), ("zu", "Zulu"), ("xh", "Xhosa"), ("af", "Afrikaanca"),
                ("st", "Sotho"), ("tn", "Tswana"), ("ss", "Swati"), ("ve", "Venda"),
                ("ts", "Tsonga"), ("nd", "Ndebele"), ("sn", "Shona"), ("rw", "Kinyarwanda"),
                ("ak", "Akan"), ("tw", "Twi"), ("ee", "Ewe"), ("lg", "Luganda"),
                ("ny", "Chichewa"), ("mg", "Malgaşça"), ("so", "Somalice"), ("om", "Oromoca"),
                ("ti", "Tigrinya")
            ]
            
            other_languages = [
                ("he", "İbranice"), ("yi", "Yidiş"), ("lb", "Lüksemburgca"), ("fo", "Faroece"),
                ("kl", "Grönlandca"), ("sm", "Samoaca"), ("to", "Tongaca"), ("fj", "Fijice"),
                ("haw", "Hawaiice"), ("mi", "Maori"), ("co", "Korsikaca"), ("oc", "Oksitanca"),
                ("sc", "Sardunyaca"), ("rm", "Romanşça"), ("fur", "Friulanca"), ("lld", "Ladin"),
                ("vec", "Venedikçe"), ("lmo", "Lombardca"), ("pms", "Piyemontece"), ("nap", "Napolice"),
                ("scn", "Sicilyaca"), ("lij", "Liguryaca"), ("pdc", "Pennsylvania Almancası"),
                ("bar", "Bavyera Almancası"), ("ksh", "Kölnce"), ("swg", "Svabyaca"),
                ("gsw", "İsviçre Almancası"), ("als", "Alsasça"), ("wae", "Walser"),
                ("sli", "Silezyaca"), ("hrx", "Hunsrik"), ("cim", "Cimbri"), ("mhn", "Mocheno")
            ]
            
            # Kategorileri göster
            tab1, tab2, tab3, tab4 = st.tabs(["🇪🇺 Avrupa", "🌏 Asya", "🌍 Afrika", "🌎 Diğer"])
            
            with tab1:
                cols = st.columns(4)
                for i, (code, name) in enumerate(european_languages):
                    with cols[i % 4]:
                        st.markdown(f"{get_language_icon(code)} {name}")
            
            with tab2:
                cols = st.columns(4)
                for i, (code, name) in enumerate(asian_languages):
                    with cols[i % 4]:
                        st.markdown(f"{get_language_icon(code)} {name}")
            
            with tab3:
                cols = st.columns(4)
                for i, (code, name) in enumerate(african_languages):
                    with cols[i % 4]:
                        st.markdown(f"{get_language_icon(code)} {name}")
            
            with tab4:
                cols = st.columns(4)
                for i, (code, name) in enumerate(other_languages):
                    with cols[i % 4]:
                        st.markdown(f"{get_language_icon(code)} {name}")
        
        st.markdown("---")
        
        # Sistem Mesajı Ayarları
        st.markdown("## 🎭 Bot Karakteri Ayarları")
        
        # Sistem mesajı açıklaması
        st.info("💡 **Sistem mesajı**, bot'un karakterini ve davranışını belirler. Örneğin: 'Sen bir matematik öğretmenisin' veya 'Sen bir programcısın'")
        
        # Sistem mesajı girişi
        system_message = st.text_area(
            "🎭 Bot Karakteri:",
            value=st.session_state.system_message,
            placeholder="Örnek: Sen bir matematik öğretmenisin. Öğrencilere sabırla ve anlaşılır şekilde matematik konularını açıklarsın.",
            height=100,
            help="Bot'un karakterini ve davranışını tanımlayan mesaj"
        )
        
        if system_message != st.session_state.system_message:
            st.session_state.system_message = system_message
            st.success("✅ Bot karakteri güncellendi!")
        
        # Hazır karakter şablonları
        st.markdown("### 📋 Hazır Karakter Şablonları")
        
        character_templates = {
            "Matematik Öğretmeni": "Sen bir matematik öğretmenisin. Öğrencilere sabırla ve anlaşılır şekilde matematik konularını açıklarsın. Karmaşık konuları basit adımlara bölersin.",
            "Programcı": "Sen bir deneyimli programcısın. Kod yazma, hata ayıklama ve yazılım geliştirme konularında uzmanlaşmışsın. Pratik çözümler önerirsin.",
            "Doktor": "Sen bir doktorsun. Sağlık konularında bilgilendirici ve güvenilir bilgiler verirsin. Ancak teşhis koymaz, sadece genel bilgi verirsin.",
            "Tarihçi": "Sen bir tarihçisin. Geçmiş olayları, kişileri ve dönemleri detaylı ve ilgi çekici şekilde anlatırsın. Tarihi bağlamları açıklarsın.",
            "Bilim İnsanı": "Sen bir bilim insanısın. Bilimsel konuları merak uyandırıcı şekilde açıklarsın. Deneyler ve araştırmalar hakkında bilgi verirsin.",
            "Yazar": "Sen bir yaratıcı yazarsın. Hikayeler, şiirler ve yaratıcı metinler yazarsın. Kelimeleri güzel ve etkili şekilde kullanırsın.",
            "Seyahat Rehberi": "Sen bir seyahat rehberisin. Ülkeler, şehirler ve turistik yerler hakkında bilgi verirsin. Seyahat önerileri sunarsın.",
            "Spor Koçu": "Sen bir spor koçusun. Fitness, egzersiz ve sağlıklı yaşam konularında rehberlik edersin. Motivasyon verirsin.",
            "Müzik Öğretmeni": "Sen bir müzik öğretmenisin. Müzik teorisi, enstrümanlar ve besteciler hakkında bilgi verirsin. Müzik zevki geliştirmeye yardım edersin.",
            "Sanat Eleştirmeni": "Sen bir sanat eleştirmenisin. Resim, heykel, mimari ve diğer sanat türleri hakkında bilgi verirsin. Sanat eserlerini analiz edersin."
        }
        
        # Karakter şablonları için butonlar
        col1, col2 = st.columns(2)
        for i, (name, template) in enumerate(character_templates.items()):
            with col1 if i % 2 == 0 else col2:
                if st.button(f"📝 {name}", key=f"template_{i}", use_container_width=True):
                    st.session_state.system_message = template
                    st.success(f"✅ {name} karakteri seçildi!")
                    st.rerun()
        
        # Sistem mesajını temizle
        if st.button("🗑️ Karakteri Temizle", use_container_width=True):
            st.session_state.system_message = ""
            st.success("✅ Bot karakteri temizlendi!")
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
        # Dil algılama (gizli)
        detected_lang = None
        if st.session_state.get('auto_detect_language', True):
            detected_lang = detect_language(prompt)
        else:
            detected_lang = st.session_state.get('preferred_language', 'tr')
        
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
                    # API'ye istek gönder (sadece kullanıcı mesajını gönder, backend geçmişi alacak)
                    request_data = {
                        "message": prompt,  # Sadece kullanıcının mesajını gönder
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "system_message": st.session_state.system_message  # Sistem mesajını ekle
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