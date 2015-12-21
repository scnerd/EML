import modules
import eml_ast
from threading import Thread
from multiprocessing import Queue
from tempfile import NamedTemporaryFile
import pickle
import itertools
# modified from http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
import os, sys, inspect
# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(
        os.path.split(os.path.split(os.path.abspath(inspect.getfile(inspect.currentframe())))[0])[0])
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
from eml.modules import queue_to_iter, iter_to_queue

node_ids = 1
class NodeDef(Thread):
   def __init__(self, parent_graph, input_width):
      global node_ids
      super().__init__()
      self.daemon = True
      self.id = node_ids
      node_ids += 1
      self.parent = parent_graph
      self.in_width = input_width
      self.out_width = None
      self._launch_children = []
      self.started = False
      
   def finalize(self, inputs):
      raise RuntimeError("finalize must be implemented for '%s'" % type(self).__name__)
      
   def launch(self):
      if not self.started:
         self.started = True
         self.start()
      
   def get_outputs(self):
      raise RuntimeError("get_outputs must be implemented for '%s'" % type(self).__name__)
      
   def run(self):
      pass
      
   def pydot(self):
      return self._pydot()
      
   def _pydot(self):
      return "%s %d [%d -> %d]" % (repr(self), self.id, self.in_width, self.out_width)
      
   def join(self):
      super().join()

class ExeGraphDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      self.named_caches = {}
      self.lines = [construct(line, self, 0, self.named_caches) for line in definition.lines]
      self.out_width = 0
      self._launch_children = self.lines
      
   def finalize(self, inputs):
      for line in self.lines:
         line.finalize([])
      
   def launch(self):
      for child in self.lines:
         child.launch()
      
   def pydot(self):
      return ("\n%s\n" % ('-' * 80)).join(line.pydot() for line in self.lines)
      
   def join(self):
      for line in self.lines:
         line.join()
      
class ExeCommandDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      command = modules.load_command_module(definition.command)
      self.executor = command(input_width, *definition.flags, **definition.args)
      self.out_width = self.executor.num_outputs()
      
   def finalize(self, inputs):
      self.inputs = inputs
      
   def get_output(self):
      return self.executor.outputs()
      
   def run(self):
      self.executor.launch_process(self.inputs)
      
   def __repr__(self):
      return "<%s object: cmd='%s'>" % (type(self).__name__, type(self.executor).__module__)
      
   def join(self):
      self.executor.join()

class ExeCacheDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      self.out_width = input_width if input_width is not None else 1
      self.name = definition.name
      named_caches[self.name] = self
      self.num_output_uses = 0
      
   def use_again(self):
      self.num_output_uses += 1
      
   def __repr__(self):
      return "<%s object: name='%s'>" % (type(self).__name__, self.name)
      
   def flatten(self):
      yield self

class ExeMemCacheDef(ExeCacheDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width, named_caches, definition)
      if input_width == 0:
         raise SyntaxError("Cannot use a memory cache before declaring data into it")
         
   def finalize(self, inputs):
      if len(inputs) == self.out_width:
         if hasattr(self, 'outputs'):
            raise RuntimeError("Tried to finalize '%s' twice" % self.name)
         inputs = [queue_to_iter(q) for q in inputs]
         output_threads = [[iter_to_queue(i) for i in itertools.tee(iterator, self.num_output_uses)]
                            for iterator in inputs]
         self.outputs = zip(*output_threads)
         self.uses = 0
      elif len(inputs) == 0:
         return
      else:
         raise RuntimeError("Tried to finalize '%s' twice with different widths" % self.name)
      
   def get_output(self):
      try:
         self.uses += 1
         return next(self.outputs)
      except StopIteration:
         raise RuntimeError("Used mem cache '%s' too many times: used %d times, only expected %d uses" %
         (self.name, self.uses, self.num_output_uses))
   
