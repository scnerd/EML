import lexer as _lexer
import yaccer as _yaccer
from ply import lex, yacc
import eml_ast
import eml_exe_ast

l = lex.lex(module=_lexer)
y = yacc.yacc(module=_yaccer)
t = open('sample_eml.eml').read()

parsed = y.parse(t, lexer=l)
graph = eml_exe_ast.construct(parsed)
#print(graph.pydot())
graph.finalize([])
graph.launch()
graph.join()
