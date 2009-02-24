'''Analyze NBER patent data.

Requirements:
    * scipy
    * networkx
    * mdp <http://mdp-toolkit.sourceforge.net/>

Things we want to do:

    1. Get basic count data by category
    2. Do citation anlysis (forward and back) by time and category
    3. Do citation analysis over time for a particular item
        * or just: what is distribution of lag times for citations
        * take all patents in 1975 and run citation data through ...
    3. Do a PCA analysis using some data

1. Links/Flows = Citations

Can use graph theoretic tools. Note extra attributes derived from patents such
as:

    * year it occurred + difference in age
    * Direction 

One *big* problem here is censoring bias. We do not have full patent set or
full citation set. Thus we lose patents as they go outside of the set. Not
clear what effect this has.


2. Patents = Technologies:
    * location of patents in technology space, patent = some vector of characteristics e.g.
        * adjacency matrix vector
        * class, subcat, etc
    * value of patents
        * no. citations, no. claims etc

Ideas:

    * knowledge flows: cite from x -> y is flow from y -> x. Equate x and y
      with their technological areas and ...
      * multi-graph with weighted links


'''
import os
import re
import simplejson as sj
import sqlalchemy.sql as sql
import scipy as S
import scipy.io

import convert_to_db as db
import data as D

datadir = D.datadir
outdir = D.outdir

