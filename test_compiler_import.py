import sys
sys.path.insert(0, './compiler')

from lexer.tokenizer import Lexer
from parser.parser import Parser

source = 'agent test { let x = 5 return x }'
lexer = Lexer(source)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

print("✅ Compiler imported successfully as a module!")
print(f"   AST has {len(ast.body)} agent(s)")
