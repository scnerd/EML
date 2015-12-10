from eml.modules import Command
import random

def choice(probability):
   return random.random() <= probability

class Main(Command):
   def num_outputs(self):
      return 2 * self.num_inputs
      
   def __call__(self):
      ratio = float(self.kwargs.get('r', '0.9'))
      seed = self.kwargs.get('seed', None)
      if seed is not None:
         random.seed(int(seed))
      done = [False for i in self.inputs]
      while not all(done):
         output = 0 if choice(ratio) else 1
         for i in range(self.num_inputs):
            if not done[i]:
               try:
                  self.queues[i * 2 + output].put(next(self.inputs[i]))
               except StopIteration:
                  done[i] = True
         
            
         
