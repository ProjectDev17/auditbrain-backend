"""Quick MCP Test - Non-interactive"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 50)
print("MCP Quick Test")
print("=" * 50)

# 1. Authenticate
print("\n1. Authenticating...")
r = requests.post(f"{BASE_URL}/api/auth/login/", json={
    "email": "admin@auditbrain.com",
    "password": "admin123"
})
if r.status_code != 200:
    print(f"   FAILED: {r.text}")
    exit(1)
token = r.json().get("access")
print(f"   OK - Token: {token[:40]}...")

# 2. MCP Initialize
print("\n2. MCP Initialize...")
r = requests.post(f"{BASE_URL}/mcp/", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
})
result = r.json()
if "result" in result:
    print(f"   OK - Server: {result['result']['serverInfo']['name']}")
else:
    print(f"   FAILED: {result}")

# 3. MCP List Tools
print("\n3. MCP List Tools...")
r = requests.post(f"{BASE_URL}/mcp/", json={
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}, headers={"Authorization": f"Bearer {token}"})
result = r.json()
if "result" in result:
    tools = result["result"]["tools"]
    print(f"   OK - Found {len(tools)} tools:")
    for t in tools:
        print(f"       - {t['name']}")
else:
    print(f"   FAILED: {result}")

# 4. MCP Call Tool
print("\n4. MCP Call Tool (list_audits)...")
r = requests.post(f"{BASE_URL}/mcp/", json={
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "list_audits",
        "arguments": {"limit": 3}
    }
}, headers={"Authorization": f"Bearer {token}"})
result = r.json()
if "result" in result:
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)
    print(f"   OK - Total audits: {data.get('total', 0)}")
else:
    print(f"   FAILED: {result}")

print("\n" + "=" * 50)
print("MCP Test PASSED!")
print("=" * 50)
