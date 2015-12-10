from eml.modules import Command
import pickle

class EndOfList(object):
   pass
   
class EndOfInputs(object):
   pass

class Main(Command):
   def num_outputs(self):
      return 0

   def __call__(self):
      name = self.kwargs.get('name', 'save')
      name += ".eml.pkl"
      with open(name, 'wb') as file:
         for input in self.inputs:
            for val in input:
               pickle.dump(val, file)
            pickle.dump(EndOfList())
         pickle.dump(EndOfInputs())
