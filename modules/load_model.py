from eml.modules import Command
import pickle
from eml.modules.save_model import EndOfList, EndOfInputs

class Main(Command):
   def num_outputs(self):
      return int(self.kwargs.get('outputs', '1'))

   def __call__(self):
      name = self.kwargs.get('name', 'save')
      name += ".eml.pkl"
      qs = iter(self.queues)
      cur_q = next(qs)
      with open(name, 'rb') as file:
         val = pickle.load(file)
         if isinstance(val, EndOfList):
            cur_q = next(qs)
         elif isinstance(val, EndOfInputs):
            return
         else:
            cur_q.put(val)
