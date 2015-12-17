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
               print("Saving model of type '%s'" % type(val).__name)
               pickle.dump(val, file)
            print("Done saving from input %d" % self.inputs.index(input))
            pickle.dump(EndOfList())
         print("Done saving")
         pickle.dump(EndOfInputs())
