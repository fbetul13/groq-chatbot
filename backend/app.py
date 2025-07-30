from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq
import json
import sqlite3
from datetime import datetime
import uuid
import hashlib
import secrets
import csv
import io

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
CORS(app, supports_credentials=True)  # Frontend'den gelen isteklere izin ver

# Groq API anahtarını al
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

# Groq client'ını başlat
client = Groq(api_key=GROQ_API_KEY)

# Veritabanı başlatma
def init_db():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sohbet oturumları tablosu (kullanıcı ID'si eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            session_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Mesajlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model TEXT,
            temperature REAL,
            max_tokens INTEGER,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# Şifre hash fonksiyonu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Kullanıcı kimlik doğrulama decorator'ı
def require_auth(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/register', methods=['POST'])
def register():
    """Kullanıcı kaydı"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            
            # Kullanıcı ID'sini al
            user_id = cursor.lastrowid
            
            conn.close()
            
            # Session'a kullanıcı bilgilerini kaydet
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                'message': 'Registration successful',
                'user_id': user_id,
                'username': username
            })
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username already exists'}), 409
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        user = cursor.fetchone()
        
        if user:
            user_id, username = user
            
            # Son giriş zamanını güncelle
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            # Session'a kullanıcı bilgilerini kaydet
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                'message': 'Login successful',
                'user_id': user_id,
                'username': username
            })
        else:
            conn.close()
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Kullanıcı çıkışı"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/user', methods=['GET'])
@require_auth
def get_user_info():
    """Kullanıcı bilgilerini getir"""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    })

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = session['user_id']
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Yeni session oluştur (eğer session_id yoksa)
        if not session_id:
            session_id = str(uuid.uuid4())
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_sessions (session_id, user_id, session_name) VALUES (?, ?, ?)',
                (session_id, user_id, f"Sohbet {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            )
            conn.commit()
            conn.close()
        else:
            # Session'ın bu kullanıcıya ait olduğunu kontrol et
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_id FROM chat_sessions WHERE session_id = ?',
                (session_id,)
            )
            session_user = cursor.fetchone()
            conn.close()
            
            if not session_user or session_user[0] != user_id:
                return jsonify({'error': 'Access denied to this session'}), 403
        
        # Streamlit'ten gelen parametreleri al (varsayılan değerlerle)
        model = data.get('model', 'llama3-8b-8192')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        
        # Kullanıcı mesajını veritabanına kaydet
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO messages (session_id, role, content, model, temperature, max_tokens) VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, 'user', user_message, model, temperature, max_tokens)
        )
        conn.commit()
        
        # Sohbet geçmişini al
        cursor.execute(
            'SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC',
            (session_id,)
        )
        chat_history = cursor.fetchall()
        
        # Groq API için mesaj formatını hazırla
        messages = []
        for role, content in chat_history:
            messages.append({"role": role, "content": content})
        
        # Groq API'ye istek gönder
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Yanıtı al
        assistant_response = chat_completion.choices[0].message.content
        
        # Bot yanıtını veritabanına kaydet
        cursor.execute(
            'INSERT INTO messages (session_id, role, content, model, temperature, max_tokens) VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, 'assistant', assistant_response, model, temperature, max_tokens)
        )
        
        # Session'ın güncellenme zamanını güncelle
        cursor.execute(
            'UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?',
            (session_id,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'response': assistant_response,
            'session_id': session_id,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Kullanıcının sohbet oturumlarını getir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, session_name, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE messages.session_id = chat_sessions.session_id) as message_count
            FROM chat_sessions 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        sessions = cursor.fetchall()
        conn.close()
        
        session_list = []
        for session_data in sessions:
            session_list.append({
                'session_id': session_data[0],
                'session_name': session_data[1],
                'created_at': session_data[2],
                'updated_at': session_data[3],
                'message_count': session_data[4]
            })
        
        return jsonify({'sessions': session_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
@require_auth
def get_session_messages(session_id):
    """Belirli bir oturumun mesajlarını getir (kullanıcı kontrolü ile)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'role': msg[0],
                'content': msg[1],
                'timestamp': msg[2],
                'model': msg[3],
                'temperature': msg[4],
                'max_tokens': msg[5]
            })
        
        return jsonify({'messages': message_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@require_auth
def delete_session(session_id):
    """Sohbet oturumunu sil (kullanıcı kontrolü ile)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        # Önce mesajları sil
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        # Sonra oturumu sil
        cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/rename', methods=['PUT'])
@require_auth
def rename_session(session_id):
    """Sohbet oturumunu yeniden adlandır (kullanıcı kontrolü ile)"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        new_name = data.get('session_name', '')
        
        if not new_name:
            return jsonify({'error': 'Session name is required'}), 400
        
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        cursor.execute(
            'UPDATE chat_sessions SET session_name = ? WHERE session_id = ?',
            (new_name, session_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session renamed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download', methods=['GET'])
@require_auth
def download_session(session_id):
    """Sohbet oturumunu JSON formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # JSON formatında hazırla
        session_data = {
            'session_id': session_id,
            'session_name': session_name,
            'user_id': user_id,
            'username': session['username'],
            'export_date': datetime.now().isoformat(),
            'messages': []
        }
        
        for msg in messages:
            session_data['messages'].append({
                'role': msg[0],
                'content': msg[1],
                'timestamp': msg[2],
                'model': msg[3],
                'temperature': msg[4],
                'max_tokens': msg[5]
            })
        
        # JSON dosyası oluştur
        json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        json_buffer.seek(0)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            json_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/download-csv', methods=['GET'])
@require_auth
def download_session_csv(session_id):
    """Sohbet oturumunu CSV formatında indir"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id, session_name FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_data = cursor.fetchone()
        
        if not session_data or session_data[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        session_name = session_data[1]
        
        # Mesajları al
        cursor.execute('''
            SELECT role, content, timestamp, model, temperature, max_tokens
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        ''', (session_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # CSV formatında hazırla
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Başlık satırı
        csv_writer.writerow(['Rol', 'İçerik', 'Zaman', 'Model', 'Sıcaklık', 'Maksimum Token'])
        
        # Mesajları yaz
        for msg in messages:
            csv_writer.writerow([
                'Kullanıcı' if msg[0] == 'user' else 'AI',
                msg[1],
                msg[2],
                msg[3],
                msg[4],
                msg[5]
            ])
        
        csv_buffer.seek(0)
        csv_data = csv_buffer.getvalue().encode('utf-8')
        csv_buffer = io.BytesIO(csv_data)
        csv_buffer.seek(0)
        
        filename = f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/clear', methods=['DELETE'])
@require_auth
def clear_session_messages(session_id):
    """Sohbet oturumundaki tüm mesajları sil (oturumu silme)"""
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Session'ın bu kullanıcıya ait olduğunu kontrol et
        cursor.execute(
            'SELECT user_id FROM chat_sessions WHERE session_id = ?',
            (session_id,)
        )
        session_user = cursor.fetchone()
        
        if not session_user or session_user[0] != user_id:
            conn.close()
            return jsonify({'error': 'Access denied to this session'}), 403
        
        # Sadece mesajları sil, oturumu silme
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session messages cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Chatbot API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050) 