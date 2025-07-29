import streamlit as st
import requests
import json
from datetime import datetime
import time

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Session state başlatma
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:5050/api"

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")
    
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

# Ana başlık
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Chatbot</h1>
    <p>Groq API ile güçlendirilmiş yapay zeka asistanı</p>
</div>
""", unsafe_allow_html=True)

# Chat container
chat_container = st.container()

# Mesajları göster
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
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
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(user_message["time"])
    
    # Bot yanıtını al
    with st.chat_message("assistant"):
        with st.spinner("🤔 Düşünüyor..."):
            try:
                # API'ye istek gönder
                response = requests.post(
                    f"{st.session_state.api_url}/chat",
                    json={
                        "message": prompt,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bot_response = data["response"]
                    
                    # Bot mesajını ekle
                    bot_message = {
                        "role": "assistant",
                        "content": bot_response,
                        "time": datetime.now().strftime("%H:%M")
                    }
                    st.session_state.messages.append(bot_message)
                    
                    # Bot yanıtını göster
                    st.markdown(bot_response)
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

with col2:
    st.markdown("**🚀 Özellikler:**")
    st.markdown("- Gerçek zamanlı chat")
    st.markdown("- Model seçimi")
    st.markdown("- Parametre ayarları")

with col3:
    st.markdown("**📞 Destek:**")
    st.markdown("- API durumu kontrolü")
    st.markdown("- Hata yönetimi")
    st.markdown("- Responsive tasarım")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🤖 AI Chatbot - Groq API ile güçlendirilmiş"
    "</div>",
    unsafe_allow_html=True
) 