class Analyzer(object):
    subcat_list = os.path.join(datadir, 'subcat_summary.js')
    nclass_list = os.path.join(datadir, 'nclass_summary.js')

    def __init__(self):
        self.subcatstats = None
        self.nclassstats = None
        self.load_cached_data()
        # (wc data/subcategories.csv) - 1
        # self.num_subcats = 36
        # tail -n +10 data/list_of_classes.txt | wc
        # self.num_classes = 426

    def load_cached_data(self):
        if not os.path.exists(self.subcat_list):
            self._get_subcat_stats()
        self.subcatstats = sj.load(file(self.subcat_list))
        if not os.path.exists(self.nclass_list):
            self._get_nclass_stats()
        self.nclassstats = sj.load(file(self.nclass_list))

    def full_join(self):
        full = db.patent.join(db.citation)
        p1 = db.patent
        p2 = db.patent.alias('cited')
        c1 = db.citation
        full = full.outerjoin(p2, p2.c.id==db.citation.c.cited_id)
        sel = sql.select(
                [p1.c.id, p2.c.id, c1.c.cited_id, p1.c.cmade,
                    p1.c.nclass, p2.c.nclass,
                    p1.c.subcat, p2.c.subcat,
                    ],
                from_obj=full)
        sel = sel.apply_labels()
        return sel

    def subcat_labels(self):
        fn = os.path.join(datadir, 'subcategories.csv')
        import csv
        r = csv.reader(file(fn))
        r.next() # skip heading
        labels = [ [int(row[1]), row[2] ] for row in r ]
        return dict(labels)

    def nclass_labels(self):
        fn = os.path.join(datadir, 'list_of_classes.txt')
        labels = {}
        for line in open(fn):
            if re.match('^\d', line):
                labels[int(line[:3])] = line[4:].strip()
        return labels

    def _get_subcat_stats(self):
        # hand-crafted sql is probably faster
        q = sql.select([db.patent.c.subcat, sql.func.count('*')])
        q = q.group_by(db.patent.c.subcat)
        data = q.execute().fetchall()
        data = [ list(x) for x in data ]
        data.sort()
        sj.dump(data, file(self.subcat_list, 'w'), indent=4)

    def _get_nclass_stats(self):
        q = sql.select([db.patent.c.nclass, sql.func.count('*')])
        q = q.group_by(db.patent.c.nclass)
        data = q.execute().fetchall()
        data = [ list(x) for x in data ]
        data.sort()
        sj.dump(data, file(self.nclass_list, 'w'), indent=4)

    def all_cite_counts(self):
        cached = 'data/cite_counts_by_year.js'
        if not os.path.exists(cached):
            res = []
            for year in range(1975, 1995):
                res.append([year, self.cite_counts(year)])
            sj.dump(res, file(cached, 'w'), indent=4)
        else:
            res = sj.load(file(cached))
        return res

    def cite_counts(self, year):
        # if not self.cite_counts
        t = db.patent.c
        results = {}
        def ddist(col):
            q = sql.select([col, sql.func.count('*')]) # ([col, sql.func.count('*'), t.gyear])
            q = q.where(t.gyear==year)
            q = q.group_by(col)
            q = q.order_by(col)
            cursor = q.execute()
            out = [ [x[0], x[1] ] for x in cursor ]
            return out
        results['cmade'] = ddist(t.cmade)
        results['creceive'] = ddist(t.creceive)
        return results

    def extract_citation_graph(self, subcat):
        '''Extract the citation graph.

        Implement the following but fast:

        patent_set = patent_query.execute()
        for patent in patent_set:
            for cite in patent.citations:
                results.append([patent.id, cite.cited_id, patent.gyear])
        '''
        q = self.full_join()
        citing = db.patent
        cited = db.patent.alias('cited')
        q = q.where(db.patent.c.subcat==subcat)
        q = q.where(db.patent.c.gyear>=1975)
        # if we want to restrict to citations which go back into the set do
        # does not work
        # q = q.where(cited.c.id != None)
        print q
        dgr = nx.DiGraph()
        count = -1
        for row in q.execute():
            count += 1
            if count % 100 == 0: print count
            citingid = row[citing.c.id]
            citedid = row[db.citation.c.cited_id]
            dgr.add_edge(citingid, citedid)
        return dgr

    def get_citation_graph(self, subcat):
        fn = os.path.join(D.citesdatadir, 'subcat_%s.dat' % subcat)
        if not os.path.exists(fn):
            dgr = self.extract_citation_graph(subcat)
            nx.write_edgelist(dgr, open(fn, 'w'), delimiter=',')
        else:
            dgr = nx.read_edgelist(open(fn), delimiter=',',
                    create_using=nx.DiGraph())
        return dgr

    def get_subject_vectors(self, subcat):
        fn = os.path.join(D.citesdatadir, 'subcat_%s_subject_vectors.dat' % subcat)
        if not os.path.exists(fn):
            mat = self.extract_subject_vectors(subcat)
            scipy.io.write_array(fn, mat)
        else:
            mat = scipy.io.read_array(fn)
        return mat

    def extract_subject_vectors(self, subcat, limit=None):
        q = self.full_join()
        citing = db.patent
        cited = db.patent.alias('cited')
        q = q.where(db.patent.c.subcat==subcat)
        q = q.where(db.patent.c.gyear>=1975)
        if limit:
            q = q.limit(limit)
        out = self.subject_vectors(q)
        tlist = [ v for v in out.values() ]
        return S.array(tlist)

    def subject_vectors(self, query):
        # TODO: refactor as used both here and below
        class CategoryProcessor(object):
            '''Convert subcategories to indices in a matrix.'''
            def __init__(self, catname, cat_summary):
                self.catname = catname
                self.src_cat_col = getattr(db.patent.c, self.catname)
                cited = db.patent.alias('cited')
                self.cited_cat_col = getattr(cited.c, self.catname)

                self.size = len(cat_summary)
                self.catlist = [ x[0] for x in cat_summary]
                self.size = len(self.catlist)

            def process(self, row):
                i = self.cat2idx(row[self.src_cat_col])
                j = self.cat2idx(row[self.cited_cat_col])
                return i,j

            def cat2idx(self, cat):
                # index into matrix
                if cat is None:
                    return self.size
                else:
                    return self.catlist.index(cat)
        proc_subcat = CategoryProcessor('subcat', self.subcatstats)
        result = {}
        count = -1
        cited = db.patent.alias('cited')
        for row in query.execute():
            count += 1
            # if count % max(1,(total/100)) == 0: # every 1%
            if count % 10000 == 0:
                print count
            citingid = row[db.patent.c.id]
            citedid = row[db.citation.c.cited_id]
            citing_cat, cited_cat = proc_subcat.process(row)
            if not citingid in result:
                # add 1 for patent id
                # add 1 for case where patents unknown
                result[citingid] = S.zeros( proc_subcat.size+2, dtype=int )
                result[citingid][0] = citingid
            result[citingid][cited_cat + 1] += 1
        return result

    def all_flows(self):
        self.flows = {}
        for year in range(1975, 1995):
            self.flows[year] = self.get_flows_by_year(year)
        return self.flows

    def get_flows_by_year(self, year, limit=0):
        '''Return an NxN matrix with N(i,j) = flow from area i to area j.

        See L{get_flows} for more details.

        NB: we use gyear not appyear to sort by year.
        '''
        # for catname in [ 'nclass', '
        fn1 = 'subcat_%s.dat' % year
        fn2 = 'nclass_%s.dat' % year
        fp1 = os.path.join(D.flowdatadir, fn1)
        fp2 = os.path.join(D.flowdatadir, fn2)
        if not os.path.exists(fp1):
            print '## Extracting flow information for year: ', year
            patents = self.full_join()
            patents = patents.where(db.patent.c.gyear==year)
            if limit > 0:
                patents = patents.limit(limit)
            msubcat, mnclass = self.get_flows(patents)
            scipy.io.write_array(fp1, msubcat) 
            scipy.io.write_array(fp2, mnclass)
        else:
            msubcat = scipy.io.read_array(fp1)
            mnclass = scipy.io.read_array(fp2)
        return (msubcat, mnclass)

    def get_flows(self, query):
        '''Citation flows from different areas (subcat/nclass).
        
        Sources for citations are patents in query so we are measuring all flow
        into those areas from *all* other patents (i.e. cited patents can be
        outside of our set of patents).

        Currently count each citation as 1 unit.

        @return 2 matrixes (subcat and nclass respectively) with M(i,j) =
        citation flow from area i to area j.

        Flow i->j is measured by a citation from i->j (so movement of 'ideas'
        from j -> i).

        Where patent is unknown assign this to an extra last category

        For efficiency do both nclass and subcat at once.
        '''
        class CategoryProcessor(object):
            def __init__(self, catname, cat_summary):
                self.catname = catname
                self.src_cat_col = getattr(db.patent.c, self.catname)
                cited = db.patent.alias('cited')
                self.cited_cat_col = getattr(cited.c, self.catname)

                self.size = len(cat_summary)
                self.catlist = [ x[0] for x in cat_summary]
                self.size = len(self.catlist)
                # add 1 for case where patents unknown
                self.matrix = S.zeros( (self.size+1, self.size+1) )

            def process(self, row):
                # weight in flow by number of citatons this patent has
                # flow = 1.0/row[db.patent.c.cmade]
                flow = 1.0
                i = self.cat2idx(row[self.src_cat_col])
                j = self.cat2idx(row[self.cited_cat_col])
                self.matrix[i,j] = self.matrix[i,j] + flow

            def cat2idx(self, cat):
                # index into matrix
                if cat is None:
                    return self.size
                else:
                    return self.catlist.index(cat)

        proc_subcat = CategoryProcessor('subcat', self.subcatstats)
        proc_nclass = CategoryProcessor('nclass', self.nclassstats)
        # very slow
        # countq = query.alias().count()
        # total = countq.execute().fetchall()[0][0]
        total = 'Unknown'
        print 'Total to process:', total
        count = -1
        for row in query.execute():
            count += 1
            # if count % max(1,(total/100)) == 0: # every 1%
            if count % 10000 == 0:
                print count
            for proc in [ proc_subcat, proc_nclass ]:
                    proc.process(row)

        return (proc_subcat.matrix, proc_nclass.matrix)
    


