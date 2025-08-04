#!/usr/bin/env python3
"""
Animation Test Script
Bu dosya mesaj gönderme animasyonlarını test etmek için kullanılır.
"""

import streamlit as st
import time
import random
import math

def test_typing_animation():
    """Yazma animasyonunu test et"""
    st.title("⌨️ Yazma Animasyonu Testi")
    
    if st.button("Yazma Animasyonu Başlat"):
        # Farklı animasyon türleri
        animation_types = {
            "thinking": ["🤔 Düşünüyor", "🤔 Düşünüyor.", "🤔 Düşünüyor..", "🤔 Düşünüyor..."],
            "typing": ["⌨️ Yazıyor", "⌨️ Yazıyor.", "⌨️ Yazıyor..", "⌨️ Yazıyor..."],
            "processing": ["⚙️ İşleniyor", "⚙️ İşleniyor.", "⚙️ İşleniyor..", "⚙️ İşleniyor..."],
            "analyzing": ["🔍 Analiz ediyor", "🔍 Analiz ediyor.", "🔍 Analiz ediyor..", "🔍 Analiz ediyor..."],
            "searching": ["🔎 Arıyor", "🔎 Arıyor.", "🔎 Arıyor..", "🔎 Arıyor..."]
        }
        
        # Rastgele animasyon türü seç
        animation_type = random.choice(list(animation_types.keys()))
        indicators = animation_types[animation_type]
        
        # Progress bar ile animasyon
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(len(indicators)):
            progress_bar.progress((i + 1) / len(indicators))
            status_text.text(indicators[i])
            time.sleep(0.3)
        
        st.success("✅ Yazma animasyonu tamamlandı!")

def test_sending_animation():
    """Gönderme animasyonunu test et"""
    st.title("📤 Gönderme Animasyonu Testi")
    
    if st.button("Gönderme Animasyonu Başlat"):
        # Gönderme animasyonu
        sending_indicators = ["📤 Gönderiliyor", "📤 Gönderiliyor.", "📤 Gönderiliyor..", "📤 Gönderiliyor..."]
        
        status_text = st.empty()
        
        for indicator in sending_indicators:
            status_text.text(indicator)
            time.sleep(0.2)
        
        st.success("✅ Gönderme animasyonu tamamlandı!")

def test_loading_dots():
    """Yükleme noktaları animasyonunu test et"""
    st.title("⠋ Yükleme Noktaları Testi")
    
    if st.button("Yükleme Noktaları Başlat"):
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        status_text = st.empty()
        
        for i in range(10):
            status_text.text(f"Yükleniyor {dots[i]}")
            time.sleep(0.1)
        
        st.success("✅ Yükleme noktaları tamamlandı!")

def test_pulse_animation():
    """Nabız animasyonunu test et"""
    st.title("💓 Nabız Animasyonu Testi")
    
    if st.button("Nabız Animasyonu Başlat"):
        status_text = st.empty()
        
        for i in range(20):
            # Sinüs dalgası ile nabız efekti
            intensity = abs(math.sin(i * 0.5)) * 100
            status_text.text(f"💓 İşleniyor... {intensity:.0f}%")
            time.sleep(0.1)
        
        st.success("✅ Nabız animasyonu tamamlandı!")

def test_typing_cursor():
    """Yazma imleci animasyonunu test et"""
    st.title("| Yazma İmleci Testi")
    
    if st.button("Yazma İmleci Başlat"):
        cursor_states = ["|", " ", "|", " "]
        
        status_text = st.empty()
        
        for i in range(8):
            status_text.text(f"Yazıyor{cursor_states[i % 4]}")
            time.sleep(0.3)
        
        st.success("✅ Yazma imleci tamamlandı!")

def test_all_animations():
    """Tüm animasyonları test et"""
    st.title("🎬 Tüm Animasyonlar Testi")
    
    if st.button("Tüm Animasyonları Başlat"):
        # Yazma animasyonu
        st.subheader("1. Yazma Animasyonu")
        test_typing_animation()
        
        # Gönderme animasyonu
        st.subheader("2. Gönderme Animasyonu")
        test_sending_animation()
        
        # Yükleme noktaları
        st.subheader("3. Yükleme Noktaları")
        test_loading_dots()
        
        # Nabız animasyonu
        st.subheader("4. Nabız Animasyonu")
        test_pulse_animation()
        
        # Yazma imleci
        st.subheader("5. Yazma İmleci")
        test_typing_cursor()
        
        st.success("🎉 Tüm animasyonlar başarıyla test edildi!")

def main():
    """Ana test fonksiyonu"""
    st.set_page_config(
        page_title="Animasyon Testi",
        page_icon="🎬",
        layout="wide"
    )
    
    st.markdown("""
    # 🎬 Mesaj Gönderme Animasyonları Test Sayfası
    
    Bu sayfa chatbot'ta kullanılan animasyonları test etmek için kullanılır.
    """)
    
    # Test seçenekleri
    test_option = st.selectbox(
        "Test edilecek animasyonu seçin:",
        [
            "Tüm Animasyonlar",
            "Yazma Animasyonu",
            "Gönderme Animasyonu", 
            "Yükleme Noktaları",
            "Nabız Animasyonu",
            "Yazma İmleci"
        ]
    )
    
    if test_option == "Tüm Animasyonlar":
        test_all_animations()
    elif test_option == "Yazma Animasyonu":
        test_typing_animation()
    elif test_option == "Gönderme Animasyonu":
        test_sending_animation()
    elif test_option == "Yükleme Noktaları":
        test_loading_dots()
    elif test_option == "Nabız Animasyonu":
        test_pulse_animation()
    elif test_option == "Yazma İmleci":
        test_typing_cursor()
    
    # Kullanım talimatları
    st.markdown("---")
    st.markdown("### 📖 Kullanım Talimatları:")
    st.markdown("""
    Chatbot'ta animasyonlar şu durumlarda kullanılır:
    
    1. **Yazma Animasyonu:** Bot yanıt verirken
    2. **Gönderme Animasyonu:** Mesaj gönderilirken
    3. **Yükleme Noktaları:** Veri yüklenirken
    4. **Nabız Animasyonu:** İşlem devam ederken
    5. **Yazma İmleci:** Metin yazılırken
    
    Animasyonlar kullanıcı deneyimini iyileştirir ve işlemlerin devam ettiğini gösterir.
    """)

if __name__ == "__main__":
    main() 