'''Things we want to do:

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
    * 

'''
import os
import simplejson as sj
import sqlalchemy.sql as sql
import numpy as N
import scipy.io

import convert_to_db as db
import data as D

datadir = D.datadir
outdir = D.outdir

class Analyzer(object):
    subcat_list = os.path.join(datadir, 'subcat_summary.js')
    nclass_list = os.path.join(datadir, 'nclass_summary.js')

    def __init__(self):
        self.subcats = None
        self.nclasss = None
        self.load_cached_data()
        # (wc data/subcategories.csv) - 1
        # self.num_subcats = 36
        # tail -n +10 data/list_of_classes.txt | wc
        # self.num_classes = 426

    def load_cached_data(self):
        if not os.path.exists(self.subcat_list):
            self._get_subcat_stats()
        self.subcats = sj.load(file(self.subcat_list))
        if not os.path.exists(self.nclass_list):
            self._get_nclass_stats()
        self.nclasss = sj.load(file(self.nclass_list))

    def full_join(self):
        full = db.patent.join(db.citation)
        p1 = db.patent
        p2 = db.patent.alias('cited')
        c1 = db.citation
        full = full.outerjoin(p2, p2.c.id==db.citation.c.cited_id)
        sel = sql.select(
                [p1.c.id, p2.c.id, p1.c.cmade,
                    p1.c.nclass, p2.c.nclass,
                    p1.c.subcat, p2.c.subcat,
                    ],
                from_obj=full)
        sel = sel.apply_labels()
        return sel

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
            sj.dump(res, file(cached, 'w'))
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

    def get_citation_matrix(self, patent_query):
        # patent_set = sql.select(d
        # sql.
        patent_set = patent_query.execute()
        for patent in patent_set:
            for cite in patent.citations:
                results.append([patent.id, cite.cited_id, patent.gyear])
            # in fact since both patent and pother must be in patent_set
            # can ignore this since we will already have it
            # (question is do we care about directionality ...
            # for pother in patent.cited_by:
            #    if pother in patent_set:
            #        results.append([patent, pother, pother.gyear])

    def get_citation_matrix_fast(self, subcat, years=None):
        # select citing_id, cited_id gyear
        # q = sql.select(
        pass

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
                self.matrix = N.zeros( (self.size+1, self.size+1) )

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

        proc_subcat = CategoryProcessor('subcat', self.subcats)
        proc_nclass = CategoryProcessor('nclass', self.nclasss)
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
def plot_category_stats():
    a = Analyzer()
    def doplot(stats, fname):
        stats = zip(*stats)
        pylab.bar(stats[0], stats[1])
        # TODO: labels bars -- see data/subcategories.csv or data/list_of_classes.txt
        print fname
        fn = os.path.join(outdir, '%s.png' % fname)
        pylab.savefig(fn)
        pylab.clf()
    doplot(a.subcats, 'subcat_stats')
    doplot(a.nclasss, 'nclass_stats')

def plot_ddist(year):
    a = Analyzer()
    c = a.all_cite_counts()
    c = dict(c)
    counts = c[year]['creceive']
    counts = zip(*counts)
    pylab.title('Distbn of Citations Received (%s)' % year)
    pylab.xlabel('No. Citations Received')
    pylab.ylabel('No. of Patents')
    pylab.bar(counts[0], counts[1], log=True)
    fn = os.path.join(outdir, 'creceive_ddist_%s.png' % year)
    pylab.savefig(fn)
    pylab.clf()

def plot_flows(year):
    a = Analyzer()
    msubcat, mnclass = a.get_flows_by_year(1985)
    # subcat 13
    idx = 2
    subcats = [ x[0] for x in a.subcats ]
    subcat = subcats[idx]
    # for undefined area
    subcats.append(subcats[-1] + 1)
    vals = msubcat[2]
    pylab.bar(subcats, vals)
    fn = os.path.join(outdir, 'flows_subcat_%s_%s.png' % (subcat, year))
    pylab.savefig(fn)

def main():
    plot_ddist(1975)
    plot_ddist(1985)
    plot_ddist(1994)

if __name__ == '__main__':
    # main()
    a = Analyzer()
    a.all_flows()
    # plot_flows(1985)


