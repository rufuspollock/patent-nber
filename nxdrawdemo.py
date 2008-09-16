import pylab
import networkx as nx

er = nx.erdos_renyi_graph(100,0.1)
# ws = watts_strogatz_graph(30,3,0.1)
# ba = barabasi_albert_graph(100,5)


nodesize = 20
pylab.figure(figsize=(8,8))

kwargs = { 'with_labels': False, 'node_size': nodesize }
nx.draw(er, **kwargs)
pylab.savefig('/tmp/nxdraw.png')

pylab.clf()
nx.draw_circular(er, **kwargs)
pylab.savefig('/tmp/nxdraw_circular.png')

pylab.clf()
pos = nx.graphviz_layout(er,prog="twopi",root=0)
nx.draw(er, pos, **kwargs)
pylab.savefig('/tmp/nxgraphviz_layout.png')

pylab.clf()
pos = nx.graphviz_layout(er, prog="neato")
nx.draw(er, pos, **kwargs)
pylab.savefig('/tmp/nxgraphviz_layout.png')
