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
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
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
        
        /* Sidebar butonları için küçük font ve tek satır */
        .sidebar .stButton > button {
            font-size: 0.75rem !important;
            padding: 0.25rem 0.5rem !important;
            min-height: auto !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        
        /* Sidebar metinlerinin tek satırda kalmasını sağla */
        .sidebar .stMarkdown {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
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
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
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
        
        /* Sidebar butonları için küçük font ve tek satır */
        .sidebar .stButton > button {
            font-size: 0.75rem !important;
            padding: 0.25rem 0.5rem !important;
            min-height: auto !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        
        /* Sidebar metinlerinin tek satırda kalmasını sağla */
        .sidebar .stMarkdown {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
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

if "deleted_sessions" not in st.session_state:
    st.session_state.deleted_sessions = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "cookies" not in st.session_state:
    st.session_state.cookies = {}

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" veya "register"

# Cache sistemi için session state
if "auth_check_time" not in st.session_state:
    st.session_state.auth_check_time = 0

if "auth_check_result" not in st.session_state:
    st.session_state.auth_check_result = False

if "admin_check_time" not in st.session_state:
    st.session_state.admin_check_time = 0

if "admin_check_result" not in st.session_state:
    st.session_state.admin_check_result = False

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
    # Cache kontrolü - son 60 saniyede kontrol edildiyse cache'den döndür
    current_time = time.time()
    if current_time - st.session_state.auth_check_time < 60:  # 60 saniye cache
        return st.session_state.auth_check_result
    
    try:
        response = requests.get(f"{st.session_state.api_url}/user", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_id = data['user_id']
            st.session_state.username = data['username']
            result = True
        else:
            st.session_state.user_id = None
            st.session_state.username = None
            result = False
        
        # Cache'e kaydet
        st.session_state.auth_check_time = current_time
        st.session_state.auth_check_result = result
        return result
    except:
        st.session_state.user_id = None
        st.session_state.username = None
        # Cache'e kaydet
        st.session_state.auth_check_time = current_time
        st.session_state.auth_check_result = False
        return False

def check_admin_status():
    """Kullanıcının admin durumunu kontrol et"""
    # Cache kontrolü - son 120 saniyede kontrol edildiyse cache'den döndür
    current_time = time.time()
    if current_time - st.session_state.admin_check_time < 120:  # 120 saniye cache
        return st.session_state.admin_check_result
    
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/dashboard", timeout=5, cookies=st.session_state.get('cookies', {}))
        result = response.status_code == 200
        
        # Cache'e kaydet
        st.session_state.admin_check_time = current_time
        st.session_state.admin_check_result = result
        return result
    except:
        # Cache'e kaydet
        st.session_state.admin_check_time = current_time
        st.session_state.admin_check_result = False
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

def register_user(username, password, email=""):
    """Kullanıcı kaydı"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/register",
            json={"username": username, "password": password, "email": email},
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

def forgot_password(email):
    """Şifre sıfırlama isteği"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/forgot-password",
            json={"email": email},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.success(data.get('message', 'Şifre sıfırlama linki gönderildi'))
            return True
        else:
            error_data = response.json()
            st.error(f"Şifre sıfırlama hatası: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return False

def reset_password(token, new_password):
    """Şifre sıfırlama"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/reset-password",
            json={"token": token, "new_password": new_password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.success(data.get('message', 'Şifre başarıyla güncellendi'))
            return True
        else:
            error_data = response.json()
            st.error(f"Şifre sıfırlama hatası: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return False

def verify_reset_token(token):
    """Reset token'ını doğrula"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/verify-reset-token",
            json={"token": token},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Token doğrulama hatası: {str(e)}")
        return None

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
            st.session_state.deleted_sessions = []
            # Arama verilerini temizle
            if hasattr(st.session_state, 'search_results'):
                del st.session_state.search_results
            if hasattr(st.session_state, 'search_query'):
                del st.session_state.search_query
            if hasattr(st.session_state, 'last_search_params'):
                del st.session_state.last_search_params
            st.session_state.cookies = {}
            st.success("Çıkış başarılı!")
            st.rerun()
        else:
            st.error("Çıkış hatası")
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")

def delete_own_account(password, confirmation):
    """Kullanıcının kendi hesabını kalıcı olarak silmesi"""
    try:
        response = requests.delete(
            f"{st.session_state.api_url}/account/delete",
            json={
                "password": password,
                "confirmation": confirmation
            },
            timeout=10,
            cookies=st.session_state.get('cookies', {})
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('deleted'):
                # Session'ı temizle
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.messages = []
                st.session_state.current_session_id = None
                st.session_state.sessions = []
                st.session_state.deleted_sessions = []
                st.session_state.cookies = {}
                
                st.success("✅ Hesabınız başarıyla silindi!")
                st.info("Tüm verileriniz kalıcı olarak kaldırıldı. Ana sayfaya yönlendiriliyorsunuz...")
                time.sleep(3)
                st.rerun()
                return True
        else:
            error_data = response.json()
            st.error(f"❌ {error_data.get('error', 'Hesap silme hatası')}")
            return False
            
    except Exception as e:
        st.error(f"❌ Bağlantı hatası: {str(e)}")
        return False

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

def load_deleted_sessions():
    """Kullanıcının silinen sohbet oturumlarını yükle"""
    try:
        response = requests.get(f"{st.session_state.api_url}/deleted-sessions", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            st.session_state.deleted_sessions = data.get('deleted_sessions', [])
        else:
            st.error("Silinen oturumlar yüklenemedi")
    except Exception as e:
        st.error(f"Silinen oturum yükleme hatası: {str(e)}")

def restore_deleted_session(session_id):
    """Silinen sohbet oturumunu geri yükle"""
    try:
        response = requests.post(f"{st.session_state.api_url}/deleted-sessions/{session_id}/restore", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            st.success("Oturum geri yüklendi!")
            load_deleted_sessions()
            load_sessions()
            st.rerun()
        else:
            st.error("Geri yükleme hatası")
    except Exception as e:
        st.error(f"Geri yükleme hatası: {str(e)}")

def permanent_delete_session(session_id):
    """Silinen sohbet oturumunu kalıcı olarak sil"""
    try:
        response = requests.delete(f"{st.session_state.api_url}/deleted-sessions/{session_id}/permanent-delete", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            st.success("Oturum kalıcı olarak silindi!")
            load_deleted_sessions()
            st.rerun()
        else:
            st.error("Kalıcı silme hatası")
    except Exception as e:
        st.error(f"Kalıcı silme hatası: {str(e)}")

def empty_trash():
    """Tüm silinen oturumları kalıcı olarak sil"""
    try:
        response = requests.delete(f"{st.session_state.api_url}/deleted-sessions/empty-trash", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            st.success("Çöp kutusu temizlendi!")
            load_deleted_sessions()
            st.rerun()
        else:
            st.error("Çöp kutusu temizleme hatası")
    except Exception as e:
        st.error(f"Çöp kutusu temizleme hatası: {str(e)}")

# Admin API Fonksiyonları
def get_admin_dashboard():
    """Admin dashboard verilerini getir"""
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/dashboard", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Dashboard verileri alınamadı")
            return None
    except Exception as e:
        st.error(f"Dashboard hatası: {str(e)}")
        return None

def get_admin_users():
    """Tüm kullanıcıları getir"""
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/users", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            return response.json()['users']
        else:
            st.error("Kullanıcı listesi alınamadı")
            return []
    except Exception as e:
        st.error(f"Kullanıcı listesi hatası: {str(e)}")
        return []

def get_admin_user_detail(user_id):
    """Kullanıcı detaylarını getir"""
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/users/{user_id}", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Kullanıcı detayları alınamadı")
            return None
    except Exception as e:
        st.error(f"Kullanıcı detay hatası: {str(e)}")
        return None

def toggle_user_admin(user_id):
    """Kullanıcının admin durumunu değiştir"""
    try:
        response = requests.post(f"{st.session_state.api_url}/admin/users/{user_id}/toggle-admin", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            st.success(f"Admin durumu güncellendi: {data['is_admin']}")
            return True
        else:
            error_data = response.json()
            st.error(f"Admin durumu güncellenemedi: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"Admin durumu güncelleme hatası: {str(e)}")
        return False

def delete_user(user_id):
    """Admin tarafından kullanıcıyı sil"""
    try:
        response = requests.delete(f"{st.session_state.api_url}/admin/users/{user_id}/delete", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            data = response.json()
            if data.get('deleted'):
                st.success(f"✅ {data['message']}")
                return True
            else:
                st.error(f"❌ Kullanıcı silinemedi: {data.get('error', 'Bilinmeyen hata')}")
                return False
        else:
            error_data = response.json()
            st.error(f"❌ Kullanıcı silinemedi: {error_data.get('error', 'Bilinmeyen hata')}")
            return False
    except Exception as e:
        st.error(f"❌ Kullanıcı silme hatası: {str(e)}")
        return False

def get_admin_system_stats():
    """Sistem performans istatistiklerini getir"""
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/system-stats", timeout=5, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Sistem istatistikleri alınamadı")
            return None
    except Exception as e:
        st.error(f"Sistem istatistikleri hatası: {str(e)}")
        return None

def search_messages(search_params):
    """Mesajlarda arama yap"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/search",
            json=search_params,
            timeout=10,
            cookies=st.session_state.get('cookies', {})
        )
        if response.status_code == 200:
            return response.json()
        else:
            # Hata mesajını burada gösterme, sadece None döndür
            return None
    except Exception as e:
        # Hata mesajını burada gösterme, sadece None döndür
        return None

def search_sessions(query):
    """Oturum adlarında arama yap"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/search/sessions?query={query}",
            timeout=5,
            cookies=st.session_state.get('cookies', {})
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Oturum arama hatası")
            return None
    except Exception as e:
        st.error(f"Oturum arama hatası: {str(e)}")
        return None

def get_search_stats():
    """Arama istatistiklerini getir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/search/stats",
            timeout=5,
            cookies=st.session_state.get('cookies', {})
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def highlight_search_term(text, search_term):
    """Arama terimini vurgula"""
    if not search_term or not text:
        return text
    
    # Büyük/küçük harf duyarsız arama
    import re
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted_text = pattern.sub(f'<mark style="background-color: yellow; padding: 2px;">{search_term}</mark>', text)
    return highlighted_text

def perform_search(search_params, search_type="Arama"):
    """Arama işlemini gerçekleştir"""
    search_results = search_messages(search_params)
    if search_results and 'messages' in search_results:
        # Başarılı arama - hata mesajlarını temizle
        if 'search_error' in st.session_state:
            del st.session_state.search_error
        
        st.session_state.search_results = search_results
        st.session_state.search_query = search_params.get('query', '')
        # Arama parametrelerini sakla (sayfalama için)
        st.session_state.last_search_params = {
            'role': search_params.get('role'),
            'session_id': search_params.get('session_id'),
            'date_from': search_params.get('date_from'),
            'date_to': search_params.get('date_to')
        }
        st.success(f"✅ {search_type}: {search_results['total_count']} sonuç bulundu!")
        st.rerun()
    else:
        # Hata durumunda session state'e hata bilgisini kaydet
        st.session_state.search_error = f"❌ {search_type} başarısız!"
        # Hata mesajını gösterme, sadece session state'e kaydet
        # st.error(f"❌ {search_type} başarısız!")

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
                    
                    # Düzenlenen mesajı otomatik olarak gönder ve chatbot yanıtı al
                    st.session_state.auto_send_message = new_content
                    st.session_state.auto_process_edit = True  # Düzenleme sonrası otomatik işlem
                    
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
    """Gelişmiş Markdown ve emoji işleme"""
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
    
    try:
        import markdown
        from markdown.extensions import codehilite, fenced_code, tables, toc, nl2br
        
        # Markdown'ı HTML'e çevir
        md = markdown.Markdown(extensions=[
            'codehilite',  # Kod vurgulama
            'fenced_code',  # Fenced code blocks
            'tables',       # Tablo desteği
            'toc',          # İçindekiler tablosu
            'nl2br',        # Satır sonlarını <br> yap
            'sane_lists',   # Akıllı liste işleme
            'def_list',     # Tanım listeleri
            'abbr',         # Kısaltmalar
            'footnotes',    # Dipnotlar
            'attr_list',    # Özellik listeleri
            'md_in_html',   # HTML içinde markdown
        ])
        
        # Markdown'ı işle
        html = md.convert(text)
        
        # CSS stilleri ekle
        css_styles = """
        <style>
        /* Markdown stilleri */
        .markdown-content h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        
        .markdown-content h2 {
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 8px;
            margin-top: 18px;
            margin-bottom: 12px;
        }
        
        .markdown-content h3 {
            color: #7f8c8d;
            margin-top: 15px;
            margin-bottom: 10px;
        }
        
        .markdown-content h4, .markdown-content h5, .markdown-content h6 {
            color: #95a5a6;
            margin-top: 12px;
            margin-bottom: 8px;
        }
        
        .markdown-content p {
            line-height: 1.6;
            margin-bottom: 12px;
        }
        
        .markdown-content ul, .markdown-content ol {
            margin-left: 20px;
            margin-bottom: 12px;
        }
        
        .markdown-content li {
            margin-bottom: 5px;
        }
        
        .markdown-content blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-left: 0;
            color: #7f8c8d;
            font-style: italic;
        }
        
        .markdown-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        
        .markdown-content th, .markdown-content td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        
        .markdown-content th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .markdown-content tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .markdown-content tr:hover {
            background-color: #e9ecef;
        }
        
        .markdown-content a {
            color: #3498db;
            text-decoration: none;
        }
        
        .markdown-content a:hover {
            text-decoration: underline;
        }
        
        .markdown-content hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 20px 0;
        }
        
        .markdown-content strong {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .markdown-content em {
            font-style: italic;
            color: #7f8c8d;
        }
        
        .markdown-content code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
            border: 1px solid #e9ecef;
        }
        
        .markdown-content pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #e9ecef;
        }
        
        .markdown-content pre code {
            background: none;
            padding: 0;
            border: none;
        }
        </style>
        """
        
        # HTML'i div içine sar
        html = f'<div class="markdown-content">{html}</div>'
        
    except ImportError:
        # Markdown kütüphanesi yoksa basit işleme
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
        
        html = text
    
    # Kod bloklarını geri yükle (işlenmemiş olarak)
    for i, code_block in enumerate(code_blocks):
        html = html.replace(f"__CODE_BLOCK_{i}__", code_block)
    
    return html

def highlight_code(code, language=None):
    """Kod için syntax highlighting uygula"""
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, TextLexer
        from pygments.formatters import HtmlFormatter
        
        # Dil belirtilmemişse otomatik algıla
        if not language or language == 'text':
            # Gelişmiş dil algılama
            code_lower = code.strip().lower()
            
            # PHP
            if code_lower.startswith('<?php') or code_lower.startswith('<?='):
                language = 'php'
            # HTML/XML
            elif code_lower.startswith('<html') or code_lower.startswith('<!doctype') or code_lower.startswith('<xml'):
                language = 'html'
            # Python
            elif code_lower.startswith('import ') or code_lower.startswith('from ') or code_lower.startswith('def ') or code_lower.startswith('class '):
                language = 'python'
            # JavaScript/TypeScript
            elif code_lower.startswith('function ') or code_lower.startswith('const ') or code_lower.startswith('let ') or code_lower.startswith('var ') or code_lower.startswith('export '):
                language = 'javascript'
            # Java
            elif code_lower.startswith('public class') or code_lower.startswith('private ') or code_lower.startswith('package ') or code_lower.startswith('import java'):
                language = 'java'
            # C/C++
            elif code_lower.startswith('#include') or code_lower.startswith('#define') or code_lower.startswith('int main'):
                language = 'cpp'
            # Go
            elif code_lower.startswith('package ') or code_lower.startswith('import ') and 'fmt' in code_lower:
                language = 'go'
            # Rust
            elif code_lower.startswith('fn ') or code_lower.startswith('use ') or code_lower.startswith('pub '):
                language = 'rust'
            # C#
            elif code_lower.startswith('using ') or code_lower.startswith('namespace ') or code_lower.startswith('public class'):
                language = 'csharp'
            # Ruby
            elif code_lower.startswith('require ') or code_lower.startswith('def ') or code_lower.startswith('class ') and 'end' in code_lower:
                language = 'ruby'
            # SQL
            elif code_lower.startswith('select ') or code_lower.startswith('insert ') or code_lower.startswith('update ') or code_lower.startswith('create '):
                language = 'sql'
            # CSS
            elif code_lower.startswith('@') or '{' in code_lower and ':' in code_lower:
                language = 'css'
            # JSON
            elif code_lower.startswith('{') or code_lower.startswith('['):
                language = 'json'
            # YAML
            elif code_lower.startswith('---') or ':' in code_lower and '\n' in code_lower:
                language = 'yaml'
            # Shell/Bash
            elif code_lower.startswith('#!') or code_lower.startswith('#!/'):
                language = 'bash'
            # Docker
            elif code_lower.startswith('from ') and 'docker' in code_lower:
                language = 'dockerfile'
            # Markdown
            elif code_lower.startswith('#') or code_lower.startswith('##'):
                language = 'markdown'
            else:
                language = 'text'
        
        # Lexer'ı al
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except:
            lexer = TextLexer()
        
        # HTML formatter
        formatter = HtmlFormatter(
            style='monokai',
            noclasses=True,
            nobackground=True,
            prestyles="margin: 0; padding: 0;"
        )
        
        # Highlight uygula
        highlighted = highlight(code, lexer, formatter)
        
        # CSS stillerini ekle
        css_styles = """
        <style>
        .highlight {
            background-color: #272822;
            border-radius: 8px;
            padding: 16px;
            margin: 10px 0;
            overflow-x: auto;
            border: 1px solid #3e3d32;
        }
        .highlight pre {
            margin: 0;
            padding: 0;
            background: none;
            border: none;
            font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        .highlight .hll { background-color: #49483e }
        .highlight .c { color: #75715e } /* Comment */
        .highlight .err { color: #960050; background-color: #1e0010 } /* Error */
        .highlight .k { color: #66d9ef } /* Keyword */
        .highlight .l { color: #ae81ff } /* Literal */
        .highlight .n { color: #f8f8f2 } /* Name */
        .highlight .o { color: #f92672 } /* Operator */
        .highlight .p { color: #f8f8f2 } /* Punctuation */
        .highlight .ch { color: #75715e } /* Comment.Hashbang */
        .highlight .cm { color: #75715e } /* Comment.Multiline */
        .highlight .cp { color: #75715e } /* Comment.Preproc */
        .highlight .cpf { color: #75715e } /* Comment.PreprocFile */
        .highlight .c1 { color: #75715e } /* Comment.Single */
        .highlight .cs { color: #75715e } /* Comment.Special */
        .highlight .gd { color: #f92672 } /* Generic.Deleted */
        .highlight .ge { font-style: italic } /* Generic.Emph */
        .highlight .gi { color: #a6e22e } /* Generic.Inserted */
        .highlight .gs { font-weight: bold } /* Generic.Strong */
        .highlight .gu { color: #75715e } /* Generic.Subheading */
        .highlight .kc { color: #66d9ef } /* Keyword.Constant */
        .highlight .kd { color: #66d9ef } /* Keyword.Declaration */
        .highlight .kn { color: #f92672 } /* Keyword.Namespace */
        .highlight .kp { color: #66d9ef } /* Keyword.Pseudo */
        .highlight .kr { color: #66d9ef } /* Keyword.Reserved */
        .highlight .kt { color: #66d9ef } /* Keyword.Type */
        .highlight .ld { color: #e6db74 } /* Literal.Date */
        .highlight .m { color: #ae81ff } /* Literal.Number */
        .highlight .s { color: #e6db74 } /* Literal.String */
        .highlight .na { color: #a6e22e } /* Name.Attribute */
        .highlight .nb { color: #f8f8f2 } /* Name.Builtin */
        .highlight .nc { color: #a6e22e } /* Name.Class */
        .highlight .no { color: #66d9ef } /* Name.Constant */
        .highlight .nd { color: #a6e22e } /* Name.Decorator */
        .highlight .ni { color: #f8f8f2 } /* Name.Entity */
        .highlight .ne { color: #a6e22e } /* Name.Exception */
        .highlight .nf { color: #a6e22e } /* Name.Function */
        .highlight .nl { color: #f8f8f2 } /* Name.Label */
        .highlight .nn { color: #f8f8f2 } /* Name.Namespace */
        .highlight .nx { color: #a6e22e } /* Name.Other */
        .highlight .py { color: #f8f8f2 } /* Name.Property */
        .highlight .nt { color: #f92672 } /* Name.Tag */
        .highlight .nv { color: #f8f8f2 } /* Name.Variable */
        .highlight .ow { color: #f92672 } /* Operator.Word */
        .highlight .w { color: #f8f8f2 } /* Text.Whitespace */
        .highlight .mb { color: #ae81ff } /* Literal.Number.Bin */
        .highlight .mf { color: #ae81ff } /* Literal.Number.Float */
        .highlight .mh { color: #ae81ff } /* Literal.Number.Hex */
        .highlight .mi { color: #ae81ff } /* Literal.Number.Integer */
        .highlight .mo { color: #ae81ff } /* Literal.Number.Oct */
        .highlight .sa { color: #e6db74 } /* Literal.String.Affix */
        .highlight .sb { color: #e6db74 } /* Literal.String.Backtick */
        .highlight .sc { color: #e6db74 } /* Literal.String.Char */
        .highlight .dl { color: #e6db74 } /* Literal.String.Delimiter */
        .highlight .sd { color: #e6db74 } /* Literal.String.Doc */
        .highlight .s2 { color: #e6db74 } /* Literal.String.Double */
        .highlight .se { color: #ae81ff } /* Literal.String.Escape */
        .highlight .sh { color: #e6db74 } /* Literal.String.Heredoc */
        .highlight .si { color: #e6db74 } /* Literal.String.Interpol */
        .highlight .sx { color: #e6db74 } /* Literal.String.Other */
        .highlight .sr { color: #e6db74 } /* Literal.String.Regex */
        .highlight .s1 { color: #e6db74 } /* Literal.String.Single */
        .highlight .ss { color: #e6db74 } /* Literal.String.Symbol */
        .highlight .bp { color: #f8f8f2 } /* Name.Builtin.Pseudo */
        .highlight .fm { color: #a6e22e } /* Name.Function.Magic */
        .highlight .vc { color: #f8f8f2 } /* Name.Variable.Class */
        .highlight .vg { color: #f8f8f2 } /* Name.Variable.Global */
        .highlight .vi { color: #f8f8f2 } /* Name.Variable.Instance */
        .highlight .vm { color: #f8f8f2 } /* Name.Variable.Magic */
        .highlight .il { color: #ae81ff } /* Literal.Number.Integer.Long */
        </style>
        """
        
        # Dil etiketi ve kopyalama butonu için JavaScript ekle
        language_label = language.upper() if language and language != 'text' else 'CODE'
        copy_button = f"""
        <div style="position: relative;">
            <div style="position: absolute; top: 8px; left: 8px; background: #66d9ef; color: #272822; border: none; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold; font-family: monospace;">
                {language_label}
            </div>
            <button onclick="copyCode(this)" style="position: absolute; top: 8px; right: 8px; background: #3e3d32; color: #f8f8f2; border: none; border-radius: 4px; padding: 4px 8px; font-size: 12px; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">
                📋 Kopyala
            </button>
            <div class='highlight' style="padding-top: 32px;">{highlighted}</div>
        </div>
        """
        
        # Kopyalama JavaScript'i ekle
        copy_script = """
        <script>
        function copyCode(button) {
            const codeBlock = button.nextElementSibling.querySelector('pre');
            const textArea = document.createElement('textarea');
            textArea.value = codeBlock.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Buton metnini geçici olarak değiştir
            const originalText = button.innerHTML;
            button.innerHTML = '✅ Kopyalandı!';
            button.style.background = '#a6e22e';
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.background = '#3e3d32';
            }, 2000);
        }
        </script>
        """
        
        return f"{css_styles}{copy_script}{copy_button}"
        
    except ImportError:
        # Pygments yoksa basit formatlama
        return f'<div style="background-color: #272822; color: #f8f8f2; padding: 16px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; margin: 10px 0; border: 1px solid #3e3d32;">{code}</div>'
    except Exception as e:
        # Hata durumunda basit formatlama
        return f'<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff; font-family: monospace; white-space: pre-wrap; margin: 10px 0;">{code}</div>'

def render_message_content(content):
    """Mesaj içeriğini render et"""
    if not content:
        return "", []
    
    # Kod bloklarını geçici olarak sakla
    code_blocks = []
    def save_code_block(match):
        language = match.group(1) if match.group(1) else None
        code = match.group(2)
        code_blocks.append((language, code))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    # Kod bloklarını geçici olarak sakla
    processed_content = re.sub(r'```(\w+)?\n([\s\S]*?)```', save_code_block, content)
    
    # Satır içi kod bloklarını işle
    def format_inline_code(match):
        code = match.group(1)
        return f'<code style="background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; font-family: monospace; border: 1px solid #e9ecef;">{code}</code>'
    
    processed_content = re.sub(r'`([^`]+)`', format_inline_code, processed_content)
    
    # Markdown ve emoji işle
    processed_content = process_markdown_and_emoji(processed_content)
    
    return processed_content, code_blocks

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
    
    # Rate Limit Durumu
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🚦 Rate Limit Durumu")
    
    # Rate limit bilgileri
    rate_limits = {
        "Chat": "10/dakika",
        "Giriş": "5/dakika", 
        "Kayıt": "3/dakika",
        "Genel": "200/gün, 50/saat"
    }
    
    for endpoint, limit in rate_limits.items():
        st.sidebar.info(f"📊 {endpoint}: {limit}")
    
    st.sidebar.caption("🚦 Rate limiting aktif - Güvenlik için")
    
    # Rate limit test butonu
    if st.sidebar.button("🧪 Rate Limit Test", use_container_width=True):
        st.session_state.test_rate_limit = True

def test_rate_limits():
    """Rate limit'leri test et"""
    if not st.session_state.get('test_rate_limit', False):
        return
    
    st.markdown("## 🧪 Rate Limit Test Sonuçları")
    
    # Test sonuçları
    test_results = []
    
    # Chat endpoint testi
    try:
        for i in range(12):  # 10 limit + 2 fazla
            response = requests.post(
                f"{st.session_state.api_url}/chat",
                json={"message": f"Test mesajı {i+1}"},
                cookies=st.session_state.get('cookies', {}),
                timeout=5
            )
            if response.status_code == 429:
                test_results.append(f"✅ Chat Rate Limit: {i+1}. istekte engellendi")
                break
            elif i == 11:
                test_results.append("❌ Chat Rate Limit çalışmıyor")
    except Exception as e:
        test_results.append(f"❌ Chat test hatası: {str(e)}")
    
    # Login endpoint testi
    try:
        for i in range(7):  # 5 limit + 2 fazla
            response = requests.post(
                f"{st.session_state.api_url}/login",
                json={"username": f"test{i}", "password": "test123"},
                timeout=5
            )
            if response.status_code == 429:
                test_results.append(f"✅ Login Rate Limit: {i+1}. istekte engellendi")
                break
            elif i == 6:
                test_results.append("❌ Login Rate Limit çalışmıyor")
    except Exception as e:
        test_results.append(f"❌ Login test hatası: {str(e)}")
    
    # Sonuçları göster
    for result in test_results:
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)
    
    # Test durumunu sıfırla
    st.session_state.test_rate_limit = False

# Admin Panel UI Fonksiyonları
def show_admin_dashboard():
    """Admin dashboard'ı göster"""
    st.markdown("## 📊 Admin Dashboard")
    
    # Dashboard verilerini getir
    dashboard_data = get_admin_dashboard()
    if not dashboard_data:
        return
    
    # Ana metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Toplam Kullanıcı", dashboard_data['total_users'])
        st.metric("📅 Bugün Aktif", dashboard_data['today_active_users'])
    
    with col2:
        st.metric("💬 Toplam Mesaj", dashboard_data['total_messages'])
        st.metric("📝 Bugün Mesaj", dashboard_data['today_messages'])
    
    with col3:
        st.metric("💻 Toplam Oturum", dashboard_data['total_sessions'])
    
    with col4:
        # Veritabanı boyutu (sistem stats'den al)
        system_stats = get_admin_system_stats()
        if system_stats:
            st.metric("💾 Veritabanı Boyutu", f"{system_stats['database_size_mb']} MB")
    
    # Popüler modeller
    st.markdown("### 🤖 En Popüler AI Modelleri")
    if dashboard_data['popular_models']:
        model_df = pd.DataFrame(dashboard_data['popular_models'])
        st.bar_chart(model_df.set_index('model')['count'])
    else:
        st.info("Henüz model kullanım verisi yok")
    
    # Haftalık aktivite
    st.markdown("### 📈 Son 7 Günlük Aktivite")
    if dashboard_data['weekly_activity']:
        activity_df = pd.DataFrame(dashboard_data['weekly_activity'])
        activity_df['date'] = pd.to_datetime(activity_df['date'])
        st.line_chart(activity_df.set_index('date')['count'])
    else:
        st.info("Henüz aktivite verisi yok")

def show_admin_users():
    """Admin kullanıcı yönetimi"""
    st.markdown("## 👥 Kullanıcı Yönetimi")
    
    # Kullanıcıları getir
    users = get_admin_users()
    if not users:
        return
    
    # Kullanıcı listesi
    for user in users:
        with st.expander(f"👤 {user['username']} {'👑' if user['is_admin'] else ''}", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**ID:** {user['id']}")
                st.markdown(f"**Kayıt Tarihi:** {user['created_at']}")
                st.markdown(f"**Son Giriş:** {user['last_login']}")
                st.markdown(f"**Oturum Sayısı:** {user['session_count']}")
                st.markdown(f"**Mesaj Sayısı:** {user['message_count']}")
            
            with col2:
                if user['is_admin']:
                    st.success("👑 Admin")
                else:
                    st.info("👤 Kullanıcı")
                
                # Admin durumu değiştir
                if user['id'] != st.session_state.user_id:  # Kendini değiştirme
                    if st.button(f"{'👤 Kullanıcı Yap' if user['is_admin'] else '👑 Admin Yap'}", key=f"admin_{user['id']}"):
                        if toggle_user_admin(user['id']):
                            st.rerun()
            
            with col3:
                # Kullanıcı detayları
                if st.button("📊 Detaylar", key=f"detail_{user['id']}"):
                    user_detail = get_admin_user_detail(user['id'])
                    if user_detail:
                        st.markdown("### 📊 Kullanıcı Detayları")
                        st.json(user_detail)
                
                # Kullanıcı sil
                if user['id'] != st.session_state.user_id:  # Kendini silme
                    if st.button("🗑️ Sil", key=f"delete_{user['id']}"):
                        if delete_user(user['id']):
                            st.rerun()

def show_admin_system():
    """Sistem istatistikleri"""
    try:
        stats = get_admin_system_stats()
        
        st.markdown("### 📊 Sistem Performansı")
        
        # Veritabanı boyutu
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💾 Veritabanı Boyutu", f"{stats.get('database_size_mb', 0)} MB")
        
        # En aktif kullanıcılar
        st.markdown("### 👥 En Aktif Kullanıcılar (Son 7 Gün)")
        top_users = stats.get('top_users', [])
        if top_users:
            for i, user in enumerate(top_users[:5], 1):
                st.markdown(f"**{i}.** {user['username']} - {user['message_count']} mesaj")
        else:
            st.info("Henüz aktif kullanıcı yok")
        
        # Model kullanım istatistikleri
        st.markdown("### 🤖 Model Kullanım İstatistikleri")
        model_stats = stats.get('model_stats', [])
        if model_stats:
            for model in model_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Model", model['model'])
                with col2:
                    st.metric("Kullanım", model['count'])
                with col3:
                    st.metric("Yüzde", f"{model['percentage']}%")
        else:
            st.info("Henüz model kullanım verisi yok")
            
    except Exception as e:
        st.error(f"Sistem istatistikleri alınamadı: {str(e)}")

def show_admin_logs():
    """Admin log görüntüleme"""
    st.markdown("### 📋 Sistem Logları")
    
    # Log dosyası yükleme
    try:
        response = requests.get(f"{st.session_state.api_url}/admin/logs", timeout=10, cookies=st.session_state.get('cookies', {}))
        if response.status_code == 200:
            logs_data = response.json()
            logs = logs_data.get('logs', [])
            
            # Log filtreleme
            col1, col2, col3 = st.columns(3)
            with col1:
                log_level = st.selectbox("Log Seviyesi", ["Tümü", "INFO", "WARNING", "ERROR"])
            with col2:
                search_term = st.text_input("Arama", placeholder="IP, kullanıcı adı, hata...")
            with col3:
                limit = st.selectbox("Gösterim Limiti", [50, 100, 200, 500])
            
            # Logları filtrele
            filtered_logs = logs
            if log_level != "Tümü":
                filtered_logs = [log for log in filtered_logs if log_level in log]
            if search_term:
                filtered_logs = [log for log in filtered_logs if search_term.lower() in log.lower()]
            
            # Son N log
            filtered_logs = filtered_logs[-limit:]
            
            # Logları göster
            if filtered_logs:
                st.markdown(f"**Toplam {len(filtered_logs)} log kaydı**")
                
                # Log indirme butonu
                if st.button("📥 Logları İndir"):
                    log_content = "\n".join(filtered_logs)
                    st.download_button(
                        label="💾 Log Dosyasını İndir",
                        data=log_content,
                        file_name=f"chatbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                        mime="text/plain"
                    )
                
                # Logları tablo halinde göster
                with st.expander("📋 Detaylı Log Görünümü", expanded=True):
                    for i, log in enumerate(reversed(filtered_logs), 1):
                        # Log seviyesine göre renk
                        if "ERROR" in log:
                            st.error(f"**{i}.** {log}")
                        elif "WARNING" in log:
                            st.warning(f"**{i}.** {log}")
                        elif "INFO" in log:
                            st.info(f"**{i}.** {log}")
                        else:
                            st.text(f"**{i}.** {log}")
            else:
                st.info("Filtre kriterlerine uygun log bulunamadı")
                
        else:
            st.error("Loglar alınamadı")
            
    except Exception as e:
        st.error(f"Log görüntüleme hatası: {str(e)}")

def show_admin_panel():
    """Ana admin paneli"""
    st.markdown("## 🔐 Admin Paneli")
    
    # Admin kontrolü
    if not check_admin_status():
        st.error("❌ Admin yetkiniz yok!")
        return
    
    # Admin sekmeleri
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["📊 Dashboard", "👥 Kullanıcılar", "⚙️ Sistem", "📋 Loglar"])
    
    with admin_tab1:
        show_admin_dashboard()
    
    with admin_tab2:
        show_admin_users()
    
    with admin_tab3:
        show_admin_system()
        
    with admin_tab4:
        show_admin_logs()

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

def check_if_needs_research(prompt: str) -> bool:
    """Mesajın web araştırması gerektirip gerektirmediğini kontrol eder"""
    research_keywords = [
        'hava', 'hava durumu', 'sıcaklık', 'yağmur', 'güneş', 'rüzgar', 'nem', 'derece',
        'yol', 'tarif', 'nasıl giderim', 'adres', 'konum', 'harita', 'gps',
        'haber', 'güncel', 'son dakika', 'olay', 'gelişme',
        'fiyat', 'kaç para', 'ne kadar', 'ucuz', 'pahalı',
        'nerede', 'hangi', 'kim', 'ne zaman', 'kaç',
        'vapur', 'otobüs', 'metro', 'tren', 'uçak', 'feribot',
        'internet', 'araştır', 'bak', 'söyle', 'bul', 'bulun',
        'saat', 'zaman', 'ne zaman', 'kaçta', 'kaç saat',
        'mesafe', 'uzaklık', 'süre', 'dakika', 'saat'
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in research_keywords)

def show_typing_animation():
    """Gelişmiş yazma animasyonu göster"""
    # Farklı animasyon türleri
    animation_types = {
        "thinking": ["🤔 Düşünüyor", "🤔 Düşünüyor.", "🤔 Düşünüyor..", "🤔 Düşünüyor..."],
        "typing": ["⌨️ Yazıyor", "⌨️ Yazıyor.", "⌨️ Yazıyor..", "⌨️ Yazıyor..."],
        "processing": ["⚙️ İşleniyor", "⚙️ İşleniyor.", "⚙️ İşleniyor..", "⚙️ İşleniyor..."],
        "analyzing": ["🔍 Analiz ediyor", "🔍 Analiz ediyor.", "🔍 Analiz ediyor..", "🔍 Analiz ediyor..."],
        "searching": ["🔎 Arıyor", "🔎 Arıyor.", "🔎 Arıyor..", "🔎 Arıyor..."]
    }
    
    # Rastgele animasyon türü seç
    import random
    animation_type = random.choice(list(animation_types.keys()))
    indicators = animation_types[animation_type]
    
    # Progress bar ile animasyon
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(len(indicators)):
        progress_bar.progress((i + 1) / len(indicators))
        status_text.text(indicators[i])
        time.sleep(0.3)
    
    return progress_bar, status_text

def show_message_sending_animation():
    """Mesaj gönderme animasyonu"""
    # Gönderme animasyonu
    sending_indicators = ["📤 Gönderiliyor", "📤 Gönderiliyor.", "📤 Gönderiliyor..", "📤 Gönderiliyor..."]
    
    status_text = st.empty()
    
    for indicator in sending_indicators:
        status_text.text(indicator)
        time.sleep(0.2)
    
    return status_text

def show_loading_dots():
    """Yükleme noktaları animasyonu"""
    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    status_text = st.empty()
    
    for i in range(10):
        status_text.text(f"Yükleniyor {dots[i]}")
        time.sleep(0.1)
    
    return status_text

def show_pulse_animation():
    """Nabız animasyonu"""
    import math
    
    status_text = st.empty()
    
    for i in range(20):
        # Sinüs dalgası ile nabız efekti
        intensity = abs(math.sin(i * 0.5)) * 100
        status_text.text(f"💓 İşleniyor... {intensity:.0f}%")
        time.sleep(0.1)
    
    return status_text

def show_typing_cursor():
    """Yazma imleci animasyonu"""
    cursor_states = ["|", " ", "|", " "]
    
    status_text = st.empty()
    
    for i in range(8):
        status_text.text(f"Yazıyor{cursor_states[i % 4]}")
        time.sleep(0.3)
    
    return status_text

# Resim Analizi Fonksiyonları
def upload_and_analyze_image(image_file, analysis_type="general", session_id=None):
    """Resim yükle ve analiz et"""
    try:
        files = {'image': image_file}
        data = {
            'analysis_type': analysis_type,
            'session_id': session_id
        }
        
        response = requests.post(
            f"{st.session_state.api_url}/upload-image",
            files=files,
            data=data,
            timeout=60,
            cookies=st.session_state.get('cookies', {})
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            return {'error': error_data.get('error', 'Resim analizi başarısız')}
            
    except Exception as e:
        return {'error': f'Resim yükleme hatası: {str(e)}'}

def reanalyze_image(analysis_id, analysis_type="general"):
    """Mevcut resmi yeniden analiz et"""
    try:
        data = {
            'analysis_id': analysis_id,
            'analysis_type': analysis_type
        }
        
        response = requests.post(
            f"{st.session_state.api_url}/analyze-image",
            json=data,
            timeout=60,
            cookies=st.session_state.get('cookies', {})
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            return {'error': error_data.get('error', 'Yeniden analiz başarısız')}
            
    except Exception as e:
        return {'error': f'Yeniden analiz hatası: {str(e)}'}

def get_image_history():
    """Resim analiz geçmişini getir"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/image-history",
            timeout=10,
            cookies=st.session_state.get('cookies', {})
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'history': []}
            
    except Exception as e:
        return {'history': []}

def delete_image_analysis(analysis_id):
    """Resim analizini sil"""
    try:
        response = requests.delete(
            f"{st.session_state.api_url}/image/{analysis_id}",
            timeout=10,
            cookies=st.session_state.get('cookies', {})
        )
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except Exception as e:
        return False

def format_file_size(size_bytes):
    """Dosya boyutunu formatla"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_analysis_type_name(analysis_type):
    """Analiz türü adını getir"""
    types = {
        'general': 'Genel Analiz',
        'objects': 'Nesne Tanıma',
        'text': 'Metin Okuma (OCR)',
        'emotions': 'Duygu Analizi'
    }
    return types.get(analysis_type, analysis_type)

def show_image_analysis_interface():
    """Resim analizi arayüzünü göster"""
    st.markdown("## 🖼️ Resim Analizi")
    st.markdown("Resim yükleyin ve AI ile analiz edin!")
    
    # Analiz türü seçimi
    analysis_type = st.selectbox(
        "Analiz Türü",
        options=['general', 'objects', 'text', 'emotions'],
        format_func=get_analysis_type_name,
        help="Resmin nasıl analiz edileceğini seçin"
    )
    
    # Resim yükleme
    uploaded_file = st.file_uploader(
        "Resim Yükle",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'],
        help="Analiz edilecek resmi seçin (maksimum 10MB)"
    )
    
    if uploaded_file is not None:
        # Resim önizleme
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(uploaded_file, caption="Yüklenen Resim", use_column_width=True)
            
            # Dosya bilgileri
            file_size = format_file_size(uploaded_file.size)
            st.info(f"📁 Dosya: {uploaded_file.name}\n📏 Boyut: {file_size}")
        
        with col2:
            if st.button("🔍 Resmi Analiz Et", type="primary", use_container_width=True):
                with st.spinner("Resim analiz ediliyor..."):
                    # Resmi analiz et
                    result = upload_and_analyze_image(
                        uploaded_file, 
                        analysis_type, 
                        st.session_state.get('current_session_id')
                    )
                    
                    if 'error' in result:
                        st.error(f"❌ Hata: {result['error']}")
                    else:
                        st.success("✅ Analiz tamamlandı!")
                        
                        # Analiz sonucunu göster
                        st.markdown("### 📊 Analiz Sonucu")
                        st.markdown(result['analysis_result'])
                        
                        # Detaylar
                        with st.expander("📋 Analiz Detayları"):
                            st.write(f"**Analiz ID:** {result['analysis_id']}")
                            st.write(f"**Analiz Türü:** {get_analysis_type_name(result['analysis_type'])}")
                            st.write(f"**Dosya Boyutu:** {format_file_size(result['file_size'])}")
                            st.write(f"**Yükleme Zamanı:** {result['upload_time']}")
    
    # Resim geçmişi
    st.markdown("---")
    st.markdown("### 📚 Resim Analiz Geçmişi")
    
    history_data = get_image_history()
    if history_data.get('history'):
        for item in history_data['history']:
            with st.expander(f"📷 {item['filename']} - {get_analysis_type_name(item['analysis_type'])}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Analiz Sonucu:**")
                    st.markdown(item['analysis_result'][:500] + "..." if len(item['analysis_result']) > 500 else item['analysis_result'])
                    
                    st.write(f"**Dosya Boyutu:** {format_file_size(item['file_size'])}")
                    st.write(f"**Yükleme Zamanı:** {item['upload_time']}")
                
                with col2:
                    # Yeniden analiz
                    new_analysis_type = st.selectbox(
                        "Yeniden Analiz",
                        options=['general', 'objects', 'text', 'emotions'],
                        format_func=get_analysis_type_name,
                        key=f"reanalyze_{item['id']}"
                    )
                    
                    if st.button("🔄 Yeniden Analiz Et", key=f"reanalyze_btn_{item['id']}"):
                        with st.spinner("Yeniden analiz ediliyor..."):
                            result = reanalyze_image(item['id'], new_analysis_type)
                            if 'error' in result:
                                st.error(f"❌ Hata: {result['error']}")
                            else:
                                st.success("✅ Yeniden analiz tamamlandı!")
                                # st.rerun() kaldırıldı - sekme değişikliğini önlemek için
                    
                    # Sil
                    if st.button("🗑️ Sil", key=f"delete_{item['id']}"):
                        if delete_image_analysis(item['id']):
                            st.success("✅ Silindi!")
                            # st.rerun() kaldırıldı - sekme değişikliğini önlemek için
                        else:
                            st.error("❌ Silme başarısız!")
    else:
        st.info("Henüz resim analizi yapılmamış.")

# URL parametrelerini kontrol et
query_params = st.experimental_get_query_params()
current_page = query_params.get("page", ["main"])[0]
reset_token = query_params.get("token", [None])[0]

# Şifre sıfırlama sayfası (token ile)
if reset_token:
    st.markdown("""
    <div class="main-header">
        <h1>🔑 Şifre Sıfırlama</h1>
        <p>Yeni şifrenizi belirleyin</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Token'ı doğrula
    token_data = verify_reset_token(reset_token)
    
    if token_data and token_data.get('valid'):
        username = token_data.get('username', 'Kullanıcı')
        st.success(f"✅ Token geçerli! Kullanıcı: {username}")
        
        with st.form("reset_password_form"):
            new_password = st.text_input("Yeni Şifre", type="password", key="new_password")
            new_password_confirm = st.text_input("Yeni Şifre Tekrar", type="password", key="new_password_confirm")
            reset_submitted = st.form_submit_button("Şifreyi Güncelle", use_container_width=True)
            
            if reset_submitted:
                if new_password and new_password_confirm:
                    if new_password == new_password_confirm:
                        if len(new_password) >= 6:
                            if reset_password(reset_token, new_password):
                                st.success("✅ Şifreniz başarıyla güncellendi!")
                                st.info("Artık yeni şifrenizle giriş yapabilirsiniz.")
                                st.markdown("""
                                <div style="text-align: center; margin: 20px 0;">
                                    <a href="?" style="color: #667eea; text-decoration: none; font-size: 14px; font-weight: 500;">
                                        ← Giriş Sayfasına Dön
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error("❌ Şifre güncellenirken bir hata oluştu!")
                        else:
                            st.error("Şifre en az 6 karakter olmalıdır!")
                    else:
                        st.error("Şifreler eşleşmiyor!")
                else:
                    st.error("Şifre alanları gerekli!")
    else:
        error_msg = token_data.get('error', 'Geçersiz token') if token_data else 'Token doğrulanamadı'
        st.error(f"❌ {error_msg}")
        st.info("Lütfen yeni bir şifre sıfırlama linki talep edin.")
        
        st.markdown("""
        <div style="text-align: center; margin: 20px 0;">
            <a href="?page=forgot-password" style="color: #ff4444; text-decoration: none; font-size: 14px; font-weight: 500;">
                🔐 Yeni Şifre Sıfırlama Linki Talep Et
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# Şifre unuttum sayfası
elif current_page == "forgot-password":
    st.markdown("""
    <div class="main-header">
        <h1>🔐 Şifre Sıfırlama</h1>
        <p>Email adresinizi girin, şifre sıfırlama linki gönderelim</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("forgot_password_form"):
        forgot_email = st.text_input("Email Adresi", key="forgot_email")
        forgot_submitted = st.form_submit_button("Şifre Sıfırlama Linki Gönder", use_container_width=True)
        
        if forgot_submitted:
            if forgot_email:
                if '@' in forgot_email and '.' in forgot_email:
                    if forgot_password(forgot_email):
                        st.success("✅ Şifre sıfırlama linki email adresinize gönderildi!")
                        st.info("📧 Email'inizi kontrol edin ve linke tıklayın.")
                else:
                    st.error("Geçerli bir email adresi girin!")
            else:
                st.error("Email adresi gerekli!")
    
    # Geri dön linki
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <a href="?" style="color: #667eea; text-decoration: none; font-size: 14px; font-weight: 500;">
            ← Giriş Sayfasına Dön
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# Ana sayfa (giriş/kayıt)
else:
    # Ana başlık ve tanıtım (her zaman giriş sayfasının en üstünde)
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Chatbot</h1>
        <p>Groq API ile güçlendirilmiş yapay zeka asistanı</p>
    </div>
    """, unsafe_allow_html=True)

    # Kullanıcı kimlik doğrulama durumunu kontrol et
    # Session state'te kullanıcı bilgileri varsa API'ye istek atmadan kullan
    if st.session_state.user_id and st.session_state.username:
        is_authenticated = True
    else:
        is_authenticated = check_auth_status()

# Kullanıcı giriş yapmamışsa giriş/ kayıt formunu ve kutuları göster
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
            
            # Şifre unuttum linki - şifre ile giriş butonu arasında
            st.markdown("""
            <div style="text-align: left; margin: 10px 0;">
                <a href="?page=forgot-password" style="color: #ff4444; text-decoration: none; font-size: 14px; font-weight: 500;">
                    🔐 Şifremi Unuttum
                </a>
            </div>
            """, unsafe_allow_html=True)
            
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
            register_email = st.text_input("Email (Opsiyonel)", key="register_email", help="Şifre sıfırlama için gerekli")
            register_password = st.text_input("Şifre", type="password", key="register_password")
            register_password_confirm = st.text_input("Şifre Tekrar", type="password", key="register_password_confirm")
            register_submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            if register_submitted:
                if register_username and register_password:
                    if register_password == register_password_confirm:
                        if len(register_username) >= 3:
                            if len(register_password) >= 6:
                                if register_user(register_username, register_password, register_email):
                                    st.rerun()
                            else:
                                st.error("Şifre en az 6 karakter olmalıdır!")
                        else:
                            st.error("Kullanıcı adı en az 3 karakter olmalıdır!")
                    else:
                        st.error("Şifreler eşleşmiyor!")
                else:
                    st.error("Kullanıcı adı ve şifre gerekli!")
    
    # Özellikler, teknolojiler ve destek kutuları (sadece girişte)
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
    st.markdown("---")

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
    # ... mevcut chat ekranı kodu ...
    # Özellikler, teknolojiler ve destek kutuları BURADAN KALDIRILDI
    # ... mevcut kod ...

    # Kullanıcı bilgileri
    st.markdown(f"""
    <div class="user-info">
        👤 <strong>{st.session_state.username}</strong> olarak giriş yaptınız
        {' 👑' if check_admin_status() else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Admin paneli butonu
    if check_admin_status():
        if st.button("🔐 Admin Paneli", use_container_width=True):
            st.session_state.show_admin_panel = not st.session_state.get('show_admin_panel', False)
            st.rerun()
        
        # Admin paneli göster
        if st.session_state.get('show_admin_panel', False):
            show_admin_panel()
            st.stop()
    
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
            # Sohbet yenileme butonu kaldırıldı
            pass
        
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
        
        # Arama ve Filtreleme
        st.markdown("## 🔍 Arama ve Filtreleme")
        
        # Arama sekmesi
        search_tab1, search_tab2 = st.tabs(["📝 Mesaj Arama", "📊 İstatistikler"])
        
        with search_tab1:
            # Hata mesajlarını göster
            if 'search_error' in st.session_state:
                st.error(st.session_state.search_error)
                del st.session_state.search_error
            
            # Arama formu
            with st.form("search_form"):
                # Arama kriterleri seçimi
                st.markdown("### 🎯 Arama Kriterleri")
                st.markdown("İstediğiniz kriterleri seçin, diğerleri opsiyonel:")
                
                # Arama terimi (opsiyonel)
                search_query = st.text_input(
                    "🔍 Arama terimi (opsiyonel):",
                    placeholder="Mesaj içeriğinde ara...",
                    help="Mesaj içeriğinde veya oturum adında arama yapın. Boş bırakabilirsiniz."
                )
                
                # Filtreler (opsiyonel)
                col1, col2 = st.columns(2)
                with col1:
                    role_filter = st.selectbox(
                        "👤 Rol Filtresi (opsiyonel):",
                        ["Tümü", "Kullanıcı", "Bot"],
                        help="Sadece belirli roldeki mesajları ara. 'Tümü' seçerseniz filtre uygulanmaz."
                    )
                
                with col2:
                    session_filter = st.selectbox(
                        "📁 Oturum Filtresi (opsiyonel):",
                        ["Tüm Oturumlar"] + [s['session_name'] for s in st.session_state.sessions],
                        help="Belirli bir oturumda ara. 'Tüm Oturumlar' seçerseniz filtre uygulanmaz."
                    )
                
                # Tarih filtreleri (opsiyonel)
                st.markdown("### 📅 Tarih Filtreleri (opsiyonel)")
                col1, col2 = st.columns(2)
                with col1:
                    date_from = st.date_input(
                        "📅 Başlangıç Tarihi:",
                        value=None,
                        help="Bu tarihten sonraki mesajları ara. Boş bırakabilirsiniz."
                    )
                
                with col2:
                    date_to = st.date_input(
                        "📅 Bitiş Tarihi:",
                        value=None,
                        help="Bu tarihten önceki mesajları ara. Boş bırakabilirsiniz."
                    )
                
                # Hızlı arama seçenekleri
                st.markdown("### ⚡ Hızlı Arama")
                quick_search_col1, quick_search_col2, quick_search_col3 = st.columns(3)
                
                with quick_search_col1:
                    if st.form_submit_button("📅 Bugünkü Mesajlar", use_container_width=True):
                        today = datetime.now().date()
                        search_params = {
                            'date_from': today.strftime('%Y-%m-%d'),
                            'date_to': today.strftime('%Y-%m-%d'),
                            'limit': 50,
                            'offset': 0
                        }
                        perform_search(search_params, "Bugünkü mesajlar")
                
                with quick_search_col2:
                    if st.form_submit_button("👤 Sadece Benim Mesajlarım", use_container_width=True):
                        search_params = {
                            'role': 'user',
                            'limit': 50,
                            'offset': 0
                        }
                        perform_search(search_params, "Kullanıcı mesajları")
                
                with quick_search_col3:
                    if st.form_submit_button("🤖 Sadece Bot Yanıtları", use_container_width=True):
                        search_params = {
                            'role': 'assistant',
                            'limit': 50,
                            'offset': 0
                        }
                        perform_search(search_params, "Bot yanıtları")
                
                # Genel arama butonu
                st.markdown("### 🔍 Özel Arama")
                search_submitted = st.form_submit_button("🔍 Ara", use_container_width=True)
                
                if search_submitted:
                    # Arama parametrelerini hazırla
                    search_params = {
                        'query': search_query,
                        'limit': 50,
                        'offset': 0
                    }
                    
                    # Rol filtresi
                    if role_filter == "Kullanıcı":
                        search_params['role'] = 'user'
                    elif role_filter == "Bot":
                        search_params['role'] = 'assistant'
                    
                    # Oturum filtresi
                    if session_filter != "Tüm Oturumlar":
                        selected_session = next((s for s in st.session_state.sessions if s['session_name'] == session_filter), None)
                        if selected_session:
                            search_params['session_id'] = selected_session['session_id']
                    
                    # Tarih filtreleri
                    if date_from:
                        search_params['date_from'] = date_from.strftime('%Y-%m-%d')
                    if date_to:
                        search_params['date_to'] = date_to.strftime('%Y-%m-%d')
                    
                    # Boş parametreleri temizle
                    search_params = {k: v for k, v in search_params.items() if v}
                    
                    if search_params:
                        perform_search(search_params, "Özel arama")
                    else:
                        st.warning("⚠️ En az bir arama kriteri belirtin!")
        
        with search_tab2:
            # İstatistikleri göster
            stats = get_search_stats()
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Toplam Mesaj", f"{stats['total_messages']:,}")
                    st.metric("👤 Kullanıcı Mesajları", f"{stats['user_messages']:,}")
                with col2:
                    st.metric("📁 Toplam Oturum", f"{stats['total_sessions']:,}")
                    st.metric("🤖 Bot Mesajları", f"{stats['bot_messages']:,}")
                
                if stats['last_message_date']:
                    st.info(f"📅 Son mesaj: {stats['last_message_date'][:10]}")
                
                if stats['most_active_day']['date']:
                    st.success(f"🔥 En aktif gün: {stats['most_active_day']['date']} ({stats['most_active_day']['message_count']} mesaj)")
            else:
                st.info("📊 İstatistikler yüklenemedi")
        
        # Arama sonuçlarını göster
        if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
            st.markdown("---")
            st.markdown("## 🔍 Arama Sonuçları")
            
            results = st.session_state.search_results
            search_query = st.session_state.get('search_query', '')
            
            # Sonuç sayısı ve arama bilgileri
            search_info = f"📊 {results['total_count']} sonuç bulundu"
            if search_query:
                search_info += f" • Arama: '{search_query}'"
            st.info(search_info)
            
            # Sayfalama
            if results['has_more'] or results['offset'] > 0:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if results['offset'] > 0:
                        if st.button("⬅️ Önceki", key="prev_page"):
                            # Önceki sayfa
                            new_offset = max(0, results['offset'] - results['limit'])
                            search_params = {
                                'query': search_query,
                                'limit': results['limit'],
                                'offset': new_offset
                            }
                            # Rol ve oturum filtrelerini geri ekle
                            if hasattr(st.session_state, 'last_search_params'):
                                search_params.update(st.session_state.last_search_params)
                            
                            new_results = search_messages(search_params)
                            if new_results:
                                st.session_state.search_results = new_results
                                st.rerun()
                
                with col2:
                    current_page = (results['offset'] // results['limit']) + 1
                    total_pages = (results['total_count'] + results['limit'] - 1) // results['limit']
                    st.caption(f"Sayfa {current_page} / {total_pages}")
                
                with col3:
                    if results['has_more']:
                        if st.button("➡️ Sonraki", key="next_page"):
                            # Sonraki sayfa
                            new_offset = results['offset'] + results['limit']
                            search_params = {
                                'query': search_query,
                                'limit': results['limit'],
                                'offset': new_offset
                            }
                            # Rol ve oturum filtrelerini geri ekle
                            if hasattr(st.session_state, 'last_search_params'):
                                search_params.update(st.session_state.last_search_params)
                            
                            new_results = search_messages(search_params)
                            if new_results:
                                st.session_state.search_results = new_results
                                st.rerun()
            
            # Sonuçları listele
            for i, message in enumerate(results['messages']):
                with st.expander(f"📝 {message['session_name']} - {message['timestamp'][:16]}", expanded=False):
                    # Mesaj rolü
                    role_icon = "👤" if message['role'] == 'user' else "🤖"
                    st.markdown(f"**{role_icon} {message['role'].title()}**")
                    
                    # Mesaj içeriği (vurgulanmış veya normal)
                    if search_query:
                        highlighted_content = highlight_search_term(message['content'], search_query)
                        st.markdown(highlighted_content, unsafe_allow_html=True)
                    else:
                        st.markdown(message['content'])
                    
                    # Mesaj detayları
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"📅 {message['timestamp'][:10]}")
                    with col2:
                        st.caption(f"🕐 {message['timestamp'][11:16]}")
                    with col3:
                        st.caption(f"📁 {message['session_name']}")
                    
                    # Oturuma git butonu
                    if st.button(f"📁 Bu Oturuma Git", key=f"goto_session_{i}"):
                        st.session_state.current_session_id = message['session_id']
                        load_session_messages(message['session_id'])
                        st.rerun()
            
            # Arama sonuçlarını temizle
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("💡 Arama sonuçlarını temizlemek için sağdaki butona tıklayın")
            with col2:
                if st.button("❌ Temizle", key="clear_search", use_container_width=True):
                    if hasattr(st.session_state, 'search_results'):
                        del st.session_state.search_results
                    if hasattr(st.session_state, 'search_query'):
                        del st.session_state.search_query
                    if hasattr(st.session_state, 'last_search_params'):
                        del st.session_state.last_search_params
                    st.rerun()
        
        st.markdown("---")
        
        # Sohbet Oturumları bölümü kaldırıldı
        
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
        
        # Silinen Oturumlar (Çöp Kutusu)
        st.markdown("---")
        st.markdown("## 🗑️ Çöp Kutusu")
        
        # Silinen oturumları yenile butonu
        if st.button("🔄 Çöp Kutusunu Yenile", use_container_width=True):
            load_deleted_sessions()
        
        # Silinen oturumları yükle
        if not hasattr(st.session_state, 'deleted_sessions') or not st.session_state.deleted_sessions:
            load_deleted_sessions()
        
        # Çöp kutusunu temizle butonu
        if st.session_state.deleted_sessions:
            if st.button("🗑️ Çöp Kutusunu Temizle", use_container_width=True, help="Tüm silinen oturumları kalıcı olarak sil"):
                empty_trash()
        
        # Silinen oturumları listele
        if st.session_state.deleted_sessions:
            st.markdown("### Silinen Oturumlar:")
            
            for session in st.session_state.deleted_sessions:
                session_id = session['session_id']
                session_name = session['session_name']
                message_count = session['message_count']
                deleted_at = session['deleted_at']
                
                # Oturum bilgilerini göster
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**📁 {session_name}**")
                
                with col2:
                    if st.button("🔄", key=f"restore_{session_id}", help="Oturumu geri yükle", use_container_width=True):
                        restore_deleted_session(session_id)
                
                with col3:
                    if st.button("🗑️", key=f"permanent_delete_{session_id}", help="Kalıcı olarak sil", use_container_width=True):
                        permanent_delete_session(session_id)
                
                # Oturum detayları
                st.caption(f"💬 {message_count} mesaj • Silindi: {deleted_at[:10]}")
        
        else:
            st.info("🗑️ Çöp kutusu boş")
        
        st.markdown("---")
        
        # Sohbet temizleme butonu kaldırıldı

        # HESAP SİLME BÖLÜMÜ (sidebar'ın en altı)
        st.markdown('---')
        st.markdown('## ❌ Hesabı Kalıcı Olarak Sil')
        st.warning('Bu işlem geri alınamaz! Tüm sohbetleriniz, oturumlarınız ve hesabınız kalıcı olarak silinir.')
        with st.expander('Hesabımı Silmek İstiyorum', expanded=False):
            st.markdown('**Dikkat:** Hesabınızı silmek için şifrenizi girin ve aşağıdaki onay kutusunu doldurun.')
            with st.form('delete_account_form'):
                password = st.text_input('Şifreniz', type='password', key='delete_account_password')
                confirmation = st.text_input('Onay Metni ("HESABIMI SİL" yazın)', key='delete_account_confirm')
                submitted = st.form_submit_button('Hesabımı Kalıcı Olarak Sil', use_container_width=True)
                if submitted:
                    if password and confirmation:
                        delete_own_account(password, confirmation)
                    else:
                        st.error('Şifre ve onay metni gerekli!')
        
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

    # Ana chat arayüzü - Sayfanın başında
    st.markdown("## 💬 AI Chatbot")
    
    # Resim analizi butonu (opsiyonel)
    if st.button("🖼️ Resim Analizi", use_container_width=True):
        show_image_analysis_interface()
    
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
                rendered_content, code_blocks = render_message_content(message["content"])
                
                # Kod bloklarını ayrı ayrı render et
                if code_blocks:
                    # Metni parçalara ayır
                    parts = rendered_content.split("__CODE_BLOCK_")
                    
                    for j, part in enumerate(parts):
                        if j == 0:
                            # İlk parça (kod bloğu yok)
                            if part.strip():
                                st.markdown(part, unsafe_allow_html=True)
                        else:
                            # Kod bloğu var
                            if "_" in part:
                                code_index = int(part.split("_")[0])
                                remaining_text = "_".join(part.split("_")[1:])
                                
                                if code_index < len(code_blocks):
                                    language, code = code_blocks[code_index]
                                    # Streamlit'in kendi code bileşenini kullan
                                    st.code(code, language=language if language else None)
                                
                                # Kalan metni render et
                                if remaining_text.strip():
                                    st.markdown(remaining_text, unsafe_allow_html=True)
                else:
                    # Kod bloğu yoksa normal render
                    st.markdown(rendered_content, unsafe_allow_html=True)
                
                # Düzenleme durumunu göster
                if message.get("edited", False):
                    st.caption(f"✏️ {message['time']} (düzenlendi: {message.get('edit_time', '')})")
                else:
                    st.caption(message["time"])
                
                # Her mesaj için kendi butonları
                if message["role"] == "user":
                    # Her kullanıcı mesajında düzenleme butonu göster
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
            if st.button("🚀 Düzenle ve Gönder", key="save_edit"):
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
        # Düzenleme sonrası otomatik işlem için flag'i temizle
        if hasattr(st.session_state, 'auto_process_edit'):
            del st.session_state.auto_process_edit
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
            rendered_prompt, _ = render_message_content(prompt)
            st.markdown(rendered_prompt, unsafe_allow_html=True)
            st.caption(user_message["time"])
        
        # Web araştırması gerekip gerekmediğini kontrol et
        needs_research = check_if_needs_research(prompt)
        
        # Bot yanıtını al
        with st.chat_message("assistant", avatar=st.session_state.bot_avatar):
            # Gelişmiş animasyon başlat
            progress_bar, status_text = show_typing_animation()
            
            try:
                # Eğer web araştırması gerekiyorsa, önce araştırma yap
                research_data = None
                if needs_research:
                    # Araştırma animasyonu
                    status_text.text("🔍 Web'den araştırıyorum...")
                    research_response = requests.post(
                        f"{st.session_state.api_url}/research",
                        json={"query": prompt},
                        timeout=30,
                        cookies=st.session_state.get('cookies', {})
                    )
                    if research_response.status_code == 200:
                        research_data = research_response.json().get('research_result', {})
                
                # Araştırma verilerini mesaja ekle
                enhanced_prompt = prompt
                if research_data and research_data.get('success'):
                    enhanced_prompt = f"{prompt}\n\n[Web Araştırma Sonuçları:]\n{json.dumps(research_data, ensure_ascii=False, indent=2)}"
                
                request_data = {
                    "message": enhanced_prompt,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "system_message": st.session_state.system_message
                }
                
                if st.session_state.current_session_id:
                    request_data["session_id"] = st.session_state.current_session_id
                
                # API çağrısı öncesi animasyon
                status_text.text("📤 Mesaj gönderiliyor...")
                
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
                    rendered_response, _ = render_message_content(bot_response)
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
        
        # Bot yanıtı alındıktan sonra sayfayı yenile ki düzenleme butonları çıksın
        st.rerun()

    # Rate limit test fonksiyonunu çağır
    test_rate_limits()
    
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
          # Ana chat arayüzü zaten yukarıda tanımlandı