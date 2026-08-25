import random
import ast
import astor

class ControlFlowFlattener:
    """Flatten control flow to confuse static analysis"""
    
    def flatten(self, code: str) -> str:
        """Convert if/else and loops into switch-based dispatch"""
        try:
            tree = ast.parse(code)
            transformer = ControlFlowTransformer()
            transformed = transformer.visit(tree)
            return astor.to_source(transformed)
        except:
            # If parsing fails, return original code with simple obfuscation
            return self._simple_obfuscation(code)
    
    def _simple_obfuscation(self, code: str) -> str:
        """Fallback: simple if/else reordering"""
        lines = code.split('\n')
        obfuscated = []
        
        for line in lines:
            if 'if ' in line and ':' in line:
                # Add random condition to if statements
                if random.random() > 0.5:
                    line = line.replace('if ', 'if (1 == 1) and ')
            obfuscated.append(line)
        
        return '\n'.join(obfuscated)

class ControlFlowTransformer(ast.NodeTransformer):
    """AST transformer for control flow flattening"""
    
    def visit_If(self, node):
        # Convert if to while with break for flattening
        if random.random() > 0.7:  # Only flatten some ifs
            return self._flatten_if(node)
        return node
    
    def _flatten_if(self, node):
        # Create a dispatch table for branches
        # This is simplified - real implementation would be more complex
        return node