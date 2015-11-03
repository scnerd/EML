import lexer as _lexer
import yaccer as _yaccer
from ply import lex, yacc
import eml_ast

l = lex.lex(module=_lexer)
y = yacc.yacc(module=_yaccer)
t = open('sample_eml.eml').read()

eml_ast.graph(y.parse(t, lexer=l))
