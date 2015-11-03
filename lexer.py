reserved = {
#'for': 'FOR',
#'end': 'END',
#'in': 'IN',
#'do': 'DO'
}

tokens = [
'ID',
'LIT_STR',
'LIT_NUM',
'ARROW'
] + list(reserved.values())

literals = '-;(),=$!'#+'

#t_ID = r'[a-zA-Z][\w\-]*'
t_LIT_STR = r'"(?:\\"|[^"])*?"'
t_LIT_NUM = r'\d+(\.\d*)?'
t_ARROW = r'->'

def t_ID(t):
   r'[a-zA-Z]\w*'
   t.type = reserved.get(t.value, 'ID')
   return t

def t_newline(t):
   r'\n+'
   t.lexer.lineno += len(t.value)
        
t_ignore  = ' \t'
        
def t_error(t):
   print("Illegal character '%s'" % t.value[0])
