import random
import hashlib
import os
import time
from typing import Dict, Any, Optional
from .variable_encryption import VariableEncryptor
from .control_flow_flattener import ControlFlowFlattener
from .import_table_obfuscator import ImportTableObfuscator
from .junk_code_injector import JunkCodeInjector
from .hash_generator import HashGenerator
from .advanced_flow_obfuscator import AdvancedFlowObfuscator
from .string_obfuscator import StringObfuscator
from .anti_analysis import AntiAnalysis
from .dynamic_api_resolver import DynamicAPIResolver

class PolymorphicEngineEnhanced:
    """
    Enhanced polymorphic engine with advanced obfuscation techniques
    """
    
    def __init__(self, enable_advanced=True):
        self.enable_advanced = enable_advanced
        
        # Core modules
        self.variable_encryptor = VariableEncryptor()
        self.control_flow_flattener = ControlFlowFlattener()
        self.import_obfuscator = ImportTableObfuscator()
        self.junk_injector = JunkCodeInjector()
        self.hash_generator = HashGenerator()
        
        # Advanced modules
        if enable_advanced:
            self.advanced_flow = AdvancedFlowObfuscator()
            self.string_obfuscator = StringObfuscator()
            self.anti_analysis = AntiAnalysis()
            self.api_resolver = DynamicAPIResolver()
        
        # Randomize seed for each run
        self.seed = int(time.time() * 1000) % 1000000
        random.seed(self.seed)
        
        self.obfuscation_count = 0
    
    def obfuscate_script(self, script_content: str, output_format: str = "python", 
                         advanced: bool = True) -> Dict[str, Any]:
        """
        Main obfuscation pipeline with enhanced techniques
        """
        self.obfuscation_count += 1
        print(f"\n[Obfuscation #{self.obfuscation_count}] Processing...")
        
        # Step 1: Anti-analysis check
        if self.enable_advanced and advanced:
            print("[1/7] Running anti-analysis checks...")
            analysis_results = self.anti_analysis.detect_analysis()
            if any(analysis_results.values()):
                print("[!] Analysis environment detected - applying evasion...")
        
        # Step 2: Advanced string obfuscation
        if self.enable_advanced and advanced:
            print("[2/7] Obfuscating strings...")
            script_content = self.string_obfuscator.obfuscate_strings(script_content)
        
        # Step 3: Advanced flow obfuscation
        if self.enable_advanced and advanced:
            print("[3/7] Obfuscating control flow...")
            script_content = self.advanced_flow.obfuscate(script_content)
        
        # Step 4: Variable encryption
        print("[4/7] Encrypting variables...")
        script_content = self.variable_encryptor.encrypt_strings(script_content)
        
        # Step 5: Control flow flattening
        print("[5/7] Flattening control flow...")
        script_content = self.control_flow_flattener.flatten(script_content)
        
        # Step 6: Import obfuscation
        print("[6/7] Obfuscating import tables...")
        obfuscated_imports, import_table = self.import_obfuscator.obfuscate(script_content)
        
        # Step 7: Junk code injection
        print("[7/7] Injecting junk code...")
        final_script = self.junk_injector.inject(obfuscated_imports)
        
        # Generate unique hash
        script_hash = self.hash_generator.generate(final_script, self.seed)
        
        return {
            'obfuscated_code': final_script,
            'hash': script_hash,
            'seed': self.seed,
            'entry_point': self._randomize_entry_point(),
            'import_table': import_table,
            'original_size': len(script_content),
            'obfuscated_size': len(final_script),
            'obfuscation_ratio': len(final_script) / len(script_content),
            'obfuscation_count': self.obfuscation_count,
            'analysis_detected': self.anti_analysis.detect_analysis() if self.enable_advanced else None
        }
    
    def _randomize_entry_point(self) -> str:
        """Create random entry point name"""
        prefixes = ['_', '__', 'func_', 'entry_', 'start_', 'main_', 'run_']
        suffixes = [str(random.randint(100, 999)) for _ in range(3)]
        return random.choice(prefixes) + ''.join(random.choices(suffixes, k=2))