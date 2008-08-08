import numpy

## Calculate some distributions

def get_cite_dist():
    cites_distbn = {}
    cited_distbn = {}
    merged_distbn = {}
    ff = file('apat63_99.txt')
    count = 0
    line_start_1975 = 784610
    for line in ff:
        if count >= line_start_1975:
            items = line.split(',')
            # year = int(items[1])
            cites = int(items[12])
            cited = int(items[13])
            merged = cites + cited
            cites_distbn[cites] = cites_distbn.get(cites, 0) + 1
            cited_distbn[cited] = cited_distbn.get(cited, 0) + 1
            merged_distbn[merged] = merged_distbn.get(merged, 0) + 1
        count += 1
        # if count >= line_start_1975 + 10:
        #     break
    return cites_distbn, cited_distbn, merged

def save_data(indict, filepath=None):
    keys = indict.keys()
    keys.sort()
    result = ''
    for key in keys:
        result += '%s,%s\n' % (key, indict[key])
    if filepath is not None:
        ff = file(filepath, 'w')
        ff.write(result)
    else:
        return result

def run_cite_dist():
    cites, cited = get_cite_dist()
    save_data(cites, './out/dist_cites.txt')
    save_data(cited, './out/dist_cited.txt')

def merge_count_data(cd1, cd2):
    # merge two sets of count data provided as numpy matrices/arrays
    d1 = dict(cd1.tolist())
    d2 = dict(cd2.tolist())
    keys = set(d1.keys() + d2.keys())
    keys = sorted(list(keys))
    out = []
    for k in keys:
        v = d1.get(k, 0) + d2.get(k, 0)
        out.append([k, v])
    return out

import pylab
def plot_dist():
    def _plot(data):
        xvals = data.T[0]
        yvals = data.T[1]
        pylab.subplot(211)
        pylab.loglog(xvals, yvals, 'bx')
        pylab.subplot(212)
        pylab.semilogy(xvals, yvals, 'bx')
    cites_data = numpy.loadtxt('./out/dist_cites.txt', dtype=int,
            delimiter=',')
    cited_data = numpy.loadtxt('./out/dist_cited.txt', dtype=int,
            delimiter=',')

    _plot(cites_data)
    pylab.savefig('./out/dist_cites.png')
    pylab.clf()
    _plot(cited_data)
    pylab.savefig('./out/dist_cited.png')
    pylab.clf()

if __name__ == '__main__':
    import pylab
    cites_data = file('./out/dist_cited.txt').read()
    plot_dist()
