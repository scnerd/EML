from eml.modules import Command
from sklearn.svm import LinearSVC
import numpy

class Main(Command):
   def num_outputs(self):
      return 1

   def __call__(self):
      def arg_convert(name, converter):
         if name in self.kwargs:
            self.kwargs[name] = converter(self.kwargs[name])
      bool_conv = lambda s: s.lower() is 'true'
      arg_convert('C', float)
      arg_convert('dual', bool_conv)
      arg_convert('tol', float)
      arg_convert('fit_intercept', bool_conv)
      arg_convert('intercept_scaling', float)
      arg_convert('verbose', int)
      arg_convert('random_state', int)
      arg_convert('max_iter', int)
      
      input_data = numpy.array(list(self.inputs[0]))
      input_labels = numpy.array(list(self.inputs[1]))
      print("SK_SVM: Done gathering, beginning training")
      print("SK_SVM: Data size: %s" % str(input_data.shape))
      
      model = LinearSVC(**self.kwargs)
      
      model.fit(input_data, input_labels)
      
      self.queues[0].put(model)
