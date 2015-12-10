from eml.modules import Command
import numpy

class Main(Command):
   def num_outputs(self):
      return self.num_inputs

   def __call__(self):
      done = [False for i in self.inputs]
      while not all(done):
         for i in range(len(self.inputs)):
            if not done[i]:
               try:
                  self.queues[i].put(numpy.ravel(next(self.inputs[i])))
               except StopIteration:
                  done[i] = True
