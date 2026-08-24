#!/usr/bin/env python3
import time
import subprocess
import requests
import statistics

def benchmark_old():
    """Test old manager"""
    start = time.time()
    for i in range(10):
        try:
            requests.post('http://localhost:5000/api/v1/agent/register',
                         json={"agent_id": f"test-{i}", "os": "windows", "ip": "127.0.0.1", "arch": "x64"},
                         timeout=1)
        except:
            pass
    return time.time() - start

def benchmark_new():
    """Test new manager"""
    start = time.time()
    for i in range(10):
        try:
            requests.post('http://localhost:5001/api/v1/agent/register',
                         json={"agent_id": f"test-{i}", "os": "windows", "ip": "127.0.0.1", "arch": "x64"},
                         timeout=1)
        except:
            pass
    return time.time() - start

print("🏁 Performance Comparison")
print("=" * 40)
print(f"Old Manager: {benchmark_old():.3f}s")
print(f"New Manager: {benchmark_new():.3f}s")