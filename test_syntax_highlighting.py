#!/usr/bin/env python3
"""
Syntax Highlighting Test Script
Bu dosya kod vurgulama özelliğini test etmek için kullanılır.
"""

import streamlit as st
import sys
import os

# Test için örnek kodlar
test_codes = {
    'python': '''def fibonacci(n):
    """Fibonacci sayılarını hesapla"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")''',

    'javascript': '''function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// ES6 arrow function
const multiply = (a, b) => a * b;

console.log(factorial(5));
console.log(multiply(3, 4));''',

    'html': '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Test Sayfası</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 800px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Merhaba Dünya!</h1>
        <p>Bu bir test sayfasıdır.</p>
    </div>
</body>
</html>''',

    'css': '''/* Ana stiller */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 20px;
}

/* Responsive tasarım */
@media (max-width: 768px) {
    .container {
        margin: 10px;
        padding: 15px;
    }
}''',

    'sql': '''-- Kullanıcı tablosu oluştur
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kullanıcı ekle
INSERT INTO users (username, email) 
VALUES ('test_user', 'test@example.com');

-- Kullanıcıları listele
SELECT id, username, email, created_at 
FROM users 
WHERE created_at > '2024-01-01'
ORDER BY created_at DESC;''',

    'json': '''{
    "name": "Test Projesi",
    "version": "1.0.0",
    "description": "Syntax highlighting test projesi",
    "author": {
        "name": "Test Kullanıcı",
        "email": "test@example.com"
    },
    "dependencies": {
        "streamlit": "^1.28.1",
        "pygments": "^2.15.0"
    },
    "scripts": {
        "start": "streamlit run app.py",
        "test": "python test_syntax_highlighting.py"
    }
}''',

    'yaml': '''# Docker Compose konfigürasyonu
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DEBUG=true
      - API_URL=http://localhost:5002
    volumes:
      - ./data:/app/data
    depends_on:
      - db
  
  db:
    image: sqlite:latest
    volumes:
      - db_data:/var/lib/sqlite
    environment:
      - SQLITE_DATABASE=chatbot.db

volumes:
  db_data:'''
}

def test_syntax_highlighting():
    """Syntax highlighting özelliğini test et"""
    st.title("🎨 Syntax Highlighting Test")
    st.markdown("Bu sayfa kod vurgulama özelliğini test etmek için kullanılır.")
    
    # Test kodlarını göster
    for language, code in test_codes.items():
        st.markdown(f"### {language.upper()} Örneği")
        st.code(code, language=language)
        st.markdown("---")

if __name__ == "__main__":
    test_syntax_highlighting() 