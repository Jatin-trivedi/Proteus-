#!/usr/bin/env python3
"""
Enhanced Polymorphic Engine Demo
Shows advanced obfuscation techniques
"""

import json
import time
import sys
from src.obfuscator import PolymorphicEngineEnhanced

def compare_obfuscation_levels():
    """Compare basic vs enhanced obfuscation"""
    
    # Sample script
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
    system_info = {
        'hostname': os.getenv('COMPUTERNAME'),
        'username': os.getenv('USERNAME'),
        'path': os.getenv('PATH')
    }
    
    processes = []
    for proc in os.listdir('/proc' if os.name == 'posix' else 'C:/'):
        if proc.isdigit():
            processes.append(proc)
    
    return {'system': system_info, 'processes': processes[:10]}

if __name__ == '__main__':
    result = main()
    print(json.dumps(result))
"""
    
    print("=" * 70)
    print("JOCKY ENHANCED POLYMORPHIC ENGINE DEMO")
    print("=" * 70)
    
    # Test 1: Basic obfuscation
    print("\n[TEST 1] Basic Obfuscation (without advanced features)")
    print("-" * 50)
    
    engine_basic = PolymorphicEngineEnhanced(enable_advanced=False)
    result_basic = engine_basic.obfuscate_script(script, advanced=False)
    
    print(f"  Original Size: {result_basic['original_size']} bytes")
    print(f"  Obfuscated Size: {result_basic['obfuscated_size']} bytes")
    print(f"  Ratio: {result_basic['obfuscation_ratio']:.2f}x")
    print(f"  Hash: {result_basic['hash'][:40]}...")
    print(f"  Import Table: {len(result_basic['import_table'])} items")
    
    # Test 2: Enhanced obfuscation
    print("\n[TEST 2] Enhanced Obfuscation (with advanced features)")
    print("-" * 50)
    
    engine_enhanced = PolymorphicEngineEnhanced(enable_advanced=True)
    result_enhanced = engine_enhanced.obfuscate_script(script, advanced=True)
    
    print(f"  Original Size: {result_enhanced['original_size']} bytes")
    print(f"  Obfuscated Size: {result_enhanced['obfuscated_size']} bytes")
    print(f"  Ratio: {result_enhanced['obfuscation_ratio']:.2f}x")
    print(f"  Hash: {result_enhanced['hash'][:40]}...")
    print(f"  Import Table: {len(result_enhanced['import_table'])} items")
    
    # Test 3: Multiple iterations
    print("\n[TEST 3] Running 5 iterations of enhanced obfuscation")
    print("-" * 50)
    
    hashes = set()
    sizes = []
    
    for i in range(5):
        result = engine_enhanced.obfuscate_script(script, advanced=True)
        hashes.add(result['hash'])
        sizes.append(result['obfuscated_size'])
        print(f"  Iteration {i+1}: {result['hash'][:30]}... ({result['obfuscated_size']} bytes)")
    
    print(f"\n  Unique Hashes: {len(hashes)}/5")
    print(f"  Size Range: {min(sizes)} - {max(sizes)} bytes")
    print(f"  Average Size: {sum(sizes)//len(sizes)} bytes")
    
    # Test 4: Code preview
    print("\n[TEST 4] Enhanced Obfuscated Code Preview")
    print("-" * 50)
    
    preview_lines = result_enhanced['obfuscated_code'].split('\n')[:10]
    print("First 10 lines of obfuscated code:")
    for i, line in enumerate(preview_lines, 1):
        if len(line) > 60:
            print(f"  {i:2d}. {line[:60]}...")
        else:
            print(f"  {i:2d}. {line}")
    
    print("\n" + "=" * 70)
    print("✅ ENHANCED POLYMORPHIC ENGINE DEMO COMPLETE")
    print("=" * 70)
    
    # Summary
    print("\n📊 COMPARISON SUMMARY:")
    print(f"  Basic Obfuscation Ratio: {result_basic['obfuscation_ratio']:.2f}x")
    print(f"  Enhanced Obfuscation Ratio: {result_enhanced['obfuscation_ratio']:.2f}x")
    print(f"  Improvement: {(result_enhanced['obfuscation_ratio']/result_basic['obfuscation_ratio'] - 1)*100:.1f}%")
    
    return result_enhanced

if __name__ == '__main__':
    compare_obfuscation_levels()
