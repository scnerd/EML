from eml.modules import Command

class Main(Command):
   def num_outputs(self):
      return 0

   def __call__(self):
      for input_stream in self.inputs:
         for val in input_stream:
            print(val, end=" ")
         print('\n')
