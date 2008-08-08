import os

import networkx as nx
import pylab
import numpy

cache = os.path.abspath('./data')
cites = os.path.join(cache, 'cite.restricted13.dat')

# min pat number in our data
min_pat_num = 3070935

def parse_line(line):
    citing, cited = line.split(',')
    citing = int(citing)
    cited = int(cited)
    return citing, cited

def make_graph(how_many=None):
    # gr = nx.DiGraph()
    gr = nx.Graph()
    count = 0
    for line in file(cites):
        # if count % 100 == 0:
        #    print count
        citing, cited = parse_line(line)
        gr.add_edge((citing, cited))
        count += 1
        if how_many and count > how_many:
            break
    return gr

def draw_graph(graph):
    import pylab
    nx.draw(graph, font_size=11)
    # pylab.show()
    fp = './out/first-50-subcat-13.png'
    pylab.savefig(fp)

def analyse(graph):
    print 'Order (Size): ', graph.order()
    num_connected = nx.number_connected_components(graph.to_undirected())
    print 'Number connected components: ', num_connected
    print 'Density: ', nx.density(graph)

def plot_degree_distbn(graph):
    nodes = graph.nodes()
    # not right to include patents outside of the set as they can only have
    # cites and cannot cite anything (will still be slightly biased)
    nodes = filter(lambda n: n > min_pat_num, nodes)
    degrees = graph.degree(nodes)
    maxdegree = max(degrees)
    (hist, lower_edges) = numpy.histogram(degrees, maxdegree+1,
            (0,maxdegree+0.5))
    # pylab.bar(lower_edges, [ hist)
    pylab.subplot(211)
    pylab.loglog(lower_edges, hist)
    pylab.subplot(212)
    pylab.semilogy(lower_edges, hist)

def plot_cat13_ddistbn():
    gr = make_graph()
    plot_degree_distbn(gr)
    pylab.savefig('./out/cat13_ddistbn.png')

if __name__ == '__main__':
    gr = make_graph(10000)
    # draw_graph(gr)
    # analyse(gr)
    plot_cat13_ddistbn()

