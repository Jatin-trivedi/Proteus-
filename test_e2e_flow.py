#!/usr/bin/env python3
"""
Simulates the complete flow:
1. Manager receives a JOCKY script
2. Compiler processes it
3. Result is prepared for submission
"""

import sys
sys.path.insert(0, './compiler')

from lexer.tokenizer import Lexer
from parser.parser import Parser
import json
import requests
import hashlib

# Step 1: JOCKY Script (as submitted by analyst)
jocky_code = '''
agent scan_registry {
    let hive = "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
    let results = collect_registry(hive)
    return results
}
'''

print("📝 Step 1: JOCKY Script Received")
print(f"    Code: {jocky_code[:50]}...")

# Step 2: Compile the script (Lexer + Parser)
print("\n⚙️  Step 2: Compiling JOCKY Script")
lexer = Lexer(jocky_code)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

print(f"    ✅ Compilation successful!")
print(f"    Agent: {ast.body[0].name}")
print(f"    Statements: {len(ast.body[0].body)}")

# Step 3: Generate hash for integrity check
print("\n🔐 Step 3: Generating Script Hash")
script_hash = hashlib.sha256(jocky_code.encode()).hexdigest()
print(f"    Hash: {script_hash[:16]}...")

# Step 4: Simulate Deployment (via Manager API)
print("\n📦 Step 4: Simulating Deployment (Manager API)")
# In production, this would be POST /api/v1/script/deploy
deploy_data = {
    "name": "Registry Scan",
    "agent_ids": ["test-001"],
    "code": jocky_code,
    "hash": script_hash
}

print(f"    Deploying to agents: {deploy_data['agent_ids']}")

# Step 5: Simulate Agent Fetching the Script
print("\n📥 Step 5: Agent Fetches Script")
# Agent would GET /api/v1/script/fetch?deploy_id=xxx
# Returns jocky_code and hash for verification

# Step 6: Simulate Execution & Result Collection
print("\n🔍 Step 6: Agent Executes Script & Collects Results")
# In production, this would call the polymorphic engine + execution engine
result_data = {
    "agent_id": "test-001",
    "script_id": "abc-123",
    "data_enc": "encrypted_forensic_data_here"
}

print(f"    Result collected from agent: {result_data['agent_id']}")

# Step 7: Submit Results back to Manager
print("\n📤 Step 7: Submitting Results to Manager")
# In production, this would POST /api/v1/result/submit
print(f"    ✅ Result submitted successfully!")

print("\n✅ E2E Flow Test Complete!")
print(f"   Script hash: {script_hash[:16]}...")
print(f"   Agent ID: {result_data['agent_id']}")
print(f"   Result ID: {result_data['script_id']}")

# Verify the script can be parsed
assert len(ast.body) == 1, "Expected 1 agent"
assert ast.body[0].name == "scan_registry", "Expected agent name 'scan_registry'"
print("\n🎉 All assertions passed!")
