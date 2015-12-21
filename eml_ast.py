try:
   import pydot
except ImportError:
   import sys
   print("Pydot could not be found, AST cannot be graphed", file=sys.stderr)

class CommandDef(object):
   def __init__(self, cmd, **args):
      self.command = cmd
      self.flags = [key for key, value in args.items() if value is None]
      self.args = {key: value for key, value in args.items() if value is not None}
      
   def pydot(self):
      name = self.command
      flags = " ".join("-%s" % f for f in self.flags)
      args = " ".join("-%s=%s" % p for p in self.args.items())
      return [pydot.Node("%s %s %s" % (name, flags, args))], []

class CacheDef(object):
   pass
      
class MemCacheDef(CacheDef):
   def __init__(self, name):
      self.name = name
      
   def pydot(self):
      return [pydot.Node("$%s" % self.name)], []
      
class DiskCacheDef(CacheDef):
   def __init__(self, name):
      self.name = name
      
   def pydot(self):
      return [pydot.Node("!%s" % self.name)], []
      
tup_ids = 1
class TupleCacheDef(CacheDef):
   def __init__(self, inner_caches, is_dest=False):
      global tup_ids
      self.inner = inner_caches
      self.id = tup_ids
      self.is_dest = is_dest
      tup_ids += 1
      self.name = "_TUP%d" % self.id
      
   def make_dest(self):
      self.is_dest = True
      for inner in self.inner:
         if hasattr(inner, 'make_dest'):
            inner.make_dest()
      
   def pydot(self):
      contained = [inner.pydot() for inner in self.inner]
      last_nodes = [nodes[-1] for nodes, edges in contained]
      contained_nodes, contained_edges = zip(*contained)
      contained_nodes = list(sum(contained_nodes, []))
      contained_edges = list(sum(contained_edges, []))
      nd = pydot.Node(self.name)
      edges = [pydot.Edge(inner, nd) if not self.is_dest else pydot.Edge(nd, inner) for inner in last_nodes]
      return contained_nodes + [nd], contained_edges + edges
      
class PipeDef(object):
   def __init__(self, source, dest):
      self.src = source
      self.dst = dest
      
   def pydot(self):
      a_ns, a_es = self.src.pydot()
      b_ns, b_es = self.dst.pydot()
      return a_ns + b_ns, a_es + b_es + [pydot.Edge(a_ns[-1], b_ns[-1])]

class BlockDef(object):
   def __init__(self, lines):
      self.lines = lines
      
   def pydot(self):
      nodes = []
      edges = []
      for line in self.lines:
         n, e = line.pydot()
         nodes += n
         edges += e
      return nodes, edges
      
def graph(root_def):
   graph = pydot.Dot(graph_type='digraph')
   nodes, edges = root_def.pydot()
   #print("=" * 80)
   #import pprint
   #pprint.pprint(nodes)
   #pprint.pprint(edges)
   for node in nodes:
      graph.add_node(node)
   for edge in edges:
      graph.add_edge(edge)
   graph.write_pdf('sample.pdf')
      
#class ForLoopDef(object):
#   def __init__(self, target_cache, source_cache, body_block):
#      self.src = source_cache
#      self.dst = target_cache
#      self.body = body_block
      

