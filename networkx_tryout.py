import os

import networkx as nx

cache = os.path.abspath('./cache')
cites = os.path.join(cache, 'cite.restricted13.dat')

def parse_line(line):
    citing, cited = line.split(',')
    citing = int(citing)
    cited = int(cited)
    return citing, cited

def make_graph():
    gr = nx.DiGraph()
    count = 0
    for line in file(cites):
        citing, cited = parse_line(line)
        gr.add_edge((citing, cited))
        count += 1
        if count >= 50:
            break
    return gr

def draw_graph(graph):
    import pylab
    nx.draw(graph, font_size=11)
    # pylab.show()
    fp = os.path.join(cache, 'first-50-subcat-13.png')
    pylab.savefig(fp)

def analyse(graph):
    print 'Order (Size): ', graph.order()
    num_connected = nx.number_connected_components(graph)
    print 'Number connected components: ', num_connected
    print 'Density: ', nx.density(graph)


if __name__ == '__main__':
    gr = make_graph()
    # draw_graph(gr)
    analyse(gr)