import pylab
import networkx as nx
import mdp
class Plotter(object):

    def __init__(self):
        self.a = Analyzer()

    def plot_category_stats(self):
        def doplot(stats, fname):
            stats = zip(*stats)
            pylab.bar(stats[0], stats[1])
            # TODO: labels bars -- see data/subcategories.csv or data/list_of_classes.txt
            print fname
            fn = os.path.join(outdir, '%s.png' % fname)
            pylab.savefig(fn)
            pylab.clf()
        doplot(self.a.subcatstats, 'subcat_stats')
        doplot(self.nclassstats, 'nclass_stats')

    def plot_ddist(self, year=None):
        c = self.a.all_cite_counts()
        c = dict(c)
        if year:
            counts = c[year]['creceive']
        else:
            counts = {}
            for tyear in c:
                yearcounts = c[tyear]['creceive']
                for cited_amount, num in yearcounts:
                    counts[cited_amount] = counts.get(cited_amount, 0) + num
            counts = [ [k,v] for k,v in counts.items() ]
            counts.sort()
            # for file names etc
            year = '1975-1994'
        counts = zip(*counts)
        pylab.title('Distbn of Citations Received (%s)' % year)
        pylab.xlabel('No. Citations Received')
        pylab.ylabel('No. of Patents')
        pylab.bar(counts[0], counts[1], log=True)
        fn = os.path.join(outdir, 'creceive_ddist_%s.png' % year)
        pylab.savefig(fn)
        pylab.clf()

    def plot_subcat_flow_bar(self, subcatid, year):
        msubcat, mnclass = self.a.get_flows_by_year(year)
        subcats = [ x[0] for x in self.a.subcatstats ]
        idx = subcats.index(subcatid)
        # for undefined area
        subcats.append(subcats[-1] + 1)
        # 2nd row
        vals = msubcat[idx]
        pylab.bar(subcats, vals)
        fn = os.path.join(outdir, 'flows_subcat_%s_%s.png' % (year, subcatid))
        pylab.savefig(fn)

    def pca_of_flows(self, year=1994):
        msubcat, mnclass = self.a.get_flows_by_year(year)
        # use numbers rather than names because names take up too much space
        slabels = self.a.subcat_labels().keys()
        nlabels = self.a.nclass_labels().keys()
        # TODO:? limit only do subcats (with classes too much!)
        for (m,l,n) in zip([msubcat, mnclass], [slabels, nlabels], ['subcat', 'nclass']):
        # for (m,l,n) in [(msubcat, slables, 'subcat')]:
            l.sort()
            self.plot_pca(m, 'flows_pca_%s_%s.png' % (n,year), l)

    def plot_pca(self, inmatrix, filename, labels=None):
        trimmed = inmatrix[:-1,:-1]
        # normalize by dividing row by row totals so rows sum to 1
        for ii, row in enumerate(trimmed):
            rowtotal = row.sum()
            if rowtotal > 0:
                trimmed[ii] = row / rowtotal

        pcanode = mdp.nodes.PCANode(output_dim=2, svd=True)
        pcanode.train(trimmed)
        pcanode.stop_training()
        outpca = pcanode.execute(trimmed)

        pylab.clf()
        pylab.scatter(outpca[:,0], outpca[:,1])
        colours = { '1': 'b', '2': 'r', '3': 'k', '4': 'y', '5': 'm', '6': 'c' }
        if labels:
            for n, xy in zip(labels, outpca):
                pylab.annotate(n, xy, fontsize='x-small')
                # colour the different groups
                # n is subcat id and and main categories share a first letter
                # only works for subcats
                if 'subcat' in filename:
                    pylab.scatter([xy[0]], [xy[1]], c=colours[str(n)[0]])
        fn = os.path.join(outdir, filename)
        pylab.savefig(fn)

    def pca_of_subject_vectors(self):
        inmats = [
                self.a.get_subject_vectors(subcat=12),
                self.a.get_subject_vectors(subcat=13),
                self.a.get_subject_vectors(subcat=67),
                ]
        # trim off patent names and the 'None' category
        def cleanup(inmatrix):
            trimmed = inmatrix[:,1:-1]
            # normalize by dividing row by row totals so rows sum to 1
            for ii, row in enumerate(trimmed):
                rowtotal = row.sum()
                if rowtotal > 0:
                    trimmed[ii] = row / rowtotal
            return trimmed
        inmats = map(cleanup, inmats)

        for m in inmats:
            pcanode = mdp.nodes.PCANode(output_dim=2)
            pcanode.train(m)

        pcanode.stop_training()
        outmats = [ pcanode.execute(m) for m in inmats ]

        pylab.clf()
        for m,c in zip(outmats, ['b', 'r', 'g', 'm'][:len(outmats)]):
            pylab.scatter(m[:,0], m[:,1], s=5, c=c)
        # filename = 'subject_vectors_subcat_%s.png' % subcat
        # filename = 'subject_vectors_subcat_12_13.png'
        filename = 'subject_vectors_subcat_12_13_67.png'
        fn = os.path.join(outdir, filename)
        pylab.savefig(fn)
        
