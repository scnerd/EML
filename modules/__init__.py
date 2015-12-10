import importlib
# http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
import os, sys, inspect
# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
   sys.path.insert(0, cmd_folder)
   
import multiprocessing
from threading import Thread

class EOQ():
   pass

class Command(object):
   END_OF_QUEUE = EOQ()
   
   def __init__(self, input_width, *flags, **kwargs):
      self.name = type(self).__module__
      self._num_outputs = None
      self.flags = flags
      self.kwargs = kwargs
      self.check_num_inputs(input_width)
      self.num_inputs = input_width
      self.queues = [multiprocessing.Queue() for i in range(self.num_outputs())]
      
   def check_num_inputs(self, num_inputs):
      '''Can be overridden in individual commands to require certain numbers of input streams'''
      pass
      
   def num_outputs(self):
      '''Returns the number of output streams this command provides (can be a function of num_inputs)'''
      if self._num_outputs is not None:
         return self._num_outputs
      raise RuntimeError("Command.num_outputs must be overridden or _num_outputs must be set")
      
   def launch_process(self, inputs):
      '''Call to launch this command as an individual process'''
      self._input_queues = inputs
      if len(inputs) is not self.num_inputs:
         raise RuntimeError("Command '%s' only received %d inputs instead of the expected %d" % 
         (self.name, inputs, self.num_inputs))
      self._proc = multiprocessing.Process(target=self.call_wrapper)
      self._proc.start()
      
   def join(self):
      '''Block until this command is done processing'''
      self._proc.join()
      
   def call_wrapper(self):
      self.inputs = [queue_to_iter(q, sentinel=Command.END_OF_QUEUE) for q in self._input_queues]
      print("Entering call for '%s'" % self.name)
      self()
      print("Exiting call for '%s'" % self.name)
      for q in self.queues:
         q.put(Command.END_OF_QUEUE)
       
   def outputs(self):
      return self.queues
      
   def __call__(self):
      '''Provides the actual functionality of this command. Of primary importance are:
      self.inputs: a list of input iterables that carry the data of the input streams;
      self.queues: a list of queues (use q.put) to carry output data from this command;
      self.args/kwargs: the arguments provided to this command'''
      raise RuntimeError("Individual commands must implement their own __call__ method: '%s'" % self.name)
      
mods = {}
def load_command_module(command_name):
   if command_name not in mods:
      mods[command_name] = importlib.import_module(".%s" % command_name, 'modules')
   return mods[command_name].Main

def queue_to_iter(queue, sentinel=Command.END_OF_QUEUE):
   #return iter(queue.get, sentinel)
   while True:
      val = queue.get()
      if not isinstance(val, EOQ):
         yield val
      else:
         break

def pusher(iterable, queue, sentinel):
   for i in iterable:
      queue.put(i)
   queue.put(sentinel)

def iter_to_queue(iterable, sentinel=Command.END_OF_QUEUE):
   q = multiprocessing.Queue()
   t = Thread(target=pusher, args=(iterable, q, sentinel))
   t.daemon = True
   t.start()
   return q
