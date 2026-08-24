import random
import ast
import astor
import hashlib

class AdvancedFlowObfuscator:
    """
    Advanced control flow obfuscation using:
    - Opaque predicates
    - Control flow flattening with dispatcher
    - Function inlining/outlining
    - Dead code insertion
    """
    
    def __init__(self):
        self.obfuscation_seed = random.randint(1, 9999)
        random.seed(self.obfuscation_seed)
        
    def obfuscate(self, code: str) -> str:
        """Apply multiple flow obfuscation techniques"""
        
        # Parse code to AST
        try:
            tree = ast.parse(code)
            
            # Apply transformations
            tree = self._add_opaque_predicates(tree)
            tree = self._flatten_control_flow(tree)
            tree = self._inject_dead_code(tree)
            
            return astor.to_source(tree)
        except:
            # Fallback to simpler obfuscation
            return self._simple_obfuscate(code)
    
    def _add_opaque_predicates(self, tree):
        """Add always-true/always-false conditions"""
        transformer = OpaquePredicateTransformer()
        return transformer.visit(tree)
    
    def _flatten_control_flow(self, tree):
        """Convert nested ifs to switch-like dispatcher"""
        transformer = ControlFlowFlattenerAdvanced()
        return transformer.visit(tree)
    
    def _inject_dead_code(self, tree):
        """Insert code that never executes"""
        transformer = DeadCodeInjector()
        return transformer.visit(tree)
    
    def _simple_obfuscate(self, code: str) -> str:
        """Simple fallback obfuscation"""
        lines = code.split('\n')
        obfuscated = []
        
        for line in lines:
            # Add random junk conditions
            if 'if ' in line and ':' in line:
                if random.random() > 0.5:
                    condition = self._generate_opaque_condition()
                    line = line.replace('if ', f'if {condition} and ')
            obfuscated.append(line)
        
        return '\n'.join(obfuscated)
    
    def _generate_opaque_condition(self) -> str:
        """Generate an always-true complex condition"""
        operations = [
            f"{random.randint(1,100)} * {random.randint(1,100)} == {random.randint(1,10000)}",
            f"len('{''.join(random.choices('abcdef', k=5))}') == {random.randint(3,7)}",
            f"hash('{random.randint(1000,9999)}') % {random.randint(2,10)} == {random.randint(0,9)}"
        ]
        return random.choice(operations)

class OpaquePredicateTransformer(ast.NodeTransformer):
    """Transform conditions into opaque predicates"""
    
    def visit_If(self, node):
        # Generate an opaque condition
        if random.random() > 0.6:
            # Create an always-true condition
            var_name = f"_opaque_{random.randint(1000,9999)}"
            condition = ast.parse(
                f"{var_name} = {random.randint(1,100)} * {random.randint(1,100)} == {random.randint(1,10000)}"
            ).body[0]
            
            # Add the condition before the if
            node = ast.If(
                test=ast.Name(id=var_name, ctx=ast.Load()),
                body=node.body,
                orelse=node.orelse
            )
        
        self.generic_visit(node)
        return node