#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter
Bu script, bitirme_projesi_taslak.md dosyasını PDF belgesine dönüştürür.
"""

import os
import subprocess
from pathlib import Path

def convert_md_to_pdf():
    """Markdown dosyasını PDF belgesine dönüştürür."""
    
    # Markdown dosyasının yolunu belirle
    md_file = Path("/Users/betul/Desktop/bitirme_projesi_taslak.md")
    
    if not md_file.exists():
        print(f"❌ {md_file} dosyası bulunamadı!")
        return False
    
    # PDF çıktı dosyası
    output_file = "bitirme_projesi_taslak.pdf"
    
    print("🔄 Markdown dosyası PDF'e dönüştürülüyor...")
    print("=" * 50)
    
    # Yöntem 1: Pandoc ile (eğer yüklüyse)
    try:
        print("📋 Pandoc ile dönüştürme deneniyor...")
        result = subprocess.run([
            'pandoc',
            str(md_file),
            '-o', output_file,
            '--pdf-engine=wkhtmltopdf',
            '--css=style.css'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ PDF başarıyla oluşturuldu: {output_file}")
            return True
        else:
            print(f"⚠️ Pandoc hatası: {result.stderr}")
    except FileNotFoundError:
        print("⚠️ Pandoc bulunamadı, alternatif yöntem deneniyor...")
    
    # Yöntem 2: Python ile HTML -> PDF
    try:
        print("📋 Python ile HTML -> PDF dönüştürme deneniyor...")
        success = convert_via_html(md_file, output_file)
        if success:
            return True
    except Exception as e:
        print(f"⚠️ HTML -> PDF hatası: {e}")
    
    # Yöntem 3: WeasyPrint ile
    try:
        print("📋 WeasyPrint ile dönüştürme deneniyor...")
        success = convert_via_weasyprint(md_file, output_file)
        if success:
            return True
    except Exception as e:
        print(f"⚠️ WeasyPrint hatası: {e}")
    
    print("❌ Hiçbir yöntem çalışmadı!")
    return False

def convert_via_html(md_file, output_file):
    """Markdown'ı HTML'e çevirip PDF'e dönüştürür."""
    
    # Gerekli kütüphaneleri kontrol et
    try:
        import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        print("📦 Gerekli kütüphaneler yükleniyor...")
        os.system("pip3 install markdown weasyprint")
        try:
            import markdown
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
        except ImportError:
            print("❌ Kütüphaneler yüklenemedi")
            return False
    
    # Markdown'ı oku
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Markdown'ı HTML'e çevir
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # HTML şablonu oluştur
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Bitirme Projesi Taslağı</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                margin: 2cm;
                font-size: 12pt;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                page-break-after: avoid;
            }}
            h2 {{
                color: #34495e;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 15px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            code {{
                background-color: #f8f9fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                border-left: 4px solid #3498db;
            }}
            .placeholder {{
                color: #7f8c8d;
                font-style: italic;
            }}
            @page {{
                margin: 2cm;
                @top-center {{
                    content: "Bitirme Projesi Taslağı";
                    font-size: 10pt;
                    color: #7f8c8d;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # HTML'i PDF'e dönüştür
    try:
        font_config = FontConfiguration()
        HTML(string=html_template).write_pdf(output_file, font_config=font_config)
        print(f"✅ PDF başarıyla oluşturuldu: {output_file}")
        return True
    except Exception as e:
        print(f"❌ PDF oluşturma hatası: {e}")
        return False

def convert_via_weasyprint(md_file, output_file):
    """WeasyPrint ile direkt dönüştürme."""
    
    try:
        import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        print("❌ WeasyPrint kütüphanesi bulunamadı")
        return False
    
    # Markdown'ı oku ve HTML'e çevir
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Basit HTML'e çevir
    html_content = markdown.markdown(md_content)
    
    # CSS stilleri
    css_content = """
    body { font-family: Arial, sans-serif; margin: 2cm; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
    h2 { color: #34495e; margin-top: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background-color: #f2f2f2; }
    """
    
    # PDF oluştur
    font_config = FontConfiguration()
    HTML(string=f"<html><head><style>{css_content}</style></head><body>{html_content}</body></html>").write_pdf(
        output_file, 
        font_config=font_config
    )
    
    print(f"✅ PDF başarıyla oluşturuldu: {output_file}")
    return True

def main():
    """Ana fonksiyon."""
    print("🔄 Markdown dosyası PDF'e dönüştürülüyor...")
    print("=" * 50)
    
    success = convert_md_to_pdf()
    
    if success:
        print("\n🎉 Dönüştürme tamamlandı!")
        print(f"\n📁 PDF dosyası: {os.path.abspath('bitirme_projesi_taslak.pdf')}")
        print("\n📋 Sonraki adımlar:")
        print("1. PDF dosyasını açın")
        print("2. İçeriği kontrol edin")
        print("3. Gerekirse düzenlemeler yapın")
    else:
        print("\n❌ Dönüştürme başarısız!")
        print("Lütfen alternatif yöntemleri deneyin.")

if __name__ == "__main__":
    main() 