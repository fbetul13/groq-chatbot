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
import pandas as pd
import os
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
        
        /* Sidebar butonları için küçük font */
        .sidebar .stButton > button {
            font-size: 0.75rem !important;
            padding: 0.25rem 0.5rem !important;
            min-height: auto !important;
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
        
        /* Sidebar butonları için küçük font */
        .sidebar .stButton > button {
            font-size: 0.75rem !important;
            padding: 0.25rem 0.5rem !important;
            min-height: auto !important;
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
    
    /* Mesaj butonları için özel stiller */
    .message-btn {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        transition: all 0.3s ease;
    }
    
    .message-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .resend-btn {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
    }
    
    .copy-btn {
        background: linear-gradient(90deg, #17a2b8 0%, #6f42c1 100%);
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
    # Environment variable'dan al, yoksa localhost kullan
    api_url = os.environ.get('BACKEND_API_URL', 'http://localhost:5002/api')
    st.session_state.api_url = api_url

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "cookies" not in st.session_state:
    st.session_state.cookies = {}

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
                    "time": datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')).strftime("%H:%M"),
                    "message_id": msg.get('id'),  # Backend'den gelen mesaj ID'si
                    "edited": msg.get('edited', False),
                    "edit_time": msg.get('edit_time')
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
                key=f"download_json_{session_id}_{int(time.time())}"
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
                key=f"download_csv_{session_id}_{int(time.time())}"
            )
            return True
        else:
            st.error("İndirme hatası")
            return False
    except Exception as e:
        st.error(f"İndirme hatası: {str(e)}")
        return False

def download_session_pdf(session_id):
    """Sohbet oturumunu PDF formatında indir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/sessions/{session_id}/download-pdf",
            cookies=st.session_state.get('cookies', {}),
            stream=True
        )
        if response.status_code == 200:
            # Dosya adını al
            content_disposition = response.headers.get('content-disposition', '')
            filename = 'sohbet.pdf'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Dosyayı indir
            st.download_button(
                label="📄 PDF İndir",
                data=response.content,
                file_name=filename,
                mime="application/pdf",
                key=f"download_pdf_{session_id}_{int(time.time())}"
            )
            return True
        else:
            st.error("İndirme hatası")
            return False
    except Exception as e:
        st.error(f"İndirme hatası: {str(e)}")
        return False

def download_session_txt(session_id):
    """Sohbet oturumunu TXT formatında indir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/sessions/{session_id}/download-txt",
            cookies=st.session_state.get('cookies', {}),
            stream=True
        )
        if response.status_code == 200:
            # Dosya adını al
            content_disposition = response.headers.get('content-disposition', '')
            filename = 'sohbet.txt'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Dosyayı indir
            st.download_button(
                label="📝 TXT İndir",
                data=response.content,
                file_name=filename,
                mime="text/plain",
                key=f"download_txt_{session_id}_{int(time.time())}"
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

def set_edit_state(message_index, content):
    """Düzenleme durumunu ayarla"""
    st.session_state.editing_message_index = message_index
    st.session_state.editing_message_content = content

def edit_message(message_index, new_content):
    """Mesajı düzenle ve chatbot yanıtını yeniden oluştur"""
    try:
        if 0 <= message_index < len(st.session_state.messages):
            message = st.session_state.messages[message_index]
            
            # Sadece kullanıcı mesajları düzenlenebilir
            if message["role"] != "user":
                st.error("❌ Sadece kullanıcı mesajları düzenlenebilir")
                return False
            
            # Backend'e mesaj güncelleme isteği gönder
            if st.session_state.current_session_id and message.get("message_id"):
                response = requests.put(
                    f"{st.session_state.api_url}/sessions/{st.session_state.current_session_id}/messages/{message['message_id']}/update",
                    json={"content": new_content},
                    timeout=10,
                    cookies=st.session_state.get('cookies', {})
                )
                
                if response.status_code == 200:
                    # Mesajı güncelle
                    st.session_state.messages[message_index]["content"] = new_content
                    st.session_state.messages[message_index]["edited"] = True
                    st.session_state.messages[message_index]["edit_time"] = datetime.now().strftime("%H:%M")
                    
                    # Bu mesajdan sonraki tüm mesajları sil (chatbot yanıtları)
                    st.session_state.messages = st.session_state.messages[:message_index + 1]
                    
                    # Düzenlenen mesajı otomatik olarak gönder
                    st.session_state.auto_send_message = new_content
                    
                    st.success("✅ Mesaj düzenlendi! Chatbot yanıtı yeniden oluşturulacak.")
                    return True
                else:
                    st.error(f"❌ Backend hatası: {response.status_code}")
                    return False
            else:
                # Session ID yoksa sadece frontend'de güncelle
                st.session_state.messages[message_index]["content"] = new_content
                st.session_state.messages[message_index]["edited"] = True
                st.session_state.messages[message_index]["edit_time"] = datetime.now().strftime("%H:%M")
                st.success("✅ Mesaj düzenlendi!")
                return True
        else:
            st.error("❌ Geçersiz mesaj indeksi")
            return False
    except Exception as e:
        st.error(f"❌ Düzenleme hatası: {str(e)}")
        return False

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

def display_token_warning(token_info):
    """Token uyarısını göster"""
    if not token_info:
        return
    
    warning_level = token_info.get('warning_level', 'safe')
    warning_message = token_info.get('warning_message', '')
    
    if warning_level == 'critical':
        st.error(f"🚨 {warning_message}")
    elif warning_level == 'warning':
        st.warning(f"⚠️ {warning_message}")
    elif warning_level == 'info':
        st.info(f"ℹ️ {warning_message}")
    elif warning_level == 'safe':
        st.success(f"✅ Token durumu güvenli")
    
    # Token detaylarını göster
    with st.expander("🔢 Token Detayları"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mevcut Token", token_info.get('current_tokens', 0))
        with col2:
            st.metric("Model Limiti", token_info.get('model_limit', 8192))
        with col3:
            st.metric("Kullanılabilir", token_info.get('available_tokens', 0))

def display_token_status_sidebar(token_info):
    """Sidebar'da token durumunu göster"""
    if not token_info:
        return
    
    warning_level = token_info.get('warning_level', 'safe')
    current_tokens = token_info.get('current_tokens', 0)
    model_limit = token_info.get('model_limit', 8192)
    available_tokens = token_info.get('available_tokens', 0)
    
    # Token kullanım yüzdesi
    usage_percentage = (current_tokens / model_limit) * 100
    
    # Renk seçimi
    if warning_level == 'critical':
        color = "🔴"
        progress_color = "red"
    elif warning_level == 'warning':
        color = "🟡"
        progress_color = "orange"
    elif warning_level == 'info':
        color = "🔵"
        progress_color = "blue"
    else:
        color = "🟢"
        progress_color = "green"
    
    # Sidebar'da göster
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔢 Token Durumu")
    
    # Progress bar
    st.sidebar.progress(usage_percentage / 100, text=f"{color} {usage_percentage:.1f}%")
    
    # Kısa bilgi
    st.sidebar.markdown(f"**Kullanılan:** {current_tokens:,}")
    st.sidebar.markdown(f"**Limit:** {model_limit:,}")
    st.sidebar.markdown(f"**Kalan:** {available_tokens:,}")
    
    # Uyarı mesajı (sadece kritik durumlarda)
    if warning_level in ['critical', 'warning']:
        st.sidebar.warning(f"⚠️ {warning_message}")
    
    # Detay butonu
    if st.sidebar.button("📊 Detaylı Görünüm", key="token_details"):
        st.session_state.show_token_details = not st.session_state.get('show_token_details', False)
    
    # Detaylı görünüm (eğer açıksa)
    if st.session_state.get('show_token_details', False):
        with st.sidebar.expander("📈 Token Analizi", expanded=True):
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Kullanılan", f"{current_tokens:,}")
            with col2:
                st.metric("Kalan", f"{available_tokens:,}")
            
            st.sidebar.markdown(f"**Model:** {token_info.get('model', 'N/A')}")
            st.sidebar.markdown(f"**Durum:** {warning_level.upper()}")

def check_language_quality(text, language):
    """Dil yanıt kalitesini kontrol et"""
    if not text:
        return {"quality": "unknown", "issues": [], "score": 0}
    
    issues = []
    score = 100
    
    # Dil özel karakter kontrolü
    language_chars = {
        'tr': ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü'],
        'de': ['ä', 'ö', 'ü', 'ß'],
        'es': ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü'],
        'fr': ['é', 'è', 'ê', 'ë', 'à', 'â', 'ï', 'î', 'ô', 'û', 'ù', 'ü', 'ç'],
        'it': ['à', 'è', 'é', 'ì', 'ò', 'ù'],
        'pt': ['ã', 'õ', 'ç', 'á', 'é', 'í', 'ó', 'ú'],
        'ru': ['ё', 'й', 'ъ', 'ь', 'э', 'ю', 'я'],
        'ja': ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ'],  # Hiragana örnekleri
        'ko': ['가', '나', '다', '라', '마', '바', '사', '아', '자', '차'],  # Hangul örnekleri
        'zh': ['你', '我', '他', '她', '它', '们', '的', '是', '在', '有'],  # Çince örnekleri
        'ar': ['ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر']  # Arapça örnekleri
    }
    
    if language in language_chars:
        chars = language_chars[language]
        missing_chars = []
        for char in chars:
            if char in text.lower() and char not in text:
                missing_chars.append(char)
        
        if missing_chars:
            issues.append(f"{language.upper()} karakterler eksik: {', '.join(missing_chars)}")
            score -= 10
    
    # Tekrar kontrolü
    words = text.lower().split()
    word_count = {}
    for word in words:
        if len(word) > 3:  # Sadece uzun kelimeleri kontrol et
            word_count[word] = word_count.get(word, 0) + 1
            if word_count[word] > 3:  # 3'ten fazla tekrar
                issues.append(f"Tekrar eden kelime: '{word}'")
                score -= 5
    
    # Cümle uzunluğu kontrolü
    sentences = text.split('.')
    long_sentences = [s for s in sentences if len(s.split()) > 20]
    if long_sentences:
        issues.append(f"{len(long_sentences)} çok uzun cümle var")
        score -= 10
    
    # Dil özel anlamsız kelime kontrolü
    meaningless_words = {
        'tr': ['şey', 'falan', 'filan', 'böyle', 'şöyle', 'vermemecessary'],
        'en': ['thing', 'stuff', 'like', 'you know', 'basically'],
        'de': ['Ding', 'Sache', 'so', 'halt', 'eigentlich'],
        'es': ['cosa', 'así', 'pues', 'bueno', 'vamos'],
        'fr': ['chose', 'truc', 'comme', 'enfin', 'voilà'],
        'it': ['cosa', 'così', 'dunque', 'beh', 'ecco'],
        'pt': ['coisa', 'assim', 'então', 'bem', 'pronto'],
        'ru': ['вещь', 'так', 'ну', 'вот', 'знаешь'],
        'ja': ['もの', 'こと', 'そう', 'まあ', 'えっと'],
        'ko': ['것', '그래', '음', '저기', '그니까'],
        'zh': ['东西', '这样', '那个', '就是', '然后'],
        'ar': ['شيء', 'هكذا', 'حسناً', 'أي', 'يعني']
    }
    
    if language in meaningless_words:
        words_to_check = meaningless_words[language]
        meaningless_count = sum(1 for word in words if word in words_to_check)
        if meaningless_count > 2:
            issues.append("Çok fazla anlamsız kelime kullanılmış")
            score -= 15
    
    # Konu tutarlılığı kontrolü (basit)
    topic_keywords = {
        'japan': ['japan', 'japanese', 'tokyo', 'osaka', 'kyoto'],
        'shopping': ['shopping', 'buy', 'store', 'market', 'shop'],
        'math': ['laplace', 'equation', 'differential', 'mathematics', 'math']
    }
    
    # Eğer önceki konu ile şu anki konu çok farklıysa uyarı ver
    text_lower = text.lower()
    current_topics = []
    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            current_topics.append(topic)
    
    if len(current_topics) > 2:  # Çok fazla farklı konu varsa
        issues.append("Çok fazla farklı konu karışmış")
        score -= 10
    
    # Kalite seviyesi
    if score >= 90:
        quality = "excellent"
    elif score >= 75:
        quality = "good"
    elif score >= 60:
        quality = "fair"
    else:
        quality = "poor"
    
    return {
        "quality": quality,
        "issues": issues,
        "score": max(0, score)
    }

def check_turkish_quality(text):
    """Türkçe yanıt kalitesini kontrol et (geriye uyumluluk için)"""
    return check_language_quality(text, 'tr')

def display_api_status_sidebar():
    """Sidebar'da API durumunu göster"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📡 API Durumu")
    
    try:
        start_time = time.time()
        response = requests.get(f"{st.session_state.api_url}/health", timeout=3)
        response_time = (time.time() - start_time) * 1000  # milisaniye
        
        if response.status_code == 200:
            # Hızlı yanıt (< 100ms)
            if response_time < 100:
                status_icon = "🟢"
                status_text = "Mükemmel"
                status_color = "success"
            # Normal yanıt (100-500ms)
            elif response_time < 500:
                status_icon = "🟡"
                status_text = "İyi"
                status_color = "info"
            # Yavaş yanıt (> 500ms)
            else:
                status_icon = "🟠"
                status_text = "Yavaş"
                status_color = "warning"
            
            st.sidebar.success(f"{status_icon} Bağlantı Aktif")
            st.sidebar.caption(f"Yanıt süresi: {response_time:.0f}ms ({status_text})")
            
            # Performans göstergesi
            performance_percentage = min(100, max(0, (500 - response_time) / 500 * 100))
            st.sidebar.progress(performance_percentage / 100, text=f"⚡ Performans: {performance_percentage:.0f}%")
            
        else:
            st.sidebar.error(f"🔴 Bağlantı Hatası ({response.status_code})")
            st.sidebar.caption("Sunucu yanıt veriyor ama hata döndürüyor")
            
    except requests.exceptions.Timeout:
        st.sidebar.error("⏰ Zaman Aşımı")
        st.sidebar.caption("API 3 saniye içinde yanıt vermedi")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("🔌 Bağlantı Yok")
        st.sidebar.caption("Backend çalışmıyor olabilir")
    except Exception as e:
        st.sidebar.error("❌ Bilinmeyen Hata")
        st.sidebar.caption(f"Hata: {str(e)[:50]}...")

def handle_api_error(error_type, error_message, response=None):
    """API hatalarını kullanıcı dostu şekilde göster"""
    
    error_templates = {
        "timeout": {
            "icon": "⏰",
            "title": "Yanıt Zaman Aşımı",
            "message": "AI çok uzun süre düşündü ve yanıt veremedi.",
            "suggestions": [
                "Daha kısa bir mesaj deneyin",
                "Maksimum token sayısını azaltın",
                "İnternet bağlantınızı kontrol edin"
            ]
        },
        "connection": {
            "icon": "🔌",
            "title": "Bağlantı Hatası",
            "message": "AI sunucusuna bağlanılamıyor.",
            "suggestions": [
                "Backend'in çalıştığından emin olun",
                "İnternet bağlantınızı kontrol edin",
                "API URL'sini kontrol edin"
            ]
        },
        "server_error": {
            "icon": "🚨",
            "title": "Sunucu Hatası",
            "message": "AI sunucusunda bir sorun oluştu.",
            "suggestions": [
                "Birkaç dakika bekleyin",
                "Mesajı tekrar gönderin",
                "Farklı bir model deneyin"
            ]
        },
        "rate_limit": {
            "icon": "🚦",
            "title": "Hız Limiti",
            "message": "Çok fazla istek gönderdiniz.",
            "suggestions": [
                "Birkaç dakika bekleyin",
                "Mesaj gönderme hızınızı azaltın"
            ]
        },
        "authentication": {
            "icon": "🔐",
            "title": "Kimlik Doğrulama Hatası",
            "message": "Oturum süreniz dolmuş olabilir.",
            "suggestions": [
                "Tekrar giriş yapın",
                "Sayfayı yenileyin"
            ]
        },
        "unknown": {
            "icon": "❓",
            "title": "Bilinmeyen Hata",
            "message": "Beklenmeyen bir hata oluştu.",
            "suggestions": [
                "Sayfayı yenileyin",
                "Tekrar deneyin",
                "Sorun devam ederse bildirin"
            ]
        }
    }
    
    # Hata tipini belirle
    if "timeout" in str(error_message).lower() or "timeout" in error_type:
        error_info = error_templates["timeout"]
    elif "connection" in str(error_message).lower() or "connection" in error_type:
        error_info = error_templates["connection"]
    elif "rate limit" in str(error_message).lower():
        error_info = error_templates["rate_limit"]
    elif "authentication" in str(error_message).lower() or "401" in str(error_message):
        error_info = error_templates["authentication"]
    elif response and response.status_code >= 500:
        error_info = error_templates["server_error"]
    else:
        error_info = error_templates["unknown"]
    
    # Hata mesajını göster
    st.error(f"{error_info['icon']} **{error_info['title']}**")
    st.info(f"💡 {error_info['message']}")
    
    # Önerileri göster
    with st.expander("🔧 Çözüm Önerileri", expanded=False):
        for i, suggestion in enumerate(error_info['suggestions'], 1):
            st.markdown(f"{i}. {suggestion}")
    
    # Tekrar deneme butonu
    if st.button("🔄 Tekrar Dene", key=f"retry_{int(time.time())}"):
        st.rerun()

def show_typing_animation():
    """Yazma animasyonu göster"""
    # Basit yazma animasyonu
    typing_indicators = ["🤔 Düşünüyor", "🤔 Düşünüyor.", "🤔 Düşünüyor..", "🤔 Düşünüyor..."]
    
    # Progress bar ile animasyon
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(4):
        progress_bar.progress((i + 1) / 4)
        status_text.text(typing_indicators[i])
        time.sleep(0.5)
    
    return progress_bar, status_text

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
            },
            "llama-3.1-8b-instant": {
                "name": "Llama 3.1 8B Instant",
                "description": "Meta'nın ultra hızlı anlık yanıt modeli",
                "strengths": "Hızlı yanıt, genel sohbet, kodlama",
                "speed": "Çok Hızlı",
                "context": "131K token",
                "icon": "⚡"
            },
            "llama-3.3-70b-versatile": {
                "name": "Llama 3.3 70B Versatile",
                "description": "Meta'nın en güçlü çok amaçlı modeli",
                "strengths": "Karmaşık analiz, yaratıcılık, uzun metinler",
                "speed": "Orta",
                "context": "131K token",
                "icon": "🧠"
            },
            "qwen/qwen3-32b": {
                "name": "Qwen 3 32B",
                "description": "Alibaba'nın gelişmiş çok dilli modeli",
                "strengths": "Çok dilli, akıl yürütme, ajan yetenekleri",
                "speed": "Hızlı",
                "context": "32K token",
                "icon": "🌟"
            },
            "moonshotai/kimi-k2-instruct": {
                "name": "Kimi K2 Instruct",
                "description": "Moonshot AI'nin 1T parametreli dev modeli",
                "strengths": "Gelişmiş araç kullanımı, ajan zekası, karmaşık görevler",
                "speed": "Orta",
                "context": "32K token",
                "icon": "🚀"
            }
        }
        
        # Model seçimi
        model = st.selectbox(
            "🤖 AI Model Seçin:",
            ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen/qwen3-32b", "moonshotai/kimi-k2-instruct"],
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
        elif model == "llama-3.1-8b-instant":
            st.info("💡 **Öneri:** Hızlı yanıt gerektiren sohbetler için ideal")
        elif model == "llama-3.3-70b-versatile":
            st.info("💡 **Öneri:** Karmaşık analiz ve yaratıcı görevler için ideal")
        elif model == "qwen/qwen3-32b":
            st.info("💡 **Öneri:** Çok dilli sohbet ve akıl yürütme için ideal")
        elif model == "moonshotai/kimi-k2-instruct":
            st.info("💡 **Öneri:** Gelişmiş araç kullanımı ve ajan görevleri için ideal")
        
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
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        if st.button("📄 JSON", key=f"download_json_{session_id}", help="JSON formatında indir"):
                            download_session_json(session_id)
                    
                    with col2:
                        if st.button("📊 CSV", key=f"download_csv_{session_id}", help="CSV formatında indir"):
                            download_session_csv(session_id)
                    
                    with col3:
                        if st.button("📄 PDF", key=f"download_pdf_{session_id}", help="PDF formatında indir"):
                            download_session_pdf(session_id)
                    
                    with col4:
                        if st.button("📝 TXT", key=f"download_txt_{session_id}", help="TXT formatında indir"):
                            download_session_txt(session_id)
                    
                    with col5:
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
        
        # API durumu ve token durumu
        display_api_status_sidebar()
        
        # Token durumu (eğer varsa)
        if hasattr(st.session_state, 'current_token_info') and st.session_state.current_token_info:
            display_token_status_sidebar(st.session_state.current_token_info)
        else:
            # Token bilgisi yoksa varsayılan göster
            st.sidebar.markdown("---")
            st.sidebar.markdown("## 🔢 Token Durumu")
            st.sidebar.info("💬 Mesaj gönderin, token durumu burada görünecek")
            
            # Varsayılan token bilgisi
            default_token_info = {
                "current_tokens": 0,
                "model_limit": 8192,
                "available_tokens": 8192,
                "warning_level": "safe",
                "warning_message": ""
            }
            display_token_status_sidebar(default_token_info)
        
        # Dil kalite ayarları
        st.sidebar.markdown("---")
        st.sidebar.markdown("## 🌍 Dil Kalite Kontrolü")
        
        # Kalite kontrolü açma/kapama
        if 'turkish_quality_check' not in st.session_state:
            st.session_state.turkish_quality_check = True
        
        quality_check = st.sidebar.checkbox(
            "🔍 Kalite Kontrolü",
            value=st.session_state.turkish_quality_check,
            help="Tüm dillerdeki yanıtların kalitesini kontrol et"
        )
        
        if quality_check != st.session_state.turkish_quality_check:
            st.session_state.turkish_quality_check = quality_check
            st.sidebar.success("✅ Kalite kontrolü güncellendi!")
        
        # Kalite eşiği
        if st.session_state.turkish_quality_check:
            if 'quality_threshold' not in st.session_state:
                st.session_state.quality_threshold = 80
            
            threshold = st.sidebar.slider(
                "📊 Kalite Eşiği",
                min_value=50,
                max_value=95,
                value=st.session_state.quality_threshold,
                step=5,
                help="Bu skorun altındaki yanıtlar için uyarı göster"
            )
            
            if threshold != st.session_state.quality_threshold:
                st.session_state.quality_threshold = threshold
                st.sidebar.success(f"✅ Kalite eşiği: {threshold}")

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
                
                # Düzenleme durumunu göster
                if message.get("edited", False):
                    st.caption(f"✏️ {message['time']} (düzenlendi: {message.get('edit_time', '')})")
                else:
                    st.caption(message["time"])
                
                # Her mesaj için kendi butonları
                if message["role"] == "user":
                    # Sadece en son kullanıcı mesajı için düzenleme butonu
                    user_messages = [j for j, msg in enumerate(st.session_state.messages) if msg["role"] == "user"]
                    if user_messages and i == user_messages[-1]:  # Bu en son kullanıcı mesajı mı?
                        st.button("✏️ Düzenle", key=f"edit_{i}", help="Bu mesajı düzenle", on_click=lambda idx=i, content=message["content"]: set_edit_state(idx, content))
                elif message["role"] == "assistant":
                    # Bot mesajları için butonlar
                    col1, col2, col3 = st.columns([1, 1, 6])
                    
                    with col1:
                        # Bu bot mesajını tekrar oluştur butonu
                        if st.button("🔄", key=f"regenerate_{i}", help="Bu yanıtı tekrar oluştur", use_container_width=True):
                            # Bu bot mesajını tekrar oluştur
                            if i > 0 and st.session_state.messages[i-1]["role"] == "user":
                                original_message = st.session_state.messages[i-1]["content"]
                                # Mesajı doğrudan gönder, rerun kullanma
                                st.session_state.auto_send_message = original_message
                    
                    with col2:
                        # Kopyala butonu (küçük)
                        if st.button("📋", key=f"copy_{i}", help="Yanıtı panoya kopyala", use_container_width=True):
                            # Mesajı panoya kopyala
                            try:
                                import pyperclip
                                pyperclip.copy(message["content"])
                                st.success("✅")
                            except ImportError:
                                st.info("📋")
                    
                    with col3:
                        # Boş alan
                        st.markdown("")

    # Mesaj düzenleme formu
    if hasattr(st.session_state, 'editing_message_index') and st.session_state.editing_message_index is not None:
        st.markdown("### ✏️ Mesaj Düzenle")
        edited_content = st.text_area(
            "Mesajı düzenle:",
            value=st.session_state.editing_message_content,
            key="edit_text_area",
            height=100
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Kaydet ve Gönder", key="save_edit"):
                if edit_message(st.session_state.editing_message_index, edited_content):
                    st.session_state.editing_message_index = None
                    st.session_state.editing_message_content = None
                    st.rerun()
        
        with col2:
            if st.button("❌ İptal", key="cancel_edit"):
                st.session_state.editing_message_index = None
                st.session_state.editing_message_content = None
                st.rerun()
        
        st.markdown("---")
    
    # Kullanıcı girişi
    # Otomatik gönderilen mesaj varsa onu kullan
    if hasattr(st.session_state, 'auto_send_message') and st.session_state.auto_send_message:
        prompt = st.session_state.auto_send_message
        del st.session_state.auto_send_message  # Mesajı temizle
    else:
        prompt = st.chat_input("Mesajınızı yazın...")
    
    if prompt:
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
                    request_data = {
                        "message": prompt,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "system_message": st.session_state.system_message
                    }
                    
                    if st.session_state.current_session_id:
                        request_data["session_id"] = st.session_state.current_session_id
                    
                    # API çağrısı
                    start_time = time.time()
                    print(f"DEBUG: API URL: {st.session_state.api_url}/chat")
                    print(f"DEBUG: Request data: {request_data}")
                    response = requests.post(
                        f"{st.session_state.api_url}/chat",
                        json=request_data,
                        timeout=30,
                        cookies=st.session_state.get('cookies', {})
                    )
                    print(f"DEBUG: Response status: {response.status_code}")
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"Backend response: {data}")  # Debug için
                        if "response" not in data:
                            st.error(f"Backend yanıtında 'response' anahtarı yok: {data}")
                        else:
                            bot_response = data["response"]
                        
                        # Session ID'yi kaydet
                        if "session_id" in data and not st.session_state.current_session_id:
                            st.session_state.current_session_id = data["session_id"]
                            load_sessions()
                        
                        # Bot mesajını ekle
                        bot_message = {
                            "role": "assistant",
                            "content": bot_response,
                            "time": datetime.now().strftime("%H:%M")
                        }
                        st.session_state.messages.append(bot_message)
                        
                        # Bot yanıtını göster
                        rendered_response = render_message_content(bot_response)
                        st.markdown(rendered_response, unsafe_allow_html=True)
                        st.caption(bot_message["time"])
                        
                        # Dil kalite kontrolü (eğer aktifse)
                        if st.session_state.get('turkish_quality_check', True):
                            quality_check = check_language_quality(bot_response, detected_lang)
                            threshold = st.session_state.get('quality_threshold', 80)
                            
                            if quality_check["score"] < threshold:
                                language_names = {
                                    'tr': 'Türkçe', 'en': 'İngilizce', 'de': 'Almanca', 'es': 'İspanyolca',
                                    'fr': 'Fransızca', 'it': 'İtalyanca', 'pt': 'Portekizce', 'ru': 'Rusça',
                                    'ja': 'Japonca', 'ko': 'Korece', 'zh': 'Çince', 'ar': 'Arapça'
                                }
                                lang_name = language_names.get(detected_lang, detected_lang.upper())
                                
                                with st.expander(f"🔍 {lang_name} Kalite Kontrolü", expanded=False):
                                    st.warning(f"⚠️ Kalite Skoru: {quality_check['score']}/100 (Eşik: {threshold})")
                                    if quality_check["issues"]:
                                        st.markdown("**Tespit Edilen Sorunlar:**")
                                        for issue in quality_check["issues"]:
                                            st.markdown(f"• {issue}")
                                    st.info("💡 Daha iyi bir yanıt için mesajı tekrar gönderebilirsiniz.")
                        
                        # Token bilgilerini kaydet
                        if "token_info" in data:
                            st.session_state.current_token_info = data["token_info"]
                        
                        # Yanıt süresi istatistiği (sadece sidebar için)
                        if not hasattr(st.session_state, 'response_times'):
                            st.session_state.response_times = []
                        st.session_state.response_times.append(response_time)
                        
                        # Otomatik kaydırma için sayfayı yenile
                        st.session_state.auto_scroll = True
                    
                    else:
                        handle_api_error("http_error", f"HTTP {response.status_code}", response)
                        
                except requests.exceptions.Timeout:
                    handle_api_error("timeout", "Yanıt zaman aşımına uğradı")
                    
                except requests.exceptions.ConnectionError:
                    handle_api_error("connection", "API bağlantısı kurulamadı")
                    
                except Exception as e:
                    handle_api_error("unknown", str(e))

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
    
    # Otomatik kaydırma için boşluk
    if st.session_state.get('auto_scroll', False):
        st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        st.session_state.auto_scroll = False 