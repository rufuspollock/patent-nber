## Utilities

def unzip_data(instr):
    xvals = []
    yvals = []
    for line in instr.split():
        xx, yy = line.split(',')
        xvals.append(int(xx))
        yvals.append(int(yy))
    return xvals, yvals

## Calculate some distributions

def get_cite_dist():
    cites_distbn = {}
    cited_distbn = {}
    ff = file('apat63_99.txt')
    count = 0
    line_start_1975 = 784610
    for line in ff:
        if count >= line_start_1975:
            items = line.split(',')
            # year = int(items[1])
            cites = int(items[12])
            cited = int(items[13])
            cites_distbn[cites] = cites_distbn.get(cites, 0) + 1
            cited_distbn[cited] = cited_distbn.get(cited, 0) + 1
        count += 1
        # if count >= line_start_1975 + 10:
        #     break
    return cites_distbn, cited_distbn

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
    save_data(cites, 'dist_cites.txt')
    save_data(cited, 'dist_cited.txt')

def plot_dist():
    import pylab
    import math
    cites_data = file('dist_cited.txt').read()
    xvals, yvals = unzip_data(cites_data) 
    yvals = [ math.log(float(yy)) for yy in yvals ]
    pylab.plot(xvals, yvals, 'bx')
    pylab.show()


class TestStuff:

    def test_save_data(self):
        indict = { 1 : 2, 0 : 20 }
        out = save_data(indict)
        print out
        assert '0,20\n1,2\n' in out

    def test_unzip_data(self):
        instr = \
'''0,50519
1,123521'''
        xx, yy = unzip_data(instr)
        print xx, yy 
        assert xx == [ 0, 1 ]
        assert yy == [ 50519, 123521 ]


if __name__ == '__main__':
    # run()
    plot_dist()
