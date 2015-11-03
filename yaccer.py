from lexer import tokens
from eml_ast import *

named_caches = {}

def p_empty(p):
   '''empty : '''
   pass

def p_double_dash(p):
   '''double_dash : '-' '-' '''
   
def p_named_cache(p):
   '''single_cache : '$' ID
                   | '!' ID'''
   c_type = MemCacheDef if p[1] == '$' else DiskCacheDef
   c_name = p[2]
   p[0] = c_type(c_name)
   
def p_parred_tuple(p):
   '''parred_tuple : '(' cache_list ')' '''
   p[0] = TupleCacheDef(p[2])
   
def p_tuple_cache(p):
   '''tuple_cache : cache_list'''
   p[0] = TupleCacheDef(p[1])
   
def p_tuple_cache2(p):
   '''tuple_cache : parred_tuple'''
   p[0] = p[1]
   
def p_parred_cache(p):
   '''parred_cache : single_cache
                   | parred_tuple'''
   p[0] = p[1]
   
def p_cache_list_2(p):
   '''cache_list : parred_cache ',' parred_cache'''
   p[0] = [p[1], p[3]]
   
def p_cache_list_more(p):
   '''cache_list : cache_list ',' parred_cache'''
   p[0] = p[1] + [p[3]]
   
def p_cache(p):
   '''cache : single_cache
            | tuple_cache'''
   p[0] = p[1]
   
def p_command(p):
   '''command : ID arg_list'''
   p[0] = CommandDef(p[1], **dict(p[2]))
   
def p_arg_list(p):
   '''arg_list : empty
               | arg_list arg'''
   p[0] = [] if len(p) < 3 else p[1] + [p[2]]
   
def p_arg(p):
   '''arg : flag '=' literal'''
   p[0] = (p[1], p[3])
   
def p_arg_none(p):
   '''arg : flag'''
   p[0] = (p[1], None)
   
def p_flag(p):
   '''flag : '-' ID
           | double_dash ID'''
   p[0] = p[2]
              
def p_literal(p):
   '''literal : LIT_STR
              | LIT_NUM'''
   p[0] = p[1]
   
def p_block(p):
   '''block : lines'''
   p[0] = BlockDef(p[1])
   
def p_lines(p):
   '''lines : empty
            | lines line '''
#            | lines subblock'''
   p[0] = [] if len(p) == 2 else p[1] + [p[2]]
   
def p_line(p):
   '''line : forward ';' '''
#           | append ';' '''
   p[0] = p[1]
   
def p_forward(p):
   '''forward : source ARROW dest'''
   p[0] = PipeDef(p[1], p[3])
   
def p_source(p):
   '''source : forward
             | cache
             | command'''
   p[0] = p[1]
   
def p_dest(p):
   '''dest : cache
           | command'''
   if hasattr(p[1], 'make_dest'):
      p[1].make_dest()
   p[0] = p[1]

start = 'block'
   
#def p_subblock(p):
#   '''subblock : forloop'''
#   p[0] = p[1]
#   
#def p_forloop(p):
#   '''forloop : FOR cache IN cache DO block END'''
#   p[0] =
   
def p_error(p):
   print("Syntax error! %s" % str(p))
