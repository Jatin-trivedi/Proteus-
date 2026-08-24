"""
JOCKY Language Grammar (BNF-like)

program         ::= agent_declaration+
agent_declaration ::= 'agent' identifier '{' statement* '}'
statement       ::= let_statement | return_statement
let_statement   ::= 'let' identifier '=' expression
return_statement ::= 'return' expression
expression      ::= call_expression | binary_operation | literal | identifier
call_expression ::= identifier '(' argument_list? ')'
argument_list   ::= expression (',' expression)*
binary_operation ::= expression operator expression
literal         ::= string_literal | number_literal | boolean_literal
string_literal  ::= '"' .*? '"'
number_literal  ::= [0-9]+ ('.' [0-9]+)?
boolean_literal ::= 'true' | 'false'
identifier      ::= [a-zA-Z_][a-zA-Z0-9_]*
operator        ::= '+' | '-' | '*' | '/' | '==' | '!=' | '<' | '>'
"""