"""
AuditBrain MCP Agent - Ollama + DRF
"""

import requests
import json
import ollama
from pathlib import Path

BASE_URL = "http://localhost:8000"
MODEL = "llama3"

# Prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename):
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# -------------------------------
# MCP CLIENT
# -------------------------------

def authenticate():
    r = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": "admin@auditbrain.com",
        "password": "admin123"
    })
    r.raise_for_status()
    return r.json()["access"]


def mcp_call(token, method, params=None, call_id=1):
    r = requests.post(
        f"{BASE_URL}/mcp/",
        json={
            "jsonrpc": "2.0",
            "id": call_id,
            "method": method,
            "params": params or {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    return r.json()["result"]


# -------------------------------
# BUSINESS LOGIC (NO LLM HERE)
# -------------------------------

def count_by_status(audits, status):
    return sum(1 for a in audits if a["status"] == status)


def summarize_audits(audits):
    return {
        "pending": count_by_status(audits, "pending"),
        "in_progress": count_by_status(audits, "in_progress"),
        "completed": count_by_status(audits, "completed"),
        "total": len(audits)
    }


# -------------------------------
# LLM DECISION LAYER
# -------------------------------

def ask_llm(question):
    system_prompt = load_prompt("intent_classifier.txt")
    response = ollama.chat(
        model=MODEL,
        messages=[{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": question
        }]
    )
    return response["message"]["content"].strip()


def generate_response(question, summary):
    """Use LLM to generate a natural language response based on data."""
    system_prompt = load_prompt("response_generator.txt")
    response = ollama.chat(
        model=MODEL,
        messages=[{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": f"""Question: {question}

Available data:
- Total audits: {summary['total']}
- Pending audits: {summary['pending']}
- In progress audits: {summary['in_progress']}
- Completed audits: {summary['completed']}

Respond naturally to the user's question using this data."""
        }]
    )
    return response["message"]["content"].strip()


# -------------------------------
# MAIN
# -------------------------------

def process_question(token, question):
    """Process a single question."""
    # Always fetch audits first (DRF is source of truth)
    result = mcp_call(token, "tools/call", {
        "name": "list_audits",
        "arguments": {"limit": 100}
    })

    audits = json.loads(result["content"][0]["text"])["audits"]
    summary = summarize_audits(audits)

    # Generate natural language response
    print("\n🤖 Thinking...")
    response = generate_response(question, summary)
    
    print(f"\n� {response}")


def main():
    print("=" * 50)
    print("🤖 AuditBrain MCP Agent")
    print("=" * 50)
    
    token = authenticate()
    print("✅ Authenticated!\n")

    print("Example questions:")
    print("  • How many audits are in progress?")
    print("  • How many pending audits are there?")
    print("  • Show me the last 5 audits")
    print("  • List audits with status completed")
    print("\n💡 Type '0' to exit\n")

    while True:
        try:
            q = input("❓ Ask a question: ").strip()
            
            if q == "0":
                print("\n👋 Goodbye!")
                break
            
            if not q:
                print("⚠️ Please enter a question or '0' to exit\n")
                continue
            
            process_question(token, q)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()

