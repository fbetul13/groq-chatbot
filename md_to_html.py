#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML Converter
Bu script, bitirme_projesi_taslak.md dosyasını HTML belgesine dönüştürür.
HTML dosyası tarayıcıda açılıp PDF olarak kaydedilebilir.
"""

import os
from pathlib import Path

def convert_md_to_html():
    """Markdown dosyasını HTML belgesine dönüştürür."""
    
    # Gerekli kütüphaneleri kontrol et
    try:
        import markdown
    except ImportError:
        print("📦 Markdown kütüphanesi yükleniyor...")
        os.system("pip3 install markdown")
        try:
            import markdown
        except ImportError:
            print("❌ Markdown kütüphanesi yüklenemedi")
            return False
    
    # Markdown dosyasının yolunu belirle
    md_file = Path("/Users/betul/Desktop/bitirme_projesi_taslak.md")
    
    if not md_file.exists():
        print(f"❌ {md_file} dosyası bulunamadı!")
        return False
    
    # Markdown içeriğini oku
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"✅ Markdown dosyası okundu: {len(md_content)} karakter")
    except Exception as e:
        print(f"❌ Markdown dosyası okunamadı: {e}")
        return False
    
    # Markdown'ı HTML'e çevir
    try:
        html_content = markdown.markdown(
            md_content, 
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        print("✅ Markdown HTML'e dönüştürüldü")
    except Exception as e:
        print(f"❌ HTML dönüştürme hatası: {e}")
        return False
    
    # HTML şablonu oluştur
    html_template = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bitirme Projesi Taslağı</title>
        <style>
            @page {{
                margin: 2cm;
                size: A4;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                font-size: 12pt;
                color: #333;
                background-color: white;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                margin-bottom: 20px;
                page-break-after: avoid;
                font-size: 24pt;
            }}
            
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 8px;
                margin-top: 25px;
                margin-bottom: 15px;
                page-break-after: avoid;
                font-size: 18pt;
            }}
            
            h3 {{
                color: #7f8c8d;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 14pt;
            }}
            
            h4 {{
                color: #95a5a6;
                margin-top: 15px;
                margin-bottom: 8px;
                font-size: 12pt;
            }}
            
            p {{
                margin-bottom: 12px;
                text-align: justify;
            }}
            
            ul, ol {{
                margin-bottom: 15px;
                padding-left: 25px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 11pt;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                vertical-align: top;
            }}
            
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            code {{
                background-color: #f8f9fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 11pt;
                color: #e74c3c;
            }}
            
            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                border-left: 4px solid #3498db;
                margin: 15px 0;
                font-family: 'Courier New', monospace;
                font-size: 11pt;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
                color: #333;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 15px 0;
                padding: 10px 20px;
                background-color: #f8f9fa;
                font-style: italic;
            }}
            
            .placeholder {{
                color: #7f8c8d;
                font-style: italic;
                background-color: #f8f9fa;
                padding: 5px;
                border-radius: 3px;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .no-break {{
                page-break-inside: avoid;
            }}
            
            /* Başlık sayfası için özel stiller */
            .title-page {{
                text-align: center;
                page-break-after: always;
                margin-top: 100px;
            }}
            
            .title-page h1 {{
                font-size: 28pt;
                margin-bottom: 30px;
                border: none;
            }}
            
            .title-page .subtitle {{
                font-size: 16pt;
                color: #7f8c8d;
                margin-bottom: 50px;
            }}
            
            .title-page .info {{
                font-size: 14pt;
                margin-bottom: 20px;
            }}
            
            /* Yazdırma için özel stiller */
            @media print {{
                body {{
                    margin: 0;
                    padding: 0;
                }}
                
                .no-print {{
                    display: none;
                }}
                
                h1, h2, h3 {{
                    page-break-after: avoid;
                }}
                
                table {{
                    page-break-inside: avoid;
                }}
            }}
            
            /* Ekran için navigasyon */
            .nav {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                text-align: center;
                z-index: 1000;
            }}
            
            .nav button {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                margin: 0 5px;
                border-radius: 3px;
                cursor: pointer;
            }}
            
            .nav button:hover {{
                background-color: #2980b9;
            }}
            
            .content {{
                margin-top: 60px;
            }}
        </style>
    </head>
    <body>
        <div class="nav no-print">
            <button onclick="window.print()">🖨️ PDF Olarak Yazdır</button>
            <button onclick="window.open('', '_blank').print()">📄 Yeni Pencerede Yazdır</button>
            <button onclick="downloadPDF()">💾 PDF İndir</button>
        </div>
        
        <div class="content">
            {html_content}
        </div>
        
        <script>
            function downloadPDF() {{
                window.print();
            }}
            
            // Sayfa yüklendiğinde placeholder'ları işaretle
            document.addEventListener('DOMContentLoaded', function() {{
                const placeholders = document.querySelectorAll('p, li, td');
                placeholders.forEach(element => {{
                    if (element.textContent.includes('[Doldurulacak]') || 
                        element.textContent.includes('[Ad Soyad]') ||
                        element.textContent.includes('[Tarih]')) {{
                        element.classList.add('placeholder');
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # HTML dosyasını kaydet
    output_file = "bitirme_projesi_taslak.html"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"✅ HTML dosyası başarıyla oluşturuldu: {output_file}")
        print(f"📁 Dosya konumu: {os.path.abspath(output_file)}")
        return True
    except Exception as e:
        print(f"❌ HTML dosyası kaydedilemedi: {e}")
        return False

def main():
    """Ana fonksiyon."""
    print("🔄 Markdown dosyası HTML'e dönüştürülüyor...")
    print("=" * 50)
    
    success = convert_md_to_html()
    
    if success:
        print("\n🎉 Dönüştürme tamamlandı!")
        print("\n📋 Sonraki adımlar:")
        print("1. HTML dosyasını tarayıcıda açın")
        print("2. 'PDF Olarak Yazdır' butonuna tıklayın")
        print("3. PDF olarak kaydedin")
        print("4. Gerekirse düzenlemeler yapın")
        
        # HTML dosyasını otomatik aç
        try:
            import subprocess
            subprocess.run(['open', 'bitirme_projesi_taslak.html'])
            print("\n🌐 HTML dosyası tarayıcıda açıldı!")
        except:
            print("\n📂 HTML dosyasını manuel olarak açın")
    else:
        print("\n❌ Dönüştürme başarısız!")
        print("Lütfen hata mesajlarını kontrol edin.")

if __name__ == "__main__":
    main() 