class FlowPlotter(object):

    def __init__(self):
        self.a = Analyzer()
        self.figsize = 4
        if self.figsize == 16:
            self.font_size = 16
        elif self.figsize == 4:
            self.font_size = 6
        else:
            self.font_size = 19 - 3 * 16.0/self.figsize
        self.flow_scaler = 1000.0 * 0.75 * 16.0/self.figsize
        self.total_scaler = 100.0 * 16.0/self.figsize
        self.do_threshold = False

    def plot_subcat_flows(self, year, pos=None):
        msubcat, mnclass = self.a.get_flows_by_year(year)
        # remove the unknown category
        trimmed = msubcat[:-1,:-1]
        # also remove the miscellaneous
        trimmed = trimmed[:-1,:-1]
        # transpose to get flows right way round (from x into y)
        trimmed = trimmed.T
        tlabels = self.a.subcat_labels()
        labels = {}
        for ii, item in enumerate(self.a.subcatstats):
            labels[ii] = tlabels[item[0]]
        del labels[len(labels) - 1]

        pylab.clf()
        pylab.figure(figsize=(self.figsize, self.figsize))
        # remove figure boundaries/axes
        pylab.axis('off')
        dgr, pos = self.draw_weighted_adjacency_matrix(trimmed, labels=labels, pos=pos)
        pylab.xticks([])
        pylab.yticks([])
        fn = os.path.join(outdir, 'flows_subcat_%s' % year)
        if not self.do_threshold: fn += '_full'
        fn += '_%s' % self.figsize
        fn += '.png'
        pylab.savefig(fn)
        return pos

    def plot_all_subcat_flows(self, baseyear=1994):
        # do 1994 first and then use pos for others ...
        msubcat, mnclass = self.a.get_flows_by_year(baseyear)
        pos = self.plot_subcat_flows(baseyear)
        for year in range(1975, 1992, 3):
            print 'Graphing flows for:', year
            self.plot_subcat_flows(year, pos)
            # self.plot_subcat_flows(year)

    def threshold(self, inmatrix, percentage_threshold):
        totalflows = inmatrix.sum(axis=1)
        # remove self
        multmat = inmatrix >= 0
        for i in range(len(inmatrix)):
            totalflows[i] += - inmatrix[i][i]
            threshold = percentage_threshold/100.0 * totalflows[i]
            multmat[i] = inmatrix[i] > threshold
        # element by element multiplication 
        inmatrix = inmatrix * multmat
        return inmatrix

    def threshold_crude(self, inmatrix, threshold):
        multmat = inmatrix > threshold
        # element by element multiplication 
        inmatrix = inmatrix * multmat
        return inmatrix

    # TODO:
    # 1. animate where we fix position and then iterate over years using the same
    # data
    # 2. impose threshold on drawing edges.
    # 3. Aggregate to higher levels
    # 4. Use flow data to do a PCA analysis
    def draw_weighted_adjacency_matrix(self, inmatrix, labels=None, pos=None):
        # remove connections with low values ...
        if self.do_threshold:
            inmatrix = self.threshold(inmatrix, 5)
        adjmat = S.sign(inmatrix)
        dgr = nx.from_numpy_matrix(adjmat, create_using=nx.DiGraph())
        if pos is None:
            pos = nx.graphviz_layout(dgr)

        edgewidth = [] 
        for (u,v) in dgr.edges():
            flow = inmatrix[u][v]
            # normalize flow by dividing by some number
            flow = flow/self.flow_scaler
            # now done above
            # set flow = 0 when less than some value ...
            # so flow originally less than 100
            # if flow < 0.5: flow = 0
            edgewidth.append(flow)
        selfflows = []
        # normalize size of nodes by dividing by arbitrary constants
        for nn in dgr.nodes():
            flowtoself = inmatrix[nn][nn] / self.total_scaler
            selfflows.append(flowtoself)
        # assume nodes are enumerated in right order
        totalflows = inmatrix.sum(axis=1) / self.total_scaler
        nx.draw_networkx_edges(dgr, pos,
                width=edgewidth,
                edge_color='b',
                alpha=0.5,
                node_size=0
                )
        nx.draw_networkx_nodes(dgr, pos,
                node_size = totalflows,
                node_color='k',
                alpha=1.0)
        nx.draw_networkx_nodes(dgr, pos,
                node_size = selfflows,
                node_color='y',
                alpha=1.0)
        nx.draw_networkx_labels(dgr, pos, labels=labels, font_size=self.font_size, font_color='r')
        return (dgr, pos)



