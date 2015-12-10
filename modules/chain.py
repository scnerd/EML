from eml.modules import Command

class Main(Command):
   def num_outputs(self):
      return 1
     
   def __call__(self):
      for input in self.inputs:
         for val in input:
            self.outputs[0].put(val)
