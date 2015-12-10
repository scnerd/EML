from eml.modules import Command
import sys

class Main(Command):
   def num_outputs(self):
      return self.num_inputs
     
   def __call__(self):
      interval = int(self.kwargs.get('interval', '1'))
      nums = [0 for i in range(self.num_inputs)]
      done = [False for i in range(self.num_inputs)]
      printout = ""
      j = 0
      while not all(done):
         for i in range(self.num_inputs):
            if not done[i]:
               try:
                  self.queues[i].put(next(self.inputs[i]))
                  nums[i] += 1
               except StopIteration:
                  done[i] = True
         if j % interval == 0:
            printout = "\r%s" % "/".join(str(i) for i in nums)
            sys.stderr.write(printout)
            sys.stderr.flush()
         j += 1
      printout = "\r%s" % "/".join(str(i) for i in nums)
      sys.stderr.write("\r%s\r" % (" " * len(printout)))
      sys.stderr.flush()
      
