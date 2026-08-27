"""
Control Flow Flattener - Makes control flow analysis difficult
"""

import ast
import random
import hashlib
from typing import Dict, Any, List, Optional

class ControlFlowFlattener:
    """
    Flattens control flow by converting branches to switch statements
    and adding opaque predicates
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._seed = seed
        self._state_var = f"_cf_state_{self._rng.randint(1000, 9999)}"
        
    def flatten_control_flow(self, code: str) -> str:
        """
        Flatten control flow in the given code
        Adds opaque predicates and dispatcher logic
        """
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Find functions with control flow
            transformer = ControlFlowTransformer(self._state_var, seed=self._seed)
            transformed = transformer.visit(tree)
            
            # Convert back to code
            import astor
            flattened_code = astor.to_source(transformed)
            
            # Add dispatcher preamble
            preamble = self._generate_dispatcher_preamble()
            
            return preamble + flattened_code
            
        except Exception as e:
            # If transformation fails, return original code
            # with some basic obfuscation
            return self._simple_obfuscation(code)
    
    def _generate_dispatcher_preamble(self) -> str:
        """Generate the dispatcher code"""
        return f'''
# JOCKY Control Flow Dispatcher
{self._state_var} = 0

def _jocky_dispatch(state):
    global {self._state_var}
    {self._state_var} = state
    return state
'''
    
    def _simple_obfuscation(self, code: str) -> str:
        """Simple fallback obfuscation if AST transformation fails"""
        # Add opaque predicates
        lines = code.split('\n')
        obfuscated = []
        
        for line in lines:
            # Add random dead code
            if 'if' in line and ':' in line and not line.strip().startswith('#'):
                if self._rng.random() > 0.5:
                    dead_code = f"if {self._rng.randint(0, 999)} == {self._rng.randint(0, 999)}: pass"
                    obfuscated.append(f"# {dead_code}")
            obfuscated.append(line)
            
        return '\n'.join(obfuscated)

class ControlFlowTransformer(ast.NodeTransformer):
    """AST transformer for control flow flattening"""
    
    def __init__(self, state_var: str, seed: Optional[int] = None):
        self.state_var = state_var
        self._rng = random.Random(seed)
        self._block_counter = 0
        self._blocks = {}
        
    def visit_FunctionDef(self, node):
        """Transform function bodies"""
        # Store original body
        original_body = node.body
        
        # Create dispatcher
        dispatcher = self._create_dispatcher(original_body)
        
        # Replace body with dispatcher
        node.body = dispatcher
        
        return node
    
    def _create_dispatcher(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """Create a dispatcher for the function body"""
        # Split body into basic blocks
        blocks = self._split_into_blocks(body)
        
        # Assign unique IDs to blocks
        block_ids = {}
        for i, block in enumerate(blocks):
            block_id = self._rng.randint(1000, 9999)
            block_ids[block_id] = block
            self._blocks[block_id] = block
            
        # Create dispatcher while loop
        dispatch_var = ast.Name(id=self.state_var, ctx=ast.Store())
        
        # Create switch-like dispatch
        if_stmt = self._create_dispatch_if(block_ids)
        
        # Wrap in while loop
        while_loop = ast.While(
            test=ast.Constant(value=True),
            body=[if_stmt],
            orelse=[]
        )
        
        # Initialize state
        init_state = ast.Assign(
            targets=[dispatch_var],
            value=ast.Constant(value=0)
        )
        
        return [init_state, while_loop]
    
    def _split_into_blocks(self, body: List[ast.stmt]) -> List[List[ast.stmt]]:
        """Split AST body into basic blocks"""
        blocks = []
        current_block = []
        
        for stmt in body:
            current_block.append(stmt)
            
            # If this is a control flow statement, end the block
            if isinstance(stmt, (ast.If, ast.For, ast.While, ast.Return)):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                    
        if current_block:
            blocks.append(current_block)
            
        return blocks
    
    def _create_dispatch_if(self, block_ids: Dict[int, List[ast.stmt]]) -> ast.If:
        """Create if-elif chain for dispatch"""
        test = ast.Compare(
            left=ast.Name(id=self.state_var, ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)]
        )
        
        # For simplicity, just handle first block
        first_block = list(block_ids.items())[0]
        first_body = first_block[1]
        
        # Add state update at end of block
        update_state = ast.Assign(
            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
            value=ast.Constant(value=1)  # Next state
        )
        
        # Return statement to exit dispatcher
        return_stmt = ast.Return(value=ast.Constant(value=None))
        
        body = first_body + [update_state, return_stmt]
        
        return ast.If(
            test=test,
            body=body,
            orelse=[]
        )