import modules
import eml_ast

class NodeDef(object):
   def __init__(self, parent_graph, input_width):
      self.parent = parent_graph
      self.in_width = input_width
      self.out_width = None

class ExeGraphDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      self.named_caches = {}
      self.lines = [construct(line, self, 0, self.named_caches) for line in definition.lines]
      self.out_width = 0
      
class ExeCommandDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      command = modules.load_command_module(definition.command)
      self.executor = command(input_width, *definition.flags, **definition.args)
      self.out_width = self.executor.num_outputs()

class ExeCacheDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      self.out_width = input_width
      self.name = definition.name
      named_caches[self.name] = self

class ExeMemCacheDef(ExeCacheDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width, named_caches, definition)
         
class ExeDiskCacheDef(ExeCacheDef):
   # http://stackoverflow.com/questions/15169101/how-to-create-a-temporary-file-that-can-be-read-by-a-subprocess/15235559#15235559
   def __init__(self, parent_graph, input_width, named_caches, definition):
      import tempfile
      super().__init__(parent_graph, input_width, named_caches, definition)
      self.file = tempfile.TemporaryFile()
   
class ExeTupleCacheDef(ExeCacheDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width, named_caches, definition)
   
class ExePipeDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
   
cache_type_map = {
eml_ast.MemCacheDef: ExeMemCacheDef,
eml_ast.DiskCacheDef: ExeDiskCacheDef,
eml_ast.TupleCacheDef: ExeTupleCacheDef
}
   
def construct(definition, current_graph=None, input_width=0, named_caches):
   if isinstance(definition, eml_ast.BlockDef):
      return ExeGraphDef(current_graph, input_width, named_caches, definition)
   elif isinstance(definition, eml_ast.CommandDef):
      return ExeCommandDef(current_graph, input_width, named_caches, definition)
   elif isinstance(definition, eml_ast.CacheDef):
      if definition.name in named_caches:
         if isinstance(named_caches[definition.name], cache_type_map[type(definition)]):
            return named_caches[definition.name]
         else:
            raise RuntimeError("Cannot have two caches of different types with the same name")
      else:
         cache_type_map[type(definition)](current_graph, input_width, named_caches, definition)
   elif isinstance(definition, eml_ast.PipeDef):
      return ExePipeDef(current_graph, input_width, named_caches, definition)
      
