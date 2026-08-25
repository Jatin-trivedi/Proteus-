"""
Integration bridge between JOCKY Compiler and Polymorphic Engine
This module connects Member B's compiler output with Member C's obfuscation
"""

import os
import json
import tempfile
import subprocess
import hashlib
from typing import Dict, Any, Optional, Tuple
from .obfuscator import PolymorphicEngineEnhanced

class JOCKYCompilerIntegration:
    """
    Bridges the JOCKY compiler with the polymorphic engine
    Handles compilation, obfuscation, and output generation
    """
    
    def __init__(self, compiler_path: Optional[str] = None):
        """
        Initialize the integration bridge
        
        Args:
            compiler_path: Path to the JOCKY compiler executable or script
        """
        self.compiler_path = compiler_path or "./jockey-compiler/jockeyc"
        self.polymorphic_engine = PolymorphicEngineEnhanced(enable_advanced=True)
        self.compilation_cache = {}
        
    def compile_and_obfuscate(self, 
                              source_code: str,
                              source_file: Optional[str] = None,
                              output_format: str = "binary",
                              obfuscation_level: str = "high") -> Dict[str, Any]:
        """
        Full pipeline: Compile JOCKY source → Obfuscate → Return binary
        
        Args:
            source_code: JOCKY source code
            source_file: Path to .jky file (optional)
            output_format: "binary", "llvm", "python", "asm"
            obfuscation_level: "low", "medium", "high"
        
        Returns:
            Dict with compilation and obfuscation results
        """
        
        print("=" * 60)
        print("JOCKY COMPILER + POLYMORPHIC ENGINE INTEGRATION")
        print("=" * 60)
        
        # Step 1: Compile JOCKY source
        print("\n[Step 1] Compiling JOCKY source code...")
        compilation_result = self._compile_jockey_source(source_code, source_file)
        
        if not compilation_result['success']:
            return {
                'success': False,
                'error': compilation_result.get('error', 'Compilation failed'),
                'compilation': compilation_result
            }
        
        print(f"  ✅ Compilation successful")
        print(f"  Output format: {compilation_result['output_format']}")
        print(f"  Output size: {len(compilation_result['output'])} bytes")
        
        # Step 2: Obfuscate the compiled output
        print("\n[Step 2] Applying polymorphic obfuscation...")
        
        # Determine obfuscation settings based on level
        advanced = obfuscation_level in ["high", "medium"]
        enable_advanced = obfuscation_level == "high"
        
        # Obfuscate the compiled code
        obfuscation_result = self.polymorphic_engine.obfuscate_script(
            compilation_result['output'],
            advanced=enable_advanced
        )
        
        print(f"  ✅ Obfuscation complete")
        print(f"  Obfuscation ratio: {obfuscation_result['obfuscation_ratio']:.2f}x")
        print(f"  Unique hash: {obfuscation_result['hash'][:40]}...")
        
        # Step 3: Generate final output
        print("\n[Step 3] Generating final output...")
        
        final_output = self._generate_final_output(
            compilation_result,
            obfuscation_result,
            output_format
        )
        
        print(f"  ✅ Final output generated")
        
        return {
            'success': True,
            'compilation': compilation_result,
            'obfuscation': obfuscation_result,
            'final_output': final_output,
            'hash': obfuscation_result['hash'],
            'metadata': {
                'compiler_version': '1.0',
                'obfuscation_level': obfuscation_level,
                'timestamp': os.times().elapsed,
                'original_size': len(source_code),
                'final_size': len(final_output['binary']),
                'obfuscation_ratio': obfuscation_result['obfuscation_ratio']
            }
        }
    
    def _compile_jockey_source(self, source_code: str, source_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Internal method to compile JOCKY source code
        Handles both file-based and in-memory compilation
        """
        
        # If source_file is provided, read it
        if source_file and os.path.exists(source_file):
            with open(source_file, 'r') as f:
                source_code = f.read()
        
        # Check if compiler exists
        if not os.path.exists(self.compiler_path):
            # Fallback: Use a simple Python-based "compiler" for demo
            return self._fallback_compile(source_code)
        
        try:
            # Use the actual JOCKY compiler
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jky', delete=False) as f:
                f.write(source_code)
                temp_source = f.name
            
            # Run the compiler
            result = subprocess.run(
                [self.compiler_path, temp_source, '--output-format', 'python'],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_source)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr,
                    'output': ''
                }
            
            return {
                'success': True,
                'output': result.stdout,
                'output_format': 'python',
                'compiler_output': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def _fallback_compile(self, source_code: str) -> Dict[str, Any]:
        """
        Fallback compilation when JOCKY compiler is not available
        Converts JOCKY-like syntax to Python
        """
        
        print("[!] Using fallback compiler (JOCKY compiler not found)")
        
        # Simple JOCKY to Python converter for demo
        python_code = self._convert_jockey_to_python(source_code)
        
        return {
            'success': True,
            'output': python_code,
            'output_format': 'python',
            'compiler_output': 'Using fallback compiler (demo mode)'
        }
    
    def _convert_jockey_to_python(self, jockey_code: str) -> str:
        """
        Basic JOCKY to Python conversion for demo purposes
        This is a simplified version - your actual compiler will be more sophisticated
        """
        
        lines = jockey_code.split('\n')
        python_lines = []
        
        for line in lines:
            # Remove JOCKY-specific syntax
            line = line.strip()
            
            # JOCKY function definition -> Python function
            if line.startswith('func '):
                line = line.replace('func ', 'def ')
                if '->' in line:
                    line = line.split('->')[0] + ':'
            
            # JOCKY variable declaration -> Python
            if 'var ' in line and ':' in line:
                line = line.replace('var ', '')
                parts = line.split(':')
                if len(parts) == 2:
                    line = f"{parts[0]} = {parts[1].strip()}"
            
            # JOCKY print -> Python print
            if line.startswith('print '):
                line = line.replace('print ', 'print(') + ')'
            
            # JOCKY if statement -> Python if
            if line.startswith('if '):
                if ':' not in line:
                    line = line + ':'
            
            # JOCKY loop -> Python for
            if line.startswith('for '):
                if ':' not in line:
                    line = line + ':'
            
            python_lines.append(line)
        
        # Add imports and main guard
        header = """
# Auto-generated Python code from JOCKY source
import os
import sys
import json

"""
        
        footer = """
if __name__ == '__main__':
    result = main() if 'main' in dir() else None
    if result:
        print(json.dumps(result))
"""
        
        return header + '\n'.join(python_lines) + footer
    
    def _generate_final_output(self, 
                              compilation: Dict,
                              obfuscation: Dict,
                              output_format: str) -> Dict[str, Any]:
        """
        Generate final output in requested format
        """
        
        output = {
            'binary': obfuscation['obfuscated_code'],
            'hash': obfuscation['hash'],
            'metadata': {
                'compilation_format': compilation['output_format'],
                'obfuscation_seed': obfuscation['seed'],
                'entry_point': obfuscation['entry_point']
            }
        }
        
        # Generate different output formats
        if output_format == "binary":
            output['binary'] = obfuscation['obfuscated_code']
            output['format'] = 'python'
            
        elif output_format == "llvm":
            output['binary'] = f"; LLVM IR generated from JOCKY\n{obfuscation['obfuscated_code']}"
            output['format'] = 'llvm'
            
        elif output_format == "asm":
            output['binary'] = f"; Assembly generated from JOCKY\n; Obfuscated with seed: {obfuscation['seed']}\n{obfuscation['obfuscated_code']}"
            output['format'] = 'asm'
            
        else:
            output['binary'] = obfuscation['obfuscated_code']
            output['format'] = 'python'
        
        return output

    def compile_file(self, jockey_file: str, output_dir: str = "./output") -> Dict[str, Any]:
        """
        Compile a JOCKY file and generate obfuscated output
        """
        
        # Read the JOCKY source file
        with open(jockey_file, 'r') as f:
            source_code = f.read()
        
        # Compile and obfuscate
        result = self.compile_and_obfuscate(source_code, source_file=jockey_file)
        
        if not result['success']:
            return result
        
        # Save output files
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(jockey_file).replace('.jky', '')
        
        # Save obfuscated code
        output_file = os.path.join(output_dir, f"{base_name}_obfuscated.py")
        with open(output_file, 'w') as f:
            f.write(result['final_output']['binary'])
        
        # Save metadata
        metadata_file = os.path.join(output_dir, f"{base_name}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(result['metadata'], f, indent=2)
        
        result['output_files'] = {
            'obfuscated_code': output_file,
            'metadata': metadata_file
        }
        
        print(f"\n✅ Output saved to: {output_dir}/")
        print(f"  - Obfuscated code: {base_name}_obfuscated.py")
        print(f"  - Metadata: {base_name}_metadata.json")
        
        return result

# Helper function for quick integration
def quick_compile_jockey(source_code: str, obfuscation_level: str = "high") -> Dict[str, Any]:
    """
    Quick function to compile JOCKY source code with obfuscation
    """
    integration = JOCKYCompilerIntegration()
    return integration.compile_and_obfuscate(
        source_code,
        obfuscation_level=obfuscation_level
    )