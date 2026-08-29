class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, body):
        self.body = body

class AgentDeclaration(ASTNode):
    def __init__(self, name, body):
        self.name = name
        self.body = body

class FunctionDeclaration(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class StructDeclaration(ASTNode):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class LetStatement(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ReturnStatement(ASTNode):
    def __init__(self, value):
        self.value = value

class PrintStatement(ASTNode):
    def __init__(self, args):
        self.args = args

class IfStatement(ASTNode):
    def __init__(self, cond, then_body, else_body):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class WhileStatement(ASTNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class ForStatement(ASTNode):
    def __init__(self, var, start, end, body):
        self.var = var
        self.start = start
        self.end = end
        self.body = body

# Expressions
class BinaryOperation(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class StringLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class NumberLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class ArrayIndex(ASTNode):
    def __init__(self, array, index):
        self.array = array
        self.index = index

class StructLiteral(ASTNode):
    def __init__(self, fields):
        self.fields = fields

class StructField(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class StructFieldAccess(ASTNode):
    def __init__(self, struct, field_name):
        self.struct = struct
        self.field_name = field_name

class ArrayLiteral(ASTNode):
    def __init__(self, elements):
        self.elements = elements

class CallExpression(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args