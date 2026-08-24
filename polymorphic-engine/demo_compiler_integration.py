#!/usr/bin/env python3
"""
Demo: JOCKY Compiler + Polymorphic Engine Integration
Shows the full pipeline from JOCKY source to obfuscated binary
"""

import json
from src.compiler_integration import JOCKYCompilerIntegration

def demo_compiler_integration():
    """Demonstrate the full compilation + obfuscation pipeline"""
    
    # Sample JOCKY source code
    jockey_source = """
# JOCKY Forensics Script
import os
import sys

func collect_registry(path):
    var data = []
    for key in path:
        var result = os.getenv(key)
        if result:
            data.append(result)
    return data

func main():
    var system_info = {
        'hostname': os.getenv('COMPUTERNAME'),
        'username': os.getenv('USERNAME'),
        'path': os.getenv('PATH')
    }
    
    var processes = []
    for proc in os.listdir('/proc' if os.name == 'posix' else 'C:/'):
        if proc.isdigit():
            processes.append(proc)
    
    var result = {
        'system': system_info,
        'processes': processes[:10]
    }
    print json.dumps(result)
    return result

if __name__ == '__main__':
    main()
"""
    
    print("=" * 70)
    print("JOCKY COMPILER + POLYMORPHIC ENGINE INTEGRATION DEMO")
    print("=" * 70)
    
    # Initialize the integration
    integration = JOCKYCompilerIntegration()
    
    # Test 1: Basic compilation with low obfuscation
    print("\n[TEST 1] Compile with LOW obfuscation")
    print("-" * 50)
    
    result_low = integration.compile_and_obfuscate(
        jockey_source,
        obfuscation_level="low"
    )
    
    if result_low['success']:
        print(f"✅ Success! Hash: {result_low['hash'][:40]}...")
        print(f"   Original size: {result_low['metadata']['original_size']} bytes")
        print(f"   Final size: {result_low['metadata']['final_size']} bytes")
        print(f"   Ratio: {result_low['metadata']['obfuscation_ratio']:.2f}x")
    
    # Test 2: Compilation with high obfuscation
    print("\n[TEST 2] Compile with HIGH obfuscation")
    print("-" * 50)
    
    result_high = integration.compile_and_obfuscate(
        jockey_source,
        obfuscation_level="high"
    )
    
    if result_high['success']:
        print(f"✅ Success! Hash: {result_high['hash'][:40]}...")
        print(f"   Original size: {result_high['metadata']['original_size']} bytes")
        print(f"   Final size: {result_high['metadata']['final_size']} bytes")
        print(f"   Ratio: {result_high['metadata']['obfuscation_ratio']:.2f}x")
    
    # Test 3: Different output formats
    print("\n[TEST 3] Different output formats")
    print("-" * 50)
    
    formats = ['python', 'llvm', 'asm']
    for fmt in formats:
        result = integration.compile_and_obfuscate(
            jockey_source,
            output_format=fmt,
            obfuscation_level="medium"
        )
        if result['success']:
            print(f"  ✅ {fmt.upper()}: {len(result['final_output']['binary'])} bytes")
    
    # Test 4: Save to file
    print("\n[TEST 4] Save to file")
    print("-" * 50)
    
    # Create a temporary JOCKY file
    with open('sample.jky', 'w') as f:
        f.write(jockey_source)
    
    result = integration.compile_file('sample.jky', './compiled_output')
    
    if result['success']:
        print(f"✅ Files saved successfully")
        print(f"  📁 {result['output_files']['obfuscated_code']}")
        print(f"  📁 {result['output_files']['metadata']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ INTEGRATION DEMO COMPLETE")
    print("=" * 70)
    
    print("\n📊 COMPARISON:")
    print(f"  Low obfuscation ratio: {result_low['metadata']['obfuscation_ratio']:.2f}x")
    print(f"  High obfuscation ratio: {result_high['metadata']['obfuscation_ratio']:.2f}x")
    print(f"  Improvement: {(result_high['metadata']['obfuscation_ratio'] / result_low['metadata']['obfuscation_ratio'] - 1) * 100:.1f}%")
    
    return result_high

if __name__ == '__main__':
    demo_compiler_integration()