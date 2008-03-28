'''Build a Citation Matrix.
'''
from numpy import zeros, array, all

def get_patents_in_subcat(subcat_num, patlist_fileobj, start_counting):
    count = 0
    results= []
    for line in patlist_fileobj:
        if count >= start_counting:
            items = line.split(',')
            subcat = int(items[11])
            patnum = int(items[0])
            if subcat == subcat_num:
                results.append(patnum)
        count += 1
        # if count >= line_start_1975 + 10:
        #     break
    return results

def make_cite_matrix(patlist, cite_fileobj):
    '''Build the basic citation matrix given a list of patents and a citation
    file object.

    NB: if a cited patent is outside of patlist it will be ignored.

    @return: a numpy array containing the citation matrix.
    '''
    size = len(patlist)
    citematrix = zeros((size, size))
    for line in cite_fileobj:
        citing, cited = line.split(',')
        citing = int(citing)
        cited = int(cited)
        try:
            row = patlist.index(citing)
            col = patlist.index(cited)
        except: # cite/cited outside of the set
            continue
        citematrix[row, col] = 1
        print citematrix
    return citematrix

data_dir = os.path.abspath('./data')
pat_file_path = os.path.join(data_dir, 'apat63_99.txt')
cite_file_path = os.path.abspath('./data/cite75_99.txt')
def run_make_cite_matrix():
    from analyse import dump_array
    # patfile = file(pat_file_path)
    # subcat = 13
    # line_start_1975 = 784610
    # patlist = get_patents_in_subcat(subcat, patfile, line_start_1975)
    fp = os.path.abspath('./cache/subcat13.dat')
    patlist = []
    for line in file(fp):
        patlist.append(int(line))
    cite_fp = os.path.abspath('./cache/cite.restricted13.dat')
    cite_fo = file(cite_fp)
    citemat = make_cite_matrix(patlist, cite_fo)
    dump_array(citemat, './cache/subcat13.citematrix.dat')


from StringIO import StringIO
class TestCitationMatrix:

    patfile = StringIO( \
'''6009552,1999,14606,1997,"IL","",386735,2,,714,2,13,5,0,1,,0.48,,12.6,0.2,0.2,,
6009553,1999,14606,1997,"US","MA",695811,2,,714,2,22,12,0,1,,0.7778,,10.9167,0,0,,
6009554,1999,14606,1997,"US","NY",219390,2,,714,2,13,9,0,1,,,,12.7778,0.1111,0.1111,,'''
        )
    
    exp1 = [6009552, 6009554]

    citefile = StringIO( \
'''6009552,6009554
6009554,3070805
3070805,3070805'''
        )

    exp_cite_matrix = array([
        [0.0, 1.0],
        [0.0, 0.0],
        ])
    
    def test_get_patents_in_subcat(self):
        out = get_patents_in_subcat(13, self.patfile, 0)
        assert out == self.exp1

    def test_make_cite_matrix(self):
        out = make_cite_matrix(self.exp1, self.citefile)
        print out
        assert all(out == self.exp_cite_matrix)