class GraphInfo:
    '''Information and manipulation of (mathematical) graphs.
    
    Not standard stuff as that can be done by networkx.
    '''

    def __init__(self):
        a = Analyzer()
        subcat = 13
        dgr = a.get_citation_graph(subcat)
        gr = dgr.to_undirected()
        # first component is largest
        conn_components = nx.connected_components(gr)
        print len(dgr)
        print len(conn_components)
        print [ len(x) for x in conn_components ]
        # first item is largest
        rgr = gr.subgraph(conn_components[0])
        print nx.density(rgr)

    def to_matrix(self, graph):
        '''Convert graph to a numpy matrix.
        
        Lots of efficiency issues. Many of our graphs have very large order
        (~10ks ...) and these cannot be converted to numpy matrices by networkx
        (and even if they could, they would be unmanageable).
        '''
        mat = nx.convert.to_numpy_matrix(rgr)
        return mat
    
    def to_matrix_sparse(self, graph):
        '''Convert to sparse matrix.

        Unfortunately this has no io support ...
        '''
        mat = nx.convert.to_scipy_sparse_matrix(graph)
        # tried this but unsuccessful
        # import scipy.io.mmio
        # fn = os.path.join(D.citesdatadir, 'subcat_%s_processed.dat' % subcat)
        # scipy.io.mmio.mmwrite(fn, mat)
        # scipy.io.write_array(fn, mat)
        return mat
    
    def to_matrix_random_cols(self, graph):
        '''Select a random set of columns from the graph.

        1. Convert to sparse
        2. Then select columns
        3. Then convert to normal matrix (now possible since reduced size)
        4. Write to disk

        Unfortunately 2 fails since sparse matrices do not seem to support
        column selection in standard numpy way ...
        '''
        # colselection = S.random.random(len(rgr))
        # take 2.5%
        # colselection = colselection < 0.025
        # take every 100th element
        colselection = S.zeros(len(rgr))
        ratio = 100
        for ii in range(len(rgr)/ratio):
            colselection[ii*ratio] = 1
        colselection = colselection > 0
        # mat = nx.convert.to_numpy_matrix(rgr)
        mat = nx.convert.to_scipy_sparse_matrix(rgr)
        # this does not work
        # mat = mat[:,colselection] 

