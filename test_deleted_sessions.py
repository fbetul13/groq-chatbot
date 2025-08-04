#!/usr/bin/env python3
"""
Test script for deleted sessions functionality
"""

import requests
import json
import time

# API base URL
API_URL = "http://localhost:5002/api"

def test_deleted_sessions():
    """Test the deleted sessions functionality"""
    
    print("🧪 Testing Deleted Sessions Functionality")
    print("=" * 50)
    
    # Test data
    test_user = {
        "username": "test_user_deleted_sessions",
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
        
        # 2. Create a test session by sending a message
        print("\n2. Creating a test session...")
        chat_data = {
            "message": "Bu bir test mesajıdır. Silinen oturumlar özelliğini test ediyoruz.",
            "model": "llama3-8b-8192",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = session.post(f"{API_URL}/chat", json=chat_data)
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ Test session created: {session_id}")
        else:
            print(f"❌ Session creation failed: {response.text}")
            return
        
        # 3. Get sessions to verify it exists
        print("\n3. Verifying session exists...")
        response = session.get(f"{API_URL}/sessions")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            print(f"✅ Found {len(sessions)} active sessions")
        else:
            print(f"❌ Failed to get sessions: {response.text}")
            return
        
        # 4. Delete the session (move to trash)
        print(f"\n4. Deleting session {session_id}...")
        response = session.delete(f"{API_URL}/sessions/{session_id}")
        if response.status_code == 200:
            print("✅ Session moved to trash successfully")
        else:
            print(f"❌ Failed to delete session: {response.text}")
            return
        
        # 5. Verify session is no longer in active sessions
        print("\n5. Verifying session is removed from active sessions...")
        response = session.get(f"{API_URL}/sessions")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            print(f"✅ Active sessions count: {len(sessions)}")
        else:
            print(f"❌ Failed to get sessions: {response.text}")
            return
        
        # 6. Get deleted sessions
        print("\n6. Getting deleted sessions...")
        response = session.get(f"{API_URL}/deleted-sessions")
        if response.status_code == 200:
            deleted_sessions = response.json().get('deleted_sessions', [])
            print(f"✅ Found {len(deleted_sessions)} deleted sessions")
            if deleted_sessions:
                deleted_session = deleted_sessions[0]
                print(f"   - Session ID: {deleted_session['session_id']}")
                print(f"   - Session Name: {deleted_session['session_name']}")
                print(f"   - Message Count: {deleted_session['message_count']}")
                print(f"   - Deleted At: {deleted_session['deleted_at']}")
        else:
            print(f"❌ Failed to get deleted sessions: {response.text}")
            return
        
        # 7. Restore the deleted session
        print(f"\n7. Restoring deleted session {session_id}...")
        response = session.post(f"{API_URL}/deleted-sessions/{session_id}/restore")
        if response.status_code == 200:
            print("✅ Session restored successfully")
        else:
            print(f"❌ Failed to restore session: {response.text}")
            return
        
        # 8. Verify session is back in active sessions
        print("\n8. Verifying session is restored...")
        response = session.get(f"{API_URL}/sessions")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            print(f"✅ Active sessions count after restore: {len(sessions)}")
        else:
            print(f"❌ Failed to get sessions: {response.text}")
            return
        
        # 9. Delete again and test permanent deletion
        print(f"\n9. Deleting session again for permanent deletion test...")
        response = session.delete(f"{API_URL}/sessions/{session_id}")
        if response.status_code == 200:
            print("✅ Session moved to trash again")
        else:
            print(f"❌ Failed to delete session: {response.text}")
            return
        
        # 10. Permanently delete the session
        print(f"\n10. Permanently deleting session {session_id}...")
        response = session.delete(f"{API_URL}/deleted-sessions/{session_id}/permanent-delete")
        if response.status_code == 200:
            print("✅ Session permanently deleted")
        else:
            print(f"❌ Failed to permanently delete session: {response.text}")
            return
        
        # 11. Verify session is completely gone
        print("\n11. Verifying session is completely removed...")
        response = session.get(f"{API_URL}/deleted-sessions")
        if response.status_code == 200:
            deleted_sessions = response.json().get('deleted_sessions', [])
            print(f"✅ Deleted sessions count after permanent deletion: {len(deleted_sessions)}")
        else:
            print(f"❌ Failed to get deleted sessions: {response.text}")
            return
        
        print("\n🎉 All tests passed! Deleted sessions functionality is working correctly.")
        
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
    test_deleted_sessions() 