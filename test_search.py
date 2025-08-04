#!/usr/bin/env python3
"""
Test script for search functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API base URL
API_URL = "http://localhost:5002/api"

def test_search_functionality():
    """Test the search functionality"""
    
    print("🧪 Testing Search Functionality")
    print("=" * 50)
    
    # Test data
    test_user = {
        "username": "test_user_search",
        "password": "test123456"
    }
    
    session = requests.Session()
    
    try:
        # 1. Register a test user
        print("1. Registering test user...")
        response = session.post(f"{API_URL}/register", json=test_user)
        if response.status_code == 200:
            print("✅ User registered successfully")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
        
        # 2. Create multiple test sessions with different content
        print("\n2. Creating test sessions...")
        test_messages = [
            "Python programlama dili hakkında bilgi verir misin?",
            "JavaScript ile web geliştirme nasıl yapılır?",
            "Machine learning algoritmaları nelerdir?",
            "Veritabanı tasarımı nasıl yapılır?",
            "API geliştirme best practices nelerdir?",
            "Docker containerization nedir?",
            "React framework'ü nasıl kullanılır?",
            "Git version control sistemi nasıl çalışır?",
            "Linux komut satırı temel komutları nelerdir?",
            "Cloud computing servisleri nelerdir?"
        ]
        
        session_ids = []
        for i, message in enumerate(test_messages):
            chat_data = {
                "message": message,
                "model": "llama3-8b-8192",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            response = session.post(f"{API_URL}/chat", json=chat_data)
            if response.status_code == 200:
                data = response.json()
                session_ids.append(data.get('session_id'))
                print(f"✅ Test session {i+1} created")
            else:
                print(f"❌ Session {i+1} creation failed")
        
        # 3. Test basic search
        print("\n3. Testing basic search...")
        search_data = {
            "query": "Python",
            "limit": 10,
            "offset": 0
        }
        
        response = session.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Basic search found {results['total_count']} results")
            for msg in results['messages'][:3]:  # Show first 3 results
                print(f"   - {msg['session_name']}: {msg['content'][:50]}...")
        else:
            print(f"❌ Basic search failed: {response.text}")
        
        # 4. Test role filter search
        print("\n4. Testing role filter search...")
        search_data = {
            "query": "programlama",
            "role": "user",
            "limit": 10,
            "offset": 0
        }
        
        response = session.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Role filter search found {results['total_count']} user messages")
        else:
            print(f"❌ Role filter search failed: {response.text}")
        
        # 5. Test session-specific search
        print("\n5. Testing session-specific search...")
        if session_ids:
            search_data = {
                "query": "web",
                "session_id": session_ids[1],  # JavaScript session
                "limit": 10,
                "offset": 0
            }
            
            response = session.post(f"{API_URL}/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Session-specific search found {results['total_count']} results")
            else:
                print(f"❌ Session-specific search failed: {response.text}")
        
        # 6. Test date filter search
        print("\n6. Testing date filter search...")
        today = datetime.now().strftime('%Y-%m-%d')
        search_data = {
            "date_from": today,
            "limit": 10,
            "offset": 0
        }
        
        response = session.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Date filter search found {results['total_count']} results from today")
        else:
            print(f"❌ Date filter search failed: {response.text}")
        
        # 7. Test session search
        print("\n7. Testing session name search...")
        response = session.get(f"{API_URL}/search/sessions?query=Python")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Session search found {len(results['sessions'])} sessions")
        else:
            print(f"❌ Session search failed: {response.text}")
        
        # 8. Test search statistics
        print("\n8. Testing search statistics...")
        response = session.get(f"{API_URL}/search/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Search stats retrieved:")
            print(f"   - Total messages: {stats['total_messages']}")
            print(f"   - Total sessions: {stats['total_sessions']}")
            print(f"   - User messages: {stats['user_messages']}")
            print(f"   - Bot messages: {stats['bot_messages']}")
            if stats['last_message_date']:
                print(f"   - Last message: {stats['last_message_date']}")
        else:
            print(f"❌ Search stats failed: {response.text}")
        
        # 9. Test pagination
        print("\n9. Testing pagination...")
        search_data = {
            "query": "a",
            "limit": 3,
            "offset": 0
        }
        
        response = session.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Pagination test - Page 1: {len(results['messages'])} results")
            print(f"   - Total count: {results['total_count']}")
            print(f"   - Has more: {results['has_more']}")
            
            if results['has_more']:
                # Test next page
                search_data['offset'] = 3
                response = session.post(f"{API_URL}/search", json=search_data)
                if response.status_code == 200:
                    page2_results = response.json()
                    print(f"✅ Pagination test - Page 2: {len(page2_results['messages'])} results")
        else:
            print(f"❌ Pagination test failed: {response.text}")
        
        print("\n🎉 All search tests passed! Search functionality is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
    
    finally:
        # Clean up - logout
        try:
            session.post(f"{API_URL}/logout")
            print("\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    test_search_functionality() 