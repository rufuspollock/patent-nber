import pylab
import networkx as nx


def drawdemo():
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

from StringIO import StringIO
def dump_and_load():
    # gr = nx.erdos_renyi_graph(100,0.1)
    gr = nx.Graph()
    dgr = nx.DiGraph()
    edges = [ (1,0), (0,2), (0,3), (1,2) ]
    for e in edges:
        gr.add_edge(e)
        dgr.add_edge(e)
    def show(gr, dumper):
        sio = StringIO()
        dumper(gr, sio, delimiter=',')
        sio.seek(0)
        print sio.read(100)
        print

    print 'Adjacency List format'
    print
    show(gr, nx.write_adjlist)
    show(dgr, nx.write_adjlist)

    print 'Edge List format'
    print
    show(gr, nx.write_edgelist)
    show(dgr, nx.write_edgelist)

    # nx.read_edgelist(fn, create_using=nx.DiGraph(), nodetype=int)

if __name__ == '__main__':
    # drawdemo()
    dump_and_load()
