#!/usr/bin/env python3
"""
Markdown Test Script
Bu dosya gelişmiş markdown özelliklerini test etmek için kullanılır.
"""

import streamlit as st

def test_markdown_features():
    """Markdown özelliklerini test et"""
    st.title("📝 Markdown Test Sayfası")
    st.markdown("Bu sayfa gelişmiş markdown özelliklerini test etmek için kullanılır.")
    
    # Test markdown içeriği
    test_markdown = """
# 🎯 Ana Başlık

Bu bir **ana başlık** örneğidir.

## 📋 Alt Başlık

Bu bir *alt başlık* örneğidir.

### 🔧 Üçüncü Seviye

Bu bir üçüncü seviye başlık örneğidir.

---

## 📝 Metin Formatlaması

**Kalın metin** ve *italik metin* örnekleri.

~~Üstü çizili metin~~ ve `kod içinde metin` örnekleri.

> Bu bir alıntı bloğudur. Önemli bilgileri vurgulamak için kullanılır.

---

## 📋 Listeler

### Sırasız Liste:
* İlk öğe
* İkinci öğe
  * Alt öğe 1
  * Alt öğe 2
* Üçüncü öğe

### Sıralı Liste:
1. Birinci adım
2. İkinci adım
3. Üçüncü adım

---

## 📊 Tablolar

| Özellik | Açıklama | Durum |
|---------|----------|-------|
| Markdown | Metin formatlaması | ✅ Aktif |
| Kod Vurgulama | Syntax highlighting | ✅ Aktif |
| Tablolar | Veri gösterimi | ✅ Aktif |
| Listeler | Sıralı/sırasız | ✅ Aktif |

---

## 🔗 Linkler ve Resimler

[Google'a Git](https://www.google.com)

![Emoji](https://via.placeholder.com/150x50/3498db/ffffff?text=📝)

---

## 💻 Kod Blokları

### Python Kodu:
```python
def hello_world():
    print("Merhaba Dünya!")
    return "Başarılı!"

hello_world()
```

### JavaScript Kodu:
```javascript
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

console.log(factorial(5));
```

### HTML Kodu:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Sayfası</title>
</head>
<body>
    <h1>Merhaba Dünya!</h1>
</body>
</html>
```

---

## 📝 Dipnotlar

Bu bir dipnot örneğidir[^1].

[^1]: Bu dipnot açıklamasıdır.

---

## 🎨 Özel Formatlar

### Tanım Listesi:
Term 1
: Açıklama 1

Term 2
: Açıklama 2

### Kısaltmalar:
*[HTML]: HyperText Markup Language
*[CSS]: Cascading Style Sheets

---

## 📈 Matematiksel İfadeler

Basit matematik: `2 + 2 = 4`

Karmaşık formül: `E = mc²`

---

## 🎯 Sonuç

Bu test sayfası, chatbot'ta kullanılabilecek tüm markdown özelliklerini göstermektedir.

**Özellikler:**
- ✅ Başlıklar (H1-H6)
- ✅ Metin formatlaması (kalın, italik, üstü çizili)
- ✅ Listeler (sıralı/sırasız)
- ✅ Tablolar
- ✅ Linkler ve resimler
- ✅ Kod blokları
- ✅ Alıntılar
- ✅ Dipnotlar
- ✅ Tanım listeleri
- ✅ Kısaltmalar
- ✅ Yatay çizgiler
- ✅ Emoji desteği
"""

    # Markdown'ı göster
    st.markdown("### Test Markdown İçeriği:")
    st.markdown(test_markdown, unsafe_allow_html=True)
    
    # Kullanım talimatları
    st.markdown("---")
    st.markdown("### 📖 Kullanım Talimatları:")
    st.markdown("""
    Chatbot'ta markdown kullanmak için:
    
    1. **Başlıklar:** `# Ana Başlık`, `## Alt Başlık`
    2. **Formatlama:** `**kalın**`, `*italik*`, `~~üstü çizili~~`
    3. **Listeler:** `* öğe` veya `1. öğe`
    4. **Tablolar:** `| sütun1 | sütun2 |` formatında
    5. **Linkler:** `[metin](url)` formatında
    6. **Kod:** `kod` (satır içi) veya ```python kod bloğu```
    7. **Alıntılar:** `> metin` ile başlayan satırlar
    """)

if __name__ == "__main__":
    test_markdown_features() 