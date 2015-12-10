from eml.modules import Command
import os, numpy, gzip

def big_endian(a, b, c, d):
   return (a << 24) | (b << 16) | (c << 8) | d
      
def recursive_read(file, dims):
   if len(dims) == 1:
      for i in range(dims[0]):
         yield ord(file.read(1))
   else:
      for i in range(dims[0]):
         yield list(recursive_read(file, dims[1:]))
      
def load_ubyte(path):
   with gzip.open(path, 'rb') as file:
      file.read(3) # The third byte actually does matter, but we already know it'll be 0x08=unsigned byte
      num_dims = ord(file.read(1))
      dims = [big_endian(*file.read(4)) for i in range(num_dims)]
      yield from recursive_read(file, dims)
      
class Main(Command):
   def check_num_inputs(self, num_inputs):
      if num_inputs > 0:
         raise SyntaxError("%s can't take inputs" % self.name)

   def num_outputs(self):
      return 2
     
   def __call__(self):
      path = os.path.expanduser(self.kwargs.get('path', '~/mnist'))
      imgs1 = load_ubyte(os.path.join(path, 'train-images-idx3-ubyte.gz'))
      imgs2 = load_ubyte(os.path.join(path, 't10k-images-idx3-ubyte.gz'))
      lbls1 = load_ubyte(os.path.join(path, 'train-labels-idx1-ubyte.gz'))
      lbls2 = load_ubyte(os.path.join(path, 't10k-labels-idx1-ubyte.gz'))
      import itertools
      imgs = itertools.chain(imgs1, imgs2)
      lbls = itertools.chain(lbls1, lbls2)
      try:
         while True:
            self.queues[0].put(next(imgs))
            self.queues[1].put(next(lbls))
      except StopIteration:
         return
