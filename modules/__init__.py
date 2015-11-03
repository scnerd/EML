import importlib
# http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
import os, sys, inspect
# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
   sys.path.insert(0, cmd_folder)

class Command(object):
   def __init__(self, num_inputs, *flags, **args):
      self.num_inputs = num_inputs
      self._num_outputs = None
      
   def num_outputs(self):
      if self._num_outputs is not None:
         return self._num_outputs
      raise RuntimeError("Command.num_outputs must be overridden or _num_outputs must be set")
      
   def launch_process(self):
      pass
      
mods = {}
def load_command_module(command_name):
   if command_name not in mods:
      mods[command_name] = importlib.import_module(".%s" % command_name, 'modules')
   return mods[command_name]
