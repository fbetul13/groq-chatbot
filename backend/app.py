from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq
import json

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
CORS(app)  # Frontend'den gelen isteklere izin ver

# Groq API anahtarını al
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

# Groq client'ını başlat
client = Groq(api_key=GROQ_API_KEY)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Streamlit'ten gelen parametreleri al (varsayılan değerlerle)
        model = data.get('model', 'llama3-8b-8192')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        
        # Groq API'ye istek gönder
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Yanıtı al
        assistant_response = chat_completion.choices[0].message.content
        
        return jsonify({
            'response': assistant_response,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Chatbot API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050) 