class ExeDiskCacheDef(ExeCacheDef):
   # http://stackoverflow.com/questions/15169101/how-to-create-a-temporary-file-that-can-be-read-by-a-subprocess/15235559#15235559
   def __init__(self, parent_graph, input_width, named_caches, definition):
      import tempfile
      super().__init__(parent_graph, input_width, named_caches, definition)
      if input_width == 0:
         raise SyntaxError("Cannot use a disk cache before declaring data into it")
      #self.file = tempfile.TemporaryFile()
      self.tempfiles = []
      
   def finalize(self, inputs):
      if len(inputs) == self.out_width:
         if hasattr(self, 'threads'):
            raise RuntimeError("Tried to finalize disk cache '%s' twice" % self.name)
         self.tempfiles = [NamedTemporaryFile('wb', delete=False) for i in inputs]
         def writer(idx, stream):
            with self.tempfiles[idx] as tmp:
               for val in queue_to_iter(stream):
                  pickle.dump(val, tmp)
         self.threads = [Thread(target=writer, args=(i, inputs[i])) for i in range(len(inputs))]
         for t in self.threads:
            t.daemon = True
            t.start()
      elif len(inputs) == 0:
         return
      else:
         raise RuntimeError("Tried to finalize disk cache '%s' twice with different widths" % self.name)
      
   def get_output(self):
      def read_stream(file):
         with open(file.name, 'rb') as reader:
            try:
               while True:
                  yield pickle.load(reader)
            except EOFError:
               pass
      return [iter_to_queue(read_stream(tmp)) for tmp in self.tempfiles] # iterator_to_queue handles threading
            
   def __del__(self):
      for temp in self.tempfiles:
         os.remove(temp.name)
      
class ExeTupleCacheDef(ExeCacheDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width, named_caches, definition)
      self.inners = [construct(inner, parent_graph, None, named_caches) for inner in definition.inner]
      self.inners = list(self.flatten())
      self.name = ", ".join(inner.name for inner in self.inners)
      actual_width = sum(inner.out_width for inner in self.inners)
      if input_width is not None and input_width != 0 and input_width != actual_width:
         raise SyntaxError('Tuple must have a name for each input value (unless used as a source): ' + 
                           'Cannot map %d (from source) to %d (names): %s' % 
                           (input_width, actual_width, self.name))
      self.out_width = actual_width
      self._launch_children = self.inners
      
   def finalize(self, inputs):
      if len(inputs) == self.out_width:
         cur = 0
         for inner in self.inners:
            sz = inner.out_width
            inner.finalize(inputs[cur:cur+sz])
            cur += sz
      elif len(inputs) == 0:
         pass
         
   def get_output(self):
      return [output for inner in self.inners for output in inner.get_output()]
      
   def launch(self):
      for inner in self.inners:
         inner.launch()
      super().launch()
      
   def flatten(self):
      yield from (sub for inner in self.inners for sub in inner.flatten())
      
   def join(self):
      for inner in self.inners:
         inner.join()
   
class ExePipeDef(NodeDef):
   def __init__(self, parent_graph, input_width, named_caches, definition):
      super().__init__(parent_graph, input_width)
      self.src = construct(definition.src, parent_graph, input_width, named_caches)
      self.carry_width = self.src.out_width
      self.dst = construct(definition.dst, parent_graph, self.carry_width, named_caches)
      self.out_width = self.dst.out_width
      self._launch_children = [self.src, self.dst]
      
   def finalize(self, inputs):
      self.src.finalize(inputs)
      self.dst.finalize(self.src.get_output())
      
   def get_output(self):
      return self.dst.get_output()
      
   def launch(self):
      self.src.launch()
      self.dst.launch()
      super().start()
      
   def pydot(self):
      return "%s\n--%d-->\n%s" % (self.src.pydot(), self.carry_width, self.dst.pydot())
      
   def join(self):
      self.src.join()
      self.dst.join()
      
   
cache_type_map = {
eml_ast.MemCacheDef: ExeMemCacheDef,
eml_ast.DiskCacheDef: ExeDiskCacheDef,
eml_ast.TupleCacheDef: ExeTupleCacheDef
}
   
def construct(definition, current_graph=None, input_width=0, named_caches={}):
   if isinstance(definition, eml_ast.BlockDef):
      return ExeGraphDef(current_graph, input_width, named_caches, definition)
   elif isinstance(definition, eml_ast.CommandDef):
      return ExeCommandDef(current_graph, input_width, named_caches, definition)
   elif isinstance(definition, eml_ast.CacheDef):
      def_name = definition.name
      if def_name in named_caches and not \
         isinstance(named_caches[def_name], cache_type_map[type(definition)]):
         raise SyntaxError("Cannot have two caches of different types with the same name '%s'" % def_name)
      elif input_width is not None and input_width > 0 and \
         def_name in named_caches and named_caches[def_name].in_width != input_width:
         raise SyntaxError("Cannot input to the same cache multiple times (consider using chain command)")
      elif def_name in named_caches:
         named_caches[def_name].use_again()
      elif def_name not in named_caches:
         named_caches[def_name] = \
            cache_type_map[type(definition)](current_graph, input_width, named_caches, definition)
      return named_caches[def_name]
   elif isinstance(definition, eml_ast.PipeDef):
      return ExePipeDef(current_graph, input_width, named_caches, definition)
   else:
      raise SyntaxError('Unknown definition encountered: %s' % repr(definition))

