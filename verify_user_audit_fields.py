import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_user_audit_fields():
    print("--- Testing User Audit Fields ---")
    
    # 1. Login
    print("\n1. Testing Login...")
    login_data = {
        "email": "admin@auditbrain.com",
        "password": "adminpass"
    }
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        data = response.json()
        print(f"Login Success. User info: {json.dumps(data.get('user'), indent=2)}")
        if 'is_auditor' in data.get('user', {}):
            print("SUCCESS: 'is_auditor' found in login response.")
        else:
            print("FAILURE: 'is_auditor' NOT found in login response.")
        
        token = data.get('access')
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Profile
        print("\n2. Testing Profile...")
        response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Profile Info: {json.dumps(data, indent=2)}")
            if 'is_auditor' in data:
                print("SUCCESS: 'is_auditor' found in profile.")
            else:
                print("FAILURE: 'is_auditor' NOT found in profile.")
        
        # 3. User List
        print("\n3. Testing User List...")
        response = requests.get(f"{BASE_URL}/users/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            users = data.get('results', []) if isinstance(data, dict) else data
            if users:
                user = users[0]
                print(f"First User Sample: {json.dumps(user, indent=2)}")
                if 'is_auditor' in user:
                    print("SUCCESS: 'is_auditor' found in user list.")
                else:
                    print("FAILURE: 'is_auditor' NOT found in user list.")
    else:
        print(f"Login Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_user_audit_fields()
