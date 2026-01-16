
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def test_question():
    print("=" * 60)
    print("  TESTING REASONING: 'Audits completed this year'")
    print("=" * 60)

    # 1. Login
    print_info("Authenticating...")
    auth_resp = requests.post(f"{API_URL}/auth/login/", json={
        "email": "admin@auditbrain.com", 
        "password": "admin123"
    })
    
    if auth_resp.status_code != 200:
        print_error("Login failed")
        return

    token = auth_resp.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    print_success("Authenticated")

    # 2. Create Conversation
    print_info("Creating conversation...")
    conv_resp = requests.post(f"{API_URL}/ai-conversations/", headers=headers, json={
        "title": "Test: Audits this year"
    })
    conversation_id = conv_resp.json()['id']
    print_success(f"Conversation created: {conversation_id}")

    # 3. Ask Question
    question = "Cuantas auditorias hay completadas el año pasado?"
    print_info(f"Asking: '{question}'")
    
    chat_resp = requests.post(
        f"{API_URL}/ai-conversations/{conversation_id}/chat/",
        headers=headers,
        json={
            "message": question,
            "enable_tools": True
        },
        timeout=120
    )


    if chat_resp.status_code != 200:
        print_error(f"Chat failed: {chat_resp.text}")
        return

    data = chat_resp.json()
    print(f"DEBUG: Full Response: {json.dumps(data, indent=2)}")

    if not data.get('messages'):
        print_error("No messages in response!")
        return

    last_msg = data['messages'][-1]
    content = last_msg['content']
    tool_calls = last_msg.get('tool_calls', [])

    print("\n" + "-"*30)
    print(f"🤖 AI Response:\n{content}")
    print("-"*30 + "\n")

    if tool_calls:
        print_success(f"Tools used: {len(tool_calls)}")
        for tc in tool_calls:
            print(f"   🔧 {tc['function']['name']}: {tc['function']['arguments']}")
    else:
        print_error("No tools used! The AI guessed or failed to query data.")

    # Cleanup
    requests.delete(f"{API_URL}/ai-conversations/{conversation_id}/", headers=headers)
    print_info("Cleanup done")

if __name__ == "__main__":
    test_question()