class Presenter:
    def __init__(self):
        self.a = Analyzer()

    def latex_subcat(self):
        # subcats = self.a.
        import econ.data
        fn = os.path.join(datadir, 'subcategories.csv')
        reader = econ.data.CsvReader()
        tabular = reader.read(open(fn))
        tabular.header = ['Id', 'Name', 'Main Category', 'No. Patents']
        data = tabular.data
        data = zip(*data)
        del data[3]
        del data[0]
        data.append([ x[1] for x in self.a.subcatstats ])
        tabular.data = zip(*data)
        writer = econ.data.LatexWriter()
        out = writer.write(tabular)
        print out


def main():
    # ddists
    pl = Plotter()
    pl.plot_ddist(1975)
    pl.plot_ddist(1985)
    pl.plot_ddist(1994)
    pl.plot_ddist()
    # flow plotter
    fpl = FlowPlotter()
    fpl.plot_subcat_flows(1994)
    # fpl.plot_all_subcat_flows()
    # pl.pca_of_flows()

    # subject vectors
    # pl.pca_of_subject_vectors()


if __name__ == '__main__':
    # main()
    p = Presenter()
    # p.latex_subcat()
    
    pl = Plotter()
    pl.pca_of_flows()

    # g = GraphInfo()
    # a = Analyzer()
    # a.get_subject_vectors(13)


