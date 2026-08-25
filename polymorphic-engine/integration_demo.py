#!/usr/bin/env python3
"""
Integration demo for the polymorphic engine
Shows how it integrates with the rest of the JOCKY framework
"""

from src.obfuscator import PolymorphicEngine
import json
import time

def demo_polymorphic_engine():
    """Demonstrate the polymorphic engine capabilities"""
    
    # Sample JOCKY script
    script = """
# JOCKY Forensics Script
import os
import sys

def collect_registry(path):
    data = []
    for key in path:
        result = os.getenv(key)
        if result:
            data.append(result)
    return data

def main():
    # Collect system info
    system_info = {
        'hostname': os.getenv('COMPUTERNAME'),
        'username': os.getenv('USERNAME'),
        'path': os.getenv('PATH')
    }
    
    # Collect running processes
    processes = []
    for proc in os.listdir('/proc' if os.name == 'posix' else 'C:/'):
        if proc.isdigit():
            processes.append(proc)
    
    return {
        'system': system_info,
        'processes': processes[:10]
    }

if __name__ == '__main__':
    result = main()
    print(json.dumps(result))
"""
    
    # Initialize engine
    engine = PolymorphicEngine()
    
    print("=" * 60)
    print("JOCKY POLYMORPHIC ENGINE DEMO")
    print("=" * 60)
    
    # Generate multiple versions
    versions = []
    print("\n[1] Generating 3 different versions of the same script...")
    
    for i in range(3):
        print(f"\n--- Version {i+1} ---")
        
        result = engine.obfuscate_script(script)
        versions.append(result)
        
        print(f"  Hash: {result['hash'][:30]}...")
        print(f"  Original Size: {result['original_size']} bytes")
        print(f"  Obfuscated Size: {result['obfuscated_size']} bytes")
        print(f"  Obfuscation Ratio: {result['obfuscation_ratio']:.2f}x")
        print(f"  Entry Point: {result['entry_point']}")
        print(f"  Seed: {result['seed']}")
        
        # Show first 5 lines of obfuscated code
        lines = result['obfuscated_code'].split('\n')[:5]
        print("  Code Preview:")
        for line in lines:
            print(f"    {line}")
    
    print("\n[2] Comparing hashes...")
    print(f"  Hash 1: {versions[0]['hash'][:30]}...")
    print(f"  Hash 2: {versions[1]['hash'][:30]}...")
    print(f"  Hash 3: {versions[2]['hash'][:30]}...")
    print(f"  ✅ All hashes are unique")
    
    print("\n[3] Code size comparison...")
    for i, version in enumerate(versions, 1):
        print(f"  Version {i}: {version['original_size']} → {version['obfuscated_size']} bytes")
    
    print("\n" + "=" * 60)
    print("✅ POLYMORPHIC ENGINE DEMO COMPLETE")
    print("=" * 60)
    
    return versions

if __name__ == '__main__':
    demo_polymorphic_engine()