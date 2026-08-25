#!/usr/bin/env python3
import requests
import json
import sys

# Add compiler to path
sys.path.insert(0, './compiler')
from lexer.tokenizer import Lexer
from parser.parser import Parser

MANAGER_URL = "http://localhost:5000"

# 1. Register an agent
print("📝 Registering agent...")
register_resp = requests.post(
    f"{MANAGER_URL}/api/v1/agent/register",
    json={
        "agent_id": "compiler-test-001",
        "os": "windows",
        "ip": "127.0.0.1",
        "arch": "x64"
    }
)

if register_resp.status_code == 200:
    print("   ✅ Agent registered successfully")
else:
    print(f"   ❌ Error: {register_resp.text}")
    exit(1)

# 2. Read a JOCKY script
with open('compiler/tests/sample_scripts/hello.jky', 'r') as f:
    jocky_code = f.read()

# 3. Compile the script (verify it's valid)
print("\n🔍 Compiling script...")
lexer = Lexer(jocky_code)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()
print(f"   ✅ Script compiled successfully! Agent: {ast.body[0].name}")

# 4. Deploy the script via Manager API
print("\n📤 Deploying script...")
deploy_resp = requests.post(
    f"{MANAGER_URL}/api/v1/script/deploy",
    json={
        "name": "Hello JOCKY",
        "agent_ids": ["compiler-test-001"],
        "code": jocky_code
    }
)

if deploy_resp.status_code == 200:
    data = deploy_resp.json()
    print(f"   ✅ Script deployed!")
    print(f"   Script ID: {data['script_id']}")
    print(f"   Deploy IDs: {data['deploy_ids']}")
else:
    print(f"   ❌ Error: {deploy_resp.text}")
    exit(1)

print("\n✅ Integration test complete!")
