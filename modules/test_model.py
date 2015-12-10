from eml.modules import Command
import sklearn
from sklearn.metrics import f1_score, accuracy_score, recall_score, precision_score
import pickle

class Main(Command):
   score_map = {'fscore': f1_score, 'accuracy': accuracy_score, 'precision': precision_score, 'recall': recall_score}

   def num_outputs(self):
      return 1

   def __call__(self):
      models = self.inputs[0]
      test_data = list(self.inputs[1])
      test_labels = list(self.inputs[2])
      out_q = self.queues[0]
      scores = [Main.score_map[flag] for flag in self.flags]
      for model in models:
         print("Testing model '%s'" % type(model).__name__)
         predicted = model.predict(test_data)
         for score in scores:
            out_q.put((self.flags[scores.index(score)], score(test_labels, predicted)))
